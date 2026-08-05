import datetime
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.db.models import Count, F
from rest_framework import serializers

from databruce import models
from databruce.templatetags.filters import format_fuzzy

UserModel = get_user_model()
VALID_SET_NAMES = [
    "Show",
    "Set 1",
    "Set 2",
    "Encore",
    "Pre-Show",
    "Post-Show",
]


def get_date_from_instance(obj):
    """Get event date from instance, creating date from id if needed."""
    event_id = getattr(obj, "event_id", None)
    date = getattr(obj, "date", None)
    early_late = getattr(obj, "early_late", None)

    if event_id is None:
        return None

    # result = {}

    if not date:
        date = datetime.datetime.strptime(format_fuzzy(event_id), "%Y-%m-%d")

    # result["display"] = date.strftime("%Y-%m-%d")
    # result["display_day"] = date.strftime("%Y-%m-%d [%a]")

    if early_late:
        return f"{date.strftime('%Y-%m-%d')} ({early_late})"

    return date.strftime("%Y-%m-%d")


def get_formatted_city(obj):
    if obj.state:
        if getattr(obj.country, "alpha_2", "").upper() == "US":
            return f"{obj.name}, {obj.state.abbrev}"

        return f"{obj.name}, {obj.state.abbrev}, {obj.country.name}"

    return f"{obj.name}, {obj.country.name}"


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
            "num_shows",
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
            "num_shows",
            "num_songs",
            "num_legs",
        ]


class OnstageSerializer(BaseSerializer):
    relation = MinimalRelationsSerializer(include=["uuid", "name"])
    band = MinimalBandsSerializer(required=False)

    class Meta:
        model = models.Onstage
        fields = ["relation", "band", "guest", "note"]


class EventTypeSerializer(BaseSerializer):
    class Meta:
        model = models.EventTypes
        fields = ["name", "slug"]


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
    notes = serializers.SerializerMethodField()

    def get_notes(self, obj):
        if not obj.setlist_notes.exists():
            return None

        return "; ".join(
            list(
                filter(None, [item.note for item in obj.setlist_notes.all()]),
            ),
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
        ]


class IndexEventsSerializer(BaseSerializer):
    venue = serializers.CharField(source="venue.name", max_length=255)
    date = serializers.CharField(max_length=255)

    class Meta:
        model = models.Events
        fields = ["event_id", "date", "venue"]


class EventsSerializer(BaseSerializer):
    date = serializers.SerializerMethodField(method_name="get_date")
    early_late = serializers.CharField(required=False, max_length=255)
    artist = MinimalBandsSerializer(required=False)
    tour = MinimalToursSerializer(required=False)
    venue = MinimalVenuesSerializer(
        required=False,
        include=["uuid", "name", "formatted"],
    )
    city = serializers.SerializerMethodField()

    def get_city(self, obj):
        return get_formatted_city(obj.venue.city)

    leg = serializers.CharField(required=False, source="leg.name", max_length=255)
    has_setlist = serializers.SerializerMethodField()
    type = serializers.CharField(required=False, source="type.name", max_length=255)
    rank = serializers.IntegerField(required=False)
    event_status = serializers.SerializerMethodField()
    public = serializers.BooleanField(required=False)

    def get_has_setlist(self, obj):
        return bool(obj.setlist_event.exists())

    def get_event_status(self, obj):
        return bool(obj.type and obj.type_id in [21, 22, 6])

    def get_bands(self, obj):
        return list({item.band_id for item in obj.onstage.all() if item.band_id})

    def get_relations(self, obj):
        return list(
            {item.relation_id for item in obj.onstage.all() if item.relation_id},
        )

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
            "type",
            "rank",
            "event_status",
            "event_id",
            "title",
            "public",
            "early_late",
        ]


class ArchiveLinksSerializer(BaseSerializer):
    event = MinimalEventSerializer()

    class Meta:
        model = models.ArchiveLinks
        fields = "__all__"


class EventRunDetailSerializer(BaseSerializer):
    events = serializers.SerializerMethodField()
    songs = serializers.SerializerMethodField()

    def get_events(self, obj):
        return models.Events.objects.filter(run__id=obj.id)

    def get_songs(self, obj):
        return (
            models.Setlists.objects.filter(
                event__run__id=obj.id,
                set_name__in=VALID_SET_NAMES,
            )
            .values("song__id")
            .annotate(
                count=Count("event"),
                name=F("song__name"),
                category=F("song__category"),
            )
            .order_by("-count", "song__name")
        )

    class Meta:
        model = models.Events
        fields = "__all__"


