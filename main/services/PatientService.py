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

		# Read the uploaded file with encoding fallback
		try:
			if str(file_path).endswith('.xlsx') or str(file_path).endswith('.xls'):
				df = pd.read_excel(file_path)
			else:
				encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
				df = None
				for encoding in encodings_to_try:
					try:
						df = pd.read_csv(file_path, encoding=encoding)
						break
					except UnicodeDecodeError:
						continue
				if df is None:
					raise ValueError('Could not read file with any supported encoding')
		except ValueError:
			raise
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

	def _findBestMatchingPatient(self, firstname: str, lastname: str, dateofbirth: str = '', gender: str = '', latitude: str = '', longitude: str = '') -> dict:
		"""
		Find the best matching patient based on name, DOB, gender, and/or location.
		Uses fullName matching with stripped name parts, or location-based matching.
		
		Returns:
			Dictionary with patient data or None if no match found
		"""
		# Check if we have any search criteria
		has_name = bool(firstname and firstname.strip())
		has_location = False
		lat_float = None
		lng_float = None

		try:
			if latitude and longitude:
				lat_float = float(latitude)
				lng_float = float(longitude)
				has_location = True
		except (ValueError, TypeError):
			pass

		if not has_name and not has_location:
			return None

		# Strip and split names
		firstname_parts = [p.strip() for p in re.split(r'[\s\-]+', firstname.strip()) if p.strip()] if firstname else []
		lastname_parts = [p.strip() for p in re.split(r'[\s\-]+', lastname.strip()) if p.strip()] if lastname else []

		# Build query for name matching using fullName
		candidates = None
		if has_name:
			name_query = Q()
			for first_part in firstname_parts:
				if first_part:
					name_query |= Q(fullName__icontains=first_part)
			for last_part in lastname_parts:
				if last_part:
					name_query |= Q(fullName__icontains=last_part)

			if name_query:
				candidates = self.model.objects.filter(name_query).distinct()

		# If no name search or no name candidates, try location matching
		if candidates is None or (not candidates.exists() and has_location):
			if has_location:
				# Find patients within ~1km radius using simple bounding box
				# 0.01 degrees ≈ 1.1km at equator
				RADIUS = 0.01
				candidates = self.model.objects.filter(
					latitude__gte=lat_float - RADIUS,
					latitude__lte=lat_float + RADIUS,
					longitude__gte=lng_float - RADIUS,
					longitude__lte=lng_float + RADIUS,
				)

		if candidates is None or not candidates.exists():
			return None

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
					filtered = candidates.filter(dateOfBirth=dob)
					if filtered.exists():
						candidates = filtered
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
				filtered = candidates.filter(gender=gender_map[gender_upper])
				if filtered.exists():
					candidates = filtered

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

			# Bonus for location proximity
			if has_location and patient.latitude and patient.longitude:
				try:
					dist = abs(lat_float - patient.latitude) + abs(lng_float - patient.longitude)
					if dist < 0.0001:  # Very close match
						score += 15
					elif dist < 0.001:
						score += 10
					elif dist < 0.01:
						score += 5
				except (TypeError, ValueError):
					pass

			if score > 0 or has_location:  # Location-only matches still count
				scored_candidates.append((max(score, 1), patient))

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
				latitude=best_patient.latitude,
				longitude=best_patient.longitude,
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

		# Read the file with encoding fallback
		try:
			if str(file_path).endswith('.xlsx') or str(file_path).endswith('.xls'):
				df = pd.read_excel(file_path)
			else:
				# Try multiple encodings for CSV files
				encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
				df = None
				last_error = None
				for encoding in encodings_to_try:
					try:
						df = pd.read_csv(file_path, encoding=encoding)
						Logger.info(f'Successfully read CSV with encoding: {encoding}')
						break
					except UnicodeDecodeError as enc_error:
						last_error = enc_error
						continue
				if df is None:
					raise ValueError(f'Could not read file with any encoding. Last error: {last_error}')
		except ValueError:
			raise
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
			'firstName': ['firstname', 'first_name', 'fname', 'first', 'given_name', 'patient_first', 'patientfirst'],
			'lastName': ['lastname', 'last_name', 'lname', 'last', 'surname', 'family_name', 'patient_last', 'patientlast'],
			'dateOfBirth': ['dateofbirth', 'date_of_birth', 'dob', 'birthdate', 'birth_date', 'birthday', 'patient_dob'],
			'age': ['age', 'patient_age', 'years_old', 'yearsold'],
			'gender': ['gender', 'sex', 'patient_gender'],
			'latitude': ['latitude', 'lat', 'patient_lat', 'location_lat', 'gps_lat', 'y_coord'],
			'longitude': ['longitude', 'long', 'lng', 'patient_long', 'location_long', 'gps_long', 'x_coord'],
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
			age = ''
			gender = ''
			latitude = ''
			longitude = ''

			if 'firstName' in final_mapping and final_mapping['firstName'] in row:
				first_name = str(row[final_mapping['firstName']]) if pd.notna(row[final_mapping['firstName']]) else ''
			if 'lastName' in final_mapping and final_mapping['lastName'] in row:
				last_name = str(row[final_mapping['lastName']]) if pd.notna(row[final_mapping['lastName']]) else ''
			if 'dateOfBirth' in final_mapping and final_mapping['dateOfBirth'] in row:
				dob = str(row[final_mapping['dateOfBirth']]) if pd.notna(row[final_mapping['dateOfBirth']]) else ''
			if 'age' in final_mapping and final_mapping['age'] in row:
				age = str(row[final_mapping['age']]) if pd.notna(row[final_mapping['age']]) else ''
			if 'gender' in final_mapping and final_mapping['gender'] in row:
				gender = str(row[final_mapping['gender']]) if pd.notna(row[final_mapping['gender']]) else ''
			if 'latitude' in final_mapping and final_mapping['latitude'] in row:
				latitude = str(row[final_mapping['latitude']]) if pd.notna(row[final_mapping['latitude']]) else ''
			if 'longitude' in final_mapping and final_mapping['longitude'] in row:
				longitude = str(row[final_mapping['longitude']]) if pd.notna(row[final_mapping['longitude']]) else ''

			# If age provided but not DOB, create fake DOB (Jan 1 of calculated birth year)
			if age and not dob:
				try:
					age_int = int(float(age))
					birth_year = datetime.now().year - age_int
					dob = f'{birth_year}-01-01'
				except (ValueError, TypeError):
					pass  # Invalid age format

			# Check if we have valid identifiers
			has_name = bool(first_name.strip() or last_name.strip())
			has_location = bool(latitude.strip() and longitude.strip())

			# Validate - need either name OR coordinates
			if not has_name and not has_location:
				validation_errors.append({
					'row_index': idx,
					'error': 'Missing both name and location coordinates',
				})

			# Check for duplicates (by name or location)
			if has_name or has_location:
				match = self._findBestMatchingPatient(first_name, last_name, dob, gender, latitude, longitude)
				if match:
					# Calculate confidence based on match score
					confidence = 0.3  # Base confidence
					if first_name.strip() and match.get('firstName', '').lower() == first_name.strip().lower():
						confidence += 0.25
					if last_name.strip() and match.get('lastName', '').lower() == last_name.strip().lower():
						confidence += 0.15
					if dob and match.get('dateOfBirth') == dob:
						confidence += 0.2
					if gender and match.get('gender', '').upper() == gender.upper():
						confidence += 0.1
					# Location proximity boost
					if has_location and match.get('latitude') and match.get('longitude'):
						try:
							lat_m = float(match.get('latitude'))
							lng_m = float(match.get('longitude'))
							lat_f = float(latitude)
							lng_f = float(longitude)
							if abs(lat_m - lat_f) < 0.001 and abs(lng_m - lng_f) < 0.001:
								confidence += 0.2
						except (ValueError, TypeError):
							pass

					duplicates.append({
						'row_index': idx,
						'match_patient_id': match['id'],
						'match_confidence': round(min(confidence, 1.0), 2),
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

		# Read the file with encoding fallback
		try:
			if str(file_path).endswith('.xlsx') or str(file_path).endswith('.xls'):
				df = pd.read_excel(file_path)
			else:
				encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
				df = None
				for encoding in encodings_to_try:
					try:
						df = pd.read_csv(file_path, encoding=encoding)
						break
					except UnicodeDecodeError:
						continue
				if df is None:
					raise ValueError('Could not read file with any supported encoding')
		except ValueError:
			raise
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
				latitude_str = ''
				longitude_str = ''

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

				# Handle age -> DOB conversion
				if 'age' in column_mapping and column_mapping['age'] in row and 'dateOfBirth' not in patient_data:
					val = row[column_mapping['age']]
					if pd.notna(val):
						try:
							age_int = int(float(str(val).strip()))
							birth_year = datetime.now().year - age_int
							patient_data['dateOfBirth'] = datetime(birth_year, 1, 1).date()
						except (ValueError, TypeError):
							pass

				if 'gender' in column_mapping and column_mapping['gender'] in row:
					val = row[column_mapping['gender']]
					if pd.notna(val):
						gender_str = str(val).upper().strip()
						gender_map = {'M': 'MALE', 'MALE': 'MALE', 'F': 'FEMALE', 'FEMALE': 'FEMALE', 'O': 'OTHER', 'OTHER': 'OTHER'}
						patient_data['gender'] = gender_map.get(gender_str, '')

				if 'notes' in column_mapping and column_mapping['notes'] in row:
					val = row[column_mapping['notes']]
					patient_data['notes'] = str(val).strip() if pd.notna(val) else ''

				# Handle latitude and longitude
				if 'latitude' in column_mapping and column_mapping['latitude'] in row:
					val = row[column_mapping['latitude']]
					if pd.notna(val):
						latitude_str = str(val).strip()
						try:
							patient_data['latitude'] = float(latitude_str)
						except (ValueError, TypeError):
							pass

				if 'longitude' in column_mapping and column_mapping['longitude'] in row:
					val = row[column_mapping['longitude']]
					if pd.notna(val):
						longitude_str = str(val).strip()
						try:
							patient_data['longitude'] = float(longitude_str)
						except (ValueError, TypeError):
							pass

				# Check if we have valid identifiers
				has_name = bool(patient_data.get('firstName') or patient_data.get('lastName'))
				has_location = bool(patient_data.get('latitude') and patient_data.get('longitude'))

				# Validate - need either name OR coordinates
				if not has_name and not has_location:
					failed += 1
					failed_rows.append({**dict(row), '_error': 'Missing both name and location'})
					continue

				# Check action for this row
				action = duplicate_actions.get(str(idx), duplicate_actions.get('default', 'create'))

				# Check for existing patient
				match = self._findBestMatchingPatient(
					patient_data.get('firstName', ''),
					patient_data.get('lastName', ''),
					str(patient_data.get('dateOfBirth', '')),
					patient_data.get('gender', ''),
					latitude_str,
					longitude_str,
				)

				if match and action == 'skip':
					# Auto-fill empty fields in existing patient with import data
					existing = self.getById(match['id'])
					update_data = {}
					if not existing.dateOfBirth and patient_data.get('dateOfBirth'):
						update_data['dateOfBirth'] = patient_data['dateOfBirth']
					if not existing.gender and patient_data.get('gender'):
						update_data['gender'] = patient_data['gender']
					if not existing.latitude and patient_data.get('latitude'):
						update_data['latitude'] = patient_data['latitude']
					if not existing.longitude and patient_data.get('longitude'):
						update_data['longitude'] = patient_data['longitude']
					if not existing.notes and patient_data.get('notes'):
						update_data['notes'] = patient_data['notes']

					if update_data:
						self.update(existing, update_data)
						updated += 1
					else:
						skipped += 1
					continue
				if match and action == 'update':
					# Update existing patient with all import data
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

		# Read the file with encoding fallback
		try:
			if str(file_path).endswith('.xlsx') or str(file_path).endswith('.xls'):
				df = pd.read_excel(file_path)
			else:
				encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
				df = None
				for encoding in encodings_to_try:
					try:
						df = pd.read_csv(file_path, encoding=encoding)
						break
					except UnicodeDecodeError:
						continue
				if df is None:
					raise ValueError('Could not read file with any supported encoding')
		except ValueError:
			raise
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
			'age': ['age', 'patient_age', 'years_old', 'yearsold'],
			'gender': ['gender', 'sex', 'patient_gender'],
			'latitude': ['latitude', 'lat', 'patient_lat', 'location_lat', 'gps_lat', 'y_coord'],
			'longitude': ['longitude', 'long', 'lng', 'patient_long', 'location_long', 'gps_long', 'x_coord'],
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
			age = ''
			gender = ''
			latitude = ''
			longitude = ''

			if 'firstName' in final_mapping and final_mapping['firstName'] in row:
				first_name = str(row[final_mapping['firstName']]) if pd.notna(row[final_mapping['firstName']]) else ''
			if 'lastName' in final_mapping and final_mapping['lastName'] in row:
				last_name = str(row[final_mapping['lastName']]) if pd.notna(row[final_mapping['lastName']]) else ''
			if 'dateOfBirth' in final_mapping and final_mapping['dateOfBirth'] in row:
				dob = str(row[final_mapping['dateOfBirth']]) if pd.notna(row[final_mapping['dateOfBirth']]) else ''
			if 'age' in final_mapping and final_mapping['age'] in row:
				age = str(row[final_mapping['age']]) if pd.notna(row[final_mapping['age']]) else ''
			if 'gender' in final_mapping and final_mapping['gender'] in row:
				gender = str(row[final_mapping['gender']]) if pd.notna(row[final_mapping['gender']]) else ''
			if 'latitude' in final_mapping and final_mapping['latitude'] in row:
				latitude = str(row[final_mapping['latitude']]) if pd.notna(row[final_mapping['latitude']]) else ''
			if 'longitude' in final_mapping and final_mapping['longitude'] in row:
				longitude = str(row[final_mapping['longitude']]) if pd.notna(row[final_mapping['longitude']]) else ''

			# If age provided but not DOB, create fake DOB
			if age and not dob:
				try:
					age_int = int(float(age))
					birth_year = datetime.now().year - age_int
					dob = f'{birth_year}-01-01'
				except (ValueError, TypeError):
					pass

			# Check identifiers
			has_name = bool(first_name.strip() or last_name.strip())
			has_location = bool(latitude.strip() and longitude.strip())

			# Try to match
			match = None
			if has_name or has_location:
				match = self._findBestMatchingPatient(first_name, last_name, dob, gender, latitude, longitude)

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

		# Read the file with encoding fallback
		try:
			if str(file_path).endswith('.xlsx') or str(file_path).endswith('.xls'):
				df = pd.read_excel(file_path)
			else:
				encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
				df = None
				for encoding in encodings_to_try:
					try:
						df = pd.read_csv(file_path, encoding=encoding)
						break
					except UnicodeDecodeError:
						continue
				if df is None:
					raise ValueError('Could not read file with any supported encoding')
		except ValueError:
			raise
		except Exception as e:
			raise ValueError(f'Error reading file: {e!s}')

		df.columns = [col.strip() for col in df.columns]
		original_columns = list(df.columns)

		# Auto-detect column mapping
		if column_mapping is None:
			column_mapping = {}

		detected_mapping = {}
		field_patterns = {
			'firstName': ['firstname', 'first_name', 'fname', 'first', 'given_name', 'patient_first', 'patientfirst'],
			'lastName': ['lastname', 'last_name', 'lname', 'last', 'surname', 'family_name', 'patient_last', 'patientlast'],
			'dateOfBirth': ['dateofbirth', 'date_of_birth', 'dob', 'birthdate', 'birth_date', 'birthday', 'patient_dob'],
			'age': ['age', 'patient_age', 'years_old', 'yearsold'],
			'gender': ['gender', 'sex', 'patient_gender'],
			'latitude': ['latitude', 'lat', 'patient_lat', 'location_lat', 'gps_lat', 'y_coord'],
			'longitude': ['longitude', 'long', 'lng', 'patient_long', 'location_long', 'gps_long', 'x_coord'],
		}

		for field, patterns in field_patterns.items():
			if field not in column_mapping:
				for col in original_columns:
					col_lower = col.lower().replace(' ', '_').replace('-', '_')
					if col_lower in patterns or col.lower() in patterns:
						detected_mapping[field] = col
						break

		final_mapping = {**detected_mapping, **column_mapping}

		# Build output columns: match metadata FIRST, then ALL original columns,
		# with matched_* columns placed next to their corresponding input columns
		base_columns = [
			'row_number',
			'match_status',
			'match_confidence',
			'matched_patient_id',
			'file_duplicate_of_row',  # If this row is a duplicate of another row in the file
			'file_patient_group',     # Group ID to identify same patients in file
		]

		# Map field keys to their matched column names
		field_to_matched_col = {
			'firstName': 'matched_firstName',
			'lastName': 'matched_lastName',
			'dateOfBirth': 'matched_dateOfBirth',
			'age': 'matched_age',
			'gender': 'matched_gender',
			'latitude': 'matched_latitude',
			'longitude': 'matched_longitude',
		}

		# Track which mapped fields need matched columns
		mapped_fields_ordered = []
		for field_key in ['firstName', 'lastName', 'dateOfBirth', 'age', 'gender', 'latitude', 'longitude']:
			if field_key in final_mapping:
				input_col = final_mapping[field_key]
				matched_col = field_to_matched_col[field_key]
				mapped_fields_ordered.append((field_key, input_col, matched_col))

		# Build output columns: base + original columns with matched columns inserted after mapped ones
		output_columns = base_columns.copy()
		mapped_input_cols = {item[1]: item[2] for item in mapped_fields_ordered}  # input_col -> matched_col

		for col in original_columns:
			output_columns.append(col)
			# If this column is mapped, add its matched column right after
			if col in mapped_input_cols:
				output_columns.append(mapped_input_cols[col])

		# Track patients seen in this file for duplicate detection
		# Key: signature (normalized name + dob/age), Value: first row index
		seen_patients = {}
		patient_groups = {}  # Track group assignments
		next_group_id = 1

		# Process all rows
		matched_count = 0
		file_duplicate_count = 0
		rows = []

		for idx, row in df.iterrows():
			row_number = idx + 2  # Excel row number (1-indexed + header)

			# Extract fields for matching
			first_name = ''
			last_name = ''
			dob = ''
			age = ''
			gender = ''
			latitude = ''
			longitude = ''

			if 'firstName' in final_mapping and final_mapping['firstName'] in row:
				first_name = str(row[final_mapping['firstName']]) if pd.notna(row[final_mapping['firstName']]) else ''
			if 'lastName' in final_mapping and final_mapping['lastName'] in row:
				last_name = str(row[final_mapping['lastName']]) if pd.notna(row[final_mapping['lastName']]) else ''
			if 'dateOfBirth' in final_mapping and final_mapping['dateOfBirth'] in row:
				dob = str(row[final_mapping['dateOfBirth']]) if pd.notna(row[final_mapping['dateOfBirth']]) else ''
			if 'age' in final_mapping and final_mapping['age'] in row:
				age = str(row[final_mapping['age']]) if pd.notna(row[final_mapping['age']]) else ''
			if 'gender' in final_mapping and final_mapping['gender'] in row:
				gender = str(row[final_mapping['gender']]) if pd.notna(row[final_mapping['gender']]) else ''
			if 'latitude' in final_mapping and final_mapping['latitude'] in row:
				latitude = str(row[final_mapping['latitude']]) if pd.notna(row[final_mapping['latitude']]) else ''
			if 'longitude' in final_mapping and final_mapping['longitude'] in row:
				longitude = str(row[final_mapping['longitude']]) if pd.notna(row[final_mapping['longitude']]) else ''

			# If age provided but not DOB, create fake DOB
			effective_dob = dob
			if age and not dob:
				try:
					age_int = int(float(age))
					birth_year = datetime.now().year - age_int
					effective_dob = f'{birth_year}-01-01'
				except (ValueError, TypeError):
					pass

			# Create a signature for within-file duplicate detection
			# Use normalized name + dob/age + location
			sig_parts = []
			if first_name.strip():
				sig_parts.append(first_name.strip().lower())
			if last_name.strip():
				sig_parts.append(last_name.strip().lower())
			if effective_dob:
				sig_parts.append(effective_dob)
			elif age:
				sig_parts.append(f'age:{age}')
			if latitude.strip() and longitude.strip():
				# Round coordinates for grouping
				try:
					sig_parts.append(f'loc:{round(float(latitude), 3)},{round(float(longitude), 3)}')
				except (ValueError, TypeError):
					pass

			patient_signature = '|'.join(sig_parts) if sig_parts else None

			# Check for within-file duplicates
			file_duplicate_of = ''
			file_group = ''
			if patient_signature:
				if patient_signature in seen_patients:
					# This is a duplicate of an earlier row
					first_row = seen_patients[patient_signature]
					file_duplicate_of = str(first_row)
					file_duplicate_count += 1
					# Use same group as first occurrence
					file_group = patient_groups.get(patient_signature, '')
				else:
					# First occurrence - record it
					seen_patients[patient_signature] = row_number
					# Assign a new group ID
					file_group = f'G{next_group_id}'
					patient_groups[patient_signature] = file_group
					next_group_id += 1

			# Check identifiers for database matching
			has_name = bool(first_name.strip() or last_name.strip())
			has_location = bool(latitude.strip() and longitude.strip())

			# Try to match against database
			match = None
			if has_name or has_location:
				match = self._findBestMatchingPatient(first_name, last_name, effective_dob, gender, latitude, longitude)

			# Build output row
			output_row = {
				'row_number': row_number,
				'file_duplicate_of_row': file_duplicate_of,
				'file_patient_group': file_group,
			}

			if match:
				matched_count += 1
				# Calculate confidence score
				confidence = 0.3
				if first_name.strip() and match.get('firstName', '').lower() == first_name.strip().lower():
					confidence += 0.25
				if last_name.strip() and match.get('lastName', '').lower() == last_name.strip().lower():
					confidence += 0.15
				if effective_dob and match.get('dateOfBirth') == effective_dob:
					confidence += 0.2
				if has_location and match.get('latitude') and match.get('longitude'):
					try:
						lat_diff = abs(float(latitude) - float(match.get('latitude', 0)))
						lng_diff = abs(float(longitude) - float(match.get('longitude', 0)))
						if lat_diff < 0.001 and lng_diff < 0.001:
							confidence += 0.2
					except (ValueError, TypeError):
						pass

				output_row['match_status'] = 'MATCHED'
				output_row['match_confidence'] = f'{min(confidence, 1.0):.0%}'
				output_row['matched_patient_id'] = str(match['id'])
			else:
				output_row['match_status'] = 'NOT_MATCHED'
				output_row['match_confidence'] = ''
				output_row['matched_patient_id'] = ''

			# Add paired columns (input value next to matched value)
			matched_values = {
				'firstName': match.get('firstName', '') if match else '',
				'lastName': match.get('lastName', '') if match else '',
				'dateOfBirth': match.get('dateOfBirth', '') if match else '',
				'age': '',  # We don't store age directly, show empty
				'gender': match.get('gender', '') if match else '',
				'latitude': str(match.get('latitude', '')) if match and match.get('latitude') else '',
				'longitude': str(match.get('longitude', '')) if match and match.get('longitude') else '',
			}

			# Add ALL original columns to output row
			for col in original_columns:
				output_row[col] = str(row[col]) if pd.notna(row[col]) else ''
				# If this column is mapped, also add its matched value
				if col in mapped_input_cols:
					matched_col = mapped_input_cols[col]
					# Find which field key this corresponds to
					for field_key, input_c, matched_c in mapped_fields_ordered:
						if input_c == col:
							output_row[matched_col] = matched_values.get(field_key, '')
							break

			rows.append(output_row)

		total_rows = len(df)
		timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

		Logger.info(f'Matching complete: {matched_count}/{total_rows} matched, {file_duplicate_count} in-file duplicates found')

		return {
			'columns': output_columns,
			'rows': rows,
			'timestamp': timestamp,
			'stats': {
				'total': total_rows,
				'matched': matched_count,
				'unmatched': total_rows - matched_count,
				'match_rate': round((matched_count / total_rows * 100), 1) if total_rows > 0 else 0,
				'file_duplicates': file_duplicate_count,
				'unique_patients': next_group_id - 1,
			},
		}

