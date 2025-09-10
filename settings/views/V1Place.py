
from settings.services import LocationService
from vvecon.zorion.views import API, Mapping

__all__ = ['V1Place']


@Mapping('api/v1/place')
class V1Place(API):
    locationService: LocationService = LocationService()

