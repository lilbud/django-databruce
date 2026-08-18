import datetime
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.postgres.expressions import ArraySubquery
from django.db.models import (
    CharField,
    Count,
    Exists,
    F,
    IntegerField,
    Max,
    Min,
    OuterRef,
    Prefetch,
    Q,
    Subquery,
    Value,
)
from django.db.models.functions import Cast, Coalesce, Lower
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import exceptions, viewsets

from api import filters
from api import serializers as api_serializers
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
date = datetime.datetime.now(tz=datetime.UTC).date()


class SubqueryCount(Subquery):
    """A custom Subquery class that performs a SQL COUNT operation.

    Instantiating fields in __init__ resolves Pylance / Pyright property type conflicts.
    """

    template = "(SELECT COUNT(*) FROM (%(subquery)s) _count)"

    def __init__(self, queryset: Any, **kwargs: Any) -> None:
        # Move the instantiation here to resolve the type-checker error
        kwargs.setdefault("output_field", IntegerField())
        super().__init__(queryset, **kwargs)


class EventSearch(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.Events.objects.select_related(
            "artist",
            "tour",
            "venue__city",
            "venue__venues_text",
        ).prefetch_related("run", "leg", "event_type")
    ).order_by("event_id")

    serializer_class = api_serializers.EventSearchSerializer
    filterset_class = filters.EventsFilter


class ArchiveViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.ArchiveLinks.objects.all().select_related("event")
    serializer_class = api_serializers.ArchiveLinksSerializer
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

    serializer_class = api_serializers.OnstageBandSerializer
    filterset_class = filters.OnstageBandFilter


class BandViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.Bands.objects.all()
        .order_by("name")
        .prefetch_related("first_event", "last_event")
    )

    serializer_class = api_serializers.BandsSerializer
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

    serializer_class = api_serializers.BootlegsSerializer
    filterset_class = filters.BootlegFilter


class CitiesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.Cities.objects.all()
        .order_by("name")
        .select_related("first_event", "last_event", "country")
        .prefetch_related("state")
    )

    serializer_class = api_serializers.CitiesSerializer
    filterset_class = filters.CitiesFilter


class SongsPageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.SongsPage.objects.all()
        .prefetch_related(
            "prev__song",
            "next__song",
            "id__setlist_stats",
            "id__setlist_notes",
            "id__event__venue__city__state",
        )
        .select_related(
            "id__event__artist",
            "id__event__tour",
            "id__event__venue__venues_text",
        )
    ).order_by("id__event__event_id", F("id__song_num").asc(nulls_first=True))

    serializer_class = api_serializers.SongsPageSerializer
    filterset_class = filters.SongsPageFilter


class ContinentsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Continents.objects.all()
    serializer_class = api_serializers.ContinentsSerializer
    filterset_fields = ["name"]
    ordering = ["name", "num_events"]


class CountriesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.Countries.objects.all()
        .order_by("name")
        .select_related("first_event", "last_event")
    )

    serializer_class = api_serializers.CountriesSerializer
    filterset_class = filters.CountryFilter


class CoversViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Covers.objects.all().select_related("event")
    serializer_class = api_serializers.CoversSerializer
    filterset_class = filters.CoversFilter
    ordering = ["event"]


class VenuesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.Venues.objects.all()
        .select_related(
            "city__country",
            "venues_text",
        )
        .prefetch_related("city__state", "first_event", "last_event")
        .order_by("name")
    )

    serializer_class = api_serializers.VenuesSerializer
    filterset_class = filters.VenuesFilter


