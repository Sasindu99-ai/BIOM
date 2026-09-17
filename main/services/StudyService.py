import contextlib
import csv
import io
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from django.conf import settings
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.dateparse import parse_date

from vvecon.zorion.core import Service
from vvecon.zorion.logger import Logger

from ..models import Patient, Study, StudyResult, StudyVariable, UserStudy
from ..utils import detect_variable_type
from .PatientService import PatientService

__all__ = ['StudyService']


class StudyService(Service):
	model = Study
	searchableFields = ('name', 'description', 'category')
	filterableFields = ('status', 'category', 'createdBy')
	advancedKnownFields = (
		{
			'key': 'patientId',
			'label': 'Patient ID',
			'type': 'NUMBER',
			'operators': ['equals', 'gt', 'gte', 'lt', 'lte', 'between'],
		},
		{
			'key': 'reference',
			'label': 'Patient Reference',
			'type': 'TEXT',
			'operators': ['contains', 'equals', 'starts_with', 'ends_with', 'is_empty', 'is_not_empty'],
		},
		{
			'key': 'firstName',
			'label': 'First Name',
			'type': 'TEXT',
			'operators': ['contains', 'equals', 'starts_with', 'ends_with', 'is_empty', 'is_not_empty'],
		},
		{
			'key': 'lastName',
			'label': 'Last Name',
			'type': 'TEXT',
			'operators': ['contains', 'equals', 'starts_with', 'ends_with', 'is_empty', 'is_not_empty'],
		},
		{
			'key': 'fullName',
			'label': 'Full Name',
			'type': 'TEXT',
			'operators': ['contains', 'equals', 'starts_with', 'ends_with', 'is_empty', 'is_not_empty'],
		},
		{
			'key': 'gender',
			'label': 'Gender',
			'type': 'TEXT',
			'operators': ['equals', 'contains', 'is_empty', 'is_not_empty'],
		},
		{
			'key': 'dateOfBirth',
			'label': 'Date of Birth',
			'type': 'DATE',
			'operators': ['equals', 'before', 'after', 'between', 'is_empty', 'is_not_empty'],
		},
		{
			'key': 'age',
			'label': 'Age',
			'type': 'NUMBER',
			'operators': ['equals', 'gt', 'gte', 'lt', 'lte', 'between', 'is_empty', 'is_not_empty'],
		},
		{
			'key': 'latitude',
			'label': 'Latitude',
			'type': 'NUMBER',
			'operators': ['equals', 'gt', 'gte', 'lt', 'lte', 'between', 'is_empty', 'is_not_empty'],
		},
		{
			'key': 'longitude',
			'label': 'Longitude',
			'type': 'NUMBER',
			'operators': ['equals', 'gt', 'gte', 'lt', 'lte', 'between', 'is_empty', 'is_not_empty'],
		},
		{
			'key': 'testedDate',
			'label': 'Tested Date',
			'type': 'DATE',
			'operators': ['equals', 'before', 'after', 'between', 'is_empty', 'is_not_empty'],
		},
		{
			'key': 'status',
			'label': 'Data Entry Status',
			'type': 'TEXT',
			'operators': ['equals', 'contains', 'is_empty', 'is_not_empty'],
		},
	)

	def search(self, filters):
		"""
		Search and filter studies based on provided criteria
		"""
		queryset = self.model.objects.all()

		# Apply search
		search_term = filters.get('search', '').strip()
		if search_term:
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

	@staticmethod
	def _operatorsForType(field_type):
		type_u = (field_type or 'TEXT').upper()
		if type_u == 'NUMBER':
			return ['equals', 'gt', 'gte', 'lt', 'lte', 'between', 'is_empty', 'is_not_empty']
		if type_u == 'DATE':
			return ['equals', 'before', 'after', 'between', 'is_empty', 'is_not_empty']
		if type_u == 'BOOLEAN':
			return ['equals', 'is_empty', 'is_not_empty']
		return ['contains', 'equals', 'starts_with', 'ends_with', 'is_empty', 'is_not_empty']

	def _collectUnionVariables(self, study_ids):
		"""
		Variables from every successfully-resolved study in `study_ids`, deduped
		case-insensitively by name (first-seen casing wins) - a variable need not
		exist in every study for this to include it: a filter rule on a variable
		only some of the selected datasets have is still meaningful (rows from
		datasets without it just don't match that rule).
		"""
		by_name = {}
		for study_id in (study_ids or []):
			try:
				study_variables = self.getVariables(study_id)
			except Exception:
				Logger.exception('Failed to get variables for study %s', study_id)
				continue
			for v in study_variables:
				by_name.setdefault(v.name.lower(), v)
		return by_name

	def getUnionVariables(self, study_ids):
		"""All variables across the given studies (deduped by name), with operators."""
		by_name = self._collectUnionVariables(study_ids)
		return [
			{'id': v.id, 'name': v.name, 'type': v.type, 'operators': self._operatorsForType(v.type)}
			for v in sorted(by_name.values(), key=lambda v: v.name.lower())
		]

	def searchVariablesAcrossStudies(self, study_ids, query='', limit=50):
		"""
		Union variables across `study_ids` (see getUnionVariables), filtered to
		names containing `query` (case-insensitive), capped to `limit`. Backs the
		variable field-key search-as-you-type on the advanced filter page - a
		plain dropdown doesn't scale once several datasets' variables are combined.
		"""
		by_name = self._collectUnionVariables(study_ids)
		query_l = (query or '').strip().lower()
		matches = [v for k, v in by_name.items() if not query_l or query_l in k]
		matches.sort(key=lambda v: v.name.lower())
		return [
			{'name': v.name, 'type': v.type, 'operators': self._operatorsForType(v.type)}
			for v in matches[:limit]
		]

	def getRelatedVariables(self, study_id, variable_id):
		"""
		Find variables related to the given variable (sharing UserStudy records).
		"""
		# Get the IDs of UserStudies that have results for this variable
		study_results = StudyResult.objects.filter(studyVariable_id=variable_id)
		user_study_ids = study_results.values_list('userStudy_id', flat=True)

		# Find other variables that also have results in these UserStudies
		related_variable_ids = StudyResult.objects.filter(userStudy_id__in=user_study_ids)\
			.exclude(studyVariable_id=variable_id)\
			.values_list('studyVariable_id', flat=True).distinct()

		# Return the variable objects
		return list(StudyVariable.objects.filter(id__in=related_variable_ids))

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

		# Batch-fetch all results for this page in one query instead of one per row
		results_by_user_study = {}
		for result in StudyResult.objects.filter(
			userStudy_id__in=[us.id for us in user_studies],
		).select_related('studyVariable'):
			results_by_user_study.setdefault(result.userStudy_id, []).append(result)

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

			for result in results_by_user_study.get(us.id, []):
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

	def _toDate(self, value):
		if not value:
			return None
		if isinstance(value, datetime):
			return value.date()
		if isinstance(value, date):
			return value
		if isinstance(value, str):
			return parse_date(value.strip())
		return None

	def _toNumber(self, value):
		if value is None or value == '':
			return None
		try:
			if isinstance(value, str):
				return float(value.replace(',', '').strip())
			return float(value)
		except (TypeError, ValueError):
			return None

	def _toBoolean(self, value):
		if isinstance(value, bool):
			return value
		if value is None:
			return None
		normalized = str(value).strip().lower()
		if normalized in ('true', '1', 'yes', 'y'):
			return True
		if normalized in ('false', '0', 'no', 'n'):
			return False
		return None

	def _isEmpty(self, value):
		return value is None or str(value).strip() == ''

	def _calcAge(self, dob):
		if not dob:
			return None
		today = timezone.now().date()
		age = today.year - dob.year
		if (today.month, today.day) < (dob.month, dob.day):
			age -= 1
		return age

	def _matchText(self, operator: str, raw_value, raw_target):  # noqa: PLR0911
		value = '' if raw_value is None else str(raw_value)
		target = '' if raw_target is None else str(raw_target)
		value_l = value.lower()
		target_l = target.lower()

		if operator == 'contains':
			return target_l in value_l
		if operator == 'equals':
			return value_l == target_l
		if operator == 'starts_with':
			return value_l.startswith(target_l)
		if operator == 'ends_with':
			return value_l.endswith(target_l)
		if operator == 'is_empty':
			return self._isEmpty(raw_value)
		if operator == 'is_not_empty':
			return not self._isEmpty(raw_value)
		return False

	def _matchNumber(self, operator: str, raw_value, raw_target, raw_target_to=None):  # noqa: PLR0911, C901
		if operator == 'is_empty':
			return self._isEmpty(raw_value)
		if operator == 'is_not_empty':
			return not self._isEmpty(raw_value)

		value = self._toNumber(raw_value)
		target = self._toNumber(raw_target)
		target_to = self._toNumber(raw_target_to)
		if value is None or target is None:
			return False

		if operator == 'equals':
			return value == target
		if operator == 'gt':
			return value > target
		if operator == 'gte':
			return value >= target
		if operator == 'lt':
			return value < target
		if operator == 'lte':
			return value <= target
		if operator == 'between':
			if target_to is None:
				return False
			low = min(target, target_to)
			high = max(target, target_to)
			return low <= value <= high
		return False

	def _matchDate(self, operator: str, raw_value, raw_target, raw_target_to=None):  # noqa: PLR0911
		if operator == 'is_empty':
			return self._isEmpty(raw_value)
		if operator == 'is_not_empty':
			return not self._isEmpty(raw_value)

		value = self._toDate(raw_value)
		target = self._toDate(raw_target)
		target_to = self._toDate(raw_target_to)
		if not value or not target:
			return False

		if operator == 'equals':
			return value == target
		if operator == 'before':
			return value < target
		if operator == 'after':
			return value > target
		if operator == 'between':
			if not target_to:
				return False
			low = min(target, target_to)
			high = max(target, target_to)
			return low <= value <= high
		return False

	def _matchBoolean(self, operator: str, raw_value, raw_target):
		if operator == 'is_empty':
			return self._isEmpty(raw_value)
		if operator == 'is_not_empty':
			return not self._isEmpty(raw_value)
		value = self._toBoolean(raw_value)
		target = self._toBoolean(raw_target)
		if value is None or target is None:
			return False
		return value == target

	def _matchFilter(self, field_type: str, operator: str, row_value, value, value_to=None):
		field_type_u = (field_type or 'TEXT').upper()
		if field_type_u == 'NUMBER':
			return self._matchNumber(operator, row_value, value, value_to)
		if field_type_u == 'DATE':
			return self._matchDate(operator, row_value, value, value_to)
		if field_type_u == 'BOOLEAN':
			return self._matchBoolean(operator, row_value, value)
		return self._matchText(operator, row_value, value)

	def _sortKeyByType(self, value, field_type):
		if value is None or value == '':
			return (1, None)
		field_type_u = (field_type or 'TEXT').upper()
		if field_type_u == 'NUMBER':
			number_val = self._toNumber(value)
			return (0, number_val) if number_val is not None else (1, None)
		if field_type_u == 'DATE':
			date_val = self._toDate(value)
			return (0, date_val) if date_val else (1, None)
		if field_type_u == 'BOOLEAN':
			bool_val = self._toBoolean(value)
			return (0, int(bool_val)) if bool_val is not None else (1, None)
		return (0, str(value).lower())

	def getAdvancedFilterMeta(self, study_id=None, study_ids=None):
		if study_ids:
			# Union, not intersection: a variable only some of the selected
			# datasets have is still a meaningful thing to sort/filter by.
			variables = self.getUnionVariables(study_ids)
		elif study_id:
			study = self.getById(study_id)
			variables = [
				{'id': v.id, 'name': v.name, 'type': v.type, 'operators': self._operatorsForType(v.type)}
				for v in study.variables.all().order_by('order', 'name')
			]
		else:
			variables = []

		return {
			'dataset': {'id': study_id, 'name': 'Selected Studies'},
			'knownFields': list(self.advancedKnownFields),
			'variables': variables,
		}

	def _buildAdvancedFilterRows(self, study):
		"""
		Build one filter/sort-ready row per UserStudy in `study`.

		Each row's variable values are stored two ways: by the variable's numeric id
		(`values`, stable only within this one study) and by its lowercased name
		(`valuesByName`, the only key that stays meaningful when rows from several
		studies are merged together, since the same conceptual variable is a
		separate StudyVariable row - with a different id - in each study).

		Returns (rows, variables, variable_lookup_by_id, variable_lookup_by_name),
		where the lookups map to plain {'id', 'name', 'type'} dicts.
		"""
		variables = list(study.variables.all().order_by('order', 'name'))
		variable_lookup_by_id = {}
		variable_lookup_by_name = {}
		for v in variables:
			entry = {'id': v.id, 'name': v.name, 'type': v.type}
			variable_lookup_by_id[str(v.id)] = entry
			variable_lookup_by_name[v.name.lower()] = entry

		user_studies = (
			UserStudy.objects
			.filter(study=study)
			.select_related('patient')
			.prefetch_related('results__studyVariable')
		)

		rows = []
		for us in user_studies:
			patient = us.patient
			patient_dob = patient.dateOfBirth if patient else None
			full_name = ''
			if patient:
				full_name = f'{patient.firstName or ""} {patient.lastName or ""}'.strip()

			row = {
				'patientId': patient.id if patient else None,
				'reference': us.reference,
				'status': us.status,
				'firstName': patient.firstName if patient else '',
				'lastName': patient.lastName if patient else '',
				'fullName': full_name,
				'gender': patient.gender if patient else '',
				'dateOfBirth': patient_dob.isoformat() if patient_dob else '',
				'age': self._calcAge(patient_dob) if patient_dob else None,
				'latitude': patient.latitude if patient else None,
				'longitude': patient.longitude if patient else None,
				'testedDate': us.testedDate.date().isoformat() if us.testedDate else '',
				'created_at': us.created_at.isoformat() if us.created_at else '',
				'values': {},
				'valuesByName': {},
				'_studyId': study.id,
				'_studyName': study.name,
			}
			for result in us.results.all():
				row['values'][str(result.studyVariable.id)] = result.value
				row['valuesByName'][result.studyVariable.name.lower()] = result.value
			rows.append(row)

		return rows, variables, variable_lookup_by_id, variable_lookup_by_name

	def _rowMatchesFilters(
		self, row_data, filter_rules, filter_logic_u, variable_lookup_by_id, variable_lookup_by_name,
	):
		"""
		Evaluate one row against `filter_rules`. A 'variable' rule's fieldKey may be
		either the variable's numeric id (single-dataset UI) or its name
		(multi-dataset UI, where id is not portable across studies) - both are
		tried so either caller works unmodified.
		"""
		if not filter_rules:
			return True
		rule_results = []
		for rule in filter_rules:
			scope = str(rule.get('scope', 'known')).lower()
			operator = str(rule.get('operator', 'contains')).lower()
			value = rule.get('value')
			value_to = rule.get('valueTo')
			field_type = str(rule.get('fieldType', 'TEXT')).upper()

			if scope == 'variable':
				field_key = str(rule.get('fieldKey', '')).strip()
				variable = variable_lookup_by_id.get(field_key) or variable_lookup_by_name.get(field_key.lower())
				if not variable:
					rule_results.append(False)
					continue
				row_value = row_data.get('valuesByName', {}).get(variable['name'].lower())
				matched = self._matchFilter(variable['type'], operator, row_value, value, value_to)
				rule_results.append(matched)
			else:
				field_key = str(rule.get('fieldKey', ''))
				row_value = row_data.get(field_key)
				matched = self._matchFilter(field_type, operator, row_value, value, value_to)
				rule_results.append(matched)

		return all(rule_results) if filter_logic_u == 'AND' else any(rule_results)

	def _sortAdvancedFilterRows(self, rows, sort_field, sort_direction, variable_lookup_by_name):
		"""Sort `rows` in place by a known field key or a variable sort key ('var:<id-or-name>')."""
		sort_direction_u = 'asc' if str(sort_direction).lower() == 'asc' else 'desc'
		is_reverse = sort_direction_u == 'desc'
		sort_field_str = str(sort_field or 'created_at')

		if sort_field_str.startswith('var:'):
			sort_key_raw = sort_field_str.replace('var:', '', 1)
			sort_var = variable_lookup_by_name.get(sort_key_raw.lower())
			sort_type = sort_var['type'] if sort_var else 'TEXT'
			sort_name_key = sort_var['name'].lower() if sort_var else sort_key_raw.lower()
			rows.sort(
				key=lambda row: self._sortKeyByType(row.get('valuesByName', {}).get(sort_name_key), sort_type),
				reverse=is_reverse,
			)
		else:
			known_types = {item['key']: item['type'] for item in self.advancedKnownFields}
			sort_type = known_types.get(sort_field_str, 'TEXT')
			rows.sort(
				key=lambda row: self._sortKeyByType(row.get(sort_field_str), sort_type),
				reverse=is_reverse,
			)
		return rows

	@staticmethod
	def _paginate(rows, page, limit):
		try:
			page = max(int(page), 1)
		except (TypeError, ValueError):
			page = 1
		try:
			limit = max(int(limit), 1)
		except (TypeError, ValueError):
			limit = 25
		start = (page - 1) * limit
		end = start + limit
		total = len(rows)
		total_pages = (total + limit - 1) // limit if total > 0 else 1
		return rows[start:end], {
			'page': page,
			'limit': limit,
			'total': total,
			'totalPages': total_pages,
			'hasNext': page < total_pages,
			'hasPrev': page > 1,
		}

	def getAdvancedFilteredData(  # noqa: PLR0913
		self, study_id, filters=None, filter_logic='AND', page=1, limit=25, sort_field='created_at',
		sort_direction='desc',
	):
		study = self.getById(study_id)
		rows, variables, variable_lookup_by_id, variable_lookup_by_name = self._buildAdvancedFilterRows(study)

		filter_rules = filters or []
		filter_logic_u = 'OR' if str(filter_logic).upper() == 'OR' else 'AND'

		filtered_rows = [
			row for row in rows
			if self._rowMatchesFilters(
				row, filter_rules, filter_logic_u, variable_lookup_by_id, variable_lookup_by_name,
			)
		]

		self._sortAdvancedFilterRows(filtered_rows, sort_field, sort_direction, variable_lookup_by_name)

		paged_rows, pagination = self._paginate(filtered_rows, page, limit)

		return {
			'dataset': {'id': study.id, 'name': study.name},
			'columns': [{'id': v.id, 'name': v.name, 'type': v.type} for v in variables],
			'knownColumns': list(self.advancedKnownFields),
			'rows': paged_rows,
			'allRows': filtered_rows,
			'pagination': pagination,
			'stats': {
				'totalBeforeFilters': len(rows),
				'totalAfterFilters': len(filtered_rows),
			},
		}

	def getMultiStudyAdvancedFilteredData(  # noqa: PLR0913
		self, study_ids, filters=None, filter_logic='AND', page=1, limit=25, sort_field='created_at',
		sort_direction='desc',
	):
		"""
		Same engine as getAdvancedFilteredData, generalized to filter, merge, sort
		and paginate rows from several datasets at once. Each dataset is filtered
		against its OWN StudyVariable rows (ids never cross studies) before the
		filtered rows are merged, so a variable rule matches correctly in every
		selected dataset regardless of that variable's numeric id there - only its
		name needs to line up.
		"""
		study_ids = [sid for sid in (study_ids or []) if sid not in (None, '')]
		filter_rules = filters or []
		filter_logic_u = 'OR' if str(filter_logic).upper() == 'OR' else 'AND'

		all_filtered_rows = []
		total_before_filters = 0
		datasets_meta = []
		# Union of every study's variables, used only to resolve a variable's TYPE
		# during the final cross-study sort - never for filtering (that stays
		# per-study so a name collision across studies can't leak the wrong id).
		union_variable_lookup_by_name = {}
		# Intersection of variable names across every successfully-resolved study,
		# used for the results table's default columns (kept deliberately narrower
		# than the union so the table doesn't balloon to hundreds of mostly-blank
		# columns). Computed inline here, not via a separate lookup, so a
		# stale/deleted study id in `study_ids` can't blow up this method - each
		# id is resolved exactly once, in the loop below, where it's easy to skip.
		common_variable_names = None

		for sid in study_ids:
			try:
				study = self.getById(sid)
			except Exception:
				Logger.error(f'getMultiStudyAdvancedFilteredData: failed to get study {sid}')
				continue

			rows, _variables, variable_lookup_by_id, variable_lookup_by_name = self._buildAdvancedFilterRows(study)
			datasets_meta.append({'id': study.id, 'name': study.name})
			total_before_filters += len(rows)

			for name, entry in variable_lookup_by_name.items():
				union_variable_lookup_by_name.setdefault(name, entry)

			this_study_names = set(variable_lookup_by_name.keys())
			common_variable_names = (
				this_study_names if common_variable_names is None else common_variable_names & this_study_names
			)

			filtered = [
				row for row in rows
				if self._rowMatchesFilters(
					row, filter_rules, filter_logic_u, variable_lookup_by_id, variable_lookup_by_name,
				)
			]
			all_filtered_rows.extend(filtered)

		self._sortAdvancedFilterRows(all_filtered_rows, sort_field, sort_direction, union_variable_lookup_by_name)

		paged_rows, pagination = self._paginate(all_filtered_rows, page, limit)

		common_variables = [
			union_variable_lookup_by_name[name] for name in sorted(common_variable_names or [])
		]

		return {
			'datasets': datasets_meta,
			'columns': [{'name': v['name'], 'type': v['type']} for v in common_variables],
			'knownColumns': list(self.advancedKnownFields),
			'rows': paged_rows,
			'allRows': all_filtered_rows,
			'pagination': pagination,
			'stats': {
				'totalBeforeFilters': total_before_filters,
				'totalAfterFilters': len(all_filtered_rows),
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
				'name': (
					f'{study.createdBy.firstName} {study.createdBy.lastName}'.strip()
					if study.createdBy else 'System'
				),
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
					'name': f'{study.createdBy.firstName} {study.createdBy.lastName}'.strip()
					if study.createdBy else 'System',
				} if study.createdBy else {
					'id': None,
					'name': 'System',
				},
				'description': f'Dataset was updated to version {study.version}',
			})

		# Recent user studies as events (last 10)
		recent_studies = UserStudy.objects.filter(study=study).order_by('-created_at')[:10]
		events.extend([
			{
				'type': 'data_added',
				'timestamp': us.created_at,
				'user': {
					'id': us.createdBy.id if us.createdBy else None,
					'name': f'{us.createdBy.firstName} {us.createdBy.lastName}'.strip() if us.createdBy else 'System',
				} if us.createdBy else {'id': None, 'name': 'System'},
				'description': f'Data entry added for patient {us.patient.firstName if us.patient else "Unknown"}',
			}
			for us in recent_studies
		])

		# Sort by timestamp descending
		events.sort(key=lambda x: x['timestamp'] or '', reverse=True)

		return events

	def getPatients(self, study_id, page=1, limit=20):
		"""
		Get patients who have data entries (UserStudy) in this dataset with pagination
		"""
		study = self.getById(study_id)

		# Get distinct patients with user studies in this dataset
		patient_ids_with_counts = (
			UserStudy.objects.filter(study=study)
			.values('patient_id')
			.annotate(entries_count=Count('id'))
		)

		# Total count of distinct patients (COUNT query, doesn't materialize rows)
		total_count = patient_ids_with_counts.count()

		# Paginate the patient IDs at the DB level (LIMIT/OFFSET, not a Python slice)
		start = (page - 1) * limit
		end = start + limit
		paginated_patient_data = list(patient_ids_with_counts.order_by('patient_id')[start:end])

		# Get actual patient objects
		patient_ids = [p['patient_id'] for p in paginated_patient_data if p['patient_id']]
		patients_map = {}

		if patient_ids:
			patients = Patient.objects.filter(id__in=patient_ids)
			patients_map = {p.id: p for p in patients}

		# Build response with patient data and entry counts
		patients_list = []
		for ppd in paginated_patient_data:
			patient = patients_map.get(ppd['patient_id'])
			if patient:
				patients_list.append({
					'id': patient.id,
					'firstName': patient.firstName,
					'lastName': patient.lastName,
					'reference': patient.reference if hasattr(patient, 'reference') else None,
					'gender': patient.gender if hasattr(patient, 'gender') else None,
					'age': patient.age if hasattr(patient, 'age') else None,
					'status': patient.status if hasattr(patient, 'status') else 'ACTIVE',
					'dataEntriesCount': ppd['entries_count'],
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
		'reference': [
			'patientreference', 'patientref', 'patient_reference', 'patient_ref', 'patientid', 'patient_id',
			'subjectid', 'subject_id', 'participantid', 'matched_patient_id',
		],
		'firstName': ['firstname', 'first_name', 'fname', 'first', 'givenname', 'patient_first'],
		'lastName': ['lastname', 'last_name', 'lname', 'last', 'surname', 'familyname', 'patient_last'],
		'dateOfBirth': ['dateofbirth', 'date_of_birth', 'dob', 'birthdate', 'birth_date', 'birthday'],
		'age': ['age', 'patient_age', 'years', 'yearsold'],
		'gender': ['gender', 'sex', 'patient_gender'],
		'latitude': ['latitude', 'lat', 'location_lat', 'gps_lat', 'y_coord'],
		'longitude': ['longitude', 'long', 'lng', 'location_long', 'gps_long', 'x_coord'],
		'testedDate': ['tested_date', 'testeddate', 'test_date', 'testdate', 'collection_date', 'visit_date'],
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
		"""Resolve file URL to absolute filesystem path, rejecting paths that escape MEDIA_ROOT."""
		relative = file_url
		if relative.startswith('/media/'):
			relative = relative.replace('/media/', '', 1)
		elif relative.startswith('media/'):
			relative = relative.replace('media/', '', 1)

		media_root = Path(settings.MEDIA_ROOT).resolve()
		resolved = (media_root / relative).resolve()

		if resolved != media_root and media_root not in resolved.parents:
			raise ValueError(f'Invalid file path: {file_url}')

		return resolved

	def _createPatientSignature(  # noqa: PLR0913
		self, first_name: str, last_name: str, reference: str, dob: str,
		age: str, latitude: str, longitude: str, tested_date: str = '',
	) -> str | None:
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
		if latitude and longitude and contextlib.suppress(ValueError, TypeError):
			sig_parts.append(f'loc:{round(float(latitude), 3)},{round(float(longitude), 3)}')
		if tested_date:
			sig_parts.append(f'date:{tested_date.strip()}')
		return '|'.join(sig_parts) if sig_parts else None

	def _detectColumnTypes(self, columns: list, sample_rows: list) -> dict:
		"""Detect data types from sample values for each column."""
		sample_size = min(len(sample_rows), 200)
		column_types = {}

		for col in columns:
			sample_values = [row.get(col, '') for row in sample_rows[:sample_size]]
			column_types[col] = detect_variable_type(sample_values)

		return column_types

	def _readFileContent(self, file_path: Path) -> tuple[list, list]:
		"""Read CSV/Excel file and return (columns, all_rows)."""
		if str(file_path).endswith(('.xlsx', '.xls')):
			df = pd.read_excel(file_path)
			df.columns = [str(col).strip() for col in df.columns]
			columns = list(df.columns)
			all_rows = df.fillna('').to_dict('records')
		else:
			# CSV with encoding fallback
			file_content = None
			for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
				try:
					with Path(file_path).open(encoding=encoding) as f:
						file_content = f.read()
					break
				except UnicodeDecodeError:
					continue
			if file_content is None:
				with Path(file_path).open(encoding='utf-8', errors='replace') as f:
					file_content = f.read()

			reader = csv.DictReader(io.StringIO(file_content))
			columns = [col.strip() for col in reader.fieldnames] if reader.fieldnames else []
			all_rows = list(reader)

		return columns, all_rows

	def previewDataImport(self, study_id: int, file_url: str, mapping: dict | None = None) -> dict:  # noqa: PLR0915, PLR0912, C901
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
			return any(
				col_lower.startswith(pattern) or pattern in col_lower for pattern in self.SKIP_COLUMN_PATTERNS
			)

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
		tested_date_col = patient_mapping.get('testedDate', '')

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
			tested_date = str(row.get(tested_date_col, '')).strip() if tested_date_col else ''

			# Convert age to DOB if needed
			effective_dob = dob
			if age and not dob:
				try:
					age_int = int(float(age))
					birth_year = timezone.now().year - age_int
					effective_dob = f'{birth_year}-01-01'
				except (ValueError, TypeError):
					pass

			# Check valid identifiers
			has_reference = bool(reference)
			has_name = bool(first_name or last_name)
			has_location = bool(latitude and longitude)

			# Create signature for duplicate detection
			patient_signature = self._createPatientSignature(
				first_name, last_name, reference, effective_dob, age, latitude, longitude, tested_date,
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
				user_study = UserStudy.objects.filter(
					study=dataset, reference=reference,
				).select_related('patient').first()
				if user_study and user_study.patient:
					patient = user_study.patient

			# Try advanced matching if no reference match
			if not patient and (has_name or has_location):
				match = patient_service._findBestMatchingPatient(  # noqa: SLF001
					first_name, last_name, effective_dob, gender, latitude, longitude,
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
				query = {'study': dataset, 'patient': patient}
				if tested_date:
					parsed_tested_date = self._toDate(tested_date)
					if parsed_tested_date:
						query['testedDate__date'] = parsed_tested_date
				else:
					query['testedDate__isnull'] = True
				existing = UserStudy.objects.filter(**query).exists()
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

