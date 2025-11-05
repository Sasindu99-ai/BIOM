from vvecon.zorion import serializers
from ...models import StudyVariable

__all__ = ['StudyVariableResponse']


class StudyVariableResponse(serializers.ModelResponse):
	model = StudyVariable
	fields = '__all__'
