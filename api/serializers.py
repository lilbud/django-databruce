import datetime

import markdown
import nh3
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from rest_framework import serializers

from bruceyversion.models import Entry, EntryComment
from databruce import models
from databruce.templatetags.filters import (
  event_id_format,
  event_note_format,
  format_fuzzy,
)
from library.models import Article, Collection

UserModel = get_user_model()

EVENT_TYPE_COLOR_MAP = {
  6: "danger",  # Cancelled
  16: "danger",  # No Gig
  21: "warning",  # Relocated
  22: "warning",  # Rescheduled
  23: "info",  # Rumored
}


class BaseSelect2Serializer(serializers.ModelSerializer):
  id = serializers.IntegerField(source="pk")
  text = serializers.SerializerMethodField()

  class Meta:
    fields = ["id", "text"]

  def __init__(self, *args, **kwargs) -> None:
    # Dynamically accept a text_field argument to specify the display field
    self.text_field = kwargs.pop("text_field", "name")
    super().__init__(*args, **kwargs)

  def get_text(self, obj):
    # Safely extract the string representation or attribute
    attr = getattr(obj, self.text_field, None)
    return str(attr) if attr is not None else str(obj)


def get_date_from_instance(obj) -> None | datetime.date | str:
  """Get event date from instance, creating date from id if needed."""
  event_id = getattr(obj, "event_id", None)
  date: datetime.date | None = getattr(obj, "date", None)

  if event_id is None:
    return None

  if not date:
    return datetime.datetime.strptime(format_fuzzy(event_id), "%Y-%m-%d").strftime(
      "%Y-%m-%d",
    )

  return date


class BaseSerializer(serializers.ModelSerializer):
  def __init__(self, *args, **kwargs) -> None:
    # Don't pass 'fields' up to the superclass
    include = kwargs.pop("include", None)
    exclude = kwargs.pop("exclude", None)
    super().__init__(*args, **kwargs)

    if include is not None:
      # Drop any fields that are not specified in the 'fields' argument
      allowed = set(include)
      existing = set(self.fields)
      for field_name in existing - allowed:
        self.fields.pop(field_name)

    if exclude is not None:
      # Drop any fields specifically specified in the 'exclude' argument
      for field_name in exclude:
        self.fields.pop(field_name, None)


class UsersSerializer(BaseSerializer):
  count = serializers.IntegerField(required=False, source="event_count")
  date_joined = serializers.SerializerMethodField()

  def get_date_joined(self, obj):
    return obj.date_joined.strftime("%Y-%m-%d")

  class Meta:
    model = UserModel
    fields = [
      "id",
      "username",
      "count",
      "is_staff",
      "date_joined",
      "uuid",
      "event_count",
    ]


class MinimalEventSerializer(BaseSerializer):
  date = serializers.SerializerMethodField()

  def get_date(self, obj):
    return get_date_from_instance(obj)

  class Meta:
    model = models.Event
    fields = ["date", "event_id", "early_late"]


class BandsSerializer(BaseSerializer):
  first_event = MinimalEventSerializer(required=False)
  last_event = MinimalEventSerializer(required=False)

  class Meta:
    model = models.Band
    fields = [
      "id",
      "slug",
      "name",
      "first_event",
      "last_event",
      "num_events",
      "bruce_band",
    ]


class ToursSerializer(BaseSerializer):
  first_event = MinimalEventSerializer(required=False)
  last_event = MinimalEventSerializer(required=False)
  band = BandsSerializer(required=False, include=["slug", "name"])

  class Meta:
    model = models.Tour
    fields = [
      "id",
      "slug",
      "name",
      "first_event",
      "last_event",
      "band",
      "num_events",
      "num_songs",
      "num_legs",
    ]


class TypesSerializer(BaseSerializer):
  class Meta:
    model = models.Type
    fields = ["id", "name", "slug"]


class EventTypeSerializer(BaseSerializer):
  type = TypesSerializer()

  class Meta:
    model = models.EventType
    fields = ["type"]


class TagsSerializer(BaseSerializer):
  class Meta:
    model = models.Tag
    fields = ["id", "name", "slug", "description"]


class EventSearchSerializer(BaseSerializer):
  date = serializers.SerializerMethodField(method_name="get_date")
  venue = serializers.CharField(
    required=False,
    source="venue.formatted",
    max_length=255,
  )
  city = serializers.CharField(
    required=False,
    source="venue.city.name",
    max_length=255,
  )
  artist = serializers.CharField(required=False, source="artist.name", max_length=255)
  type = serializers.CharField(required=False, source="type.name", max_length=255)
  run = serializers.CharField(required=False, source="run.name", max_length=255)
  rank = serializers.FloatField(required=False)

  def get_date(self, obj):
    return get_date_from_instance(obj)

  class Meta:
    model = models.Event
    fields = [
      "id",
      "event_id",
      "date",
      "venue",
      "city",
      "artist",
      "type",
      "rank",
      "run",
    ]


