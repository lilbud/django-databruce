from django.contrib import admin

from . import models


class OnstageInline(admin.TabularInline):
    model = models.Onstage
    autocomplete_fields = ["relation", "band"]
    list_select_related = ["relation", "band", "event"]
    fields = [
        "relation",
        "band",
        "note",
        "guest",
    ]
    fk_name = "event"
    extra = 1


class SetlistInline(admin.TabularInline):
    model = models.Setlists
    autocomplete_fields = ["song"]
    list_select_related = ["event", "song"]
    fields = [
        "event",
        "set_name",
        "song_num",
        "song",
        "segue",
        "song_note",
        "premiere",
        "debut",
    ]  # Specify the fields you want to include
    fk_name = "event"
    ordering = ("song_num",)
    extra = 1


@admin.register(models.ArchiveLinks)
class ArchiveAdmin(admin.ModelAdmin):
    search_fields = ["event"]
    list_select_related = ["event"]
    list_display = ["id", "event", "url"]
    list_display_links = ["id", "event"]


@admin.register(models.UserAttendedShows)
class UserAttendedShowsAdmin(admin.ModelAdmin):
    search_fields = ["user", "event"]
    list_select_related = ["user", "event"]


@admin.register(models.Bands)
class BandAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ["id", "name"]
    list_display_links = ["id"]


@admin.register(models.Bootlegs)
class BootlegAdmin(admin.ModelAdmin):
    search_fields = ["event", "title", "label", "source"]
    list_select_related = ["event"]
    list_display = ["id", "event", "title", "label", "source"]
    list_display_links = ["id", "event"]


@admin.register(models.Cities)
class CityAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_select_related = ["state", "country"]
    list_display = ["id", "name", "state__name", "country__name"]
    list_display_links = ["id", "state__name", "country__name"]


@admin.register(models.Continents)
class ContinentAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ["id", "name"]
    list_display_links = ["id"]


@admin.register(models.Countries)
class CountryAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ["id", "name"]
    list_display_links = ["id"]


@admin.register(models.Covers)
class CoverAdmin(admin.ModelAdmin):
    search_fields = ["event"]
    list_select_related = ["event"]
    list_display = ["id", "event", "url"]
    list_display_links = ["id", "event"]


@admin.register(models.NugsReleases)
class NugsAdmin(admin.ModelAdmin):
    search_fields = ["event"]
    list_select_related = ["event"]
    list_display = ["id", "event", "url"]
    list_display_links = ["id", "event"]


@admin.register(models.Events)
class EventAdmin(admin.ModelAdmin):
    search_fields = [
        "id",
        "date",
    ]
    autocomplete_fields = ["venue", "artist", "tour", "run", "leg", "nugs_id"]
    list_select_related = [
        "venue",
        "artist",
        "tour",
        "run",
        "leg",
        "nugs_id",
    ]
    list_display = ["id", "date", "venue"]
    list_display_links = ["id", "venue"]
    inlines = [SetlistInline, OnstageInline]


@admin.register(models.Songs)
class SongAdmin(admin.ModelAdmin):
    search_fields = ["name", "original_artist"]
    list_display = ["id", "name"]
    list_display_links = ["id"]


@admin.register(models.Setlists)
class SetlistAdmin(admin.ModelAdmin):
    autocomplete_fields = ["event", "song"]
    search_fields = ["song__name", "event__id", "set_name"]
    list_select_related = ["event", "song"]
    list_display = ["id", "event", "set_name", "song_num", "song"]
    list_display_links = ["id", "event", "song"]


@admin.register(models.Onstage)
class OnstageAdmin(admin.ModelAdmin):
    search_fields = ["relation__name", "band__name"]
    list_select_related = ["relation", "band"]
    list_display = ["id", "event", "relation__name", "band__name"]
    list_display_links = ["id", "event", "relation__name", "band__name"]


@admin.register(models.Relations)
class RelationAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ["id", "name"]
    list_display_links = ["id"]


@admin.register(models.ReleaseTracks)
class ReleaseTrackAdmin(admin.ModelAdmin):
    search_fields = ["release__name", "song_name"]
    list_select_related = ["release", "song"]
    list_display = ["id", "release__name", "track", "song", "song__name"]
    list_display_links = ["id", "release__name", "song"]


@admin.register(models.Releases)
class ReleaseAdmin(admin.ModelAdmin):
    search_fields = ["name", "type"]
    list_display = ["id", "name", "type", "date"]
    list_display_links = ["id"]


@admin.register(models.Snippets)
class SnippetAdmin(admin.ModelAdmin):
    search_fields = [
        "snippet__song_name",
        "event",
        "setlist",
    ]
    autocomplete_fields = ["event", "setlist", "snippet"]
    list_select_related = [
        "setlist",
        "snippet",
        "event",
        "setlist__song",
        "setlist__event",
    ]
    list_display = [
        "id",
        "event",
        "setlist",
        "setlist__song__name",
        "snippet__name",
        "note",
    ]
    list_display_links = [
        "id",
        "event",
        "setlist",
        "setlist__song__name",
        "snippet__name",
    ]


@admin.register(models.States)
class StateAdmin(admin.ModelAdmin):
    search_fields = ["name", "state_abbrev", "country", "first", "last"]
    list_select_related = ["country", "first", "last"]
    list_display = ["id", "name", "state_abbrev", "country", "first", "last"]
    list_display_links = ["id", "country", "first", "last"]


@admin.register(models.Tours)
class TourAdmin(admin.ModelAdmin):
    search_fields = ["name", "band"]
    list_select_related = ["first", "band", "last"]
    list_display = ["id", "name", "band", "first", "last"]
    list_display_links = ["id", "band", "first", "last"]


@admin.register(models.TourLegs)
class TourLegAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_select_related = ["first", "last", "tour"]
    list_display = ["id", "tour", "name", "first", "last"]
    list_display_links = ["id", "tour", "first", "last"]


@admin.register(models.Venues)
class VenueAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_select_related = ["first", "last", "city", "state", "country"]
    list_display = [
        "id",
        "name",
        "first",
        "last",
        "city__name",
        "state__name",
        "country__name",
    ]

    list_display_links = [
        "id",
        "name",
        "first",
        "last",
        "city__name",
        "state__name",
        "country__name",
    ]


@admin.register(models.Runs)
class RunAdmin(admin.ModelAdmin):
    search_fields = ["name", "band"]
    autocomplete_fields = ["band"]
    list_select_related = ["band", "first", "last"]
    list_display = ["id", "name", "band", "num_shows", "first", "last"]
    list_display_links = ["id", "band", "first", "last"]


@admin.register(models.Tags)
class TagAdmin(admin.ModelAdmin):
    search_fields = ["event"]
    list_select_related = ["id", "event"]
    list_display = ["id", "event", "tags"]
    list_display_links = ["id", "event"]
