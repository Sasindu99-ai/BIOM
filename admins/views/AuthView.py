from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect

from authentication.payload.requests import LoginRequest
from authentication.services import UserService
from res import R
from vvecon.zorion.auth import Authenticated
from vvecon.zorion.logger import Logger
from vvecon.zorion.views import GetMapping, Mapping, PostMapping, View

__all__ = ['AuthView']


@Mapping('dashboard/auth')
class AuthView(View):
	R: R = R()

	userService: UserService = UserService()

	def authConfig(self):
		self.R.data.navigator.enabled = False
		self.R.data.aside['admin'].enabled = False

	@GetMapping('/')
	def auth(self, request):
		self.authConfig()

		if request.user.is_authenticated:
			return redirect('dashboard')

		return self.render(request, dict(validated=False), 'dashboard/auth')

	@PostMapping('/')
	def login(self, request, data: LoginRequest):
		self.authConfig()

		errors = dict()

		Logger.info(f"Validating Login Request: {data.initial_data['email']}")
		if data.is_valid(raise_exception=False):
			Logger.info(f"Login Request is Valid: {data.validated_data['email']}")
			valid, error = self.userService.validatePassword(data.validated_data['password'])
			if not valid:
				Logger.info(f'Password Validation Error: {error}')
				errors['password'] = error
			else:
				Logger.info(f"Authenticating User: {data.validated_data['email']}")
				user = self.userService.getByEmail(data.validated_data['email'], None)
				if user is None:
					Logger.info(f"User Not Found: {data.validated_data['email']}")
					errors['login'] = 'Invalid Email Address or Password!'
				else:
					Logger.info(f'Authenticating User: {user.mobileNumber}')
					user = authenticate(request, username=user.username, password=data.validated_data['password'])
					if user is None:
						Logger.info(f"Invalid Password: {data.validated_data['email']}")
						errors['login'] = 'Invalid Email Address or Password!'
					else:
						Logger.info(f'Login Success: {user.mobileNumber}')
						login(request, user)

						if data.validated_data.get('remember'):
							request.session.set_expiry(1209600)
						else:
							request.session.set_expiry(0)
						Logger.info(f'Redirecting to Admin Dashboard: {user.mobileNumber}')
						return redirect('dashboard')
		else:
			if 'email' in data.errors:
				errors['email'] = data.errors['email'][0]
			if 'password' in data.errors:
				errors['password'] = data.errors['password'][0]

		data.validated_data.pop('password', None)
		context = dict(errors=errors, validated=True, data=data.validated_data)

		return self.render(request, context, 'dashboard/auth')

	@GetMapping('/forget-password')
	def forgetPassword(self, request):
		return self.render(request, dict(), 'dashboard/auth/forget-password')

	@PostMapping('/logout')
	@Authenticated()
	def logout(self, request):
		logout(request)

		# Flushing the session
		if hasattr(request, 'session'):
			request.session.flush()

		# Redirecting the user to the home page
		return redirect('dashboard')
