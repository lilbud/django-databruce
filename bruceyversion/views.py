from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, OuterRef
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from api.views import SubqueryCount
from databruce import models as db_models
from databruce.views import PageTitleMixin

from . import forms
from . import models as bv_models

users = bv_models.EntryVotes.objects.filter(entry__user_id=OuterRef("user"))


class GroupRequiredMixin(AccessMixin):
  """CBV mixin to restrict access by group names."""

  allowed_groups = ["Beta Testers", "Admin"]

  def dispatch(self, request, *args, **kwargs):
    if not request.user.is_authenticated:
      return self.handle_no_permission()

    # Check if the user belongs to any group in allowed_groups
    in_group = request.user.groups.filter(name__in=self.allowed_groups).exists()

    if not in_group and not request.user.is_superuser:
      raise PermissionDenied

    return super().dispatch(request, *args, **kwargs)  # type: ignore


class Submit(GroupRequiredMixin, PageTitleMixin, TemplateView):
  template_name = "bruceyversion/submit_form.html"
  title = "Bruceyversion Submit Form"
  form = forms.SubmitForm

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context["title"] = self.title
    context["form"] = self.form

    return context

  def post(self, request: HttpRequest, *args, **kwargs):
    form = self.form(request.POST)

    if form.is_valid():
      form.cleaned_data["user"] = db_models.CustomUser.objects.get(pk=request.user.id)  # type: ignore

      bv_models.Entries.objects.create(
        **form.cleaned_data,
      )

      messages.success(request, "Your entry has been submitted successfully")

      return redirect(reverse("bruceyversion:submit"))

    messages.error(request, "Error submitting entry")
    return render(
      request,
      template_name=self.template_name,  # type: ignore
      context={"form": form},
    )


class EntriesList(PageTitleMixin, TemplateView):
  template_name = "bruceyversion/entries.html"
  title = "Bruceyversion Entries"

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context["title"] = self.title

    context["users"] = users

    queryset = (
      bv_models.Entries.objects.select_related(
        "user",
        "event",
        "song",
      )
      .exclude(hidden=True)
      .order_by("-created_at")
      .annotate(
        user_vote_count=SubqueryCount(
          users,
        ),
      )
    )

    paginator = Paginator(queryset, 10)
    page_number = self.request.GET.get("page", 1)
    context["page"] = paginator.get_page(page_number)

    return context


class EntryDetail(PageTitleMixin, TemplateView):
  template_name = "bruceyversion/entry_detail.html"
  title = "Bruceyversion Entry Detail"
  description = "Bruceyversion Entry Detail"
  form = forms.CommentForm

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context["title"] = self.title

    context["entry"] = bv_models.Entries.objects.select_related(
      "user",
      "event",
      "song",
    ).get(uuid=self.kwargs["id"])

    context["description"] = context["entry"].comment

    context["form"] = self.form

    context["comments"] = (
      bv_models.EntryComments.objects.filter(
        entry=context["entry"].pk,
      )
      .exclude(hidden=True)
      .order_by("-created_at")
    )

    if self.request.user.is_authenticated:
      context["user_voted"] = bv_models.EntryVotes.objects.filter(
        user=self.request.user,
        entry=context["entry"].id,
      ).exists()

      context["is_users_entry"] = self.request.user == context["entry"].user
      print(context["is_users_entry"])

      try:
        context["user_comment"] = bv_models.EntryComments.objects.get(
          user=self.request.user,
          entry=context["entry"].id,
        )

        context["form"] = self.form(
          initial={"comment": context["user_comment"].comment},
        )
      except bv_models.EntryComments.DoesNotExist:
        context["user_comment"] = None
        context["form"] = self.form()

    else:
      context["user_voted"] = False

    return context