class AdvancedEventSearch(viewsets.ReadOnlyModelViewSet):
    serializer_class = api_serializers.AdvSearchSerializer
    filter_backends = [DjangoFilterBackend, filters.NotEqualFilterBackend]
    filterset_class = filters.EventsFilter

    def get_queryset(self):
        onstage_qs = models.Onstage.objects.select_related("relation").prefetch_related(
            "band",
        )

        status_check = models.EventTypes.objects.filter(
            event_id=OuterRef("pk"),
            type_id__in=[6, 21, 22],  # Uses the through-table IDs directly
        )

        return (
            models.Events.objects.all()
            .select_related(
                "artist",
                "tour",
                "venue__city__country",
                "venue__venues_text",
            )
            .prefetch_related(
                "run",
                "venue__city__state",
                "leg",
                "tags",
                "type",
                Prefetch("onstage_event", queryset=onstage_qs, to_attr="onstage"),
                Prefetch(
                    "setlist_event",
                    queryset=models.Setlists.objects.select_related(
                        "song",
                    ).prefetch_related("setlist_notes"),
                ),
            )
            .annotate(event_status=Exists(status_check))
        ).order_by("event_id")

    def filter_queryset(self, queryset):
        # 1. Let django-filter process the standard form fields first
        queryset = super().filter_queryset(queryset)

        # Base structure mapping positions to Q objects
        position_filters = {
            "show_opener": Q(setlist_event__is_opener=True),
            "in_show": Q(setlist_event__set_name="show"),
            "in_set_one": Q(setlist_event__set_name="set 1"),
            "set_one_opener": Q(setlist_event__set_name="set 1", is_set_opener=True),
            "set_one_closer": Q(setlist_event__set_name="set 1", is_set_closer=True),
            "in_set_two": Q(setlist_event__set_name="set 2"),
            "set_two_opener": Q(setlist_event__set_name="set 2", is_set_opener=True),
            "set_two_closer": Q(setlist_event__set_name="set 2", is_set_closer=True),
            "main_set_closer": Q(setlist_event__is_main_set_closer=True),
            "encore_opener": Q(setlist_event__set_name="encore", is_set_opener=True),
            "in_encore": Q(setlist_event__set_name="encore"),
            "in_preshow": Q(setlist_event__set_name="pre-show"),
            "in_recording": Q(setlist_event__set_name="recording"),
            "in_soundcheck": Q(setlist_event__set_name="soundcheck"),
            "show_closer": Q(setlist_event__is_closer=True),
            "anywhere": Q(),
            "premiere": Q(setlist_event__premiere=True),
            "debut": Q(setlist_event__debut=True),
            "nobruce": Q(setlist_event__nobruce=True),
            "request": Q(setlist_event__sign_request=True),
        }

        # 2. Extract query parameters for the dynamic formset
        query_params = self.request.query_params  # type: ignore
        conjunction = query_params.get("conjunction", "and").lower()

        try:
            total_forms = int(query_params.get("form-TOTAL_FORMS", 0))
        except ValueError:
            total_forms = 0

        if total_forms == 0:
            return queryset

        # 3. Parse and collect all valid formset queries
        formset_queries = []
        for i in range(total_forms):
            song_1 = query_params.get(f"form-{i}-song1")
            song_2 = query_params.get(f"form-{i}-song2")
            choice = query_params.get(f"form-{i}-choice")
            position = query_params.get(f"form-{i}-position")

            if song_1:
                formset_queries.append(
                    {
                        "song_1": song_1,
                        "choice": choice.lower() == "true",
                        "position": position,
                        "song_2": song_2,
                    },
                )

        if not formset_queries:
            return queryset

        # =========================================================================
        # 4. CHOP UP FILTERS ACCORDING TO LOGICAL OPERATOR (THE FIX)
        # =========================================================================
        if conjunction == "or":
            # For OR operations, a single combined filter is required.
            or_filter = Q()
            for query in formset_queries:
                condition = self._build_form_condition(query, position_filters)
                or_filter |= condition

            queryset = queryset.filter(or_filter)
        else:
            # For AND operations, loop and CHAIN discrete .filter() statements.
            # This isolates the SQL multi-joins per row instead of cross-contaminating them.
            for query in formset_queries:
                condition = self._build_form_condition(query, position_filters)
                queryset = queryset.filter(condition)

        # 5. Prevent duplicate entries from Many-To-Many relational joins
        return queryset.distinct()

    def _build_form_condition(self, query, position_filters) -> Q:
        match_songs = [query["song_1"]]

        condition = Q(setlist_event__set_name__in=VALID_SET_NAMES)

        if query["position"] == "followed_by" and query["song_2"]:
            condition &= Q(setlist_event__song_id=query["song_1"]) & Q(
                setlist_event__songs_page__next__song_id=query["song_2"],
            )

        else:
            condition &= Q(setlist_event__song_id=query["song_1"])

            if query["position"] and query["position"] not in [
                "anywhere",
                "followed_by",
            ]:
                condition &= position_filters.get(query["position"], Q())

        # Invert condition if choice is False (NOT evaluation)
        if query["choice"] is False:
            condition = ~condition

            # followed by special case
            if query["position"] == "followed_by" and query["song_2"]:
                match_songs.append(query["song_2"])
                condition = (
                    Q(setlist_event__set_name__in=VALID_SET_NAMES)
                    & Q(
                        Q(setlist_event__song_id=query["song_1"])
                        & ~Q(
                            setlist_event__songs_page__next__song_id=query["song_2"],
                        ),
                    )
                    & Q(setlist_event__song_id__in=match_songs)
                )

        return condition


class IndexSetlistViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        models.Setlists.objects.all()
        .select_related(
            "event",
            "song",
        )
        .prefetch_related(
            "setlist_notes",
        )
        .order_by("event__event_id", F("song_num").asc(nulls_first=True))
    )

    serializer_class = api_serializers.IndexSetlistSerializer
    filterset_class = filters.SetlistFilter
    ordering_fields = ["event__event_id", "song_num", "song__category", "song__name"]


class IndexEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        models.Events.objects.all().select_related(
            "venue__venues_text",
        )
    ).order_by("event_id")

    serializer_class = api_serializers.IndexEventsSerializer
    filterset_class = filters.EventsFilter
    ordering_fields = ["event_id"]


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    def get_queryset(self):
        status_check = models.EventTypes.objects.filter(
            event_id=OuterRef("pk"),
            type_id__in=[6, 21, 22],  # Uses the through-table IDs directly
        )

        onstage_qs = models.Onstage.objects.select_related("relation").prefetch_related(
            "band",
        )

        return (
            models.Events.objects.select_related(
                "artist",
                "tour",
                "venue__city__country",
                "venue__venues_text",
                "venue__parent",
            )
            .prefetch_related(
                "run",
                "venue__city__state",
                "leg",
                Prefetch("onstage_event", queryset=onstage_qs, to_attr="onstage"),
                Prefetch(
                    "setlist_event",
                    queryset=models.Setlists.objects.select_related(
                        "song",
                    ).prefetch_related("setlist_notes"),
                ),
                "type",
                "tags",
            )
            .annotate(event_status=Exists(status_check))
        ).order_by("event_id")

    serializer_class = api_serializers.EventsSerializer
    filterset_class = filters.EventsFilter
    ordering_fields = ["event_id"]


class AdvancedSearch(viewsets.ReadOnlyModelViewSet):
    queryset = (
        models.Events.objects.all()
        .select_related(
            "venue",
            "artist",
            "tour",
            "venue__city__country",
            "venue__venues_text",
            "type",
            "tags",
        )
        .prefetch_related(
            "onstage",
            "run",
            "venue__city__state",
            "leg",
            "setlist_event",
        )
        .order_by("event_id")
    )

    serializer_class = api_serializers.AdvSearchSerializer
    # filterset_class = filters.EventsFilter
    filter_backends = [filters.EventsFilter, filters.NotEqualFilterBackend]


class NugsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.NugsReleases.objects.all()
        .filter(date__isnull=False)
        .select_related(
            "event__venue__venues_text",
            "event__tour",
            "event__artist",
            "event__venue__city__country",
        )
        .prefetch_related(
            "event__venue__city__state",
        )
    ).order_by("-date")

    serializer_class = api_serializers.NugsSerializer
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

    serializer_class = api_serializers.RelationsSerializer
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

    serializer_class = api_serializers.OnstageSerializer
    filterset_class = filters.OnstageFilter


class ReleaseTracksViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.ReleaseTracks.objects.all()
        .order_by("discnum", "position")
        .select_related("song", "release")
        .prefetch_related("event", "disc")
    )

    serializer_class = api_serializers.ReleaseTracksSerializer
    filterset_class = filters.ReleaseTracksFilter


class ReleasesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.Releases.objects.all()
        .prefetch_related("event")
        .annotate(
            date_str=Cast("date", output_field=CharField(max_length=10)),
            time_str=Cast("length", output_field=CharField(max_length=10)),
        )
        .order_by("-date")
    )
    serializer_class = api_serializers.ReleasesSerializer
    filterset_class = filters.ReleaseFilter


class SetlistStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.SetlistStats.objects.all()
        .select_related("event", "setlist")
        .prefetch_related("ltp")
    )
    serializer_class = api_serializers.SetlistStatsSerializer
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
            "setlist_notes",
        )
        .order_by("event__event_id", F("song_num").asc(nulls_first=True))
    )

    serializer_class = api_serializers.SetlistSerializer
    filterset_class = filters.SetlistFilter
    ordering_fields = ["event__event_id", "song_num", "song__category", "song__name"]


class SetlistMobileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        models.Setlists.objects.all()
        .select_related(
            "event",
            "song",
        )
        .prefetch_related(
            "setlist_notes",
        )
        .order_by("event", F("song_num").asc(nulls_first=True))
    )

    serializer_class = api_serializers.SetlistMobileSerializer
    filterset_class = filters.SetlistFilter
    ordering_fields = ["event__event_id", "song_num", "song__category", "song__name"]


class SetlistEntriesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        models.SetlistEntries.objects.all()
        .select_related(
            "event",
            "event__venue__city",
        )
        .order_by("event__event_id")
        .prefetch_related(
            "show_opener",
            "s1_closer",
            "s2_opener",
            "main_closer",
            "encore_opener",
            "show_closer",
        )
    )

    serializer_class = api_serializers.SetlistEntrySerializer
    filterset_class = filters.SetlistEntryFilter


class SetlistSongsViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        filter = Q(set_name__in=VALID_SET_NAMES, event__public=True, nobruce=False) | Q(
            set_name__in=["Recording", "Rehearsal"],
            event__public=False,
        )

        queryset = (
            models.Setlists.objects.filter(filter)
            .select_related("song", "event")
            .prefetch_related("song__first_event", "song__last_event")
            .all()
        )

        queryset = (
            queryset.values("song_id")
            .annotate(
                count=Count("id", distinct=True),
                first_event=Min("event__event_id"),
                last_event=Max("event__event_id"),
            )
            .order_by("-count")
        )

        return self.filter_queryset(queryset)  # type: ignore

    serializer_class = api_serializers.SetlistSongsSerializer
    filterset_class = filters.SetlistSongsFilter
    ordering_fields = ["count"]


class SnippetViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    def get_queryset(self):
        queryset = (
            models.Snippets.objects.all().select_related(
                "setlist__song",
                "setlist__event__artist",
                "setlist__event__venue",
            )
        ).order_by("setlist__event__event_id")

        return self.filter_queryset(queryset)

    serializer_class = api_serializers.SnippetSerializer
    filterset_class = filters.SnippetFilter


class IncludedSongViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    def get_queryset(self):
        queryset = models.Snippets.objects.all().select_related(
            "setlist__song",
            "setlist__event__artist",
            "setlist__event__venue",
            "snippet",
        )

        queryset = (
            queryset.values("snippet_id")
            .annotate(
                count=Count("id", distinct=True),
                first_event=Min("setlist__event__event_id"),
                last_event=Max("setlist__event__event_id"),
            )
            .order_by("-count")
        )

        return self.filter_queryset(queryset)

    serializer_class = api_serializers.IncludedSerializer
    filterset_class = filters.IncludedFilter


class StatesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.States.objects.all()
        .select_related("country")
        .prefetch_related("first_event", "last_event")
        .order_by("name")
    )

    serializer_class = api_serializers.StatesSerializer
    filterset_class = filters.StateFilter


class SongsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.Songs.objects.all().prefetch_related(
            "first_event",
            "last_event",
            "lyrics_song",
        )
    ).order_by("sort_song_name")

    serializer_class = api_serializers.SongsSerializer
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

    serializer_class = api_serializers.ToursSerializer
    filterset_class = filters.TourFilter


class TourLegsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = (
        models.TourLegs.objects.all()
        .select_related(
            "tour",
            "first_event__artist",
            "first_event__tour",
            "last_event__artist",
            "last_event__tour",
        )
        .order_by("-last_event__event_id")
    )

    serializer_class = api_serializers.TourLegsSerializer
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
            "venue__venues_text",
        )
        .prefetch_related(
            "venue__city__state",
            "venue__city__country",
        )
        .order_by("first_event__event_id")
    )

    serializer_class = api_serializers.EventRunSerializer
    filterset_class = filters.EventRunFilter


class LyricsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Lyrics.objects.all().select_related("song").order_by("song__name")
    serializer_class = api_serializers.LyricsSerializer


class SetlistNotesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        models.SetlistNotes.objects.all()
        .select_related(
            "setlist__song",
            "event",
            "event__venue__city",
            "event__venue__venues_text",
        )
        .prefetch_related(
            "event__venue__city__state",
            "event__venue__city__country",
        )
    )

    serializer_class = api_serializers.SetlistNotesSerializer
    filterset_class = filters.SetlistNoteFilter


class UpdatesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Updates.objects.all().order_by("-created_at", "-id")
    serializer_class = api_serializers.UpdatesSerializer


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

    serializer_class = api_serializers.UsersSerializer


class UsersAttendedShowsViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return (
            models.UserAttendedShows.objects.all().select_related(
                "user",
                "event",
            )
        ).order_by("-event__event_id")

    serializer_class = api_serializers.UserAttendedShowsSerializer
    filterset_class = filters.UserAttendedShowsFilter


from rest_framework.exceptions import ValidationError


class SetlistBreakdown(viewsets.ReadOnlyModelViewSet):
    """Return setlist breakdown by category with album completion status."""

    serializer_class = api_serializers.SetlistBreakdownSerializer
    ordering = ["-song_count", "total_setlist_songs"]

    def get_queryset(self):
        event_id = self.request.query_params.get("event")  # type: ignore
        user = self.request.query_params.get("user")  # type: ignore
        event_filter = Q(set_name__in=VALID_SET_NAMES)

        if not event_id and not user:
            raise ValidationError({"event": "This parameter is required."})

        if user:
            event_filter = Q(
                Q(event__user_event__user_id=user) & Q(set_name__in=VALID_SET_NAMES),
            )

        if event_id:
            event_filter = Q(Q(event_id=event_id) & Q(set_name__in=VALID_SET_NAMES))

        # Base setlist for this event (reused for total count and filtering)
        event_setlist = models.Setlists.objects.filter(
            event_filter,
        )

        # Total songs in entire setlist (for percentage calculations, etc.)
        total_setlist_songs = event_setlist.annotate(
            cnt=Count("id"),
        ).values("cnt")

        # Album songs subquery: songs from releases matching this category
        album_songs_subquery = (
            models.ReleaseTracks.objects.filter(
                release__songs__category=OuterRef("song__category"),
            )
            .distinct("position", "song_id")
            .order_by("position")
            .values("song_id")
        )

        # Setlist songs subquery: songs from this event matching this category
        setlist_songs_subquery = (
            event_setlist.filter(
                song__category=OuterRef("song__category"),
            )
            .order_by("song_num")
            .values("song_id")
        )

        # Aggregate by category
        return (
            event_setlist.select_related("song", "event")
            .values(category=F("song__category"))
            .annotate(
                song_count=Count("id"),  # songs in this category
                total_setlist_songs=SubqueryCount(
                    total_setlist_songs,
                ),  # total songs in setlist
                songs=ArraySubquery(setlist_songs_subquery),
                category_slug=F("song__category_slug"),
                album_songs=ArraySubquery(album_songs_subquery),
            )
        )


class TypesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Types.objects.all()
    serializer_class = api_serializers.TypesSerializer
    filterset_class = filters.TypeFilter


class EventTypesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.EventTypes.objects.all()
    serializer_class = api_serializers.EventTypeSerializer
    filterset_class = filters.EventTypeFilter


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Tags.objects.all()
    serializer_class = api_serializers.TagsSerializer
    filterset_class = filters.TagFilter


class EventTagsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.EventTags.objects.all()
    serializer_class = api_serializers.EventTagSerializer
    filterset_class = filters.EventTagFilter


# class UserAlbumBreakdown(viewsets.ReadOnlyModelViewSet):
#     def get_queryset(self):
#         user = self.request.query_params.get("user")  # type: ignore

#         filter = Q(
#             Q(release_tracks__song__setlists__event__user_event__user_id=user)
#             & Q(release_tracks__song__setlists__set_name__in=VALID_SET_NAMES),
#         )

#         return (
#             models.Releases.objects.filter(type="Studio")
#             .prefetch_related("release_tracks")
#             .annotate(
#                 user_album_count=Count(
#                     "release_tracks",
#                     filter=filter,
#                     distinct=True,
#                 ),
#                 album_song_count=Count("release_tracks", distinct=True),
#             )
#             .order_by("date")
#         )

#     def list(self, request, *args, **kwargs) -> response.Response:
#         queryset = self.get_queryset()  # Assuming the annotations from previous steps
#         user = self.request.query_params.get("user")  # type: ignore
#         valid_sets = ["Show", "Encore", "Set 1", "Set 2", "Pre-Show", "Post-Show"]

