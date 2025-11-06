import json

from django.contrib.postgres.expressions import ArraySubquery
from django.core.exceptions import FieldError
from django.db.models import (
    Case,
    CharField,
    Count,
    ExpressionWrapper,
    F,
    IntegerField,
    Max,
    Min,
    OuterRef,
    PositiveIntegerField,
    Q,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Coalesce, JSONObject, TruncYear
from django_filters.rest_framework import DjangoFilterBackend
from querystring_parser import parser
from rest_framework import filters as dj_filters
from rest_framework import permissions, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework_datatables.django_filters.backends import DatatablesFilterBackend

from api import filters, serializers
from databruce import models

permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ArchiveViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.ArchiveLinks.objects.all()
    serializer_class = serializers.ArchiveLinksSerializer
    permission_classes = permission_classes
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.ArchiveFilter
    ordering = ["created_at", "event"]


class BandViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Bands.objects.all().order_by("name")
    serializer_class = serializers.BandsSerializer
    permission_classes = permission_classes
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["name"]
    ordering = ["name"]


class BootlegViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Bootlegs.objects.all()
    serializer_class = serializers.BootlegsSerializer
    permission_classes = permission_classes
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = filters.BootlegFilter
    ordering = ["event", "title"]


class CitiesViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Cities.objects.all().order_by("name")
    serializer_class = serializers.CitiesSerializer
    permission_classes = permission_classes
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.CitiesFilter
    ordering = ["name", "first", "last"]


class SongsPageViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    def get_queryset(self):
        filter = Q()
        query_params = parser.parse(self.request.GET.urlencode())

        song = query_params.get("song")

        setlist = models.Setlists.objects.filter(
            set_name=OuterRef("set_name"),
            event__id=OuterRef("event__id"),
        ).select_related("song")

        qs = (
            models.Setlists.objects.select_related(
                "event",
                "song",
                "event__tour",
                "event__artist",
                "event__venue",
            )
            .prefetch_related("song__first", "song__last")
            .filter(
                song=song,
            )
            .annotate(
                venue=Subquery(
                    models.VenuesText.objects.filter(
                        id=OuterRef("event__venue"),
                    ).values(json=JSONObject(id="id", name="formatted")),
                ),
                prev_song=Subquery(
                    setlist.filter(song_num__lt=OuterRef("song_num"))
                    .order_by("-song_num", "-event")
                    .values(json=JSONObject(id="song__id", name="song__name"))[:1],
                ),
                next_song=Subquery(
                    setlist.filter(song_num__gt=OuterRef("song_num"))
                    .order_by("event", "song_num")
                    .values(json=JSONObject(id="song__id", name="song__name"))[:1],
                ),
            )
            .order_by("event", "song_num")
        )

        # ordering
        try:
            order_params = filters.order_queryset(query_params["order"])
            qs = qs.order_by(*order_params)
        except KeyError:
            qs = qs.order_by("event", "song_num")

        try:  # noqa: SIM105
            # searching
            filter.add(
                filters.search_queryset(
                    query_params["columns"],
                    query_params["search"]["value"],
                ),
                Q.AND,
            )
        except KeyError:
            pass

        # searchbuilder
        filter.add(
            filters.queryset_sb_filter(query_params),
            Q.AND,
        )

        return qs.filter(filter)

    serializer_class = serializers.SongsPageSerializer


class ContinentsViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Continents.objects.all()
    serializer_class = serializers.ContinentsSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    permission_classes = permission_classes
    filterset_fields = ["name"]
    ordering = ["name", "num_events"]


class CountriesViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Countries.objects.all().order_by("name")
    serializer_class = serializers.CountriesSerializer
    permission_classes = permission_classes
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["name"]
    ordering = ["name", "num_events"]


class CoversViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Covers.objects.all()
    serializer_class = serializers.CoversSerializer
    permission_classes = permission_classes
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.CoversFilter
    ordering = ["event"]


class VenuesTextViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.VenuesText.objects.all()
    serializer_class = serializers.VenuesTextSerializer
    permission_classes = permission_classes
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering = ["formatted"]


class VenuesViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Venues.objects.all()
    serializer_class = serializers.VenuesSerializer
    permission_classes = permission_classes
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.VenuesFilter
    ordering = ["name", "first", "last"]


class EventViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    def get_queryset(self):
        filter = Q()
        query_params = parser.parse(self.request.GET.urlencode())

        event = query_params.get("year")

        qs = (
            models.Events.objects.annotate(
                setlist=Case(
                    When(
                        setlist_certainty__in=["Probable", "Confirmed"],
                        then=F("setlist_certainty"),
                    ),
                    default=None,
                ),
            )
            .filter(id__startswith=event)
            .select_related("venue", "artist", "tour")
        )

        # ordering
        try:
            order_params = filters.order_queryset(query_params["order"])
            qs = qs.order_by(*order_params)
        except KeyError:
            qs = qs.order_by("id")

        try:  # noqa: SIM105
            # searching
            filter.add(
                filters.search_queryset(
                    query_params["columns"],
                    query_params["search"]["value"],
                ),
                Q.AND,
            )
        except KeyError:
            pass

        # searchbuilder
        filter.add(
            filters.queryset_sb_filter(query_params),
            Q.AND,
        )

        # for item in dict(query_params["columns"]):
        #     column = query_params["columns"][item]

        #     if column["search"]["value"] != "":
        #         filter.add(
        #             Q(**{f"{column['name']}__regex": column["search"]["value"]}),
        #             Q.AND,
        #         )

        #     if query_params["search"]["value"] != "":
        #         filter.add(
        #             Q(
        #                 **{
        #                     f"{column['name']}__icontains": query_params["search"][
        #                         "value"
        #                     ],
        #                 },
        #             ),
        #             Q.OR,
        #         )

        # try:
        #     criteria = query_params["searchBuilder"]["criteria"]
        #     filter.add(
        #         filters.queryset_sb_filter(query_params, criteria, filter),
        #         Q.AND,
        #     )
        # except KeyError:
        #     pass

        return qs.filter(filter)

    serializer_class = serializers.EventsSerializer


class NugsViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.NugsReleases.objects.all()
    serializer_class = serializers.NugsSerializer
    permission_classes = permission_classes


class RelationsViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Relations.objects.all()
    serializer_class = serializers.RelationsSerializer
    permission_classes = permission_classes
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    search_fields = ["name", "aliases"]
    ordering_fields = ["name"]


class OnstageBandViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Onstage.objects.distinct("event").order_by("event")

    serializer_class = serializers.OnstageSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["event", "relation", "band"]
    search_fields = ["event", "relation", "band"]
    ordering_fields = ["id"]
    permission_classes = permission_classes


class OnstageViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Onstage.objects.all()
    serializer_class = serializers.OnstageSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.OnstageFilter
    ordering_fields = ["id", "event"]
    permission_classes = permission_classes


class ReleaseTracksViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.ReleaseTracks.objects.all().order_by("track")
    serializer_class = serializers.ReleaseTracksSerializer
    permission_classes = permission_classes
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.ReleaseTracksFilter
    ordering_fields = ["id", "event"]


class ReleasesViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Releases.objects.all()
    serializer_class = serializers.ReleasesSerializer
    permission_classes = permission_classes
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.ReleaseFilter


class SetlistViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Setlists.objects.all()
    serializer_class = serializers.SetlistSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    permission_classes = permission_classes
    filterset_fields = ["song", "event"]


class SnippetViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    def get_queryset(self):
        filter = Q()
        query_params = parser.parse(self.request.GET.urlencode())

        song = query_params.get("song")

        qs = (
            models.Snippets.objects.filter(snippet=song)
            .select_related("snippet")
            .order_by("setlist__event")
        )

        # ordering
        try:
            order_params = filters.order_queryset(query_params["order"])
            qs = qs.order_by(*order_params)
        except KeyError:
            qs = qs.order_by("setlist__event")

        try:  # noqa: SIM105
            # searching
            filter.add(
                filters.search_queryset(
                    query_params["columns"],
                    query_params["search"]["value"],
                ),
                Q.AND,
            )
        except KeyError:
            pass

        # searchbuilder
        filter.add(
            filters.queryset_sb_filter(query_params),
            Q.AND,
        )

        return qs.filter(filter)

    serializer_class = serializers.SnippetSerializer


class StatesViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.States.objects.all()
    serializer_class = serializers.StatesSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.StateFilter
    permission_classes = permission_classes


class SongsViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    def get_queryset(self):
        filter = Q()
        query_params = parser.parse(self.request.GET.urlencode())

        qs = (
            models.Songs.objects.all()
            .order_by("name")
            .prefetch_related(
                "first",
                "last",
                "first__artist",
                "first__tour",
                "last__artist",
                "last__tour",
            )
        )

        # ordering
        try:
            order_params = filters.order_queryset(query_params["order"])
            qs = qs.order_by(*order_params)
        except KeyError:
            qs = qs.order_by("name")

        try:  # noqa: SIM105
            # searching
            filter.add(
                filters.search_queryset(
                    query_params,
                    query_params["search"]["value"],
                ),
                Q.AND,
            )
        except KeyError:
            pass

        # searchbuilder
        filter.add(
            filters.queryset_sb_filter(query_params),
            Q.AND,
        )

        return qs.filter(filter)

    serializer_class = serializers.SongsSerializer


class ToursViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    def get_queryset(self):
        filter = Q()
        query_params = parser.parse(self.request.GET.urlencode())

        qs = (
            models.Tours.objects.all()
            .select_related(
                "first",
                "last",
                "band",
                "first__artist",
                "first__tour",
                "last__artist",
                "last__tour",
            )
            .order_by("-last")
        )

        # ordering
        try:
            order_params = filters.order_queryset(query_params["order"])
            qs = qs.order_by(*order_params)
        except KeyError:
            qs = qs.order_by("id")

        try:  # noqa: SIM105
            # searching
            filter.add(
                filters.search_queryset(
                    query_params,
                    query_params["search"]["value"],
                ),
                Q.AND,
            )
        except KeyError:
            pass

        # searchbuilder
        filter.add(
            filters.queryset_sb_filter(query_params),
            Q.AND,
        )

        return qs.filter(filter)

    serializer_class = serializers.ToursSerializer


class TourLegsViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.TourLegs.objects.all()
    serializer_class = serializers.TourLegsSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.TourLegFilter
    permission_classes = permission_classes


class EventRunViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        filter = Q()
        query_params = parser.parse(self.request.GET.urlencode())

        qs = (
            models.Runs.objects.all()
            .select_related(
                "band",
                "venue",
                "first__venue",
                "first__tour",
                "first__artist",
                "first",
                "last",
                "last__venue",
                "last__tour",
                "last__artist",
            )
            .order_by("first")
        )

        # ordering
        try:
            order_params = filters.order_queryset(query_params["order"])
            qs = qs.order_by(*order_params)
        except KeyError:
            qs = qs.order_by("id")

        try:  # noqa: SIM105
            # searching
            filter.add(
                filters.search_queryset(
                    query_params,
                    query_params["search"]["value"],
                ),
                Q.AND,
            )
        except KeyError:
            pass

        # searchbuilder
        filter.add(
            filters.queryset_sb_filter(query_params),
            Q.AND,
        )

        return qs.filter(filter)

    serializer_class = serializers.EventRunSerializer