class EntryVote(View):
  def post(self, request: HttpRequest, *args, **kwargs):
    entry_id = request.POST.get("entry")
    entry = get_object_or_404(bv_models.Entries, id=entry_id)

    # Prevent users from voting on their own entry on the backend
    if entry.user == request.user:
      return JsonResponse(
        {
          "message": "You cannot vote on your own entry",
          "success": False,
        },
        status=400,
      )

    with transaction.atomic():
      vote, created = bv_models.EntryVotes.objects.get_or_create(
        entry=entry,
        user=request.user,
      )

      if created:
        entry.votes += 1
        entry.save(update_fields=["votes"])
        voted = True
        message = "You have successfully voted for this entry."
      else:
        vote.delete()
        entry.votes = max(0, entry.votes - 1)
        entry.save(update_fields=["votes"])
        voted = False
        message = "Your vote has been removed."

    return JsonResponse(
      {
        "message": message,
        "votes": entry.votes,
        "voted": voted,
        "success": True,
      },
    )


class SubmitComment(View):
  def post(self, request: HttpRequest, *args, **kwargs):
    form = forms.CommentForm(request.POST)

    if form.is_valid():
      form.cleaned_data["user"] = db_models.CustomUser.objects.get(pk=request.user.id)  # type: ignore
      form.cleaned_data["entry"] = bv_models.Entries.objects.get(
        pk=request.POST["entry"],
      )

      bv_models.EntryComments.objects.create(
        **form.cleaned_data,
      )

      return JsonResponse(
        {"success": True, "message": "Your comment has been submitted successfully"},
      )

    return JsonResponse({"success": False, "errors": form.errors})


class UpdateComment(View):
  def post(self, request: HttpRequest, *args, **kwargs):
    form = forms.CommentForm(request.POST)

    if form.is_valid():
      comment = bv_models.EntryComments.objects.get(
        pk=request.POST["commentID"],
      )

      if comment.user != request.user:
        return JsonResponse({"success": False, "errors": "You can't edit this comment"})

      comment.comment = form.cleaned_data["comment"]
      comment.save()

      return JsonResponse(
        {"success": True, "message": "Your comment has been edited successfully"},
      )

    return JsonResponse({"success": False, "errors": form.errors})


class EntriesBySong(TemplateView):
  template_name = "bruceyversion/entries_by_song.html"
  title = "Bruceyversion Entries By Song"

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    queryset = (
      bv_models.Entries.objects.select_related("song")
      .filter(
        song__uuid=self.kwargs["id"],
      )
      .exclude(hidden=True)
      .annotate(user_vote_count=SubqueryCount(users))
      .order_by("-votes")
    )

    if queryset:
      context["song"] = queryset.first().song  # type: ignore
    else:
      context["song"] = db_models.Songs.objects.get(uuid=self.kwargs["id"])

    context["title"] = f"Bruceyversion Entries for: {context['song'].name}"

    paginator = Paginator(queryset, 10)
    page_number = self.request.GET.get("page", 1)
    context["page"] = paginator.get_page(page_number)

    return context


class EntriesByEvent(TemplateView):
  template_name = "bruceyversion/entries_by_event.html"
  title = "Bruceyversion Entries By Event"

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)

    queryset = (
      bv_models.Entries.objects.select_related("event")
      .filter(
        event__event_id=self.kwargs["id"],
      )
      .annotate(user_vote_count=SubqueryCount(users))
      .order_by("-votes")
    )

    if queryset:
      context["event"] = queryset.first().event  # type: ignore
    else:
      context["event"] = db_models.Events.objects.get(event_id=self.kwargs["id"])

    context["title"] = f"Bruceyversion Entries for: {context['event'].get_date()}"

    paginator = Paginator(queryset, 10)
    page_number = self.request.GET.get("page", 1)
    context["page"] = paginator.get_page(page_number)

    return context


class SongList(TemplateView):
  template_name = "bruceyversion/songs.html"
  title = "Bruceyversion Songs"

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context["title"] = self.title

    queryset = (
      bv_models.Entries.objects.select_related("song")
      .annotate(
        song_name=F("song__name"),
        song_votes=SubqueryCount(
          bv_models.EntryVotes.objects.filter(entry=OuterRef("id")),
        ),
      )
      .exclude(hidden=True)
      .order_by("-song_votes")
    )

    context["songs"] = queryset

    return context
