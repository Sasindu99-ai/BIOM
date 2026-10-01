from .auth import ApiKeyAuthentication

__all__ = ['ApiKeyMiddleware']


class ApiKeyMiddleware:
	"""
	Middleware that inspects incoming requests for an API key header
	(X-API-Key or Authorization: Bearer/Api-Key). If present and valid,
	attaches the authenticated staff/superuser to request.user.
	"""

	def __init__(self, get_response):
		self.get_response = get_response
		self.auth = ApiKeyAuthentication()

	def __call__(self, request):
		if not getattr(request, 'user', None) or not request.user.is_authenticated:
			try:
				user_auth = self.auth.authenticate(request)
				if user_auth:
					request.user, request.auth = user_auth
			except Exception:
				# Authentication failure in middleware is ignored here to let
				# DRF or downstream view decorators issue standard 401/403 responses.
				pass
		return self.get_response(request)
