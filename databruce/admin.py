from django import forms
from django.contrib import admin
from django.contrib.admin import site
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.models import Group, User
from django.db import models as dj_models
from django.db.models.functions import Cast, JSONObject
from unfold.admin import ModelAdmin, StackedInline, TabularInline
from unfold.contrib.inlines.admin import (
    NonrelatedStackedInline,
    NonrelatedTabularInline,
)
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold_markdown.widgets import MarkdownWidget

from . import models

# Unregister the default User admin
site.unregister(Group)


# class CustomModelAdmin(ModelAdmin):
#     class Media:
#         css = {
#             "all": ("admin/css/custom_unfold.css",),
#         }
#         js = ("admin/js/custom_unfold.js",)


@admin.register(models.CustomUser)
class UserAdmin(DefaultUserAdmin, ModelAdmin):
    search_fields = ["username"]
    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "date_joined",
        "last_login",
        "is_active",
        "uuid",
    ]
    # Forms loaded from `unfold.forms`
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


class OnstageInline(StackedInline):
    model = models.Onstage
    collapsible = True

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "relation",
            )
            .prefetch_related("band")
        )

    autocomplete_fields = ["relation", "band"]

    fields = ["relation", "band", "note", "guest"]
    fk_name = "event"
    ordering = ("relation__name",)
    extra = 0


class SetlistInline(StackedInline):
    model = models.Setlists
    collapsible = True

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "song",
                "event",
            )
        )

    autocomplete_fields = ["song"]

    fields = ["set_name", "song_num", "song", "segue", "note"]
    fk_name = "event"
    ordering = ("song_num",)
    extra = 0


class ReleaseTrackInline(StackedInline):
    model = models.ReleaseTracks
    collapsible = True

    def get_queryset(self, request):
        base_qs = super().get_queryset(request)
        return (
            base_qs.select_related("song", "release")
            .prefetch_related("event", "discid")
            .order_by("discnum", Cast("track", output_field=dj_models.IntegerField()))
        )

    autocomplete_fields = ["song", "event", "discid"]

    fields = [
        "discnum",
        "discid",
        "track",
        "song",
        "event",
        "length",
        "note",
    ]
    fk_name = "release"
    ordering = ("discnum", "track")
    extra = 0


@admin.register(models.ArchiveLinks)
class ArchiveAdmin(ModelAdmin):
    search_fields = ["event__id", "url"]
    list_select_related = ["event", "event__venue", "event__venue__city"]
    autocomplete_fields = ["event"]
    list_display = ["id", "url"]
    list_display_links = ["id"]


@admin.register(models.UserAttendedShows)
class UserAttendedShowsAdmin(ModelAdmin):
    search_fields = ["user__username", "event", "event__date"]
    list_select_related = [
        "user",
        "event",
        "event__venue",
        "event__venue__city",
    ]
    list_display = ["id", "user__username", "event"]
    autocomplete_fields = ["user", "event"]
    list_display_links = ["id"]


@admin.register(models.Bands)
class BandAdmin(ModelAdmin):
    search_fields = ["name"]
    list_display = ["id", "name"]
    list_display_links = ["id"]
    autocomplete_fields = ["first_event", "last_event"]
    list_select_related = [
        "first_event",
        "last_event",
        "first_event__venue",
        "first_event__venue__city",
        "last_event__venue",
        "last_event__venue__city",
    ]


@admin.register(models.Guests)
class GuestAdmin(ModelAdmin):
    autocomplete_fields = ["setlist", "guest"]
    search_fields = ["guest__name", "setlist__id", "setlist__event__event_id", "setlist__song__name"]
    list_display = [
        "setlist__id",
        "setlist__event__event_id",
        "setlist__song",
        "guest__name",
    ]
    list_select_related = ["setlist", "guest", "setlist__song"]


@admin.register(models.Bootlegs)
class BootlegAdmin(ModelAdmin):
    search_fields = [
        "event__event_id",
        "event__date",
        "title",
        "label",
        "source",
        "archive__url",
    ]
    list_select_related = ["event", "event__venue", "event__venue__city"]
    autocomplete_fields = ["event", "archive"]
    list_display = ["id", "event", "title", "label", "source"]
    list_display_links = ["id", "event"]


@admin.register(models.Cities)
class CityAdmin(ModelAdmin):
    search_fields = ["name"]
    list_select_related = [
        "state",
        "country",
        "first_event",
        "last_event",
        "first_event__venue",
        "last_event__venue",
    ]
    autocomplete_fields = ["state", "country", "first_event", "last_event"]
    list_display = ["id", "name", "state", "country"]
    list_display_links = ["id", "state", "country"]


