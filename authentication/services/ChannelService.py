import uuid

import boto3
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound, ValidationError

from vvecon.zorion.core import Service
from vvecon.zorion.logger import Logger

from ..models import Channel
from .IceCastServerService import IceCastServerService

__all__ = ['ChannelService']


class ChannelService(Service):
	model = Channel
	searchableFields = ('name', 'description')
	filterableFields = ('user', 'isActive')

	def __init__(self, *args, **kwargs):
		super(ChannelService, self).__init__(*args, **kwargs)
		self.iceCastServerService = IceCastServerService()

	def getByName(self, name: str) -> Channel:
		return self.model.objects.filter(name=name).first()

	def getByUser(self, user_id: uuid.UUID) -> list[Channel]:
		return self.model.objects.filter(user_id=user_id, isActive=True)

	def getByPublicId(self, publicId: uuid.UUID) -> Channel:
		try:
			return self.model.objects.get(publicId=publicId)
		except (ObjectDoesNotExist, ValidationError):
			raise NotFound(f'Channel {publicId} not found')

	def createChannel(self, user, data: dict) -> Channel:
		# Check if a channel with this name already exists
		if self.getByName(data['name']) is not None:
			Logger.error(f"Channel with name {data['name']} already exists.")
			raise ValidationError(f"Channel with name {data['name']} already exists.")

		# Add user to data
		data['user'] = user

		testing = True

		if not testing:
			# Create S3 folder path
			s3_folder_name = f'channel_{uuid.uuid4()}'
			data['s3FolderPath'] = s3_folder_name

			# Create a tracks folder in S3 bucket
			self._createS3TracksFolder(s3_folder_name)

			# Create a channel in the icecast server
			icecast_mount_point, icecast_password = self.iceCastServerService.createIcecastChannel(data['name'])
		else:
			# In production, we would not create an S3 folder or Icecast channel here
			data['s3FolderPath'] = f'channel_{uuid.uuid4()}'
			icecast_mount_point = f"/{data['name'].lower().replace(' ', '_')}"
			icecast_password = str(uuid.uuid4())[:12]

		# Create a channel
		channel = self.create(data)
		Logger.info(f'Channel created: {channel}')

		# Create an IceCast server configuration for the channel
		self.iceCastServerService.createIceCastServer(dict(
			icecastMountPoint=icecast_mount_point,
			icecastPassword=icecast_password,
			channel=channel,
			isActive=True,
			isSecret=True,
		))
		Logger.info(f'IceCast server created for channel: {channel.name}')

		return channel


	@staticmethod
	def _createS3TracksFolder(folder_name: str) -> None:
		Logger.info(f'Creating S3 channel folder: {folder_name}')
		try:
			s3_client = boto3.client(
				's3',
				aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
				aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
				region_name=settings.AWS_S3_REGION_NAME,
			)
			s3_client.put_object(
				Bucket=settings.AWS_STORAGE_BUCKET_NAME,
				Key=f'{folder_name}/',
			)
			Logger.info(f'Successfully created S3 channel folder: {folder_name}')
		except Exception as e:
			error_msg = 'Failed to create S3 channel folder'
			Logger.error(f'error_msg: {e!s}')
			raise ValidationError(error_msg)
