from vvecon.zorion import serializers

from ...models import Place

__all__ = ['PlaceResponse']


class PlaceResponse(serializers.ModelResponse):
    place = serializers.SerializerMethodField()

    model = Place
    fields = ('id', 'name', 'placeId', 'latitude', 'longitude', 'place')

    @staticmethod
    def get_place(obj):
        return obj.name.split(',')[0].strip()
