from vvecon.zorion.urls import paths

from .views import AdvancedFilterView, AuthView, BioMarkerView, DataSetView, HomeView, PatientView

urlpatterns = paths([
    HomeView, AuthView, DataSetView, PatientView, BioMarkerView, AdvancedFilterView,
])
