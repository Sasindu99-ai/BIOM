import enum

__all__ = ['EnvMode']


class EnvMode(enum.Enum):
	DEBUG = 'Debug'
	RELEASE = 'Release'
