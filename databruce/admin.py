from datetime import time
from typing import Any, Never

from django import forms
from django.contrib import admin, messages
from django.contrib.admin import site
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.models import Group
from django.db import models as dj_models
from django.db.models import QuerySet
from django.db.models.functions import Cast
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from unfold.admin import ModelAdmin, StackedInline
from unfold.decorators import action, display
from unfold.forms import (
  AdminPasswordChangeForm,
  UserChangeForm,
  UserCreationForm,
)
from unfold_markdown.widgets import MarkdownWidget

from blog.models import BlogCategory, BlogPost, BlogPostCategory, BlogPostTag, BlogTag
from bruceyversion.models import Entry
from library.models import Article, Collection

from . import models as db_models

# Unregister the default User admin
site.unregister(Group)


class CustomModelAdmin(ModelAdmin):
  # 1. Globally mark these as read-only for any inheriting class
  readonly_fields = ("created_at", "updated_at")


@admin.register(db_models.CustomUser)
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

  def get_readonly_fields(
    self,
    request: HttpRequest,
    obj: Any | None = ...,
  ) -> list[str] | tuple[str, ...] | tuple[Never]:
    fields = super().get_readonly_fields(request, obj)
    return (*fields, "date_joined", "last_login")

  def get_search_results(
    self,
    request,
    queryset,
    search_term,
  ) -> QuerySet[Any, Any] | tuple[QuerySet[Any, Any], bool]:
    # Apply filter during autocomplete requests
    if "autocomplete" in request.path:
      queryset = queryset.filter(groups=3)

    return super().get_search_results(request, queryset, search_term)

  form = UserChangeForm
  add_form = UserCreationForm
  change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
  pass


class EventTypeInline(StackedInline):
  model = db_models.EventType
  autocomplete_fields = ["type"]
  search_fields = ["type__name"]

  def get_queryset(self, request) -> QuerySet[Any, Any]:
    return (
      super()
      .get_queryset(request)
      .select_related(
        "event",
        "type",
      )
    )

  collapsible = True

  fields = ["event", "type"]
  fk_name = "event"
  ordering = ("type__name",)
  extra = 0


class EventTagInline(StackedInline):
  model = db_models.EventTag
  autocomplete_fields = ["tag"]
  search_fields = ["tag__name"]

  def get_queryset(self, request):
    return (
      super()
      .get_queryset(request)
      .select_related(
        "event",
        "tag",
      )
    )

  collapsible = True

  fields = ["event", "tag"]
  fk_name = "event"
  ordering = ("tag__name",)
  extra = 0


class OnstageInline(StackedInline):
  model = db_models.Onstage
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

  fields = ["relation", "band", "note", "guest", "event"]
  fk_name = "event"
  ordering = ("relation__name",)
  extra = 0


class SetlistInline(StackedInline):
  model = db_models.Setlist
  collapsible = True
  ordering_field = "position"

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

  fields = [
    "set_name",
    "song_num",
    "song",
    "segue",
    "note",
    ("nobruce", "instrumental", "sign_request"),
    "position",
  ]
  fk_name = "event"
  ordering = ("song_num",)
  extra = 0


class ReleaseTrackInline(StackedInline):
  model = db_models.ReleaseTrack
  collapsible = True

  def get_queryset(self, request):
    base_qs = super().get_queryset(request)
    return (
      base_qs.select_related("song", "release")
      .prefetch_related("event", "disc")
      .order_by("discnum", Cast("track", output_field=dj_models.IntegerField()))
    )

  autocomplete_fields = ["song", "event", "disc"]

  fields = [
    "discnum",
    "disc",
    "track",
    "song",
    "event",
    "length",
    "note",
  ]
  fk_name = "release"
  ordering = ("discnum", "track")
  extra = 0


@admin.register(db_models.ArchiveLinks)
class ArchiveAdmin(CustomModelAdmin):
  search_fields = ["event__id", "url"]
  list_select_related = ["event", "event__venue", "event__venue__city"]
  autocomplete_fields = ["event"]
  list_display = ["id", "url"]
  list_display_links = ["id"]


