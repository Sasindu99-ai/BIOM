import uuid

from drf_spectacular.utils import extend_schema
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED

from vvecon.zorion.logger import Logger
from vvecon.zorion.views import API, Mapping, PostMapping

from ..payload.requests import RegisterDeviceRequest
from ..payload.responses import DeviceResponse
from ..services import DeviceService

__all__ = ['V1Device']


@Mapping('api/v1/device')
class V1Device(API):
	deviceService = DeviceService()

	@extend_schema(
		tags=['Device'],
		summary='Register a new device',
		description='Register a new device with the provided data',
		request=RegisterDeviceRequest,
		responses={201: DeviceResponse().response()},
	)
	@PostMapping('/register')
	def registerDevice(self, request, data: RegisterDeviceRequest):
		Logger.info(f'Registering device with data: {data.initial_data}')
		if data.is_valid(raise_exception=True):
			Logger.info('Device data is valid')
			device = self.deviceService.registerDevice(
				request, data,
			)
			return DeviceResponse(data=device).json(status=HTTP_201_CREATED)

	@extend_schema(
		tags=['Device'],
		summary='Validate a device',
		description='Validate a device by its public ID and update its lastSeen timestamp',
		responses={200: DeviceResponse().response()},
	)
	@PostMapping('/<uuid:deviceId>/validate')
	def validateDevice(self, request, deviceId: uuid.UUID):
		device = self.deviceService.validateDevice(
			request, deviceId,
		)
		return DeviceResponse(data=device).json(status=HTTP_200_OK)

	@extend_schema(
		tags=['Device'],
		summary='Deactivate a device',
		description='Deactivate a device by its public ID',
		responses={200: DeviceResponse().response()},
	)
	@PostMapping('/<uuid:deviceId>/deactivate')
	def deactivateDevice(self, request, deviceId: uuid.UUID):
		device = self.deviceService.deactivateDevice(
			deviceId,
		)
		return DeviceResponse(data=device).json(status=HTTP_200_OK)
