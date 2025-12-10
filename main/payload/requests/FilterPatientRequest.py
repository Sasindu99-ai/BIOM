from settings.payload.requests import PageableRequest
from vvecon.zorion import serializers
from ...models import Patient

__all__ = ['FilterPatientRequest']


class FilterPatientRequest(serializers.ModelRequest):
	search = serializers.CharField(max_length=100, required=False)
	pagination = PageableRequest(allow_null=True)
	age = serializers.IntegerField(required=False)

	class Meta:
		model = Patient
		fields = ('search', 'pagination', 'dateOfBirth', 'gender', 'createdBy', 'age')
		extra_kwargs = dict(
			gender=dict(required=False),
		)
