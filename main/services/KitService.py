from django.db.models import Count, Q

from vvecon.zorion.core import Service

from ..models import Study
from .StudyService import StudyService

__all__ = ['KitService']


class KitService(Service):
	"""
	Service layer supporting the biom-kit client and programmatic data science queries.
	Handles discovery catalogs (fields, datasets, variables) and flattens filtered
	study results into format ready for direct conversion to pandas DataFrame.
	"""

	model = Study

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.studyService = StudyService()

	TYPE_OPERATORS = {
		'TEXT': ['contains', 'equals', 'starts_with', 'ends_with', 'is_empty', 'is_not_empty'],
		'NUMBER': ['equals', 'gt', 'gte', 'lt', 'lte', 'between', 'is_empty', 'is_not_empty'],
		'DATE': ['equals', 'before', 'after', 'between', 'is_empty', 'is_not_empty'],
		'BOOLEAN': ['equals', 'is_empty', 'is_not_empty'],
	}

	def getKnownProfileFields(self) -> dict:
		"""
		Returns all known patient profile fields with their metadata and valid operators.
		"""
		fields = []
		for field in self.studyService.advancedKnownFields:
			field_dict = dict(field)
			field_dict['source'] = 'profile'
			fields.append(field_dict)

		return {
			'fields': fields,
			'typeOperators': self.TYPE_OPERATORS,
		}

	def getDatasetsCatalog(self, study_ids: list[int] | None = None, search: str = '') -> list[dict]:
		"""
		Returns catalog of datasets with summary statistics (record count, variable count).
		"""
		queryset = Study.objects.annotate(
			record_count=Count('userStudies', distinct=True),
			variable_count=Count('variables', distinct=True),
		)

		if study_ids:
			queryset = queryset.filter(id__in=study_ids)

		search_term = (search or '').strip()
		if search_term:
			queryset = queryset.filter(
				Q(name__icontains=search_term) |
				Q(reference__icontains=search_term) |
				Q(category__icontains=search_term),
			)

		return [
			{
				'id': study.id,
				'name': study.name,
				'reference': study.reference or '',
				'category': study.category or '',
				'status': study.status or '',
				'version': study.version,
				'recordCount': study.record_count,
				'variableCount': study.variable_count,
				'createdAt': study.created_at.isoformat() if hasattr(study, 'created_at') and study.created_at else '',
			}
			for study in queryset.order_by('name')
		]

	def getDatasetVariables(self, study_id: int) -> dict:
		"""
		Returns all variables for a given dataset, with data type and available operators.
		"""
		study = self.studyService.getById(study_id)
		variables = [
			{
				'id': v.id,
				'name': v.name,
				'type': v.type,
				'field': v.field,
				'isRange': v.isRange,
				'isSearchable': v.isSearchable,
				'notes': v.notes or '',
				'operators': self.studyService._operatorsForType(v.type),  # noqa: SLF001
			}
			for v in study.variables.all().order_by('order', 'name')
		]

		return {
			'dataset': {
				'id': study.id,
				'name': study.name,
				'reference': study.reference or '',
			},
			'variables': variables,
		}

	def searchVariables(self, query: str = '', study_ids: list[int] | None = None, limit: int = 50) -> list[dict]:
		"""
		Searches variables across selected or all datasets.
		"""
		if not study_ids:
			study_ids = list(Study.objects.values_list('id', flat=True))
		return self.studyService.searchVariablesAcrossStudies(study_ids, query=query, limit=limit)

	def queryKitData(  # noqa: C901, PLR0912, PLR0913, PLR0915
		self,
		study_ids: list[int],
		filters: list[dict] | None = None,
		filter_logic: str = 'AND',
		fields: list[str] | None = None,
		page: int = 1,
		limit: int = 5000,
		sort_field: str = 'created_at',
		sort_direction: str = 'desc',
	) -> dict:
		"""
		Executes type-aware filtering across single or multiple datasets,
		returning records in flat dictionary format ready for pandas.DataFrame.
		"""
		if not study_ids:
			study_ids = list(Study.objects.values_list('id', flat=True))

		# Known profile column keys and types
		known_types = {item['key']: item['type'] for item in self.studyService.advancedKnownFields}

		# Normalize incoming filter rules for StudyService
		normalized_filters = []
		for rule in (filters or []):
			norm_rule = dict(rule)
			field_key = norm_rule.get('fieldKey') or norm_rule.get('field') or norm_rule.get('name') or ''
			norm_rule['fieldKey'] = str(field_key)

			scope = str(norm_rule.get('scope', '')).lower()
			if not scope or scope in ('auto', 'none'):
				scope = 'known' if str(field_key) in known_types else 'variable'
			norm_rule['scope'] = scope

			if not norm_rule.get('fieldType') and scope == 'known':
				norm_rule['fieldType'] = known_types.get(str(field_key), 'TEXT')

			normalized_filters.append(norm_rule)

		filter_rules = normalized_filters
		filter_logic_u = 'OR' if str(filter_logic).upper() == 'OR' else 'AND'

		# Use single-dataset query or multi-dataset query
		if len(study_ids) == 1:
			raw_data = self.studyService.getAdvancedFilteredData(
				study_id=study_ids[0],
				filters=filter_rules,
				filter_logic=filter_logic_u,
				page=page,
				limit=limit,
				sort_field=sort_field,
				sort_direction=sort_direction,
			)
			variable_columns = raw_data.get('columns', [])
		else:
			raw_data = self.studyService.getMultiStudyAdvancedFilteredData(
				study_ids=study_ids,
				filters=filter_rules,
				filter_logic=filter_logic_u,
				page=page,
				limit=limit,
				sort_field=sort_field,
				sort_direction=sort_direction,
			)
			variable_columns = raw_data.get('columns', [])

		rows = raw_data.get('rows', [])
		pagination = raw_data.get('pagination', {})

		known_keys = [
			'patientId', 'reference', 'firstName', 'lastName', 'fullName',
			'gender', 'dateOfBirth', 'age', 'latitude', 'longitude',
			'testedDate', 'status', 'created_at',
		]

		# Build column definitions
		all_columns = [
			{'name': k, 'type': known_types.get(k, 'TEXT'), 'source': 'profile'} for k in known_keys
		] + [
			{'name': v['name'], 'type': v.get('type', 'TEXT'), 'source': 'variable'} for v in variable_columns
		]

		# If caller requested specific fields, filter column definitions
		requested_fields_set = set(fields) if fields else None
		if requested_fields_set:
			active_columns = [col for col in all_columns if col['name'] in requested_fields_set]
		else:
			active_columns = all_columns

		# Flatten each row
		flat_records = []
		for row in rows:
			record = {}
			# Add study identification
			record['datasetId'] = row.get('_studyId')
			record['datasetName'] = row.get('_studyName')

			# Add known fields
			for k in known_keys:
				if requested_fields_set is None or k in requested_fields_set:
					record[k] = row.get(k)

			# Add variable values by original variable name
			values_by_name = row.get('valuesByName', {})
			for v in variable_columns:
				var_name = v['name']
				if requested_fields_set is None or var_name in requested_fields_set:
					record[var_name] = values_by_name.get(var_name.lower())

			flat_records.append(record)

		studies = Study.objects.filter(id__in=study_ids).values('id', 'name')

		return {
			'meta': {
				'totalRecords': pagination.get('total', len(rows)),
				'returnedRecords': len(flat_records),
				'page': pagination.get('page', page),
				'limit': pagination.get('limit', limit),
				'totalPages': pagination.get('totalPages', 1),
				'hasNext': pagination.get('hasNext', False),
				'hasPrev': pagination.get('hasPrev', False),
				'filterLogic': filter_logic_u,
				'datasets': list(studies),
			},
			'columns': active_columns,
			'records': flat_records,
		}
