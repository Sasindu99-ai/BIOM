from vvecon.zorion.urls import paths

from .views import (
	AboutView,
	ApiView,
	AuthView,
	ContactView,
	ExploreView,
	HomeView,
	PublicationsView,
	TeamView,
	ToolsView,
	V1BioMarker,
	V1DataSet,
	V1Kit,
	V1Patient,
)

urlpatterns = paths([
    HomeView,
    AuthView,
    V1Patient,
    V1DataSet,
    V1BioMarker,
    V1Kit,
    AboutView,
    ExploreView,
    PublicationsView,
    ToolsView,
    ApiView,
    ContactView,
    TeamView,
])
