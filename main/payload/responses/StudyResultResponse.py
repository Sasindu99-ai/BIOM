from vvecon.zorion import serializers

from ...models import StudyResult
from .StudyVariableResponse import StudyVariableResponse

__all__ = ['StudyResultResponse']


class StudyResultResponse(serializers.ModelResponse):
	studyVariable = StudyVariableResponse().response()

	model = StudyResult
	fields = '__all__'
