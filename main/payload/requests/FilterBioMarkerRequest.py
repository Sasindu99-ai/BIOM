from settings.payload.requests import PageableRequest
from vvecon.zorion import serializers

from ...models import BioMarker

__all__ = ['FilterBioMarkerRequest']


class FilterBioMarkerRequest(serializers.ModelRequest):
	search = serializers.CharField(max_length=100, required=False)
	pagination = PageableRequest(allow_null=True)
	sortField = serializers.CharField(max_length=50, required=False, default='created_at')
	sortDirection = serializers.CharField(max_length=4, required=False, default='desc')

	class Meta:
		model = BioMarker
		fields = ('search', 'pagination', 'status', 'type', 'biomType', 'sortField', 'sortDirection')
		extra_kwargs = dict(
			status=dict(required=False),
			type=dict(required=False),
			biomType=dict(required=False),
		)
