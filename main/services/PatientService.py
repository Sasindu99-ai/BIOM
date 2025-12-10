import re
from datetime import datetime
from pathlib import Path

import pandas as pd
from django.conf import settings
from django.db.models import Count, Q, ExpressionWrapper, Case, F, When, Value, IntegerField
from django.db.models.functions import ExtractYear, Now, ExtractMonth, ExtractDay

from vvecon.zorion.core import Service
from vvecon.zorion.logger import Logger
from ..models import Patient

__all__ = ['PatientService']


class PatientService(Service):
	model = Patient
	searchableFields = ('fullName', 'notes')
	filterableFields = ('dateOfBirth', 'gender', 'createdBy', 'age')
	annotations = dict(
		userStudiesCount=Count('userStudies'),
		age=ExpressionWrapper(
			ExtractYear(Now()) - ExtractYear(F('dateOfBirth')) -
			Case(
				When(
					dateOfBirth__month__gt=ExtractMonth(Now()),
					then=Value(1),
				),
				When(
					dateOfBirth__month=ExtractMonth(Now()),
					dateOfBirth__day__gt=ExtractDay(Now()),
					then=Value(1),
				),
				default=Value(0),
				output_field=IntegerField()
			),
			output_field=IntegerField()
		)
	)

	def matchPatientsFromFile(self, file_url: str, column_mapping: dict = None) -> str:
		"""
		Process CSV/Excel file and match patients with existing records.
		
		Args:
			file_url: URL or path to the uploaded file
			column_mapping: Dictionary mapping standard fields to CSV columns
				e.g., {'firstName': 'first_name', 'lastName': 'last_name', ...}
		
		Returns:
			Path to the results CSV file (relative to MEDIA_ROOT)
		"""
		Logger.info(f'Processing file for patient matching: {file_url}')
		
		# Resolve file path
		if file_url.startswith('/media/'):
			file_path = Path(settings.MEDIA_ROOT) / file_url.replace('/media/', '')
		elif file_url.startswith('media/'):
			file_path = Path(settings.MEDIA_ROOT) / file_url.replace('media/', '')
		else:
			file_path = Path(settings.MEDIA_ROOT) / file_url
		
		if not file_path.exists():
			raise ValueError(f'File not found: {file_path}')
		
		# Read the uploaded file
		try:
			if str(file_path).endswith('.xlsx') or str(file_path).endswith('.xls'):
				df = pd.read_excel(file_path)
			else:
				df = pd.read_csv(file_path)
		except Exception as e:
			Logger.error(f'Error reading file: {str(e)}')
			raise ValueError(f'Error reading file: {str(e)}')
		
		# Normalize column names (strip whitespace, keep original case for mapping)
		original_columns = list(df.columns)
		df.columns = [col.strip() for col in df.columns]
		
		# Define required and optional fields
		required_fields = ['firstName']
		optional_fields = ['lastName', 'dateOfBirth', 'gender']
		
		# Use provided column mapping or auto-detect
		if column_mapping is None:
			column_mapping = dict()
		
		# Auto-detect columns if not provided
		file_columns = dict()
		for field in required_fields + optional_fields:
			if field in column_mapping:
				# Use user-provided mapping
				mapped_col = column_mapping[field]
				if mapped_col in df.columns:
					file_columns[field] = mapped_col
				else:
					# Column doesn't exist - check if required
					if field in required_fields:
						raise ValueError(f'Required column "{mapped_col}" (mapped to {field}) not found in file')
			else:
				# Auto-detect
				possible_names = {
					'firstName': ['firstname', 'first_name', 'fname', 'first'],
					'lastName': ['lastname', 'last_name', 'lname', 'last'],
					'dateOfBirth': ['dateofbirth', 'date_of_birth', 'dob', 'birthdate', 'birth_date'],
					'gender': ['gender', 'sex']
				}
				for col in df.columns:
					if col.lower() in [n.lower() for n in possible_names.get(field, [])]:
						file_columns[field] = col
						break
		
		# Validate required fields
		for field in required_fields:
			if field not in file_columns:
				raise ValueError(f'Required field "{field}" not found in file. Please provide column mapping.')
		
		# Prepare results
		results = []
		skipped_rows = []
		
		# Process each row
		for idx, row in df.iterrows():
			row_data = dict()
			row_original = dict()  # Store all original column values
			
			# Extract mapped fields
			for field in required_fields + optional_fields:
				if field in file_columns:
					col = file_columns[field]
					value = row[col] if col in row else None
					if pd.notna(value):
						row_data[field] = str(value).strip()
					else:
						row_data[field] = ''
						
					# Check if required field is missing
					if field in required_fields and not row_data[field]:
						skipped_rows.append(dict(row=idx + 1, reason=f'Missing required field: {field}'))
						break
			else:
				# Store all original columns
				for col in original_columns:
					value = row[col] if col in row else None
					row_original[col] = str(value) if pd.notna(value) else ''
				
				# Try to match with existing patients
				matched_patient = self._findBestMatchingPatient(
					row_data.get('firstName', ''),
					row_data.get('lastName', ''),
					row_data.get('dateOfBirth', ''),
					row_data.get('gender', '')
				)
				
				# Build result row - order: user columns, matched patient id, matched patient data
				result_row = dict()
				
				# Add all original columns first
				for col in original_columns:
					result_row[col] = row_original.get(col, '')
				
				# Add matched patient id
				result_row['matched_patient_id'] = matched_patient['id'] if matched_patient else ''
				
				# Add matched patient data
				if matched_patient:
					result_row['matched_patient_firstName'] = matched_patient.get('firstName', '')
					result_row['matched_patient_lastName'] = matched_patient.get('lastName', '')
					result_row['matched_patient_fullName'] = matched_patient.get('fullName', '')
					result_row['matched_patient_dateOfBirth'] = matched_patient.get('dateOfBirth', '')
					result_row['matched_patient_gender'] = matched_patient.get('gender', '')
				else:
					result_row['matched_patient_firstName'] = ''
					result_row['matched_patient_lastName'] = ''
					result_row['matched_patient_fullName'] = ''
					result_row['matched_patient_dateOfBirth'] = ''
					result_row['matched_patient_gender'] = ''
				
				results.append(result_row)
		
		if skipped_rows:
			Logger.warning(f'Skipped {len(skipped_rows)} rows due to missing required fields')
		
		# Create results DataFrame
		if not results:
			raise ValueError('No valid rows to process')
		
		results_df = pd.DataFrame(results)
		
		# Save results to CSV
		results_dir = Path(settings.MEDIA_ROOT) / 'patients' / 'matchResults'
		results_dir.mkdir(parents=True, exist_ok=True)
		
		timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
		results_file = results_dir / f'match_results_{timestamp}.csv'
		
		results_df.to_csv(results_file, index=False)
		
		Logger.info(f'Match results saved to: {results_file}. Processed {len(results)} rows, skipped {len(skipped_rows)} rows.')
		
		# Return relative path from MEDIA_ROOT
		return str(results_file.relative_to(settings.MEDIA_ROOT))
	
	def _findBestMatchingPatient(self, firstname: str, lastname: str, dateofbirth: str = '', gender: str = '') -> dict:
		"""
		Find the best matching patient based on name, DOB, and gender.
		Uses fullName matching with stripped name parts.
		
		Returns:
			Dictionary with patient data or None if no match found
		"""
		if not firstname:
			return None
		
		# Strip and split names
		firstname_parts = [p.strip() for p in re.split(r'[\s\-]+', firstname.strip()) if p.strip()]
		lastname_parts = [p.strip() for p in re.split(r'[\s\-]+', lastname.strip()) if p.strip()] if lastname else []
		
		# Build query for name matching using fullName
		name_query = Q()
		for first_part in firstname_parts:
			if first_part:
				name_query |= Q(fullName__icontains=first_part)
		for last_part in lastname_parts:
			if last_part:
				name_query |= Q(fullName__icontains=last_part)
		
		if not name_query:
			return None
		
		# Get candidates
		candidates = self.model.objects.filter(name_query).distinct()
		
		# Filter by date of birth if provided
		if dateofbirth:
			try:
				# Try to parse various date formats
				dob = None
				for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d', '%d-%m-%Y', '%Y-%m-%d %H:%M:%S']:
					try:
						dob = datetime.strptime(dateofbirth.strip(), fmt).date()
						break
					except ValueError:
						continue
				
				if dob:
					candidates = candidates.filter(dateOfBirth=dob)
			except Exception:
				pass  # If date parsing fails, skip DOB filtering
		
		# Filter by gender if provided
		if gender:
			gender_upper = gender.upper().strip()
			gender_map = dict(
				M='MALE', MALE='MALE',
				F='FEMALE', FEMALE='FEMALE',
				O='OTHER', OTHER='OTHER'
			)
			if gender_upper in gender_map:
				candidates = candidates.filter(gender=gender_map[gender_upper])
		
		# Score and rank candidates
		scored_candidates = []
		for patient in candidates[:50]:  # Limit to 50 for performance
			score = 0
			full_name = (patient.fullName or '').strip()
			
			# Score based on name parts matching
			for first_part in firstname_parts:
				if first_part and first_part.lower() in full_name.lower():
					score += 2
			
			for last_part in lastname_parts:
				if last_part and last_part.lower() in full_name.lower():
					score += 2
			
			# Bonus for exact first name match
			if patient.firstName and firstname_parts:
				if patient.firstName.strip().lower() == firstname_parts[0].lower():
					score += 5
			
			# Bonus for DOB match
			if dateofbirth and patient.dateOfBirth:
				try:
					for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
						try:
							dob = datetime.strptime(dateofbirth.strip(), fmt).date()
							if patient.dateOfBirth == dob:
								score += 10
								break
						except ValueError:
							continue
				except Exception:
					pass
			
			# Bonus for gender match
			if gender and patient.gender:
				gender_upper = gender.upper().strip()
				gender_map = dict(M='MALE', MALE='MALE', F='FEMALE', FEMALE='FEMALE', O='OTHER', OTHER='OTHER')
				if gender_upper in gender_map and patient.gender == gender_map[gender_upper]:
					score += 3
			
			if score > 0:
				scored_candidates.append((score, patient))
		
		# Return best match
		if scored_candidates:
			scored_candidates.sort(key=lambda x: x[0], reverse=True)
			best_patient = scored_candidates[0][1]
			
			return dict(
				id=best_patient.id,
				firstName=best_patient.firstName or '',
				lastName=best_patient.lastName or '',
				fullName=best_patient.fullName or '',
				dateOfBirth=str(best_patient.dateOfBirth) if best_patient.dateOfBirth else '',
				gender=best_patient.gender or ''
			)
		
		return None