@admin.register(db_models.UserAttendedShow)
class UserAttendedShowsAdmin(CustomModelAdmin):
  def get_queryset(self, request: HttpRequest) -> QuerySet:
    return (
      super()
      .get_queryset(request)
      .select_related("user", "event", "event__venue", "event__venue__city")
    )

  search_fields = ["user__username", "event", "event__date"]
  list_select_related = [
    "user",
    "event__venue__city",
  ]
  list_display = ["id", "user__username", "event"]
  autocomplete_fields = ["user", "event"]
  list_display_links = ["id"]


class NoteForm(forms.ModelForm):
  note = forms.CharField(
    widget=MarkdownWidget(),
  )


class BandsForm(NoteForm):
  note = forms.CharField(
    widget=MarkdownWidget(),
    required=False,
  )

  class Meta:
    model = db_models.Band
    fields = "__all__"


class RunForm(NoteForm):
  note = forms.CharField(
    widget=MarkdownWidget(),
  )

  class Meta:
    model = db_models.Run
    fields = "__all__"


@admin.register(db_models.Band)
class BandAdmin(CustomModelAdmin):
  form = BandsForm
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


@admin.register(db_models.Guest)
class GuestAdmin(CustomModelAdmin):
  autocomplete_fields = ["setlist", "relation"]
  search_fields = [
    "relation__name",
    "setlist__id",
    "setlist__event__event_id",
    "setlist__song__name",
  ]
  list_display = [
    "setlist__id",
    "setlist__event__event_id",
    "setlist__song",
    "relation__name",
  ]
  list_select_related = ["setlist", "relation", "setlist__song", "setlist__event"]


@admin.register(db_models.Bootleg)
class BootlegAdmin(CustomModelAdmin):
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


@admin.register(db_models.City)
class CityAdmin(CustomModelAdmin):
  search_fields = ["name"]
  list_select_related = [
    "state",
    "country",
    "first_event__venue",
    "last_event__venue",
  ]
  autocomplete_fields = ["state", "country", "first_event", "last_event"]
  list_display = ["id", "name", "state", "country", "timezone"]
  list_display_links = ["id", "state", "country"]


@admin.register(db_models.Continent)
class ContinentAdmin(CustomModelAdmin):
  search_fields = ["name"]
  list_display = ["id", "name"]
  list_display_links = ["id", "name"]


@admin.register(db_models.Country)
class CountryAdmin(CustomModelAdmin):
  search_fields = ["name"]
  list_display = ["id", "name"]
  list_display_links = ["id", "name"]
  list_select_related = [
    "first_event__venue",
    "last_event__venue",
  ]
  autocomplete_fields = ["first_event", "last_event", "continent"]


@admin.register(db_models.Cover)
class CoverAdmin(CustomModelAdmin):
  search_fields = ["event"]
  list_select_related = ["event", "event__venue", "event__venue__city"]
  list_display = ["id", "event", "url"]
  autocomplete_fields = ["event"]

  list_display_links = ["id", "event"]


@admin.register(db_models.NugsRelease)
class NugsAdmin(CustomModelAdmin):
  search_fields = ["event"]
  autocomplete_fields = ["event"]

  list_select_related = ["event", "event__venue", "event__venue__city"]
  list_display = ["id", "event", "url", "date"]
  list_display_links = ["id", "event"]


