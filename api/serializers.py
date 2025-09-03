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
        fields = "__all__"


class EventsSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    venue = serializers.SerializerMethodField()
    artist = serializers.SerializerMethodField()
    tour = serializers.SerializerMethodField()

    def get_date(self, obj):
        """Get event date, falling back to the event_id if no date."""
        date = f"{obj.id[0:4]}-{obj.id[4:6]}-{obj.id[6:8]}"

        if obj.date:
            date = obj.date.strftime("%Y-%m-%d")

        if obj.early_late:
            date += f" {obj.early_late}"

        return f"<a href='{reverse('event_details', kwargs={'id': obj.id})}'>{date}</a>"

    def get_venue(self, obj):
        name = obj.venue.name

        if obj.venue.detail:
            name = f"{obj.venue.name}, {obj.venue.detail}"

        return f"<a href='{reverse('venue_details', kwargs={'id': obj.venue.id})}'>{name}</a>"

    def get_artist(self, obj):
        return obj.artist.name

    def get_tour(self, obj):
        return obj.tour.name

    class Meta:
        model = models.Events
        fields = ["date", "venue", "artist", "tour"]


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
    first = EventsSerializer()
    last = EventsSerializer()
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
    prev = serializers.SerializerMethodField()
    current = SetlistSerializer()
    band = serializers.SerializerMethodField()
    next = serializers.SerializerMethodField()

    # date, band, venue, tour, position, gap, set, note

    def get_band(self, obj):
        try:
            return obj.current.event.band.name
        except:
            return ""

    def get_prev(self, obj):
        try:
            return obj.prev.song.name
        except AttributeError:
            return ""

    def get_next(self, obj):
        try:
            return obj.next.song.name
        except AttributeError:
            return ""

    class Meta:
        model = models.SongsPage
        fields = "__all__"
