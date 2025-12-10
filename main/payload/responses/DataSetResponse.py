from vvecon.zorion import serializers
from ...models import Study

__all__ = ['DataSetResponse']


class DataSetResponse(serializers.ModelResponse):
	variablesCount = serializers.IntegerField(read_only=True, required=False)
	userStudiesCount = serializers.IntegerField(read_only=True, required=False)

	model = Study
	fields = (
		'id', 'name', 'description', 'category', 'status', 'version',
		'reference', 'created_at', 'updated_at', 'createdBy',
		'variablesCount', 'userStudiesCount'
	)

	def to_representation(self, instance):
		data = super().to_representation(instance)
		
		# Add computed fields
		data['variablesCount'] = instance.variables.count() if hasattr(instance, 'variables') else 0
		data['userStudiesCount'] = instance.userStudies.count() if hasattr(instance, 'userStudies') else 0
		
		# Add creator name if available
		if instance.createdBy:
			data['createdByName'] = f"{instance.createdBy.firstName} {instance.createdBy.lastName}".strip()
		
		return data
