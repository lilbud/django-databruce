import datetime
from zoneinfo import ZoneInfo

import strip_markdown
from django.contrib.auth import get_user_model
from rest_framework import serializers

from databruce import models
from databruce.templatetags.filters import format_fuzzy

UserModel = get_user_model()


class BaseSelect2Serializer(serializers.ModelSerializer):
  id = serializers.IntegerField(source="pk")
  text = serializers.SerializerMethodField()

  class Meta:
    fields = ["id", "text"]

  def __init__(self, *args, **kwargs):
    # Dynamically accept a text_field argument to specify the display field
    self.text_field = kwargs.pop("text_field", "name")
    super().__init__(*args, **kwargs)

  def get_text(self, obj):
    # Safely extract the string representation or attribute
    attr = getattr(obj, self.text_field, None)
    return str(attr) if attr is not None else str(obj)


def get_date_from_instance(obj):
  """Get event date from instance, creating date from id if needed."""
  event_id = getattr(obj, "event_id", None)
  date = getattr(obj, "date", None)

  if event_id is None:
    return None

  if not date:
    date = datetime.datetime.strptime(format_fuzzy(event_id), "%Y-%m-%d")

  return date.strftime("%Y-%m-%d")


def get_formatted_city(obj):
  try:
    if obj.state:
      if getattr(obj.country, "alpha_2", "").upper() == "US":
        return f"{obj.name}, {obj.state.abbrev}"

      return f"{obj.name}, {obj.state.abbrev}, {obj.country.name}"

    return f"{obj.name}, {obj.country.name}"
  except AttributeError:
    return None


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


class MinimalStatesSerializer(BaseSerializer):
  class Meta:
    model = models.States
    fields = ["name", "abbrev", "uuid"]


class MinimalCountriesSerializer(BaseSerializer):
  class Meta:
    model = models.Countries
    fields = ["name", "uuid"]


class MinimalBandsSerializer(BaseSerializer):
  class Meta:
    model = models.Bands
    fields = ["name", "uuid"]


class MinimalCitiesSerializer(BaseSerializer):
  formatted = serializers.SerializerMethodField()

  def get_formatted(self, obj):
    return get_formatted_city(obj)

  class Meta:
    model = models.Cities
    fields = ["name", "formatted", "uuid"]


class MinimalVenuesTextSerializer(BaseSerializer):
  class Meta:
    model = models.VenuesText
    fields = ["formatted", "location"]


class MinimalVenuesSerializer(BaseSerializer):
  class Meta:
    model = models.Venues
    fields = [
      "name",
      "detail",
      "uuid",
    ]


class MinimalToursSerializer(BaseSerializer):
  class Meta:
    model = models.Tours
    fields = ["name", "uuid"]


class MinimalUserSerializer(BaseSerializer):
  class Meta:
    model = UserModel
    fields = ["id", "username", "uuid"]


class MinimalEventSerializer(BaseSerializer):
  date = serializers.SerializerMethodField()

  def get_date(self, obj):
    return get_date_from_instance(obj)

  class Meta:
    model = models.Events
    fields = ["date", "event_id"]


class MinimalTourLegsSerializer(BaseSerializer):
  class Meta:
    model = models.TourLegs
    fields = ["name", "uuid"]


class MinimalEventRunSerializer(BaseSerializer):
  class Meta:
    model = models.Runs
    fields = ["name", "uuid"]


class MinimalRelationsSerializer(BaseSerializer):
  class Meta:
    model = models.Relations
    fields = ["name", "instruments", "uuid"]


class MinimalSongsSerializer(BaseSerializer):
  first_event = MinimalEventSerializer(required=False)
  last_event = MinimalEventSerializer(required=False)

  class Meta:
    model = models.Songs
    fields = [
      "id",
      "name",
      "album",
      "category_slug",
      "slug",
      "category",
      "uuid",
      "original",
      "original_artist",
      "num_plays_public",
      "first_event",
      "last_event",
    ]


