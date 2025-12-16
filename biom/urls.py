from vvecon.zorion.urls import paths

from .views import V1Study

__all__ = ['urlpatterns']

urlpatterns = paths([
	V1Study,
])
