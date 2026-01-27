import datetime
import json
import re

import rest_framework
from django.contrib.postgres.expressions import ArraySubquery
from django.core.exceptions import FieldError
from django.db.models import (
    Case,
    Count,
    Exists,
    F,
    Max,
    Min,
    OuterRef,
    PositiveIntegerField,
    Q,
    QuerySet,
    Subquery,
    When,
    Window,
)
from django.db.models.functions import Coalesce, JSONObject, RowNumber
from django.db.models.functions.window import Lag, Lead
from django_filters.rest_framework import DjangoFilterBackend
from querystring_parser import parser
from rest_framework import permissions, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import LimitOffsetPagination

from api import filters, serializers
from databruce import models

from .selectors import get_band_members

permission_classes = [permissions.IsAuthenticatedOrReadOnly]

VALID_SET_NAMES = [
    "Show",
    "Set 1",
    "Set 2",
    "Encore",
    "Pre-Show",
    "Post-Show",
]


class SubqueryCount(Subquery):
    # Custom Count function to just perform simple count on any queryset without grouping.
    # https://stackoverflow.com/a/47371514/1164966
    template = "(SELECT count(*) FROM (%(subquery)s) _count)"
    output_field = PositiveIntegerField()


class ArchiveViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.ArchiveLinks.objects.all()
    serializer_class = serializers.ArchiveLinksSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.ArchiveFilter
    ordering = ["created_at", "event"]


class BandViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.Bands.objects.all()
        .order_by("name")
        .select_related("first", "last")
        .annotate(
            count=SubqueryCount(
                models.Onstage.objects.select_related("event")
                .filter(band=OuterRef("pk"))
                .distinct("event"),
            ),
        )
    )
    serializer_class = serializers.BandsSerializer
    filter_backends = [DjangoFilterBackend, filters.DTFilter]
    filterset_class = filters.BandsFilter


class BootlegViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.Bootlegs.objects.select_related(
            "event",
        )
        .prefetch_related("archive")
        .order_by("event")
    )
    serializer_class = serializers.BootlegsSerializer

    filter_backends = [DjangoFilterBackend, filters.DTFilter]
    filterset_class = filters.BootlegFilter


class CitiesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.Cities.objects.all()
        .order_by("name")
        .annotate(
            count=SubqueryCount(
                models.Events.objects.filter(venue__city__id=OuterRef("pk")),
            ),
        )
        .select_related("first", "last", "country")
        .prefetch_related("state")
    )
    serializer_class = serializers.CitiesSerializer
    filter_backends = [DjangoFilterBackend, filters.DTFilter]
    filterset_class = filters.CitiesFilter


class SongsPageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    setlist = models.Setlists.objects.filter(
        set_name=OuterRef("set_name"),
        event__id=OuterRef("event__id"),
    ).select_related("song")

    queryset = (
        models.Setlists.objects.select_related(
            "event",
            "song",
            "event__tour",
            "event__artist",
            "event__venue",
            "event__venue__first",
            "event__venue__last",
            "event__venue__state",
            "event__venue__country",
        )
        .prefetch_related(
            "song__first",
            "song__last",
            "event__venue__city",
            "event__run",
            "event__venue__city__state",
            "event__venue__city__country",
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

    serializer_class = serializers.SongsPageSerializer
    filter_backends = [DjangoFilterBackend, filters.DTFilter]
    filterset_class = filters.SongsPageFilter


class ContinentsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Continents.objects.all()
    serializer_class = serializers.ContinentsSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]

    filterset_fields = ["name"]
    ordering = ["name", "num_events"]


class CountriesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.Countries.objects.all()
        .order_by("name")
        .annotate(
            count=SubqueryCount(
                models.Events.objects.filter(venue__country__id=OuterRef("pk")),
            ),
        )
        .select_related("first", "last")
    )

    serializer_class = serializers.CountriesSerializer
    filter_backends = [DjangoFilterBackend, filters.DTFilter]
    filterset_class = filters.CountryFilter


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

    events = models.Events.objects.filter(venue=OuterRef("id"))

    queryset = (
        models.Venues.objects.all()
        .select_related(
            "first",
            "last",
            "state",
            "country",
        )
        .prefetch_related("city", "city__state", "city__country")
        .order_by("name")
    )
    serializer_class = serializers.VenuesSerializer

    filter_backends = [DjangoFilterBackend, filters.DTFilter]
    filterset_class = filters.VenuesFilter


class IndexViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        params = parser.parse(self.request.GET.urlencode())

        queryset = (
            models.Events.objects.all()
            .select_related(
                "venue",
                "artist",
                "tour",
                "venue__city",
                "venue__first",
                "venue__last",
                "venue__state",
                "venue__country",
            )
            .prefetch_related(
                "run",
                "venue__city",
                "venue__city__state",
                "venue__city__country",
            )
            .order_by("-id")
        )

        try:
            if params["upcoming"] == "true":
                return queryset.filter(date__gte=datetime.datetime.today().date())
        except KeyError:
            pass

        try:
            if params["recent"]:
                return queryset.filter(date__lte=datetime.datetime.today().date())
        except KeyError:
            pass

        return queryset

    serializer_class = serializers.IndexSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.IndexFilter


class EventCalendar(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        queryset = (
            models.Events.objects.all()
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
                "run",
                "venue__city",
                "venue__city__state",
                "venue__city__country",
            )
            .order_by("id")
        )

        return queryset

    serializer_class = serializers.EventCalendar
    filter_backends = [DjangoFilterBackend, filters.DTFilter]
    filterset_class = filters.EventsFilter


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    def get_queryset(self):
        params = parser.parse(self.request.GET.urlencode())

        queryset = (
            models.Events.objects.all()
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
                "run",
                "venue__city",
                "venue__city__state",
                "venue__city__country",
            )
            .order_by("id")
        )

        try:
            limit = int(params["limit"])
            queryset = queryset[:limit]
        except KeyError:
            pass

        return queryset

    serializer_class = serializers.EventsSerializer
    filter_backends = [DjangoFilterBackend, filters.DTFilter]
    filterset_class = filters.EventsFilter


class AdvancedSearch(viewsets.ReadOnlyModelViewSet):
    queryset = (
        models.Events.objects.all()
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
            "run",
            "venue__city",
            "venue__city__state",
            "venue__city__country",
        )
        .order_by("id")
    )

    serializer_class = serializers.EventsSerializer
    filter_backends = [DjangoFilterBackend, filters.DTFilter]
    filterset_class = filters.EventsFilter


class NugsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.NugsReleases.objects.all()
        .select_related(
            "event",
            "event__tour",
            "event__artist",
            "event__venue",
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
    ).order_by("-date")
    serializer_class = serializers.NugsSerializer
    filter_backends = [filters.DTFilter]


class RelationsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.Relations.objects.all()
        .order_by("name")
        .select_related("first", "last")
        .annotate(
            count=SubqueryCount(
                models.Onstage.objects.select_related("relation").filter(
                    relation__id=OuterRef("id"),
                ),
            ),
        )
    )

    serializer_class = serializers.RelationsSerializer
    filter_backends = [DjangoFilterBackend, filters.DTFilter]
    filterset_class = filters.RelationFilter


def get_event(self, obj):
    result = {"id": obj.id}

    try:
        date = datetime.datetime.strptime(obj.date, "%Y-%m-%d").strftime(
            "%Y-%m-%d",
        )
    except (ValueError, TypeError):
        # no month or day
        if re.search(r"(19|20)\d{2}0{4}-", obj.id):
            date = datetime.datetime.strptime(
                f"{obj.id[0:4]}-01-01",
                "%Y-%m-%d",
            ).strftime(
                "%Y-%m-%d",
            )
        # month, no day
        elif re.search(r"(19|20)\d{2}[0-3]\d00-", obj.id):
            date = datetime.datetime.strptime(
                f"{obj.id[0:4]}-{obj.id[4:6]}-01",
                "%Y-%m-%d",
            ).strftime(
                "%Y-%m-%d",
            )
        else:
            date = datetime.datetime.strptime(obj.id[0:8], "%Y%m%d").strftime(
                "%Y-%m-%d",
            )

    result["filter"] = date
    result["display"] = date

    if obj.early_late:
        result["display"] = f"{date} ({obj.early_late})"

    return result


class OnstageBandViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    def get_queryset(self):
        query_params = parser.parse(self.request.GET.urlencode())
        band = query_params.get("band")

        return (
            models.OnstageBandMembers.objects.filter(band__id=band)
            .select_related(
                "relation",
                "band",
                "first",
                "last",
            )
            .annotate(
                count=SubqueryCount(
                    models.Onstage.objects.filter(
                        relation=OuterRef("relation"),
                        band=OuterRef("band"),
                    ),
                ),
            )
            .order_by("count")
        )

    serializer_class = serializers.OnstageRelationSerializer
    filter_backends = [DjangoFilterBackend, filters.DTFilter]


class OnstageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.Onstage.objects.all()
        .select_related(
            "relation",
            "event",
        )
        .prefetch_related(
            "band",
        )
    ).order_by("event", F("band").asc(nulls_first=True), "relation__name")

    serializer_class = serializers.OnstageSerializer
    filter_backends = [DjangoFilterBackend, filters.DTFilter]
    filterset_class = filters.OnstageFilter


class OnstageEventsViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        q = Q()
        query_params = parser.parse(self.request.GET.urlencode())
        band = query_params.get("band")
        relation = query_params.get("relation")

        qs = (
            models.Onstage.objects.all()
            .select_related("relation", "event")
            .prefetch_related("band")
            .order_by("event")
        )

        if band:
            q.add(Q(band__id=band), Q.AND)
        if relation:
            q.add(Q(relation__id=relation), Q.AND)

        return (
            models.Events.objects.filter(
                id__in=qs.filter(q).values_list("event__id"),
            )
            .select_related(
                "venue",
                "artist",
                "tour",
                "venue__city",
                "venue__country",
                "venue__first",
                "venue__last",
            )
            .prefetch_related(
                "venue__state",
                "run",
                "venue__city__state",
                "venue__city__country",
            )
            .order_by("id")
        )

    serializer_class = serializers.EventsSerializer
    filter_backends = [DjangoFilterBackend, filters.DTFilter]


class ReleaseTracksViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.ReleaseTracks.objects.all()
        .order_by("discnum", "track")
        .select_related("song", "release")
        .prefetch_related("event", "discid")
    )
    serializer_class = serializers.ReleaseTracksSerializer

    filter_backends = [DjangoFilterBackend, filters.DTFilter]
    filterset_class = filters.ReleaseTracksFilter


class ReleasesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Releases.objects.all().order_by("-date")
    serializer_class = serializers.ReleasesSerializer

    filter_backends = [filters.DTFilter]
    filterset_class = filters.ReleaseFilter


class SubqueryCount(Subquery):
    # Custom Count function to just perform simple count on any queryset without grouping.
    # https://stackoverflow.com/a/47371514/1164966
    template = "(SELECT count(*) FROM (%(subquery)s) _count)"
    output_field = PositiveIntegerField()


class SetlistViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    song = models.Songs.objects.filter(id=OuterRef("song__id"))

    queryset = (
        models.Setlists.objects.filter(
            set_name__in=VALID_SET_NAMES,
        )
        .select_related(
            "event",
            "song",
        )
        .prefetch_related("song__first", "song__last")
        .values("song__id")
        .annotate(
            count=Count(F("event__id")),
            songinfo=Subquery(
                song.values(json=JSONObject(id="id", name="name", category="category")),
            ),
        )
        .order_by("-count", "song__name")
    )

    serializer_class = serializers.SetlistFilterSerializer
    filter_backends = [DjangoFilterBackend, filters.DTFilter, OrderingFilter]
    ordering_fields = ["song_num"]
    filterset_class = filters.SetlistFilter


class SetlistEntriesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        models.SetlistEntries.objects.prefetch_related()
        .select_related(
            "event",
            "event__venue",
            "event__artist",
            "event__tour",
            "event__venue__city",
            "event__venue__country",
            "event__venue__first",
            "event__venue__last",
        )
        .prefetch_related(
            "event__venue__state",
            "event__run",
            "event__venue__city__state",
            "event__venue__city__country",
            "show_opener",
            "s1_closer",
            "s2_opener",
            "main_closer",
            "encore_opener",
            "show_closer",
        )
        .order_by("event")
    )

    serializer_class = serializers.SetlistEntrySerializer
    filter_backends = [DjangoFilterBackend, filters.DTFilter]
    filterset_class = filters.SetlistEntryFilter


class SnippetViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.Snippets.objects.all()
        .select_related(
            "snippet",
            "setlist",
            "setlist__song",
            "setlist__event",
            "setlist__event__venue",
            "setlist__event__venue__first",
            "setlist__event__venue__last",
            "setlist__event__venue__state",
            "setlist__event__venue__country",
        )
        .prefetch_related(
            "snippet__first",
            "snippet__last",
            "setlist__event__venue__city",
            "setlist__event__venue__city__state",
            "setlist__event__venue__city__country",
        )
        .order_by("setlist__event")
    )

    serializer_class = serializers.SnippetSerializer
    filter_backends = [DjangoFilterBackend, filters.DTFilter]
    filterset_class = filters.SnippetFilter


class StatesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.States.objects.all()
        .annotate(
            count=SubqueryCount(
                models.Events.objects.filter(venue__state__id=OuterRef("pk")),
            ),
        )
        .select_related("first", "last", "country")
        .order_by("name")
    )
    serializer_class = serializers.StatesSerializer
    filter_backends = [DjangoFilterBackend, filters.DTFilter]
    filterset_class = filters.StateFilter


class SongsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.Songs.objects.all()
        .order_by("name")
        .prefetch_related(
            "first",
            "last",
        )
    )
    serializer_class = serializers.SongsSerializer
    filter_backends = [DjangoFilterBackend, filters.DTFilter]
    filterset_class = filters.SongsFilter


class ToursViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
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

    serializer_class = serializers.ToursSerializer
    filter_backends = [DjangoFilterBackend, filters.DTFilter]
    filterset_class = filters.TourFilter


class TourLegsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.TourLegs.objects.all()
        .select_related(
            "tour",
            "first",
            "last",
            "first__artist",
            "first__tour",
            "last__artist",
            "last__tour",
        )
        .order_by("-last__id")
    )

    serializer_class = serializers.TourLegsSerializer
    filter_backends = [DjangoFilterBackend, filters.DTFilter]
    filterset_class = filters.TourLegFilter


class EventRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
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
    serializer_class = serializers.EventRunSerializer
    filter_backends = [DjangoFilterBackend, filters.DTFilter]
    filterset_class = filters.EventRunFilter


class EventRunDetailViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
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
    serializer_class = serializers.EventRunDetailSerializer
    filter_backends = [DjangoFilterBackend, filters.DTFilter]


class LyricsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Lyrics.objects.all().select_related("song").order_by("song__name")
    serializer_class = serializers.LyricsSerializer
    filter_backends = [DjangoFilterBackend, filters.DTFilter]


class EventSetlist(viewsets.ReadOnlyModelViewSet):
    notes = models.Notes.objects.filter(
        setlist__id=OuterRef("pk"),
    ).select_related("event", "setlist")

    queryset = (
        models.Setlists.objects.all()
        .select_related("song", "event")
        .prefetch_related("ltp")
        .prefetch_related("song__first", "song__last")
        .annotate(
            notes_list=Case(
                When(
                    Exists(ArraySubquery(notes.values("note"))),
                    then=ArraySubquery(notes.values("note")),
                ),
            ),
            t_total=Case(
                When(
                    Q(set_name__in=VALID_SET_NAMES),
                    SubqueryCount(
                        ArraySubquery(
                            models.Setlists.objects.filter(
                                song__id=OuterRef("song"),
                                event__tour__id=OuterRef("event__tour__id"),
                            ),
                        ),
                    ),
                ),
            ),
            t_count=Case(
                When(
                    Q(set_name__in=VALID_SET_NAMES),
                    Window(
                        expression=RowNumber(),
                        partition_by=[F("song__id"), F("event__tour__id")],
                        order_by=[F("event__id").asc(), F("song_num").asc()],
                    ),
                ),
            ),
        )
        .order_by("event", F("song_num").asc(nulls_first=True))
    )
    serializer_class = serializers.SetlistSerializer
    filter_backends = [DjangoFilterBackend, filters.DTFilter]
    filterset_class = filters.SetlistFilter


class SetlistNotesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        models.Notes.objects.all()
        .select_related(
            "setlist",
            "setlist__song",
            "event",
            "event__venue__first",
            "event__venue__last",
            "event__venue__state",
            "event__venue__country",
            "event__tour",
            "event__artist",
        )
        .prefetch_related(
            "event__run",
            "event__leg",
            "event__venue__city",
            "event__venue__city__state",
            "event__venue__city__country",
        )
    )

    serializer_class = serializers.NotesSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.SetlistNoteFilter


class UpdatesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Updates.objects.all().order_by("-created_at")
    serializer_class = serializers.UpdatesSerializer
    filter_backends = [DjangoFilterBackend, filters.DTFilter]