class MinimalSetlistSerializer(BaseSerializer):
  song = MinimalSongsSerializer()

  class Meta:
    model = models.Setlists
    fields = ["id", "event_id", "song", "set_name", "uuid"]


class MinimalOnstageSerializer(BaseSerializer):
  class Meta:
    model = models.Onstage
    fields = ["relation_id", "uuid"]


class MinimalArchiveLinksSerializer(BaseSerializer):
  class Meta:
    model = models.ArchiveLinks
    fields = ["id", "url", "uuid"]


class MinimalEventTypeSerializer(BaseSerializer):
  class Meta:
    model = models.EventTypes
    fields = ["id", "name"]


class StatesSerializer(BaseSerializer):
  first_event = MinimalEventSerializer(required=False)
  last_event = MinimalEventSerializer(required=False)
  country = MinimalCountriesSerializer()

  class Meta:
    model = models.States
    fields = [
      "id",
      "uuid",
      "name",
      "country",
      "first_event",
      "last_event",
      "num_events",
    ]


class CountriesSerializer(BaseSerializer):
  first_event = MinimalEventSerializer(required=False)
  last_event = MinimalEventSerializer(required=False)

  class Meta:
    model = models.Countries
    fields = ["id", "uuid", "name", "first_event", "last_event", "num_events"]


class CitiesSerializer(BaseSerializer):
  state = MinimalStatesSerializer(required=False)
  country = MinimalCountriesSerializer()
  first_event = MinimalEventSerializer(required=False)
  last_event = MinimalEventSerializer(required=False)
  formatted = serializers.SerializerMethodField()

  def get_formatted(self, obj):
    return get_formatted_city(obj)

  class Meta:
    model = models.Cities
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


class BandsSerializer(BaseSerializer):
  first_event = MinimalEventSerializer(required=False)
  last_event = MinimalEventSerializer(required=False)

  class Meta:
    model = models.Bands
    fields = [
      "id",
      "uuid",
      "name",
      "first_event",
      "last_event",
      "num_events",
      "springsteen_band",
    ]


class VenuesSerializer(BaseSerializer):
  name = serializers.SerializerMethodField()
  city = MinimalCitiesSerializer(required=False)
  state = MinimalStatesSerializer(required=False, source="city.state")
  country = MinimalCountriesSerializer(required=False, source="city.country")
  first_event = MinimalEventSerializer(required=False)
  last_event = MinimalEventSerializer(required=False)
  formatted = serializers.CharField(
    source="venues_text.formatted",
    required=False,
    max_length=255,
  )

  def get_name(self, obj):
    if obj.detail:
      return f"{obj.name}, {obj.detail}"

    return obj.name

  class Meta:
    model = models.Venues
    fields = [
      "id",
      "uuid",
      "name",
      "city",
      "state",
      "country",
      "formatted",
      "first_event",
      "last_event",
      "num_events",
    ]


class EventRunSerializer(BaseSerializer):
  band = MinimalBandsSerializer()
  venue = MinimalVenuesSerializer(include=["uuid", "name"])
  city = serializers.CharField(source="venue.city", required=False, max_length=255)
  first_event = MinimalEventSerializer(required=False, include=["event_id", "date"])
  last_event = MinimalEventSerializer(required=False, include=["event_id", "date"])

  class Meta:
    model = models.Runs
    fields = [
      "id",
      "name",
      "band",
      "venue",
      "city",
      "first_event",
      "last_event",
      "num_events",
      "num_songs",
      "uuid",
    ]


class IndexSerializer(BaseSerializer):
  date = serializers.SerializerMethodField(method_name="get_date")
  venue = VenuesSerializer()

  def get_date(self, obj):
    return get_date_from_instance(obj)

  class Meta:
    model = models.Events
    fields = ["id", "event_id", "date", "venue"]


class ToursSerializer(BaseSerializer):
  first_event = MinimalEventSerializer(required=False)
  last_event = MinimalEventSerializer(required=False)
  band = MinimalBandsSerializer(required=False)

  class Meta:
    model = models.Tours
    fields = [
      "id",
      "uuid",
      "name",
      "first_event",
      "last_event",
      "band",
      "num_events",
      "num_songs",
      "num_legs",
    ]


