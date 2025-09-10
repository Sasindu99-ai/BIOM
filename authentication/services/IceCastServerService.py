import uuid
from urllib.parse import urljoin

import defusedxml.ElementTree as ET
import requests
from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework.status import HTTP_200_OK

from vvecon.zorion.core import Service
from vvecon.zorion.logger import Logger

from ..models import IceCastServer

__all__ = ['IceCastServerService']


class IceCastServerService(Service):
	model = IceCastServer
	searchableFields = ('icecastMountPoint', 'host')
	filterableFields = ('isActive', 'isSecret', 'channel')

	def createIceCastServer(self, data: dict) -> IceCastServer:
		"""Create a new IceCast server configuration"""
		if self.model.objects.filter(icecastMountPoint=data['icecastMountPoint']).exists():
			Logger.error(f"Mount point {data['icecastMountPoint']} already exists")
			raise ValidationError(f"Mount point {data['icecastMountPoint']} already exists")

		# Set default values from settings if not provided
		data['host'] = settings.ICECAST_SERVER_HOST
		data['port'] = settings.ICECAST_SERVER_PORT
		data['username'] = settings.ICECAST_ADMIN_USER
		data['password'] = settings.ICECAST_ADMIN_PASSWORD

		return self.create(data)

	def getByMountPoint(self, mount_point: str) -> IceCastServer:
		"""Get IceCast server configuration by mount point"""
		return self.model.objects.filter(
			icecastMountPoint=mount_point,
			isActive=True,
		).first()

	def getByChannel(self, channel_id) -> list[IceCastServer]:
		"""Get IceCast server configurations by channel"""
		return self.model.objects.filter(
			channel_id=channel_id,
			isActive=True,
		)

	def deactivateServer(self, mount_point: str) -> bool:
		"""Deactivate an IceCast server configuration"""
		server = self.getByMountPoint(mount_point)
		if server:
			server.isActive = False
			server.save()
			return True
		return False

	@staticmethod
	def createIcecastChannel(channel_name: str) -> tuple[str, str]:
		Logger.info(f'Creating icecast channel: {channel_name}')
		mount_point = f"/{channel_name.lower().replace(' ', '_')}"
		password = str(uuid.uuid4())[:12]
		if not all([
			settings.ICECAST_SERVER_HOST,
			settings.ICECAST_ADMIN_USER,
			settings.ICECAST_ADMIN_PASSWORD,
		]):
			Logger.warning('Icecast server settings not fully configured, using generated mount point and password')
			return mount_point, password

		try:
			icecast_url = f'http://{settings.ICECAST_SERVER_HOST}:{settings.ICECAST_SERVER_PORT}'
			admin_url = urljoin(icecast_url, '/admin/')

			xml_payload = f"""
				<icecast>
					<mount>
						<mount-name>{mount_point}</mount-name>
						<password>{password}</password>
						<max-listeners>{settings.ICECAST_MAX_LISTENERS}</max-listeners>
						<stream-name>{channel_name}</stream-name>
						<stream-description>Channel for {channel_name}</stream-description>
						<public>1</public>
					</mount>
				</icecast>
				"""

			response = requests.post(
				urljoin(admin_url, 'mountpoint/add'),
				auth=(settings.ICECAST_ADMIN_USER, settings.ICECAST_ADMIN_PASSWORD),
				data=xml_payload,
				headers={'Content-Type': 'application/xml'},
				timeout=10,
			)

			if response.status_code == HTTP_200_OK:
				root = ET.fromstring(response.text)
				success = root.find('success')

				if success is not None and success.text == 'true':
					Logger.info(f'Successfully created Icecast mount point: {mount_point}')
					return mount_point, password
				error = root.find('error')
				error_msg = error.text if error is not None else 'Unknown error'
				Logger.error(f'Failed to create Icecast mount point: {error_msg}')
			else:
				Logger.error(f'Icecast server returned status code {response.status_code}: {response.text}')

		except requests.RequestException as e:
			Logger.error(f'Error communicating with Icecast server: {e!s}')
		except Exception as e:
			Logger.error(f'Unexpected error creating Icecast channel: {e!s}')
		Logger.warning(f'Using fallback mount point and password for channel: {channel_name}')
		return mount_point, password
