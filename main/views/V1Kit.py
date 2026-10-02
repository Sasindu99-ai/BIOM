import contextlib

from drf_spectacular.utils import extend_schema

from vvecon.zorion.auth import Authorized
from vvecon.zorion.logger import Logger
from vvecon.zorion.serializers import Return
from vvecon.zorion.views import API, GetMapping, Mapping, PostMapping

from ..services import KitService

__all__ = ['V1Kit']


@Mapping('api/v1/kit')
class V1Kit(API):
	kitService: KitService = KitService()

	@extend_schema(
		tags=['Kit'],
		summary='Verify API Key / Session Credentials',
		description='Checks authentication and returns current user details and permissions.',
	)
	@GetMapping('/auth/verify')
	@Authorized(True, permissions=['main.view_study'])
	def verifyAuth(self, request):
		user = request.user
		return Return.ok({
			'status': 'success',
			'user': {
				'id': user.id,
				'username': user.username,
				'fullName': getattr(user, 'fullName', '') or f'{user.firstName} {user.lastName}'.strip(),
				'email': user.email,
				'isStaff': user.is_staff,
				'isSuperuser': user.is_superuser,
			},
		})

	@extend_schema(
		tags=['Kit'],
		summary='Get Patient Profile Fields Schema',
		description='Returns all known patient profile fields with types and supported filter operators.',
	)
	@GetMapping('/fields')
	@Authorized(True, permissions=['main.view_study'])
	def getFields(self, request):
		data = self.kitService.getKnownProfileFields()
		return Return.ok(data)

	@extend_schema(
		tags=['Kit'],
		summary='Get Datasets Catalog',
		description='Returns available datasets/studies with metadata and record counts.',
	)
	@GetMapping('/datasets')
	@Authorized(True, permissions=['main.view_study'])
	def getDatasets(self, request):
		search = request.GET.get('search', '') or request.GET.get('q', '')
		catalog = self.kitService.getDatasetsCatalog(search=search)
		return Return.ok({'datasets': catalog})

	@extend_schema(
		tags=['Kit'],
		summary='Get Single Dataset Details and Variables',
		description='Returns metadata and variable schema for a given dataset.',
	)
	@GetMapping('/datasets/<int:dataset_id>')
	@Authorized(True, permissions=['main.view_study'])
	def getDatasetDetails(self, request, dataset_id: int):
		data = self.kitService.getDatasetVariables(dataset_id)
		return Return.ok(data)

	@extend_schema(
		tags=['Kit'],
		summary='Get Dataset Variables',
		description='Returns list of all variables for a dataset with data types and operators.',
	)
	@GetMapping('/datasets/<int:dataset_id>/variables')
	@Authorized(True, permissions=['main.view_study'])
	def getDatasetVariables(self, request, dataset_id: int):
		data = self.kitService.getDatasetVariables(dataset_id)
		return Return.ok(data)

	@extend_schema(
		tags=['Kit'],
		summary='Search Variables Across Datasets',
		description='Search variable names across all or specified datasets.',
	)
	@GetMapping('/variables/search')
	@Authorized(True, permissions=['main.view_study'])
	def searchVariables(self, request):
		query = request.GET.get('q', '') or request.GET.get('search', '')
		try:
			limit = min(int(request.GET.get('limit', 50)), 200)
		except (TypeError, ValueError):
			limit = 50

		results = self.kitService.searchVariables(query=query, limit=limit)
		return Return.ok({'variables': results})

	@extend_schema(
		tags=['Kit'],
		summary='Execute Structured Filtered Query',
		description='Filters rows by type-aware rules and returns records ready for DataFrame conversion.',
	)
	@PostMapping('/query')
	@Authorized(True, permissions=['main.view_study'])
	def executeQuery(self, request):
		payload = request.data or {}

		# Extract dataset IDs: support 'dataset', 'datasets', or 'study_ids'
		dataset = payload.get('dataset')
		datasets = payload.get('datasets') or payload.get('study_ids')

		study_ids = []
		if dataset is not None:
			with contextlib.suppress(TypeError, ValueError):
				study_ids.append(int(dataset))
		if datasets is not None:
			if isinstance(datasets, list):
				for item in datasets:
					with contextlib.suppress(TypeError, ValueError):
						study_ids.append(int(item))
			else:
				with contextlib.suppress(TypeError, ValueError):
					study_ids.append(int(datasets))

		filters = payload.get('filters', []) or []
		filter_logic = payload.get('filterLogic', 'AND')
		fields = payload.get('fields')

		try:
			page = max(int(payload.get('page', 1)), 1)
		except (TypeError, ValueError):
			page = 1

		try:
			limit = max(int(payload.get('limit', 5000)), 1)
		except (TypeError, ValueError):
			limit = 5000

		sort_field = payload.get('sortField', 'created_at')
		sort_direction = payload.get('sortDirection', 'desc')

		Logger.info(f'Kit query: studies={study_ids}, filters={len(filters)}, limit={limit}')

		result = self.kitService.queryKitData(
			study_ids=study_ids,
			filters=filters,
			filter_logic=filter_logic,
			fields=fields,
			page=page,
			limit=limit,
			sort_field=sort_field,
			sort_direction=sort_direction,
		)
		return Return.ok(result)

	@PostMapping('/query/')
	@Authorized(True, permissions=['main.view_study'])
	def executeQuerySlash(self, request):
		return self.executeQuery(request)

	@GetMapping('/fields/')
	@Authorized(True, permissions=['main.view_study'])
	def getFieldsSlash(self, request):
		return self.getFields(request)

	@GetMapping('/datasets/')
	@Authorized(True, permissions=['main.view_study'])
	def getDatasetsSlash(self, request):
		return self.getDatasets(request)

	@GetMapping('/auth/verify/')
	@Authorized(True, permissions=['main.view_study'])
	def verifyAuthSlash(self, request):
		return self.verifyAuth(request)

