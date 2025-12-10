from vvecon.zorion.urls import paths

from .views import V1Media, V1Place

urlpatterns = paths([V1Media, V1Place])
