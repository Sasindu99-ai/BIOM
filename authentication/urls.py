from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from vvecon.zorion.urls import paths
from vvecon.zorion.views import JWTView

from .views import V1Auth, V1Channel, V1Device, V1Profile

urlpatterns = paths([V1Auth, V1Channel, V1Profile, V1Device]) + [
    path('api/v1/auth/token', JWTView.as_view(), name='token'),
    path('api/v1/auth/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
]
