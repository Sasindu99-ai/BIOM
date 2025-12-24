from vvecon.zorion.core import Service

from ..models import Study, StudyResult, StudyVariable, UserStudy

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
