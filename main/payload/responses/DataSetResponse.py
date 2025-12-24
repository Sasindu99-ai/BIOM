from vvecon.zorion import serializers

from ...models import Study

__all__ = ['DataSetResponse']


class DataSetResponse(serializers.ModelResponse):
	variablesCount = serializers.SerializerMethodField()
	userStudiesCount = serializers.SerializerMethodField()
	createdByName = serializers.SerializerMethodField()

	model = Study
	fields = (
		'id', 'name', 'description', 'category', 'status', 'version',
		'reference', 'created_at', 'updated_at', 'createdBy',
		'variablesCount', 'userStudiesCount', 'createdByName',
	)

	def get_variablesCount(self, obj):
		return obj.variables.count() if hasattr(obj, 'variables') else 0

	def get_userStudiesCount(self, obj):
		return obj.userStudies.count() if hasattr(obj, 'userStudies') else 0

	def get_createdByName(self, obj):
		if obj.createdBy:
			return f'{obj.createdBy.firstName} {obj.createdBy.lastName}'.strip()
		return ''
