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
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination

from api import filters as api_filters
from api import serializers as api_serializers
from bruceyversion.models import Entry, EntryComment
from databruce import models as db_models
from library.models import Article

UserModel = get_user_model()

date = datetime.datetime.now(tz=datetime.UTC).date()


class StandardSetPagination(PageNumberPagination):
  page_size = 10
  page_size_query_param = "per_page"
  max_page_size = 100


class SubqueryCount(Subquery):
  """A custom Subquery class that performs a SQL COUNT operation.

  Instantiating fields in __init__ resolves Pylance / Pyright property type conflicts.
  """

  template = "(SELECT COUNT(*) FROM (%(subquery)s) _count)"

  def __init__(self, queryset: Any, **kwargs: Any) -> None:
    kwargs.setdefault("output_field", IntegerField())
    super().__init__(queryset, **kwargs)


class EventSearchViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  queryset = (
    db_models.Event.objects.select_related(
      "artist",
      "tour",
      "venue__venues_text",
    ).prefetch_related("run", "leg", "event_type")
  ).order_by("event_id")

  serializer_class = api_serializers.EventSearchSerializer
  filterset_class = api_filters.EventsFilter


class ArchiveViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  queryset = db_models.ArchiveLinks.objects.all().select_related("event")
  serializer_class = api_serializers.ArchiveLinksSerializer
  filterset_class = api_filters.ArchiveFilter


class OnstageBandViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  def get_queryset(self):
    return (
      db_models.OnstageBandMember.objects.all()
      .select_related(
        "relation",
        "band",
        "first",
        "last",
      )
      .order_by("count")
    )

  serializer_class = api_serializers.OnstageBandSerializer
  filterset_class = api_filters.OnstageBandFilter


class BandViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  queryset = db_models.Band.objects.order_by("name")

  serializer_class = api_serializers.BandsSerializer
  filterset_class = api_filters.BandsFilter


class BootlegViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  queryset = (
    db_models.Bootleg.objects.select_related(
      "event",
    )
    .prefetch_related("archive")
    .order_by("event")
  )

  serializer_class = api_serializers.BootlegsSerializer
  filterset_class = api_filters.BootlegFilter


class CitiesViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  queryset = (
    db_models.City.objects.all()
    .order_by("name")
    .select_related("first_event", "last_event", "country")
    .prefetch_related("state")
  )

  serializer_class = api_serializers.CitiesSerializer
  filterset_class = api_filters.CitiesFilter


class SongsPageViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  queryset = (
    db_models.SongPage.objects.all()
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
  filterset_class = api_filters.SongsPageFilter


class ContinentsViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  queryset = db_models.Continent.objects.all()
  serializer_class = api_serializers.ContinentsSerializer
  filterset_fields = ["name"]
  ordering = ["name", "num_events"]


class CountriesViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  queryset = (
    db_models.Country.objects.all()
    .order_by("name")
    .select_related("first_event", "last_event")
  )

  serializer_class = api_serializers.CountriesSerializer
  filterset_class = api_filters.CountryFilter


class CoversViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  queryset = db_models.Cover.objects.all().select_related("event")
  serializer_class = api_serializers.CoversSerializer
  filterset_class = api_filters.CoversFilter
  ordering = ["event"]


class VenuesViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  queryset = (
    db_models.Venue.objects.all()
    .select_related(
      "city__country",
      "venues_text",
    )
    .prefetch_related("city__state", "first_event", "last_event")
    .order_by("name")
  )

  serializer_class = api_serializers.VenuesSerializer
  filterset_class = api_filters.VenuesFilter


class AdvancedEventSearchViewSet(viewsets.ReadOnlyModelViewSet):
  serializer_class = api_serializers.AdvSearchSerializer
  filter_backends = [
    api_filters.DataTablesFilterBackend,
    DjangoFilterBackend,
    api_filters.NotEqualFilterBackend,
  ]
  filterset_class = api_filters.AdvSearchFilter

  def get_queryset(self):
    status_check = db_models.EventType.objects.filter(
      event_id=OuterRef("pk"),
      type_id__in=[6, 21, 22],  # Uses the through-table IDs directly
    )

    return (
      db_models.Event.objects.all()
      .select_related(
        "artist",
        "tour",
        "venue__city__country",
        "venue",
      )
      .prefetch_related(
        "run",
        "venue__city__state",
        "leg",
        "event_tag",
        "event_type",
      )
      .annotate(event_status=Exists(status_check))
    ).order_by("event_id")

  def filter_queryset(self, queryset):
    # 1. Let django-filter process the standard form fields first
    queryset = super().filter_queryset(queryset)

    # Base structure mapping positions to Q objects
    position_filters = {
      "show_opener": Q(setlist_event__is_opener=True),
      "in_show": Q(setlist_event__set_name=db_models.SetType.SHOW),
      "in_set_one": Q(setlist_event__set_name=db_models.SetType.SET_1),
      "is_set_opener": Q(setlist_event__is_set_opener=True),
      "set_one_opener": Q(
        setlist_event__set_name=db_models.SetType.SET_1,
        setlist_event__is_set_opener=True,
      ),
      "set_one_closer": Q(
        setlist_event__set_name=db_models.SetType.SET_1,
        setlist_event__is_set_closer=True,
      ),
      "in_set_two": Q(setlist_event__set_name=db_models.SetType.SET_2),
      "set_two_opener": Q(
        setlist_event__set_name=db_models.SetType.SET_2,
        setlist_event__is_set_opener=True,
      ),
      "set_two_closer": Q(
        setlist_event__set_name=db_models.SetType.SET_2,
        setlist_event__is_set_closer=True,
      ),
      "main_set_closer": Q(setlist_event__is_main_set_closer=True),
      "encore_opener": Q(
        setlist_event__set_name=db_models.SetType.ENCORE,
        setlist_event__is_set_opener=True,
      ),
      "in_encore": Q(setlist_event__set_name=db_models.SetType.ENCORE),
      "in_preshow": Q(setlist_event__set_name=db_models.SetType.PRE_SHOW),
      "in_recording": Q(
        setlist_event__set_name=db_models.SetType.RECORDING,
      ),
      "in_soundcheck": Q(
        setlist_event__set_name=db_models.SetType.SOUNDCHECK,
      ),
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
    setlist_queries = []
    index = 0

    while f"songs[{index}][song_1]" in query_params:
      # Safely convert choice string back to a Python boolean
      choice_str = query_params.get(f"songs[{index}][choice]", "false").lower()

      song_dict = {
        "song_1": query_params.get(f"songs[{index}][song_1]"),
        "song_2": query_params.get(
          f"songs[{index}][song_2]",
        ),  # Will be None if missing
        "choice": choice_str == "true",
        "position": query_params.get(f"songs[{index}][position]"),
      }

      setlist_queries.append(song_dict)
      index += 1

    # =========================================================================
    # 4. CHOP UP FILTERS ACCORDING TO LOGICAL OPERATOR (THE FIX)
    # =========================================================================
    songs = []

    if conjunction == "or":
      # For OR operations, a single combined filter is required.
      or_filter = Q()
      for query in setlist_queries:
        condition = self._build_form_condition(query, position_filters)
        or_filter |= condition

      queryset = queryset.filter(or_filter)
    else:
      and_filter = Q()
      # For AND operations, loop and CHAIN discrete .filter() statements.
      # This isolates the SQL multi-joins per row instead of cross-contaminating them.
      for query in setlist_queries:
        # songs.append(query["song_1"])

        if query["song_2"]:
          songs.append(query["song_2"])

        condition = self._build_form_condition(query, position_filters)
        and_filter &= condition

      queryset = queryset.filter(and_filter)

    songs = list(set(songs))

    if songs:
      queryset = queryset.filter(setlist_event__song_id__in=songs)

    # 5. Prevent duplicate entries from Many-To-Many relational joins
    return queryset.distinct()

  def _build_form_condition(self, query, position_filters) -> Q:
    match_songs = [int(query["song_1"])]

    condition = Q(setlist_event__set_name__in=db_models.SetType.valid_sets())

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
        match_songs.append(int(query["song_2"]))

        condition = Q(setlist_event__set_name__in=db_models.SetType.valid_sets()) & Q(
          Q(setlist_event__song_id=query["song_1"])
          & ~Q(
            setlist_event__songs_page__next__song_id=query["song_2"],
          ),
        )

    print(condition)

    return condition


class IndexSetlistViewSet(viewsets.ReadOnlyModelViewSet):
  queryset = (
    db_models.Setlist.objects.all()
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
  filterset_class = api_filters.SetlistFilter
  ordering_fields = ["event__event_id", "song_num", "song__category", "song__name"]


class IndexEventViewSet(viewsets.ReadOnlyModelViewSet):
  queryset = (
    db_models.Event.objects.all().select_related(
      "venue__venues_text",
    )
  ).order_by("event_id")

  serializer_class = api_serializers.IndexEventsSerializer
  filterset_class = api_filters.EventsFilter
  ordering_fields = ["event_id"]


class EventViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  def get_queryset(self):
    status_check = db_models.EventType.objects.filter(
      event_id=OuterRef("pk"),
      type_id__in=[6, 21, 22],  # Uses the through-table IDs directly
    )

    return (
      db_models.Event.objects.select_related(
        "artist",
        "tour",
        "venue__city__country",
      )
      .prefetch_related(
        "venue__city__state",
        "leg",
        "setlist_event",
        "type",
        "tags",
      )
      .annotate(event_status=Exists(status_check))
    ).order_by("event_id")

  serializer_class = api_serializers.EventsSerializer
  filterset_class = api_filters.EventsFilter
  ordering_fields = ["event_id"]


class AdvancedSearchViewSet(viewsets.ReadOnlyModelViewSet):
  queryset = (
    db_models.Event.objects.all()
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
  filter_backends = [api_filters.EventsFilter, api_filters.NotEqualFilterBackend]


class NugsViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  queryset = (
    db_models.NugsRelease.objects.all()
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
  filter_backends = [api_filters.DataTablesFilterBackend]


class RelationsViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  # rel_aliases = db_models.RelationAlias.objects.filter(relation=OuterRef("id"))
  onstage = db_models.Onstage.objects.select_related("relation").filter(
    relation=OuterRef("id"),
  )

  queryset = (
    db_models.Relation.objects.all()
    .order_by("name")
    .select_related("first_event", "last_event")
  )

  serializer_class = api_serializers.RelationsSerializer
  filterset_class = api_filters.RelationFilter


class OnstageViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  queryset = (
    db_models.Onstage.objects.all()
    .select_related(
      "relation",
      "event",
    )
    .prefetch_related(
      "band",
    )
  ).order_by("event", F("band").asc(nulls_first=True), "relation__name")

  serializer_class = api_serializers.OnstageSerializer
  filterset_class = api_filters.OnstageFilter


class ReleaseTracksViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  queryset = (
    db_models.ReleaseTrack.objects.all()
    .order_by("discnum", "position")
    .select_related("song", "release")
    .prefetch_related("event", "disc")
  )

  serializer_class = api_serializers.ReleaseTracksSerializer
  filterset_class = api_filters.ReleaseTracksFilter


class ReleasesViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  queryset = (
    db_models.Release.objects.all()
    .prefetch_related("event")
    .annotate(
      date_str=Cast("date", output_field=CharField(max_length=10)),
      time_str=Cast("length", output_field=CharField(max_length=10)),
    )
    .order_by("-date")
  )
  serializer_class = api_serializers.ReleasesSerializer
  filterset_class = api_filters.ReleaseFilter


class SetlistStatsViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  queryset = (
    db_models.SetlistStats.objects.all()
    .select_related("event", "setlist")
    .prefetch_related("ltp")
  )
  serializer_class = api_serializers.SetlistStatsSerializer
  filterset_class = api_filters.SetlistStatsFilter


class SetlistViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  queryset = (
    db_models.Setlist.objects.all()
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
  filterset_class = api_filters.SetlistFilter
  ordering_fields = ["event__event_id", "song_num", "song__category", "song__name"]


class SetlistMobileViewSet(viewsets.ReadOnlyModelViewSet):
  queryset = (
    db_models.Setlist.objects.all()
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
  filterset_class = api_filters.SetlistFilter
  ordering_fields = ["event__event_id", "song_num", "song__category", "song__name"]


class SetlistEntriesViewSet(viewsets.ReadOnlyModelViewSet):
  queryset = (
    db_models.SetlistEntries.objects.all()
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
  filterset_class = api_filters.SetlistEntryFilter


class SetlistSongsViewSet(viewsets.ReadOnlyModelViewSet):
  def get_queryset(self):
    filter = Q(
      set_name__in=db_models.SetType.valid_sets(),
      event__public=True,
      nobruce=False,
    ) | Q(
      set_name__in=["Recording", "Rehearsal"],
      event__public=False,
    )

    queryset = (
      db_models.Setlist.objects.filter(filter)
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
  filterset_class = api_filters.SetlistSongsFilter
  ordering_fields = ["count"]


class SnippetViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  def get_queryset(self):
    queryset = (
      db_models.Snippet.objects.all().select_related(
        "setlist__song",
        "setlist__event__artist",
        "setlist__event__venue",
      )
    ).order_by("setlist__event__event_id")

    return self.filter_queryset(queryset)

  serializer_class = api_serializers.SnippetSerializer
  filterset_class = api_filters.SnippetFilter


class IncludedSongViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  def get_queryset(self):
    queryset = db_models.Snippet.objects.all().select_related(
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
  filterset_class = api_filters.IncludedFilter


class StatesViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  queryset = (
    db_models.State.objects.all()
    .select_related("country")
    .prefetch_related("first_event", "last_event")
    .order_by("name")
  )

  serializer_class = api_serializers.StatesSerializer
  filterset_class = api_filters.StateFilter


class SongsViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  queryset = (
    db_models.Song.objects.all().prefetch_related(
      "first_event",
      "last_event",
      "lyrics_song",
    )
  ).order_by("sort_song_name")

  serializer_class = api_serializers.SongsSerializer
  filterset_class = api_filters.SongsFilter


class ToursViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  queryset = (
    db_models.Tour.objects.all()
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
  filterset_class = api_filters.TourFilter


class TourLegsViewSet(viewsets.ReadOnlyModelViewSet):
  """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

  queryset = (
    db_models.TourLeg.objects.all()
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
  filterset_class = api_filters.TourLegFilter


class EventRunViewSet(viewsets.ReadOnlyModelViewSet):
  queryset = (
    db_models.Run.objects.all()
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
  filterset_class = api_filters.EventRunFilter


class LyricsViewSet(viewsets.ReadOnlyModelViewSet):
  queryset = db_models.Lyric.objects.all().select_related("song").order_by("song__name")
  serializer_class = api_serializers.LyricsSerializer


class SetlistNotesViewSet(viewsets.ReadOnlyModelViewSet):
  queryset = db_models.SetlistNote.objects.all().select_related(
    "setlist__song",
    "event__venue",
  )

  serializer_class = api_serializers.SetlistNotesSerializer
  filterset_class = api_filters.SetlistNoteFilter


class UpdatesViewSet(viewsets.ReadOnlyModelViewSet):
  queryset = db_models.Update.objects.all().order_by("-created_at", "-id")
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
      db_models.UserAttendedShow.objects.all().select_related(
        "user",
        "event",
      )
    ).order_by("-event__event_id")

  serializer_class = api_serializers.UserAttendedShowsSerializer
  filterset_class = api_filters.UserAttendedShowsFilter


class SetlistBreakdown(viewsets.ReadOnlyModelViewSet):
  """Return setlist breakdown by category with album completion status."""

  serializer_class = api_serializers.SetlistBreakdownSerializer
  ordering = ["-song_count", "total_setlist_songs"]

  def get_queryset(self):
    event_id = self.request.query_params.get("event")  # type: ignore
    event_filter = Q(set_name__in=db_models.SetType.valid_sets())

    if not event_id:
      raise ValidationError({"event": "This parameter is required."})

    event_filter = Q(
      Q(event_id=event_id) & Q(set_name__in=db_models.SetType.valid_sets()),
    )

    # Base setlist for this event (reused for total count and filtering)
    event_setlist = db_models.Setlist.objects.filter(
      event_filter,
    )

    # Total songs in entire setlist (for percentage calculations, etc.)
    total_setlist_songs = event_setlist.annotate(
      cnt=Count("id"),
    ).values("cnt")

    # Album songs subquery: songs from releases matching this category
    album_songs_subquery = (
      db_models.ReleaseTrack.objects.filter(
        release__name=OuterRef("song__category"),
      )
      .values("song_id")
      .order_by("position")
    )

    # Setlist songs subquery: songs from this event matching this category
    setlist_songs_subquery = (
      event_setlist.filter(
        song__category=OuterRef("song__category"),
      )
      .values("song_id")
      .order_by("song_num")
    )

    # Aggregate by category
    return (
      event_setlist.select_related("song", "event")
      .values(category=F("song__category"))
      .annotate(
        song_count=Count("song_id", distinct=True),  # songs in this category
        total_setlist_songs=SubqueryCount(
          total_setlist_songs,
        ),  # total songs in setlist
        songs=ArraySubquery(setlist_songs_subquery),
        category_slug=F("song__category_slug"),
        album_songs=ArraySubquery(album_songs_subquery),
      )
    )


class TypesViewSet(viewsets.ReadOnlyModelViewSet):
  queryset = db_models.Type.objects.all()
  serializer_class = api_serializers.TypesSerializer
  filterset_class = api_filters.TypeFilter


class EventTypesViewSet(viewsets.ReadOnlyModelViewSet):
  queryset = db_models.EventType.objects.all()
  serializer_class = api_serializers.EventTypeSerializer
  filterset_class = api_filters.EventTypeFilter


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
  queryset = db_models.Tag.objects.all()
  serializer_class = api_serializers.TagsSerializer
  filterset_class = api_filters.TagFilter


class EventTagsViewSet(viewsets.ReadOnlyModelViewSet):
  queryset = db_models.EventTag.objects.all()
  serializer_class = api_serializers.EventTagSerializer
  filterset_class = api_filters.EventTagFilter


class UserAlbumBreakdown(viewsets.ReadOnlyModelViewSet):
  serializer_class = api_serializers.UserAlbumBreakdownSerializer

  def get_queryset(self):
    user_id = self.request.query_params.get("user")  # type: ignore
    if not user_id:
      return db_models.Release.objects.none()

    # 1. Corrected Subquery: Group by song_id using values() BEFORE annotate()
    # DO NOT slice with [:1] here as it corrupts the Prefetch query grouping.
    times_seen_subquery = (
      db_models.Setlist.objects.filter(
        song_id=OuterRef("song_id"),
        event__user_event__user_id=user_id,
        set_name__in=db_models.SetType.valid_sets(),
      )
      .values("song_id")
      .annotate(cnt=Count("id"))
      .values("cnt")
    )

    # 2. Prefetch release tracks with annotated play count
    tracks_prefetch = Prefetch(
      "release_tracks",
      queryset=db_models.ReleaseTrack.objects.select_related("song")
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
      db_models.Release.objects.filter(type="Studio")
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
      db_models.Setlist.objects.filter(
        Q(set_name__in=db_models.SetType.valid_sets()) & Q(event__date__isnull=False),
      )
      .values(year=F("event__date__year"))
      .annotate(
        count=Count(
          "event__event_id",
          distinct=True,
          filter=Q(set_name__in=db_models.SetType.valid_sets()),
        ),
      )
    )

  serializer_class = api_serializers.YearSongBreakdownSerializer
  filterset_class = api_filters.YearSongBreakdownFilter


class ItemInsertLogViewSet(viewsets.ReadOnlyModelViewSet):
  queryset = db_models.ItemInsertLog.objects.all()
  serializer_class = api_serializers.ItemInsertLogSerializer


class ArticlesViewSet(viewsets.ModelViewSet):
  queryset = Article.objects.all()
  serializer_class = api_serializers.ArticlesSerializer
  lookup_field = (
    "slug"  # Use slug in URLs instead of PK (e.g. /api/articles/my-article-slug/)
  )

  filterset_class = api_filters.ArticleFilter


class ArticlesSearchViewSet(viewsets.ModelViewSet):
  queryset = Article.objects.all()
  serializer_class = api_serializers.ArticlesSearchSerializer
  lookup_field = (
    "slug"  # Use slug in URLs instead of PK (e.g. /api/articles/my-article-slug/)
  )

  filterset_class = api_filters.ArticleFilter
  pagination_class = StandardSetPagination


class BVEntriesViewSet(viewsets.ReadOnlyModelViewSet):
  queryset = Entry.objects.all().select_related("song", "event", "user")
  serializer_class = api_serializers.BVEntriesSerializer


class BVEntryCommentsViewSet(viewsets.ReadOnlyModelViewSet):
  queryset = EntryComment.objects.all().select_related(
    "entry",
    "user",
    "entry__song",
    "entry__event",
    "entry__user",
  )
  serializer_class = api_serializers.BVEntryCommentsSerializer
