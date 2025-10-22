from drf_spectacular.utils import extend_schema

from biom.services import StudyService
from vvecon.zorion.serializers import Response, Return
from vvecon.zorion.views import API, GetMapping, Mapping
from ..payload.requests import StudyRequest
from ..payload.responses import StudyResponse

__all__ = ['V1Study']


@Mapping('api/v1/studies')
class V1Study(API):
	studyService: StudyService = StudyService()

	@extend_schema(
		tags=['Studies'],
		summary='Get paginated studies',
		description='Get paginated list of studies with optional search and filters',
		request=StudyRequest,
		responses={200: StudyResponse},
	)
	@GetMapping('/')
	def getStudies(self, request, data: StudyRequest):
		if data.is_valid(raise_exception=True):
			page = data.validated_data.get('page', 1)
			limit = data.validated_data.get('limit', 10)
			search = data.validated_data.get('search', None)

			# Build filters
			filters = {}
			if data.validated_data.get('status'):
				filters['status'] = data.validated_data.get('status')
			if data.validated_data.get('category'):
				filters['category'] = data.validated_data.get('category')

			# Get paginated studies
			result = self.studyService.getPaginatedStudies(
				page=page,
				limit=limit,
				search=search,
				filters=filters if filters else None
			)

			return Return.ok(dict(
				studies=StudyResponse(data=result['studies'], many=True).json().data,
				pagination=result['pagination']
			))
