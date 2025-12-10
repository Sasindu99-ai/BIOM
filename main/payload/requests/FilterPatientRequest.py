from settings.payload.requests import PageableRequest
from vvecon.zorion import serializers
from ...models import Patient

__all__ = ['FilterPatientRequest']


class FilterPatientRequest(serializers.ModelRequest):
	search = serializers.CharField(max_length=100, required=False)
	pagination = PageableRequest(allow_null=True)
	age = serializers.IntegerField(required=False)
	sortField = serializers.CharField(max_length=50, required=False, default='created_at')
	sortDirection = serializers.CharField(max_length=4, required=False, default='desc')

	class Meta:
		model = Patient
		fields = ('search', 'pagination', 'dateOfBirth', 'gender', 'createdBy', 'age', 'sortField', 'sortDirection')
		extra_kwargs = dict(
			gender=dict(required=False),
		)