class BootlegsSerializer(BaseSerializer):
    event = MinimalEventSerializer()
    archive = MinimalArchiveLinksSerializer(required=False)

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
        fields = "__all__"


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
            "appearances",
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
    notes = serializers.SerializerMethodField()

    def get_notes(self, obj):
        if not obj.setlist_notes.exists():
            return None

        return "; ".join(
            list(
                filter(None, [item.note for item in obj.setlist_notes.all()]),
            ),
        )

    class Meta:
        model = models.Setlists
        fields = "__all__"


class SetlistSerializer(BaseSerializer):
    song = MinimalSongsSerializer(include=["name", "uuid", "category_slug", "slug"])
    last_event = MinimalEventSerializer(
        source="ltp",
        required=False,
        include=["date", "event_id"],
    )
    count = serializers.IntegerField(required=False)
    notes = serializers.SerializerMethodField()
    gap = serializers.SerializerMethodField()

    def get_gap(self, obj):
        if obj.last == 0:
            return None

        return obj.last

    def get_notes(self, obj):
        if not obj.setlist_notes.exists():
            return None

        return "; ".join(
            list(
                filter(None, [item.note for item in obj.setlist_notes.all()]),
            ),
        )

    class Meta:
        model = models.Setlists
        fields = [
            "song",
            "ltp",
            "segue",
            "debut",
            "premiere",
            "set_name",
            "count",
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


class NotesSerializer(BaseSerializer):
    event = EventsSerializer()

    class Meta:
        model = models.Notes
        fields = "__all__"


class SetlistFilterSerializer(BaseSerializer):
    count = serializers.IntegerField()
    song = MinimalSongsSerializer()

    class Meta:
        model = models.Setlists
        fields = "__all__"


class SetlistNotesSerializer(BaseSerializer):
    event = EventsSerializer(include=["id", "event_id", "name", "venue", "date"])
    setlist = MinimalSetlistSerializer()

    class Meta:
        model = models.SetlistNotes
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
            "num_shows",
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
        fields = ["song", "version", "source", "language", "note", "uuid"]


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
            self._event_map = {
                e.event_id: MinimalEventSerializer(e).data for e in events
            }
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
        return obj.created_at.strftime("%m/%d")

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
        include=["id", "event_id", "date", "venue", "tour", "artist", "has_setlist"],
    )
    user = MinimalUserSerializer()

    class Meta:
        model = models.UserAttendedShows
        fields = "__all__"


class SetlistBreakdownSerializer(BaseSerializer):
    max = serializers.IntegerField(required=False)
    num = serializers.IntegerField(required=False)
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
        """Check if all songs on album are present in setlist."""
        # intros that shouldn't be counted in setlist for album check
        remove = [689, 1021, 514]

        if obj["category"] == "Covers" or obj["category"] == "Originals":
            return False

        album_songs = obj["album_songs"]
        setlist_songs = [song for song in obj["songs"] if song not in remove]

        album_len = len(album_songs)
        setlist_len = len(setlist_songs)

        # if album_len > setlist_len:
        #     return False

        # print(album_songs, setlist_songs)

        return any(
            setlist_songs[i : i + album_len] == album_songs
            for i in range(setlist_len - album_len + 1)
        )

    songs = serializers.SerializerMethodField(required=False)

    def get_songs(self, obj):
        try:
            return [self.songs_map[s] for s in obj["songs"]]
        except KeyError:
            return []

    class Meta:
        model = models.Setlists
        fields = [
            "max",
            "num",
            "songs",
            "category",
            "album_complete",
            "category_slug",
        ]


class UserAlbumBreakdownSerializer(BaseSerializer):
    album_song_count = serializers.IntegerField(read_only=True)
    user_album_count = serializers.IntegerField(read_only=True)
    album_percent = serializers.FloatField(read_only=True)
    songs = serializers.SerializerMethodField()  # Single unified list

    class Meta:
        model = models.Releases
        fields = [
            "id",
            "name",
            "uuid",
            "mbid",
            "songs",
            "album_song_count",
            "user_album_count",
            "album_percent",
        ]

    def get_songs(self, obj):
        # Retrieve maps from context
        songs_map = self.context.get("songs_map", {})
        tracks_by_release = self.context.get("tracks_by_release", {})

        # Get the ordered song IDs for this specific release
        ordered_song_ids = tracks_by_release.get(obj.id, [])

        # Return the enriched song data in order
        return [songs_map.get(s_id) for s_id in ordered_song_ids if s_id in songs_map]


class YearSongBreakdownSerializer(BaseSerializer):
    year = serializers.IntegerField()
    count = serializers.IntegerField()

    class Meta:
        model = models.Setlists
        fields = ["year", "count"]
