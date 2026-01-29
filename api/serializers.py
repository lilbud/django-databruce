import datetime
import re

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import (
    Count,
    F,
    Max,
    Min,
    OuterRef,
    PositiveIntegerField,
    Subquery,
)
from django.db.models.functions import JSONObject, TruncYear
from django.urls import reverse
from rest_framework import serializers

from databruce import models


class SubqueryCount(Subquery):
    # Custom Count function to just perform simple count on any queryset without grouping.
    # https://stackoverflow.com/a/47371514/1164966
    template = "(SELECT count(*) FROM (%(subquery)s) _count)"
    output_field = PositiveIntegerField()


def get_date(event):
    """Get event date, falling back to the event_id if no date."""
    event_id = event["id"]
    event_date = event["date"]
    early_late = event["early_late"]

    result = {"id": event["id"]}

    try:
        date = datetime.datetime.strptime(event_date, "%Y-%m-%d").strftime(
            "%Y-%m-%d",
        )
    except (ValueError, TypeError):
        # no month or day
        if re.search(r"(19|20)\d{2}0{4}-", event_id):
            date = datetime.datetime.strptime(
                f"{event_id[0:4]}-01-01",
                "%Y-%m-%d",
            ).strftime(
                "%Y-%m-%d",
            )
        # month, no day
        elif re.search(r"(19|20)\d{2}[0-3]\d00-", event_id):
            date = datetime.datetime.strptime(
                f"{event_id[0:4]}-{event_id[4:6]}-01",
                "%Y-%m-%d",
            ).strftime(
                "%Y-%m-%d",
            )
        else:
            date = datetime.datetime.strptime(event_id[0:8], "%Y%m%d").strftime(
                "%Y-%m-%d",
            )

    result["filter"] = date
    result["display"] = date

    if early_late:
        result["display"] = f"{date} ({early_late})"

    return result


class RestrictedEventsSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField(method_name="get_date")

    def get_date(self, obj):
        """Get event date, falling back to the event_id if no date."""
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

    class Meta:
        model = models.Events
        fields = [
            "id",
            "date",
        ]


class CountriesSerializer(serializers.ModelSerializer):
    first = RestrictedEventsSerializer()
    last = RestrictedEventsSerializer()
    count = serializers.IntegerField()
    text = serializers.CharField(source="name")

    class Meta:
        model = models.Countries
        fields = "__all__"


class RestrictedCitiesSerializer(serializers.ModelSerializer):
    display = serializers.SerializerMethodField()

    def get_display(self, obj):
        try:
            return f"{obj.name}, {obj.state.abbrev}"
        except AttributeError:
            return f"{obj.name}, {obj.country}"

    class Meta:
        model = models.Cities
        fields = ["id", "name", "display"]


class RestrictedStatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.States
        fields = ["id", "name", "abbrev"]


class RestrictedCountriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Countries
        fields = ["id", "name"]


class StatesSerializer(serializers.ModelSerializer):
    first = RestrictedEventsSerializer()
    last = RestrictedEventsSerializer()
    country = RestrictedCountriesSerializer()
    count = serializers.IntegerField(required=False)
    text = serializers.CharField(source="name")

    class Meta:
        model = models.States
        fields = "__all__"


class CitiesSerializer(serializers.ModelSerializer):
    display = serializers.SerializerMethodField()
    first = RestrictedEventsSerializer()
    last = RestrictedEventsSerializer()
    state = RestrictedStatesSerializer()
    country = RestrictedCountriesSerializer()
    count = serializers.IntegerField()
    text = serializers.SerializerMethodField(method_name="get_display")

    def get_display(self, obj):
        try:
            return f"{obj.name}, {obj.state.abbrev}"
        except AttributeError:
            return f"{obj.name}, {obj.country}"

    class Meta:
        model = models.Cities
        fields = "__all__"


class ToursRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tours
        fields = ["id", "name"]


class RestrictedBandsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Bands
        fields = ["id", "name"]


class VenuesTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.VenuesText
        fields = "__all__"


class EventRelationSerializer(serializers.ModelSerializer):
    # date = serializers.SerializerMethodField(method_name="get_date")
    artist = RestrictedBandsSerializer()
    tour = ToursRelationSerializer()

    class Meta:
        model = models.Events
        fields = ["id", "date", "public", "early_late", "artist", "tour"]


class BandsSerializer(serializers.ModelSerializer):
    first = RestrictedEventsSerializer(required=False)
    last = RestrictedEventsSerializer(required=False)
    count = serializers.IntegerField()
    text = serializers.CharField(source="name")

    class Meta:
        model = models.Bands
        fields = "__all__"


class VenuesSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    city = RestrictedCitiesSerializer(required=False)
    state = RestrictedStatesSerializer(required=False)
    country = RestrictedCountriesSerializer(required=False)
    first = RestrictedEventsSerializer(required=False)
    last = RestrictedEventsSerializer(required=False)
    formatted = serializers.SerializerMethodField()
    text = serializers.SerializerMethodField(method_name="get_name")

    def get_name(self, obj):
        if obj.detail:
            return f"{obj.name}, {obj.detail}"

        return obj.name

    def get_formatted(self, obj):
        name = self.get_name(obj)

        try:
            if obj.country.id == 37:
                return f"{name}, {obj.city.name}, {obj.state.abbrev}"

            return f"{name}, {obj.city.name}, {obj.country.name}"
        except AttributeError:
            return name

    class Meta:
        model = models.Venues
        fields = "__all__"


class RestrictedVenuesSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        if obj.detail:
            return f"{obj.name}, {obj.detail}"

        return obj.name

    class Meta:
        model = models.Venues
        fields = ["id", "name"]


class EventRunSerializer(serializers.ModelSerializer):
    band = RestrictedBandsSerializer()
    venue = VenuesSerializer()
    name = serializers.CharField()
    first = RestrictedEventsSerializer()
    last = RestrictedEventsSerializer()

    class Meta:
        model = models.Runs
        fields = [
            "id",
            "name",
            "band",
            "venue",
            "first",
            "last",
            "num_shows",
            "num_songs",
        ]


class RestrictedEventRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Runs
        fields = ["id", "name"]


class IndexSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField(method_name="get_date")
    venue = VenuesSerializer()

    def get_date(self, obj):
        """Get event date, falling back to the event_id if no date."""
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

    class Meta:
        model = models.Events
        fields = ["id", "date", "venue"]


class EventCalendar(serializers.ModelSerializer):
    start = serializers.DateField(source="date")
    title = serializers.SerializerMethodField()

    def get_title(self, obj):
        return f"<span class='text-xs text-wrap'>{obj.artist}: {obj.venue.name}</span>"

    class Meta:
        model = models.Events
        fields = ["id", "start", "title"]


class EventsSerializer(serializers.ModelSerializer):
    order = serializers.SerializerMethodField(method_name="sort_id")
    date = serializers.SerializerMethodField(method_name="get_date")
    venue = VenuesSerializer()
    artist = RestrictedBandsSerializer()
    tour = ToursRelationSerializer()
    run = RestrictedEventRunSerializer(required=False)
    setlist = serializers.BooleanField(source="has_setlist", required=False)
    setlist_songs = serializers.JSONField
    public = serializers.BooleanField()

    def sort_id(self, obj):
        return int(str(obj.id).replace("-", ""))

    def get_date(self, obj):
        """Get event date, falling back to the event_id if no date."""
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

    class Meta:
        model = models.Events
        fields = [
            "id",
            "order",
            "date",
            "venue",
            "artist",
            "tour",
            "title",
            "public",
            "early_late",
            "setlist",
            "run",
        ]


class ToursSerializer(serializers.ModelSerializer):
    first = RestrictedEventsSerializer()
    last = RestrictedEventsSerializer()
    band = RestrictedBandsSerializer()
    text = serializers.CharField(source="name")

    class Meta:
        model = models.Tours
        fields = "__all__"


class TourRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tours
        fields = [
            "id",
            "name",
        ]


class ArchiveLinksSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ArchiveLinks
        fields = "__all__"


class EventRunDetailSerializer(serializers.ModelSerializer):
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


class BootlegsSerializer(serializers.ModelSerializer):
    event = RestrictedEventsSerializer()
    archive = ArchiveLinksSerializer()

    class Meta:
        model = models.Bootlegs
        fields = "__all__"


class ContinentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Continents
        fields = ["id", "name"]


class CoversSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Covers
        fields = "__all__"


class NugsSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    event = RestrictedEventsSerializer()
    venue = VenuesSerializer(source="event.venue")

    def get_date(self, obj):
        date = obj.date.strftime(
            "%Y-%m-%d [%a]",
        )
        time = obj.date.replace(tzinfo=datetime.timezone.utc).strftime(
            "%I:%M:%S %p",
        )

        return {"date": date, "time": time}

    class Meta:
        model = models.NugsReleases
        fields = "__all__"


class RelationsSerializer(serializers.ModelSerializer):
    first = RestrictedEventsSerializer(required=False)
    last = RestrictedEventsSerializer(required=False)
    text = serializers.CharField(source="name")
    # first_event = serializers.CharField()
    # last_event = serializers.CharField()

    count = serializers.IntegerField()
    nickname = serializers.SerializerMethodField()

    def get_nickname(self, obj):
        names = []

        if obj.nickname:
            names.append(*[n.strip() for n in obj.nickname.split(",")])

        if obj.aliases:
            names.append(*[n.strip() for n in obj.aliases.split(",")])

        return ", ".join(names)

    class Meta:
        model = models.Relations
        fields = "__all__"


class RestrictedRelationsSerializer(serializers.ModelSerializer):
    nickname = serializers.SerializerMethodField()

    def get_nickname(self, obj):
        try:
            obj.nickname
        except AttributeError:
            obj = self.Meta.model.objects.select_related("first", "last").get(id=obj)

        names = []

        if obj.nickname:
            names.append(*[n.strip() for n in obj.nickname.split(",")])

        if obj.aliases:
            names.append(*[n.strip() for n in obj.aliases.split(",")])

        return ", ".join(names)

    class Meta:
        model = models.Relations
        fields = ["id", "name", "instruments", "nickname"]