class OnstageSerializer(BaseSerializer):
  relation = MinimalRelationsSerializer(include=["uuid", "name"])
  band = MinimalBandsSerializer(required=False)

  class Meta:
    model = models.Onstage
    fields = ["relation", "band", "guest", "note"]


class TypesSerializer(BaseSerializer):
  class Meta:
    model = models.Types
    fields = ["id", "name", "slug"]


class EventTypeSerializer(BaseSerializer):
  type = TypesSerializer()

  class Meta:
    model = models.EventTypes
    fields = ["type"]


class TagsSerializer(BaseSerializer):
  class Meta:
    model = models.Tags
    fields = ["id", "name", "slug", "description"]


class EventTagSerializer(BaseSerializer):
  event = MinimalEventSerializer()
  tag = TagsSerializer()

  class Meta:
    model = models.EventTags
    fields = ["id", "event", "tag"]


class EventSearchSerializer(BaseSerializer):
  date = serializers.SerializerMethodField(method_name="get_date")
  venue = serializers.CharField(
    required=False,
    source="venue.venues_text.formatted",
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
    model = models.Events
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


class IndexSetlistSerializer(BaseSerializer):
  song = MinimalSongsSerializer(include=["name", "uuid"])
  notes = serializers.SlugRelatedField(
    source="setlist_notes",
    many=True,
    read_only=True,
    slug_field="note",
  )

  class Meta:
    model = models.Setlists
    fields = [
      "song",
      "song_num",
      "position",
      "instrumental",
      "sign_request",
      "nobruce",
      "premiere",
      "debut",
      "last",
      "notes",
      "set_name",
      "segue",
    ]


class IndexEventsSerializer(BaseSerializer):
  # 1. Change venue to a SerializerMethodField
  venue = serializers.SlugRelatedField(
    source="venue.venues_text",
    slug_field="formatted",
    read_only=True,
    required=False,
  )
  date = serializers.CharField(max_length=255)

  class Meta:
    model = models.Events
    fields = ["event_id", "date", "venue", "early_late"]


class EventTypesSerializer(BaseSerializer):
  event = MinimalEventSerializer()
  type = TypesSerializer()

  class Meta:
    model = models.EventTypes
    fields = ["id", "name", "slug"]


class EventsSerializer(BaseSerializer):
  date = serializers.SerializerMethodField(method_name="get_date")
  early_late = serializers.CharField(required=False, max_length=255)
  artist = MinimalBandsSerializer(required=False)
  tour = MinimalToursSerializer(required=False)
  venue = MinimalVenuesSerializer(
    required=False,
    include=["uuid", "name"],
  )

  city = serializers.SerializerMethodField(required=False)

  def get_city(self, obj):
    try:
      return get_formatted_city(obj.venue.city)
    except AttributeError:
      return None

  leg = serializers.CharField(required=False, source="leg.name", max_length=255)
  has_setlist = serializers.SerializerMethodField()

  rank = serializers.IntegerField(required=False)
  event_status = serializers.BooleanField(required=False)
  public = serializers.BooleanField(required=False)

  type = serializers.SlugRelatedField(
    many=True,
    read_only=True,
    slug_field="name",
    required=False,
  )

  tags = serializers.SlugRelatedField(
    many=True,
    read_only=True,
    slug_field="name",
    required=False,
  )

  def get_has_setlist(self, obj):
    return bool(obj.setlist_event.exists())

  def get_date(self, obj):
    return get_date_from_instance(obj)

  class Meta:
    model = models.Events
    fields = [
      "date",
      "artist",
      "tour",
      "venue",
      "city",
      "leg",
      "has_setlist",
      # "setlist",
      "rank",
      "event_status",
      "event_id",
      "title",
      "public",
      "early_late",
      "type",
      "tags",
      "note",
      # "bands",
      # "relations",
    ]


class AdvSearchSerializer(BaseSerializer):
  date = serializers.SerializerMethodField(method_name="get_date")
  early_late = serializers.CharField(required=False, max_length=255)
  artist = MinimalBandsSerializer(required=False)
  tour = MinimalToursSerializer(required=False)
  venue = MinimalVenuesSerializer(
    required=False,
    include=["uuid", "name"],
  )
  city = serializers.SerializerMethodField(required=False)

  def get_city(self, obj):
    return get_formatted_city(obj.venue.city)

  leg = serializers.CharField(required=False, source="leg.name", max_length=255)
  has_setlist = serializers.SerializerMethodField()

  type = serializers.SlugRelatedField(
    many=True,
    read_only=True,
    slug_field="name",
    required=False,
  )

  tags = serializers.SlugRelatedField(
    many=True,
    read_only=True,
    slug_field="name",
    required=False,
  )

  rank = serializers.IntegerField(required=False)
  event_status = serializers.BooleanField(required=False)
  public = serializers.BooleanField(required=False)

  def get_has_setlist(self, obj):
    return obj.setlist_certainty != "Unknown"

  def get_date(self, obj):
    return get_date_from_instance(obj)

  class Meta:
    model = models.Events
    fields = [
      "date",
      "artist",
      "tour",
      "venue",
      "city",
      "leg",
      "has_setlist",
      "rank",
      "event_status",
      "event_id",
      "title",
      "public",
      "early_late",
      "type",
      "tags",
      "note",
    ]


class ArchiveLinksSerializer(BaseSerializer):
  event = MinimalEventSerializer()

  class Meta:
    model = models.ArchiveLinks
    fields = ["id", "event", "url"]


class BootlegsSerializer(BaseSerializer):
  class Meta:
    model = models.Bootlegs
    fields = "__all__"


class ContinentsSerializer(BaseSerializer):
  class Meta:
    model = models.Continents
    fields = "__all__"


class CoversSerializer(BaseSerializer):
  class Meta:
    model = models.Covers
    fields = ["id", "url"]


class NugsSerializer(BaseSerializer):
  date = serializers.SerializerMethodField()
  event = EventsSerializer(include=["id", "event_id", "venue", "date"])
  city = MinimalCitiesSerializer(required=False, source="event.venue.city")

  def get_date(self, obj):
    try:
      return {
        "date": obj.date.strftime("%Y-%m-%d [%a]"),
        "time": obj.date.astimezone(ZoneInfo("UTC")).strftime(
          "%I:%M:%S %p",
        ),
      }
    except AttributeError:
      return None

  class Meta:
    model = models.NugsReleases
    fields = "__all__"


class RelationsSerializer(BaseSerializer):
  first_event = MinimalEventSerializer(required=False)
  last_event = MinimalEventSerializer(required=False)
  aliases = serializers.ListField(required=False)
  nicknames = serializers.ListField(required=False)
  birthday = serializers.SerializerMethodField()

  def get_birthday(self, obj):
    try:
      return obj.start_date.strftime("%Y-%m-%d")
    except AttributeError:
      return None

  class Meta:
    model = models.Relations
    fields = [
      "id",
      "first_event",
      "last_event",
      "start_date",
      "birthday",
      "instruments",
      "name",
      "aliases",
      "nicknames",
      "uuid",
      "num_events",
    ]


class OnstageBandSerializer(BaseSerializer):
  first = MinimalEventSerializer()
  last = MinimalEventSerializer()
  relation = RelationsSerializer(include=["id", "name", "instruments", "uuid"])

  class Meta:
    model = models.OnstageBandMembers
    fields = "__all__"


class ReleasesSerializer(BaseSerializer):
  event = MinimalEventSerializer(required=False)
  length = serializers.TimeField(format="%H:%M:%S", required=False)  # type: ignore
  month_day = serializers.SerializerMethodField()

  def get_month_day(self, obj):
    return obj.date.strftime("%m-%d")

  class Meta:
    model = models.Releases
    fields = ["uuid", "name", "date", "length", "event", "month_day", "type"]


class SongsSerializer(BaseSerializer):
  first_event = MinimalEventSerializer()
  last_event = MinimalEventSerializer()
  has_lyrics = serializers.SerializerMethodField(required=False)

  def get_has_lyrics(self, obj):
    return obj.lyrics_song.exists()

  class Meta:
    model = models.Songs
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
      "category",
      "has_lyrics",
      "sort_song_name",
      "uuid",
      "slug",
      "original",
    ]


