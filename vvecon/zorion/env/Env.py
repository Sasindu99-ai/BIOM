import os
from dotenv import load_dotenv

from ..enums import EnvMode

__all__ = ['Env']


class Env:
	def __init__(self, mode: EnvMode, envPath: str | None = None, **kwargs):
		self.mode = mode
		self.envPath = envPath
		self.debug = mode == EnvMode.DEBUG

		# Load .env file from the path env
		if envPath:
			load_dotenv(envPath)

		self.__dict__.update(kwargs)

	def set(self, key: str, value):
		setattr(self, key, value)
		os.environ[key] = value

	def get(self, key: str):
		return getattr(self, key)

	def init(self):
		os.environ.setdefault('DEBUG', str(self.debug))
		for key, value in self.__dict__.items():
			if isinstance(value, str):
				os.environ.setdefault(key, value)
			elif isinstance(value, bool):
				os.environ.setdefault(key, str(value).lower())
			else:
				os.environ.setdefault(key, str(value))
