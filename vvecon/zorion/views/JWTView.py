from rest_framework_simplejwt.views import TokenObtainPairView

from ..auth import JWTProvider

__all__ = ['JWTView']


class JWTView(TokenObtainPairView):
    serializer_class = JWTProvider
