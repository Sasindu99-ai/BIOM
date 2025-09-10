from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

__all__ = ['JWTProvider']


class JWTProvider(TokenObtainPairSerializer):
    token_class = AccessToken

    @classmethod
    def generateTokens(cls, user):
        token = super().get_token(user)
        return dict(token=str(token), refresh=str(RefreshToken.for_user(user)))
