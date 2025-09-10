from ..enums import EnvMode
from .Env import Env

__all__ = ['EnvManager']


class EnvManager:
	_env = None

	@classmethod
	def set_env(cls, env: Env):
		cls._env = env

	@classmethod
	def get_env(cls) -> Env:
		if cls._env is None:
			raise ValueError('Environment not set')
		return cls._env

	@classmethod
	def get(cls, key: str):
		return cls.get_env().get(key)

	def __init__(self, envs: dict[EnvMode, Env] | None = None, default=EnvMode.DEBUG):
		if envs is None:
			envs = {
				EnvMode.DEBUG: Env(EnvMode.DEBUG),
				EnvMode.RELEASE: Env(EnvMode.RELEASE),
			}
		self.envs = envs
		self.current_env = self.envs[default]
		self.set_env(self.current_env)

	def current(self) -> Env:
		return self.current_env

	def init(self):
		self.current_env.init()
