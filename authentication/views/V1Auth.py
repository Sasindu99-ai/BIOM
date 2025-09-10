from concurrent.futures import ThreadPoolExecutor

import requests
from drf_spectacular.utils import extend_schema

from settings.payload.responses import CountryResponse
from settings.services.CountryService import CountryService
from vvecon.zorion.logger import Logger
from vvecon.zorion.views import API, GetMapping, Mapping, PostMapping

from ..payload.requests import LoginRequest, RegisterRequest
from ..payload.responses import TokenResponse
from ..services import UserService

__all__ = ['V1Auth']


@Mapping('api/v1/auth')
class V1Auth(API):
	executor = ThreadPoolExecutor()
	userService: UserService = UserService()
	countryService: CountryService = CountryService()

	@extend_schema(
		tags=['Auth'],
		summary='Get client country',
		description='Get client country',
		responses={200: CountryResponse().response()},
	)
	@GetMapping('/country')
	def getCountryFromRequest(self, request):
		IP = request.META.get('HTTP_X_FORWARDED_FOR')
		geo = requests.get(f'https://ip-api.com/json/{IP}', timeout=10).json()
		if geo['status'] == 'fail':
			country = self.countryService.getByName('Sri Lanka')
		else:
			country = self.countryService.getByName(geo['country'])
		return CountryResponse(data=country).json()

	@extend_schema(
		tags=['Auth'],
		summary='Login',
		description='Login',
		request=LoginRequest,
		responses={200: TokenResponse},
	)
	@PostMapping('/login')
	def login(self, request, data: LoginRequest):
		Logger.info(f'Validating login data: {data.initial_data}')
		if data.is_valid(raise_exception=True):
			Logger.info('Login data is valid')
			tokens = self.userService.authenticate(
				request, data.validated_data['username'], data.validated_data['password'],
			)
			return TokenResponse(data=tokens).json()

	@extend_schema(
		tags=['Auth'],
		summary='Register',
		description='Register',
		request=RegisterRequest,
		responses={200: TokenResponse},
	)
	@PostMapping('/register')
	def register(self, request, data: RegisterRequest):
		Logger.info(f'Validating registration data: {data.initial_data}')
		if data.is_valid(raise_exception=True):
			Logger.info('Registration data is valid')
			Logger.info(f'Creating user {data.validated_data["username"]}')
			user = self.userService.create(data.validated_data)
			user.set_password(data.validated_data['password'])
			user.save()
			Logger.info(f'User {user.username} created successfully')
			tokens = self.userService.authenticate(request, user.username, data.validated_data['password'])
			return TokenResponse(data=tokens).json()
