from vvecon.zorion.urls import paths

from .views import AuthView, HomeView, V1Patient

urlpatterns = paths([
    HomeView, AuthView, V1Patient
])
