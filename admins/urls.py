from vvecon.zorion.urls import paths

from .views import AuthView, DataSetView, HomeView, PatientView, AdvancedFilterView

urlpatterns = paths([
    HomeView, AuthView, DataSetView, PatientView, AdvancedFilterView,
])
