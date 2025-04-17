from datetime import datetime

from django.urls import reverse
from django.utils.html import format_html
from django_filters import filters
from rest_framework import serializers
from rest_framework_datatables.django_filters.backends import DatatablesFilterBackend
from rest_framework_datatables.django_filters.filters import GlobalFilter
from rest_framework_datatables.django_filters.filterset import DatatablesFilterSet

from databruce import models


class ToursSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tours
        fields = "__all__"


class VenuesSerializer(serializers.ModelSerializer):
    city_name = serializers.ReadOnlyField(source="city.name")
    state_abbrev = serializers.ReadOnlyField(source="state.state_abbrev", default=None)
    country_name = serializers.ReadOnlyField(source="country.name")
    location = serializers.SerializerMethodField("get_location")

    def get_location(self, obj):
        if obj.city:
            if obj.state:
                return f"{obj.city.name}, {obj.state.state_abbrev}"

            return f"{obj.city.name}, {obj.country.name}"

        return ""

    class Meta:
        model = models.Venues
        fields = "__all__"


class BandsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Bands
        fields = "__all__"


class EventsSerializer(serializers.ModelSerializer):
    venue = VenuesSerializer()
    artist = BandsSerializer()
    tour = ToursSerializer()
    date = serializers.SerializerMethodField("get_date")

    def get_date(self, obj):
        """Get event date, falling back to the event_id if no date."""
        date = f"{obj.id[0:4]}-{obj.id[4:6]}-{obj.id[6:8]}"

        if obj.event_date:
            date = obj.event_date.strftime("%Y-%m-%d [%a]")

        if obj.early_late:
            date += f" {obj.early_late}"

        return {
            "url": reverse("databruce:event_details", args=[obj.id]),
            "date": date,
        }

    class Meta:
        model = models.Events
        fields = "__all__"


class ArchiveLinksSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ArchiveLinks
        fields = "__all__"


class BootlegsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Bootlegs
        fields = "__all__"


class StatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.States
        fields = "__all__"


class CountriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Countries
        fields = "__all__"


class CitiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Cities
        fields = "__all__"


class ContinentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Continents
        fields = "__all__"


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
        fields = "__all__"


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
    class Meta:
        model = models.Songs
        exclude = ["fts"]


class ReleaseTracksSerializer(serializers.ModelSerializer):
    release = ReleasesSerializer()
    song = SongsSerializer()

    class Meta:
        model = models.ReleaseTracks
        fields = "__all__"


class SetlistSerializer(serializers.ModelSerializer):
    song = SongsSerializer()

    class Meta:
        model = models.Setlists
        fields = "__all__"


class SetlistNotesSerializer(serializers.ModelSerializer):
    id = SetlistSerializer()
    event = EventsSerializer()

    class Meta:
        model = models.SetlistNotes
        fields = "__all__"


class SnippetSerializer(serializers.ModelSerializer):
    event = EventsSerializer()
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