class IndexEventsSerializer(BaseSerializer):
  venue = serializers.CharField(
    source="venue.formatted",
    read_only=True,
    required=False,
  )

  date = serializers.CharField(max_length=255)

  class Meta:
    model = models.Event
    fields = ["event_id", "date", "venue", "early_late"]


class EventSetlistSerializer(BaseSerializer):
  song = serializers.CharField(source="song.name", max_length=255)

  highlight = serializers.SerializerMethodField()

  def get_highlight(self, obj):
    return bool(obj.debut or obj.premiere)

  class Meta:
    model = models.Setlist
    fields = ["song", "highlight", "set_name", "segue"]


class CountriesSerializer(BaseSerializer):
  first_event = MinimalEventSerializer(required=False)
  last_event = MinimalEventSerializer(required=False)

  class Meta:
    model = models.Country
    fields = ["id", "uuid", "name", "first_event", "last_event", "num_events"]


class StatesSerializer(BaseSerializer):
  first_event = MinimalEventSerializer(required=False)
  last_event = MinimalEventSerializer(required=False)
  country = CountriesSerializer(include=["name", "uuid"])

  class Meta:
    model = models.State
    fields = [
      "id",
      "uuid",
      "name",
      "country",
      "first_event",
      "last_event",
      "num_events",
    ]


class CitiesSerializer(BaseSerializer):
  state = StatesSerializer(required=False, include=["name", "uuid"])
  country = CountriesSerializer(include=["name", "uuid"])
  first_event = MinimalEventSerializer(required=False)

  class Meta:
    model = models.City
    fields = [
      "id",
      "name",
      "formatted",
      "uuid",
      "state",
      "country",
      "first_event",
      "last_event",
      "num_events",
    ]


class VenuesSerializer(BaseSerializer):
  name = serializers.SerializerMethodField()
  city = CitiesSerializer(required=False, include=["name", "uuid", "formatted"])
  state = StatesSerializer(
    required=False,
    source="city.state",
    include=["name", "uuid"],
  )

  country = CountriesSerializer(
    required=False,
    source="city.country",
    include=["name", "uuid"],
  )

  first_event = MinimalEventSerializer(required=False)
  last_event = MinimalEventSerializer(required=False)

  def get_name(self, obj):
    if obj.detail:
      return f"{obj.name}, {obj.detail}"

    return obj.name

  class Meta:
    model = models.Venue
    fields = [
      "id",
      "slug",
      "name",
      "city",
      "state",
      "country",
      "formatted",
      "first_event",
      "last_event",
      "num_events",
    ]


class EventsSerializer(BaseSerializer):
  date = serializers.SerializerMethodField(method_name="get_date")
  early_late = serializers.CharField(required=False, max_length=255)
  artist = BandsSerializer(required=False, include=["slug", "name"])
  tour = ToursSerializer(required=False, include=["slug", "name"])
  venue = VenuesSerializer(
    required=False,
    include=["slug", "name"],
  )

  city = serializers.CharField(
    required=False,
    source="venue.city.formatted",
    max_length=255,
  )
  leg = serializers.CharField(required=False, source="leg.name", max_length=255)

  rank = serializers.IntegerField(required=False)
  user_present = serializers.BooleanField(required=False)
  public = serializers.BooleanField(required=False)

  type = serializers.SerializerMethodField()

  def get_type(self, obj):
    return [
      {"name": type.name, "class": EVENT_TYPE_COLOR_MAP.get(type.id, "primary")}
      for type in obj.type.all()
    ]

  tags = serializers.SlugRelatedField(
    many=True,
    read_only=True,
    slug_field="name",
    required=False,
  )

  setlist = EventSetlistSerializer(
    source="setlist_event",
    read_only=True,
    many=True,
    required=False,
  )

  event_note = serializers.SerializerMethodField(required=False)

  def get_date(self, obj) -> None | datetime.date | str:
    return get_date_from_instance(obj)

  def get_event_note(self, obj) -> None | str:
    if obj.note in ["", None]:
      return None

    return event_note_format(obj.note)

  class Meta:
    model = models.Event
    fields = [
      "id",
      "date",
      "artist",
      "tour",
      "venue",
      "city",
      "leg",
      "rank",
      "user_present",
      "setlist",
      "event_note",
      "event_id",
      "title",
      "public",
      "early_late",
      "type",
      "tags",
    ]


class ArchiveLinksSerializer(BaseSerializer):
  event = EventsSerializer(include=["date", "event_id", "early_late"])

  class Meta:
    model = models.ArchiveLinks
    fields = ["id", "event", "url"]


