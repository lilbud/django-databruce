from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, OuterRef
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
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
      "Note: Only one entry can be submitted for a given song and show. If your entry is already taken, check the <a href='/entries/'>entries page</a> and vote or comment on it instead.",
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
      form.cleaned_data["user"] = db_models.CustomUser.objects.get(pk=request.user.id)  # type: ignore

      entry, created = bv_models.Entry.objects.get_or_create(
        **form.cleaned_data,
      )

      if created:
        messages.success(request, "Your entry has been submitted successfully")

        return redirect(
          reverse("bruceyversion:entry_detail", kwargs={"id": entry.uuid}),
        )

      messages.error(
        request,
        "An entry has already been submitted for this song and show",
      )

      return render(
        request,
        template_name=self.template_name,  # type: ignore
        context={"form": form},
      )

    messages.error(request, "Error submitting entry")
    return render(
      request,
      template_name=self.template_name,  # type: ignore
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

    context["entry"] = (
      bv_models.Entry.objects.select_related(
        "user",
        "event",
        "song",
      )
      .prefetch_related("entry_comment")
      .get(uuid=self.kwargs["id"])
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


class EntryVote(View):
  def post(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
    entry_id = request.POST.get("entry")
    entry = get_object_or_404(bv_models.Entry, id=entry_id)

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
      vote, created = bv_models.EntryVote.objects.get_or_create(
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


class SubmitEntryComment(View):
  def post(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
    form = forms.CommentForm(request.POST)

    if form.is_valid():
      form.cleaned_data["user"] = db_models.CustomUser.objects.get(pk=request.user.id)  # type: ignore
      form.cleaned_data["entry"] = bv_models.Entry.objects.get(
        pk=request.POST["entry"],
      )

      bv_models.EntryComment.objects.create(
        **form.cleaned_data,
      )

      return JsonResponse(
        {"success": True, "message": "Your comment has been submitted successfully"},
      )

    return JsonResponse({"success": False, "errors": form.errors})


class UpdateEntryComment(View):
  def post(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
    form = forms.CommentForm(request.POST)

    if form.is_valid():
      comment = bv_models.EntryComment.objects.get(
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


class SongEntryListView(TemplateView):
  template_name = "bruceyversion/entries_by_song.html"
  title = "Bruceyversion Entries By Song"

  def get_context_data(self, **kwargs) -> dict[str, Any]:
    context = super().get_context_data(**kwargs)
    queryset = (
      bv_models.Entry.objects.select_related("song")
      .filter(
        song__uuid=self.kwargs["id"],
      )
      .annotate(user_vote_count=SubqueryCount(users))
      .order_by("-votes")
    )

    if queryset:
      context["song"] = queryset.first().song  # type: ignore
    else:
      context["song"] = db_models.Song.objects.get(uuid=self.kwargs["id"])

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
      context["event"] = queryset.first().event  # type: ignore
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
