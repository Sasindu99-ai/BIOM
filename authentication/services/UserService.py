import re

from django.contrib.auth import authenticate, login
from rest_framework.exceptions import PermissionDenied

from settings.services import CountryService
from vvecon.zorion.auth import JWTProvider
from vvecon.zorion.core import Service
from vvecon.zorion.logger import Logger

from ..models import User

__all__ = ['UserService']


class UserService(Service):
	model = User
	updateInclude = ('firstName', 'lastName')

	class Meta:
		model = User
		fields = '__all__'

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.countryService = CountryService()

	@staticmethod
	def validatePassword(password: str) -> tuple[bool, str]:
		if not re.search(r'\d', password):
			return False, 'Password must contain at least one digit'
		if not re.search(r'[A-Z]', password):
			return False, 'Password must contain at least one uppercase letter'
		if not re.search(r'[a-z]', password):
			return False, 'Password must contain at least one lowercase letter'
		if not re.search(r'[@_!#$%^&*()<>?/\\|}{~:]', password):
			return False, 'Password must contain at least one special character'
		return True, password


	@staticmethod
	def authenticate(request, username: str, password: str) -> dict:
		Logger.info(f'Authenticating user {username}')
		user = authenticate(request, username=username, password=password)
		if not user.has_perm('authentication.login_user'):
			Logger.info(f'User {user.username} does not have permission to login')
			raise PermissionDenied('You do not have permission to login')
		if not user.has_perm('authentication.login_user'):
			Logger.info(f'User {username} does not have permission to login')
			raise PermissionDenied('You do not have permission to login')
		login(request, user)
		Logger.info(f'User {user.username} authenticated successfully')
		Logger.info(f'Generating tokens for user {user.username}')
		tokens = JWTProvider().generateTokens(user)
		Logger.info(f'Tokens generated successfully for user {user.username}')
		return tokens