class BootlegsSerializer(BaseSerializer):
  event = EventsSerializer(include=["date", "event_id", "early_late"])
  archive = ArchiveLinksSerializer(required=False)

  class Meta:
    model = models.Bootleg
    fields = ["id", "event", "archive", "title", "label", "source", "type"]


class EventRunSerializer(BaseSerializer):
  id = serializers.IntegerField(read_only=True)
  name = serializers.CharField(read_only=True, max_length=255)
  slug = serializers.CharField(read_only=True, max_length=255)
  band = serializers.CharField(source="band_name", read_only=True, max_length=255)
  venue = serializers.CharField(source="venue_name", read_only=True, max_length=255)
  city = serializers.CharField(source="city_name", read_only=True, max_length=255)
  num_events = serializers.IntegerField(read_only=True)
  num_songs = serializers.IntegerField(read_only=True)
  first_event = EventsSerializer(
    read_only=True,
    include=["date", "event_id", "early_late"],
  )
  last_event = EventsSerializer(
    read_only=True,
    include=["date", "event_id", "early_late"],
  )

  class Meta:
    model = models.Run
    fields = [
      "id",
      "name",
      "slug",
      "band",
      "venue",
      "city",
      "first_event",
      "last_event",
      "num_events",
      "num_songs",
    ]


class AdvSearchSerializer(BaseSerializer):
  date = serializers.SerializerMethodField(method_name="get_date")
  early_late = serializers.CharField(required=False, max_length=255)
  artist = BandsSerializer(required=False, include=["slug", "name"])
  tour = ToursSerializer(required=False, include=["slug", "name"])
  venue = VenuesSerializer(
    required=False,
    include=["slug", "name"],
  )
  city = serializers.CharField(
    required=False,
    source="venue.city.formatted",
    max_length=255,
  )
  leg = serializers.CharField(required=False, source="leg.name", max_length=255)
  has_setlist = serializers.SerializerMethodField()

  type = serializers.SerializerMethodField()

  def get_type(self, obj):
    return [
      {"name": type.name, "class": EVENT_TYPE_COLOR_MAP.get(type.id, "primary")}
      for type in obj.type.all()
    ]

  tags = serializers.SlugRelatedField(
    many=True,
    read_only=True,
    slug_field="name",
    required=False,
  )

  event_anchor = serializers.SerializerMethodField(required=False)
  setlist = EventSetlistSerializer(
    source="setlist_event",
    read_only=True,
    many=True,
    required=False,
  )

  def get_event_anchor(self, obj) -> str:
    return event_id_format(obj.event_id)

  def get_has_setlist(self, obj) -> bool:
    return bool(obj.setlist_event.exists())

  def get_date(self, obj) -> None | datetime.date | str:
    return get_date_from_instance(obj)

  def get_event_note(self, obj) -> None | str:
    if obj.note is None or obj.note == "":
      return None

    return event_note_format(obj.note)

  class Meta:
    model = models.Event
    fields = [
      "id",
      "date",
      "artist",
      "tour",
      "venue",
      "city",
      "leg",
      "has_setlist",
      "event_anchor",
      "setlist",
      "event_id",
      "title",
      "public",
      "early_late",
      "type",
      "tags",
      "note",
    ]


class ContinentsSerializer(BaseSerializer):
  class Meta:
    model = models.Continent
    fields = ["id", "name", "num_events"]


class CoversSerializer(BaseSerializer):
  class Meta:
    model = models.Cover
    fields = ["id", "url"]


class NugsSerializer(BaseSerializer):
  event = EventsSerializer(include=["event_id", "venue", "date", "early_late"])
  city = serializers.CharField(
    source="event.venue.city.formatted",
    read_only=True,
    max_length=255,
  )
  category = serializers.SerializerMethodField()
  article = serializers.SerializerMethodField(required=False)

  def get_article(self, obj):
    if not obj.article:
      return None

    return reverse_lazy("library:article_detail", args=[obj.article.slug])

  def get_category(self, obj):
    return obj.get_category_display()

  class Meta:
    model = models.NugsRelease
    fields = [
      "id",
      "event",
      "date",
      "city",
      "url",
      "name",
      "category",
      "article",
      "length",
    ]


class RelationAliasSerializer(serializers.ModelSerializer):
  type_display = serializers.CharField(
    source="get_type_display",
    read_only=True,
    max_length=255,
  )

  class Meta:
    model = models.RelationAlias
    fields = ["id", "name", "type", "type_display"]


