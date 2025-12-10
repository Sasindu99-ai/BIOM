from settings.payload.requests import PageableRequest
from vvecon.zorion import serializers
from ...models import Study

__all__ = ['FilterDataSetRequest']


class FilterDataSetRequest(serializers.ModelRequest):
	search = serializers.CharField(max_length=100, required=False)
	pagination = PageableRequest(allow_null=True)
	sortField = serializers.CharField(max_length=50, required=False, default='created_at')
	sortDirection = serializers.CharField(max_length=4, required=False, default='desc')

	class Meta:
		model = Study
		fields = ('search', 'pagination', 'status', 'category', 'createdBy', 'sortField', 'sortDirection')
		extra_kwargs = dict(
			status=dict(required=False),
			category=dict(required=False),
			createdBy=dict(required=False),
		)
