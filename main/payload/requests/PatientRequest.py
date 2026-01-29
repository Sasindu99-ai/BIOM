from vvecon.zorion import serializers

from ...models import Patient

__all__ = ['PatientRequest']


class PatientRequest(serializers.ModelRequest):
	class Meta:
		model = Patient
		fields = '__all__'
