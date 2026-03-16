import datetime
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.db.models import (
    Count,
    F,
    PositiveIntegerField,
    Subquery,
)
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
        fields = ["id", "name", "abbrev", "uuid"]


class MinimalCountriesSerializer(BaseSerializer):
    class Meta:
        model = models.Countries
        fields = ["id", "name", "uuid"]


class MinimalBandsSerializer(BaseSerializer):
    class Meta:
        model = models.Bands
        fields = ["id", "name", "uuid"]


class MinimalCitiesSerializer(BaseSerializer):
    formatted = serializers.SerializerMethodField()

    def get_formatted(self, obj):
        try:
            if obj.state and obj.country_id in (2, 6, 37):
                return f"{obj.name}, {obj.state.abbrev}"
        except models.Cities.state.RelatedObjectDoesNotExist:
            return f"{obj.name}, {obj.country.name}"

    class Meta:
        model = models.Cities
        fields = ["id", "name", "formatted", "uuid"]


class MinimalVenuesTextSerializer(BaseSerializer):
    class Meta:
        model = models.VenuesText
        fields = ["formatted"]


class MinimalVenuesSerializer(BaseSerializer):
    city = MinimalCitiesSerializer(required=False)
    state = MinimalStatesSerializer(source="city.state", required=False)
    country = MinimalCountriesSerializer(source="city.country", required=False)
    formatted = serializers.SerializerMethodField()
    display = serializers.SerializerMethodField()

    def get_display(self, obj):
        return ", ".join(filter(None, [obj.detail, obj.name]))

    def get_formatted(self, obj):
        return MinimalVenuesTextSerializer(obj.venues_text).data["formatted"]

    class Meta:
        model = models.Venues
        fields = [
            "id",
            "name",
            "detail",
            "city",
            "state",
            "country",
            "formatted",
            "uuid",
            "display",
        ]


class MinimalToursSerializer(BaseSerializer):
    class Meta:
        model = models.Tours
        fields = ["id", "name", "uuid"]


class MinimalUserSerializer(BaseSerializer):
    class Meta:
        model = UserModel
        fields = ["id", "username"]


class MinimalEventSerializer(BaseSerializer):
    date = serializers.SerializerMethodField(method_name="get_date")

    def get_date(self, obj):
        return get_date_from_instance(obj)

    class Meta:
        model = models.Events
        fields = ["id", "date", "event_id"]


class MinimalTourLegsSerializer(BaseSerializer):
    class Meta:
        model = models.TourLegs
        fields = ["id", "name", "uuid"]


class MinimalEventRunSerializer(BaseSerializer):
    class Meta:
        model = models.Runs
        fields = ["id", "name", "uuid"]


class MinimalRelationsSerializer(BaseSerializer):
    class Meta:
        model = models.Relations
        fields = ["id", "name", "instruments", "uuid"]


