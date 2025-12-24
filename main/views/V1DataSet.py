from drf_spectacular.utils import extend_schema

from vvecon.zorion.auth import Authorized
from vvecon.zorion.logger import Logger
from vvecon.zorion.serializers import Return
from vvecon.zorion.views import API, DeleteMapping, GetMapping, Mapping, PostMapping, PutMapping

from ..payload.requests import FilterDataSetRequest, StudyVariableRequest
from ..payload.responses import DataSetResponse, StudyVariableResponse
from ..services import PatientService, StudyService

__all__ = ['V1DataSet']


@Mapping('api/v1/dataset')
class V1DataSet(API):
	studyService: StudyService = StudyService()
	patientService: PatientService = PatientService()

	# Column patterns to skip when auto-creating variables (from patient match output)
	SKIP_COLUMN_PATTERNS = (
		'matched_',
		'file_duplicate_',
		'file_patient_group',
		'match_status',
		'match_confidence',
		'row_number',
	)

	# Patterns for auto-selecting patient columns
	PATIENT_COLUMN_PATTERNS = {
		'reference': ['patientreference', 'reference', 'ref', 'patient_ref', 'patientid', 'patient_id'],
		'firstName': ['firstname', 'first_name', 'fname', 'first', 'givenname', 'given_name'],
		'lastName': ['lastname', 'last_name', 'lname', 'last', 'surname', 'familyname', 'family_name'],
		'dateOfBirth': ['dob', 'dateofbirth', 'date_of_birth', 'birthdate', 'birth_date', 'birthday'],
		'age': ['age', 'patient_age', 'patientage'],
		'gender': ['gender', 'sex', 'patient_gender', 'patientgender'],
		'latitude': ['latitude', 'lat', 'gps_lat', 'gpslat'],
		'longitude': ['longitude', 'lng', 'lon', 'gps_lng', 'gpslon', 'gps_lon'],
	}

	@extend_schema(
		tags=['Dataset'],
		summary='Get datasets',
		description='Get datasets with filtering, search, and pagination',
		request=FilterDataSetRequest,
		responses={200: DataSetResponse().response()},
	)
	@PostMapping('/')
	@Authorized(True, permissions=['main.view_study'])
	def getDatasets(self, request, data: FilterDataSetRequest):
		Logger.info(f'Validating dataset filter data: {data.initial_data}')
		if data.is_valid(raise_exception=True):
			Logger.info('Dataset filter data is valid')

			# Get pagination info before filtering
			validated_data = data.validated_data.copy()
			pagination_data = validated_data.get('pagination', {})
			page = pagination_data.get('page', 1) if pagination_data else 1
			limit = pagination_data.get('limit', 20) if pagination_data else 20

			# Get filtered queryset WITHOUT pagination for stats
			search_data = validated_data.copy()
			search_data.pop('pagination', None)  # Remove pagination to get all filtered results
			filtered_queryset = self.studyService.search(search_data)

			# Apply sorting
			sort_field = validated_data.get('sortField', 'created_at')
			sort_direction = validated_data.get('sortDirection', 'desc')

			# Map frontend field names to model field names
			field_mapping = {
				'name': 'name',
				'created': 'created_at',
				'version': 'version',
				'category': 'category',
				'created_at': 'created_at',
			}

			# Get the actual field name
			actual_field = field_mapping.get(sort_field, 'created_at')

			# Apply ordering
			if sort_direction == 'asc':
				filtered_queryset = filtered_queryset.order_by(actual_field)
			else:
				filtered_queryset = filtered_queryset.order_by(f'-{actual_field}')

			# Calculate statistics from filtered results
			from django.db.models import Count, Max

			total_count = filtered_queryset.count()

			# Get aggregated stats
			stats_query = filtered_queryset.aggregate(
				totalVariables=Count('variables', distinct=True),
				totalUserStudies=Count('userStudies', distinct=True),
				maxVersion=Max('version'),
			)

			# Now get paginated datasets using paginate method
			datasets = self.studyService.paginate(filtered_queryset, page, limit)

			# Build response
			total_pages = (total_count + limit - 1) // limit if limit > 0 else 1

			response_data = {
				'results': DataSetResponse(data=datasets, many=True).json().data,
				'pagination': {
					'page': page,
					'limit': limit,
					'total': total_count,
					'totalPages': total_pages,
					'hasNext': page < total_pages,
					'hasPrev': page > 1,
				},
				'stats': {
					'total': total_count,
					'totalVariables': stats_query['totalVariables'] or 0,
					'totalUserStudies': stats_query['totalUserStudies'] or 0,
					'latestVersion': stats_query['maxVersion'] or 1,
				},
			}

			Logger.info(f'{len(datasets)} datasets found on page {page}/{total_pages}')
			return Return.ok(response_data)

	@extend_schema(
		tags=['Dataset'],
		summary='Get dataset',
		description='Get single dataset details',
		responses={200: DataSetResponse().response()},
	)
	@GetMapping('/<int:id>')
	@Authorized(True, permissions=['main.view_study'])
	def getDataset(self, request, id: int):
		Logger.info(f'Fetching dataset {id}')
		dataset = self.studyService.getById(id)
		Logger.info(f'Dataset {dataset} fetched')
		return DataSetResponse(data=dataset).json()

	@extend_schema(
		tags=['Dataset'],
		summary='Delete dataset',
		description='Delete dataset',
	)
	@DeleteMapping('/<int:id>')
	@Authorized(True, permissions=['main.delete_study'])
	def deleteDataset(self, request, id: int):
		Logger.info(f'Deleting dataset {id}')
		self.studyService.delete(id)
		Logger.info(f'Dataset {id} deleted')
		return Return.ok()

	# ========== Phase 2 Endpoints ==========

	@extend_schema(
		tags=['Dataset'],
		summary='Get dataset details',
		description='Get full dataset details with variables and statistics',
	)
	@GetMapping('/<int:id>/details')
	@Authorized(True, permissions=['main.view_study'])
	def getDatasetDetails(self, request, id: int):
		Logger.info(f'Fetching dataset details for {id}')
		details = self.studyService.getDetails(id)

		response_data = {
			'dataset': DataSetResponse(data=details['study']).json().data,
			'variables': StudyVariableResponse(data=details['variables'], many=True).json().data,
			'stats': details['stats'],
		}

		Logger.info(f'Dataset {id} details fetched')
		return Return.ok(response_data)

	@extend_schema(
		tags=['Dataset'],
		summary='Get dataset variables',
		description='Get all variables for a dataset',
	)
	@GetMapping('/<int:id>/variables')
	@Authorized(True, permissions=['main.view_study'])
	def getDatasetVariables(self, request, id: int):
		Logger.info(f'Fetching variables for dataset {id}')
		variables = self.studyService.getVariables(id)
		Logger.info(f'{len(variables)} variables found for dataset {id}')
		return StudyVariableResponse(data=variables, many=True).json()

	@extend_schema(
		tags=['Dataset'],
		summary='Add variable to dataset',
		description='Add a new variable to a dataset',
		request=StudyVariableRequest,
	)
	@PostMapping('/<int:id>/variables')
	@Authorized(True, permissions=['main.change_study'])
	def addDatasetVariable(self, request, id: int, data: StudyVariableRequest):
		Logger.info(f'Adding variable to dataset {id}')
		if data.is_valid(raise_exception=True):
			variable = self.studyService.addVariable(id, data.validated_data)
			Logger.info(f'Variable {variable.id} added to dataset {id}')
			return StudyVariableResponse(data=variable).json()

	@extend_schema(
		tags=['Dataset'],
		summary='Update variable',
		description='Update an existing variable',
		request=StudyVariableRequest,
	)
	@PutMapping('/<int:dataset_id>/variables/<int:variable_id>')
	@Authorized(True, permissions=['main.change_study'])
	def updateDatasetVariable(self, request, dataset_id: int, variable_id: int, data: StudyVariableRequest):
		Logger.info(f'Updating variable {variable_id} in dataset {dataset_id}')
		if data.is_valid(raise_exception=True):
			variable = self.studyService.updateVariable(variable_id, data.validated_data)
			Logger.info(f'Variable {variable_id} updated')
			return StudyVariableResponse(data=variable).json()

	@extend_schema(
		tags=['Dataset'],
		summary='Delete variable',
		description='Remove a variable from a dataset',
	)
	@DeleteMapping('/<int:dataset_id>/variables/<int:variable_id>')
	@Authorized(True, permissions=['main.change_study'])
	def deleteDatasetVariable(self, request, dataset_id: int, variable_id: int):
		Logger.info(f'Removing variable {variable_id} from dataset {dataset_id}')
		self.studyService.removeVariable(dataset_id, variable_id)
		Logger.info(f'Variable {variable_id} removed from dataset {dataset_id}')
		return Return.ok()

	@extend_schema(
		tags=['Dataset'],
		summary='Get data preview',
		description='Get paginated data preview for a dataset',
	)
	@PostMapping('/<int:id>/data')
	@Authorized(True, permissions=['main.view_study'])
	def getDataPreview(self, request, id: int):
		Logger.info(f'Fetching data preview for dataset {id}')

		# Get pagination from request body
		page = request.data.get('page', 1)
		limit = request.data.get('limit', 10)

		data_preview = self.studyService.getDataPreview(id, page, limit)
		Logger.info(f'{len(data_preview["rows"])} data rows found for dataset {id}')
		return Return.ok(data_preview)

	@extend_schema(
		tags=['Dataset'],
		summary='Get dataset history',
		description='Get update history timeline for a dataset',
	)
	@GetMapping('/<int:id>/history')
	@Authorized(True, permissions=['main.view_study'])
	def getDatasetHistory(self, request, id: int):
		Logger.info(f'Fetching history for dataset {id}')
		history = self.studyService.getHistory(id)
		Logger.info(f'{len(history)} history events found for dataset {id}')
		return Return.ok({'events': history})

	@extend_schema(
		tags=['Dataset'],
		summary='Get dataset patients',
		description='Get patients who have data entries in this dataset with pagination',
	)
	@GetMapping('/<int:id>/patients')
	@Authorized(True, permissions=['main.view_study'])
	def getDatasetPatients(self, request, id: int):
		Logger.info(f'Fetching patients for dataset {id}')

		page = int(request.GET.get('page', 1))
		limit = int(request.GET.get('limit', 20))

		patients_data = self.studyService.getPatients(id, page, limit)
		Logger.info(f'{len(patients_data.get("patients", []))} patients found for dataset {id}')
		return Return.ok(patients_data)

	@extend_schema(
		tags=['Dataset'],
		summary='Download import template',
		description='Download a template (CSV or Excel) with columns for patient info and dataset variables',
	)
	@GetMapping('/<int:id>/template')
	@Authorized(True, permissions=['main.view_study'])
	def downloadTemplate(self, request, id: int):
		Logger.info(f'Generating import template for dataset {id}')

		import csv
		import io

		from django.http import HttpResponse, StreamingHttpResponse

		# Get format (csv or xlsx) - use 'file_type' param to avoid DRF 'format' conflict
		file_format = request.GET.get('file_type', 'csv').lower()

		# Get dataset and variables
		dataset = self.studyService.getById(id)
		variables = list(dataset.variables.all().order_by('order', 'name'))

		# Define patient info columns (canonical names)
		patient_info_cols = ['PatientReference', 'FirstName', 'LastName', 'DateOfBirth', 'Age', 'Gender', 'Latitude', 'Longitude']

		# Build unique headers: patient info + variables (excluding duplicates)
		used_names = set(col.lower() for col in patient_info_cols)
		headers = patient_info_cols.copy()
		variable_start_index = len(headers)

		for v in variables:
			# Skip if variable name matches a patient column
			if v.name.lower() in used_names:
				continue
			headers.append(v.name)
			used_names.add(v.name.lower())

		safe_name = ''.join(c for c in dataset.name if c.isalnum() or c in (' ', '-', '_')).strip()

		if file_format == 'xlsx':
			# Generate Excel file with data validation
			try:
				from openpyxl import Workbook
				from openpyxl.comments import Comment
				from openpyxl.styles import Alignment, Font, PatternFill
				from openpyxl.utils import get_column_letter
				from openpyxl.worksheet.datavalidation import DataValidation

				wb = Workbook()
				ws = wb.active
				ws.title = 'Import Data'

				# Styles
				patient_fill = PatternFill(start_color='D6EAF8', end_color='D6EAF8', fill_type='solid')
				variable_fill = PatternFill(start_color='D5F5E3', end_color='D5F5E3', fill_type='solid')
				header_font = Font(bold=True)

				# Write headers with styling
				for col_idx, header in enumerate(headers, 1):
					cell = ws.cell(row=1, column=col_idx, value=header)
					cell.font = header_font
					cell.alignment = Alignment(horizontal='center')

					# Color coding
					if col_idx <= variable_start_index:
						cell.fill = patient_fill
					else:
						cell.fill = variable_fill

				# Add column comments (hints)
				hints = {
					'PatientReference': 'Unique patient ID (e.g., PATIENT-001)',
					'FirstName': 'Patient first name',
					'LastName': 'Patient last/family name',
					'DateOfBirth': 'Format: YYYY-MM-DD',
					'Age': 'Number, will create fake DOB if no DOB provided',
					'Gender': 'M or F',
					'Latitude': 'GPS latitude (decimal)',
					'Longitude': 'GPS longitude (decimal)',
				}
				for col_idx, header in enumerate(headers, 1):
					if header in hints:
						ws.cell(row=1, column=col_idx).comment = Comment(hints[header], 'System')

				# Add hints for variables based on type
				for v in variables:
					if v.name.lower() in [col.lower() for col in patient_info_cols]:
						continue
					try:
						col_idx = headers.index(v.name) + 1
						if v.type == 'NUMBER':
							ws.cell(row=1, column=col_idx).comment = Comment('Numeric value', 'System')
						elif v.type == 'DATE':
							ws.cell(row=1, column=col_idx).comment = Comment('Format: YYYY-MM-DD', 'System')
						elif v.type == 'BOOLEAN':
							ws.cell(row=1, column=col_idx).comment = Comment('Yes or No', 'System')
					except ValueError:
						pass

				# Data validations
				# Gender validation
				gender_col = get_column_letter(headers.index('Gender') + 1)
				gender_dv = DataValidation(type='list', formula1='"M,F"', allow_blank=True)
				gender_dv.error = 'Please select M or F'
				gender_dv.prompt = 'Select gender'
				ws.add_data_validation(gender_dv)
				gender_dv.add(f'{gender_col}2:{gender_col}1000')

				# Boolean validations for boolean variables
				for v in variables:
					if v.type == 'BOOLEAN' and v.name in headers:
						col_letter = get_column_letter(headers.index(v.name) + 1)
						bool_dv = DataValidation(type='list', formula1='"Yes,No"', allow_blank=True)
						bool_dv.error = 'Please select Yes or No'
						ws.add_data_validation(bool_dv)
						bool_dv.add(f'{col_letter}2:{col_letter}1000')

				# Add sample rows
				sample_data = [
					['PATIENT-001', 'John', 'Doe', '1985-03-15', '39', 'M', '', ''],
					['PATIENT-002', 'Jane', 'Smith', '', '45', 'F', '', ''],
					['PATIENT-003', '', '', '', '32', '', '6.9271', '79.8612'],
				]
				for row_idx, sample in enumerate(sample_data, 2):
					for col_idx, value in enumerate(sample, 1):
						if col_idx <= len(sample):
							ws.cell(row=row_idx, column=col_idx, value=value)

				# Auto-size columns
				for col_idx, header in enumerate(headers, 1):
					ws.column_dimensions[get_column_letter(col_idx)].width = max(12, len(header) + 2)

				# Save to bytes
				output = io.BytesIO()
				wb.save(output)
				output.seek(0)

				response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
				response['Content-Disposition'] = f'attachment; filename="{safe_name}_import_template.xlsx"'

				Logger.info(f'Excel template generated for dataset {id} with {len(variables)} variables')
				return response

			except ImportError:
				Logger.warning('openpyxl not installed, falling back to CSV')
				file_format = 'csv'

		# Generate CSV (default)
		def generate_csv():
			output = io.StringIO()
			writer = csv.writer(output)

			writer.writerow(headers)
			yield output.getvalue()
			output.seek(0)
			output.truncate(0)

			# Sample rows
			sample_data = [
				('PATIENT-001', 'John', 'Doe', '1985-03-15', '39', 'M', '', ''),
				('PATIENT-002', 'Jane', 'Smith', '', '45', 'F', '', ''),
				('PATIENT-003', '', '', '', '32', '', '6.9271', '79.8612'),
			]
			for sample in sample_data:
				row = list(sample)
				# Pad with empty values for variables
				while len(row) < len(headers):
					row.append('')
				writer.writerow(row)
				yield output.getvalue()
				output.seek(0)
				output.truncate(0)

		response = StreamingHttpResponse(generate_csv(), content_type='text/csv')
		response['Content-Disposition'] = f'attachment; filename="{safe_name}_import_template.csv"'

		Logger.info(f'CSV template generated for dataset {id} with {len(variables)} variables')
		return response

	@extend_schema(
		tags=['Dataset'],
		summary='Create dataset',
		description='Create a new dataset',
	)
	@PostMapping('/create')
	@Authorized(True, permissions=['main.add_study'])
	def createDataset(self, request):
		Logger.info('Creating new dataset')
		data = request.data

		# Create the dataset
		from ..models import Study
		dataset = Study.objects.create(
			name=data.get('name'),
			description=data.get('description', ''),
			category=data.get('category'),
			status=data.get('status', 'ACTIVE'),
			reference=data.get('reference', ''),
			createdBy=request.user,
			version=1,
		)

		Logger.info(f'Dataset {dataset.id} created')
		return DataSetResponse(data=dataset).json()

	@extend_schema(
		tags=['Dataset'],
		summary='Update dataset',
		description='Update an existing dataset',
	)
	@PutMapping('/<int:id>')
	@Authorized(True, permissions=['main.change_study'])
	def updateDataset(self, request, id: int):
		Logger.info(f'Updating dataset {id}')
		data = request.data

		dataset = self.studyService.getById(id)

		# Track changes for history
		changes = []
		if 'name' in data and data['name'] != dataset.name:
			changes.append(f"Name changed from '{dataset.name}' to '{data['name']}'")
			dataset.name = data['name']
		if 'description' in data and data['description'] != dataset.description:
			changes.append('Description updated')
			dataset.description = data['description']
		if 'category' in data and data['category'] != dataset.category:
			changes.append(f"Category changed to '{data['category']}'")
			dataset.category = data['category']
		if 'status' in data and data['status'] != dataset.status:
			changes.append(f"Status changed to '{data['status']}'")
			dataset.status = data['status']
		if 'reference' in data and data['reference'] != dataset.reference:
			changes.append('Reference updated')
			dataset.reference = data['reference']

		# Increment version if there are changes
		if changes:
			dataset.version = (dataset.version or 1) + 1
			dataset.save()
			Logger.info(f'Dataset {id} updated to version {dataset.version}: {", ".join(changes)}')
		else:
			Logger.info(f'No changes made to dataset {id}')

		return DataSetResponse(data=dataset).json()

	@extend_schema(
		tags=['Dataset'],
		summary='Preview import data',
		description='Parse uploaded file and preview data for import with column detection',
	)
	@PostMapping('/<int:id>/import/preview')
	@Authorized(True, permissions=['main.change_study'])
	def previewImportData(self, request, id: int):
		Logger.info(f'Previewing import data for dataset {id}')

		data = request.data
		file_url = data.get('fileUrl')
		mapping = data.get('mapping')
		preview_mode = data.get('preview', False)

		if not file_url:
			return Return.badRequest('No file URL provided')

		# Get dataset and variables
		dataset = self.studyService.getById(id)
		variables = list(dataset.variables.all())

		try:
			# Parse file (simplified - in production would use pandas/openpyxl)
			import csv

			# Construct file path from URL
			file_path = file_url.replace('/media/', 'media/')

			columns = []
			sample_rows = []
			all_rows = []

			if file_path.endswith('.csv'):
				# Try multiple encodings to handle various file sources
				encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
				file_content = None
				for encoding in encodings:
					try:
						with open(file_path, encoding=encoding) as f:
							file_content = f.read()
						break
					except UnicodeDecodeError:
						continue

				if file_content is None:
					# Last resort: read with errors='replace'
					with open(file_path, encoding='utf-8', errors='replace') as f:
						file_content = f.read()

				# Parse CSV from string
				import io
				reader = csv.DictReader(io.StringIO(file_content))
				columns = reader.fieldnames or []
				for i, row in enumerate(reader):
					all_rows.append(row)
					if i < 5:
						sample_rows.append(row)

			# If just parsing (step 1), return columns with system column info
			if not preview_mode or not mapping:
				# Identify system columns to skip for variable creation
				system_columns = []
				data_columns = []
				for col in columns:
					is_system = any(col.lower().startswith(pattern.lower()) or col.lower() == pattern.lower()
									for pattern in self.SKIP_COLUMN_PATTERNS)
					if is_system:
						system_columns.append(col)
					else:
						data_columns.append(col)

				# Auto-suggest patient field mappings based on column names
				patient_suggestions = {}
				for field, patterns in self.PATIENT_COLUMN_PATTERNS.items():
					for col in columns:
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

				# Detect data types from sample values
				import re
				column_types = {}
				date_pattern = re.compile(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}$|^\d{1,2}[-/]\d{1,2}[-/]\d{4}$')
				bool_values = {'yes', 'no', 'true', 'false', 'y', 'n', '1', '0'}

				for col in data_columns:
					# Get non-empty sample values
					sample_values = [row.get(col, '').strip() for row in all_rows[:20] if row.get(col, '').strip()]
					if not sample_values:
						column_types[col] = 'TEXT'
						continue

					# Check if all values are numbers
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

				return Return.ok({
					'columns': columns,
					'dataColumns': data_columns,
					'systemColumns': system_columns,
					'sampleRows': sample_rows,
					'totalRows': len(all_rows),
					'patientSuggestions': patient_suggestions,
					'variableSuggestions': variable_suggestions,
					'columnTypes': column_types,
				})

			# If preview mode (step 2), analyze data
			# Get patient field mappings
			patient_mapping = mapping.get('patient', {})
			patient_col = patient_mapping.get('reference', '') or mapping.get('patientColumn', '')
			first_name_col = patient_mapping.get('firstName', '')
			last_name_col = patient_mapping.get('lastName', '')
			dob_col = patient_mapping.get('dateOfBirth', '')
			age_col = patient_mapping.get('age', '')
			gender_col = patient_mapping.get('gender', '')
			lat_col = patient_mapping.get('latitude', '')
			lng_col = patient_mapping.get('longitude', '')

			# Legacy support: patient identifier type
			patient_identifier = mapping.get('patientIdentifier', 'reference')
			variable_mapping = mapping.get('variables', {})

			from datetime import datetime

			from ..models import Patient, UserStudy

			# Track within-file duplicates
			seen_patients = {}  # signature -> first row number
			patient_groups = {}  # signature -> group id
			next_group_id = 1

			rows_result = []
			new_count = 0
			update_count = 0
			error_count = 0
			file_duplicate_count = 0
			errors = []

			for idx, row in enumerate(all_rows):
				row_number = idx + 2  # Excel row (1-indexed + header)

				# Extract patient fields from row
				reference = row.get(patient_col, '').strip() if patient_col else ''
				first_name = row.get(first_name_col, '').strip() if first_name_col else ''
				last_name = row.get(last_name_col, '').strip() if last_name_col else ''
				dob = row.get(dob_col, '').strip() if dob_col else ''
				age = row.get(age_col, '').strip() if age_col else ''
				gender = row.get(gender_col, '').strip() if gender_col else ''
				latitude = row.get(lat_col, '').strip() if lat_col else ''
				longitude = row.get(lng_col, '').strip() if lng_col else ''

				# Convert age to fake DOB if needed
				effective_dob = dob
				if age and not dob:
					try:
						age_int = int(float(age))
						birth_year = datetime.now().year - age_int
						effective_dob = f'{birth_year}-01-01'
					except (ValueError, TypeError):
						pass

				# Check for valid patient identifier
				has_reference = bool(reference)
				has_name = bool(first_name or last_name)
				has_location = bool(latitude and longitude)

				if not has_reference and not has_name and not has_location:
					errors.append({'row': row_number, 'message': 'Missing patient identifier (need reference, name, or location)'})
					error_count += 1
					continue

				# Create patient signature for duplicate detection
				sig_parts = []
				if first_name:
					sig_parts.append(first_name.lower())
				if last_name:
					sig_parts.append(last_name.lower())
				if reference:
					sig_parts.append(f'ref:{reference.lower()}')
				if effective_dob:
					sig_parts.append(effective_dob)
				elif age:
					sig_parts.append(f'age:{age}')
				if latitude and longitude:
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
						# Duplicate of earlier row
						file_duplicate_of = str(seen_patients[patient_signature])
						file_duplicate_count += 1
						file_group = patient_groups.get(patient_signature, '')
					else:
						seen_patients[patient_signature] = row_number
						file_group = f'G{next_group_id}'
						patient_groups[patient_signature] = file_group
						next_group_id += 1

				# Find patient in database using PatientService
				patient = None
				match = None

				# Try reference first (fastest/most accurate)
				# Reference is on UserStudy (the join table), not on Patient directly
				if has_reference:
					user_study = UserStudy.objects.filter(study=dataset, reference=reference).select_related('patient').first()
					if user_study and user_study.patient:
						patient = user_study.patient

				# If no reference match, try advanced matching
				if not patient and (has_name or has_location):
					match = self.patientService._findBestMatchingPatient(
						first_name, last_name, effective_dob, gender, latitude, longitude
					)
					if match:
						patient = Patient.objects.filter(id=match['id']).first()

				# Determine status
				status = 'new'
				if patient:
					existing = UserStudy.objects.filter(study=dataset, patient=patient).exists()
					if existing:
						status = 'update'
						update_count += 1
					else:
						new_count += 1
				else:
					status = 'error'
					identifier = reference or f'{first_name} {last_name}'.strip() or f'({latitude}, {longitude})'
					errors.append({'row': row_number, 'message': f'Patient not found: {identifier}'})
					error_count += 1

				# Build values dict
				values = {}
				for var_id, col_name in variable_mapping.items():
					values[var_id] = row.get(col_name, '')

				rows_result.append({
					'rowNumber': row_number,
					'patientName': reference or f'{first_name} {last_name}'.strip(),
					'patientId': patient.id if patient else None,
					'matchedPatient': match,
					'status': status,
					'values': values,
					'fileDuplicateOf': file_duplicate_of,
					'fileGroup': file_group,
				})

			return Return.ok({
				'total': len(all_rows),
				'newCount': new_count,
				'updateCount': update_count,
				'errorCount': error_count,
				'fileDuplicates': file_duplicate_count,
				'uniquePatients': next_group_id - 1,
				'errors': errors[:20],  # Limit errors
				'rows': rows_result[:100],  # Limit preview rows
			})

		except Exception as e:
			Logger.error(f'Error previewing import: {e!s}')
			return Return.badRequest(f'Failed to parse file: {e!s}')

	@extend_schema(
		tags=['Dataset'],
		summary='Execute data import',
		description='Execute the data import from uploaded file into the dataset',
	)
	@PostMapping('/<int:id>/import/execute')
	@Authorized(True, permissions=['main.change_study'])
	def executeImportData(self, request, id: int):
		Logger.info(f'Executing data import for dataset {id}')

		data = request.data
		file_url = data.get('fileUrl')
		mapping = data.get('mapping')
		column_types = data.get('columnTypes', {})  # Detected types from frontend

		if not file_url or not mapping:
			return Return.badRequest('File URL and mapping are required')

		# Get dataset and variables
		dataset = self.studyService.getById(id)
		existing_variables = {v.name.lower(): v for v in dataset.variables.all()}

		try:
			import csv
			from datetime import datetime

			file_path = file_url.replace('/media/', 'media/')

			# Get patient field mappings
			patient_mapping = mapping.get('patient', {})
			patient_col = patient_mapping.get('reference', '') or mapping.get('patientColumn', '')
			first_name_col = patient_mapping.get('firstName', '')
			last_name_col = patient_mapping.get('lastName', '')
			dob_col = patient_mapping.get('dateOfBirth', '')
			age_col = patient_mapping.get('age', '')
			gender_col = patient_mapping.get('gender', '')
			lat_col = patient_mapping.get('latitude', '')
			lng_col = patient_mapping.get('longitude', '')

			variable_mapping = mapping.get('variables', {})

			from ..models import Patient, StudyResult, StudyVariable, UserStudy

			imported = 0
			updated = 0
			skipped = 0
			failed = 0
			variables_created = 0
			duplicates_skipped = 0
			patients_created = 0

			# Track within-file duplicates
			seen_patients = set()

			# Auto-create variables for unmapped columns (always enabled)
			auto_created_vars = {}

			# Read headers from file with encoding handling
			import io
			encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
			file_content = None
			for encoding in encodings:
				try:
					with open(file_path, encoding=encoding) as f:
						file_content = f.read()
					break
				except UnicodeDecodeError:
					continue
			if file_content is None:
				with open(file_path, encoding='utf-8', errors='replace') as f:
					file_content = f.read()

			reader = csv.reader(io.StringIO(file_content))
			headers = next(reader, [])

			# Patient mapping columns to exclude from variable creation
			patient_cols = {patient_col, first_name_col, last_name_col, dob_col, age_col, gender_col, lat_col, lng_col}
			patient_cols = {c for c in patient_cols if c}  # Remove empty strings

			# Mapped variable columns
			mapped_cols = set(variable_mapping.values())

			for col in headers:
				# Skip if already mapped as patient info or variable
				if col in patient_cols or col in mapped_cols:
					continue

				# Skip system columns from patient match output
				is_system = any(
					col.lower().startswith(pattern.lower()) or col.lower() == pattern.lower()
					for pattern in self.SKIP_COLUMN_PATTERNS
				)
				if is_system:
					continue

				# Skip if variable with same name exists
				if col.lower() in existing_variables:
					auto_created_vars[col] = existing_variables[col.lower()]
					continue

				# Get detected type from frontend, default to TEXT
				var_type = column_types.get(col, 'TEXT')

				# Create new variable with detected type
				new_var = StudyVariable.objects.create(
					study=dataset,
					name=col,
					type=var_type,
					status='ACTIVE',
					order=len(existing_variables) + variables_created,
				)
				auto_created_vars[col] = new_var
				variables_created += 1
				Logger.info(f'Auto-created variable: {col} (type: {var_type}) for dataset {id}')

			# Read file with encoding handling
			import io
			encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
			file_content = None
			for encoding in encodings:
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

			for row in reader:
				# Extract patient fields from row
				reference = row.get(patient_col, '').strip() if patient_col else ''
				first_name = row.get(first_name_col, '').strip() if first_name_col else ''
				last_name = row.get(last_name_col, '').strip() if last_name_col else ''
				dob = row.get(dob_col, '').strip() if dob_col else ''
				age = row.get(age_col, '').strip() if age_col else ''
				gender = row.get(gender_col, '').strip() if gender_col else ''
				latitude = row.get(lat_col, '').strip() if lat_col else ''
				longitude = row.get(lng_col, '').strip() if lng_col else ''

				# Convert age to fake DOB if needed
				effective_dob = dob
				if age and not dob:
					try:
						age_int = int(float(age))
						birth_year = datetime.now().year - age_int
						effective_dob = f'{birth_year}-01-01'
					except (ValueError, TypeError):
						pass

				# Check for valid patient identifier
				has_reference = bool(reference)
				has_name = bool(first_name or last_name)
				has_location = bool(latitude and longitude)

				if not has_reference and not has_name and not has_location:
					skipped += 1
					continue

				# Create patient signature for duplicate detection
				sig_parts = []
				if first_name:
					sig_parts.append(first_name.lower())
				if last_name:
					sig_parts.append(last_name.lower())
				if reference:
					sig_parts.append(f'ref:{reference.lower()}')
				if effective_dob:
					sig_parts.append(effective_dob)
				elif age:
					sig_parts.append(f'age:{age}')
				if latitude and longitude:
					try:
						sig_parts.append(f'loc:{round(float(latitude), 3)},{round(float(longitude), 3)}')
					except (ValueError, TypeError):
						pass

				patient_signature = '|'.join(sig_parts) if sig_parts else None

				# Skip within-file duplicates (only import first occurrence)
				if patient_signature and patient_signature in seen_patients:
					duplicates_skipped += 1
					continue
				if patient_signature:
					seen_patients.add(patient_signature)

				# Find patient using PatientService
				patient = None

				# Try reference first
				# Reference is on UserStudy (the join table), not on Patient directly
				if has_reference:
					user_study = UserStudy.objects.filter(study=dataset, reference=reference).select_related('patient').first()
					if user_study and user_study.patient:
						patient = user_study.patient

				# If no reference match, try advanced matching
				if not patient and (has_name or has_location):
					match = self.patientService._findBestMatchingPatient(
						first_name, last_name, effective_dob, gender, latitude, longitude
					)
					if match:
						patient = Patient.objects.filter(id=match['id']).first()

				if not patient:
					# Create patient if we have enough info (at least name or reference)
					if has_reference or has_name:
						# Parse DOB if available
						parsed_dob = None
						if effective_dob:
							try:
								from dateutil import parser
								parsed_dob = parser.parse(effective_dob).date()
							except Exception:
								pass

						# Parse coordinates
						parsed_lat, parsed_lng = None, None
						if latitude and longitude:
							try:
								parsed_lat = float(latitude)
								parsed_lng = float(longitude)
							except (ValueError, TypeError):
								pass

						patient = Patient.objects.create(
							reference=reference or f'AUTO-{datetime.now().strftime("%Y%m%d%H%M%S")}-{imported + 1}',
							firstName=first_name or '',
							lastName=last_name or '',
							dateOfBirth=parsed_dob,
							gender=gender.upper()[:1] if gender else '',
							latitude=parsed_lat,
							longitude=parsed_lng,
							createdBy=request.user,
						)
						patients_created += 1
						Logger.info(f'Auto-created patient: {patient.reference} for dataset {id}')
					else:
						# Can't create patient without name or reference
						failed += 1
						continue

				# Create or update UserStudy
				user_study, created = UserStudy.objects.get_or_create(
					study=dataset,
					patient=patient,
					defaults={
						'status': 'ACTIVE',
						'createdBy': request.user,
					},
				)

				if created:
					imported += 1
				else:
					updated += 1

				# Create/update StudyResults for mapped variables
				for var_id, col_name in variable_mapping.items():
					value = row.get(col_name, '').strip()
					if value:
						try:
							variable = StudyVariable.objects.get(id=var_id)
							StudyResult.objects.update_or_create(
								userStudy=user_study,
								studyVariable=variable,
								defaults={'value': value},
							)
						except StudyVariable.DoesNotExist:
							pass

				# Create/update StudyResults for auto-created variables
				for col_name, variable in auto_created_vars.items():
					value = row.get(col_name, '').strip()
					if value:
						StudyResult.objects.update_or_create(
							userStudy=user_study,
							studyVariable=variable,
							defaults={'value': value},
						)

			Logger.info(f'Import complete for dataset {id}: {imported} imported, {updated} updated, {skipped} skipped, {failed} failed, {duplicates_skipped} duplicates skipped, {variables_created} variables created, {patients_created} patients created')

			return Return.ok({
				'imported': imported,
				'updated': updated,
				'skipped': skipped,
				'failed': failed,
				'duplicatesSkipped': duplicates_skipped,
				'variablesCreated': variables_created,
				'patientsCreated': patients_created,
			})

		except Exception as e:
			Logger.error(f'Error executing import: {e!s}')
			return Return.badRequest(f'Import failed: {e!s}')

