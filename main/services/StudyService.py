import csv
import io
import re
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.db.models import Q

from vvecon.zorion.core import Service
from vvecon.zorion.logger import Logger

from ..models import Patient, Study, StudyResult, StudyVariable, UserStudy

__all__ = ['StudyService']


class StudyService(Service):
	model = Study
	searchableFields = ('name', 'description', 'category')
	filterableFields = ('status', 'category', 'createdBy')

	def search(self, filters):
		"""
		Search and filter studies based on provided criteria
		"""
		queryset = self.model.objects.all()

		# Apply search
		search_term = filters.get('search', '').strip()
		if search_term:
			from django.db.models import Q
			query = Q()
			for field in self.searchableFields:
				query |= Q(**{f'{field}__icontains': search_term})
			queryset = queryset.filter(query)

		# Apply filters
		for field in self.filterableFields:
			value = filters.get(field)
			if value is not None and value != '':
				queryset = queryset.filter(**{field: value})

		return queryset

	def paginate(self, queryset, page=1, limit=20):
		"""
		Paginate a queryset
		"""
		start = (page - 1) * limit
		end = start + limit
		return list(queryset[start:end])

	def getDetails(self, study_id):
		"""
		Get full dataset details with variables and statistics
		"""

		study = self.model.objects.prefetch_related('variables', 'userStudies').get(id=study_id)

		return {
			'study': study,
			'variables': list(study.variables.all().order_by('order', 'name')),
			'stats': {
				'variablesCount': study.variables.count(),
				'userStudiesCount': study.userStudies.count(),
				'resultsCount': StudyResult.objects.filter(userStudy__study=study).count(),
			},
		}

	def getVariables(self, study_id):
		"""
		Get all variables for a dataset
		"""
		study = self.getById(study_id)
		return list(study.variables.all().order_by('order', 'name'))

	def addVariable(self, study_id, data):
		"""
		Add a new variable to a dataset
		"""
		study = self.getById(study_id)
		variable = StudyVariable.objects.create(**data)
		study.variables.add(variable)
		return variable

	def updateVariable(self, variable_id, data):
		"""
		Update an existing variable
		"""
		variable = StudyVariable.objects.get(id=variable_id)
		for key, value in data.items():
			setattr(variable, key, value)
		variable.save()
		return variable

	def removeVariable(self, study_id, variable_id):
		"""
		Remove a variable from a dataset
		"""
		study = self.getById(study_id)
		variable = StudyVariable.objects.get(id=variable_id)
		study.variables.remove(variable)
		# Optionally delete the variable if not used elsewhere
		if variable.studies.count() == 0:
			variable.delete()
		return True

	def getDataPreview(self, study_id, page=1, limit=10):
		"""
		Get paginated data preview (UserStudy results as rows)
		"""
		study = self.getById(study_id)
		variables = list(study.variables.all().order_by('order', 'name'))

		# Get user studies for this dataset
		user_studies_qs = UserStudy.objects.filter(study=study).select_related('patient')
		total_count = user_studies_qs.count()

		# Paginate
		start = (page - 1) * limit
		end = start + limit
		user_studies = list(user_studies_qs[start:end])

		# Build data rows
		rows = []
		for us in user_studies:
			row = {
				'id': us.id,
				'patient': {
					'id': us.patient.id if us.patient else None,
					'name': f'{us.patient.firstName} {us.patient.lastName}'.strip() if us.patient else 'N/A',
				},
				'reference': us.reference,
				'status': us.status,
				'created_at': us.created_at,
				'values': {},
			}

			# Get results for this user study
			results = StudyResult.objects.filter(userStudy=us).select_related('studyVariable')
			for result in results:
				row['values'][result.studyVariable.id] = result.value

			rows.append(row)

		total_pages = (total_count + limit - 1) // limit if limit > 0 else 1

		return {
			'columns': [{'id': v.id, 'name': v.name, 'type': v.type} for v in variables],
			'rows': rows,
			'pagination': {
				'page': page,
				'limit': limit,
				'total': total_count,
				'totalPages': total_pages,
				'hasNext': page < total_pages,
				'hasPrev': page > 1,
			},
		}

	def getHistory(self, study_id):
		"""
		Get update history for a dataset (based on timestamps and related records)
		"""
		study = self.getById(study_id)

		# Build history events from available data
		events = []

		# Dataset created event
		events.append({
			'type': 'created',
			'timestamp': study.created_at,
			'user': {
				'id': study.createdBy.id if study.createdBy else None,
				'name': f'{study.createdBy.firstName} {study.createdBy.lastName}'.strip() if study.createdBy else 'System',
			} if study.createdBy else {'id': None, 'name': 'System'},
			'description': f'Dataset "{study.name}" was created',
		})

		# Dataset updated event (if updated_at differs from created_at)
		if study.updated_at and study.updated_at != study.created_at:
			events.append({
				'type': 'updated',
				'timestamp': study.updated_at,
				'user': {
					'id': study.createdBy.id if study.createdBy else None,
					'name': f'{study.createdBy.firstName} {study.createdBy.lastName}'.strip() if study.createdBy else 'System',
				} if study.createdBy else {'id': None, 'name': 'System'},
				'description': f'Dataset was updated to version {study.version}',
			})

		# Recent user studies as events (last 10)
		recent_studies = UserStudy.objects.filter(study=study).order_by('-created_at')[:10]
		for us in recent_studies:
			events.append({
				'type': 'data_added',
				'timestamp': us.created_at,
				'user': {
					'id': us.createdBy.id if us.createdBy else None,
					'name': f'{us.createdBy.firstName} {us.createdBy.lastName}'.strip() if us.createdBy else 'System',
				} if us.createdBy else {'id': None, 'name': 'System'},
				'description': f'Data entry added for patient {us.patient.firstName if us.patient else "Unknown"}',
			})

		# Sort by timestamp descending
		events.sort(key=lambda x: x['timestamp'] if x['timestamp'] else '', reverse=True)

		return events

	def getPatients(self, study_id, page=1, limit=20):
		"""
		Get patients who have data entries (UserStudy) in this dataset with pagination
		"""
		from django.db.models import Count

		study = self.getById(study_id)

		# Get distinct patients with user studies in this dataset
		patient_ids_with_counts = (
			UserStudy.objects.filter(study=study)
			.values('patient_id')
			.annotate(entries_count=Count('id'))
		)

		# Total count of distinct patients
		total_count = len(patient_ids_with_counts)

		# Paginate the patient IDs
		start = (page - 1) * limit
		end = start + limit
		paginated_patient_data = list(patient_ids_with_counts[start:end])

		# Get actual patient objects
		patient_ids = [p['patient_id'] for p in paginated_patient_data if p['patient_id']]
		patients_map = {}

		if patient_ids:
			from ..models import Patient
			patients = Patient.objects.filter(id__in=patient_ids)
			patients_map = {p.id: p for p in patients}

		# Build response with patient data and entry counts
		patients_list = []
		for pd in paginated_patient_data:
			patient = patients_map.get(pd['patient_id'])
			if patient:
				patients_list.append({
					'id': patient.id,
					'firstName': patient.firstName,
					'lastName': patient.lastName,
					'reference': patient.reference,
					'gender': patient.gender if hasattr(patient, 'gender') else None,
					'age': patient.age if hasattr(patient, 'age') else None,
					'status': patient.status if hasattr(patient, 'status') else 'ACTIVE',
					'dataEntriesCount': pd['entries_count'],
				})

		total_pages = (total_count + limit - 1) // limit if limit > 0 else 1

		return {
			'patients': patients_list,
			'pagination': {
				'page': page,
				'limit': limit,
				'total': total_count,
				'totalPages': total_pages,
				'hasNext': page < total_pages,
				'hasPrev': page > 1,
			},
		}

	def getPaginatedStudies(self, page=1, limit=10, search=None, filters=None):
		"""
		Get paginated studies with optional search and filters
		"""
		queryset = self.model.objects.all()

		# Apply search
		if search:
			from django.db.models import Q
			query = Q()
			for field in self.searchableFields:
				query |= Q(**{f'{field}__icontains': search})
			queryset = queryset.filter(query)

		# Apply filters
		if filters:
			for field, value in filters.items():
				if field in self.filterableFields and value:
					queryset = queryset.filter(**{field: value})

		# Get total count before pagination
		total_count = queryset.count()

		# Apply pagination
		start = (page - 1) * limit
		end = start + limit
		studies = queryset[start:end]

		# Calculate pagination info
		total_pages = (total_count + limit - 1) // limit
		has_next = page < total_pages
		has_previous = page > 1

		return {
			'studies': list(studies),
			'pagination': {
				'current_page': page,
				'limit': limit,
				'total_count': total_count,
				'total_pages': total_pages,
				'has_next': has_next,
				'has_previous': has_previous,
			},
		}

	# ==========================================================================
	# Data Import Methods
	# ==========================================================================

	# Column patterns for auto-detecting patient fields
	# Note: matched_patient_id is valid for reference as it links to matched patients
	PATIENT_COLUMN_PATTERNS = {
		'reference': ['patientreference', 'patientref', 'patient_reference', 'patient_ref', 'patientid', 'patient_id', 'subjectid', 'subject_id', 'participantid', 'matched_patient_id'],
		'firstName': ['firstname', 'first_name', 'fname', 'first', 'givenname', 'patient_first'],
		'lastName': ['lastname', 'last_name', 'lname', 'last', 'surname', 'familyname', 'patient_last'],
		'dateOfBirth': ['dateofbirth', 'date_of_birth', 'dob', 'birthdate', 'birth_date', 'birthday'],
		'age': ['age', 'patient_age', 'years', 'yearsold'],
		'gender': ['gender', 'sex', 'patient_gender'],
		'latitude': ['latitude', 'lat', 'location_lat', 'gps_lat', 'y_coord'],
		'longitude': ['longitude', 'long', 'lng', 'location_long', 'gps_long', 'x_coord'],
	}

	# Columns to skip during variable matching and patient column detection
	# These are system-added columns from matching process or internal use
	SKIP_COLUMN_PATTERNS = (
		# Match process columns
		'matched_', 'match_', 'file_duplicate_', 'file_patient_',
		'match_status', 'match_confidence', 'matched_patient',
		# Row tracking columns
		'row_number', '_row_number', '_row_index', '_original_index',
		# Status/internal columns
		'_status', '_patient_', '_file_', '_match_',
		# Pandas auto-generated
		'unnamed:',
	)

	def _resolveFilePath(self, file_url: str) -> Path:
		"""Resolve file URL to absolute filesystem path."""
		if file_url.startswith('/media/'):
			return Path(settings.MEDIA_ROOT) / file_url.replace('/media/', '')
		if file_url.startswith('media/'):
			return Path(settings.MEDIA_ROOT) / file_url.replace('media/', '')
		return Path(settings.MEDIA_ROOT) / file_url

	def _createPatientSignature(self, first_name: str, last_name: str, reference: str, dob: str, age: str, latitude: str, longitude: str) -> str | None:
		"""Create unique signature for in-file duplicate detection."""
		sig_parts = []
		if first_name:
			sig_parts.append(first_name.lower().strip())
		if last_name:
			sig_parts.append(last_name.lower().strip())
		if reference:
			sig_parts.append(f'ref:{reference.lower().strip()}')
		if dob:
			sig_parts.append(f'dob:{dob}')
		elif age:
			sig_parts.append(f'age:{age}')
		if latitude and longitude:
			try:
				sig_parts.append(f'loc:{round(float(latitude), 3)},{round(float(longitude), 3)}')
			except (ValueError, TypeError):
				pass
		return '|'.join(sig_parts) if sig_parts else None

	def _detectColumnTypes(self, columns: list, sample_rows: list) -> dict:
		"""Detect data types from sample values for each column."""
		date_pattern = re.compile(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}$|^\d{1,2}[-/]\d{1,2}[-/]\d{4}$')
		bool_values = {'yes', 'no', 'true', 'false', 'y', 'n', '1', '0'}
		column_types = {}

		for col in columns:
			# Get non-empty sample values
			sample_values = [str(row.get(col, '')).strip() for row in sample_rows[:20] if str(row.get(col, '')).strip()]
			if not sample_values:
				column_types[col] = 'TEXT'
				continue

			is_number = True
			is_date = True
			is_bool = True

			for val in sample_values:
				# Number check
				try:
					float(val.replace(',', ''))
				except (ValueError, TypeError):
					is_number = False

				# Date check
				if not date_pattern.match(val):
					is_date = False

				# Boolean check
				if val.lower() not in bool_values:
					is_bool = False

			if is_bool and len(sample_values) >= 2:
				column_types[col] = 'BOOLEAN'
			elif is_date:
				column_types[col] = 'DATE'
			elif is_number:
				column_types[col] = 'NUMBER'
			else:
				column_types[col] = 'TEXT'

		return column_types

	def _readFileContent(self, file_path: Path) -> tuple[list, list]:
		"""Read CSV/Excel file and return (columns, all_rows)."""
		if str(file_path).endswith(('.xlsx', '.xls')):
			import pandas as pd
			df = pd.read_excel(file_path)
			df.columns = [str(col).strip() for col in df.columns]
			columns = list(df.columns)
			all_rows = df.fillna('').to_dict('records')
		else:
			# CSV with encoding fallback
			file_content = None
			for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
				try:
					with open(file_path, encoding=encoding) as f:
						file_content = f.read()
					break
				except UnicodeDecodeError:
					continue
			if file_content is None:
				with open(file_path, encoding='utf-8', errors='replace') as f:
					file_content = f.read()

			reader = csv.DictReader(io.StringIO(file_content))
			columns = [col.strip() for col in reader.fieldnames] if reader.fieldnames else []
			all_rows = list(reader)

		return columns, all_rows

	def previewDataImport(self, study_id: int, file_url: str, mapping: dict = None) -> dict:
		"""
		Preview data import with duplicate detection and patient matching.
		
		Args:
			study_id: Dataset ID to import into
			file_url: Path to uploaded CSV/Excel file
			mapping: Optional column mapping from frontend
			
		Returns:
			Dictionary with columns, preview rows, suggestions, stats, etc.
		"""
		Logger.info(f'Previewing import data for dataset {study_id}')

		# Get dataset and variables
		dataset = self.getById(study_id)
		variables = list(dataset.variables.all().order_by('order', 'name'))

		# Resolve and read file
		file_path = self._resolveFilePath(file_url)
		if not file_path.exists():
			raise ValueError(f'File not found: {file_path}')

		columns, all_rows = self._readFileContent(file_path)

		# Filter columns - skip system columns (check both startswith and contains)
		def is_system_column(col_name: str) -> bool:
			col_lower = col_name.lower()
			for pattern in self.SKIP_COLUMN_PATTERNS:
				if col_lower.startswith(pattern) or pattern in col_lower:
					return True
			return False

		data_columns = [col for col in columns if not is_system_column(col)]

		# Auto-detect patient column suggestions (only from data columns, not system columns)
		patient_suggestions = {}
		for field, patterns in self.PATIENT_COLUMN_PATTERNS.items():
			for col in data_columns:  # Use data_columns to exclude system columns
				col_lower = col.lower().replace(' ', '').replace('_', '')
				if any(p in col_lower for p in patterns):
					patient_suggestions[field] = col
					break

		# Auto-map variables to existing dataset variables
		variable_suggestions = {}
		for var in variables:
			var_name_lower = var.name.lower().replace(' ', '').replace('_', '')
			for col in data_columns:
				col_lower = col.lower().replace(' ', '').replace('_', '')
				if var_name_lower == col_lower or var_name_lower in col_lower or col_lower in var_name_lower:
					variable_suggestions[str(var.id)] = col
					break

		# Detect column types
		column_types = self._detectColumnTypes(data_columns, all_rows)

		# If no mapping provided, return initial preview (step 1)
		if mapping is None:
			return {
				'columns': columns,
				'dataColumns': data_columns,
				'variables': [{'id': v.id, 'name': v.name, 'type': v.type} for v in variables],
				'previewData': all_rows[:10],
				'totalRows': len(all_rows),
				'patientSuggestions': patient_suggestions,
				'variableSuggestions': variable_suggestions,
				'columnTypes': column_types,
			}

		# Step 2: Full preview with patient matching
		from ..services import PatientService
		patient_service = PatientService()

		# Extract patient mapping
		patient_mapping = mapping.get('patient', {})
		patient_col = patient_mapping.get('reference', '')
		first_name_col = patient_mapping.get('firstName', '')
		last_name_col = patient_mapping.get('lastName', '')
		dob_col = patient_mapping.get('dateOfBirth', '')
		age_col = patient_mapping.get('age', '')
		gender_col = patient_mapping.get('gender', '')
		lat_col = patient_mapping.get('latitude', '')
		lng_col = patient_mapping.get('longitude', '')

		# Track in-file duplicates
		seen_patients = {}  # signature -> first row number
		patient_groups = {}  # signature -> group id
		next_group_id = 1

		rows_result = []
		new_count = 0
		update_count = 0
		file_duplicate_count = 0
		
		# Patient-specific stats
		patients_existing = 0  # Patients that already exist in the system
		patients_to_create = 0  # New patients that will be created
		patients_matched_ids = set()  # Track unique existing patients matched

		for idx, row in enumerate(all_rows):
			row_number = idx + 2  # Excel row (1-indexed + header)

			# Extract patient fields
			reference = str(row.get(patient_col, '')).strip() if patient_col else ''
			first_name = str(row.get(first_name_col, '')).strip() if first_name_col else ''
			last_name = str(row.get(last_name_col, '')).strip() if last_name_col else ''
			dob = str(row.get(dob_col, '')).strip() if dob_col else ''
			age = str(row.get(age_col, '')).strip() if age_col else ''
			gender = str(row.get(gender_col, '')).strip() if gender_col else ''
			latitude = str(row.get(lat_col, '')).strip() if lat_col else ''
			longitude = str(row.get(lng_col, '')).strip() if lng_col else ''

			# Convert age to DOB if needed
			effective_dob = dob
			if age and not dob:
				try:
					age_int = int(float(age))
					birth_year = datetime.now().year - age_int
					effective_dob = f'{birth_year}-01-01'
				except (ValueError, TypeError):
					pass

			# Check valid identifiers
			has_reference = bool(reference)
			has_name = bool(first_name or last_name)
			has_location = bool(latitude and longitude)

			# Create signature for duplicate detection
			patient_signature = self._createPatientSignature(
				first_name, last_name, reference, effective_dob, age, latitude, longitude
			)

			# Check for in-file duplicates
			file_duplicate_of = ''
			file_group = ''
			if patient_signature:
				if patient_signature in seen_patients:
					file_duplicate_of = str(seen_patients[patient_signature])
					file_duplicate_count += 1
					file_group = patient_groups.get(patient_signature, '')
				else:
					seen_patients[patient_signature] = row_number
					file_group = f'G{next_group_id}'
					patient_groups[patient_signature] = file_group
					next_group_id += 1

			# Find existing patient
			patient = None
			match_info = None

			# Try reference first (via UserStudy)
			if has_reference:
				user_study = UserStudy.objects.filter(study=dataset, reference=reference).select_related('patient').first()
				if user_study and user_study.patient:
					patient = user_study.patient

			# Try advanced matching if no reference match
			if not patient and (has_name or has_location):
				match = patient_service._findBestMatchingPatient(
					first_name, last_name, effective_dob, gender, latitude, longitude
				)
				if match:
					patient = Patient.objects.filter(id=match['id']).first()
					match_info = match

			# Determine status
			if patient:
				# Track unique existing patients
				if patient.id not in patients_matched_ids:
					patients_matched_ids.add(patient.id)
					patients_existing += 1
				
				# Check if patient already has data in this dataset
				existing = UserStudy.objects.filter(study=dataset, patient=patient).exists()
				if existing:
					status = 'update'
					update_count += 1
				else:
					status = 'new'  # Patient exists but new to this dataset
					new_count += 1
			else:
				# No matching patient - will create during import
				status = 'will_create'
				new_count += 1
				# Only count as new patient if not a file duplicate
				if not file_duplicate_of:
					patients_to_create += 1

			# Build row result
			row_result = {
				'_row_number': row_number,
				'_status': status,
				'_patient_id': patient.id if patient else None,
				'_patient_name': f'{patient.firstName or ""} {patient.lastName or ""}'.strip() if patient else None,
				'_file_duplicate_of': file_duplicate_of,
				'_file_group': file_group,
				'_match_confidence': match_info.get('confidence', 0) if match_info else None,
				**row,
			}
			rows_result.append(row_result)

		return {
			'columns': columns,
			'dataColumns': data_columns,
			'variables': [{'id': v.id, 'name': v.name, 'type': v.type} for v in variables],
			'previewData': rows_result[:50],  # First 50 for preview
			'totalRows': len(all_rows),
			'patientSuggestions': patient_suggestions,
			'variableSuggestions': variable_suggestions,
			'columnTypes': column_types,
			'stats': {
				# Record stats
				'total': len(all_rows),
				'new': new_count,
				'update': update_count,
				'fileDuplicates': file_duplicate_count,
				# Patient stats
				'patientsExisting': patients_existing,
				'patientsToCreate': patients_to_create,
				'uniquePatients': patients_existing + patients_to_create,
			},
		}

	def executeDataImport(self, study_id: int, file_url: str, mapping: dict, column_types: dict = None, created_by=None) -> dict:
		"""
		Execute data import: create patients if needed, create UserStudy & StudyResult records.
		
		Args:
			study_id: Dataset ID to import into
			file_url: Path to uploaded CSV/Excel file
			mapping: Column mapping from frontend (patient fields + variables)
			column_types: Detected/confirmed column types for new variables
			created_by: User performing the import
			
		Returns:
			Dictionary with import statistics
		"""
		Logger.info(f'Executing data import for dataset {study_id}')

		# Get dataset and variables
		dataset = self.getById(study_id)
		existing_variables = {v.name.lower(): v for v in dataset.variables.all()}

		# Resolve and read file
		file_path = self._resolveFilePath(file_url)
		if not file_path.exists():
			raise ValueError(f'File not found: {file_path}')

		columns, all_rows = self._readFileContent(file_path)

		# Extract mappings
		patient_mapping = mapping.get('patient', {})
		variable_mapping = mapping.get('variables', {})  # var_id -> column_name
		column_types = column_types or {}

		# Patient columns
		patient_col = patient_mapping.get('reference', '')
		first_name_col = patient_mapping.get('firstName', '')
		last_name_col = patient_mapping.get('lastName', '')
		dob_col = patient_mapping.get('dateOfBirth', '')
		age_col = patient_mapping.get('age', '')
		gender_col = patient_mapping.get('gender', '')
		lat_col = patient_mapping.get('latitude', '')
		lng_col = patient_mapping.get('longitude', '')

		# Import PatientService for matching
		from ..services import PatientService
		patient_service = PatientService()

		# Track stats
		imported = 0
		updated = 0
		patients_created = 0
		variables_created = 0
		skipped = 0
		duplicates_skipped = 0
		errors = []

		# Track in-file duplicates
		seen_patients = set()

		# Create new variables for unmapped columns
		mapped_columns = set(variable_mapping.values())
		patient_columns = {patient_col, first_name_col, last_name_col, dob_col, age_col, gender_col, lat_col, lng_col}
		patient_columns.discard('')

		data_columns = [
			col for col in columns
			if not any(col.lower().startswith(p) for p in self.SKIP_COLUMN_PATTERNS)
		]

		for col in data_columns:
			if col not in mapped_columns and col not in patient_columns:
				# Check if variable already exists
				if col.lower() not in existing_variables:
					var_type = column_types.get(col, 'TEXT')
					new_var = StudyVariable.objects.create(
						name=col,
						type=var_type,
						description=f'Auto-created during import',
					)
					dataset.variables.add(new_var)
					existing_variables[col.lower()] = new_var
					variables_created += 1
					Logger.info(f'Created variable: {col} ({var_type})')

		# Process each row
		for idx, row in enumerate(all_rows):
			try:
				# Extract patient fields
				reference = str(row.get(patient_col, '')).strip() if patient_col else ''
				first_name = str(row.get(first_name_col, '')).strip() if first_name_col else ''
				last_name = str(row.get(last_name_col, '')).strip() if last_name_col else ''
				dob = str(row.get(dob_col, '')).strip() if dob_col else ''
				age = str(row.get(age_col, '')).strip() if age_col else ''
				gender = str(row.get(gender_col, '')).strip() if gender_col else ''
				latitude = str(row.get(lat_col, '')).strip() if lat_col else ''
				longitude = str(row.get(lng_col, '')).strip() if lng_col else ''

				# Convert age to DOB if needed
				effective_dob = dob
				if age and not dob:
					try:
						age_int = int(float(age))
						birth_year = datetime.now().year - age_int
						effective_dob = f'{birth_year}-01-01'
					except (ValueError, TypeError):
						pass

				# Check valid identifiers
				has_reference = bool(reference)
				has_name = bool(first_name or last_name)
				has_location = bool(latitude and longitude)

				if not has_reference and not has_name and not has_location:
					skipped += 1
					continue

				# Create signature for duplicate detection
				patient_signature = self._createPatientSignature(
					first_name, last_name, reference, effective_dob, age, latitude, longitude
				)

				# Skip in-file duplicates
				if patient_signature and patient_signature in seen_patients:
					duplicates_skipped += 1
					continue
				if patient_signature:
					seen_patients.add(patient_signature)

				# Find or create patient
				patient = None

				# Try reference first (via UserStudy)
				if has_reference:
					user_study = UserStudy.objects.filter(study=dataset, reference=reference).select_related('patient').first()
					if user_study and user_study.patient:
						patient = user_study.patient

				# Try advanced matching
				if not patient and (has_name or has_location):
					match = patient_service._findBestMatchingPatient(
						first_name, last_name, effective_dob, gender, latitude, longitude
					)
					if match:
						patient = Patient.objects.filter(id=match['id']).first()

				# Create patient if not found
				if not patient:
					# Parse DOB for patient creation
					parsed_dob = None
					if effective_dob:
						try:
							parsed_dob = datetime.strptime(effective_dob, '%Y-%m-%d').date()
						except ValueError:
							try:
								parsed_dob = datetime.strptime(effective_dob, '%d/%m/%Y').date()
							except ValueError:
								pass

					# Parse coordinates
					parsed_lat = None
					parsed_lng = None
					if latitude and longitude:
						try:
							parsed_lat = float(latitude)
							parsed_lng = float(longitude)
						except (ValueError, TypeError):
							pass

					# Normalize gender
					normalized_gender = 'PREFER_NOT_TO_SAY'
					if gender:
						gender_upper = gender.upper().strip()
						if gender_upper in ('M', 'MALE'):
							normalized_gender = 'MALE'
						elif gender_upper in ('F', 'FEMALE'):
							normalized_gender = 'FEMALE'

					patient = Patient.objects.create(
						firstName=first_name or None,
						lastName=last_name or None,
						dateOfBirth=parsed_dob,
						gender=normalized_gender,
						latitude=parsed_lat,
						longitude=parsed_lng,
						createdBy=created_by,
					)
					patients_created += 1
					Logger.info(f'Created patient: {first_name} {last_name}')

				# Find or create UserStudy record
				user_study, us_created = UserStudy.objects.get_or_create(
					study=dataset,
					patient=patient,
					defaults={
						'reference': reference or f'AUTO-{patient.id}',
						'createdBy': created_by,
					},
				)

				if us_created:
					imported += 1
				else:
					updated += 1

				# Store variable values
				for var_id_str, column_name in variable_mapping.items():
					try:
						var_id = int(var_id_str)
						variable = StudyVariable.objects.filter(id=var_id).first()
						if variable and column_name in row:
							value = str(row.get(column_name, '')).strip()
							if value:
								StudyResult.objects.update_or_create(
									userStudy=user_study,
									studyVariable=variable,
									defaults={'value': value},
								)
					except (ValueError, TypeError):
						pass

				# Also store unmapped columns as auto-created variables
				for col in data_columns:
					if col not in mapped_columns and col not in patient_columns:
						variable = existing_variables.get(col.lower())
						if variable:
							value = str(row.get(col, '')).strip()
							if value:
								StudyResult.objects.update_or_create(
									userStudy=user_study,
									studyVariable=variable,
									defaults={'value': value},
								)

			except Exception as e:
				errors.append({'row': idx + 2, 'error': str(e)})
				Logger.error(f'Error importing row {idx + 2}: {e}')

		Logger.info(f'Import complete: {imported} new, {updated} updated, {patients_created} patients created, {variables_created} variables created')

		return {
			'success': True,
			'imported': imported,
			'updated': updated,
			'patientsCreated': patients_created,
			'variablesCreated': variables_created,
			'skipped': skipped,
			'duplicatesSkipped': duplicates_skipped,
			'errors': errors,
		}

	def executeDataImportStream(self, study_id: int, file_url: str, mapping: dict, column_types: dict = None, created_by=None):
		"""
		Optimized streaming version of executeDataImport - yields progress events for SSE.
		
		Performance optimizations:
		- Pre-fetch all variables by ID upfront (no per-row queries)
		- Cache UserStudy records by reference for quick lookup
		- Skip expensive patient matching when reference match found
		- Use efficient bulk-friendly patterns
		
		Yields:
			dict: Progress events with type 'progress' or 'complete'
		"""
		Logger.info(f'Executing optimized streaming data import for dataset {study_id}')

		# Get dataset and variables
		dataset = self.getById(study_id)
		
		# Pre-fetch ALL variables for this dataset (by ID and by name)
		all_vars = list(dataset.variables.all())
		existing_variables = {v.name.lower(): v for v in all_vars}
		variables_by_id = {str(v.id): v for v in all_vars}

		# Resolve and read file
		file_path = self._resolveFilePath(file_url)
		if not file_path.exists():
			yield {'type': 'error', 'message': f'File not found: {file_path}'}
			return

		columns, all_rows = self._readFileContent(file_path)
		total_rows = len(all_rows)

		# Extract mappings
		patient_mapping = mapping.get('patient', {})
		variable_mapping = mapping.get('variables', {})
		column_types = column_types or {}

		# Patient columns
		patient_col = patient_mapping.get('reference', '')
		first_name_col = patient_mapping.get('firstName', '')
		last_name_col = patient_mapping.get('lastName', '')
		dob_col = patient_mapping.get('dateOfBirth', '')
		age_col = patient_mapping.get('age', '')
		gender_col = patient_mapping.get('gender', '')
		lat_col = patient_mapping.get('latitude', '')
		lng_col = patient_mapping.get('longitude', '')

		# Track stats
		imported = 0
		updated = 0
		patients_created = 0
		variables_created = 0
		skipped = 0
		duplicates_skipped = 0
		errors = []

		# Track in-file duplicates
		seen_patients = set()

		# Create new variables for unmapped columns
		mapped_columns = set(variable_mapping.values())
		patient_columns = {patient_col, first_name_col, last_name_col, dob_col, age_col, gender_col, lat_col, lng_col}
		patient_columns.discard('')

		data_columns = [
			col for col in columns
			if not any(col.lower().startswith(p) for p in self.SKIP_COLUMN_PATTERNS)
		]

		for col in data_columns:
			if col not in mapped_columns and col not in patient_columns:
				if col.lower() not in existing_variables:
					var_type = column_types.get(col, 'TEXT')
					new_var = StudyVariable.objects.create(
						name=col,
						type=var_type,
						description='Auto-created during import',
					)
					dataset.variables.add(new_var)
					existing_variables[col.lower()] = new_var
					variables_by_id[str(new_var.id)] = new_var
					variables_created += 1

		# PRE-FETCH: Cache existing UserStudy records by reference for this dataset
		# This avoids repeated DB lookups during the import loop
		existing_user_studies = {}
		if patient_col:
			for us in UserStudy.objects.filter(study=dataset).select_related('patient'):
				if us.reference:
					existing_user_studies[us.reference] = us

		# Also cache by patient_id for quick lookup
		patient_id_to_user_study = {us.patient_id: us for us in existing_user_studies.values() if us.patient_id}

		# Yield initial progress
		yield {
			'type': 'progress',
			'current': 0,
			'total': total_rows,
			'imported': 0,
			'updated': 0,
			'skipped': 0,
			'patientsCreated': 0,
			'variablesCreated': variables_created,
		}

		# Process each row
		batch_size = 10  # Update progress every 10 rows
		for idx, row in enumerate(all_rows):
			try:
				# Extract patient fields
				reference = str(row.get(patient_col, '')).strip() if patient_col else ''
				first_name = str(row.get(first_name_col, '')).strip() if first_name_col else ''
				last_name = str(row.get(last_name_col, '')).strip() if last_name_col else ''
				dob = str(row.get(dob_col, '')).strip() if dob_col else ''
				age = str(row.get(age_col, '')).strip() if age_col else ''
				gender = str(row.get(gender_col, '')).strip() if gender_col else ''
				latitude = str(row.get(lat_col, '')).strip() if lat_col else ''
				longitude = str(row.get(lng_col, '')).strip() if lng_col else ''

				# Convert age to DOB if needed
				effective_dob = dob
				if age and not dob:
					try:
						age_int = int(float(age))
						birth_year = datetime.now().year - age_int
						effective_dob = f'{birth_year}-01-01'
					except (ValueError, TypeError):
						pass

				# Check valid identifiers
				has_reference = bool(reference)
				has_name = bool(first_name or last_name)
				has_location = bool(latitude and longitude)

				if not has_reference and not has_name and not has_location:
					skipped += 1
					continue

				# Create signature for duplicate detection
				patient_signature = self._createPatientSignature(
					first_name, last_name, reference, effective_dob, age, latitude, longitude
				)

				# Skip in-file duplicates
				if patient_signature and patient_signature in seen_patients:
					duplicates_skipped += 1
					continue
				if patient_signature:
					seen_patients.add(patient_signature)

				# OPTIMIZED: Find patient with cached lookups first
				patient = None
				user_study = None

				# Try cached reference lookup first (fastest path)
				if has_reference and reference in existing_user_studies:
					user_study = existing_user_studies[reference]
					patient = user_study.patient

				# If no cached match but has reference, check DB once
				if not patient and has_reference:
					user_study = UserStudy.objects.filter(study=dataset, reference=reference).select_related('patient').first()
					if user_study and user_study.patient:
						patient = user_study.patient
						existing_user_studies[reference] = user_study

				# Simple name-based patient lookup (faster than _findBestMatchingPatient)
				if not patient and has_name:
					# Quick DB lookup by name - good enough for most cases
					name_query = Patient.objects.all()
					if first_name:
						name_query = name_query.filter(firstName__iexact=first_name)
					if last_name:
						name_query = name_query.filter(lastName__iexact=last_name)
					if effective_dob:
						try:
							dob_date = datetime.strptime(effective_dob, '%Y-%m-%d').date()
							name_query = name_query.filter(dateOfBirth=dob_date)
						except ValueError:
							pass
					patient = name_query.first()

				# Create patient if not found
				if not patient:
					# Parse DOB for patient creation
					parsed_dob = None
					if effective_dob:
						try:
							parsed_dob = datetime.strptime(effective_dob, '%Y-%m-%d').date()
						except ValueError:
							try:
								parsed_dob = datetime.strptime(effective_dob, '%d/%m/%Y').date()
							except ValueError:
								pass

					# Parse coordinates
					parsed_lat = None
					parsed_lng = None
					if latitude and longitude:
						try:
							parsed_lat = float(latitude)
							parsed_lng = float(longitude)
						except (ValueError, TypeError):
							pass

					# Normalize gender
					normalized_gender = 'PREFER_NOT_TO_SAY'
					if gender:
						gender_upper = gender.upper().strip()
						if gender_upper in ('M', 'MALE'):
							normalized_gender = 'MALE'
						elif gender_upper in ('F', 'FEMALE'):
							normalized_gender = 'FEMALE'

					patient = Patient.objects.create(
						firstName=first_name or None,
						lastName=last_name or None,
						dateOfBirth=parsed_dob,
						gender=normalized_gender,
						latitude=parsed_lat,
						longitude=parsed_lng,
						createdBy=created_by,
					)
					patients_created += 1

				# Find or create UserStudy record
				if not user_study or user_study.patient_id != patient.id:
					user_study, us_created = UserStudy.objects.get_or_create(
						study=dataset,
						patient=patient,
						defaults={
							'reference': reference or f'AUTO-{patient.id}',
							'createdBy': created_by,
						},
					)
					if us_created:
						imported += 1
						# Cache for future lookups
						if reference:
							existing_user_studies[reference] = user_study
					else:
						updated += 1
				else:
					updated += 1

				# OPTIMIZED: Store variable values using pre-fetched variables_by_id
				for var_id_str, column_name in variable_mapping.items():
					variable = variables_by_id.get(var_id_str)
					if variable and column_name in row:
						value = str(row.get(column_name, '')).strip()
						if value:
							StudyResult.objects.update_or_create(
								userStudy=user_study,
								studyVariable=variable,
								defaults={'value': value},
							)

				# Also store unmapped columns as auto-created variables
				for col in data_columns:
					if col not in mapped_columns and col not in patient_columns:
						variable = existing_variables.get(col.lower())
						if variable:
							value = str(row.get(col, '')).strip()
							if value:
								StudyResult.objects.update_or_create(
									userStudy=user_study,
									studyVariable=variable,
									defaults={'value': value},
								)

			except Exception as e:
				errors.append({'row': idx + 2, 'error': str(e)})
				Logger.error(f'Error importing row {idx + 2}: {e}')

			# Yield progress every batch_size rows
			if (idx + 1) % batch_size == 0 or idx == total_rows - 1:
				yield {
					'type': 'progress',
					'current': idx + 1,
					'total': total_rows,
					'imported': imported,
					'updated': updated,
					'skipped': skipped,
					'patientsCreated': patients_created,
					'variablesCreated': variables_created,
				}

		Logger.info(f'Streaming import complete: {imported} new, {updated} updated, {patients_created} patients created')

		# Yield final completion event
		yield {
			'type': 'complete',
			'success': True,
			'imported': imported,
			'updated': updated,
			'patientsCreated': patients_created,
			'variablesCreated': variables_created,
			'skipped': skipped,
			'duplicatesSkipped': duplicates_skipped,
			'errors': errors,
		}