class EventForm(forms.ModelForm):
  note = forms.CharField(
    widget=MarkdownWidget(),
    required=False,
  )

  exclude = ["summary", "type"]

  brucebase_url = dj_models.CharField(max_length=255)
  title = dj_models.CharField(max_length=255)

  class Meta:
    model = db_models.Event
    fields = "__all__"

  def clean(self):
    cleaned_data = super().clean()
    changed_data = self.changed_data

    location = cleaned_data.get("venue", None)

    if location:
      tz = location.city.timezone

      # 1. FIX: Mutate AND explicitly save back to self.instance.
      # Without explicitly binding to self.instance, Django admin completely
      # drops your timezone manipulations and falls back to project default UTC.
      if "scheduled_time" in changed_data and cleaned_data.get("scheduled_time"):
        cleaned_data["scheduled_time"] = cleaned_data["scheduled_time"].replace(
          tzinfo=tz,
        )
        self.instance.scheduled_time = cleaned_data["scheduled_time"]

      if "start_time" in changed_data and cleaned_data.get("start_time"):
        cleaned_data["start_time"] = cleaned_data["start_time"].replace(
          tzinfo=tz,
        )
        self.instance.start_time = cleaned_data["start_time"]

      if "end_time" in changed_data and cleaned_data.get("end_time"):
        cleaned_data["end_time"] = cleaned_data["end_time"].replace(tzinfo=tz)
        self.instance.end_time = cleaned_data["end_time"]

    # 2. FIX: Calculate length safely using the modified timezoned objects
    # We look up the freshly altered cleaned_data first, falling back to
    # what's currently assigned to the instance if a field wasn't changed.
    start = cleaned_data.get("start_time") or getattr(
      self.instance,
      "start_time",
      None,
    )
    end = cleaned_data.get("end_time") or getattr(self.instance, "end_time", None)

    if start and end:
      # Subtraction gives a Python timedelta object
      duration = end - start
      total_seconds = int(duration.total_seconds())

      if total_seconds >= 0:
        # Math to extract whole hours and remaining minutes
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        # 3. FIX: Convert the calculated duration into a datetime.time object
        # This formatting is compatible with Django's TimeField requirements
        self.instance.length = time(hour=hours, minute=minutes)
        cleaned_data["length"] = time(hour=hours, minute=minutes)
      else:
        # Fallback error check if end time is configured before the start time
        msg = "End time cannot be earlier than start time."
        raise forms.ValidationError(
          msg,
        )
    else:
      self.instance.length = None
      cleaned_data["length"] = None

    return cleaned_data


@admin.register(db_models.Event)
class EventAdmin(CustomModelAdmin):
  form = EventForm

  def get_queryset(self, request: HttpRequest) -> QuerySet:
    return (
      super()
      .get_queryset(request)
      .select_related("venue", "tour", "artist")
      .prefetch_related("run", "leg")
    )

  search_fields = ["id", "event_id", "date"]
  autocomplete_fields = [
    "venue",
    "artist",
    "tour",
    "run",
    "leg",
  ]

  exclude = ("summary", "type")

  list_display = ["id", "date", "event_id"]
  list_display_links = ["id"]
  inlines = [EventTypeInline, EventTagInline, SetlistInline, OnstageInline]

  def save_model(self, request, obj, form, change):
    if not change:
      # IT IS A NEW CREATION
      # Temporarily hide the 'summary' field from the ORM compiler for this save
      original_fields = obj._meta.local_fields
      try:
        obj._meta.local_fields = [f for f in original_fields if f.name != "summary"]
        obj.save()  # Performs a clean INSERT completely ignoring 'summary'
      finally:
        # Always restore the original fields list to prevent side-effects
        obj._meta.local_fields = original_fields
    else:
      # IT IS AN UPDATE
      # Grab every field name except 'summary' and 'id'
      fields_to_update = [
        f.name for f in obj._meta.fields if f.name not in {"summary", "id"}
      ]
      obj.save(update_fields=fields_to_update)


@admin.register(db_models.Type)
class TypeAdmin(CustomModelAdmin):
  search_fields = ["name", "slug"]
  list_display = ["id", "name"]
  list_display_links = ["id"]


# @admin.register(db_models.EventType)
# class EventTypeAdmin(ModelAdmin):
#   autocomplete_fields = ["event", "type"]
#   search_fields = ["type__name", "type__slug"]
#   list_display = ["event", "type"]
#   list_select_related = ["event", "type", "event__venue", "event__venue__city"]
#   list_display_links = ["event", "type"]


