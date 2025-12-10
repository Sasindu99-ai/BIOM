from vvecon.zorion.urls import paths

from .views import (
	AuthView, HomeView, V1Patient, V1DataSet, AboutView, ExploreView, PublicationsView, ToolsView, ApiView, ContactView, TeamView
)

urlpatterns = paths([
    HomeView,
    AuthView,
    V1Patient,
    V1DataSet,
    AboutView,
    ExploreView,
    PublicationsView,
    ToolsView,
    ApiView,
    ContactView,
    TeamView,
])