class MinimalSongsSerializer(BaseSerializer):
    class Meta:
        model = models.Songs
        fields = [
            "id",
            "name",
            "album",
            "category",
            "uuid",
            "original_artist",
            "num_plays_public",
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


class SubqueryCount(Subquery):
    # Custom Count function to just perform simple count on any queryset without grouping.
    # https://stackoverflow.com/a/47371514/1164966
    template = "(SELECT count(*) FROM (%(subquery)s) _count)"
    output_field = PositiveIntegerField()


def get_date_from_instance(obj):
    """Get event date from instance, creating date from id if needed."""
    event_id = getattr(obj, "event_id", None)
    date = getattr(obj, "date", None)
    early_late = getattr(obj, "early_late", None)

    if event_id is None:
        return None

    result = {}

    if not date:
        date = datetime.datetime.strptime(format_fuzzy(event_id), "%Y-%m-%d")

    result["filter"] = date.strftime("%Y-%m-%d")
    result["display"] = date.strftime("%Y-%m-%d")
    result["display_day"] = date.strftime("%Y-%m-%d [%a]")

    if early_late:
        result["display"] = f"{date.strftime('%Y-%m-%d')} ({early_late})"
        result["display_day"] = f"{date.strftime('%Y-%m-%d [%a]')} ({early_late})"

    return result


class StatesSerializer(BaseSerializer):
    first_event = MinimalEventSerializer()
    last_event = MinimalEventSerializer()
    country = MinimalCountriesSerializer()
    count = serializers.IntegerField(required=False)
    text = serializers.CharField(source="name")

    class Meta:
        model = models.States
        fields = "__all__"


class CountriesSerializer(BaseSerializer):
    first_event = MinimalEventSerializer(required=False)
    last_event = MinimalEventSerializer(required=False)
    count = serializers.IntegerField(required=False)

    class Meta:
        model = models.Countries
        fields = "__all__"


class CitiesSerializer(BaseSerializer):
    state = MinimalStatesSerializer(required=False)
    country = MinimalCountriesSerializer()
    count = serializers.IntegerField()
    first_event = MinimalEventSerializer(required=False)
    last_event = MinimalEventSerializer(required=False)

    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        try:
            if obj.state and obj.country_id in (2, 6, 37):
                return f"{obj.name}, {obj.state.abbrev}"
        except models.Cities.state.RelatedObjectDoesNotExist:
            return f"{obj.name}, {obj.country.name}"

        return obj.name

    class Meta:
        model = models.Cities
        fields = "__all__"


class BandsSerializer(BaseSerializer):
    first_event = MinimalEventSerializer(required=False)
    last_event = MinimalEventSerializer(required=False)

    class Meta:
        model = models.Bands
        fields = "__all__"


class VenuesSerializer(BaseSerializer):
    name = serializers.SerializerMethodField()
    city = MinimalCitiesSerializer(required=False)
    state = MinimalStatesSerializer(required=False, source="city.state")
    country = MinimalCountriesSerializer(required=False)
    text = serializers.SerializerMethodField(method_name="get_name")
    location = serializers.SerializerMethodField()
    first_event = MinimalEventSerializer(required=False)
    last_event = MinimalEventSerializer(required=False)

    def get_location(self, obj):
        try:
            return f"{obj.name}, {obj.city.name}, {obj.state.abbrev}"
        except AttributeError:
            return f"{obj.name}, {obj.city.name}, {obj.country.name}"

    def get_name(self, obj):
        if obj.detail:
            return f"{obj.name}, {obj.detail}"

        return obj.name

    class Meta:
        model = models.Venues
        fields = "__all__"


class EventRunSerializer(BaseSerializer):
    band = MinimalBandsSerializer()
    venue = MinimalVenuesSerializer()
    first_event = MinimalEventSerializer(required=False)
    last_event = MinimalEventSerializer(required=False)

    class Meta:
        model = models.Runs
        fields = [
            "id",
            "name",
            "band",
            "venue",
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


class EventCalendar(BaseSerializer):
    start = serializers.DateField(source="date")
    title = serializers.SerializerMethodField()

    def get_title(self, obj):
        return f"<span class='text-xs text-wrap'>{obj.artist}: {obj.venue}</span>"

    class Meta:
        model = models.Events
        fields = ["id", "start", "title", "venue"]


class ToursSerializer(BaseSerializer):
    first_event = MinimalEventSerializer(required=False)
    last_event = MinimalEventSerializer(required=False)
    band = MinimalBandsSerializer(required=False)

    class Meta:
        model = models.Tours
        fields = "__all__"


class OnstageSerializer(BaseSerializer):
    event = MinimalEventSerializer()
    relation = MinimalRelationsSerializer()
    band = MinimalBandsSerializer(required=False)

    class Meta:
        model = models.Onstage
        fields = ["event", "relation", "band", "guest", "uuid", "note"]


class EventsSerializer(BaseSerializer):
    order = serializers.SerializerMethodField(method_name="sort_id")
    date = serializers.SerializerMethodField(method_name="get_date")
    run = MinimalEventRunSerializer(required=False)
    artist = MinimalBandsSerializer(required=False)
    tour = MinimalToursSerializer(required=False)
    venue = MinimalVenuesSerializer(required=False)
    leg = MinimalTourLegsSerializer(required=False)
    has_setlist = serializers.BooleanField(required=False)

    bands = serializers.SerializerMethodField(required=False)
    relations = serializers.SerializerMethodField(required=False)

    event_status = serializers.SerializerMethodField()

    def get_event_status(self, obj):
        return bool(obj.type and obj.type in ["Cancelled", "Relocated", "Rescheduled"])

    def get_bands(self, obj):
        return list({item.band_id for item in obj.onstage.all() if item.band_id})

    def get_relations(self, obj):
        return list(
            {item.relation_id for item in obj.onstage.all() if item.relation_id},
        )

    def sort_id(self, obj):
        return int(str(obj.event_id).replace("-", ""))

    def get_date(self, obj):
        return get_date_from_instance(obj)

    class Meta:
        model = models.Events
        fields = "__all__"


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

    def get_date(self, obj):
        return {
            "date": obj.date.strftime("%Y-%m-%d [%a]"),
            "time": obj.date.astimezone(ZoneInfo("UTC")).strftime(
                "%I:%M:%S %p",
            ),
        }

    class Meta:
        model = models.NugsReleases
        fields = "__all__"


class RelationsSerializer(BaseSerializer):
    first_event = MinimalEventSerializer(required=False)
    last_event = MinimalEventSerializer(required=False)
    count = serializers.IntegerField(required=False)
    aliases = serializers.ListField(required=False)
    nicknames = serializers.ListField(required=False)

    class Meta:
        model = models.Relations
        fields = [
            "first_event",
            "last_event",
            "id",
            "instruments",
            "count",
            "name",
            "aliases",
            "nicknames",
            "uuid",
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
    length = serializers.TimeField(format="%H:%M:%S", required=False)

    class Meta:
        model = models.Releases
        fields = "__all__"


class SongsSerializer(BaseSerializer):
    first_event = MinimalEventSerializer()
    last_event = MinimalEventSerializer()
    has_lyrics = serializers.BooleanField(required=False)
    text = serializers.SerializerMethodField(method_name="get_name")

    def get_name(self, obj):
        if obj.original_artist and obj.original is False:
            return f"{obj.name} ({obj.original_artist})"

        return obj.name

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
            "num_plays_snippet",
            "opener",
            "closer",
            "category",
            "has_lyrics",
            "sort_song_name",
            "text",
            "uuid",
        ]


class SetlistStatsSerializer(BaseSerializer):
    ltp = MinimalEventSerializer()

    class Meta:
        model = models.SetlistStats
        fields = "__all__"


class SetlistSerializer(BaseSerializer):
    song = MinimalSongsSerializer()
    last_event = MinimalEventSerializer(source="ltp", required=False)
    event = EventsSerializer(include=["id", "event_id"])
    count = serializers.IntegerField(required=False)
    notes = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()
    stats = SetlistStatsSerializer(
        required=False,
        read_only=True,
        source="setlist_stats",
    )

    def get_notes(self, obj):
        if not obj.setlist_notes.exists():
            return None

        return list(
            {item.note for item in obj.setlist_notes.all() if item.note != ""},
        )

    def get_position(self, obj):
        try:
            return obj.setlist_position.position
        except models.Setlists.setlist_position.RelatedObjectDoesNotExist:
            return None

    class Meta:
        model = models.Setlists
        fields = [
            "song",
            "event",
            "ltp",
            "segue",
            "debut",
            "premiere",
            "set_name",
            "count",
            "last",
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
            "setlist_position",
            "stats",
        ]


class ReleaseDiscSerializer(BaseSerializer):
    class Meta:
        model = models.ReleaseDiscs
        fields = ["id", "name", "uuid"]


class ReleaseTracksSerializer(BaseSerializer):
    event = MinimalEventSerializer(required=False)
    disc = ReleaseDiscSerializer(source="discid", required=False)
    song = SongsSerializer(
        include=[
            "id",
            "name",
            "uuid",
            "first_event",
            "last_event",
            "num_plays_public",
            "num_plays_private",
            "num_plays_snippet",
        ],
    )
    length = serializers.TimeField(format="%M:%S", required=False)

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


class SnippetSerializer(BaseSerializer):
    event = EventsSerializer(
        source="setlist.event",
        include=["id", "event_id", "artist", "venue", "date"],
    )
    snippet = MinimalSongsSerializer()
    setlist = MinimalSetlistSerializer()
    count = serializers.IntegerField(required=False)
    first = serializers.SerializerMethodField()
    last = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Performance trick: Map ONLY the events needed for this specific page of results
        if self.instance and hasattr(self.instance, "__iter__"):
            event_ids = set()
            for obj in self.instance:
                if obj.first_event_id:
                    event_ids.add(obj.first_event_id)
                if obj.last_event_id:
                    event_ids.add(obj.last_event_id)

            self.page_event_map = {
                e.event_id: MinimalEventSerializer(e).data
                for e in models.Events.objects.filter(event_id__in=event_ids)
            }

    def get_first(self, obj):
        return self.page_event_map.get(obj.first_event_id)

    def get_last(self, obj):
        return self.page_event_map.get(obj.last_event_id)

    # event = EventsSerializer(
    #     source="setlist.event",
    #     include=["id", "event_id", "artist", "venue", "date"],
    # )
    # snippet = MinimalSongsSerializer()
    # setlist = MinimalSetlistSerializer()
    # count = serializers.IntegerField(required=False)
    # first = serializers.SerializerMethodField(required=False)
    # last = serializers.SerializerMethodField(required=False)

    # event_map = {
    #     s.event_id: MinimalEventSerializer(s).data for s in models.Events.objects.all()
    # }

    # snippet_qs = models.Snippets.objects.select_related(
    #     "setlist__event",
    #     "setlist",
    #     "setlist__song",
    # ).order_by("setlist__event__event_id")

    # def get_first(self, obj):
    #     event = (
    #         self.snippet_qs.filter(
    #             setlist__song=obj.setlist.song_id,
    #             snippet=obj.snippet_id,
    #         )
    #         .values(event=F("setlist__event__event_id"))
    #         .first()
    #     )

    #     return self.event_map[event["event"]]

    # def get_last(self, obj):
    #     event = (
    #         self.snippet_qs.filter(
    #             setlist__song=obj.setlist.song_id,
    #             snippet=obj.snippet_id,
    #         )
    #         .values(event=F("setlist__event__event_id"))
    #         .last()
    #     )

    #     return self.event_map[event["event"]]

    class Meta:
        model = models.Snippets
        fields = "__all__"


class TourLegsSerializer(BaseSerializer):
    tour = MinimalToursSerializer()
    first_event = MinimalEventSerializer()
    last_event = MinimalEventSerializer()

    class Meta:
        model = models.TourLegs
        fields = "__all__"


class SongsPageSerializer(BaseSerializer):
    id = serializers.IntegerField()
    song = SongsSerializer(include=["id", "name", "uuid"])
    event = EventsSerializer(
        include=["id", "event_id", "venue", "artist", "date", "tour"],
    )

    position = serializers.SerializerMethodField()

    songs_map = {
        s.id: MinimalSongsSerializer(s).data for s in models.Songs.objects.all()
    }

    prev_song = SongsSerializer(
        source="songs_page.prev",
        include=["id", "name", "uuid"],
        required=False,
    )

    next_song = SongsSerializer(
        source="songs_page.next",
        include=["id", "name", "uuid"],
        required=False,
    )

    notes = serializers.SerializerMethodField()

    def get_notes(self, obj):
        if not obj.setlist_notes.exists():
            return None

        return list(
            {item.note for item in obj.setlist_notes.all() if item.note != ""},
        )

    # def get_prev_song(self, obj):
    #     try:
    #         return self.songs_map[obj.songs_page.prev_id]
    #     except (KeyError, TypeError):
    #         return None

    # def get_next_song(self, obj):
    #     try:
    #         return self.songs_map[obj.songs_page.next_id]
    #     except (KeyError, TypeError):
    #         return None

    def get_position(self, obj):
        try:
            return obj.setlist_position.position
        except models.Setlists.setlist_position.RelatedObjectDoesNotExist:
            return None

    class Meta:
        model = models.Setlists
        fields = "__all__"


class LyricsSerializer(BaseSerializer):
    song = MinimalSongsSerializer()

    class Meta:
        model = models.Lyrics
        fields = "__all__"


class SetlistEntrySerializer(BaseSerializer):
    event = EventsSerializer(
        include=["id", "tour", "date", "leg", "run", "event_id"],
    )
    show_opener = serializers.SerializerMethodField(required=False)
    s1_closer = serializers.SerializerMethodField(required=False)
    s2_opener = serializers.SerializerMethodField(required=False)
    main_closer = serializers.SerializerMethodField(required=False)
    encore_opener = serializers.SerializerMethodField(required=False)
    show_closer = serializers.SerializerMethodField(required=False)

    songs_map = {
        s.id: MinimalSongsSerializer(s).data for s in models.Songs.objects.all()
    }

    def get_show_opener(self, obj):
        return self.songs_map.get(obj.show_opener_id, None)

    def get_s1_closer(self, obj):
        return self.songs_map.get(obj.s1_closer_id, None)

    def get_s2_opener(self, obj):
        return self.songs_map.get(obj.s2_opener_id, None)

    def get_main_closer(self, obj):
        return self.songs_map.get(obj.main_closer_id, None)

    def get_encore_opener(self, obj):
        return self.songs_map.get(obj.encore_opener_id, None)

    def get_show_closer(self, obj):
        return self.songs_map.get(obj.show_closer_id, None)

    class Meta:
        model = models.SetlistEntries
        fields = "__all__"


class SetlistNotesSerializer(BaseSerializer):
    event = EventsSerializer(include=["id", "event_id", "name", "venue", "date"])
    setlist = MinimalSetlistSerializer()

    class Meta:
        model = models.SetlistNotes
        fields = ["event", "note", "setlist"]


class SetlistSongsSerializer(BaseSerializer):
    count = serializers.IntegerField(required=False)
    song = serializers.SerializerMethodField(required=False)
    first_event = serializers.SerializerMethodField(required=False)
    last_event = serializers.SerializerMethodField(required=False)
    sets = serializers.ListField(required=False)

    soundcheck_only = serializers.SerializerMethodField(required=False)
    recording_only = serializers.SerializerMethodField(required=False)

    event_map = {
        s.event_id: MinimalEventSerializer(s).data for s in models.Events.objects.all()
    }

    song_map = {
        s.id: MinimalSongsSerializer(s).data for s in models.Songs.objects.all()
    }

    def get_song(self, obj):
        return self.song_map[obj["song_id"]]

    def get_first_event(self, obj):
        return self.event_map[obj["first_event"]]

    def get_last_event(self, obj):
        return self.event_map[obj["last_event"]]

    def get_soundcheck_only(self, obj):
        return obj["sets"] == ["Soundcheck"]

    def get_recording_only(self, obj):
        return obj["sets"] == ["Recording"]

    class Meta:
        model = models.Setlists
        fields = [
            "song",
            "count",
            "first_event",
            "last_event",
            "sets",
            "soundcheck_only",
            "recording_only",
        ]


class UpdatesSerializer(BaseSerializer):
    created_at = serializers.SerializerMethodField(method_name="get_created")

    def get_created(self, obj):
        return obj.created_at.strftime("%m/%d")

    class Meta:
        model = models.Updates
        fields = "__all__"


class UsersSerializer(BaseSerializer):
    event_count = serializers.IntegerField()

    date_joined = serializers.SerializerMethodField()

    def get_date_joined(self, obj):
        return obj.date_joined.strftime("%Y-%m-%d")

    class Meta:
        model = UserModel
        fields = [
            "id",
            "username",
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
    max_val = serializers.IntegerField(required=False)
    num = serializers.IntegerField(required=False)
    percent = serializers.CharField(required=False)
    category = serializers.CharField(required=False)

    songs_map = {
        s.id: MinimalSongsSerializer(s).data for s in models.Songs.objects.all()
    }

    total = serializers.IntegerField(required=False)
    album_complete = serializers.SerializerMethodField(required=False)

    def get_album_complete(self, obj):
        """Check if all songs on album are present in setlist."""
        album_songs = obj["album_songs"]
        setlist_songs = obj["songs"]

        album_songs.sort()
        setlist_songs.sort()

        return album_songs == setlist_songs

    songs = serializers.SerializerMethodField(required=False)

    def get_songs(self, obj):
        try:
            return [self.songs_map[s] for s in obj["songs"]]
        except KeyError:
            return []

    class Meta:
        model = models.Songs
        fields = [
            "max_val",
            "percent",
            "category",
            "num",
            "total",
            "songs",
            "album_complete",
        ]