@admin.register(db_models.Tag)
class TagAdmin(CustomModelAdmin):
  search_fields = ["name", "slug"]
  list_display = ["id", "name"]
  prepopulated_fields = {"slug": ("name",)}
  list_display_links = ["id"]


# @admin.register(db_models.EventTag)
# class EventTagAdmin(ModelAdmin):
#   def get_queryset(self, request):
#     return super().get_queryset(request).select_related("tag", "event")

#   search_fields = ["tag__name", "tag__slug"]
#   list_display = ["event", "tag"]
#   autocomplete_fields = ["event", "tag"]
#   list_select_related = ["event", "tag"]
#   list_display_links = ["event", "tag"]


@admin.register(db_models.Song)
class SongAdmin(CustomModelAdmin):
  search_fields = ["name", "original_artist"]
  list_select_related = ["first_event", "last_event", "album"]
  autocomplete_fields = ["first_event", "last_event", "album"]
  list_display = ["id", "name"]
  prepopulated_fields = {"slug": ("name",)}
  list_display_links = ["id"]
  ordering = ("name",)


class LyricForm(forms.ModelForm):
  text = forms.CharField(
    widget=MarkdownWidget(),
  )

  class Meta:
    model = db_models.Lyric
    fields = "__all__"


@admin.register(db_models.Lyric)
class LyricsAdmin(CustomModelAdmin):
  search_fields = ["song__name", "text"]
  autocomplete_fields = ["song"]
  list_display = ["id", "song__name"]
  list_display_links = ["id"]
  list_select_related = ["song"]
  ordering = ("song__name",)

  form = LyricForm


class SetlistNoteInline(StackedInline):
  model = db_models.SetlistNote
  collapsible = True

  def get_queryset(self, request):
    return super().get_queryset(request).select_related("setlist")

  fields = [
    "setlist",
    "num",
    "note",
  ]

  fk_name = "setlist"
  extra = 0

  autocomplete_fields = ["setlist"]
  list_select_related = ["setlist"]

  list_display = ["setlist", "num", "note"]


@admin.register(db_models.Setlist)
class SetlistAdmin(CustomModelAdmin):
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
  readonly_fields = ["last", "next", "tour_num", "tour_total", "ltp"]
  list_display_links = ["id", "event", "song"]
  inlines = [SetlistNoteInline]


@admin.register(db_models.Onstage)
class OnstageAdmin(CustomModelAdmin):
  def get_queryset(self, request):
    return (
      super()
      .get_queryset(request)
      .select_related("relation", "band", "event", "event__venue", "event__venue__city")
    )

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


@admin.register(db_models.Relation)
class RelationAdmin(CustomModelAdmin):
  def get_queryset(self, request):
    return (
      super()
      .get_queryset(request)
      .select_related(
        "first_event",
        "last_event",
        "first_event__venue",
        "last_event__venue",
      )
    )

  search_fields = ["name"]
  list_display = ["id", "name"]
  list_select_related = ["first_event", "last_event"]
  autocomplete_fields = ["first_event", "last_event"]
  list_display_links = ["id"]
  ordering = ("name",)


@admin.register(db_models.ReleaseDisc)
class ReleaseDiscAdmin(CustomModelAdmin):
  search_fields = ["release__name"]
  list_display = ["id", "name", "release__name"]
  list_select_related = ["release"]
  autocomplete_fields = ["release"]
  list_display_links = ["id"]


@admin.register(db_models.ReleaseTrack)
class ReleaseTrackAdmin(CustomModelAdmin):
  def get_queryset(self, request):
    return (
      super()
      .get_queryset(request)
      .select_related("release", "song")
      .prefetch_related("event", "disc", "setlist")
    )

  search_fields = ["release__name", "song__name"]
  list_select_related = ["release", "song", "event", "disc", "setlist"]
  list_display = ["id", "release__name", "track", "song", "song__name"]
  autocomplete_fields = ["release", "song", "event", "disc", "setlist"]
  list_display_links = ["id"]


