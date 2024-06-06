from django.urls import path, include
from rest_framework.routers import DefaultRouter

from planetarium.views import AstronomyShowViewSet, PlanetariumDomeViewSet, ShowSessionViewSet, ShowThemeViewSet, \
    ReservationViewSet, TicketViewSet

router = DefaultRouter()
router.register("astronomy_show", AstronomyShowViewSet)
router.register("planetarium_domes", PlanetariumDomeViewSet)
router.register("show_sessions", ShowSessionViewSet)
router.register("show_themes", ShowThemeViewSet)
router.register("reservations", ReservationViewSet)
router.register("tickets", TicketViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