class RelationsSerializer(BaseSerializer):
  first_event = EventsSerializer(
    required=False,
    include=["date", "event_id", "early_late"],
  )
  last_event = EventsSerializer(
    required=False,
    include=["date", "event_id", "early_late"],
  )

  aliases = serializers.SlugRelatedField(
    source="relation_alias",
    many=True,
    read_only=True,
    slug_field="name",
    required=False,
  )

  class Meta:
    model = models.Relation
    fields = [
      "id",
      "first_event",
      "last_event",
      "start_date",
      "instruments",
      "name",
      "aliases",
      "uuid",
      "num_events",
    ]


class OnstageSerializer(BaseSerializer):
  relation = RelationsSerializer(include=["uuid", "name"])
  band = BandsSerializer(required=False, include=["slug", "name"])

  class Meta:
    model = models.Onstage
    fields = ["relation", "band", "guest", "note"]


class OnstageBandSerializer(BaseSerializer):
  first = EventsSerializer(required=False, include=["date", "event_id", "early_late"])
  last = EventsSerializer(required=False, include=["date", "event_id", "early_late"])
  relation = RelationsSerializer(include=["id", "name", "instruments", "uuid"])

  class Meta:
    model = models.OnstageBandMember
    fields = ["id", "first", "last", "relation", "count"]


class ReleasesSerializer(BaseSerializer):
  event = EventsSerializer(required=False, include=["date", "event_id", "early_late"])
  length = serializers.TimeField(format="%H:%M:%S", required=False)  # type: ignore

  class Meta:
    model = models.Release
    fields = ["uuid", "name", "date", "length", "event", "type"]


class SongCategorySerializer(BaseSerializer):
  class Meta:
    model = models.SongCategory
    fields = ["id", "name", "slug"]


class SongsSerializer(BaseSerializer):
  first_event = EventsSerializer(
    required=False,
    include=["date", "event_id", "early_late"],
  )

  last_event = EventsSerializer(
    required=False,
    include=["date", "event_id", "early_late"],
  )

  has_lyrics = serializers.SerializerMethodField(required=False)
  album = ReleasesSerializer(required=False)

  category = SongCategorySerializer(required=False)

  def get_has_lyrics(self, obj):
    return obj.lyrics_song.exists()

  class Meta:
    model = models.Song
    fields = [
      "id",
      "name",
      "first_event",
      "last_event",
      "original_artist",
      "num_plays_public",
      "num_plays_private",
      "opener",
      "closer",
      "has_lyrics",
      "sort_song_name",
      "uuid",
      "slug",
      "original",
      "album",
      "category",
    ]


class SetlistStatsSerializer(BaseSerializer):
  ltp = EventsSerializer(required=False, include=["date", "event_id", "early_late"])

  class Meta:
    model = models.SetlistStats
    fields = ["ltp"]


class SetlistMobileSerializer(BaseSerializer):
  song = SongsSerializer(include=["name", "slug"])

  class Meta:
    model = models.Setlist
    fields = "__all__"


class SetlistNotesSerializer(BaseSerializer):
  event = EventsSerializer(include=["event_id", "date"], required=False)
  song = serializers.CharField(source="setlist.song.name", max_length=255)

  set_name = serializers.CharField(
    source="setlist.set_name",
    max_length=255,
    required=False,
  )

  class Meta:
    model = models.SetlistNote
    fields = ["event", "song", "set_name", "note"]


class SetlistSerializer(BaseSerializer):
  def to_representation(self, instance):
    if isinstance(self.instance, list) and not hasattr(self, "_event_cache"):
      event_ids = set()

      for obj in self.instance:
        if obj.ltp_id:
          event_ids.add(obj.ltp_id)

      events = models.Event.objects.filter(id__in=event_ids)
      self._event_cache = {
        e.id: EventsSerializer(e, include=["date", "event_id"]).data for e in events
      }

    return super().to_representation(instance)

  song = SongsSerializer(include=["name", "slug", "category"])

  last_event = serializers.SerializerMethodField(required=False)

  def get_last_event(self, obj):
    ltp_id = obj.ltp_id

    if ltp_id is None:
      return None

    if hasattr(self, "_event_cache"):
      return self._event_cache[ltp_id]

    return None

  notes = serializers.SlugRelatedField(
    source="setlist_notes",
    many=True,
    read_only=True,
    required=False,
    slug_field="note",
  )

  tour_num = serializers.SerializerMethodField(required=False)
  tour_total = serializers.SerializerMethodField(required=False)

  def get_tour_num(self, obj):
    if obj.tour_num == 0:
      return None

    return obj.tour_num

  def get_tour_total(self, obj):
    if obj.tour_total == 0:
      return None

    return obj.tour_total

  gap = serializers.SerializerMethodField()

  def get_gap(self, obj):
    if obj.last == 0:
      return None

    return obj.last

  class Meta:
    model = models.Setlist
    fields = [
      "song",
      "segue",
      "debut",
      "premiere",
      "set_name",
      "gap",
      "nobruce",
      "sign_request",
      "instrumental",
      "tour_num",
      "tour_total",
      "song_num",
      "position",
      "notes",
      "last_event",
    ]