class SetlistStatsSerializer(BaseSerializer):
  ltp = MinimalEventSerializer()

  class Meta:
    model = models.SetlistStats
    fields = "__all__"


class SetlistMobileSerializer(BaseSerializer):
  song = MinimalSongsSerializer(include=["name", "uuid", "slug"])
  # notes = serializers.SerializerMethodField()

  # def get_notes(self, obj):
  #     if not obj.setlist_notes.exists():
  #         return None

  #     return "; ".join(
  #         list(
  #             filter(None, [item.note for item in obj.setlist_notes.all()]),
  #         ),
  #     )

  class Meta:
    model = models.Setlists
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
    model = models.SetlistNotes
    fields = ["event", "song", "set_name", "note"]


class SetlistSerializer(BaseSerializer):
  song = MinimalSongsSerializer(include=["name", "uuid", "category_slug", "slug"])
  last_event = MinimalEventSerializer(
    source="ltp",
    required=False,
    include=["date", "event_id"],
  )

  notes = serializers.SlugRelatedField(
    source="setlist_notes",
    many=True,
    read_only=True,
    required=False,
    slug_field="note",
  )

  gap = serializers.SerializerMethodField()

  def get_gap(self, obj):
    if obj.last == 0:
      return None

    return obj.last

  class Meta:
    model = models.Setlists
    fields = [
      "song",
      "ltp",
      "segue",
      "debut",
      "premiere",
      "set_name",
      "gap",
      "nobruce",
      "sign_request",
      "instrumental",
      "id",
      "tour_num",
      "tour_total",
      "song_num",
      "position",
      "uuid",
      "notes",
      "last_event",
    ]


