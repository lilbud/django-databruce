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
        fields = ["id", "name", "alpha_2"]


class CitiesSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        try:
            return f"{obj.name}, {obj.state.abbrev}"
        except AttributeError:
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


class VenuesTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.VenuesText
        fields = "__all__"


class EventRelationSerializer(serializers.ModelSerializer):
    # date = serializers.SerializerMethodField(method_name="get_date")
    artist = BandsSerializer()
    tour = ToursRelationSerializer()

    class Meta:
        model = models.Events
        fields = ["id", "date", "public", "early_late", "artist", "tour"]


class RestrictedEventsSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField(method_name="get_date")

    def get_date(self, obj):
        """Get event date, falling back to the event_id if no date."""
        try:
            result = {"id": obj.id}
        except AttributeError:
            obj = models.Events.objects.get(id=obj)
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


class VenuesSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    city = CitiesSerializer(required=False)
    first = RestrictedEventsSerializer(required=False)
    last = RestrictedEventsSerializer(required=False)
    formatted = serializers.SerializerMethodField()

    def get_name(self, obj):
        if obj.detail:
            return f"{obj.name}, {obj.detail}"

        return obj.name

    def get_formatted(self, obj):
        name = self.get_name(obj)
        city = obj.city.name
        country = obj.country

        if country.id == 37:
            return f"{name}, {city}, {obj.state.abbrev}"

        try:
            return f"{name}, {city}, {obj.state.abbrev}, {country}"
        except AttributeError:
            return f"{name}, {city}, {country}"

    class Meta:
        model = models.Venues
        fields = "__all__"


class EventsSerializer(serializers.ModelSerializer):
    order = serializers.SerializerMethodField(method_name="sort_id")
    date = serializers.SerializerMethodField(method_name="get_date")
    venue = VenuesSerializer()
    artist = BandsSerializer()
    tour = ToursRelationSerializer()
    setlist = serializers.SerializerMethodField(method_name="has_setlist")

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

    def has_setlist(self, obj):
        return obj.setlist_certainty in ["Confirmed", "Probable"]

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
        ]


class ToursSerializer(serializers.ModelSerializer):
    first = RestrictedEventsSerializer()
    last = RestrictedEventsSerializer()
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


class EventRunSerializer(serializers.ModelSerializer):
    band = BandsSerializer()
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


class SongsSerializer(serializers.ModelSerializer):
    first = RestrictedEventsSerializer()
    last = RestrictedEventsSerializer()

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
    event = RestrictedEventsSerializer()
    count = serializers.IntegerField(required=False)

    class Meta:
        model = models.Setlists
        fields = ["event", "song", "count"]


class SnippetSerializer(serializers.ModelSerializer):
    event = EventsSerializer(source="setlist.event")
    setlist = SetlistSerializer()
    snippet = SongsSerializer()

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


class SongsPageSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    song = SongsRelationSerializer()
    event = EventsSerializer()
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
            "note",
            "last",
            "position",
        ]
