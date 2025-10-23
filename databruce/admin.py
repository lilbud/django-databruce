from django.contrib import admin

from . import models


class OnstageInline(admin.TabularInline):
    model = models.Onstage

    list_select_related = ["relation", "band", "event"]
    autocomplete_fields = ["relation", "band"]

    fields = [
        "relation",
        "band",
        "note",
        "guest",
    ]
    fk_name = "event"
    ordering = ("relation__name",)
    extra = 0


class SetlistInline(admin.TabularInline):
    model = models.Setlists
    list_select_related = ["song", "event"]
    autocomplete_fields = ["song"]
    fields = [
        "event",
        "set_name",
        "song_num",
        "song",
        "segue",
        "note",
        "premiere",
        "debut",
        "sign_request",
        "instrumental",
        "nobruce",
    ]  # Specify the fields you want to include
    fk_name = "event"
    ordering = ("song_num",)
    extra = 0


@admin.register(models.ArchiveLinks)
class ArchiveAdmin(admin.ModelAdmin):
    search_fields = ["event"]
    list_select_related = ["event"]
    list_display = ["id", "event", "url"]
    list_display_links = ["id", "event"]


@admin.register(models.UserAttendedShows)
class UserAttendedShowsAdmin(admin.ModelAdmin):
    search_fields = ["user__username", "event__id", "event__date"]
    list_select_related = ["user", "event"]
    list_display = ["user__username", "event"]
    list_display_links = ["user__username", "event"]


@admin.register(models.Bands)
class BandAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ["id", "name"]
    list_display_links = ["id"]
    list_select_related = ["first", "last"]
    ordering = ("name",)


@admin.register(models.Guests)
class GuestAdmin(admin.ModelAdmin):
    autocomplete_fields = ["setlist", "guest", "event"]
    search_fields = ["guest__name", "setlist__id"]
    list_display = ["setlist__id", "setlist__song", "guest__name"]
    list_select_related = ["setlist", "guest"]


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
    autocomplete_fields = ["event"]

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
    list_select_related = True
    list_display = ["id", "date", "venue"]
    list_display_links = ["id", "venue"]
    inlines = [SetlistInline, OnstageInline]


@admin.register(models.Songs)
class SongAdmin(admin.ModelAdmin):
    search_fields = ["name", "original_artist"]
    list_display = ["id", "name"]
    list_display_links = ["id"]
    ordering = ("name",)


@admin.register(models.Setlists)
class SetlistAdmin(admin.ModelAdmin):
    autocomplete_fields = ["event", "song"]
    search_fields = ["song__name", "event__id", "set_name"]
    list_select_related = True
    list_display = ["id", "event", "set_name", "song_num", "song"]
    list_display_links = ["id", "event", "song"]


@admin.register(models.Onstage)
class OnstageAdmin(admin.ModelAdmin):
    search_fields = ["relation__name", "band__name"]
    list_select_related = True
    list_display = ["id", "event", "relation__name", "band__name"]
    list_display_links = ["id", "event", "relation__name", "band__name"]
    ordering = ("relation__name",)


@admin.register(models.Relations)
class RelationAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ["id", "name"]
    list_display_links = ["id"]
    ordering = ("name",)


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
        "snippet__name",
        "setlist__event__id",
        "setlist__id",
    ]

    autocomplete_fields = ["setlist", "snippet"]

    list_select_related = [
        "setlist",
        "snippet",
        "setlist__song",
        "setlist__event",
    ]
    list_display = [
        "id",
        "setlist__event__id",
        "setlist__song__name",
        "snippet__name",
        "note",
    ]
    list_display_links = [
        "id",
        "setlist__event__id",
        "setlist__song__name",
        "snippet__name",
    ]


@admin.register(models.States)
class StateAdmin(admin.ModelAdmin):
    search_fields = ["name", "abbrev", "country", "first", "last"]
    list_select_related = ["country", "first", "last"]
    list_display = ["id", "name", "abbrev", "country", "first", "last"]
    list_display_links = ["id", "country", "first", "last"]


from django.db.models import Q


@admin.register(models.Tours)
class TourAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_select_related = ["first", "band", "last"]
    list_display = ["id", "name", "band", "first", "last"]
    list_display_links = ["id", "band", "first", "last"]
    ordering = ("name",)


@admin.register(models.TourLegs)
class TourLegAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_select_related = ["first", "last", "tour"]
    list_display = ["id", "tour", "name", "first", "last"]
    list_display_links = ["id", "tour", "first", "last"]
    ordering = ("name",)


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

    def get_search_results(self, request, queryset, search_term):
        queryset, may_have_duplicates = super().get_search_results(
            request,
            queryset,
            search_term,
        )
        try:
            search_term_as_int = int(search_term)
        except ValueError:
            pass
        else:
            queryset |= self.model.objects.filter(age=search_term_as_int)
        return queryset, may_have_duplicates

    autocomplete_fields = ["city", "state"]

    list_display_links = [
        "id",
        "name",
        "first",
        "last",
        "city__name",
        "state__name",
        "country__name",
    ]
    ordering = ("name",)


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


@admin.register(models.VenuesText)
class VenuesTextAdmin(admin.ModelAdmin):
    search_fields = ["formatted_loc"]
    list_display = ["id", "formatted_loc"]
