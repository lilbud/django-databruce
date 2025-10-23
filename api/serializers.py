from django.urls import reverse
from rest_framework import serializers

from databruce import models


class ToursSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tours
        fields = ["id", "name"]


class VenuesTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.VenuesText
        fields = "__all__"


class BandsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Bands
        fields = ["id", "name"]


class VenuesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Venues
        fields = ["id", "name"]


class EventsSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    # venue = VenuesSerializer()
    # artist = BandsSerializer()
    # tour = ToursSerializer()

    def get_date(self, obj):
        """Get event date, falling back to the event_id if no date."""
        date = f"{obj.id[0:4]}-{obj.id[4:6]}-{obj.id[6:8]}"

        if obj.date:
            date = obj.date.strftime("%Y-%m-%d")

        if obj.early_late:
            date += f" {obj.early_late}"

        return f"<a href='{reverse('event_details', kwargs={'id': obj.id})}'>{date}</a>"

    class Meta:
        model = models.Events
        fields = ["date", "public"]
        read_only_fields = fields


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
        fields = ["id", "name"]


class CountriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Countries
        fields = ["id", "name"]


class CitiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Cities
        fields = ["id", "name"]


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
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        name = obj.name

        if obj.short_name:
            name = obj.short_name

        return format_html(
            "<a href={}>{}<a>",
            reverse("song_details", kwargs={"id": f"{obj.id}"}),
            name,
        )

    class Meta:
        model = models.Songs
        fields = ["id", "name"]
        read_only_fields = fields


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


class SongsPageSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    song = serializers.IntegerField()
    num = serializers.IntegerField()
    event = EventsSerializer()
    artist = serializers.IntegerField()
    artist_name = serializers.CharField()
    venue = serializers.IntegerField()
    venue_name = serializers.CharField()
    tour = serializers.IntegerField()
    tour_name = serializers.CharField()
    position = serializers.CharField()
    gap = serializers.IntegerField()
    set_name = serializers.CharField()
    prev = serializers.IntegerField()
    prev_name = serializers.CharField()
    next = serializers.IntegerField()
    next_name = serializers.CharField()
    note = serializers.CharField()

    class Meta:
        model = models.Songspagenew
        fields = [
            "id",
            "song",
            "num",
            "event",
            "artist",
            "artist_name",
            "venue",
            "venue_name",
            "tour",
            "tour_name",
            "position",
            "gap",
            "set_name",
            "prev",
            "prev_name",
            "next",
            "next_name",
            "note",
        ]
        # read_only_fields = fields
