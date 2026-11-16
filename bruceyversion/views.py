from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import F, OuterRef
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView

from api.views import SubqueryCount
from databruce import models as db_models
from databruce.mixins import PageTitleMixin

from . import forms
from . import models as bv_models

users = bv_models.EntryVote.objects.filter(entry__user_id=OuterRef("user"))


class EntrySubmit(LoginRequiredMixin, PageTitleMixin, TemplateView):
  template_name = "bruceyversion/submit_form.html"
  title = "Bruceyversion Submit Form"
  form = forms.SubmitForm

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context["title"] = self.title
    context["form"] = self.form

    messages.warning(
      self.request,
      "Note: Only one entry can be submitted for a given song and show. Submitting one for an existing song/show will instead submit as a comment to that entry instead.",
    )

    return context

  def post(
    self,
    request: HttpRequest,
    *args,
    **kwargs,
  ) -> HttpResponseRedirect | HttpResponse:
    form = self.form(request.POST)

    if form.is_valid():
      form.cleaned_data["user"] = request.user

      try:
        entry, created = bv_models.Entry.objects.get_or_create(
          **form.cleaned_data,
        )

        if created:
          messages.success(request, "Your entry has been submitted successfully")

          return redirect(
            reverse("bruceyversion:entry_detail", kwargs={"id": entry.uuid}),
          )
      except IntegrityError:
        # if an entry exists, instead submit a comment to that entry
        entry = bv_models.Entry.objects.get(
          song=form.cleaned_data["song"],
          event=form.cleaned_data["event"],
        )

        bv_models.EntryComment.objects.create(
          user=request.user,
          entry=entry,
          comment=form.cleaned_data["comment"],
        )

        messages.success(request, "Your comment has been submitted successfully")

        return redirect(
          reverse("bruceyversion:entry_detail", kwargs={"id": entry.uuid}),
        )

    messages.error(request, "Error submitting entry")

    return render(
      request,
      template_name=self.template_name,
      context={"form": form},
    )


