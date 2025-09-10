from collections.abc import Callable
from unittest import TestCase as TestCaseAbstract

from django.test import Client
from django.urls import reverse

from vvecon.zorion.config import TestConfig

__all__ = ['TestCase']


class TestCase(TestCaseAbstract):
    """
	TestCase class for testing API endpoints

	Description:
		TestCase class is used to test API endpoints by sending requests to the API endpoints and receiving responses.
		TestCase class uses Django test client to send requests to the API endpoints.
		TestCase class includes methods to send POST, GET, PUT, and DELETE requests to the API endpoints.
		TestCase class includes a method to retry login if JWT token is expired.

	Attributes:
		api (str): API endpoint
		auth (TestConfig): Test configuration
		JWTToken (str): JWT token
		RefreshToken (str): Refresh token
		client (Client): Django test client

	Methods:
		_retryLogin: Retry login if JWT token is expired
		post: Send POST request to API endpoint
		get: Send GET request to API endpoint
		put: Send PUT request to API endpoint
		delete: Send DELETE request to API endpoint
	"""

    api: str = NotImplemented
    auth: TestConfig = NotImplemented
    JWTToken: str = NotImplemented
    RefreshToken: str = NotImplemented
    client: Client = Client()

    def _retryLogin(self, method: Callable, endpoint: str, data: dict):
        """
		Retry login if JWT token is expired
		:param method: Method to retry
		:type method: Callable
		:param endpoint: API endpoint
		:type endpoint: str
		:param data: Data to send
		:type data: dict
		:return: Response
		"""
        if self.RefreshToken is NotImplemented:
            response = self.client.post(
                reverse(self.auth.authUrl), data=self.auth.credentials, follow=True, secure=True,
            )
            jsonData = response.json()
            self.JWTToken = jsonData.get('token')
            self.RefreshToken = jsonData.get('refresh')
        else:
            response = self.client.post(
                reverse(self.auth.refreshUrl), data=dict(refresh=self.RefreshToken), follow=True, secure=True,
            )
            jsonData = response.json()
            self.JWTToken = jsonData.get('access')
        return method(endpoint, data, isAuthorized=True, retry=False)

    def post(self, endpoint: str, data: dict, *, isAuthorized: bool, retry: bool = True, reverseUrl: bool = False):
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
		:param reverseUrl: Reverse URL
		:type reverseUrl: bool
		:return: Response
		"""
        url = reverse(self.api + endpoint) if reverseUrl else self.api + endpoint
        if not isAuthorized:
            return self.client.post(url, data=data, follow=True, secure=True, content_type='application/json')
        response = self.client.post(
            url,
            data=data,
            follow=True,
            secure=True,
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.JWTToken}'},
        )
        if response.status_code in (400, 401, 403) and retry:
            return self._retryLogin(self.post, endpoint, data)
        return response

    def get(self, endpoint: str, params: dict, *, isAuthorized: bool, retry: bool = True, reverseUrl: bool = False):
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
		:param reverseUrl: Reverse URL
		:type reverseUrl: bool
		:return: Response
		"""
        paramString = '&'.join([f'{key}={value}' for key, value in params.items()])
        url = reverse(self.api + endpoint) if reverseUrl else self.api + endpoint
        if not isAuthorized:
            return self.client.get(url + f'?{paramString}', follow=True, secure=True, content_type='application/json')
        response = self.client.get(
            url + f'?{paramString}',
            follow=True,
            secure=True,
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.JWTToken}'},
        )
        if response.status_code in (400, 401, 403) and retry:
            return self._retryLogin(self.get, endpoint, {})
        return response

    def put(self, endpoint: str, data: dict, *, isAuthorized: bool, retry: bool = True, reverseUrl: bool = False):
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
		:param reverseUrl: Reverse URL
		:type reverseUrl: bool
		:return: Response
		"""
        url = reverse(self.api + endpoint) if reverseUrl else self.api + endpoint
        if not isAuthorized:
            return self.client.put(url, data=data, follow=True, secure=True, content_type='application/json')
        response = self.client.put(
            url,
            data=data,
            follow=True,
            secure=True,
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.JWTToken}'},
        )
        if response.status_code in (400, 401, 403) and retry:
            return self._retryLogin(self.put, endpoint, data)
        return response

    def delete(self, endpoint: str, data: dict, *, isAuthorized: bool, retry: bool = True, reverseUrl: bool = False):
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
		:param reverseUrl: Reverse URL
		:type reverseUrl: bool
		:return: Response
		"""
        url = reverse(self.api + endpoint) if reverseUrl else self.api + endpoint
        if not isAuthorized:
            return self.client.delete(url, data=data, follow=True, secure=True, content_type='application/json')
        response = self.client.delete(
            url,
            data=data,
            follow=True,
            secure=True,
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.JWTToken}'},
        )
        if response.status_code in (400, 401, 403) and retry:
            return self._retryLogin(self.delete, endpoint, data)
        return response
