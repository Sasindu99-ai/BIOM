from typing import ClassVar

from settings.payload.requests import PageableRequest
from vvecon.zorion import serializers

from ...models import Channel

__all__ = ['FilterChannelRequest']


class FilterChannelRequest(serializers.ModelRequest):
	search = serializers.CharField(required=False, allow_blank=True, allow_null=True)
	pagination = PageableRequest(required=False, allow_null=True)

	class Meta:
		model = Channel
		fields = ('search', 'user', 'isActive', 'pagination')
		extra_kwargs: ClassVar = dict(
			user=dict(required=False),
			isActive=dict(required=False),
		)
