from rest_framework import serializers

__all__ = ['PageableRequest']


class PageableRequest(serializers.Serializer):
    sortBy = serializers.ListField(
        child=serializers.CharField(), required=False, allow_null=True,
    )
    page = serializers.IntegerField(default=1, required=False, allow_null=True)
    limit = serializers.IntegerField(default=10, required=False, allow_null=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        page = attrs.get('page')
        limit = attrs.get('limit')

        if page is None and limit is None and not self.allow_null:
            raise serializers.ValidationError('Page and limit are required')
        return attrs
