from vvecon.zorion.urls import paths

from .views import (
	AuthView, HomeView, V1Patient, AboutView, ExploreView, PublicationsView, ToolsView, ApiView, ContactView, TeamView
)

urlpatterns = paths([
    HomeView,
    AuthView,
    V1Patient,
    AboutView,
    ExploreView,
    PublicationsView,
    ToolsView,
    ApiView,
    ContactView,
    TeamView,
])
