from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("show_themes", views.ShowThemeViewSet)
router.register("astronomy_shows", views.AstronomyShowViewSet)
router.register("planetarium_domes", views.PlanetariumDomeViewSet)
router.register("show_sessions", views.ShowSessionViewSet)
router.register("reservations", views.ReservationViewSet)
router.register("tickets", views.TicketViewSet)


urlpatterns = [
    path("", include(router.urls)),
    path(
        "astronomy_shows/<int:pk>/upload-image/",
        views.AstronomyShowViewSet.as_view({"post": "upload_image"}),
        name="astronomyshow-upload-image",
    ),
]

app_name = "planetarium"
