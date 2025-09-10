from django.urls import include as django_include
from django.urls import path as django_path

from vvecon.zorion.views import API, View

__all__ = ['django_include', 'django_path', 'include', 'path', 'paths']


def path(view: type[View] | type[API], app_name: str = NotImplemented) -> list:
    return view().generateURLPatterns(app_name=app_name)


def paths(views: list[type[View] | type[API]], app_name: str = NotImplemented) -> list:
    urlpatterns = []
    for view in views:
        urlpatterns += view().generateURLPatterns(app_name=app_name)
    return urlpatterns


def include(appUrls: str) -> list:
    return django_path('', django_include(appUrls))