class ReleaseDiscSerializer(BaseSerializer):
  class Meta:
    model = models.ReleaseDisc
    fields = ["id", "name", "uuid"]


class ReleaseTracksSerializer(BaseSerializer):
  event = EventsSerializer(required=False, include=["date", "event_id", "early_late"])
  disc = ReleaseDiscSerializer(required=False)
  song = SongsSerializer(
    include=[
      "id",
      "name",
      "slug",
    ],
  )
  length = serializers.TimeField(format="%M:%S", required=False)  # type: ignore

  class Meta:
    model = models.ReleaseTrack
    fields = [
      "event",
      "disc",
      "discnum",
      "track",
      "song",
      "length",
      "id",
      "uuid",
    ]


class SnippetSerializer(BaseSerializer):
  event = EventsSerializer(
    source="setlist.event",
    include=["event_id", "date", "early_late"],
  )

  artist = serializers.CharField(source="setlist.event.artist.name", max_length=255)
  venue = serializers.CharField(source="setlist.event.venue.name", max_length=255)
  city = serializers.CharField(source="setlist.event.venue.city", max_length=255)
  song = SongsSerializer(source="setlist.song", include=["name", "slug"])

  notes = serializers.SerializerMethodField()

  def get_notes(self, obj):
    if not obj.setlist.setlist_notes.exists():
      return None

    return list(
      {item.note for item in obj.setlist.setlist_notes.all() if item.note != ""},
    )

  class Meta:
    model = models.Snippet
    fields = ["event", "song", "venue", "notes", "city", "artist"]


class IncludedSerializer(serializers.ModelSerializer):
  count = serializers.IntegerField(read_only=True)
  snippet = serializers.SerializerMethodField(required=False)
  first_event = serializers.SerializerMethodField()
  last_event = serializers.SerializerMethodField()

  def to_representation(self, instance):
    if (
      isinstance(self.instance, list)
      and not hasattr(self, "_event_cache")
      and not hasattr(self, "_song_cache")
    ):
      event_ids = set()
      song_ids = set()

      for obj in self.instance:
        if obj["first_event"]:
          event_ids.add(obj["first_event"])
        if obj["last_event"]:
          event_ids.add(obj["last_event"])
        if obj["snippet_id"]:
          song_ids.add(obj["snippet_id"])

      events = models.Event.objects.filter(id__in=event_ids)
      songs = models.Song.objects.filter(id__in=song_ids)

      self._event_cache = {
        e.id: EventsSerializer(e, include=["date", "event_id", "early_late"]).data
        for e in events
      }

      self._song_cache = {
        s.id: SongsSerializer(s, include=["name", "slug"]).data for s in songs
      }

    return super().to_representation(instance)

  def get_first_event(self, obj):
    event_id = obj["first_event"]

    if hasattr(self, "_event_cache"):
      return self._event_cache.get(event_id)

    return None

  def get_last_event(self, obj):
    event_id = obj["last_event"]

    if hasattr(self, "_event_cache"):
      return self._event_cache.get(event_id)

    return None

  def get_snippet(self, obj):
    song_id = obj["snippet_id"]

    if hasattr(self, "_song_cache"):
      return self._song_cache.get(song_id)

    return None

  class Meta:
    model = models.Snippet
    fields = ["count", "snippet", "first_event", "last_event"]


class TourLegsSerializer(BaseSerializer):
  first_event = EventsSerializer(include=["date", "event_id", "early_late"])
  last_event = EventsSerializer(include=["date", "event_id", "early_late"])
  tour = serializers.CharField(source="tour.name", max_length=255)

  class Meta:
    model = models.TourLeg
    fields = [
      "id",
      "slug",
      "name",
      "tour",
      "first_event",
      "last_event",
      "num_events",
      "num_songs",
      "note",
    ]


class SongsPageSerializer(BaseSerializer):
  position = serializers.CharField(
    required=False,
  )

  event = EventsSerializer(
    include=["date", "event_id", "early_late", "artist", "venue", "tour"],
    required=False,
  )

  prev = SetlistSerializer(
    source="songs_page.prev",
    include=["id", "song", "segue"],
    required=False,
  )

  next = SetlistSerializer(
    source="songs_page.next",
    include=["id", "song", "segue"],
    required=False,
  )

  notes = serializers.SerializerMethodField(required=False)

  def get_notes(self, obj):
    if not obj.setlist_notes.exists():
      return None

    return list(
      {item.note for item in obj.setlist_notes.all() if item.note != ""},
    )

  gap = serializers.SerializerMethodField()

  def get_gap(self, obj):
    if obj.last == 0:
      return None

    return obj.last

  class Meta:
    model = models.Setlist
    fields = [
      # "id",
      "position",
      "prev",
      "next",
      "event",
      "gap",
      "segue",
      "debut",
      "premiere",
      "notes",
      "set_name",
    ]


