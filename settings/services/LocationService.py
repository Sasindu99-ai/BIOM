import os

import requests
from django.core.exceptions import ObjectDoesNotExist

from vvecon.zorion.logger import Logger

__all__ = ['LocationService']


class LocationService:
	BASE_URL = 'https://maps.googleapis.com/maps/api/'
	GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

	def callAPI(self, action: str, params: dict) -> dict:
		params['key'] = self.GOOGLE_MAPS_API_KEY
		url = f'{self.BASE_URL}{action}'

		try:
			Logger.info(f'Calling Google Maps API: {url} {params}')
			response = requests.get(url, params=params, timeout=10)
			response.raise_for_status()
			return response.json()
		except requests.exceptions.RequestException as e:
			errorMsg = f'Error calling Google Maps API: {e}'
			Logger.error(errorMsg)
			raise ObjectDoesNotExist(errorMsg) from e

	def autoComplete(
		self,
		query: str,
		components: str | None = None,
		placeType: str | None = None,
	) -> dict:
		params = dict(input=query)
		if components:
			params['components'] = components
		if placeType:
			params['type'] = placeType
		return self.callAPI('place/autocomplete/json', params)

	def locationInfo(self, placeId: str) -> dict:
		params = dict(place_id=placeId)
		return self.callAPI('place/details/json', params)

	def distance(self, origin: dict, destination: dict) -> dict:
		params = dict(
			origins=f"{origin.get('lat')},{origin.get('lng')}",
			destinations=f"{destination.get('lat')},{destination.get('lng')}",
		)
		return self.callAPI('distancematrix/json', params)
