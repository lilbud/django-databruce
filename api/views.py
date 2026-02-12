import datetime

from django.contrib.auth import get_user_model
from django.contrib.postgres.expressions import ArraySubquery
from django.db.models import (
    Exists,
    F,
    OuterRef,
    PositiveIntegerField,
    Prefetch,
    Subquery,
)
from django.db.models.functions import JSONObject
from django_filters.rest_framework import DjangoFilterBackend
from querystring_parser import parser
from rest_framework import permissions, viewsets
from rest_framework.decorators import action

from api import filters, serializers
from databruce import models

UserModel = get_user_model()
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
    filterset_class = filters.ArchiveFilter


class OnstageBandViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    def get_queryset(self):
        return (
            models.OnstageBandMembers.objects.all()
            .select_related(
                "relation",
                "band",
                "first",
                "last",
            )
            .order_by("count")
        )

    serializer_class = serializers.OnstageBandSerializer
    filterset_class = filters.OnstageBandFilter


class BandViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.Bands.objects.all()
        .order_by("name")
        .prefetch_related("first_event", "last_event")
    )

    serializer_class = serializers.BandsSerializer
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
        .select_related("first_event", "last_event", "country")
        .prefetch_related("state")
    )

    serializer_class = serializers.CitiesSerializer
    filterset_class = filters.CitiesFilter


class SongsPageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    setlist = models.Setlists.objects.filter(
        set_name=OuterRef("set_name"),
        event__id=OuterRef("event__id"),
    ).select_related("song", "event")

    queryset = (
        models.Setlists.objects.select_related(
            "event",
            "song",
            "event__tour",
            "event__artist",
            "event__venue",
            "event__venue__city",
        )
        .prefetch_related(
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
        .order_by("event__event_id", F("song_num").asc(nulls_first=True))
    )

    serializer_class = serializers.SongsPageSerializer
    filterset_class = filters.SongsPageFilter


class ContinentsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Continents.objects.all()
    serializer_class = serializers.ContinentsSerializer
    filterset_fields = ["name"]
    ordering = ["name", "num_events"]


class CountriesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.Countries.objects.all()
        .order_by("name")
        .annotate(
            count=SubqueryCount(
                models.Events.objects.filter(venue__city__country__id=OuterRef("pk")),
            ),
        )
        .select_related("first_event", "last_event")
    )

    serializer_class = serializers.CountriesSerializer
    filterset_class = filters.CountryFilter


class CoversViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Covers.objects.all()
    serializer_class = serializers.CoversSerializer

    filterset_class = filters.CoversFilter
    ordering = ["event"]


class VenuesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    events = models.Events.objects.filter(venue=OuterRef("id"))

    queryset = (
        models.Venues.objects.all()
        .select_related(
            "first_event",
            "last_event",
            "city",
        )
        .prefetch_related("city__state", "city__country")
        .order_by("name")
    )

    serializer_class = serializers.VenuesSerializer
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
                "venue__first_event",
                "venue__last_event",
            )
            .prefetch_related(
                "run",
            )
            .order_by("-event_id")
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
    filterset_class = filters.IndexFilter


class EventCalendar(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return (
            models.Events.objects.all()
            .select_related(
                "venue",
                "artist",
                "tour",
                "venue__first_event",
                "venue__last_event",
                "venue__city",
                "venue__city__country",
            )
            .prefetch_related(
                "run",
                "venue__city__state",
            )
            .order_by("event_id")
        )

    serializer_class = serializers.EventCalendar
    filterset_class = filters.EventsFilter


class AdvancedEventSearch(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        onstage_qs = models.Onstage.objects.select_related("relation").prefetch_related(
            "band",
        )

        return (
            models.Events.objects.all()
            .select_related(
                "venue",
                "artist",
                "tour",
                "venue__city",
                "venue__city__country",
            )
            .prefetch_related(
                "run",
                "venue__city__state",
                "leg",
                Prefetch("onstage", queryset=onstage_qs),
            )
        ).order_by("event_id")

    serializer_class = serializers.EventsSerializer
    filterset_class = filters.EventsFilter
    ordering = ["event_id"]  # Default ordering


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    def get_queryset(self):
        params = parser.parse(self.request.GET.urlencode())

        onstage_qs = models.Onstage.objects.select_related("relation").prefetch_related(
            "band",
        )

        queryset = (
            models.Events.objects.all()
            .select_related(
                "venue",
                "artist",
                "tour",
                "venue__city",
                "venue__city__country",
            )
            .prefetch_related(
                "run",
                "venue__city__state",
                "leg",
                Prefetch("onstage", queryset=onstage_qs),
            )
        ).order_by("event_id")

        try:
            if params["recent"]:
                queryset = queryset.order_by("-event_id")
        except KeyError:
            pass

        return queryset

    serializer_class = serializers.EventsSerializer
    filterset_class = filters.EventsFilter
    ordering = ["event_id"]  # Default ordering


class AdvancedSearch(viewsets.ReadOnlyModelViewSet):
    queryset = (
        models.Events.objects.all()
        .select_related(
            "venue",
            "artist",
            "tour",
            "venue__city",
        )
        .order_by("event_id")
    )

    serializer_class = serializers.EventsSerializer
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
        )
        .prefetch_related(
            "event__venue__city__state",
            "event__venue__city__country",
        )
    ).order_by("-date")

    serializer_class = serializers.NugsSerializer
    filter_backends = [filters.DataTablesFilterBackend]


class RelationsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    rel_aliases = models.RelationAliases.objects.filter(relation=OuterRef("id"))
    onstage = models.Onstage.objects.select_related("relation").filter(
        relation=OuterRef("id"),
    )

    queryset = (
        models.Relations.objects.all()
        .order_by("name")
        .select_related("first_event", "last_event")
        .annotate(
            count=SubqueryCount(
                onstage.filter(
                    relation__id=OuterRef("id"),
                ),
            ),
            aliases=ArraySubquery(
                rel_aliases.filter(
                    type="alias",
                ).values("name"),
            ),
            nicknames=ArraySubquery(
                rel_aliases.filter(
                    type="nickname",
                ).values("name"),
            ),
        )
    )

    serializer_class = serializers.RelationsSerializer
    filterset_class = filters.RelationFilter


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

    filterset_class = filters.OnstageFilter


class ReleaseTracksViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.ReleaseTracks.objects.all()
        .order_by("discnum", "track")
        .select_related("song", "release")
        .prefetch_related("event", "discid")
    )

    serializer_class = serializers.ReleaseTracksSerializer
    filterset_class = filters.ReleaseTracksFilter


class ReleasesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Releases.objects.all().order_by("-date")
    serializer_class = serializers.ReleasesSerializer
    filterset_class = filters.ReleaseFilter


class SetlistViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.Setlists.objects.all()
        .select_related(
            "event",
            "song",
        )
        .prefetch_related("ltp")
        .order_by("event", F("song_num").asc(nulls_first=True))
    )

    serializer_class = serializers.SetlistSerializer
    filterset_class = filters.SetlistFilter


class SetlistEntriesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        models.SetlistEntries.objects.all()
        .select_related("event")
        .order_by("event")
        .prefetch_related(
            "event__venue",
            "event__venue__city",
            "event__venue__city__state",
            "event__venue__city__country",
            "event__tour",
            "event__leg",
            "event__run",
            "show_opener",
            "s1_closer",
            "s2_opener",
            "main_closer",
            "encore_opener",
            "show_closer",
        )
    )

    serializer_class = serializers.SetlistEntrySerializer
    filterset_class = filters.SetlistEntryFilter


class SnippetViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Snippets.objects.all().select_related(
        "snippet",
        "setlist",
        "setlist__song",
    )

    serializer_class = serializers.SnippetSerializer
    filterset_class = filters.SnippetFilter


class StatesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.States.objects.all()
        .annotate(
            count=SubqueryCount(
                models.Events.objects.filter(venue__city__state__id=OuterRef("pk")),
            ),
        )
        .prefetch_related("first_event", "last_event", "country")
        .order_by("name")
    )

    serializer_class = serializers.StatesSerializer
    filterset_class = filters.StateFilter


class SongsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.Songs.objects.all()
        .prefetch_related(
            "first_event",
            "last_event",
        )
        .annotate(
            has_lyrics=Exists(
                Subquery(models.Lyrics.objects.filter(song=OuterRef("id"))),
            ),
        )
    )

    serializer_class = serializers.SongsSerializer
    filterset_class = filters.SongsFilter


class ToursViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.Tours.objects.all()
        .select_related(
            "first_event",
            "last_event",
            "band",
            "first_event__artist",
            "first_event__tour",
            "last_event__artist",
            "last_event__tour",
        )
        .order_by("-last_event__event_id")
    )

    serializer_class = serializers.ToursSerializer
    filterset_class = filters.TourFilter


class TourLegsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.TourLegs.objects.all()
        .select_related(
            "tour",
            "first_event",
            "last_event",
            "first_event__artist",
            "first_event__tour",
            "last_event__artist",
            "last_event__tour",
        )
        .order_by("-last_event__event_id")
    )

    serializer_class = serializers.TourLegsSerializer
    filterset_class = filters.TourLegFilter


class EventRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        models.Runs.objects.all()
        .select_related(
            "venue",
            "band",
            "first_event",
            "last_event",
            "venue__city",
        )
        .prefetch_related(
            "venue__city__state",
            "venue__city__country",
        )
        .order_by("first_event__event_id")
    )

    serializer_class = serializers.EventRunSerializer
    filterset_class = filters.EventRunFilter


class LyricsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Lyrics.objects.all().select_related("song").order_by("song__name")
    serializer_class = serializers.LyricsSerializer


class EventSetlist(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return (
            models.Setlists.objects.all()
            .select_related("song", "event", "tour_stats_link")
            .prefetch_related("ltp")
            .order_by("event", F("song_num").asc(nulls_first=True))
        )

    serializer_class = serializers.SetlistSerializer
    filterset_class = filters.SetlistFilter


class SetlistNotesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        models.SetlistNotes.objects.all()
        .select_related(
            "setlist",
            "setlist__song",
            "event",
            "event__venue",
            "event__venue__city",
        )
        .prefetch_related(
            "event__venue__city__state",
            "event__venue__city__country",
        )
    )

    serializer_class = serializers.SetlistNotesSerializer
    filterset_class = filters.SetlistNoteFilter


class UpdatesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Updates.objects.all().order_by("-created_at")
    serializer_class = serializers.UpdatesSerializer


class UsersViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserModel.objects.all()
    serializer_class = serializers.UsersSerializer


class UsersAttendedShowsViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return (
            models.UserAttendedShows.objects.all()
            .select_related(
                "user",
                "event",
                "event__venue",
                "event__artist",
                "event__tour",
                "event__venue__city",
            )
            .prefetch_related(
                "event__venue__city__state",
                "event__venue__city__country",
            )
        )

    serializer_class = serializers.UserAttendedShowsSerializer
    filterset_class = filters.UserAttendedShowsFilter