class LyricsSerializer(BaseSerializer):
  song = serializers.CharField(source="song.name", max_length=255)
  language = serializers.SerializerMethodField()

  def get_language(self, obj):
    return obj.get_language_display()

  class Meta:
    model = models.Lyric
    fields = ["song", "version", "source", "language", "uuid"]


class SetlistEntrySerializer(BaseSerializer):
  event = EventsSerializer(
    include=["date", "event_id", "early_late"],
  )

  show_opener = SongsSerializer(include=["name", "slug"])
  s1_closer = SongsSerializer(include=["name", "slug"])
  s2_opener = SongsSerializer(include=["name", "slug"])
  main_closer = SongsSerializer(include=["name", "slug"])
  encore_opener = SongsSerializer(include=["name", "slug"])
  show_closer = SongsSerializer(include=["name", "slug"])

  class Meta:
    model = models.SetlistEntries
    fields = [
      "event",
      "show_opener",
      "s1_closer",
      "s2_opener",
      "main_closer",
      "encore_opener",
      "show_closer",
    ]


class SetlistSongsSerializer(BaseSerializer):
  count = serializers.IntegerField(required=False)
  song = serializers.SerializerMethodField(required=False)
  first_event = serializers.SerializerMethodField(required=False)
  last_event = serializers.SerializerMethodField(required=False)

  def to_representation(self, instance):
    if not hasattr(self, "_caches_initialized"):
      self._caches_initialized = True

      # Determine the list of items being serialized
      dataset = self.instance if isinstance(self.instance, list) else [self.instance]

      event_ids = set()
      song_ids = set()

      for obj in dataset:
        assert obj is not None
        if obj["first_event"]:
          event_ids.add(obj["first_event"])
        if obj["last_event"]:
          event_ids.add(obj["last_event"])
        if obj["song_id"]:
          song_ids.add(obj["song_id"])

      self._event_cache = {
        e.event_id: EventsSerializer(e, include=["date", "event_id", "early_late"]).data
        for e in models.Event.objects.filter(event_id__in=event_ids)
      }

      self._song_cache = {
        s["id"]: {
          "id": s["id"],
          "name": s["name"],
          "category": s["category__name"],
        }
        for s in models.Song.objects.filter(id__in=song_ids)
        .select_related("category")
        .values(
          "id",
          "name",
          "category__name",
        )
      }

    return super().to_representation(instance)

  def get_song(self, obj):
    return self._song_cache.get(obj["song_id"])

  def get_first_event(self, obj):
    return self._event_cache.get(obj["first_event"])

  def get_last_event(self, obj):
    return self._event_cache.get(obj["last_event"])

  class Meta:
    model = models.Setlist
    fields = [
      "song",
      "count",
      "first_event",
      "last_event",
    ]


class SetlistSongCountSerializer(BaseSerializer):
  count = serializers.IntegerField(required=False)
  song = serializers.SerializerMethodField(required=False)

  def to_representation(self, instance):
    # Initialize bulk caches ONCE on the parent serializer instance
    if not hasattr(self, "_caches_initialized"):
      self._caches_initialized = True

      dataset = self.instance if isinstance(self.instance, list) else [self.instance]

      song_ids = set()

      for obj in dataset:
        assert obj is not None
        if obj["song_id"]:
          song_ids.add(obj["song_id"])

      self._song_cache = {
        s["id"]: {
          "id": s["id"],
          "name": s["name"],
          "slug": s["slug"],
        }
        for s in models.Song.objects.filter(id__in=song_ids).values(
          "id",
          "name",
          "slug",
        )
      }

    return super().to_representation(instance)

  def get_song(self, obj):
    song_cache = getattr(self, "_song_cache", {})
    return song_cache.get(obj["song_id"])

  class Meta:
    model = models.Setlist
    fields = [
      "song",
      "count",
    ]


class UpdatesSerializer(BaseSerializer):
  created_at = serializers.SerializerMethodField(method_name="get_created")

  def get_created(self, obj):
    return obj.created_at.strftime("%Y-%m-%d")

  class Meta:
    model = models.Update
    fields = ["created_at", "item_id", "item", "value", "view", "msg"]


class UserAttendedShowsSerializer(BaseSerializer):
  event = EventsSerializer(
    include=["event_id", "date"],
  )

  user = UsersSerializer()

  class Meta:
    model = models.UserAttendedShow
    fields = ["event", "user"]


