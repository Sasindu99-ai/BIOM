from vvecon.zorion import serializers

from ...models import Channel

__all__ = ['ChannelRequest']


class ChannelRequest(serializers.ModelRequest):
    class Meta:
        model = Channel
        fields = ('name', 'description')
