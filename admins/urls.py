from vvecon.zorion.urls import paths

from .views import (
	AdvancedFilterView,
	AuthView,
	BioMarkerView,
	CMSView,
	DataSetView,
	HomeView,
	PatientView,
	SettingsView,
)

urlpatterns = paths([
    HomeView, AuthView, DataSetView, PatientView, BioMarkerView, AdvancedFilterView, SettingsView, CMSView,
])

