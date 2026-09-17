from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema
from rest_framework.status import HTTP_201_CREATED

from vvecon.zorion.auth import Authorized
from vvecon.zorion.logger import Logger
from vvecon.zorion.serializers import Return
from vvecon.zorion.views import API, DeleteMapping, GetMapping, Mapping, PostMapping, PutMapping

from ..enums import BioMarkerStatus
from ..payload.requests import BioMarkerRequest, BioMarkerReviewRequest, FilterBioMarkerRequest
from ..payload.responses import BioMarkerResponse
from ..services import BioMarkerService

__all__ = ['V1BioMarker']


@Mapping('api/v1/biomarker')
class V1BioMarker(API):
	biomarkerService: BioMarkerService = BioMarkerService()

	@extend_schema(
		tags=['BioMarker'],
		summary='Get biomarkers',
		description='Get biomarkers with filtering, search, and pagination',
		request=FilterBioMarkerRequest,
		responses={200: BioMarkerResponse().response()},
	)
	@PostMapping('/')
	@Authorized(True, permissions=['main.view_biomarker'])
	def getBioMarkers(self, request, data: FilterBioMarkerRequest):
		Logger.info(f'Validating biomarker filter data: {data.initial_data}')
		if data.is_valid(raise_exception=True):
			validated_data = data.validated_data.copy()
			pagination_data = validated_data.get('pagination', {})
			page = pagination_data.get('page', 1) if pagination_data else 1
			limit = pagination_data.get('limit', 20) if pagination_data else 20

			search_data = validated_data.copy()
			search_data.pop('pagination', None)
			filtered_queryset = self.biomarkerService.search(search_data)

			sort_field = validated_data.get('sortField', 'created_at')
			sort_direction = validated_data.get('sortDirection', 'desc')
			field_mapping = {
				'name': 'name',
				'created': 'created_at',
				'created_at': 'created_at',
				'status': 'status',
				'type': 'type',
			}
			actual_field = field_mapping.get(sort_field, 'created_at')
			if sort_direction == 'asc':
				filtered_queryset = filtered_queryset.order_by(actual_field)
			else:
				filtered_queryset = filtered_queryset.order_by(f'-{actual_field}')

			total_count = filtered_queryset.count()
			stats_query = filtered_queryset.aggregate(
				pending=Count('id', filter=Q(status=BioMarkerStatus.PENDING)),
				approved=Count('id', filter=Q(status=BioMarkerStatus.APPROVED)),
				rejected=Count('id', filter=Q(status=BioMarkerStatus.REJECTED)),
			)

			biomarkers = self.biomarkerService.paginate(filtered_queryset, page, limit)
			total_pages = (total_count + limit - 1) // limit if limit > 0 else 1

			response_data = {
				'results': BioMarkerResponse(data=biomarkers, many=True).json().data,
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
					'pending': stats_query['pending'] or 0,
					'approved': stats_query['approved'] or 0,
					'rejected': stats_query['rejected'] or 0,
				},
			}

			Logger.info(f'{len(biomarkers)} biomarkers found on page {page}/{total_pages}')
			return Return.ok(response_data)

	@extend_schema(
		tags=['BioMarker'],
		summary='Create biomarker',
		description='Submit a new biomarker for review',
		request=BioMarkerRequest,
		responses={201: BioMarkerResponse().response()},
	)
	@PostMapping('/create')
	@Authorized(True, permissions=['main.add_biomarker'])
	def addBioMarker(self, request, data: BioMarkerRequest):
		Logger.info('Validating biomarker data')
		if data.is_valid(raise_exception=True):
			validated_data = data.validated_data
			validated_data['uploadedBy'] = request.user
			biomarker = self.biomarkerService.create(validated_data)
			Logger.info(f'Biomarker {biomarker.id} created')
			return BioMarkerResponse(data=biomarker).json(status=HTTP_201_CREATED)

	@extend_schema(
		tags=['BioMarker'],
		summary='Update biomarker',
		description='Update biomarker',
		request=BioMarkerRequest,
		responses={200: BioMarkerResponse().response()},
	)
	@PutMapping('/<int:bid>')
	@Authorized(True, permissions=['main.change_biomarker'])
	def updateBioMarker(self, request, bid: int, data: BioMarkerRequest):
		Logger.info('Validating biomarker data')
		if data.is_valid(raise_exception=True):
			biomarker = self.biomarkerService.update(self.biomarkerService.getById(bid), data.validated_data)
			Logger.info(f'Biomarker {biomarker.id} updated')
			return BioMarkerResponse(data=biomarker).json()

	@extend_schema(
		tags=['BioMarker'],
		summary='Review biomarker',
		description='Approve or reject a pending biomarker',
		request=BioMarkerReviewRequest,
		responses={200: BioMarkerResponse().response()},
	)
	@PostMapping('/<int:bid>/review')
	@Authorized(True, permissions=['main.change_biomarker'])
	def reviewBioMarker(self, request, bid: int, data: BioMarkerReviewRequest):
		Logger.info(f'Validating biomarker review for {bid}')
		if data.is_valid(raise_exception=True):
			biomarker = self.biomarkerService.getById(bid)
			biomarker.status = data.validated_data['status']
			biomarker.administeredBy = request.user
			biomarker.save()
			Logger.info(f'Biomarker {biomarker.id} reviewed as {biomarker.status}')
			return BioMarkerResponse(data=biomarker).json()

	@extend_schema(
		tags=['BioMarker'],
		summary='Delete biomarker',
		description='Delete biomarker',
	)
	@DeleteMapping('/<int:bid>')
	@Authorized(True, permissions=['main.delete_biomarker'])
	def deleteBioMarker(self, request, bid: int):
		Logger.info(f'Deleting biomarker {bid}')
		self.biomarkerService.delete(bid)
		Logger.info(f'Biomarker {bid} deleted')
		return Return.ok()

	@extend_schema(
		tags=['BioMarker'],
		summary='Get biomarker',
		description='Get biomarker',
		responses={200: BioMarkerResponse().response()},
	)
	@GetMapping('/<int:bid>')
	@Authorized(True, permissions=['main.view_biomarker'])
	def getBioMarker(self, request, bid: int):
		Logger.info(f'Fetching biomarker {bid}')
		biomarker = self.biomarkerService.getById(bid)
		return BioMarkerResponse(data=biomarker).json()