@admin.register(models.Continents)
class ContinentAdmin(ModelAdmin):
    search_fields = ["name"]
    list_display = ["id", "name"]
    list_display_links = ["id"]


@admin.register(models.Countries)
class CountryAdmin(ModelAdmin):
    search_fields = ["name"]
    list_display = ["id", "name"]
    list_display_links = ["id"]
    list_select_related = [
        "first_event",
        "last_event",
        "first_event__venue",
        "last_event__venue",
    ]
    autocomplete_fields = ["first_event", "last_event", "continent"]


@admin.register(models.Covers)
class CoverAdmin(ModelAdmin):
    search_fields = ["event"]
    list_select_related = ["event", "event__venue", "event__venue__city"]
    list_display = ["id", "event", "url"]
    autocomplete_fields = ["event"]

    list_display_links = ["id", "event"]


@admin.register(models.NugsReleases)
class NugsAdmin(ModelAdmin):
    search_fields = ["event"]
    autocomplete_fields = ["event"]

    list_select_related = ["event", "event__venue", "event__venue__city"]
    list_display = ["id", "event", "url", "date"]
    list_display_links = ["id", "event"]


class EventForm(forms.ModelForm):
    note = forms.CharField(
        widget=MarkdownWidget(),
    )

    brucebase_url = dj_models.TextField()
    title = dj_models.CharField()

    class Meta:
        model = models.Events
        fields = "__all__"


@admin.register(models.Events)
class EventAdmin(ModelAdmin):
    form = EventForm
    search_fields = ["id", "event_id", "date"]
    autocomplete_fields = [
        "venue",
        "artist",
        "tour",
        "run",
        "leg",
        "nugs_id",
        "official_id",
    ]

    formfield_overrides = {
        dj_models.TextField: {
            "widget": forms.Textarea(attrs={"style": "height: 200px;"}),
        },
    }

    list_display = ["id", "date", "event_id"]
    list_display_links = ["id"]
    inlines = [SetlistInline, OnstageInline]


@admin.register(models.Songs)
class SongAdmin(ModelAdmin):
    search_fields = ["name", "original_artist"]
    list_select_related = ["first_event", "last_event", "album"]
    autocomplete_fields = ["first_event", "last_event", "album"]
    list_display = ["id", "name"]
    list_display_links = ["id"]
    ordering = ("name",)


class LyricForm(forms.ModelForm):
    note = forms.CharField(
        widget=MarkdownWidget(),
    )

    class Meta:
        model = models.Lyrics
        fields = "__all__"


@admin.register(models.Lyrics)
class LyricsAdmin(ModelAdmin):
    search_fields = ["song__name", "text"]
    autocomplete_fields = ["song"]
    list_display = ["id", "song__name"]
    list_display_links = ["id"]
    list_select_related = ["song"]
    ordering = ("song__name",)

    form = LyricForm


@admin.register(models.Setlists)
class SetlistAdmin(ModelAdmin):
    autocomplete_fields = ["event", "song", "ltp"]
    search_fields = ["song__name", "set_name", "event__event_id"]
    list_select_related = [
        "song",
        "event",
        "event__venue",
        "event__venue__city",
        "ltp",
    ]
    list_display = ["id", "event", "set_name", "song_num", "song"]
    list_display_links = ["id", "event", "song"]


@admin.register(models.Onstage)
class OnstageAdmin(ModelAdmin):
    search_fields = ["relation__name", "band__name"]
    list_select_related = [
        "relation",
        "band",
        "event",
        "event__venue",
        "event__venue__city",
    ]
    list_display = ["id", "event__event_id", "relation__name", "band__name"]
    list_display_links = ["id"]
    autocomplete_fields = ["event", "relation", "band"]
    ordering = ("relation__name",)


@admin.register(models.Relations)
class RelationAdmin(ModelAdmin):
    search_fields = ["name"]
    list_display = ["id", "name"]
    list_select_related = ["first_event", "last_event"]
    autocomplete_fields = ["first_event", "last_event"]
    list_display_links = ["id"]
    ordering = ("name",)


@admin.register(models.ReleaseDiscs)
class ReleaseDiscAdmin(ModelAdmin):
    search_fields = ["release__name"]
    list_display = ["id", "name", "release__name"]
    list_select_related = ["release"]
    autocomplete_fields = ["release"]
    list_display_links = ["id"]


