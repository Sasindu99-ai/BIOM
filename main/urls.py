from vvecon.zorion.urls import paths

from .views import AuthView, HomeView

urlpatterns = paths([
    HomeView, AuthView,
])