class EntryListView(PageTitleMixin, TemplateView):
  template_name = "bruceyversion/entries.html"
  title = "Bruceyversion Entries"

  def get_context_data(self, **kwargs) -> dict[str, Any]:
    context = super().get_context_data(**kwargs)
    context["title"] = self.title

    context["users"] = users

    queryset = (
      bv_models.Entry.objects.select_related(
        "user",
        "event",
        "song",
      )
      .filter(status=bv_models.Entry.ModerationStatus.APPROVED)
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


class EntryDetailView(PageTitleMixin, TemplateView):
  template_name = "bruceyversion/entry_detail.html"
  title = "Bruceyversion Entry Detail"
  description = "Bruceyversion Entry Detail"
  form = forms.CommentForm

  def get_context_data(self, **kwargs) -> dict[str, Any]:
    context = super().get_context_data(**kwargs)
    context["title"] = self.title

    context["entry"] = get_object_or_404(
      bv_models.Entry.objects.select_related(
        "user",
        "event",
        "song",
      ).prefetch_related("entry_comment"),
      uuid=self.kwargs["id"],
    )

    if context["entry"].status == bv_models.Entry.ModerationStatus.PENDING:
      messages.warning(self.request, "This entry is awaiting moderation")

    if context["entry"].status == bv_models.Entry.ModerationStatus.REJECTED:
      messages.error(self.request, "This entry has been rejected")

    context["description"] = context["entry"].comment
    context["form"] = self.form

    if self.request.user.is_authenticated:
      context["user_voted"] = bv_models.EntryVote.objects.filter(
        user=self.request.user,
        entry=context["entry"].id,
      ).exists()

      try:
        context["user_comment"] = bv_models.EntryComment.objects.get(
          user=self.request.user,
          entry=context["entry"].id,
        )

        context["form"] = self.form(
          initial={"comment": context["user_comment"].comment},
        )
      except bv_models.EntryComment.DoesNotExist:
        context["user_comment"] = None
        context["form"] = self.form()

    else:
      context["user_voted"] = False
      context["user_comment"] = None

    return context


@method_decorator(login_required, name="dispatch")
class EntryVote(View):
  def post(self, request: HttpRequest, entry_id: int, *args, **kwargs) -> JsonResponse:
    # Support both URL kwargs (recommended) and fallback form/JSON data
    entry = get_object_or_404(bv_models.Entry, id=entry_id)

    try:
      with transaction.atomic():
        # Lock the Entry row to prevent concurrent race conditions on vote counts
        entry = bv_models.Entry.objects.select_for_update().get(id=entry.id)

        vote, created = bv_models.EntryVote.objects.get_or_create(
          entry=entry,
          user=request.user,
        )

        if created:
          bv_models.Entry.objects.filter(id=entry.id).update(votes=F("votes") + 1)
          voted = True
          message = "You have successfully voted for this entry."
        else:
          vote.delete()
          # Ensure votes never drop below 0
          bv_models.Entry.objects.filter(id=entry.id, votes__gt=0).update(
            votes=F("votes") - 1
          )
          voted = False
          message = "Your vote has been removed."

        # Refresh entry instance to get updated vote count
        entry.refresh_from_db(fields=["votes"])

    except Exception as e:
      return JsonResponse(
        {
          "success": False,
          "message": "An error occurred while processing your vote.",
          "error": str(e),
        },
        status=400,
      )

    return JsonResponse(
      {
        "success": True,
        "message": message,
        "votes": entry.votes,
        "voted": voted,
      },
      status=200,
    )


class SubmitEntryComment(View):
  def post(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
    form = forms.CommentForm(request.POST)

    if form.is_valid():
      item, created = bv_models.EntryComment.objects.update_or_create(
        user_id=request.user.id,
        entry_id=request.POST["entry"],
        defaults=form.cleaned_data,
      )

      if not created:
        return JsonResponse(
          {
            "success": True,
            "message": "Your comment has been updated successfully",
          },
        )

      return JsonResponse(
        {"success": True, "message": "Your comment has been created successfully"},
      )

    return JsonResponse({"success": False, "errors": form.errors})


class SongEntryListView(TemplateView):
  template_name = "bruceyversion/entries_by_song.html"
  title = "Bruceyversion Entries By Song"

  def get_context_data(self, **kwargs) -> dict[str, Any]:
    context = super().get_context_data(**kwargs)
    queryset = (
      bv_models.Entry.objects.select_related("song")
      .filter(
        song__slug=self.kwargs["slug"],
      )
      .annotate(user_vote_count=SubqueryCount(users))
      .order_by("-votes")
    )

    if queryset:
      context["song"] = queryset.first().song
    else:
      context["song"] = db_models.Song.objects.get(slug=self.kwargs["slug"])

    context["title"] = f"Bruceyversion Entries for: {context['song'].name}"

    paginator = Paginator(queryset, 10)
    page_number = self.request.GET.get("page", 1)
    context["page"] = paginator.get_page(page_number)

    return context


class EventEntryListView(TemplateView):
  template_name = "bruceyversion/entries_by_event.html"
  title = "Bruceyversion Entries By Event"

  def get_context_data(self, **kwargs) -> dict[str, Any]:
    context = super().get_context_data(**kwargs)

    queryset = (
      bv_models.Entry.objects.select_related("event")
      .filter(
        event__event_id=self.kwargs["id"],
      )
      .annotate(user_vote_count=SubqueryCount(users))
      .order_by("-votes")
    )

    if queryset:
      context["event"] = queryset.first().event
    else:
      context["event"] = db_models.Event.objects.get(event_id=self.kwargs["id"])

    context["title"] = f"Bruceyversion Entries for: {context['event'].get_date()}"

    paginator = Paginator(queryset, 10)
    page_number = self.request.GET.get("page", 1)
    context["page"] = paginator.get_page(page_number)

    return context


class SongListView(TemplateView):
  template_name = "bruceyversion/songs.html"
  title = "Bruceyversion Songs"

  def get_context_data(self, **kwargs) -> dict[str, Any]:
    context = super().get_context_data(**kwargs)
    context["title"] = self.title

    queryset = (
      bv_models.Entry.objects.select_related("song")
      .annotate(
        song_name=F("song__name"),
        song_votes=SubqueryCount(
          bv_models.EntryVote.objects.filter(entry=OuterRef("id")),
        ),
      )
      .order_by("-song_votes")
    )

    context["songs"] = queryset

    return context
