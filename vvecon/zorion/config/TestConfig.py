from dataclasses import dataclass

__all__ = ['TestConfig']


@dataclass
class TestConfig:
    refreshUrl: str
    authUrl: str
    credentials: dict
