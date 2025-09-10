from drf_spectacular.utils import extend_schema

from vvecon.zorion.auth import Authorized
from vvecon.zorion.logger import Logger
from vvecon.zorion.views import API, GetMapping, Mapping

from ..payload.responses import UserResponse
from ..services import UserService

__all__ = ['V1Profile']


@Mapping('api/v1/profile')
class V1Profile(API):
	userService: UserService = UserService()

	@extend_schema(
		tags=['Profile'],
		summary='Get user profile',
		description='Get user profile',
		responses={200: UserResponse().response()},
	)
	@GetMapping()
	@Authorized(authorized=True, permissions=['authentication.view_profile'])
	def getProfile(self, request):
		Logger.info(f'Fetching user profile for {request.user.username}')
		return UserResponse(data=self.userService.getById(request.user.id)).json()
