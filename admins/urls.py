from vvecon.zorion.urls import paths

from .views import HomeView, AuthView, DataSetView

urlpatterns = paths([
    HomeView, AuthView, DataSetView
])
