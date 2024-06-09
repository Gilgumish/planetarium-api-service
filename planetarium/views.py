from datetime import datetime

from django.db.models import F, Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from planetarium.models import ShowTheme, AstronomyShow, PlanetariumDome, ShowSession, Reservation, Ticket
from planetarium.permissions import IsAdminOrIfAuthenticatedReadOnly, IsAdminOrIsOwner
from planetarium.serializers import (
    ShowThemeSerializer,
    AstronomyShowSerializer,
    AstronomyShowListSerializer,
    AstronomyShowDetailSerializer,
    PlanetariumDomeSerializer,
    ShowSessionSerializer,
    ShowSessionListSerializer,
    ShowSessionDetailSerializer,
    ReservationSerializer,
    ReservationListSerializer,
    TicketSerializer,
    TicketListSerializer
)
from planetarium.pagination import StandardResultsSetPagination
from planetarium.ordering import CustomOrderingFilter

class ShowThemeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = ShowTheme.objects.all()
    serializer_class = ShowThemeSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    pagination_class = StandardResultsSetPagination
    filter_backends = [CustomOrderingFilter]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='name', description='Name of the show theme', required=True, type=OpenApiTypes.STR),
        ],
        responses={200: ShowThemeSerializer(many=True)},
        examples=[
            OpenApiExample(
                'Example Theme List',
                value=[
                    {"id": 1, "name": "Solar System"},
                    {"id": 2, "name": "Galaxies"}
                ]
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class AstronomyShowViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = AstronomyShow.objects.prefetch_related("themes")
    serializer_class = AstronomyShowSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    pagination_class = StandardResultsSetPagination
    filter_backends = [CustomOrderingFilter]

    def get_queryset(self):
        title = self.request.query_params.get("title")
        themes = self.request.query_params.get("themes")

        queryset = self.queryset

        if title:
            queryset = queryset.filter(title__icontains=title)

        if themes:
            themes_ids = [int(theme) for theme in themes.split(",")]
            queryset = queryset.filter(themes__id__in=themes_ids)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return AstronomyShowListSerializer

        if self.action == "retrieve":
            return AstronomyShowDetailSerializer

        return AstronomyShowSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "themes",
                type={"type": "list", "items": {"type": "number"}},
                description="Filter by theme id (ex. ?themes=1,2)",
            ),
            OpenApiParameter(
                "title",
                type=OpenApiTypes.STR,
                description="Filter by show title (ex. ?title=galaxy)",
            ),
        ],
        examples=[
            OpenApiExample(
                'Example Show List',
                value=[
                    {"id": 1, "title": "Exploring the Solar System", "themes": ["Solar System"], "image": "path/to/image1.jpg"},
                    {"id": 2, "title": "The Mysteries of Galaxies", "themes": ["Galaxies"], "image": "path/to/image2.jpg"}
                ]
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class PlanetariumDomeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = PlanetariumDome.objects.all()
    serializer_class = PlanetariumDomeSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    pagination_class = StandardResultsSetPagination
    filter_backends = [CustomOrderingFilter]

    @extend_schema(
        responses={200: PlanetariumDomeSerializer(many=True)},
        examples=[
            OpenApiExample(
                'Example Dome List',
                value=[
                    {"id": 1, "name": "Main Dome", "rows": 10, "seats_in_row": 20, "capacity": 200}
                ]
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class ShowSessionViewSet(viewsets.ModelViewSet):
    queryset = (
        ShowSession.objects.all()
        .select_related("astronomy_show", "planetarium_dome")
        .annotate(
            tickets_available=(
                F("planetarium_dome__rows") * F("planetarium_dome__seats_in_row")
                - Count("tickets")
            )
        )
    )
    serializer_class = ShowSessionSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    pagination_class = StandardResultsSetPagination
    filter_backends = [CustomOrderingFilter]

    def get_queryset(self):
        date = self.request.query_params.get("date")
        show_id_str = self.request.query_params.get("show")

        queryset = self.queryset

        if date:
            date = datetime.strptime(date, "%Y-%m-%d").date()
            queryset = queryset.filter(show_time__date=date)

        if show_id_str:
            queryset = queryset.filter(astronomy_show_id=int(show_id_str))

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return ShowSessionListSerializer

        if self.action == "retrieve":
            return ShowSessionDetailSerializer

        return ShowSessionSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "show",
                type=OpenApiTypes.INT,
                description="Filter by show id (ex. ?show=1)",
            ),
            OpenApiParameter(
                "date",
                type=OpenApiTypes.DATE,
                description=(
                    "Filter by datetime of ShowSession "
                    "(ex. ?date=2024-07-01)"
                ),
            ),
        ],
        examples=[
            OpenApiExample(
                'Example Session List',
                value=[
                    {"id": 1, "show_time": "2024-07-01T10:00:00Z", "astronomy_show_title": "Exploring the Solar System", "planetarium_dome_name": "Main Dome", "planetarium_dome_capacity": 200, "tickets_available": 198},
                    {"id": 2, "show_time": "2024-07-01T14:00:00Z", "astronomy_show_title": "The Mysteries of Galaxies", "planetarium_dome_name": "Main Dome", "planetarium_dome_capacity": 200, "tickets_available": 200}
                ]
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class ReservationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    queryset = Reservation.objects.prefetch_related(
        "tickets__show_session__astronomy_show", "tickets__show_session__planetarium_dome"
    )
    serializer_class = ReservationSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = (IsAuthenticated, IsAdminOrIsOwner)
    filter_backends = [CustomOrderingFilter]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Reservation.objects.all()
        return Reservation.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return ReservationListSerializer

        return ReservationSerializer

    @extend_schema(
        responses={200: ReservationListSerializer(many=True)},
        examples=[
            OpenApiExample(
                'Example Reservation List',
                value=[
                    {
                        "id": 1,
                        "tickets": [
                            {
                                "id": 1,
                                "row": 1,
                                "seat": 1,
                                "show_session": {
                                    "id": 1,
                                    "show_time": "2024-07-01T10:00:00Z",
                                    "astronomy_show_title": "Exploring the Solar System",
                                    "planetarium_dome_name": "Main Dome",
                                    "planetarium_dome_capacity": 200,
                                    "tickets_available": 198
                                }
                            },
                            {
                                "id": 2,
                                "row": 1,
                                "seat": 2,
                                "show_session": {
                                    "id": 1,
                                    "show_time": "2024-07-01T10:00:00Z",
                                    "astronomy_show_title": "Exploring the Solar System",
                                    "planetarium_dome_name": "Main Dome",
                                    "planetarium_dome_capacity": 200,
                                    "tickets_available": 198
                                }
                            }
                        ],
                        "created_at": "2024-06-01T10:00:00Z",
                        "user_email": "user@example.com"
                    }
                ]
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        responses={200: ReservationListSerializer()},
        examples=[
            OpenApiExample(
                'Example Reservation Detail',
                value={
                    "id": 1,
                    "tickets": [
                        {
                            "id": 1,
                            "row": 1,
                            "seat": 1,
                            "show_session": {
                                "id": 1,
                                "show_time": "2024-07-01T10:00:00Z",
                                "astronomy_show_title": "Exploring the Solar System",
                                "planetarium_dome_name": "Main Dome",
                                "planetarium_dome_capacity": 200,
                                "tickets_available": 198
                            }
                        },
                        {
                            "id": 2,
                            "row": 1,
                            "seat": 2,
                            "show_session": {
                                "id": 1,
                                "show_time": "2024-07-01T10:00:00Z",
                                "astronomy_show_title": "Exploring the Solar System",
                                "planetarium_dome_name": "Main Dome",
                                "planetarium_dome_capacity": 200,
                                "tickets_available": 198
                            }
                        }
                    ],
                    "created_at": "2024-06-01T10:00:00Z",
                    "user_email": "user@example.com"
                }
            )
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        if self.action == 'list':
            self.permission_classes = [IsAdminOrIsOwner]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @extend_schema(
        request=TicketSerializer,
        responses={201: TicketSerializer},
        examples=[
            OpenApiExample(
                'Example Ticket Create',
                value={
                    "show_session_id": 1,
                    "row": 1,
                    "seat": 1
                },
                request_only=True
            )
        ]
    )
    def create(self, request, *args, **kwargs):
        user = request.user
        reservation, created = Reservation.objects.get_or_create(user=user)
        data = request.data.copy()
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(reservation=reservation)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @extend_schema(
        responses={200: TicketListSerializer(many=True)},
        examples=[
            OpenApiExample(
                'Example Ticket List',
                value=[
                    {
                        "id": 1,
                        "row": 1,
                        "seat": 1,
                        "show_session": {
                            "id": 1,
                            "show_time": "2024-07-01T10:00:00Z",
                            "astronomy_show_title": "Exploring the Solar System",
                            "planetarium_dome_name": "Main Dome",
                            "planetarium_dome_capacity": 200,
                            "tickets_available": 198
                        },
                        "reservation": 1
                    },
                    {
                        "id": 2,
                        "row": 2,
                        "seat": 3,
                        "show_session": {
                            "id": 1,
                            "show_time": "2024-07-01T10:00:00Z",
                            "astronomy_show_title": "Exploring the Solar System",
                            "planetarium_dome_name": "Main Dome",
                            "planetarium_dome_capacity": 200,
                            "tickets_available": 198
                        },
                        "reservation": 1
                    }
                ]
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
