from django.urls import reverse
from django.utils.html import format_html
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


class EventsSerializer(serializers.ModelSerializer):
    venue = VenuesTextSerializer(read_only=True)
    artist = BandsSerializer(read_only=True)
    tour = ToursSerializer(read_only=True)
    date = serializers.SerializerMethodField()

    def get_date(self, obj):
        """Get event date, falling back to the event_id if no date."""
        date = f"{obj.id[0:4]}-{obj.id[4:6]}-{obj.id[6:8]}"

        if obj.date:
            date = obj.date.strftime("%Y-%m-%d")

        if obj.early_late:
            date += f" {obj.early_late}"

        return f"<a href='{reverse('event_details', kwargs={'id': obj.id})}'>{date}</a>"

        # return date

    class Meta:
        model = models.Events
        fields = ["venue", "artist", "tour", "date", "id"]


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


class SongsSerializer(serializers.ModelSerializer):
    first = EventsSerializer()
    last = EventsSerializer()
    name = serializers.SerializerMethodField()
    original = serializers.SerializerMethodField()

    def get_name(self, obj):
        song_url = reverse("song_details", kwargs={"id": f"{obj.id}"})
        name = obj.name

        if obj.lyrics:
            name = format_html(
                "{} <i class='bi bi-file-earmark-check' data-bs-toggle='tooltip' data-bs-placement='top' data-bs-title='Has Lyrics'></i>",
                obj.name,
            )

        return format_html("<a href={}>{}<a>", song_url, name)

    def get_original(self, obj):
        return obj.original

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
    song = SongsSerializer(read_only=True)
    event = EventsSerializer(read_only=True)

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
    qs = models.Setlists.objects.prefetch_related("song", "event")
    # No additional database hits required
    prev = SetlistSerializer(qs, many=False)
    current = SetlistSerializer(qs, many=False)
    next = SetlistSerializer(qs, many=False)

    class Meta:
        model = models.SongsPage
        fields = "__all__"


class VenuesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Venues
        fields = "__all__"