class ReleaseForm(forms.ModelForm):
  note = forms.CharField(
    widget=MarkdownWidget(),
    required=False,
  )

  class Meta:
    model = db_models.Release
    fields = "__all__"


@admin.register(db_models.Release)
class ReleaseAdmin(CustomModelAdmin):
  def get_queryset(self, request):
    base_qs = super().get_queryset(request)
    return base_qs.prefetch_related("event")

  form = ReleaseForm
  search_fields = ["name", "type"]
  list_display = ["id", "name", "type", "date", "mbid"]
  list_display_links = ["id"]
  autocomplete_fields = ["event"]
  prepopulated_fields = {"slug": ("name",)}
  inlines = [ReleaseTrackInline]


@admin.register(db_models.Snippet)
class SnippetAdmin(CustomModelAdmin):
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


@admin.register(db_models.State)
class StateAdmin(CustomModelAdmin):
  search_fields = ["name", "abbrev", "country__name"]
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


@admin.register(db_models.Tour)
class TourAdmin(CustomModelAdmin):
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
  prepopulated_fields = {"slug": ("name",)}

  list_display_links = ["id"]


@admin.register(db_models.TourLeg)
class TourLegAdmin(CustomModelAdmin):
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
  prepopulated_fields = {"slug": ("name",)}
  list_display_links = ["id"]


@admin.register(db_models.Venue)
class VenueAdmin(CustomModelAdmin):
  search_fields = ["name"]
  list_select_related = [
    "first_event",
    "last_event",
    "city",
    "first_event__venue",
    "last_event__venue",
  ]
  list_display = [
    "id",
    "name",
    "first_event",
    "last_event",
    "city__name",
  ]

  def get_queryset(self, request):
    base_qs = super().get_queryset(request)
    return base_qs.prefetch_related("first_event", "last_event").select_related("city")

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


@admin.register(db_models.Run)
class RunAdmin(CustomModelAdmin):
  form = RunForm
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
  prepopulated_fields = {"slug": ("name",)}
  list_display = ["id", "name", "band", "num_events", "first_event", "last_event"]
  list_display_links = ["id"]


@admin.register(db_models.Contact)
class ContactAdmin(CustomModelAdmin):
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

  def get_readonly_fields(
    self,
    request: HttpRequest,
    obj: Any | None = ...,
  ) -> list[str] | tuple[str, ...] | tuple[Never]:
    fields = super().get_readonly_fields(request, obj)
    return (*fields, "message")


@admin.register(BlogCategory)
class BlogCategoryAdmin(CustomModelAdmin):
  list_display = ("name", "slug", "created_at")
  search_fields = ["name", "slug"]
  prepopulated_fields = {"slug": ("name",)}
  readonly_fields = ("created_at", "updated_at")


@admin.register(BlogTag)
class BlogTagAdmin(CustomModelAdmin):
  list_display = ("name", "slug", "created_at")
  search_fields = ["name", "slug"]
  prepopulated_fields = {"slug": ("name",)}
  readonly_fields = ("created_at", "updated_at")


class TagInline(StackedInline):
  model = BlogPostTag
  autocomplete_fields = ["tag"]
  extra = 0


class CategoryInline(StackedInline):
  model = BlogPostCategory
  autocomplete_fields = ["category"]
  extra = 0


class PostForm(forms.ModelForm):
  body = forms.CharField(
    widget=MarkdownWidget(),
  )

  class Meta:
    model = BlogPost
    fields = [
      "title",
      "slug",
      "author",
      "excerpt",
      "published",
      "published_at",
      "body",
    ]


