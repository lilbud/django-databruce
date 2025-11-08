import json

from django.contrib.postgres.expressions import ArraySubquery
from django.core.exceptions import FieldError
from django.db.models import (
    Case,
    Count,
    F,
    OuterRef,
    PositiveIntegerField,
    Q,
    Subquery,
    When,
)
from django.db.models.functions import JSONObject
from django_filters.rest_framework import DjangoFilterBackend
from querystring_parser import parser
from rest_framework import permissions, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from api import filters, serializers
from databruce import models

permission_classes = [permissions.IsAuthenticatedOrReadOnly]

VALID_SET_NAMES = [
    "Show",
    "Set 1",
    "Set 2",
    "Encore",
    "Pre-Show",
    "Post-Show",
]


class ArchiveViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.ArchiveLinks.objects.all()
    serializer_class = serializers.ArchiveLinksSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.ArchiveFilter
    ordering = ["created_at", "event"]


class BandViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Bands.objects.all().order_by("name")
    serializer_class = serializers.BandsSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["name"]
    ordering = ["name"]


class BootlegViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Bootlegs.objects.all()
    serializer_class = serializers.BootlegsSerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = filters.BootlegFilter
    ordering = ["event", "title"]


class CitiesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Cities.objects.all().order_by("name")
    serializer_class = serializers.CitiesSerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.CitiesFilter
    ordering = ["name", "first", "last"]


class SongsPageViewSet(viewsets.ReadOnlyModelViewSet):
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
                "song__first",
                "song__last",
                "event__venue__first",
                "event__venue__last",
                "event__venue__state",
                "event__venue__country",
            )
            .prefetch_related(
                "event__venue__city",
                "event__venue__city__state",
                "event__venue__city__country",
            )
            .filter(
                song=song,
            )
            .annotate(
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

        try:
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

    serializer_class = serializers.SongsPageSerializer


class ContinentsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Continents.objects.all()
    serializer_class = serializers.ContinentsSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]

    filterset_fields = ["name"]
    ordering = ["name", "num_events"]


class CountriesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Countries.objects.all().order_by("name")
    serializer_class = serializers.CountriesSerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["name"]
    ordering = ["name", "num_events"]


class CoversViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Covers.objects.all()
    serializer_class = serializers.CoversSerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.CoversFilter
    ordering = ["event"]


class VenuesTextViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    def get_queryset(self):
        query_params = parser.parse(self.request.GET.urlencode())
        venue = query_params.get("id")

        qs = (
            models.Venues.objects.all()
            .select_related("city", "country", "first", "last")
            .prefetch_related("state")
        )

        if venue:
            qs = qs.filter(id=venue)

        return qs

    serializer_class = serializers.VenuesSerializer


class VenuesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Venues.objects.all()
    serializer_class = serializers.VenuesSerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.VenuesFilter
    ordering = ["name", "first", "last"]


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    def get_queryset(self):
        filter = Q()
        event_filter = Q()
        query_params = parser.parse(self.request.GET.urlencode())

        year = query_params.get("year")
        run = query_params.get("run")
        tour = query_params.get("tour")
        leg = query_params.get("tour_leg")

        if year:
            event_filter = Q(id__startswith=year)

        if run:
            event_filter = Q(run=run)

        if tour:
            event_filter = Q(tour=tour)

        if leg:
            event_filter = Q(leg=leg)

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
            .filter(event_filter)
            .select_related(
                "venue",
                "artist",
                "tour",
                "venue__first",
                "venue__last",
                "venue__state",
                "venue__country",
            )
            .prefetch_related(
                "venue__city",
                "venue__city__state",
                "venue__city__country",
            )
            .order_by("id")
        )

        # ordering
        try:
            order_params = filters.order_queryset(query_params["order"])
            qs = qs.order_by(*order_params)
        except KeyError:
            pass

        try:
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

    serializer_class = serializers.EventsSerializer


class NugsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.NugsReleases.objects.all()
    serializer_class = serializers.NugsSerializer


class RelationsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Relations.objects.all()
    serializer_class = serializers.RelationsSerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    search_fields = ["name", "aliases"]
    ordering_fields = ["name"]


class OnstageBandViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Onstage.objects.distinct("event").order_by("event")

    serializer_class = serializers.OnstageSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["event", "relation", "band"]
    search_fields = ["event", "relation", "band"]
    ordering_fields = ["id"]


class OnstageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Onstage.objects.all()
    serializer_class = serializers.OnstageSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.OnstageFilter
    ordering_fields = ["id", "event"]


class ReleaseTracksViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.ReleaseTracks.objects.all().order_by("track")
    serializer_class = serializers.ReleaseTracksSerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.ReleaseTracksFilter
    ordering_fields = ["id", "event"]


class ReleasesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Releases.objects.all()
    serializer_class = serializers.ReleasesSerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.ReleaseFilter


class SubqueryCount(Subquery):
    # Custom Count function to just perform simple count on any queryset without grouping.
    # https://stackoverflow.com/a/47371514/1164966
    template = "(SELECT count(*) FROM (%(subquery)s) _count)"
    output_field = PositiveIntegerField()


class SetlistViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    def get_queryset(self):
        filter = Q()
        event_filter = Q()
        query_params = parser.parse(self.request.GET.urlencode())

        song = query_params.get("song")
        event_run = query_params.get("event_run")

        if song:
            event_filter = Q(song=song)

        if event_run:
            event_filter = Q(event__run=event_run)

        qs = models.Setlists.objects.select_related(
            "event",
            "song",
            "song__first",
            "song__last",
        ).filter(event_filter, set_name__in=VALID_SET_NAMES)

        # ordering
        try:
            order_params = filters.order_queryset(query_params["order"])
            qs = qs.order_by(*order_params)
        except KeyError:
            pass

        try:
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

    serializer_class = serializers.SetlistSerializer


class SnippetViewSet(viewsets.ReadOnlyModelViewSet):
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

        try:
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

    serializer_class = serializers.SnippetSerializer


class StatesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.States.objects.all()
    serializer_class = serializers.StatesSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.StateFilter


class SongsViewSet(viewsets.ReadOnlyModelViewSet):
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

        try:
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


class ToursViewSet(viewsets.ReadOnlyModelViewSet):
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
            .order_by("-last__id")
        )

        # ordering
        try:
            order_params = filters.order_queryset(query_params["order"])
            qs = qs.order_by(*order_params)
        except KeyError:
            pass

        try:
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


class TourLegsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    def get_queryset(self):
        filter = Q()
        query_params = parser.parse(self.request.GET.urlencode())

        qs = models.TourLegs.objects.all().select_related(
            "tour",
            "first",
            "last",
            "first__artist",
            "first__tour",
            "last__artist",
            "last__tour",
        )

        # ordering
        try:
            order_params = filters.order_queryset(query_params["order"])
            qs = qs.order_by(*order_params)
        except KeyError:
            qs = qs.order_by("id")

        try:
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

    serializer_class = serializers.TourLegsSerializer
    # filter_backends = [DjangoFilterBackend, OrderingFilter]
    # filterset_class = filters.TourLegFilter
    #


class EventRunViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        filter = Q()
        query_params = parser.parse(self.request.GET.urlencode())

        qs = (
            models.Runs.objects.all()
            .select_related(
                "venue",
                "band",
                "venue__first",
                "venue__last",
                "first",
                "last",
                "venue__state",
                "venue__country",
            )
            .prefetch_related(
                "venue__city",
                "venue__city__state",
                "venue__city__country",
            )
            .order_by("first")
        )

        # ordering
        try:
            order_params = filters.order_queryset(query_params["order"])
            qs = qs.order_by(*order_params)
        except KeyError:
            qs = qs.order_by("id")

        try:
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
