from vvecon.zorion import serializers

from ...models import Channel
from .IceCastServerResponse import IceCastServerResponse

__all__ = ['ChannelResponse']


class ChannelResponse(serializers.ModelResponse):
	iceCastServers = serializers.SerializerMethodField()

	model = Channel
	fields = ('id', 'name', 'description', 'user', 'publicId', 's3FolderPath', 'isActive', 'iceCastServers')

	@staticmethod
	def get_iceCastServers(obj):
		return IceCastServerResponse(data=obj.icecast_servers.all(), many=True).json().data
