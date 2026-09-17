import csv
import io
import json
import time

from django.db.models import Count, Max
from django.http import HttpResponse, StreamingHttpResponse
from drf_spectacular.utils import extend_schema
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from vvecon.zorion.auth import Authorized
from vvecon.zorion.logger import Logger
from vvecon.zorion.serializers import Return
from vvecon.zorion.views import API, DeleteMapping, GetMapping, Mapping, PostMapping, PutMapping

from ..models import DataImportJob, Study
from ..payload.requests import FilterDataSetRequest, StudyVariableRequest
from ..payload.responses import DataSetResponse, StudyVariableResponse
from ..services import DataImportService, PatientService, StudyService

__all__ = ['V1DataSet']


@Mapping('api/v1/dataset')
class V1DataSet(API):
	studyService: StudyService = StudyService()
	patientService: PatientService = PatientService()
	importService: DataImportService = DataImportService()

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
		'testedDate': ['tested_date', 'testeddate', 'test_date', 'testdate', 'collection_date', 'visit_date'],
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
	@GetMapping('/<int:dataset_id>')
	@Authorized(True, permissions=['main.view_study'])
	def getDataset(self, request, dataset_id: int):
		Logger.info(f'Fetching dataset {dataset_id}')
		dataset = self.studyService.getById(dataset_id)
		Logger.info(f'Dataset {dataset} fetched')
		return DataSetResponse(data=dataset).json()

	@extend_schema(
		tags=['Dataset'],
		summary='Delete dataset',
		description='Delete dataset',
	)
	@DeleteMapping('/<int:dataset_id>')
	@Authorized(True, permissions=['main.delete_study'])
	def deleteDataset(self, request, dataset_id: int):
		Logger.info(f'Deleting dataset {dataset_id}')
		self.studyService.delete(dataset_id)
		Logger.info(f'Dataset {dataset_id} deleted')
		return Return.ok()

	@extend_schema(
		tags=['Dataset'],
		summary='Get related variables',
		description='Get variables related to the selected variable',
	)
	@GetMapping('/<int:dataset_id>/advanced-filter/related-variables/<int:variable_id>')
	@Authorized(True, permissions=['main.view_study'])
	def getRelatedVariables(self, request, dataset_id: int, variable_id: int):
		Logger.info(f'Fetching related variables for {variable_id} in dataset {dataset_id}')
		variables = self.studyService.getRelatedVariables(dataset_id, variable_id)
		return StudyVariableResponse(data=variables, many=True).json()

	# ========== Phase 2 Endpoints ==========

	@extend_schema(
		tags=['Dataset'],
		summary='Get dataset details',
		description='Get full dataset details with variables and statistics',
	)
	@GetMapping('/<int:dataset_id>/details')
	@Authorized(True, permissions=['main.view_study'])
	def getDatasetDetails(self, request, dataset_id: int):
		Logger.info(f'Fetching dataset details for {dataset_id}')
		details = self.studyService.getDetails(dataset_id)

		response_data = {
			'dataset': DataSetResponse(data=details['study']).json().data,
			'variables': StudyVariableResponse(data=details['variables'], many=True).json().data,
			'stats': details['stats'],
		}

		Logger.info(f'Dataset {dataset_id} details fetched')
		return Return.ok(response_data)

	@extend_schema(
		tags=['Dataset'],
		summary='Get dataset variables',
		description='Get all variables for a dataset',
	)
	@GetMapping('/<int:dataset_id>/variables')
	@Authorized(True, permissions=['main.view_study'])
	def getDatasetVariables(self, request, dataset_id: int):
		Logger.info(f'Fetching variables for dataset {dataset_id}')
		variables = self.studyService.getVariables(dataset_id)
		Logger.info(f'{len(variables)} variables found for dataset {dataset_id}')
		return StudyVariableResponse(data=variables, many=True).json()

	@extend_schema(
		tags=['Dataset'],
		summary='Add variable to dataset',
		description='Add a new variable to a dataset',
		request=StudyVariableRequest,
	)
	@PostMapping('/<int:dataset_id>/variables')
	@Authorized(True, permissions=['main.change_study'])
	def addDatasetVariable(self, request, dataset_id: int, data: StudyVariableRequest):
		Logger.info(f'Adding variable to dataset {dataset_id}')
		if data.is_valid(raise_exception=True):
			variable = self.studyService.addVariable(dataset_id, data.validated_data)
			Logger.info(f'Variable {variable.id} added to dataset {dataset_id}')
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
	@PostMapping('/<int:dataset_id>/data')
	@Authorized(True, permissions=['main.view_study'])
	def getDataPreview(self, request, dataset_id: int):
		Logger.info(f'Fetching data preview for dataset {dataset_id}')

		# Get pagination from request body
		page = request.data.get('page', 1)
		limit = request.data.get('limit', 10)

		data_preview = self.studyService.getDataPreview(dataset_id, page, limit)
		Logger.info(f'{len(data_preview["rows"])} data rows found for dataset {dataset_id}')
		return Return.ok(data_preview)

	@extend_schema(
		tags=['Dataset'],
		summary='Get advanced filter metadata',
		description='Get filterable known patient fields and dataset variables with operators',
	)
	@PostMapping('/<int:dataset_id>/advanced-filter/meta')
	@Authorized(True, permissions=['main.view_study'])
	def getAdvancedFilterMeta(self, request, dataset_id: int):
		Logger.info(f'Fetching advanced filter metadata for dataset {dataset_id}')
		study_ids = request.data.get('study_ids')
		meta = self.studyService.getAdvancedFilterMeta(dataset_id, study_ids=study_ids)
		return Return.ok(meta)

	@extend_schema(
		tags=['Dataset'],
		summary='Query advanced filtered data',
		description='Filter dataset rows by dynamic type-aware rules and return paginated results',
	)
	@PostMapping('/<int:dataset_id>/advanced-filter/query')
	@Authorized(True, permissions=['main.view_study'])
	def queryAdvancedFilteredData(self, request, dataset_id: int):
		Logger.info(f'Applying advanced filters for dataset {dataset_id}')

		payload = request.data or {}
		filters = payload.get('filters', []) or []
		filter_logic = payload.get('filterLogic', 'AND')
		page = payload.get('page', 1)
		limit = payload.get('limit', 25)
		sort_field = payload.get('sortField', 'created_at')
		sort_direction = payload.get('sortDirection', 'desc')

		data = self.studyService.getAdvancedFilteredData(
			study_id=dataset_id,
			filters=filters,
			filter_logic=filter_logic,
			page=page,
			limit=limit,
			sort_field=sort_field,
			sort_direction=sort_direction,
		)

		# allRows is only needed for export, keep query response slim
		data.pop('allRows', None)
		return Return.ok(data)

	@extend_schema(
		tags=['Dataset'],
		summary='Export advanced filtered data to CSV',
		description='Download full filtered dataset table (patient columns + all variable columns)',
	)
	@PostMapping('/<int:dataset_id>/advanced-filter/export')
	@Authorized(True, permissions=['main.view_study'])
	def exportAdvancedFilteredDataCsv(self, request, dataset_id: int):
		Logger.info(f'Exporting advanced filtered CSV for dataset {dataset_id}')

		payload = request.data or {}
		filters = payload.get('filters', []) or []
		filter_logic = payload.get('filterLogic', 'AND')
		sort_field = payload.get('sortField', 'created_at')
		sort_direction = payload.get('sortDirection', 'desc')

		data = self.studyService.getAdvancedFilteredData(
			study_id=dataset_id,
			filters=filters,
			filter_logic=filter_logic,
			page=1,
			limit=1000000,
			sort_field=sort_field,
			sort_direction=sort_direction,
		)

		dataset = data.get('dataset', {})
		dataset_name = dataset.get('name', f'dataset_{dataset_id}')
		safe_name = ''.join(c for c in dataset_name if c.isalnum() or c in (' ', '-', '_')).strip()
		if not safe_name:
			safe_name = f'dataset_{dataset_id}'

		known_columns = [
			# ('userStudyId', 'UserStudyID'),
			('patientId', 'PatientID'),
			('reference', 'Reference'),
			('firstName', 'FirstName'),
			('lastName', 'LastName'),
			('fullName', 'FullName'),
			('gender', 'Gender'),
			('dateOfBirth', 'DateOfBirth'),
			('age', 'Age'),
			('latitude', 'Latitude'),
			('longitude', 'Longitude'),
			('testedDate', 'TestedDate'),
			('status', 'EntryStatus'),
			('created_at', 'CreatedAt'),
		]
		variable_columns = data.get('columns', [])
		rows = data.get('allRows', [])

		def generate_csv():
			output = io.StringIO()
			writer = csv.writer(output)

			headers = [col_label for _, col_label in known_columns] + [v['name'] for v in variable_columns]
			writer.writerow(headers)
			yield output.getvalue()
			output.seek(0)
			output.truncate(0)

			for row in rows:
				line = [row.get(col_key, '') for col_key, _ in known_columns]
				line.extend([
					row.get('values', {}).get(str(variable['id']), '')
					for variable in variable_columns
				])
				writer.writerow(line)
				yield output.getvalue()
				output.seek(0)
				output.truncate(0)

		response = StreamingHttpResponse(generate_csv(), content_type='text/csv')
		response['Content-Disposition'] = f'attachment; filename="{safe_name}_advanced_filtered.csv"'
		return response

	# ========== Multi-dataset advanced filtering (Admin "Advanced Filter" page) ==========
	# Same filtering engine as the endpoints above, generalized to filter and merge
	# rows from several datasets at once. Variable rules are matched by NAME - a
	# StudyVariable's numeric id is local to one dataset, so it can't be reused to
	# find "the same" variable in a different dataset.

	@extend_schema(
		tags=['Dataset'],
		summary='Get advanced filter metadata for multiple datasets',
		description='Get known patient fields plus the union of dataset variables across all selected datasets',
	)
	@PostMapping('/advanced-filter/meta')
	@Authorized(True, permissions=['main.view_study'])
	def getMultiDatasetAdvancedFilterMeta(self, request):
		study_ids = request.data.get('studyIds') or []
		Logger.info(f'Fetching advanced filter metadata for datasets {study_ids}')

		meta = self.studyService.getAdvancedFilterMeta(study_ids=study_ids)
		datasets = self.studyService.model.objects.filter(id__in=study_ids) if study_ids else []
		meta['datasets'] = [{'id': s.id, 'name': s.name} for s in datasets]
		return Return.ok(meta)

	@extend_schema(
		tags=['Dataset'],
		summary='Search dataset variables across multiple datasets',
		description='Type-ahead search over the union of variables across selected datasets, '
					'for the variable field-key picker',
	)
	@PostMapping('/advanced-filter/variables/search')
	@Authorized(True, permissions=['main.view_study'])
	def searchMultiDatasetAdvancedFilterVariables(self, request):
		payload = request.data or {}
		study_ids = payload.get('studyIds') or []
		search = payload.get('search', '')

		variables = self.studyService.searchVariablesAcrossStudies(study_ids, query=search, limit=50)
		return Return.ok({'variables': variables})

	@extend_schema(
		tags=['Dataset'],
		summary='Query advanced filtered data across multiple datasets',
		description='Filter, merge, sort and paginate rows from several datasets by dynamic type-aware rules',
	)
	@PostMapping('/advanced-filter/query')
	@Authorized(True, permissions=['main.view_study'])
	def queryMultiDatasetAdvancedFilteredData(self, request):
		payload = request.data or {}
		study_ids = payload.get('studyIds') or []
		Logger.info(f'Applying advanced filters across datasets {study_ids}')

		data = self.studyService.getMultiStudyAdvancedFilteredData(
			study_ids=study_ids,
			filters=payload.get('filters', []) or [],
			filter_logic=payload.get('filterLogic', 'AND'),
			page=payload.get('page', 1),
			limit=payload.get('limit', 25),
			sort_field=payload.get('sortField', 'created_at'),
			sort_direction=payload.get('sortDirection', 'desc'),
		)

		# allRows is only needed for export, keep query response slim
		data.pop('allRows', None)
		return Return.ok(data)

	@extend_schema(
		tags=['Dataset'],
		summary='Export advanced filtered data across multiple datasets to CSV',
		description='Download merged or per-dataset-grouped filtered rows as CSV',
	)
	@PostMapping('/advanced-filter/export')
	@Authorized(True, permissions=['main.view_study'])
	def exportMultiDatasetAdvancedFilteredDataCsv(self, request):
		payload = request.data or {}
		study_ids = payload.get('studyIds') or []
		output_format = 'grouped' if payload.get('outputFormat') == 'grouped' else 'merged'
		Logger.info(f'Exporting advanced filtered CSV ({output_format}) for datasets {study_ids}')

		data = self.studyService.getMultiStudyAdvancedFilteredData(
			study_ids=study_ids,
			filters=payload.get('filters', []) or [],
			filter_logic=payload.get('filterLogic', 'AND'),
			page=1,
			limit=1000000,
			sort_field=payload.get('sortField', 'created_at'),
			sort_direction=payload.get('sortDirection', 'desc'),
		)

		known_columns = [
			('_studyName', 'Dataset'),
			('patientId', 'PatientID'),
			('reference', 'Reference'),
			('firstName', 'FirstName'),
			('lastName', 'LastName'),
			('fullName', 'FullName'),
			('gender', 'Gender'),
			('dateOfBirth', 'DateOfBirth'),
			('age', 'Age'),
			('latitude', 'Latitude'),
			('longitude', 'Longitude'),
			('testedDate', 'TestedDate'),
			('status', 'EntryStatus'),
			('created_at', 'CreatedAt'),
		]
		variable_columns = data.get('columns', [])
		rows = data.get('allRows', [])

		def row_values(row, columns):
			line = [row.get(key, '') for key, _ in columns]
			line.extend([row.get('valuesByName', {}).get(v['name'].lower(), '') for v in variable_columns])
			return line

		def generate_csv():
			output = io.StringIO()
			writer = csv.writer(output)

			if output_format == 'grouped':
				grouped_columns = [c for c in known_columns if c[0] != '_studyName']
				grouped = {}
				for row in rows:
					grouped.setdefault(row.get('_studyName', ''), []).append(row)

				for study_name, study_rows in grouped.items():
					writer.writerow([f'Dataset: {study_name}'])
					writer.writerow([label for _, label in grouped_columns] + [v['name'] for v in variable_columns])
					yield output.getvalue()
					output.seek(0)
					output.truncate(0)

					for row in study_rows:
						writer.writerow(row_values(row, grouped_columns))
						yield output.getvalue()
						output.seek(0)
						output.truncate(0)

					writer.writerow([])
					yield output.getvalue()
					output.seek(0)
					output.truncate(0)
			else:
				writer.writerow([label for _, label in known_columns] + [v['name'] for v in variable_columns])
				yield output.getvalue()
				output.seek(0)
				output.truncate(0)

				for row in rows:
					writer.writerow(row_values(row, known_columns))
					yield output.getvalue()
					output.seek(0)
					output.truncate(0)

		response = StreamingHttpResponse(generate_csv(), content_type='text/csv')
		response['Content-Disposition'] = 'attachment; filename="advanced_filtered_multi_dataset.csv"'
		return response

	@extend_schema(
		tags=['Dataset'],
		summary='Get dataset history',
		description='Get update history timeline for a dataset',
	)
	@GetMapping('/<int:dataset_id>/history')
	@Authorized(True, permissions=['main.view_study'])
	def getDatasetHistory(self, request, dataset_id: int):
		Logger.info(f'Fetching history for dataset {dataset_id}')
		history = self.studyService.getHistory(dataset_id)
		Logger.info(f'{len(history)} history events found for dataset {dataset_id}')
		return Return.ok({'events': history})

	@extend_schema(
		tags=['Dataset'],
		summary='Get dataset patients',
		description='Get patients who have data entries in this dataset with pagination',
	)
	@GetMapping('/<int:dataset_id>/patients')
	@Authorized(True, permissions=['main.view_study'])
	def getDatasetPatients(self, request, dataset_id: int):
		Logger.info(f'Fetching patients for dataset {dataset_id}')

		page = int(request.GET.get('page', 1))
		limit = int(request.GET.get('limit', 20))

		patients_data = self.studyService.getPatients(dataset_id, page, limit)
		Logger.info(f'{len(patients_data.get("patients", []))} patients found for dataset {dataset_id}')
		return Return.ok(patients_data)

	@extend_schema(
		tags=['Dataset'],
		summary='Download import template',
		description='Download a template (CSV or Excel) with columns for patient info and dataset variables',
	)
	@GetMapping('/<int:dataset_id>/template')
	@Authorized(True, permissions=['main.view_study'])
	def downloadTemplate(self, request, dataset_id: int):  # noqa: PLR0915, PLR0912, C901
		Logger.info(f'Generating import template for dataset {dataset_id}')

		# Get format (csv or xlsx) - use 'file_type' param to avoid DRF 'format' conflict
		file_format = request.GET.get('file_type', 'csv').lower()

		# Get dataset and variables
		dataset = self.studyService.getById(dataset_id)
		variables = list(dataset.variables.all().order_by('order', 'name'))

		# Define patient info columns (canonical names)
		patient_info_cols = [
			'PatientReference', 'FirstName', 'LastName', 'DateOfBirth', 'Age',
			'Gender', 'Latitude', 'Longitude', 'TestedDate',
		]

		# Build unique headers: patient info + variables (excluding duplicates)
		used_names = set(col.lower() for col in patient_info_cols)  # noqa: C401
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
					'TestedDate': 'Format: YYYY-MM-DD',
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
					['PATIENT-001', 'John', 'Doe', '1985-03-15', '39', 'M', '', '', '2023-01-15'],
					['PATIENT-002', 'Jane', 'Smith', '', '45', 'F', '', '', '2023-02-20'],
					['PATIENT-003', '', '', '', '32', '', '6.9271', '79.8612', '2023-03-10'],
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

				response = HttpResponse(
					output.read(),
					content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
				)
				response['Content-Disposition'] = f'attachment; filename="{safe_name}_import_template.xlsx"'

				Logger.info(f'Excel template generated for dataset {dataset_id} with {len(variables)} variables')
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
				('PATIENT-001', 'John', 'Doe', '1985-03-15', '39', 'M', '', '', '2023-01-15'),
				('PATIENT-002', 'Jane', 'Smith', '', '45', 'F', '', '', '2023-02-20'),
				('PATIENT-003', '', '', '', '32', '', '6.9271', '79.8612', '2023-03-10'),
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

		Logger.info(f'CSV template generated for dataset {dataset_id} with {len(variables)} variables')
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
	@PutMapping('/<int:dataset_id>')
	@Authorized(True, permissions=['main.change_study'])
	def updateDataset(self, request, dataset_id: int):
		Logger.info(f'Updating dataset {dataset_id}')
		data = request.data

		dataset = self.studyService.getById(dataset_id)

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
			Logger.info(f'Dataset {dataset_id} updated to version {dataset.version}: {", ".join(changes)}')
		else:
			Logger.info(f'No changes made to dataset {dataset_id}')

		return DataSetResponse(data=dataset).json()

	@extend_schema(
		tags=['Dataset'],
		summary='Preview import data',
		description='Parse uploaded file and preview data for import with column detection',
	)
	@PostMapping('/<int:dataset_id>/import/preview')
	@Authorized(True, permissions=['main.change_study'])
	def previewImportData(self, request, dataset_id: int):
		"""Preview import data - delegated to StudyService."""
		data = request.data
		file_url = data.get('fileUrl')
		mapping = data.get('mapping')

		if not file_url:
			return Return.badRequest('No file URL provided')

		try:
			result = self.studyService.previewDataImport(
				study_id=dataset_id,
				file_url=file_url,
				mapping=mapping,
			)
			return Return.ok(result)
		except ValueError as e:
			Logger.error(f'Error previewing import: {e}')
			return Return.badRequest(str(e))
		except Exception as e:
			Logger.error(f'Error previewing import: {e}')
			return Return.badRequest(f'Failed to parse file: {e}')

	@extend_schema(
		tags=['Dataset Import Jobs'],
		summary='Stream import job progress',
		description='Stream the real-time progress of a background import job via Server-Sent Events',
	)
	@GetMapping('/<int:dataset_id>/import/jobs/<int:job_id>/stream')
	@Authorized(True, permissions=['main.view_study'])
	def streamImportJobProgress(self, request, dataset_id: int, job_id: int):
		"""Stream import job progress via SSE. Lightweight — just reads DB."""
		def event_generator():
			while True:
				try:
					job = DataImportJob.objects.get(id=job_id, study_id=dataset_id)
				except DataImportJob.DoesNotExist:
					yield f"event: error\ndata: {json.dumps({'type': 'error', 'message': 'Job not found'})}\n\n"
					return

				status_data = {
					'type': 'progress',
					'current': job.processed_rows,
					'total': job.total_rows,
					'imported': job.imported_count,
					'updated': job.updated_count,
					'skipped': job.skipped_count,
					'failed': job.error_count,
					'patientsCreated': job.patients_created,
					'variablesCreated': job.variables_created,
					'status': job.status,
				}

				if job.status in ('COMPLETED', 'FAILED', 'CANCELLED'):
					event_type = 'complete' if job.status == 'COMPLETED' else 'error'
					status_data['type'] = event_type
					if job.status == 'FAILED':
						status_data['message'] = job.errors[-1]['error'] if job.errors else 'Unknown error'
					yield f'event: {event_type}\ndata: {json.dumps(status_data)}\n\n'
					return

				if job.status == 'PAUSED':
					status_data['type'] = 'paused'
					status_data['paused_reason'] = job.paused_reason
					yield f'event: paused\ndata: {json.dumps(status_data)}\n\n'
					return

				yield f'event: progress\ndata: {json.dumps(status_data)}\n\n'
				time.sleep(0.5)

		response = StreamingHttpResponse(
			event_generator(),
			content_type='text/event-stream; charset=utf-8',
		)
		response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
		response['Pragma'] = 'no-cache'
		response['Expires'] = '0'
		response['X-Accel-Buffering'] = 'no'  # Disable nginx buffering
		return response


	# ========== Import Job Endpoints (Background Processing) ==========

	@extend_schema(
		tags=['Dataset Import Jobs'],
		summary='List import jobs',
		description='Get all import jobs for a dataset',
	)
	@GetMapping('/<int:dataset_id>/import/jobs')
	@Authorized(True, permissions=['main.view_study'])
	def listImportJobs(self, request, dataset_id: int):
		"""List all import jobs for a dataset."""
		Logger.info(f'Listing import jobs for dataset {dataset_id}')

		jobs = self.importService.get_jobs_for_study(dataset_id)
		jobs_data = [self.importService.get_job_status(job.id) for job in jobs]

		# Check for active job
		active_job = self.importService.get_active_job_for_study(dataset_id)

		return Return.ok({
			'jobs': jobs_data,
			'active_job_id': active_job.id if active_job else None,
		})

	@extend_schema(
		tags=['Dataset Import Jobs'],
		summary='Create and start import job',
		description='Create a new background import job and start processing',
	)
	@PostMapping('/<int:dataset_id>/import/jobs')
	@Authorized(True, permissions=['main.change_study'])
	def createImportJob(self, request, dataset_id: int):
		"""Create and start a new background import job."""
		Logger.info(f'Creating import job for dataset {dataset_id}')

		data = request.data
		file_url = data.get('fileUrl')
		mapping = data.get('mapping', {})
		column_types = data.get('columnTypes', {})
		total_rows = data.get('totalRows', 0)
		file_name = data.get('fileName', 'import.csv')

		if not file_url:
			return Return.badRequest('No file URL provided')

		# Note: mapping can be empty for pending jobs (created at Step 1→2)

		try:
			# Create the job
			job = self.importService.create_job(
				study_id=dataset_id,
				file_url=file_url,
				file_name=file_name,
				mapping=mapping,
				column_types=column_types,
				total_rows=total_rows,
				user=request.user,
			)

			# Start the job immediately if mapping is provided, otherwise keep pending
			if mapping:
				job = self.importService.start_job(job.id)

			return Return.ok(self.importService.get_job_status(job.id))

		except ValueError as e:
			Logger.error(f'Error creating import job: {e}')
			return Return.badRequest(str(e))
		except Exception as e:
			Logger.error(f'Error creating import job: {e}')
			return Return.badRequest(f'Failed to create import job: {e}')

	@extend_schema(
		tags=['Dataset Import Jobs'],
		summary='Update and start import job',
		description='Update job mapping and start processing',
	)
	@PutMapping('/<int:dataset_id>/import/jobs/<int:job_id>')
	@Authorized(True, permissions=['main.change_study'])
	def updateAndStartImportJob(self, request, dataset_id: int, job_id: int):
		"""Update job mapping and start the import."""
		Logger.info(f'Updating and starting import job {job_id}')

		data = request.data
		mapping = data.get('mapping', {})
		column_types = data.get('columnTypes', {})
		total_rows = data.get('totalRows', 0)

		if not mapping:
			return Return.badRequest('Column mapping required')

		try:
			job = DataImportJob.objects.get(id=job_id, study_id=dataset_id)

			# Update job with mapping
			job.mapping = mapping
			job.column_types = column_types
			if total_rows:
				job.total_rows = total_rows
			job.save(update_fields=['mapping', 'column_types', 'total_rows', 'updated_at'])

			# Start the job
			job = self.importService.start_job(job.id)

			return Return.ok(self.importService.get_job_status(job.id))

		except DataImportJob.DoesNotExist:
			return Return.notFound('Import job not found')
		except ValueError as e:
			return Return.badRequest(str(e))
		except Exception as e:
			Logger.error(f'Error starting job: {e}')
			return Return.badRequest(f'Failed to start job: {e}')

	@extend_schema(
		tags=['Dataset Import Jobs'],
		summary='Get import job status',
		description='Get current status and progress of an import job',
	)
	@GetMapping('/<int:dataset_id>/import/jobs/<int:job_id>')
	@Authorized(True, permissions=['main.view_study'])
	def getImportJobStatus(self, request, dataset_id: int, job_id: int):
		"""Get current status of an import job."""
		Logger.info(f'Getting status for import job {job_id}')

		try:
			status = self.importService.get_job_status(job_id)
			return Return.ok(status)
		except Exception as e:
			Logger.error(f'Error getting job status: {e}')
			return Return.notFound('Import job not found')

	@extend_schema(
		tags=['Dataset Import Jobs'],
		summary='Pause import job',
		description='Pause a running import job',
	)
	@PostMapping('/<int:dataset_id>/import/jobs/<int:job_id>/pause')
	@Authorized(True, permissions=['main.change_study'])
	def pauseImportJob(self, request, dataset_id: int, job_id: int):
		"""Pause a running import job."""
		Logger.info(f'Pausing import job {job_id}')

		try:
			job = self.importService.pause_job(job_id, reason='manual')
			return Return.ok(self.importService.get_job_status(job.id))
		except ValueError as e:
			return Return.badRequest(str(e))
		except Exception as e:
			Logger.error(f'Error pausing job: {e}')
			return Return.badRequest(f'Failed to pause job: {e}')

	@extend_schema(
		tags=['Dataset Import Jobs'],
		summary='Resume import job',
		description='Resume a paused import job',
	)
	@PostMapping('/<int:dataset_id>/import/jobs/<int:job_id>/resume')
	@Authorized(True, permissions=['main.change_study'])
	def resumeImportJob(self, request, dataset_id: int, job_id: int):
		"""Resume a paused import job."""
		Logger.info(f'Resuming import job {job_id}')

		try:
			job = self.importService.resume_job(job_id)
			return Return.ok(self.importService.get_job_status(job.id))
		except ValueError as e:
			return Return.badRequest(str(e))
		except Exception as e:
			Logger.error(f'Error resuming job: {e}')
			return Return.badRequest(f'Failed to resume job: {e}')

	@extend_schema(
		tags=['Dataset Import Jobs'],
		summary='Cancel import job',
		description='Cancel an import job',
	)
	@DeleteMapping('/<int:dataset_id>/import/jobs/<int:job_id>')
	@Authorized(True, permissions=['main.change_study'])
	def cancelImportJob(self, request, dataset_id: int, job_id: int):
		"""Cancel an import job."""
		Logger.info(f'Cancelling import job {job_id}')

		try:
			job = self.importService.cancel_job(job_id)
			return Return.ok(self.importService.get_job_status(job.id))
		except ValueError as e:
			return Return.badRequest(str(e))
		except Exception as e:
			Logger.error(f'Error cancelling job: {e}')
			return Return.badRequest(f'Failed to cancel job: {e}')
