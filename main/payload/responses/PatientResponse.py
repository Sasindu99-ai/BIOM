from vvecon.zorion import serializers
from ...models import Patient

__all__ = ['PatientResponse']


class PatientResponse(serializers.ModelResponse):
	model = Patient
	fields = '__all__'
