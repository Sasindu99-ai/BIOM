import os

from ..enums import EnvMode

__all__ = ['Env']


class Env:
	def __init__(self, mode: EnvMode, **kwargs):
		self.mode = mode
		self.debug = mode == EnvMode.DEBUG

		self.__dict__.update(kwargs)

	def set(self, key: str, value):
		setattr(self, key, value)
		os.environ.setdefault(key, value)

	def get(self, key: str):
		return getattr(self, key)

	def init(self):
		for key, value in self.__dict__.items():
			if isinstance(value, str):
				os.environ.setdefault(key, value)
			elif isinstance(value, bool):
				os.environ.setdefault(key, str(value).lower())
			else:
				os.environ.setdefault(key, str(value))
