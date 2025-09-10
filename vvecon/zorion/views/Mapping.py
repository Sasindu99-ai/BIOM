from functools import wraps

from vvecon.zorion.enums import Method

__all__ = ['DeleteMapping', 'GetMapping', 'Mapping', 'PostMapping', 'PutMapping']


def GetMapping(path: str = ''):

    def decorator(func):

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        wrapper.method = Method.GET
        wrapper.path = path
        return wrapper

    return decorator


def PostMapping(path: str = ''):

    def decorator(func):

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        wrapper.method = Method.POST
        wrapper.path = path
        return wrapper

    return decorator


def PutMapping(path: str = ''):

    def decorator(func):

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        wrapper.method = Method.PUT
        wrapper.path = path
        return wrapper

    return decorator


def DeleteMapping(path: str = ''):

    def decorator(func):

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        wrapper.method = Method.DELETE
        wrapper.path = path
        return wrapper

    return decorator


def Mapping(path: str = ''):

    def decorator(cls):
        cls.base = path
        return cls

    return decorator
