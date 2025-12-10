from drf_spectacular.utils import extend_schema
from rest_framework.status import HTTP_201_CREATED

from vvecon.zorion.auth import Authorized
from vvecon.zorion.logger import Logger
from vvecon.zorion.serializers import Return
from vvecon.zorion.views import API, Mapping, GetMapping, PostMapping, PutMapping, DeleteMapping
from ..payload.requests import FilterDataSetRequest
from ..payload.responses import DataSetResponse
from ..services import StudyService

__all__ = ['V1DataSet']


@Mapping('api/v1/dataset')
class V1DataSet(API):
	studyService: StudyService = StudyService()

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
				'created_at': 'created_at'
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
				maxVersion=Max('version')
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
				}
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
