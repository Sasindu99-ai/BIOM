from django.core.exceptions import ObjectDoesNotExist, SynchronousOnlyOperation
from django.db.utils import OperationalError
from icecream import ic
from rest_framework.exceptions import NotFound

from vvecon.zorion.core import Service

from ..models import Setting

__all__ = ['SettingService']


class SettingService(Service):
	model = Setting

	def getByKey(self, key: str, tag: str = '', default=NotImplemented):
		try:
			setting: Setting = self.model.objects.filter(key=key, tag=tag).first()
			if setting is None and default is NotImplemented:
				raise KeyError(f"Setting with key '{key}' not found")
			if setting is None:
				return default
			return setting.getValue()
		except (
			ObjectDoesNotExist,
			NotFound,
			OperationalError,
			SynchronousOnlyOperation,
		) as e:
			ic(e)
			if default is NotImplemented:
				raise KeyError(f"Setting with key '{key}' not found") from e
			return default

	async def getAsyncByKey(self, key: str, tag: str = '', default=NotImplemented):
		try:
			setting: Setting = await self.model.objects.filter(key=key, tag=tag).first()
			if setting is None and default is NotImplemented:
				raise KeyError(f"Setting with key '{key}' not found")
			if setting is None:
				return default
			return setting.getValue()
		except (
			ObjectDoesNotExist,
			NotFound,
			OperationalError,
			SynchronousOnlyOperation,
		) as e:
			ic(e)
			if default is NotImplemented:
				keyNotExistErrorMsg = f"Setting with key '{key}' not found"
				raise KeyError(keyNotExistErrorMsg) from e
			return default
