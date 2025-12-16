import re
from datetime import datetime
from pathlib import Path

import pandas as pd
from django.conf import settings
from django.db.models import Case, Count, ExpressionWrapper, F, IntegerField, Q, Value, When
from django.db.models.functions import ExtractDay, ExtractMonth, ExtractYear, Now

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
				output_field=IntegerField(),
			),
			output_field=IntegerField(),
		),
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
			Logger.error(f'Error reading file: {e!s}')
			raise ValueError(f'Error reading file: {e!s}')

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
				# Column doesn't exist - check if required
				elif field in required_fields:
					raise ValueError(f'Required column "{mapped_col}" (mapped to {field}) not found in file')
			else:
				# Auto-detect
				possible_names = {
					'firstName': ['firstname', 'first_name', 'fname', 'first'],
					'lastName': ['lastname', 'last_name', 'lname', 'last'],
					'dateOfBirth': ['dateofbirth', 'date_of_birth', 'dob', 'birthdate', 'birth_date'],
					'gender': ['gender', 'sex'],
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
					row_data.get('gender', ''),
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
				O='OTHER', OTHER='OTHER',
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
				gender=best_patient.gender or '',
			)

		return None

	def previewImport(self, file_url: str, column_mapping: dict = None) -> dict:
		"""
		Preview CSV/Excel file for import with duplicate detection.
		
		Returns:
			Dictionary with preview data, columns, duplicates, and stats
		"""
		Logger.info(f'Previewing file for import: {file_url}')

		# Resolve file path
		if file_url.startswith('/media/'):
			file_path = Path(settings.MEDIA_ROOT) / file_url.replace('/media/', '')
		elif file_url.startswith('media/'):
			file_path = Path(settings.MEDIA_ROOT) / file_url.replace('media/', '')
		else:
			file_path = Path(settings.MEDIA_ROOT) / file_url

		if not file_path.exists():
			raise ValueError(f'File not found: {file_path}')

		# Read the file
		try:
			if str(file_path).endswith('.xlsx') or str(file_path).endswith('.xls'):
				df = pd.read_excel(file_path)
			else:
				df = pd.read_csv(file_path)
		except Exception as e:
			Logger.error(f'Error reading file: {e!s}')
			raise ValueError(f'Error reading file: {e!s}')

		# Clean column names
		df.columns = [col.strip() for col in df.columns]
		columns = list(df.columns)

		# Auto-detect column mapping if not provided
		if column_mapping is None:
			column_mapping = {}

		detected_mapping = {}
		field_patterns = {
			'firstName': ['firstname', 'first_name', 'fname', 'first', 'given_name'],
			'lastName': ['lastname', 'last_name', 'lname', 'last', 'surname', 'family_name'],
			'dateOfBirth': ['dateofbirth', 'date_of_birth', 'dob', 'birthdate', 'birth_date', 'birthday'],
			'gender': ['gender', 'sex'],
			'notes': ['notes', 'comments', 'remarks', 'description'],
		}

		for field, patterns in field_patterns.items():
			if field not in column_mapping:
				for col in columns:
					if col.lower().replace(' ', '_') in patterns or col.lower() in patterns:
						detected_mapping[field] = col
						break

		# Merge provided mapping with detected
		final_mapping = {**detected_mapping, **column_mapping}

		# Process rows and detect duplicates
		preview_rows = []
		duplicates = []
		validation_errors = []

		for idx, row in df.iterrows():
			if idx >= 100:  # Limit preview to 100 rows
				break

			row_data = {}
			for col in columns:
				value = row[col]
				row_data[col] = str(value) if pd.notna(value) else ''

			# Extract mapped fields
			first_name = ''
			last_name = ''
			dob = ''
			gender = ''

			if 'firstName' in final_mapping and final_mapping['firstName'] in row:
				first_name = str(row[final_mapping['firstName']]) if pd.notna(row[final_mapping['firstName']]) else ''
			if 'lastName' in final_mapping and final_mapping['lastName'] in row:
				last_name = str(row[final_mapping['lastName']]) if pd.notna(row[final_mapping['lastName']]) else ''
			if 'dateOfBirth' in final_mapping and final_mapping['dateOfBirth'] in row:
				dob = str(row[final_mapping['dateOfBirth']]) if pd.notna(row[final_mapping['dateOfBirth']]) else ''
			if 'gender' in final_mapping and final_mapping['gender'] in row:
				gender = str(row[final_mapping['gender']]) if pd.notna(row[final_mapping['gender']]) else ''

			# Validate required fields (need at least firstName or lastName)
			if not first_name.strip() and not last_name.strip():
				validation_errors.append({
					'row_index': idx,
					'error': 'Missing both first name and last name',
				})

			# Check for duplicates
			if first_name.strip() or last_name.strip():
				match = self._findBestMatchingPatient(first_name, last_name, dob, gender)
				if match:
					# Calculate confidence based on match score
					confidence = 0.5  # Base confidence for name match
					if dob and match.get('dateOfBirth') == dob:
						confidence += 0.3
					if gender and match.get('gender', '').upper() == gender.upper():
						confidence += 0.2

					duplicates.append({
						'row_index': idx,
						'match_patient_id': match['id'],
						'match_confidence': round(confidence, 2),
						'match_name': match.get('fullName', ''),
						'match_dob': match.get('dateOfBirth', ''),
					})

			row_data['_row_index'] = idx
			preview_rows.append(row_data)

		# Calculate stats
		total_rows = len(df)
		duplicate_count = len(duplicates)
		error_count = len(validation_errors)
		new_count = total_rows - duplicate_count - error_count

		return {
			'total_rows': total_rows,
			'columns': columns,
			'detected_mapping': detected_mapping,
			'final_mapping': final_mapping,
			'preview_rows': preview_rows[:20],  # First 20 for preview
			'duplicates': duplicates,
			'validation_errors': validation_errors,
			'stats': {
				'total': total_rows,
				'new': max(0, new_count),
				'duplicates': duplicate_count,
				'errors': error_count,
			},
		}

	def executeImport(self, file_url: str, column_mapping: dict, duplicate_actions: dict = None, created_by=None) -> dict:
		"""
		Execute the import of patients from CSV/Excel file.
		
		Args:
			file_url: Path to the uploaded file
			column_mapping: Mapping of patient fields to CSV columns
			duplicate_actions: Dict of row_index -> action ('skip', 'update', 'create')
			created_by: User who is creating the patients
		
		Returns:
			Dictionary with import results
		"""
		Logger.info(f'Executing patient import from: {file_url}')

		if duplicate_actions is None:
			duplicate_actions = {}

		# Resolve file path
		if file_url.startswith('/media/'):
			file_path = Path(settings.MEDIA_ROOT) / file_url.replace('/media/', '')
		elif file_url.startswith('media/'):
			file_path = Path(settings.MEDIA_ROOT) / file_url.replace('media/', '')
		else:
			file_path = Path(settings.MEDIA_ROOT) / file_url

		if not file_path.exists():
			raise ValueError(f'File not found: {file_path}')

		# Read the file
		try:
			if str(file_path).endswith('.xlsx') or str(file_path).endswith('.xls'):
				df = pd.read_excel(file_path)
			else:
				df = pd.read_csv(file_path)
		except Exception as e:
			raise ValueError(f'Error reading file: {e!s}')

		df.columns = [col.strip() for col in df.columns]

		# Results tracking
		imported = 0
		skipped = 0
		updated = 0
		failed = 0
		failed_rows = []

		# Process each row
		for idx, row in df.iterrows():
			try:
				# Extract mapped fields
				patient_data = {}

				if 'firstName' in column_mapping and column_mapping['firstName'] in row:
					val = row[column_mapping['firstName']]
					patient_data['firstName'] = str(val).strip() if pd.notna(val) else ''

				if 'lastName' in column_mapping and column_mapping['lastName'] in row:
					val = row[column_mapping['lastName']]
					patient_data['lastName'] = str(val).strip() if pd.notna(val) else ''

				if 'dateOfBirth' in column_mapping and column_mapping['dateOfBirth'] in row:
					val = row[column_mapping['dateOfBirth']]
					if pd.notna(val):
						# Try to parse date
						dob_str = str(val).strip()
						for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d', '%d-%m-%Y']:
							try:
								patient_data['dateOfBirth'] = datetime.strptime(dob_str, fmt).date()
								break
							except ValueError:
								continue

				if 'gender' in column_mapping and column_mapping['gender'] in row:
					val = row[column_mapping['gender']]
					if pd.notna(val):
						gender_str = str(val).upper().strip()
						gender_map = {'M': 'MALE', 'MALE': 'MALE', 'F': 'FEMALE', 'FEMALE': 'FEMALE', 'O': 'OTHER', 'OTHER': 'OTHER'}
						patient_data['gender'] = gender_map.get(gender_str, '')

				if 'notes' in column_mapping and column_mapping['notes'] in row:
					val = row[column_mapping['notes']]
					patient_data['notes'] = str(val).strip() if pd.notna(val) else ''

				# Validate - need at least one name
				if not patient_data.get('firstName') and not patient_data.get('lastName'):
					failed += 1
					failed_rows.append({**dict(row), '_error': 'Missing name'})
					continue

				# Check action for this row
				action = duplicate_actions.get(str(idx), duplicate_actions.get('default', 'create'))

				# Check for existing patient
				match = self._findBestMatchingPatient(
					patient_data.get('firstName', ''),
					patient_data.get('lastName', ''),
					str(patient_data.get('dateOfBirth', '')),
					patient_data.get('gender', ''),
				)

				if match and action == 'skip':
					skipped += 1
					continue
				if match and action == 'update':
					# Update existing patient
					existing = self.getById(match['id'])
					self.update(existing, patient_data)
					updated += 1
				else:
					# Create new patient
					if created_by:
						patient_data['createdBy'] = created_by
					self.create(patient_data)
					imported += 1

			except Exception as e:
				Logger.error(f'Error importing row {idx}: {e!s}')
				failed += 1
				failed_rows.append({**dict(row), '_error': str(e)})

		# Save failed rows to CSV if any
		failed_file = None
		if failed_rows:
			results_dir = Path(settings.MEDIA_ROOT) / 'patients' / 'importResults'
			results_dir.mkdir(parents=True, exist_ok=True)

			timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
			failed_file = results_dir / f'failed_import_{timestamp}.csv'

			failed_df = pd.DataFrame(failed_rows)
			failed_df.to_csv(failed_file, index=False)
			failed_file = str(failed_file.relative_to(settings.MEDIA_ROOT))

		Logger.info(f'Import complete: {imported} imported, {updated} updated, {skipped} skipped, {failed} failed')

		return {
			'status': 'complete',
			'imported': imported,
			'updated': updated,
			'skipped': skipped,
			'failed': failed,
			'failed_rows_file': failed_file,
		}

	def previewMatching(self, file_url: str, column_mapping: dict = None) -> dict:
		"""
		Preview patient matching with stats before download.
		
		Returns:
			Dictionary with preview data and matching stats
		"""
		Logger.info(f'Previewing patient matching for: {file_url}')

		# Resolve file path
		if file_url.startswith('/media/'):
			file_path = Path(settings.MEDIA_ROOT) / file_url.replace('/media/', '')
		elif file_url.startswith('media/'):
			file_path = Path(settings.MEDIA_ROOT) / file_url.replace('media/', '')
		else:
			file_path = Path(settings.MEDIA_ROOT) / file_url

		if not file_path.exists():
			raise ValueError(f'File not found: {file_path}')

		# Read the file
		try:
			if str(file_path).endswith('.xlsx') or str(file_path).endswith('.xls'):
				df = pd.read_excel(file_path)
			else:
				df = pd.read_csv(file_path)
		except Exception as e:
			raise ValueError(f'Error reading file: {e!s}')

		df.columns = [col.strip() for col in df.columns]
		columns = list(df.columns)

		# Auto-detect column mapping
		if column_mapping is None:
			column_mapping = {}

		detected_mapping = {}
		field_patterns = {
			'firstName': ['firstname', 'first_name', 'fname', 'first', 'given_name', 'patient_first', 'patientfirst'],
			'lastName': ['lastname', 'last_name', 'lname', 'last', 'surname', 'family_name', 'patient_last', 'patientlast'],
			'dateOfBirth': ['dateofbirth', 'date_of_birth', 'dob', 'birthdate', 'birth_date', 'birthday', 'patient_dob'],
			'gender': ['gender', 'sex', 'patient_gender'],
		}

		for field, patterns in field_patterns.items():
			if field not in column_mapping:
				for col in columns:
					col_lower = col.lower().replace(' ', '_').replace('-', '_')
					if col_lower in patterns or col.lower() in patterns:
						detected_mapping[field] = col
						break

		final_mapping = {**detected_mapping, **column_mapping}

		# Process rows for preview (first 20)
		preview_rows = []
		matched_count = 0
		unmatched_count = 0

		for idx, row in df.iterrows():
			# Extract fields
			first_name = ''
			last_name = ''
			dob = ''
			gender = ''

			if 'firstName' in final_mapping and final_mapping['firstName'] in row:
				first_name = str(row[final_mapping['firstName']]) if pd.notna(row[final_mapping['firstName']]) else ''
			if 'lastName' in final_mapping and final_mapping['lastName'] in row:
				last_name = str(row[final_mapping['lastName']]) if pd.notna(row[final_mapping['lastName']]) else ''
			if 'dateOfBirth' in final_mapping and final_mapping['dateOfBirth'] in row:
				dob = str(row[final_mapping['dateOfBirth']]) if pd.notna(row[final_mapping['dateOfBirth']]) else ''
			if 'gender' in final_mapping and final_mapping['gender'] in row:
				gender = str(row[final_mapping['gender']]) if pd.notna(row[final_mapping['gender']]) else ''

			# Try to match
			match = None
			if first_name.strip() or last_name.strip():
				match = self._findBestMatchingPatient(first_name, last_name, dob, gender)

			if match:
				matched_count += 1
			else:
				unmatched_count += 1

			# Build preview row (first 20 only)
			if idx < 20:
				row_data = {}
				for col in columns:
					row_data[col] = str(row[col]) if pd.notna(row[col]) else ''
				row_data['_matched'] = match is not None
				row_data['_match_id'] = match['id'] if match else None
				row_data['_match_name'] = match.get('fullName', '') if match else ''
				preview_rows.append(row_data)

		total_rows = len(df)

		return {
			'total_rows': total_rows,
			'columns': columns,
			'detected_mapping': detected_mapping,
			'final_mapping': final_mapping,
			'preview_rows': preview_rows,
			'stats': {
				'total': total_rows,
				'matched': matched_count,
				'unmatched': unmatched_count,
				'match_rate': round((matched_count / total_rows * 100), 1) if total_rows > 0 else 0,
			},
		}

	def matchPatientsForDownload(self, file_url: str, column_mapping: dict = None) -> dict:
		"""
		Match all patients and prepare data for streaming download.
		
		Returns:
			Dictionary with columns, rows (generator), stats, and timestamp
		"""
		Logger.info(f'Processing patient matching for download: {file_url}')

		# Resolve file path
		if file_url.startswith('/media/'):
			file_path = Path(settings.MEDIA_ROOT) / file_url.replace('/media/', '')
		elif file_url.startswith('media/'):
			file_path = Path(settings.MEDIA_ROOT) / file_url.replace('media/', '')
		else:
			file_path = Path(settings.MEDIA_ROOT) / file_url

		if not file_path.exists():
			raise ValueError(f'File not found: {file_path}')

		# Read the file
		try:
			if str(file_path).endswith('.xlsx') or str(file_path).endswith('.xls'):
				df = pd.read_excel(file_path)
			else:
				df = pd.read_csv(file_path)
		except Exception as e:
			raise ValueError(f'Error reading file: {e!s}')

		df.columns = [col.strip() for col in df.columns]
		original_columns = list(df.columns)

		# Auto-detect column mapping
		if column_mapping is None:
			column_mapping = {}

		detected_mapping = {}
		field_patterns = {
			'firstName': ['firstname', 'first_name', 'fname', 'first', 'given_name'],
			'lastName': ['lastname', 'last_name', 'lname', 'last', 'surname', 'family_name'],
			'dateOfBirth': ['dateofbirth', 'date_of_birth', 'dob', 'birthdate', 'birth_date', 'birthday'],
			'gender': ['gender', 'sex'],
		}

		for field, patterns in field_patterns.items():
			if field not in column_mapping:
				for col in original_columns:
					col_lower = col.lower().replace(' ', '_').replace('-', '_')
					if col_lower in patterns or col.lower() in patterns:
						detected_mapping[field] = col
						break

		final_mapping = {**detected_mapping, **column_mapping}

		# Output columns: original + matched patient info
		output_columns = original_columns + [
			'matched_patient_id',
			'matched_patient_firstName',
			'matched_patient_lastName',
			'matched_patient_fullName',
			'matched_patient_dateOfBirth',
			'matched_patient_gender',
			'match_status',
		]

		# Process all rows
		matched_count = 0
		rows = []

		for idx, row in df.iterrows():
			# Build output row with original data
			output_row = {}
			for col in original_columns:
				output_row[col] = str(row[col]) if pd.notna(row[col]) else ''

			# Extract fields for matching
			first_name = ''
			last_name = ''
			dob = ''
			gender = ''

			if 'firstName' in final_mapping and final_mapping['firstName'] in row:
				first_name = str(row[final_mapping['firstName']]) if pd.notna(row[final_mapping['firstName']]) else ''
			if 'lastName' in final_mapping and final_mapping['lastName'] in row:
				last_name = str(row[final_mapping['lastName']]) if pd.notna(row[final_mapping['lastName']]) else ''
			if 'dateOfBirth' in final_mapping and final_mapping['dateOfBirth'] in row:
				dob = str(row[final_mapping['dateOfBirth']]) if pd.notna(row[final_mapping['dateOfBirth']]) else ''
			if 'gender' in final_mapping and final_mapping['gender'] in row:
				gender = str(row[final_mapping['gender']]) if pd.notna(row[final_mapping['gender']]) else ''

			# Try to match
			match = None
			if first_name.strip() or last_name.strip():
				match = self._findBestMatchingPatient(first_name, last_name, dob, gender)

			# Add matched patient info
			if match:
				matched_count += 1
				output_row['matched_patient_id'] = str(match['id'])
				output_row['matched_patient_firstName'] = match.get('firstName', '')
				output_row['matched_patient_lastName'] = match.get('lastName', '')
				output_row['matched_patient_fullName'] = match.get('fullName', '')
				output_row['matched_patient_dateOfBirth'] = match.get('dateOfBirth', '')
				output_row['matched_patient_gender'] = match.get('gender', '')
				output_row['match_status'] = 'MATCHED'
			else:
				output_row['matched_patient_id'] = ''
				output_row['matched_patient_firstName'] = ''
				output_row['matched_patient_lastName'] = ''
				output_row['matched_patient_fullName'] = ''
				output_row['matched_patient_dateOfBirth'] = ''
				output_row['matched_patient_gender'] = ''
				output_row['match_status'] = 'NOT_MATCHED'

			rows.append(output_row)

		total_rows = len(df)
		timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

		Logger.info(f'Matching complete: {matched_count}/{total_rows} matched')

		return {
			'columns': output_columns,
			'rows': rows,
			'timestamp': timestamp,
			'stats': {
				'total': total_rows,
				'matched': matched_count,
				'unmatched': total_rows - matched_count,
				'match_rate': round((matched_count / total_rows * 100), 1) if total_rows > 0 else 0,
			},
		}

