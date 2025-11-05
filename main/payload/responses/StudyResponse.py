from authentication.payload.responses import UserResponse
from vvecon.zorion import serializers
from ...models import Study

__all__ = ['StudyResponse']


class StudyResponse(serializers.ModelResponse):
	members = UserResponse(many=True).response()

	model = Study
	fields = '__all__'
