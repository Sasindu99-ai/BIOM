from vvecon.zorion.urls import paths

from .views import HomeView, AuthView, DataSetView, PatientView

urlpatterns = paths([
    HomeView, AuthView, DataSetView, PatientView
])
