import tempfile
import os
from datetime import datetime, timezone

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from planetarium.models import (
    ShowTheme,
    AstronomyShow,
    PlanetariumDome,
    ShowSession,
)
from planetarium.serializers import (
    ShowThemeSerializer,
    AstronomyShowListSerializer,
    PlanetariumDomeSerializer,
    ShowSessionListSerializer,
)

SHOW_THEME_URL = reverse("planetarium:showtheme-list")
ASTRONOMY_SHOW_URL = reverse("planetarium:astronomyshow-list")
PLANETARIUM_DOME_URL = reverse("planetarium:planetariumdome-list")
SHOW_SESSION_URL = reverse("planetarium:showsession-list")


def sample_show_theme(name="Sample Theme"):
    ShowTheme.objects.all().delete()
    return ShowTheme.objects.create(name=name)


def sample_astronomy_show(**params):
    defaults = {
        "title": "Sample Show",
        "description": "Sample description",
    }
    defaults.update(params)
    show = AstronomyShow.objects.create(**defaults)
    show.themes.add(sample_show_theme())
    return show


def sample_planetarium_dome(**params):
    defaults = {
        "name": "Main Dome",
        "rows": 10,
        "seats_in_row": 20,
    }
    defaults.update(params)
    return PlanetariumDome.objects.create(**defaults)


def sample_show_session(**params):
    dome = sample_planetarium_dome()
    show = sample_astronomy_show()
    defaults = {
        "show_time": datetime(2024, 7, 1, 10, 0, tzinfo=timezone.utc),
        "astronomy_show": show,
        "planetarium_dome": dome,
    }
    defaults.update(params)
    return ShowSession.objects.create(**defaults)


def image_upload_url(show_id):
    """Return URL for astronomy show image upload"""
    return reverse("planetarium:astronomyshow-upload-image", args=[show_id])


def detail_url(show_id):
    return reverse("planetarium:astronomyshow-detail", args=[show_id])


class UnauthenticatedApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(ASTRONOMY_SHOW_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user("test@test.com", "testpass")
        self.client.force_authenticate(self.user)

    def test_list_astronomy_shows(self):
        sample_astronomy_show()
        sample_astronomy_show(title="Another Show")

        res = self.client.get(ASTRONOMY_SHOW_URL)

        shows = AstronomyShow.objects.order_by("id")
        serializer = AstronomyShowListSerializer(shows, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_list_show_themes(self):
        sample_show_theme()
        sample_show_theme(name="Another Theme")

        res = self.client.get(SHOW_THEME_URL)

        themes = ShowTheme.objects.order_by("id")
        serializer = ShowThemeSerializer(themes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_list_planetarium_domes(self):
        sample_planetarium_dome()
        sample_planetarium_dome(name="Secondary Dome", rows=5, seats_in_row=10)

        res = self.client.get(PLANETARIUM_DOME_URL)

        domes = PlanetariumDome.objects.order_by("id")
        serializer = PlanetariumDomeSerializer(domes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_list_show_sessions(self):
        sample_show_session()
        sample_show_session(show_time=datetime(2024, 7, 1, 14, 0, tzinfo=timezone.utc))

        res = self.client.get(SHOW_SESSION_URL)

        sessions = ShowSession.objects.order_by("id")
        serializer = ShowSessionListSerializer(sessions, many=True)

        for session, serialized_session in zip(res.data["results"], serializer.data):
            self.assertEqual(session["id"], serialized_session["id"])
            self.assertEqual(session["show_time"], serialized_session["show_time"])
            self.assertEqual(session["astronomy_show_title"], serialized_session["astronomy_show_title"])
            self.assertEqual(session["planetarium_dome_name"], serialized_session["planetarium_dome_name"])
            self.assertEqual(session["planetarium_dome_capacity"], serialized_session["planetarium_dome_capacity"])
            if "tickets_available" in session and "tickets_available" in serialized_session:
                self.assertEqual(session["tickets_available"], serialized_session["tickets_available"])


class AdminApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_show_session(self):
        show = sample_astronomy_show()
        dome = sample_planetarium_dome()
        payload = {
            "show_time": "2024-08-01T10:00:00Z",
            "astronomy_show": show.id,
            "planetarium_dome": dome.id,
        }
        res = self.client.post(SHOW_SESSION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        session = ShowSession.objects.get(id=res.data["id"])