@admin.register(models.ReleaseTracks)
class ReleaseTrackAdmin(ModelAdmin):
    search_fields = ["release__name", "song__name"]
    list_select_related = ["release", "song", "event", "discid", "setlist"]
    list_display = ["id", "release__name", "track", "song", "song__name"]
    autocomplete_fields = ["release", "song", "event", "discid", "setlist"]
    list_display_links = ["id"]


class ReleaseForm(forms.ModelForm):
    note = forms.CharField(
        widget=MarkdownWidget(),
        required=False,
    )

    class Meta:
        model = models.Releases
        fields = "__all__"


@admin.register(models.Releases)
class ReleaseAdmin(ModelAdmin):
    def get_queryset(self, request):
        base_qs = super().get_queryset(request)
        return base_qs.prefetch_related("event")

    form = ReleaseForm
    search_fields = ["name", "type"]
    list_display = ["id", "name", "type", "date", "mbid"]
    list_display_links = ["id"]
    autocomplete_fields = ["event"]
    inlines = [ReleaseTrackInline]


@admin.register(models.Snippets)
class SnippetAdmin(ModelAdmin):
    search_fields = [
        "snippet__name",
        "setlist",
        "setlist__id",
    ]

    autocomplete_fields = ["setlist", "snippet"]

    list_select_related = [
        "setlist",
        "setlist__event",
        "snippet",
        "setlist__song",
        "setlist",
    ]
    list_display = [
        "id",
        "setlist",
        "setlist__song__name",
        "snippet__name",
        "note",
    ]
    list_display_links = [
        "id",
        "setlist",
        "setlist__song__name",
        "snippet__name",
    ]


@admin.register(models.States)
class StateAdmin(ModelAdmin):
    search_fields = ["name", "abbrev", "country", "first_event", "last_event"]
    list_select_related = [
        "country",
        "first_event",
        "last_event",
        "first_event__venue",
        "last_event__venue",
        "first_event__venue__city",
        "last_event__venue__city",
        "country",
    ]

    autocomplete_fields = ["country", "first_event", "last_event"]

    list_display = ["id", "name", "abbrev", "country", "first_event", "last_event"]
    list_display_links = ["id"]


@admin.register(models.Tours)
class TourAdmin(ModelAdmin):
    def get_queryset(self, request):
        base_qs = super().get_queryset(request)
        return base_qs.prefetch_related(
            "band",
            "first_event",
            "last_event",
        )

    search_fields = ["name"]
    autocomplete_fields = ["band", "first_event", "last_event"]
    list_display = [
        "id",
        "name",
        "band__name",
    ]
    list_display_links = ["id"]


@admin.register(models.TourLegs)
class TourLegAdmin(ModelAdmin):
    search_fields = ["name"]
    list_select_related = [
        "first_event",
        "last_event",
        "tour",
        "first_event__venue",
        "last_event__venue",
        "first_event__venue__city",
        "last_event__venue__city",
    ]
    list_display = ["id", "tour", "name", "first_event", "last_event"]
    autocomplete_fields = ["first_event", "last_event", "tour"]
    list_display_links = ["id"]


@admin.register(models.Venues)
class VenueAdmin(ModelAdmin):
    search_fields = ["name"]
    list_select_related = ["first_event", "last_event", "city"]
    list_display = [
        "id",
        "name",
        "first_event",
        "last_event",
        "city__name",
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

    autocomplete_fields = ["city"]

    list_display_links = [
        "id",
    ]
    ordering = ("name",)


@admin.register(models.Runs)
class RunAdmin(ModelAdmin):
    search_fields = ["name", "band__name"]
    autocomplete_fields = ["band", "first_event", "last_event", "venue"]
    list_select_related = [
        "band",
        "first_event",
        "last_event",
        "venue",
        "first_event__venue",
        "last_event__venue",
        "first_event__venue__city",
        "last_event__venue__city",
    ]
    list_display = ["id", "name", "band", "num_shows", "first_event", "last_event"]
    list_display_links = ["id"]


@admin.register(models.Tags)
class TagAdmin(ModelAdmin):
    search_fields = ["event"]
    list_select_related = [
        "event",
        "event__venue",
        "event__venue__city",
    ]
    autocomplete_fields = ["event"]
    list_display = ["id", "event", "tags"]
    list_display_links = ["id"]


@admin.register(models.Contact)
class ContactAdmin(ModelAdmin):
    search_fields = ["email", "subject", "message"]
    list_display = [
        "id",
        "email",
        "subject",
        "message",
        "is_user",
        "created_at",
    ]
    list_display_links = ["id"]
