from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from planetarium.models import (
    ShowTheme,
    AstronomyShow,
    PlanetariumDome,
    ShowSession,
    Reservation,
    Ticket,
)


class ShowThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShowTheme
        fields = ("id", "name")


class AstronomyShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = AstronomyShow
        fields = (
            "id",
            "title",
            "description",
            "themes",
            "image",
        )


class AstronomyShowListSerializer(AstronomyShowSerializer):
    themes = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")

    class Meta:
        model = AstronomyShow
        fields = ("id", "title", "themes", "image")


class AstronomyShowDetailSerializer(AstronomyShowSerializer):
    themes = ShowThemeSerializer(many=True, read_only=True)

    class Meta:
        model = AstronomyShow
        fields = (
            "id",
            "title",
            "description",
            "themes",
            "image",
        )


class PlanetariumDomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanetariumDome
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class ShowSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShowSession
        fields = ("id", "show_time", "astronomy_show", "planetarium_dome")


class ShowSessionListSerializer(ShowSessionSerializer):
    astronomy_show_title = serializers.CharField(
        source="astronomy_show.title", read_only=True
    )
    planetarium_dome_name = serializers.CharField(
        source="planetarium_dome.name", read_only=True
    )
    planetarium_dome_capacity = serializers.IntegerField(
        source="planetarium_dome.capacity", read_only=True
    )
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = ShowSession
        fields = (
            "id",
            "show_time",
            "astronomy_show_title",
            "planetarium_dome_name",
            "planetarium_dome_capacity",
            "tickets_available",
        )


class ShowSessionDetailSerializer(serializers.ModelSerializer):
    astronomy_show_title = serializers.CharField(
        source="astronomy_show.title", read_only=True
    )
    planetarium_dome_name = serializers.CharField(
        source="planetarium_dome.name", read_only=True
    )
    planetarium_dome_rows = serializers.IntegerField(
        source="planetarium_dome.rows", read_only=True
    )
    planetarium_dome_seats_in_row = serializers.IntegerField(
        source="planetarium_dome.seats_in_row", read_only=True
    )

    class Meta:
        model = ShowSession
        fields = (
            "id",
            "show_time",
            "astronomy_show_title",
            "planetarium_dome_name",
            "planetarium_dome_rows",
            "planetarium_dome_seats_in_row",
        )


class TicketSerializer(serializers.ModelSerializer):
    show_session = ShowSessionDetailSerializer(read_only=True)
    show_session_id = serializers.PrimaryKeyRelatedField(
        queryset=ShowSession.objects.all(), source="show_session", write_only=True
    )

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "show_session", "show_session_id", "reservation")
        read_only_fields = ("reservation",)

    def create(self, validated_data):
        show_session = validated_data.pop("show_session")
        reservation = validated_data.pop("reservation")
        ticket = Ticket.objects.create(
            show_session=show_session, reservation=reservation, **validated_data
        )
        return ticket


class TicketListSerializer(TicketSerializer):
    show_session = ShowSessionListSerializer(many=False, read_only=True)


class TicketSeatsSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class ReservationSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Reservation
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            reservation = Reservation.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(reservation=reservation, **ticket_data)
            return reservation


class ReservationListSerializer(ReservationSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Reservation
        fields = ("id", "tickets", "created_at", "user_email")