class ReleaseDiscSerializer(BaseSerializer):
  class Meta:
    model = models.ReleaseDiscs
    fields = ["id", "name", "uuid"]


class ReleaseTracksSerializer(BaseSerializer):
  event = MinimalEventSerializer(required=False)
  disc = ReleaseDiscSerializer(required=False)
  song = SongsSerializer(
    include=[
      "id",
      "name",
      "uuid",
    ],
  )
  length = serializers.TimeField(format="%M:%S", required=False)  # type: ignore

  class Meta:
    model = models.ReleaseTracks
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


class SetlistFilterSerializer(BaseSerializer):
  count = serializers.IntegerField()
  song = MinimalSongsSerializer()

  class Meta:
    model = models.Setlists
    fields = "__all__"


class SnippetSerializer(BaseSerializer):
  event = EventsSerializer(
    source="setlist.event",
    include=["event_id", "artist", "date"],
  )

  venue = MinimalVenuesSerializer(
    include=["uuid", "name"],
    source="setlist.event.venue",
  )

  song = MinimalSongsSerializer(source="setlist.song")

  notes = serializers.SerializerMethodField()

  def get_notes(self, obj):
    if not obj.setlist.setlist_notes.exists():
      return None

    return list(
      {item.note for item in obj.setlist.setlist_notes.all() if item.note != ""},
    )

  class Meta:
    model = models.Snippets
    fields = ["event", "song", "venue", "notes"]


