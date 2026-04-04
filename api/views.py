import datetime

from django.contrib.auth import get_user_model
from django.contrib.postgres.aggregates import ArrayAgg, JSONBAgg
from django.contrib.postgres.expressions import ArraySubquery
from django.db.models import (
    CharField,
    Count,
    DecimalField,
    Exists,
    ExpressionWrapper,
    F,
    FloatField,
    IntegerField,
    JSONField,
    Max,
    Min,
    OuterRef,
    PositiveIntegerField,
    Prefetch,
    Q,
    StringAgg,
    Subquery,
    Value,
    Window,
)
from django.db.models.functions import Cast, JSONObject, Lower
from django.shortcuts import get_list_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from querystring_parser import parser
from rest_framework import mixins, permissions, response, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

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
    "Rehearsal",
    "Recording",
]
date = datetime.datetime.now(tz=datetime.timezone.utc).date()


class SubqueryCount(Subquery):
    # Custom Count function to just perform simple count on any queryset without grouping.
    # https://stackoverflow.com/a/47371514/1164966
    template = "(SELECT count(*) FROM (%(subquery)s) _count)"
    output_field = PositiveIntegerField()


class ArchiveViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.ArchiveLinks.objects.all().select_related("event")
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
            "event__venue__venues_text",
            "event__venue__city__country",
        )
        .prefetch_related(
            "setlist_notes",
            "setlist_position",
            "songs_page",
            "songs_page__prev",
            "songs_page__next",
            "event__venue__city__state",
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
            "city",
        )
        .prefetch_related("city__state", "city__country", "first_event", "last_event")
        .order_by("name")
    )

    serializer_class = serializers.VenuesSerializer
    filterset_class = filters.VenuesFilter


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
        onstage_qs = models.Onstage.objects.select_related("relation").prefetch_related(
            "band",
        )

        return (
            models.Events.objects.select_related(
                "venue",
                "venue__city",
                "artist",
                "tour",
                "venue__city__country",
                "venue__venues_text",
                "type",
            ).prefetch_related(
                "run",
                "venue__city__state",
                "leg",
                Prefetch("onstage", queryset=onstage_qs),
                "user_event",
            )
        ).order_by("event_id")

    serializer_class = serializers.EventsSerializer
    filterset_class = filters.EventsFilter
    ordering_fields = ["event_id"]


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
        .filter(date__isnull=False)
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
        .order_by("discnum", Cast("track", output_field=IntegerField()))
        .select_related("song", "release")
        .prefetch_related("event", "discid", "song__first_event", "song__last_event")
    )

    serializer_class = serializers.ReleaseTracksSerializer
    filterset_class = filters.ReleaseTracksFilter


class ReleasesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.Releases.objects.all()
        .annotate(
            date_str=Cast("date", output_field=CharField()),
            time_str=Cast("length", output_field=CharField()),
        )
        .order_by("-date")
    )
    serializer_class = serializers.ReleasesSerializer
    filterset_class = filters.ReleaseFilter


class SetlistStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.SetlistStats.objects.all()
        .select_related("event", "id")
        .prefetch_related("ltp")
    )
    serializer_class = serializers.SetlistStatsSerializer
    filterset_class = filters.SetlistStatsFilter


class SetlistViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.Setlists.objects.all()
        .select_related(
            "event",
            "song",
        )
        .prefetch_related(
            "ltp",
            "song__last_event",
            "setlist_notes",
            "setlist_position",
            "setlist_stats",
            "setlist_stats__ltp",
        )
        .order_by("event", F("song_num").asc(nulls_first=True))
        .annotate(
            count=Count("song__category"),
        )
    )

    serializer_class = serializers.SetlistSerializer
    filterset_class = filters.SetlistFilter
    ordering_fields = ["event__event_id", "song_num", "song__category", "song__name"]


class SetlistEntriesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        models.SetlistEntries.objects.all()
        .select_related(
            "event",
            "event__venue",
            "event__venue__city",
            "event__venue__venues_text",
        )
        .order_by("event__event_id")
        .prefetch_related(
            "event__venue__city__state",
            "event__venue__city__country",
            "event__tour",
            "event__leg",
            "event__run",
        )
    )

    serializer_class = serializers.SetlistEntrySerializer
    filterset_class = filters.SetlistEntryFilter


class SetlistSongsViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        filter = Q(set_name__in=VALID_SET_NAMES, event__public=True) | Q(
            set_name__in=["Recording", "Rehearsal"],
            event__public=False,
        )

        # set_name in valid and event public
        # set_name in recording and event not public

        queryset = (
            models.Setlists.objects.filter(filter).select_related("song", "event").all()
        )

        queryset = (
            queryset.values("song_id")
            .annotate(
                count=Count("id", distinct=True),
                first_event=Min("event__event_id"),
                last_event=Max("event__event_id"),
                sets=ArrayAgg("set_name", distinct=True),
            )
            .order_by("-count")
        )

        return self.filter_queryset(queryset)

    serializer_class = serializers.SetlistSongsSerializer
    filterset_class = filters.SetlistSongsFilter
    ordering_fields = ["count"]


class SnippetViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    def get_queryset(self):
        # Base subquery to find related events for the current Snippet row
        # OuterRef("snippet_id") links the subquery to the main row
        related_events = models.Snippets.objects.filter(
            snippet_id=OuterRef("snippet_id"),
            setlist__song_id=OuterRef("setlist__song_id"),
        ).order_by("setlist__event__event_id")

        queryset = (
            models.Snippets.objects.all()
            .select_related(
                "snippet",
                "setlist",
                "setlist__song",
                "setlist__event",
                "setlist__event__artist",
                "setlist__event__venue",
                "setlist__event__venue__city",
                "setlist__event__venue__venues_text",
            )
            .prefetch_related(
                "setlist__event__venue__city__state",
                "setlist__event__venue__city__country",
            )
            .annotate(
                # Get the first and last event_id via subquery
                first_event_id=Subquery(
                    related_events.values("setlist__event__event_id")[:1],
                ),
                last_event_id=Subquery(
                    related_events.order_by("-setlist__event__event_id").values(
                        "setlist__event__event_id",
                    )[:1],
                ),
                # Count total occurrences of this snippet/song combo
                count=SubqueryCount(related_events),  # Adjust based on how you group
            )
        )

        return self.filter_queryset(queryset)

    # def get_queryset(self):
    #     queryset = (
    #         models.Snippets.objects.all()
    #         .select_related(
    #             "snippet",
    #             "setlist",
    #             "setlist__song",
    #             "setlist__event",
    #             "setlist__event__artist",
    #             "setlist__event__venue",
    #             "setlist__event__venue__city",
    #             "setlist__event__venue__venues_text",
    #         )
    #         .prefetch_related(
    #             "setlist__event__venue__city__state",
    #             "setlist__event__venue__city__country",
    #         )
    #     )

    #     return self.filter_queryset(queryset)

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
    ).order_by("sort_song_name")

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
    queryset = models.Updates.objects.all().order_by("-created_at", "-id")
    serializer_class = serializers.UpdatesSerializer


class UsersViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        UserModel.objects.filter(is_active=True)
        .prefetch_related(
            "user_attended_shows",
        )
        .annotate(
            event_count=Count(
                "user_attended_shows__event",
            ),
            user_slug=Lower("username"),
        )
    )

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
        ).order_by("-event__event_id")

    serializer_class = serializers.UserAttendedShowsSerializer
    filterset_class = filters.UserAttendedShowsFilter


