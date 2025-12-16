from rest_framework import serializers

from vvecon.zorion import serializers as zorion_serializers

from ...models import Study

__all__ = ['StudyListResponse', 'StudyResponse']


class StudyResponse(zorion_serializers.ModelResponse):
	id = zorion_serializers.SerializerMethodField()
	model = Study
	fields = ('id', 'name', 'description', 'status', 'category', 'createdAt', 'updatedAt', 'reference', 'version')

	@staticmethod
	def get_id(obj):
		return str(obj.id)


class StudyListResponse(serializers.Serializer):
	studies = zorion_serializers.SerializerMethodField()
	pagination = serializers.DictField()

	def get_studies(self, obj):
		studies = obj.get('studies', [])
		return StudyResponse(data=studies, many=True).json().data
