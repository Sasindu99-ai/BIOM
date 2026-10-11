import contextlib
import re
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from django.conf import settings
from django.db.models import Case, Count, ExpressionWrapper, F, IntegerField, Value, When
from django.db.models.functions import ExtractDay, ExtractMonth, ExtractYear, Now
from django.utils import timezone

from authentication.enums import Gender
from vvecon.zorion.core import Service
from vvecon.zorion.logger import Logger

from ..models import Patient

__all__ = ['PatientService']


class PatientService(Service):
	model = Patient
	searchableFields = ('fullName', 'notes', 'reference')
	filterableFields = ('dateOfBirth', 'gender', 'createdBy', 'age', 'reference')
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

	def matchPatientsFromFile(self, file_url: str, column_mapping: dict | None = None) -> str:  # noqa: PLR0915, PLR0912, C901
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

		# Resolve file path, rejecting paths that escape MEDIA_ROOT
		relative = file_url
		if relative.startswith('/media/'):
			relative = relative.replace('/media/', '', 1)
		elif relative.startswith('media/'):
			relative = relative.replace('media/', '', 1)

		media_root = Path(settings.MEDIA_ROOT).resolve()
		file_path = (media_root / relative).resolve()

		if file_path != media_root and media_root not in file_path.parents:
			raise ValueError(f'Invalid file path: {file_url}')

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
		optional_fields = ['reference', 'lastName', 'dateOfBirth', 'gender']

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
					'reference': [
						'reference', 'ref', 'patient_reference', 'patient_ref', 'patientid', 'patient_id', 'mrn',
					],
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
					value = row.get(col, None)
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
					value = row.get(col, None)
					row_original[col] = str(value) if pd.notna(value) else ''

				# Try to match with existing patients
				matched_patient = self._findBestMatchingPatient(
					row_data.get('firstName', ''),
					row_data.get('lastName', ''),
					row_data.get('dateOfBirth', ''),
					row_data.get('gender', ''),
					reference=row_data.get('reference', ''),
				)

				# Build result row - order: user columns, matched patient id, matched patient data
				result_row = dict()

				# Add all original columns first
				for col in original_columns:
					result_row[col] = row_original.get(col, '')

				# Add matched patient id and reference
				result_row['matched_patient_id'] = matched_patient['id'] if matched_patient else ''
				result_row['matched_patient_reference'] = (
					matched_patient.get('reference', '') if matched_patient else ''
				)

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

		timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # noqa: DTZ005
		results_file = results_dir / f'match_results_{timestamp}.csv'

		results_df.to_csv(results_file, index=False)

		Logger.info(
			f'Match results saved to: {results_file}. Processed {len(results)} rows, '
			f'skipped {len(skipped_rows)} rows.',
		)

		# Return relative path from MEDIA_ROOT
		return str(results_file.relative_to(settings.MEDIA_ROOT))

	def _parseDate(self, val) -> date | None:
		"""Safely parse various date formats and types (Timestamp, datetime, strings)."""
		if val is None or pd.isna(val):
			return None
		if isinstance(val, (datetime, pd.Timestamp)):
			return val.date()
		if isinstance(val, date):
			return val

		val_str = str(val).strip()
		if not val_str or val_str.lower() in ('nan', 'none', 'null', 'nat', ''):
			return None

		# Strip time suffix if present (e.g. 1985-06-15 00:00:00 or 1985-06-15T00:00:00)
		if ' ' in val_str:
			val_str = val_str.split(' ')[0].strip()
		elif 'T' in val_str:
			val_str = val_str.split('T')[0].strip()

		formats = [
			'%Y-%m-%d',
			'%d/%m/%Y',
			'%m/%d/%Y',
			'%Y/%m/%d',
			'%d-%m-%Y',
			'%m-%d-%Y',
			'%Y.%m.%d',
			'%d.%m.%Y',
		]
		for fmt in formats:
			try:
				return datetime.strptime(val_str, fmt).date()  # noqa: DTZ007
			except (ValueError, TypeError):
				continue
		return None

	def _normalizeGender(self, val) -> str:
		"""Normalize gender value to valid Gender choices."""
		if val is None or pd.isna(val):
			return Gender.PREFER_NOT_TO_SAY.value
		val_str = str(val).strip().upper()
		if not val_str or val_str in ('NAN', 'NONE', 'NULL', ''):
			return Gender.PREFER_NOT_TO_SAY.value
		if val_str in ('M', 'MALE', 'MAN', 'BOY'):
			return Gender.MALE.value
		if val_str in ('F', 'FEMALE', 'WOMAN', 'GIRL'):
			return Gender.FEMALE.value
		return Gender.PREFER_NOT_TO_SAY.value

	def _cleanString(self, val) -> str:
		"""Clean string value, treating NaN / None / null as empty."""
		if val is None or pd.isna(val):
			return ''
		s = str(val).strip()
		if s.lower() in ('nan', 'none', 'null', ''):
			return ''
		return s

	def _parseFloat(self, val) -> float | None:
		"""Safely parse float value (e.g. latitude, longitude)."""
		if val is None or pd.isna(val):
			return None
		s = str(val).strip()
		if s.lower() in ('nan', 'none', 'null', ''):
			return None
		try:
			return float(s)
		except (ValueError, TypeError):
			return None

	def _resolveFilePath(self, file_url: str) -> Path:
		"""Resolve file path safely within MEDIA_ROOT."""
		relative = file_url
		if relative.startswith('/media/'):
			relative = relative.replace('/media/', '', 1)
		elif relative.startswith('media/'):
			relative = relative.replace('media/', '', 1)

		media_root = Path(settings.MEDIA_ROOT).resolve()
		file_path = (media_root / relative).resolve()

		if file_path != media_root and media_root not in file_path.parents:
			raise ValueError(f'Invalid file path: {file_url}')

		if not file_path.exists():
			raise ValueError(f'File not found: {file_path}')

		return file_path

	def _patientToDict(self, patient) -> dict:
		return dict(
			id=patient.id,
			reference=patient.reference or '',
			firstName=patient.firstName or '',
			lastName=patient.lastName or '',
			fullName=patient.fullName or '',
			dateOfBirth=str(patient.dateOfBirth) if patient.dateOfBirth else '',
			gender=patient.gender or '',
			latitude=patient.latitude,
			longitude=patient.longitude,
		)

	def _findBestMatchingPatient(  # noqa: C901, PLR0911, PLR0912, PLR0915, PLR0913
		self, firstname: str = '', lastname: str = '', dateofbirth: str = '', gender: str = '', latitude: str = '',
		longitude: str = '', reference: str = '', patient_id: int | str = '',
	) -> dict | None:
		"""
		Find the best matching patient with prioritized flow:
		1. patient_id (Direct database PK match - 100% confidence)
		2. reference (Patient.reference - 100% confidence)
		3. Location + Confirmed Demographics (Mandatory location prerequisite;
		names + birthdays alone without location are NEVER matched to prevent false identification).
		"""
		# 1. Tier 1: Deterministic match by database patient_id if provided
		if patient_id:
			try:
				pid_int = int(float(str(patient_id).strip()))
				if pid_int > 0:
					exact_patient = self.model.objects.filter(id=pid_int).first()
					if exact_patient:
						return self._patientToDict(exact_patient)
			except (ValueError, TypeError):
				pass

		# 2. Tier 2: Deterministic match on patient reference if provided
		ref_clean = self._cleanString(reference)
		if ref_clean:
			exact_patient = self.model.objects.filter(reference__iexact=ref_clean).first()
			if exact_patient:
				return self._patientToDict(exact_patient)

		# 3. Tier 3: Location + Confirmed Demographics
		# Strict rule: Location is MANDATORY. Normal fields like names and birthdays
		# are never matched together without location to prevent false identification.
		lat_float = self._parseFloat(latitude)
		lng_float = self._parseFloat(longitude)
		if lat_float is None or lng_float is None:
			return None

		fn_clean = self._cleanString(firstname)
		ln_clean = self._cleanString(lastname)
		# Demographics must also be provided to confirm the location match
		if not fn_clean and not ln_clean:
			return None

		# Query spatial bounding box (~1.1km / 0.01 deg)
		RADIUS = 0.01
		candidates = self.model.objects.filter(
			latitude__gte=lat_float - RADIUS,
			latitude__lte=lat_float + RADIUS,
			longitude__gte=lng_float - RADIUS,
			longitude__lte=lng_float + RADIUS,
		)

		if not candidates.exists():
			return None

		parsed_dob = self._parseDate(dateofbirth)
		norm_gender = self._normalizeGender(gender) if gender else None

		firstname_parts = [p.strip().lower() for p in re.split(r'[\s\-]+', fn_clean) if p.strip()] if fn_clean else []
		lastname_parts = [p.strip().lower() for p in re.split(r'[\s\-]+', ln_clean) if p.strip()] if ln_clean else []

		scored_candidates = []
		for patient in candidates[:50]:
			p_fn = (patient.firstName or '').strip().lower()
			p_ln = (patient.lastName or '').strip().lower()
			p_full = (patient.fullName or '').strip().lower()

			fn_matches = False
			ln_matches = False

			# Name verification: reject candidate on conflicting name
			if fn_clean:
				if (p_fn and fn_clean.lower() == p_fn) or any(p in p_full for p in firstname_parts):
					fn_matches = True
				elif p_fn:
					# First name exists on both and conflicts
					continue

			if ln_clean:
				if (p_ln and ln_clean.lower() == p_ln) or any(p in p_full for p in lastname_parts):
					ln_matches = True
				elif p_ln:
					# Last name exists on both and conflicts
					continue

			# Must have at least one confirmed name match
			if not fn_matches and not ln_matches:
				continue

			# DOB verification: reject on conflicting date of birth
			if parsed_dob and patient.dateOfBirth and patient.dateOfBirth != parsed_dob:
				continue

			# Gender verification: reject on conflicting gender
			prefer_not_to_say = Gender.PREFER_NOT_TO_SAY.value
			if (
				norm_gender
				and norm_gender != prefer_not_to_say
				and patient.gender
				and patient.gender not in (prefer_not_to_say, norm_gender)
			):
				continue

			# Candidate confirmed by demographics and location
			# Score primarily by geographic proximity with demographic tie-breakers
			dist = abs(lat_float - patient.latitude) + abs(lng_float - patient.longitude)
			proximity_score = max(0, 20 - (dist * 1000))
			demo_score = (
				(5 if fn_matches else 0)
				+ (5 if ln_matches else 0)
				+ (10 if (parsed_dob and patient.dateOfBirth == parsed_dob) else 0)
			)
			total_score = proximity_score + demo_score

			scored_candidates.append((total_score, patient))

		if scored_candidates:
			scored_candidates.sort(key=lambda x: x[0], reverse=True)
			best_patient = scored_candidates[0][1]
			return self._patientToDict(best_patient)

		return None

	def previewImport(self, file_url: str, column_mapping: dict | None = None) -> dict:  # noqa: C901, PLR0912, PLR0915
		"""
		Preview CSV/Excel file for import with duplicate detection.
		Returns:
			Dictionary with preview data, columns, duplicates, and stats
		"""
		Logger.info(f'Previewing file for import: {file_url}')
		file_path = self._resolveFilePath(file_url)

		# Read file with encoding fallback
		try:
			if str(file_path).endswith('.xlsx') or str(file_path).endswith('.xls'):
				df = pd.read_excel(file_path)
			else:
				encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
				df = None
				last_error = None
				for encoding in encodings_to_try:
					try:
						df = pd.read_csv(file_path, encoding=encoding)
						break
					except UnicodeDecodeError as enc_err:
						last_error = enc_err
						continue
				if df is None:
					raise ValueError(f'Could not read file with any encoding: {last_error}')
		except ValueError:
			raise
		except Exception as e:
			Logger.error(f'Error reading file: {e!s}')
			raise ValueError(f'Error reading file: {e!s}')

		df.columns = [str(col).strip() for col in df.columns]
		columns = list(df.columns)

		if column_mapping is None:
			column_mapping = {}

		detected_mapping = {}
		field_patterns = {
			'patient_id': [
				'patient_id', 'patientid', 'matched_patient_id', 'id',
			],
			'reference': [
				'reference', 'patient_reference', 'patientreference', 'patient_ref', 'patientref',
				'ref', 'patient_code', 'code_name', 'mrn', 'medical_record_number',
			],
			'firstName': [
				'firstname', 'first_name', 'fname', 'first', 'given_name', 'patient_first', 'patientfirst',
			],
			'lastName': [
				'lastname', 'last_name', 'lname', 'last', 'surname', 'family_name', 'patient_last', 'patientlast',
			],
			'fullName': [
				'name', 'patient_name', 'fullname', 'full_name', 'patient', 'patientname',
			],
			'dateOfBirth': [
				'dateofbirth', 'date_of_birth', 'dob', 'birthdate', 'birth_date', 'birthday',
				'patient_dob', 'birth_day',
			],
			'age': ['age', 'patient_age', 'years_old', 'yearsold', 'patientage'],
			'gender': ['gender', 'sex', 'patient_gender', 'patientsex'],
			'latitude': ['latitude', 'lat', 'patient_lat', 'location_lat', 'gps_lat', 'y_coord', 'y'],
			'longitude': [
				'longitude', 'long', 'lng', 'patient_long', 'patient_lng',
				'location_long', 'gps_long', 'x_coord', 'x',
			],
			'testedDate': ['tested_date', 'testeddate', 'test_date', 'testdate', 'collection_date', 'visit_date'],
			'notes': ['notes', 'comments', 'remarks', 'description', 'note', 'comment'],
		}

		for field, patterns in field_patterns.items():
			if field not in column_mapping:
				for col in columns:
					col_norm = col.lower().replace(' ', '_').replace('-', '_')
					if col_norm in patterns or col.lower() in patterns:
						detected_mapping[field] = col
						break

		final_mapping = {**detected_mapping, **column_mapping}

		preview_rows = []
		duplicates = []
		validation_errors = []

		for idx, row in df.iterrows():
			row_data = {}
			for col in columns:
				val = row[col]
				if pd.isna(val):
					row_data[col] = ''
				elif isinstance(val, (datetime, pd.Timestamp)):
					row_data[col] = val.strftime('%Y-%m-%d')
				else:
					row_data[col] = str(val).strip()

			# Extract mapped fields
			patient_id = (
				self._cleanString(row[final_mapping['patient_id']])
				if 'patient_id' in final_mapping and final_mapping['patient_id'] in row
				else ''
			)
			reference = (
				self._cleanString(row[final_mapping['reference']])
				if 'reference' in final_mapping and final_mapping['reference'] in row
				else ''
			)
			first_name = (
				self._cleanString(row[final_mapping['firstName']])
				if 'firstName' in final_mapping and final_mapping['firstName'] in row
				else ''
			)
			last_name = (
				self._cleanString(row[final_mapping['lastName']])
				if 'lastName' in final_mapping and final_mapping['lastName'] in row
				else ''
			)

			if 'fullName' in final_mapping and final_mapping['fullName'] in row:
				full_val = self._cleanString(row[final_mapping['fullName']])
				if full_val and not (first_name and last_name):
					name_parts = full_val.split(None, 1)
					if not first_name:
						first_name = name_parts[0]
					if not last_name and len(name_parts) > 1:
						last_name = name_parts[1]

			tested_date = (
				self._cleanString(row[final_mapping['testedDate']])
				if 'testedDate' in final_mapping and final_mapping['testedDate'] in row
				else ''
			)
			parsed_tested_date = self._parseDate(tested_date) if tested_date else None

			dob = ''
			if 'dateOfBirth' in final_mapping and final_mapping['dateOfBirth'] in row:
				parsed_d = self._parseDate(row[final_mapping['dateOfBirth']])
				if parsed_d:
					dob = str(parsed_d)

			if not dob and 'age' in final_mapping and final_mapping['age'] in row:
				age_val = self._cleanString(row[final_mapping['age']])
				if age_val:
					try:
						age_int = int(float(age_val))
						ref_year = parsed_tested_date.year if parsed_tested_date else timezone.now().year
						birth_year = ref_year - age_int
						dob = f'{birth_year}-01-01'
					except (ValueError, TypeError):
						pass

			gender = ''
			if 'gender' in final_mapping and final_mapping['gender'] in row:
				gender = self._normalizeGender(row[final_mapping['gender']])

			latitude = ''
			if 'latitude' in final_mapping and final_mapping['latitude'] in row:
				lat_f = self._parseFloat(row[final_mapping['latitude']])
				if lat_f is not None:
					latitude = str(lat_f)

			longitude = ''
			if 'longitude' in final_mapping and final_mapping['longitude'] in row:
				lng_f = self._parseFloat(row[final_mapping['longitude']])
				if lng_f is not None:
					longitude = str(lng_f)

			has_id = bool(patient_id)
			has_ref = bool(reference)
			has_name = bool(first_name or last_name)
			has_location = bool(latitude and longitude)

			if not has_id and not has_ref and not has_name and not has_location:
				validation_errors.append({
					'row_index': idx,
					'error': 'Missing patient ID, reference, name, and location coordinates',
				})
			else:
				match = self._findBestMatchingPatient(
					first_name, last_name, dob, gender, latitude, longitude,
					reference=reference, patient_id=patient_id,
				)
				if match:
					confidence = 0.5
					id_match = patient_id and str(match['id']) == str(patient_id)
					ref_match = reference and match.get('reference', '').lower() == reference.lower()
					if id_match or ref_match:
						confidence = 1.0
					else:
						if first_name and match.get('firstName', '').lower() == first_name.lower():
							confidence += 0.25
						if last_name and match.get('lastName', '').lower() == last_name.lower():
							confidence += 0.25
						if dob and match.get('dateOfBirth') == dob:
							confidence += 0.15

					duplicates.append({
						'row_index': idx,
						'match_patient_id': match['id'],
						'match_confidence': round(min(confidence, 1.0), 2),
						'match_name': match.get('fullName', ''),
						'match_dob': match.get('dateOfBirth', ''),
						'match_reference': match.get('reference', ''),
					})

			row_data['_row_index'] = idx
			if idx < 20:  # noqa: PLR2004
				preview_rows.append(row_data)

		total_rows = len(df)
		duplicate_count = len(duplicates)
		error_count = len(validation_errors)
		new_count = max(0, total_rows - duplicate_count - error_count)

		return {
			'total_rows': total_rows,
			'columns': columns,
			'detected_mapping': detected_mapping,
			'final_mapping': final_mapping,
			'preview_rows': preview_rows,
			'duplicates': duplicates,
			'validation_errors': validation_errors,
			'stats': {
				'total': total_rows,
				'new': new_count,
				'duplicates': duplicate_count,
				'errors': error_count,
			},
		}

	def executeImport(  # noqa: PLR0915, PLR0912, C901
		self,
		file_url: str,
		column_mapping: dict,
		duplicate_actions: dict | None = None,
		created_by=None,
	) -> dict:
		"""
		Execute the import of patients from CSV/Excel file.
		"""
		Logger.info(f'Executing patient import from: {file_url}')

		if duplicate_actions is None:
			duplicate_actions = {}

		file_path = self._resolveFilePath(file_url)

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

		df.columns = [str(col).strip() for col in df.columns]

		imported = 0
		skipped = 0
		updated = 0
		failed = 0
		failed_rows = []

		for idx, row in df.iterrows():
			try:
				patient_data = {}

				patient_id = (
					self._cleanString(row[column_mapping['patient_id']])
					if 'patient_id' in column_mapping and column_mapping['patient_id'] in row
					else ''
				)
				reference = (
					self._cleanString(row[column_mapping['reference']])
					if 'reference' in column_mapping and column_mapping['reference'] in row
					else ''
				)
				first_name = (
					self._cleanString(row[column_mapping['firstName']])
					if 'firstName' in column_mapping and column_mapping['firstName'] in row
					else ''
				)
				last_name = (
					self._cleanString(row[column_mapping['lastName']])
					if 'lastName' in column_mapping and column_mapping['lastName'] in row
					else ''
				)

				if reference:
					patient_data['reference'] = reference

				if 'fullName' in column_mapping and column_mapping['fullName'] in row:
					full_val = self._cleanString(row[column_mapping['fullName']])
					if full_val and not (first_name and last_name):
						name_parts = full_val.split(None, 1)
						if not first_name:
							first_name = name_parts[0]
						if not last_name and len(name_parts) > 1:
							last_name = name_parts[1]

				if first_name:
					patient_data['firstName'] = first_name
				if last_name:
					patient_data['lastName'] = last_name

				tested_date = (
					self._cleanString(row[column_mapping['testedDate']])
					if 'testedDate' in column_mapping and column_mapping['testedDate'] in row
					else ''
				)
				parsed_td = self._parseDate(tested_date) if tested_date else None

				if 'dateOfBirth' in column_mapping and column_mapping['dateOfBirth'] in row:
					parsed_d = self._parseDate(row[column_mapping['dateOfBirth']])
					if parsed_d:
						patient_data['dateOfBirth'] = parsed_d

				if 'dateOfBirth' not in patient_data and 'age' in column_mapping and column_mapping['age'] in row:
					age_val = self._cleanString(row[column_mapping['age']])
					if age_val:
						try:
							age_int = int(float(age_val))
							ref_year = parsed_td.year if parsed_td else timezone.now().year
							birth_year = ref_year - age_int
							patient_data['dateOfBirth'] = datetime(birth_year, 1, 1).date()  # noqa: DTZ001
						except (ValueError, TypeError):
							pass

				if 'gender' in column_mapping and column_mapping['gender'] in row:
					patient_data['gender'] = self._normalizeGender(row[column_mapping['gender']])
				else:
					patient_data['gender'] = Gender.PREFER_NOT_TO_SAY.value

				if 'notes' in column_mapping and column_mapping['notes'] in row:
					notes_val = self._cleanString(row[column_mapping['notes']])
					if notes_val:
						patient_data['notes'] = notes_val

				lat_f = None
				lng_f = None
				if 'latitude' in column_mapping and column_mapping['latitude'] in row:
					lat_f = self._parseFloat(row[column_mapping['latitude']])
					if lat_f is not None:
						patient_data['latitude'] = lat_f

				if 'longitude' in column_mapping and column_mapping['longitude'] in row:
					lng_f = self._parseFloat(row[column_mapping['longitude']])
					if lng_f is not None:
						patient_data['longitude'] = lng_f

				has_id = bool(patient_id)
				has_ref = bool(reference)
				has_name = bool(first_name or last_name)
				has_location = bool(lat_f is not None and lng_f is not None)

				if not has_id and not has_ref and not has_name and not has_location:
					failed += 1
					failed_rows.append({**dict(row), '_error': 'Missing patient ID, reference, name, and location'})
					continue

				default_action = duplicate_actions.get('default', 'create')
				action = duplicate_actions.get(str(idx), duplicate_actions.get(idx, default_action))

				match = self._findBestMatchingPatient(
					first_name,
					last_name,
					str(patient_data.get('dateOfBirth', '')),
					patient_data.get('gender', ''),
					str(lat_f) if lat_f is not None else '',
					str(lng_f) if lng_f is not None else '',
					reference=reference,
					patient_id=patient_id,
				)

				if match and action == 'skip':
					existing = self.getById(match['id'])
					update_data = {}
					if not existing.reference and patient_data.get('reference'):
						update_data['reference'] = patient_data['reference']
					if not existing.dateOfBirth and patient_data.get('dateOfBirth'):
						update_data['dateOfBirth'] = patient_data['dateOfBirth']
					prefer_not_to_say = Gender.PREFER_NOT_TO_SAY
					if (
						existing.gender == prefer_not_to_say
						and patient_data.get('gender') != prefer_not_to_say
					):
						update_data['gender'] = patient_data['gender']
					if existing.latitude is None and patient_data.get('latitude') is not None:
						update_data['latitude'] = patient_data['latitude']
					if existing.longitude is None and patient_data.get('longitude') is not None:
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
					existing = self.getById(match['id'])
					self.update(existing, patient_data)
					updated += 1
				else:
					if created_by:
						patient_data['createdBy'] = created_by
					self.create(patient_data)
					imported += 1

			except Exception as e:
				Logger.error(f'Error importing row {idx}: {e!s}')
				failed += 1
				failed_rows.append({**dict(row), '_error': str(e)})

		failed_file = None
		if failed_rows:
			results_dir = Path(settings.MEDIA_ROOT) / 'patients' / 'importResults'
			results_dir.mkdir(parents=True, exist_ok=True)

			timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # noqa: DTZ005
			failed_file_path = results_dir / f'failed_import_{timestamp}.csv'

			failed_df = pd.DataFrame(failed_rows)
			failed_df.to_csv(failed_file_path, index=False)
			failed_file = failed_file_path.relative_to(settings.MEDIA_ROOT).as_posix()

		Logger.info(f'Import complete: {imported} imported, {updated} updated, {skipped} skipped, {failed} failed')

		return {
			'status': 'complete',
			'imported': imported,
			'updated': updated,
			'skipped': skipped,
			'failed': failed,
			'failed_rows_file': failed_file,
		}

	def previewMatching(self, file_url: str, column_mapping: dict | None = None) -> dict:  # noqa: PLR0915, PLR0912, C901
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
			'patient_id': ['patient_id', 'patientid', 'matched_patient_id', 'id'],
			'reference': ['reference', 'ref', 'patient_reference', 'patient_ref', 'patient_code', 'code_name', 'mrn'],
			'firstName': ['firstname', 'first_name', 'fname', 'first', 'given_name', 'patient_first', 'patientfirst'],
			'lastName': [
				'lastname', 'last_name', 'lname', 'last', 'surname', 'family_name', 'patient_last', 'patientlast',
			],
			'dateOfBirth': [
				'dateofbirth', 'date_of_birth', 'dob', 'birthdate', 'birth_date', 'birthday', 'patient_dob',
			],
			'age': ['age', 'patient_age', 'years_old', 'yearsold'],
			'gender': ['gender', 'sex', 'patient_gender'],
			'latitude': ['latitude', 'lat', 'patient_lat', 'location_lat', 'gps_lat', 'y_coord'],
			'longitude': ['longitude', 'long', 'lng', 'patient_long', 'location_long', 'gps_long', 'x_coord'],
			'testedDate': ['tested_date', 'testeddate', 'test_date', 'testdate', 'collection_date', 'visit_date'],
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
			patient_id = ''
			reference = ''
			first_name = ''
			last_name = ''
			dob = ''
			age = ''
			gender = ''
			latitude = ''
			longitude = ''
			tested_date = ''

			if 'patient_id' in final_mapping and final_mapping['patient_id'] in row:
				val = row[final_mapping['patient_id']]
				patient_id = str(val) if pd.notna(val) else ''
			if 'reference' in final_mapping and final_mapping['reference'] in row:
				val = row[final_mapping['reference']]
				reference = str(val) if pd.notna(val) else ''
			if 'firstName' in final_mapping and final_mapping['firstName'] in row:
				val = row[final_mapping['firstName']]
				first_name = str(val) if pd.notna(val) else ''
			if 'lastName' in final_mapping and final_mapping['lastName'] in row:
				val = row[final_mapping['lastName']]
				last_name = str(val) if pd.notna(val) else ''
			if 'dateOfBirth' in final_mapping and final_mapping['dateOfBirth'] in row:
				val = row[final_mapping['dateOfBirth']]
				dob = str(val) if pd.notna(val) else ''
			if 'age' in final_mapping and final_mapping['age'] in row:
				val = row[final_mapping['age']]
				age = str(val) if pd.notna(val) else ''
			if 'gender' in final_mapping and final_mapping['gender'] in row:
				val = row[final_mapping['gender']]
				gender = str(val) if pd.notna(val) else ''
			if 'latitude' in final_mapping and final_mapping['latitude'] in row:
				val = row[final_mapping['latitude']]
				latitude = str(val) if pd.notna(val) else ''
			if 'longitude' in final_mapping and final_mapping['longitude'] in row:
				val = row[final_mapping['longitude']]
				longitude = str(val) if pd.notna(val) else ''
			if 'testedDate' in final_mapping and final_mapping['testedDate'] in row:
				val = row[final_mapping['testedDate']]
				tested_date = str(val) if pd.notna(val) else ''

			# If age provided but not DOB, calculate from tested_date (or current date)
			if age and not dob:
				try:
					age_int = int(float(age))
					parsed_td = self._parseDate(tested_date) if tested_date else None
					ref_year = parsed_td.year if parsed_td else timezone.now().year
					birth_year = ref_year - age_int
					dob = f'{birth_year}-01-01'
				except (ValueError, TypeError):
					pass

			# Check identifiers
			has_id = bool(patient_id.strip())
			has_ref = bool(reference.strip())
			has_name = bool(first_name.strip() or last_name.strip())
			has_location = bool(latitude.strip() and longitude.strip())

			# Try to match
			match = None
			if has_id or has_ref or has_name or has_location:
				match = self._findBestMatchingPatient(
					first_name, last_name, dob, gender, latitude, longitude,
					reference=reference, patient_id=patient_id,
				)

			if match:
				matched_count += 1
			else:
				unmatched_count += 1

			# Build preview row (first 20 only)
			if idx < 20:  # noqa: PLR2004
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

	def matchPatientsForDownload(self, file_url: str, column_mapping: dict | None = None) -> dict:  # noqa: PLR0915, PLR0912, C901
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
			'reference': ['reference', 'ref', 'patient_reference', 'patient_ref', 'patient_id', 'patientid', 'mrn'],
			'firstName': ['firstname', 'first_name', 'fname', 'first', 'given_name', 'patient_first', 'patientfirst'],
			'lastName': [
				'lastname', 'last_name', 'lname', 'last', 'surname', 'family_name', 'patient_last', 'patientlast',
			],
			'dateOfBirth': [
				'dateofbirth', 'date_of_birth', 'dob', 'birthdate', 'birth_date', 'birthday', 'patient_dob',
			],
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
			'patient_id': 'matched_patient_id',
			'reference': 'matched_reference',
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
		field_keys = [
			'patient_id', 'reference', 'firstName', 'lastName',
			'dateOfBirth', 'age', 'gender', 'latitude', 'longitude',
		]
		for field_key in field_keys:
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
			patient_id = ''
			reference = ''
			first_name = ''
			last_name = ''
			dob = ''
			age = ''
			gender = ''
			latitude = ''
			longitude = ''
			tested_date = ''

			if 'patient_id' in final_mapping and final_mapping['patient_id'] in row:
				val = row[final_mapping['patient_id']]
				patient_id = str(val) if pd.notna(val) else ''
			if 'reference' in final_mapping and final_mapping['reference'] in row:
				val = row[final_mapping['reference']]
				reference = str(val) if pd.notna(val) else ''
			if 'firstName' in final_mapping and final_mapping['firstName'] in row:
				val = row[final_mapping['firstName']]
				first_name = str(val) if pd.notna(val) else ''
			if 'lastName' in final_mapping and final_mapping['lastName'] in row:
				val = row[final_mapping['lastName']]
				last_name = str(val) if pd.notna(val) else ''
			if 'dateOfBirth' in final_mapping and final_mapping['dateOfBirth'] in row:
				val = row[final_mapping['dateOfBirth']]
				dob = str(val) if pd.notna(val) else ''
			if 'age' in final_mapping and final_mapping['age'] in row:
				val = row[final_mapping['age']]
				age = str(val) if pd.notna(val) else ''
			if 'gender' in final_mapping and final_mapping['gender'] in row:
				val = row[final_mapping['gender']]
				gender = str(val) if pd.notna(val) else ''
			if 'latitude' in final_mapping and final_mapping['latitude'] in row:
				val = row[final_mapping['latitude']]
				latitude = str(val) if pd.notna(val) else ''
			if 'longitude' in final_mapping and final_mapping['longitude'] in row:
				val = row[final_mapping['longitude']]
				longitude = str(val) if pd.notna(val) else ''
			if 'testedDate' in final_mapping and final_mapping['testedDate'] in row:
				val = row[final_mapping['testedDate']]
				tested_date = str(val) if pd.notna(val) else ''

			# If age provided but not DOB, calculate from tested_date (or current date)
			effective_dob = dob
			if age and not dob:
				try:
					age_int = int(float(age))
					parsed_td = self._parseDate(tested_date) if tested_date else None
					ref_year = parsed_td.year if parsed_td else timezone.now().year
					birth_year = ref_year - age_int
					effective_dob = f'{birth_year}-01-01'
				except (ValueError, TypeError):
					pass

			# Create a signature for within-file duplicate detection
			# Use normalized reference OR name + dob/age + location
			sig_parts = []
			if patient_id.strip():
				sig_parts.append(f'id:{patient_id.strip()}')
			if reference.strip():
				sig_parts.append(f'ref:{reference.strip().lower()}')
			if first_name.strip():
				sig_parts.append(first_name.strip().lower())
			if last_name.strip():
				sig_parts.append(last_name.strip().lower())
			if effective_dob:
				sig_parts.append(effective_dob)
			elif age:
				sig_parts.append(f'age:{age}')
			if latitude.strip() and longitude.strip() and contextlib.suppress(ValueError, TypeError):
				# Round coordinates for grouping
				sig_parts.append(f'loc:{round(float(latitude), 3)},{round(float(longitude), 3)}')

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
			has_id = bool(patient_id.strip())
			has_ref = bool(reference.strip())
			has_name = bool(first_name.strip() or last_name.strip())
			has_location = bool(latitude.strip() and longitude.strip())

			# Try to match against database
			match = None
			if has_id or has_ref or has_name or has_location:
				match = self._findBestMatchingPatient(
					first_name, last_name, effective_dob, gender, latitude, longitude,
					reference=reference, patient_id=patient_id,
				)

			# Build output row
			output_row = {
				'row_number': row_number,
				'file_duplicate_of_row': file_duplicate_of,
				'file_patient_group': file_group,
			}

			if match:
				matched_count += 1
				# Calculate confidence score (100% if matched by patient_id or reference)
				id_match = patient_id.strip() and str(match['id']) == patient_id.strip()
				ref_match = (
					reference.strip()
					and match.get('reference', '').lower() == reference.strip().lower()
				)
				if id_match or ref_match:
					confidence = 1.0
				else:
					confidence = 0.8
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
							if lat_diff < 0.001 and lng_diff < 0.001:  # noqa: PLR2004
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
				'reference': match.get('reference', '') if match else '',
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
					for field_key, input_c, _ in mapped_fields_ordered:
						if input_c == col:
							output_row[matched_col] = matched_values.get(field_key, '')
							break

			rows.append(output_row)

		total_rows = len(df)
		timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # noqa: DTZ005

		Logger.info(
			f'Matching complete: {matched_count}/{total_rows} matched, {file_duplicate_count} '
			'in-file duplicates found',
		)

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

