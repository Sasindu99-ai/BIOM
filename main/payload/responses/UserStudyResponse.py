from vvecon.zorion import serializers
from ...models import UserStudy

__all__ = ['UserStudyResponse']


class UserStudyResponse(serializers.ModelResponse):
	model = UserStudy
	fields = '__all__'
