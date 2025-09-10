import enum

__all__ = ['Method']


class Method(enum.Enum):
    """Enum for the different methods of the Zorion API."""
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    PATCH = 'PATCH'
    OPTIONS = 'OPTIONS'
    HEAD = 'HEAD'
    TRACE = 'TRACE'
    CONNECT = 'CONNECT'
    ANY = 'ANY'