class SetlistBreakdown(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        event = self.request.query_params.get("event")
        user = self.request.query_params.get("user")

        song_filter = Q(
            Q(setlists__event__event_id=event)
            & Q(setlists__set_name__in=VALID_SET_NAMES),
        )

        album_filter = Q(
            Q(release__songs__category=OuterRef("category"))
            & Q(release__songs__setlists__event__event_id=event)
            & Q(release__songs__setlists__set_name__in=VALID_SET_NAMES),
        )

        songs_in_setlist = (
            models.Songs.objects.prefetch_related(
                "album",
                "album__release_tracks",
                "album__release_tracks__song",
            )
            .filter(
                song_filter,
            )
            .order_by("setlists__song_num")
        )

        album_song_count = (
            models.ReleaseTracks.objects.filter(
                album_filter,
            )
            .values("song_id")
            .distinct("song_id")
            .order_by("song_id")
        )

        breakdown_qs = (
            songs_in_setlist.values("category")
            .annotate(num=Count("id"))
            .order_by("-num")
        )

        songs = (
            songs_in_setlist.filter(category=OuterRef("category"))
            .order_by("setlists__song_num")
            .values(
                "id",
            )
        )

        song_count = songs_in_setlist.count()
        album_max = breakdown_qs.aggregate(max_val=Max("num"))["max_val"] or 1

        # 4. Final Annotation
        return breakdown_qs.annotate(
            max_val=Value(album_max),
            percent=ExpressionWrapper(
                (F("num") * 100) / song_count,
                output_field=DecimalField(max_digits=20, decimal_places=15),
            ),
            total=Value(song_count),
            songs=ArraySubquery(songs),
            album_songs=ArraySubquery(album_song_count),
        )

    serializer_class = serializers.SetlistBreakdownSerializer
    ordering = ["category", "max_val", "percent", "num"]


class SongsPage(viewsets.ReadOnlyModelViewSet):
    queryset = models.SongsPage.objects.all()
    serializer_class = serializers.SongsPageSerializer


class EventTypesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.EventTypes.objects.all()
    serializer_class = serializers.EventTypeSerializer
    filterset_class = filters.EventTypeFilter


class UserAlbumBreakdown(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        user = self.request.query_params.get("user")

        filter = Q(
            Q(release_tracks__song__setlists__event__user_event__user=user)
            & Q(release_tracks__song__setlists__set_name__in=VALID_SET_NAMES),
        )

        return (
            models.Releases.objects.filter(type="Studio")
            .prefetch_related("release_tracks", "release_tracks__song")
            .annotate(
                all_album_songs=ArrayAgg("release_tracks__song_id", distinct=True),
                songs_seen=ArrayAgg(
                    "release_tracks__song__id",
                    filter=filter,
                    distinct=True,
                ),
                user_album_count=Count(
                    "release_tracks__song__id",
                    filter=filter,
                    distinct=True,
                ),
                album_song_count=Count("release_tracks", distinct=True),
            )
            .annotate(
                album_percent=ExpressionWrapper(
                    F("user_album_count") * 100.0 / F("album_song_count"),
                    output_field=FloatField(),
                ),
            )
            .order_by("date")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()  # Assuming the annotations from previous steps
        user = self.request.query_params.get("user")
        valid_sets = ["Show", "Encore", "Set 1", "Set 2", "Pre-Show", "Post-Show"]

        # 1. Get all ReleaseTracks for these albums to maintain Disc/Track order
        # We order by discnum and track here so the list is ready
        release_tracks = (
            models.ReleaseTracks.objects.filter(
                release__in=queryset,
            )
            .select_related("song", "release")
            .order_by("discnum", Cast("track", output_field=IntegerField()))
        )

        # 2. Map song IDs to their respective Releases
        tracks_by_release = {}
        all_required_song_ids = set()
        for rt in release_tracks:
            all_required_song_ids.add(rt.song_id)
            if rt.release_id not in tracks_by_release:
                tracks_by_release[rt.release_id] = []
            tracks_by_release[rt.release_id].append(rt.song_id)

        # 3. Get "times seen" counts for this user
        user_song_counts = (
            models.Setlists.objects.filter(
                event__user_event__user=user,
                set_name__in=valid_sets,
                song_id__in=all_required_song_ids,
            )
            .values("song_id")
            .annotate(times_seen=Count("id"))
        )
        count_map = {item["song_id"]: item["times_seen"] for item in user_song_counts}

        # 4. Bulk fetch and serialize the song objects
        relevant_songs = models.Songs.objects.filter(id__in=all_required_song_ids)
        serialized_songs = serializers.MinimalSongsSerializer(
            relevant_songs,
            many=True,
        ).data

        # 5. Enrich the map with "times_seen" and "user_seen"
        songs_map = {}
        for song_data in serialized_songs:
            s_id = song_data["id"]
            count = count_map.get(s_id, 0)

            song_data["times_seen"] = count
            song_data["user_seen"] = count > 0  # New boolean field

            songs_map[s_id] = song_data

        # 6. Pass enriched data to context
        serializer = self.get_serializer(
            queryset,
            many=True,
            context={
                "songs_map": songs_map,
                "tracks_by_release": tracks_by_release,
            },
        )
        return response.Response(serializer.data)

    serializer_class = serializers.UserAlbumBreakdownSerializer
