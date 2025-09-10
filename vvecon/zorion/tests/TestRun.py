from collections.abc import Callable
from unittest import TestCase as TestCaseAbstract

import requests

from vvecon.zorion.config import TestConfig

__all__ = ['TestRun']


class TestRun(TestCaseAbstract):
	"""
	TestRun class for testing the application

	Description:
		TestRun class is used to test API endpoints by sending requests to the API endpoints and receiving responses.
		TestRun class uses Django test client to send requests to the API endpoints.
		TestRun class includes methods to send POST, GET, PUT, and DELETE requests to the API endpoints.
		TestRun class includes a method to retry login if JWT token is expired.

	Attributes:
		api (str): API URL
		auth (TestConfig): TestConfig object
		JWTToken (str): JWT token
		RefreshToken (str): Refresh token

	Methods:
		_retryLogin: Retry login if JWT token is expired
		post: Send POST request
		get: Send GET request
		put: Send PUT request
		delete: Send DELETE request
	"""

	base: str = 'http://0.0.0.0'
	port: str = '8008'
	api: str = NotImplemented
	auth: TestConfig = NotImplemented
	JWTToken: str = NotImplemented
	RefreshToken: str = NotImplemented
	DEFAULT_TIMEOUT = 5

	def _retryLogin(
		self, method: Callable, endpoint: str, params: dict | list | None = None, data: dict | list | None = None,
	):
		"""
		Retry login if JWT token is expired
		:param method: Method to retry
		:type method: Callable
		:param endpoint: API endpoint
		:type endpoint: str
		:param data: Data to send
		:type data: dict
		:param params: Parameters
		:type params: dict | list | None
		:return: Response
		"""
		if self.RefreshToken is NotImplemented:
			response = requests.post(self.auth.authUrl, json=self.auth.credentials, timeout=self.DEFAULT_TIMEOUT)
			jsonData = response.json()
			self.JWTToken = jsonData.get('token')
			self.RefreshToken = jsonData.get('refresh')
		else:
			response = requests.post(
				self.auth.refreshUrl, json=dict(refresh=self.RefreshToken), timeout=self.DEFAULT_TIMEOUT,
			)
			jsonData = response.json()
			self.JWTToken = jsonData.get('access')
		return method(endpoint, isAuthorized=True, retry=False, params=params, data=data)

	def generateUrl(self, endpoint: str) -> str:
		"""
		Generate URL
		:param endpoint: API endpoint
		:type endpoint: str
		:return: URL
		"""
		return f'{self.base}' + ':' + f'{self.port}/{self.api}{endpoint}'

	def post(
		self,
		endpoint: str,
		data: dict | list,
		*,
		isAuthorized: bool,
		retry: bool = True,
		params: dict | list | None = None,
	):
		"""
		Send POST request
		:param endpoint: API endpoint
		:type endpoint: str
		:param data: Data to send
		:type data: dict
		:param isAuthorized: Is authorized
		:type isAuthorized: bool
		:param retry: Retry login
		:type retry: bool
		:param params: Parameters
		:type params: dict | list | None
		:return: Response
		"""
		if params is None:
			params = dict()
		if data is None:
			data = dict()
		url = self.generateUrl(endpoint)
		headers = {'Content-Type': 'application/json'}
		if isAuthorized:
			headers['Authorization'] = f'Bearer {self.JWTToken}'
		response = requests.post(url, json=data, headers=headers, timeout=self.DEFAULT_TIMEOUT)
		if response.status_code in (400, 401, 403) and retry and isAuthorized:
			return self._retryLogin(self.post, endpoint, params=params, data=data)
		return response

	def get(
		self,
		endpoint: str,
		params: dict | list,
		*,
		isAuthorized: bool,
		retry: bool = True,
		data: dict | list | None = None,
	):
		"""
		Send GET request
		:param endpoint: API endpoint
		:type endpoint: str
		:param params: Parameters
		:type params: dict
		:param isAuthorized: Is authorized
		:type isAuthorized: bool
		:param retry: Retry login
		:type retry: bool
		:param data: Data to send
		:type data: dict | list | None
		:return: Response
		"""
		if params is None:
			params = dict()
		if data is None:
			data = dict()
		url = self.generateUrl(endpoint)
		headers = {'Content-Type': 'application/json'}
		if isAuthorized:
			headers['Authorization'] = f'Bearer {self.JWTToken}'
		response = requests.get(url, params=params, headers=headers, timeout=self.DEFAULT_TIMEOUT)
		if response.status_code in (400, 401, 403) and retry and isAuthorized:
			return self._retryLogin(self.get, endpoint, params=params, data=data)
		return response

	def put(
		self,
		endpoint: str,
		data: dict | list,
		*,
		isAuthorized: bool,
		retry: bool = True,
		params: dict | list | None = None,
	):
		"""
		Send PUT request
		:param endpoint: API endpoint
		:type endpoint: str
		:param data: Data to send
		:type data: dict
		:param isAuthorized: Is authorized
		:type isAuthorized: bool
		:param retry: Retry login
		:type retry: bool
		:param params: Parameters
		:type params: dict | list | None
		:return: Response
		"""
		if params is None:
			params = dict()
		if data is None:
			data = dict()
		url = self.generateUrl(endpoint)
		headers = {'Content-Type': 'application/json'}
		if isAuthorized:
			headers['Authorization'] = f'Bearer {self.JWTToken}'
		response = requests.put(url, json=data, headers=headers, timeout=self.DEFAULT_TIMEOUT)
		if response.status_code in (400, 401, 403) and retry and isAuthorized:
			return self._retryLogin(self.put, endpoint, params=params, data=data)
		return response

	def delete(
		self,
		endpoint: str,
		data: dict | list,
		*,
		isAuthorized: bool,
		retry: bool = True,
		params: dict | list | None = None,
	):
		"""
		Send DELETE request
		:param endpoint: API endpoint
		:type endpoint: str
		:param data: Data to send
		:type data: dict
		:param isAuthorized: Is authorized
		:type isAuthorized: bool
		:param retry: Retry login
		:type retry: bool
		:param params: Parameters
		:type params: dict | list | None
		:return: Response
		"""
		if params is None:
			params = dict()
		if data is None:
			data = dict()
		url = self.generateUrl(endpoint)
		headers = {'Content-Type': 'application/json'}
		if isAuthorized:
			headers['Authorization'] = f'Bearer {self.JWTToken}'

		response = requests.delete(url, json=data, headers=headers, timeout=self.DEFAULT_TIMEOUT)
		if response.status_code in (400, 401, 403) and retry and isAuthorized:
			return self._retryLogin(self.delete, endpoint, params=params, data=data)
		return response
