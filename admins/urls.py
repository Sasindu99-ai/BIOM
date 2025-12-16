from vvecon.zorion.urls import paths

from .views import AuthView, DataSetView, HomeView, PatientView

urlpatterns = paths([
    HomeView, AuthView, DataSetView, PatientView,
])
