import datetime
import re

from django.db.models.functions import JSONObject, TruncYear
from django.urls import reverse
from rest_framework import serializers

from databruce import models


class StatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.States
        fields = ["id", "name", "abbrev"]


class CountriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Countries
        fields = ["id", "name"]


class CitiesSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        if hasattr(obj, "state"):
            return f"{obj.name}, {obj.state.abbrev}"

        return f"{obj.name}, {obj.country}"

    class Meta:
        model = models.Cities
        fields = ["id", "name"]


class ToursRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tours
        fields = ["id", "name"]


class BandsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Bands
        fields = ["id", "name"]


class VenuesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Venues
        fields = ["id", "name"]


class VenuesTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.VenuesText
        fields = "__all__"


class EventRelationSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField(method_name="get_date")
    artist = BandsSerializer()
    tour = ToursRelationSerializer()

    def get_date(self, obj):
        """Get event date, falling back to the event_id if no date."""
        date = obj.date

        if not obj.date:
            date = f"{obj.id[0:4]}-{obj.id[4:6]}-{obj.id[6:8]}"

        # year, no month or day
        if re.search(r"\d{4}0{4}-\d{2}", obj.id):
            date = datetime.datetime.strptime(f"{obj.id[0:4]}-01-01", "%Y-%m-%d").date()

        # year, no month, day
        if re.search(r"\d{4}0{2}\d{2}-\d{2}", obj.id):
            date = datetime.datetime.strptime(
                f"{obj.id[0:4]}-01-01",
                "%Y-%m-%d",
            ).date()

        # year, month, no day
        if re.search(r"\d{6}0{2}-\d{2}", obj.id):
            date = datetime.datetime.strptime(
                f"{obj.id[0:4]}-01-01",
                "%Y-%m-%d",
            ).date()

        return date

    class Meta:
        model = models.Events
        fields = ["id", "date", "public", "early_late", "artist", "tour"]


class EventsSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField(method_name="get_date")
    venue = VenuesTextSerializer()
    artist = BandsSerializer()
    tour = ToursRelationSerializer()
    setlist = serializers.SerializerMethodField(method_name="has_setlist")

    def get_date(self, obj):
        """Get event date, falling back to the event_id if no date."""
        try:
            return datetime.datetime.strptime(obj.id[0:8], "%Y%m%d").strftime(
                "%Y-%m-%d",
            )
        except ValueError:
            return f"{obj.id[0:4]}-{obj.id[4:6]}-{obj.id[6:8]}"

    def has_setlist(self, obj):
        return obj.setlist_certainty in ["Confirmed", "Probable"]

    class Meta:
        model = models.Events
        fields = [
            "id",
            "date",
            "venue",
            "artist",
            "tour",
            "title",
            "public",
            "early_late",
            "setlist",
        ]


class ToursSerializer(serializers.ModelSerializer):
    first = EventRelationSerializer()
    last = EventRelationSerializer()
    band = BandsSerializer()

    class Meta:
        model = models.Tours
        fields = [
            "id",
            "name",
            "band",
            "first",
            "last",
            "num_shows",
            "num_songs",
            "num_legs",
        ]


class ArchiveLinksSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ArchiveLinks
        fields = "__all__"


class EventRunSerializer(serializers.ModelSerializer):
    band = BandsSerializer()
    venue = VenuesTextSerializer()
    first = EventsSerializer()
    last = EventsSerializer()

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


class BootlegsSerializer(serializers.ModelSerializer):
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
    event = EventsSerializer()

    class Meta:
        model = models.NugsReleases
        fields = "__all__"


class RelationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Relations
        fields = ["id", "name"]


class OnstageSerializer(serializers.ModelSerializer):
    relation = RelationsSerializer()

    class Meta:
        model = models.Onstage
        fields = "__all__"


class ReleasesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Releases
        fields = "__all__"


from django.utils.html import format_html


class SongsSerializer(serializers.ModelSerializer):
    first = EventRelationSerializer()
    last = EventRelationSerializer()

    class Meta:
        model = models.Songs
        fields = "__all__"


class SongsRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Songs
        fields = "__all__"


class ReleaseTracksSerializer(serializers.ModelSerializer):
    release = ReleasesSerializer()
    song = SongsSerializer()

    class Meta:
        model = models.ReleaseTracks
        fields = "__all__"


class SetlistNotesSerializer(serializers.ModelSerializer):
    event = EventsSerializer()

    class Meta:
        model = models.SetlistNotes
        fields = "__all__"


class SetlistSerializer(serializers.ModelSerializer):
    song = SongsSerializer()
    event = EventsSerializer()

    class Meta:
        model = models.Setlists
        fields = "__all__"


class SnippetSerializer(serializers.ModelSerializer):
    event = EventsSerializer(source="setlist.event")
    setlist = SetlistSerializer()
    snippet = SongsSerializer()

    class Meta:
        model = models.Snippets
        fields = "__all__"


class TourLegsSerializer(serializers.ModelSerializer):
    tour = ToursSerializer()
    first = EventsSerializer()
    last = EventsSerializer()

    class Meta:
        model = models.TourLegs
        fields = "__all__"


class SongsPageSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    song = SongsRelationSerializer()
    event = EventRelationSerializer()
    venue = serializers.JSONField()
    # venue = VenuesTextSerializer(source="event.venue.id")
    prev_song = serializers.JSONField()
    next_song = serializers.JSONField()

    class Meta:
        model = models.Setlists
        fields = [
            "id",
            "song",
            "event",
            "prev_song",
            "next_song",
            "set_name",
            "venue",
            "note",
            "last",
            "position",
        ]