class IncludedSerializer(BaseSerializer):
  count = serializers.IntegerField(required=False)

  event_map = {
    s.event_id: MinimalEventSerializer(s).data for s in models.Events.objects.all()
  }

  song_map = {
    s.id: MinimalSongsSerializer(
      s,
      include=["uuid", "name", "category", "original"],
    ).data
    for s in models.Songs.objects.all()
  }

  first_event = serializers.SerializerMethodField()
  last_event = serializers.SerializerMethodField()
  snippet = serializers.SerializerMethodField()

  def get_snippet(self, obj):
    return self.song_map[obj["snippet_id"]]

  def get_first_event(self, obj):
    return self.event_map[obj["first_event"]]

  def get_last_event(self, obj):
    return self.event_map[obj["last_event"]]

  class Meta:
    model = models.Snippets
    fields = [
      "count",
      "snippet",
      "first_event",
      "last_event",
    ]


class TourLegsSerializer(BaseSerializer):
  first_event = MinimalEventSerializer()
  last_event = MinimalEventSerializer()
  tour = MinimalToursSerializer()

  class Meta:
    model = models.TourLegs
    fields = [
      "id",
      "uuid",
      "name",
      "tour",
      "first_event",
      "last_event",
      "num_events",
      "num_songs",
      "note",
    ]


class SongsPageSerializer(BaseSerializer):
  # id = serializers.IntegerField(source="id_id")
  id = SetlistSerializer(
    include=["set_name", "position", "gap", "debut", "premiere"],
  )

  event = EventsSerializer(
    source="id.event",
    include=["id", "event_id", "venue", "artist", "date", "tour", "public"],
  )

  stats = SetlistStatsSerializer(
    required=False,
    read_only=True,
    source="id.setlist_stats",
    exclude=["ltp"],
    include=["gap", "debut", "premiere"],
  )

  position = serializers.CharField(
    required=False,
    source="id.position",
  )

  set_name = serializers.CharField(
    source="id.set_name",
  )

  prev = SetlistSerializer(
    include=["id", "segue", "song"],
    read_only=True,
    required=False,
  )

  next = SetlistSerializer(
    include=["id", "segue", "song"],
    read_only=True,
    required=False,
  )

  notes = serializers.SerializerMethodField()

  def get_notes(self, obj):
    if not obj.id.setlist_notes.exists():
      return None

    return list(
      {item.note for item in obj.id.setlist_notes.all() if item.note != ""},
    )

  class Meta:
    model = models.SongsPage
    fields = [
      "id",
      "stats",
      "event",
      "position",
      "prev",
      "next",
      "notes",
      "set_name",
    ]


class LyricsSerializer(BaseSerializer):
  song = serializers.CharField(source="song.name", max_length=255)

  class Meta:
    model = models.Lyrics
    fields = ["song", "version", "source", "language", "note", "uuid", "translator"]


class SetlistEntrySerializer(BaseSerializer):
  event = EventsSerializer(
    include=["date", "event_id"],
  )
  show_opener = MinimalSongsSerializer(include=["uuid", "name"])
  s1_closer = MinimalSongsSerializer(include=["uuid", "name"])
  s2_opener = MinimalSongsSerializer(include=["uuid", "name"])
  main_closer = MinimalSongsSerializer(include=["uuid", "name"])
  encore_opener = MinimalSongsSerializer(include=["uuid", "name"])
  show_closer = MinimalSongsSerializer(include=["uuid", "name"])

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


# class SetlistSongsSerializer(BaseSerializer):
#     count = serializers.IntegerField(required=False)
#     song = serializers.SerializerMethodField(required=False)
#     first_event = serializers.SerializerMethodField(required=False)
#     last_event = serializers.SerializerMethodField(required=False)

#     @cached_property
#     def event_map(self):
#         return {
#             s.event_id: MinimalEventSerializer(s).data
#             for s in models.Events.objects.all()
#         }

#     @cached_property
#     def song_map(self):
#         """Will ONLY run the first time a song lookup is requested.

#         completely bypassing Django system checks and startup freezes.
#         """
#         return {
#             s.id: MinimalSongsSerializer(
#                 s,
#                 include=[
#                     "uuid",
#                     "name",
#                     "category",
#                     "original",
#                     "num_plays_public",
#                 ],
#             ).data
#             for s in models.Songs.objects.all()
#         }

