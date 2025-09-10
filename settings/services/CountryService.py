from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound

from vvecon.zorion.core import Service

from ..models import Country

__all__ = ['CountryService']


class CountryService(Service):
    model = Country
    filterableFields = ('code', 'name')

    def getByCountryCode(self, countryCode: str):
        try:
            country = self.model.objects.filter(code=countryCode).first()
            if country is None:
                raise NotFound('Country not found')
            return country
        except ObjectDoesNotExist as e:
            raise NotFound('Country not found') from e

    def getByName(self, name: str) -> Country:
        try:
            country = self.model.objects.filter(name=name).first()
            if country is None:
                raise NotFound('Country not found')
            return country
        except ObjectDoesNotExist as e:
            raise NotFound('Country not found') from e