@admin.register(BlogPost)
class PostAdmin(CustomModelAdmin):
  form = PostForm
  list_filter = (
    "published",
    "author",
    "created_at",
  )

  list_display = ("title", "author", "published", "created_at")
  search_fields = ("title", "body")
  prepopulated_fields = {"slug": ("title",)}
  exclude = ("categories", "tags")  # Prevent double-rendering of fields

  autocomplete_fields = ["author"]
  list_select_related = ["author"]

  # Add the inlines here
  inlines = [CategoryInline, TagInline]

  # 1. Filter the list so they only see their own posts
  def get_queryset(self, request):
    qs = super().get_queryset(request)

    if request.user.is_superuser:
      return qs

    return qs.filter(author=request.user)

  # 2. Prevent editing if they somehow access another user's post URL
  def has_change_permission(self, request, obj=None):
    if obj is not None and not request.user.is_superuser and obj.author != request.user:
      return False
    return super().has_change_permission(request, obj)

  # 3. Prevent deleting if they aren't the owner
  def has_delete_permission(self, request, obj=None):
    if obj is not None and not request.user.is_superuser and obj.author != request.user:
      return False
    return super().has_delete_permission(request, obj)


@admin.register(Collection)
class CollectionAdmin(CustomModelAdmin):
  list_display = ("name", "slug", "created_at")
  search_fields = ["name", "slug"]
  prepopulated_fields = {"slug": ("name",)}


class ArticleForm(forms.ModelForm):
  content = forms.CharField(
    widget=MarkdownWidget(),
  )

  class Meta:
    model = Article
    fields = [
      "title",
      "slug",
      "author",
      "collection",
      "excerpt",
      "published_at",
      "content",
    ]


@admin.register(Article)
class ArticleAdmin(CustomModelAdmin):
  form = ArticleForm

  def get_queryset(self, request: HttpRequest) -> dj_models.QuerySet:
    return (
      super()
      .get_queryset(request)
      .select_related("collection")
      .prefetch_related("event")
    )

  list_display = ("title", "author", "created_at")
  search_fields = ["title", "author", "content"]
  list_select_related = ["collection"]
  autocomplete_fields = ["collection", "event"]
  prepopulated_fields = {"slug": ("title",)}


@admin.register(Entry)
class EntryAdmin(CustomModelAdmin):
  # This places action buttons directly inside each row of the table list
  list_display = ["id", "status_badge"]
  actions_row = ["mark_row_approved", "mark_row_rejected"]

  @display(
    description="Moderation Status",
    ordering="status",  # Enables column header sorting
    label={
      Entry.ModerationStatus.APPROVED: "success",  # Green badge
      Entry.ModerationStatus.REJECTED: "danger",  # Red badge
      Entry.ModerationStatus.PENDING: "warning",  # Orange/Yellow badge
    },
  )
  def status_badge(self, obj: Entry):
    # Return the human-readable text label choice
    return obj.status

  @action(description="Approve", icon="check_circle", url_path="approve-row")  # type: ignore
  def mark_row_approved(
    self,
    request: HttpRequest,
    object_id: int,
  ) -> HttpResponseRedirect:
    Entry.objects.filter(pk=object_id).update(
      status=Entry.ModerationStatus.APPROVED,
    )
    self.message_user(request, "Entry approved.", messages.SUCCESS)

    # 3. Redirect back to the entry list page to refresh the view
    return redirect(
      reverse_lazy("admin:bruceyversion_entries_changelist"),
    )

  @action(description="Reject", icon="cancel", url_path="reject-row")  # type: ignore
  def mark_row_rejected(
    self,
    request: HttpRequest,
    object_id: int,
  ) -> HttpResponseRedirect:
    Entry.objects.filter(pk=object_id).update(
      status=Entry.ModerationStatus.REJECTED,
    )
    self.message_user(request, "Entry rejected.", messages.WARNING)

    # 3. Redirect back to the entry list page to refresh the view
    return redirect(
      reverse_lazy("admin:bruceyversion_entries_changelist"),
    )

  def get_queryset(self, request: HttpRequest) -> dj_models.QuerySet:
    return super().get_queryset(request).select_related("user", "event", "song")

  list_select_related = ["user", "event", "song"]
  autocomplete_fields = ["user", "event", "song"]
  search_fields = ["user__username", "comment", "status"]