#     def get_song(self, obj):
#         # Access via self.song_map (cached_property attaches to the instance)
#         return self.song_map[obj["song_id"]]

#     def get_first_event(self, obj):
#         return self.event_map[obj["first_event"]]

#     def get_last_event(self, obj):
#         return self.event_map[obj["last_event"]]

#     class Meta:
#         model = models.Setlists
#         fields = [
#             "song",
#             "count",
#             "first_event",
#             "last_event",
#         ]


class SetlistSongsSerializer(BaseSerializer):
  count = serializers.IntegerField(required=False)
  song = serializers.SerializerMethodField(required=False)
  first_event = serializers.SerializerMethodField(required=False)
  last_event = serializers.SerializerMethodField(required=False)

  def to_representation(self, instance):
    if not hasattr(self, "_page_maps_loaded"):
      page_data = (
        self.parent.instance
        if self.parent and hasattr(self.parent, "instance")
        else [instance]
      )

      song_ids = {item["song_id"] for item in page_data if "song_id" in item}  # type: ignore
      event_ids = {
        e_id
        for item in page_data  # type: ignore
        for e_id in (item.get("first_event"), item.get("last_event"))
        if e_id
      }

      songs = models.Songs.objects.filter(id__in=song_ids)
      events = models.Events.objects.filter(event_id__in=event_ids)

      self._song_map = {
        s.id: MinimalSongsSerializer(
          s,
          include=[
            "uuid",
            "name",
            "category",
            "original",
          ],
        ).data
        for s in songs
      }
      self._event_map = {e.event_id: MinimalEventSerializer(e).data for e in events}
      self._page_maps_loaded = True

    return super().to_representation(instance)

  def get_song(self, obj):
    return self._song_map.get(obj["song_id"])

  def get_first_event(self, obj):
    return self._event_map.get(obj["first_event"])

  def get_last_event(self, obj):
    return self._event_map.get(obj["last_event"])

  class Meta:
    model = models.Setlists
    fields = [
      "song",
      "count",
      "first_event",
      "last_event",
    ]


class UpdatesSerializer(BaseSerializer):
  created_at = serializers.SerializerMethodField(method_name="get_created")

  def get_created(self, obj):
    return obj.created_at.strftime("%Y-%m-%d")

  class Meta:
    model = models.Updates
    fields = ["created_at", "item_id", "item", "value", "view", "msg"]


class UsersSerializer(BaseSerializer):
  event_count = serializers.IntegerField()
  user_slug = serializers.CharField(max_length=255)

  date_joined = serializers.SerializerMethodField()

  def get_date_joined(self, obj):
    return obj.date_joined.strftime("%Y-%m-%d")

  class Meta:
    model = UserModel
    fields = [
      "id",
      "username",
      "user_slug",
      "event_count",
      "is_staff",
      "date_joined",
      "uuid",
    ]


class UserAttendedShowsSerializer(BaseSerializer):
  event = EventsSerializer(
    include=["event_id", "date"],
  )

  user = MinimalUserSerializer()

  class Meta:
    model = models.UserAttendedShows
    fields = ["event", "user"]