#         # 1. Get all ReleaseTracks for these albums to maintain Disc/Track order
#         # We order by discnum and track here so the list is ready
#         release_tracks = (
#             models.ReleaseTracks.objects.filter(
#                 release_id__in=queryset.values("id"),
#             )
#             .select_related("song")
#             .order_by("discnum", "position")
#         )

#         # 2. Map song IDs to their respective Releases
#         tracks_by_release = {}

#         for rt in release_tracks:
#             if rt.release_id not in tracks_by_release:  # type: ignore
#                 tracks_by_release[rt.release_id] = []  # type: ignore

#             tracks_by_release[rt.release_id].append(rt.song_id)  # type: ignore

#         # 3. Get "times seen" counts for this user
#         user_song_counts = (
#             models.Setlists.objects.filter(
#                 event__user_event__user_id=user,
#                 set_name__in=valid_sets,
#                 song_id__in=release_tracks.values_list("song_id", flat=True),
#             )
#             .select_related("song", "event__user_event")
#             .annotate(times_seen=Count("id"))
#         )

#         count_map = {
#             item["song_id"]: item["times_seen"]
#             for item in user_song_counts.values("song_id", "times_seen")
#         }

#         # 4. Bulk fetch and serialize the song objects
#         relevant_songs = models.Songs.objects.filter(
#             id__in=release_tracks.values_list("song_id", flat=True),
#         )

#         serialized_songs = api_serializers.MinimalSongsSerializer(
#             relevant_songs,
#             many=True,
#             include=["slug", "name", "id"],
#         ).data

#         # 5. Enrich the map with "times_seen" and "user_seen"
#         songs_map = {}

#         for song_data in serialized_songs:
#             s_id = song_data["id"]
#             count = count_map.get(s_id, 0)

#             song_data["times_seen"] = count

#             songs_map[s_id] = song_data

#         # 6. Pass enriched data to context
#         serializer = self.get_serializer(
#             queryset,
#             many=True,
#             context={
#                 "songs_map": songs_map,
#                 "tracks_by_release": tracks_by_release,
#             },
#         )
#         return response.Response(serializer.data)

#     serializer_class = api_serializers.UserAlbumBreakdownSerializer
#     filterset_class = filters.UserAlbumBreakdownFilter


class UserAlbumBreakdown(viewsets.ReadOnlyModelViewSet):
    serializer_class = api_serializers.UserAlbumBreakdownSerializer

    def get_queryset(self):
        user_id = self.request.query_params.get("user")  # type: ignore
        if not user_id:
            return models.Releases.objects.none()

        # 1. Corrected Subquery: Group by song_id using values() BEFORE annotate()
        # DO NOT slice with [:1] here as it corrupts the Prefetch query grouping.
        times_seen_subquery = (
            models.Setlists.objects.filter(
                song_id=OuterRef("song_id"),
                event__user_event__user_id=user_id,
                set_name__in=VALID_SET_NAMES,
            )
            .values("song_id")
            .annotate(cnt=Count("id"))
            .values("cnt")
        )

        # 2. Prefetch release tracks with annotated play count
        tracks_prefetch = Prefetch(
            "release_tracks",
            queryset=models.ReleaseTracks.objects.select_related("song")
            .annotate(
                times_seen=Coalesce(
                    Subquery(times_seen_subquery),
                    Value(0),
                ),
            )
            .order_by("discnum", "position"),
        )

        # 3. Fetch all Studio releases and prefetch their full track lists
        return (
            models.Releases.objects.filter(type="Studio")
            .prefetch_related(tracks_prefetch)
            .order_by("date")
        )

    def list(self, request, *args, **kwargs):
        if "user" not in request.query_params:
            raise exceptions.ValidationError(
                {"user": "This query parameter is required."},
            )
        return super().list(request, *args, **kwargs)


class YearSongBreakdown(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return (
            models.Setlists.objects.filter(
                Q(set_name__in=VALID_SET_NAMES) & Q(event__date__isnull=False),
            )
            .values(year=F("event__date__year"))
            .annotate(
                count=Count(
                    "event__event_id",
                    distinct=True,
                    filter=Q(set_name__in=VALID_SET_NAMES),
                ),
            )
        )

    serializer_class = api_serializers.YearSongBreakdownSerializer
    filterset_class = filters.YearSongBreakdownFilter
