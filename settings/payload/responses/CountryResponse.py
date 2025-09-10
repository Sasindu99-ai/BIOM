from vvecon.zorion import serializers

from ...models import Country

__all__ = ['CountryResponse']


class CountryResponse(serializers.ModelResponse):
    model = Country
    fields = ('id', 'name', 'code', 'flag', 'length', 'emoji')