class SetlistBreakdownSerializer(BaseSerializer):
  total_setlist_songs = serializers.IntegerField(required=False)
  song_count = serializers.IntegerField(required=False)
  category = serializers.CharField(required=False, max_length=255)
  category_slug = serializers.CharField(required=False, max_length=255)

  songs_map = {
    s.id: MinimalSongsSerializer(
      s,
      include=["id", "name", "original_artist", "original"],
    ).data
    for s in models.Songs.objects.all()
  }

  album_complete = serializers.SerializerMethodField(required=False)

  def get_album_complete(self, obj):
    """Check if all songs on album are present in setlist in order."""
    # intros/outros that shouldn't be counted in setlist for album check
    remove = [689, 1021, 514]

    # Skip non-album categories
    if obj["category"] in ("Covers", "Originals"):
      return False

    album_songs = obj.get("album_songs", [])
    setlist_songs = obj.get("songs", [])

    print(len(album_songs), len(setlist_songs))

    # Edge case: empty album is trivially complete
    if not album_songs:
      return True

    # Edge case: no setlist songs to check
    if not setlist_songs:
      return False

    ignore_set = set(remove)

    filtered_setlist = [
      song_id for song_id in setlist_songs if song_id not in ignore_set
    ]

    if not filtered_setlist:
      return False

    # Check if album songs appear in order within filtered setlist
    album_idx = 0

    if set(setlist_songs).issubset(set(album_songs)) and len(setlist_songs) == len(
      album_songs,
    ):
      return True

    # Check if we found all album songs in order
    return album_idx == len(album_songs)

  songs = serializers.SerializerMethodField(required=False)

  def get_songs(self, obj):
    try:
      return [self.songs_map[s] for s in obj["songs"]]
    except KeyError:
      return []

  class Meta:
    model = models.Setlists
    fields = [
      "total_setlist_songs",
      "song_count",
      "songs",
      "category",
      "album_complete",
      "category_slug",
    ]


# class SetlistBreakdownSerializer(BaseSerializer):
#   total_setlist_songs = serializers.IntegerField(required=False)
#   song_count = serializers.IntegerField(required=False)
#   category = serializers.CharField(required=False, max_length=255)
#   category_slug = serializers.CharField(required=False, max_length=255)
#   album_complete = serializers.SerializerMethodField(required=False)
#   songs = serializers.SerializerMethodField(required=False)

#   def get_songs(self, obj):
#     song_ids = obj.get("songs") or []
#     if not song_ids:
#       return []

#     # Fetch only the relevant song records for this aggregated group
#     songs_qs = models.Songs.objects.filter(id__in=song_ids)
#     return MinimalSongsSerializer(
#       songs_qs,
#       many=True,
#       include=["id", "name", "original_artist", "original"],
#     ).data

#   def get_album_complete(self, obj):
#     remove = {689, 1021, 514}

#     if obj.get("category") in ("Covers", "Originals"):
#       return False

#     album_songs = obj.get("album_songs") or []
#     setlist_songs = obj.get("songs") or []

#     if not album_songs:
#       return True
#     if not setlist_songs:
#       return False

#     filtered_setlist = [s for s in setlist_songs if s not in remove]
#     if not filtered_setlist:
#       return False

#     return set(setlist_songs).issubset(set(album_songs)) and len(
#       setlist_songs,
#     ) == len(album_songs)

#   class Meta:
#     model = models.Setlists
#     fields = [
#       "total_setlist_songs",
#       "song_count",
#       "songs",
#       "category",
#       "album_complete",
#       "category_slug",
#     ]


class ReleaseTrackSongSerializer(serializers.ModelSerializer):
  """Serializes tracks on a release along with user-specific play count."""

  id = serializers.IntegerField(source="song.id")
  name = serializers.CharField(source="song.name", max_length=255)
  slug = serializers.CharField(source="song.slug", max_length=255)
  times_seen = serializers.IntegerField(default=0)

  class Meta:
    model = models.ReleaseTracks
    fields = ["id", "name", "slug", "times_seen"]


class UserAlbumBreakdownSerializer(serializers.ModelSerializer):
  songs = serializers.SerializerMethodField()
  user_album_count = serializers.SerializerMethodField()
  album_song_count = serializers.SerializerMethodField()
  album_percent = serializers.SerializerMethodField()

  class Meta:
    model = models.Releases
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
    model = models.Setlists
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


class ArticlesSerializer(serializers.ModelSerializer):
  category = serializers.CharField(
    source="get_category_display",
    read_only=True,
  )

  excerpt = serializers.SerializerMethodField()

  def get_excerpt(self, obj):
    return strip_markdown.strip_markdown(obj.content[:250])

  class Meta:
    model = models.Articles
    fields = [
      "title",
      "author",
      "content",
      "slug",
      "uuid",
      "published_at",
      "category",
      "source",
      "collection_name",
      "excerpt",
    ]