class SetlistBreakdownSerializer(BaseSerializer):
  total_setlist_songs = serializers.IntegerField(required=False)
  song_count = serializers.IntegerField(required=False)
  category = serializers.SerializerMethodField(required=False)
  album_complete = serializers.SerializerMethodField(required=False)
  album_in_order = serializers.SerializerMethodField(required=False)
  songs = serializers.SerializerMethodField(required=False)

  def to_representation(self, instance):
    # Initialize bulk caches ONCE on the parent serializer instance
    if not hasattr(self, "_caches_initialized"):
      self._caches_initialized = True

      # Determine the list of items being serialized
      dataset = self.instance if isinstance(self.instance, list) else [self.instance]

      song_ids = set()
      category_ids = set()

      for obj in dataset:
        assert obj is not None
        combined = (obj.get("songs") or []) + (obj.get("album_songs") or [])
        song_ids.update(combined)

        if obj.get("category"):
          category_ids.add(obj["category"])

      # Build data maps without repeatedly invoking full DRF serializer instances
      self._category_cache = {
        c["id"]: {"id": c["id"], "name": c["name"], "slug": c["slug"]}
        for c in models.SongCategory.objects.filter(
          id__in=category_ids,
        ).values("id", "name", "slug")
      }

      self._song_cache = {
        s["id"]: {
          "id": s["id"],
          "name": s["name"],
          "original_artist": s["original_artist"],
          "original": s["original"],
        }
        for s in models.Song.objects.filter(id__in=song_ids).values(
          "id",
          "name",
          "original_artist",
          "original",
        )
      }

    return super().to_representation(instance)

  def get_category(self, obj):
    return getattr(self, "_category_cache", {}).get(obj["category"])

  def get_songs(self, obj):
    song_cache = getattr(self, "_song_cache", {})
    return [song_cache[s] for s in obj.get("songs", []) if s in song_cache]

  def get_album_complete(self, obj):
    """Check if every song ID in album_songs is present in setlist_songs."""
    # Skip non-album categories
    if obj.get("category") in (8, 19):
      return False

    raw_album_songs = obj.get("album_songs") or []
    raw_setlist_songs = obj.get("songs") or []

    # Edge case: empty album is trivially complete
    if not raw_album_songs:
      return True

    # Edge case: no setlist songs means album cannot be complete
    if not raw_setlist_songs:
      return False

    # Standardize data types (cast all elements to int) to prevent type mismatch bugs
    try:
      album_set = {int(x) for x in raw_album_songs if x is not None}
      setlist_set = {int(x) for x in raw_setlist_songs if x is not None}
    except (ValueError, TypeError):
      album_set = set(raw_album_songs)
      setlist_set = set(raw_setlist_songs)

    if not album_set:
      return True

    # Check set containment (Order does not matter)
    return album_set.issubset(setlist_set)

  def get_album_in_order(self, obj):
    """Check if album songs present in the setlist appear in exact relative album sequence."""
    # Non-album categories can't be in order
    if obj.get("category") in (8, 19):
      return False

    album_songs = obj.get("album_songs") or []
    setlist_songs = obj.get("songs") or []

    if not album_songs or not setlist_songs:
      return False

    # Exclude intros, outros, or fillers that don't count against sequence continuity
    remove = {689, 1021, 514}
    filtered_setlist = [
      int(s) for s in setlist_songs if s is not None and int(s) not in remove
    ]

    if not filtered_setlist:
      return False

    # Build map of album song_id -> expected track position index
    album_order_map = {
      int(song_id): idx
      for idx, song_id in enumerate(album_songs)
      if song_id is not None
    }

    # Extract only the album songs that appeared in the setlist, keeping their setlist order
    played_album_songs = [
      album_order_map[s] for s in filtered_setlist if s in album_order_map
    ]

    # Must have played at least 2 album songs to establish a sequence
    if len(played_album_songs) < 2:
      return len(played_album_songs) == 1

    # Verify indices strictly increase (e.g., track 1 -> track 2 -> track 3)
    return all(
      played_album_songs[i] < played_album_songs[i + 1]
      for i in range(len(played_album_songs) - 1)
    )

  class Meta:
    model = models.Setlist
    fields = [
      "total_setlist_songs",
      "song_count",
      "songs",
      "category",
      "album_complete",
      "album_in_order",
    ]


class ReleaseTrackSongSerializer(serializers.ModelSerializer):
  """Serializes tracks on a release along with user-specific play count."""

  id = serializers.IntegerField(source="song.id")
  name = serializers.CharField(source="song.name", max_length=255)
  slug = serializers.CharField(source="song.slug", max_length=255)
  times_seen = serializers.IntegerField(default=0)

  class Meta:
    model = models.ReleaseTrack
    fields = ["id", "name", "slug", "times_seen"]