class OnstageRelationSerializer(serializers.ModelSerializer):
    first = RestrictedEventsSerializer()
    last = RestrictedEventsSerializer()
    count = serializers.IntegerField()
    relation = RestrictedRelationsSerializer()

    class Meta:
        model = models.OnstageBandMembers
        fields = "__all__"


class OnstageSerializer(serializers.ModelSerializer):
    event = RestrictedEventsSerializer()
    relation = RestrictedRelationsSerializer()
    band = RestrictedBandsSerializer(required=False)

    class Meta:
        model = models.Onstage
        fields = "__all__"


class ReleasesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Releases
        fields = "__all__"


class SongsSerializer(serializers.ModelSerializer):
    first = RestrictedEventsSerializer()
    last = RestrictedEventsSerializer()
    has_lyrics = serializers.BooleanField(required=False)

    class Meta:
        model = models.Songs
        fields = [
            "id",
            "name",
            "first",
            "last",
            "original_artist",
            "num_plays_public",
            "num_plays_private",
            "num_plays_snippet",
            "category",
            "has_lyrics",
        ]


class SongsRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Songs
        fields = ["id", "name"]


class ReleaseDiscSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ReleaseDiscs
        fields = "__all__"


class ReleaseTracksSerializer(serializers.ModelSerializer):
    event = RestrictedEventsSerializer(required=False)
    disc = ReleaseDiscSerializer(source="discid", required=False)
    song = SongsRelationSerializer()

    class Meta:
        model = models.ReleaseTracks
        fields = "__all__"


VALID_SET_NAMES = [
    "Show",
    "Set 1",
    "Set 2",
    "Encore",
    "Pre-Show",
    "Post-Show",
]


class RestrictedSetlistsSerializer(serializers.ModelSerializer):
    song = SongsRelationSerializer()
    event = RestrictedEventsSerializer()

    class Meta:
        model = models.Setlists
        fields = "__all__"


class SetlistSerializer(serializers.ModelSerializer):
    song = SongsSerializer()
    event = RestrictedEventsSerializer()
    ltp = RestrictedEventsSerializer()
    segue = serializers.BooleanField()
    debut = serializers.BooleanField()
    premiere = serializers.BooleanField()
    nobruce = serializers.BooleanField()
    sign_request = serializers.BooleanField()
    instrumental = serializers.BooleanField()
    notes = serializers.ListField(required=False, source="notes_list")
    t_total = serializers.IntegerField(required=False)
    t_count = serializers.IntegerField(required=False)

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
            "nobruce",
            "sign_request",
            "instrumental",
            "notes",
            "t_total",
            "t_count",
            "song_num",
        ]


class NotesSerializer(serializers.ModelSerializer):
    setlist = RestrictedSetlistsSerializer()
    event = EventsSerializer()
    # song = SongsRelationSerializer(source="setlist.song")

    class Meta:
        model = models.Notes
        fields = "__all__"


class SetlistFilterSerializer(serializers.ModelSerializer):
    # songid = serializers.IntegerField()
    count = serializers.IntegerField()
    # name = serializers.CharField()
    # category = serializers.CharField()
    song = serializers.JSONField(source="songinfo")

    class Meta:
        model = models.Setlists
        fields = "__all__"


class SnippetSerializer(serializers.ModelSerializer):
    event = EventsSerializer(source="setlist.event")
    snippet = SongsSerializer()
    setlist = RestrictedSetlistsSerializer()

    class Meta:
        model = models.Snippets
        fields = "__all__"


class TourLegsSerializer(serializers.ModelSerializer):
    tour = TourRelationSerializer()
    first = RestrictedEventsSerializer()
    last = RestrictedEventsSerializer()

    class Meta:
        model = models.TourLegs
        fields = "__all__"


from django.contrib.postgres.fields import JSONField


class SongsPageSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    song = SongsRelationSerializer()
    event = EventsSerializer()
    prev_song = serializers.JSONField()
    next_song = serializers.JSONField()

    class Meta:
        model = models.Setlists
        fields = "__all__"


class LyricsSerializer(serializers.ModelSerializer):
    song = SongsRelationSerializer()

    class Meta:
        model = models.Lyrics
        fields = "__all__"


class SetlistEntrySerializer(serializers.ModelSerializer):
    event = EventsSerializer()
    show_opener = SongsRelationSerializer(required=False)
    s1_closer = SongsRelationSerializer(required=False)
    s2_opener = SongsRelationSerializer(required=False)
    main_closer = SongsRelationSerializer(required=False)
    encore_opener = SongsRelationSerializer(required=False)
    show_closer = SongsRelationSerializer(required=False)

    class Meta:
        model = models.SetlistEntries
        fields = "__all__"


class SetlistNotesSerializer(serializers.ModelSerializer):
    event = RestrictedEventsSerializer()
    # setlist = SetlistSerializer(source="id")

    class Meta:
        model = models.SetlistNotes
        fields = "__all__"


class UpdatesSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField(method_name="get_created")

    def get_created(self, obj):
        return obj.created_at.strftime("%Y-%m-%d")

    class Meta:
        model = models.Updates
        fields = "__all__"
