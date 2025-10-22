from rest_framework import serializers

__all__ = ['StudyRequest']


class StudyRequest(serializers.Serializer):
	page = serializers.IntegerField(default=1, required=False, min_value=1)
	limit = serializers.IntegerField(default=10, required=False, min_value=1, max_value=100)
	search = serializers.CharField(required=False, allow_blank=True)
	status = serializers.CharField(required=False, allow_blank=True)
	category = serializers.CharField(required=False, allow_blank=True)