class UserAlbumBreakdownSerializer(serializers.ModelSerializer):
  songs = serializers.SerializerMethodField()
  user_album_count = serializers.SerializerMethodField()
  album_song_count = serializers.SerializerMethodField()
  album_percent = serializers.SerializerMethodField()

  class Meta:
    model = models.Release
    fields = [
      "id",
      "name",
      "slug",
      "songs",
      "user_album_count",
      "album_song_count",
      "album_percent",
    ]

  def _get_tracks(self, obj) -> list:
    """Helper to retrieve tracks queryset/list safely."""
    # Handles whether related_name returns a Manager or a single instance
    tracks = getattr(obj, "release_tracks", [])

    if hasattr(tracks, "all"):
      return list(tracks.all())  # type: ignore

    return list(tracks) if isinstance(tracks, (list, tuple)) else [tracks]

  def get_songs(self, obj) -> list[dict]:
    tracks = self._get_tracks(obj)
    return ReleaseTrackSongSerializer(tracks, many=True).data  # type: ignore

  def get_user_album_count(self, obj) -> int:
    tracks = self._get_tracks(obj)
    # Count distinct songs seen at least once (times_seen > 0)
    seen_song_ids = {
      track.song_id for track in tracks if getattr(track, "times_seen", 0) > 0
    }
    return len(seen_song_ids)

  def get_album_song_count(self, obj) -> int:
    tracks = self._get_tracks(obj)

    # Count total distinct songs on the album
    distinct_song_ids = {track.song_id for track in tracks if track.song_id}
    return len(distinct_song_ids)

  def get_album_percent(self, obj) -> float:
    total = self.get_album_song_count(obj)

    if not total:
      return 0.0

    seen = self.get_user_album_count(obj)
    return round((seen / total) * 100, 2)


class YearSongBreakdownSerializer(BaseSerializer):
  year = serializers.IntegerField()
  count = serializers.IntegerField()

  class Meta:
    model = models.Setlist
    fields = ["year", "count"]


class ItemInsertLogSerializer(serializers.ModelSerializer):
  # Generates a fully-resolved target URL by replacing {id} with source_id
  target_url = serializers.SerializerMethodField()

  class Meta:
    model = models.ItemInsertLog
    fields = [
      "id",
      "source_id",
      "item_name",
      "django_view",
      "target_url",
      "message",
      "source_created_at",
      "logged_at",
    ]

  def get_target_url(self, obj):
    if not obj.django_view:
      return None

    return f"{obj.django_view}{obj.source_id}"


class LibraryCollectionSerializer(serializers.ModelSerializer):
  class Meta:
    model = Collection
    fields = ["id", "name", "slug"]


class ArticlesSerializer(serializers.ModelSerializer):
  category = serializers.CharField(
    source="get_category_display",
    read_only=True,
  )

  collection = serializers.CharField(
    source="collection.name",
    read_only=True,
  )

  class Meta:
    model = Article
    fields = [
      "title",
      "author",
      "slug",
      "language",
      "published_at",
      "category",
      "source",
      "collection",
    ]


class ArticlesSearchSerializer(serializers.ModelSerializer):
  category = serializers.CharField(
    source="get_category_display",
    read_only=True,
  )

  collection = serializers.CharField(
    source="collection.name",
    read_only=True,
  )

  rank = serializers.FloatField(required=False)

  content = serializers.SerializerMethodField()

  def get_content(self, obj):
    raw_html = markdown.markdown(obj.content[:500])
    # 2. Define safe elements
    allowed_tags = [
      "p",
      "strong",
      "em",
      "h1",
      "h2",
      "h3",
      "h4",
      "ul",
      "ol",
      "li",
      "br",
      "code",
      "pre",
      "blockquote",
    ]

    # 3. Clean the HTML (strips script tags, onerror events, etc.)
    cleaned_html = nh3.clean(
      raw_html,
      tags=set(allowed_tags),
    )

    return mark_safe(cleaned_html)

  class Meta:
    model = Article
    fields = [
      "title",
      "author",
      "slug",
      "category",
      "collection",
      "content",
      "published_at",
      "rank",
    ]


class BVEntriesSerializer(serializers.ModelSerializer):
  song = serializers.CharField(source="song.name", max_length=255)
  event = EventsSerializer(include=["event_id", "date", "early_late"])
  user = UsersSerializer()

  class Meta:
    model = Entry
    fields = ["id", "song", "event", "user", "comment"]


class BVEntryCommentsSerializer(serializers.ModelSerializer):
  entry = BVEntriesSerializer()
  user = UsersSerializer()

  class Meta:
    model = EntryComment
    fields = ["id", "entry", "user", "comment"]
