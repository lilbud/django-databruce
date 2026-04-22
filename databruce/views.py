import calendar
import datetime
import json
import logging
import os
import re
from typing import Any
from zoneinfo import ZoneInfo

import markdown
import requests
from django import template
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.models import Group, User
from django.contrib.auth.tokens import (
    default_token_generator,
)
from django.contrib.auth.views import LoginView
from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.postgres.expressions import ArraySubquery
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import (
    Count,
    ExpressionWrapper,
    F,
    IntegerField,
    Max,
    Min,
    OuterRef,
    PositiveIntegerField,
    Q,
    QuerySet,
    Subquery,
    Sum,
    Value,
    Window,
)
from django.forms import formset_factory
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_list_or_404, get_object_or_404, redirect, render
from django.template import Context, Template, loader
from django.urls import reverse, reverse_lazy
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.dateparse import parse_datetime
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.safestring import mark_safe
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import TemplateView
from django_filters.filterset import filterset_factory
from shortener import shortener

from databruce import models
from databruce.config import base
from databruce.forms import (
    AdvancedEventSearch,
    ContactForm,
    LoginForm,
    SetlistNoteSearch,
    SetlistSearch,
    UpdateUserForm,
    UserForm,
)
from databruce.templatetags.filters import format_fuzzy

UserModel = get_user_model()
logger = logging.getLogger("django.contrib.auth")

VALID_SET_NAMES = [
    "Show",
    "Set 1",
    "Set 2",
    "Encore",
    "Pre-Show",
    "Post-Show",
]


class Test(TemplateView):
    model = models.Events
    template_name = "databruce/test.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        return super().get_context_data(**kwargs)


class PageTitleMixin:
    def get_page_title(self, context):
        return getattr(self, "title", None)

    def get_page_description(self, context):
        return getattr(self, "description", None)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.get_page_title(context)
        context["description"] = self.get_page_description(context)
        context["date"] = datetime.datetime.today()

        return context


class Index(PageTitleMixin, TemplateView):
    template_name = "databruce/index.html"
    title = "Home"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)

        queryset = models.Events.objects.select_related(
            "artist",
            "venue",
            "venue__city",
            "venue__venues_text",
        ).prefetch_related("venue__city__state", "setlist_event")

        latest = (
            models.Setlists.objects.filter(set_name__in=VALID_SET_NAMES)
            .select_related("event")
            .order_by("-event__event_id")
            .first()
            .event.id
        )

        context["latest_event"] = queryset.get(id=latest)

        return context


class Song(PageTitleMixin, TemplateView):
    template_name = "databruce/songs/songs.html"
    title = "Songs"


class About(PageTitleMixin, TemplateView):
    template_name = "databruce/about.html"
    title = "About"


class Roadmap(PageTitleMixin, TemplateView):
    template_name = "databruce/roadmap.html"
    title = "Roadmap"


class Links(PageTitleMixin, TemplateView):
    template_name = "databruce/links.html"
    title = "Links"


class Calendar(PageTitleMixin, TemplateView):
    template_name = "databruce/calendar.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)

        context["years"] = list(range(context["date"].year, 1964, -1))
        context["title"] = f"Event Calendar - {context['date'].strftime('%B %Y')}"
        context["description"] = f"Events in {context['date'].strftime('%B %Y')}"

        context["end_date"] = f"{context['date'].year}-12-31"

        try:
            if re.search(
                r"^\d{4}-\d{2}-\d{2}|^\d{4}-\d{2}$|^\d{4}$",
                self.request.GET["start"],
            ):
                context["start_date"] = self.request.GET["start"]
        except MultiValueDictKeyError:
            context["start_date"] = context["date"].strftime("%Y-%m-%d")

        return context


class Users(PageTitleMixin, TemplateView):
    template_name = "users/users.html"
    title = "Users"
    description = "List of Users"


class UserProfile(PageTitleMixin, TemplateView):
    template_name = "users/profile.html"
    title = "User Profile"

    def get_context_data(self, **kwargs: dict) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["info"] = get_object_or_404(UserModel, uuid=self.kwargs["id"])
        context["title"] = f'User "{context["info"]}"'
        context["description"] = f"{context['info']} Profile"
        return context


class ResendActivation(PageTitleMixin, TemplateView):
    template_name = "users/resend_activation.html"
    title = "Resend Activation"

    def post(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        email = request.POST.get("email")
        user = User.objects.filter(email=email, is_active=False).first()
        if user:
            # RE-RUN YOUR ACTIVATION EMAIL LOGIC HERE
            messages.success(request, "Activation email resent!")
        else:
            messages.error(request, "No inactive account found with that email.")

        return render(request, template_name=self.template_name)


class Login(PageTitleMixin, LoginView):
    form_class = LoginForm
    template_name = "users/login.html"
    title = "Login"
    success_url = reverse_lazy("home")

    def form_invalid(self, form):
        username = self.request.POST.get("username")
        password = self.request.POST.get("password")
        user = authenticate(self.request, username=username, password=password)

        if user is None:
            for field, errors in form.errors.items():
                for error in errors:
                    if field.title() == "__All__":
                        messages.error(self.request, f"{error}")
                    else:
                        messages.error(self.request, f"{field.title()}: {error}")

        return super().form_invalid(form)

    def form_valid(self, form):
        remember_me = form.cleaned_data.get("remember_me")

        if not remember_me:
            self.request.session.set_expiry(0)
        else:
            self.request.session.set_expiry(1209600)

        return super().form_valid(form)


class SignUp(PageTitleMixin, TemplateView):
    template_name = "users/signup.html"
    email_template_name = "users/signup_email.html"
    subject_template_name = "users/signup_confirm_subject.txt"
    title = "Signup"
    token_generator = default_token_generator
    form_class = UserForm

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form_class
        return context

    def post(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        form = self.form_class(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            current_site = get_current_site(request)
            use_https = True

            context = {
                "email": user.email,
                "domain": current_site.domain,
                "site_name": current_site.name,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "user": user,
                "token": self.token_generator.make_token(user),
                "protocol": "https" if use_https else "http",
            }

            self.send_mail(
                context=context,
                from_email=os.getenv("MAILGUN_EMAIL"),
                to_email=user.email,
            )

            return redirect(reverse("signup_done"))

        return render(request, template_name=self.template_name, context={"form": form})

    def send_mail(self, context, from_email, to_email):
        subject = loader.render_to_string(self.subject_template_name, context).strip()
        body = loader.render_to_string(self.email_template_name, context)

        # This will now be intercepted by the test runner
        return send_mail(
            subject,
            body,
            from_email,
            [to_email],
            fail_silently=False,
        )


class SignUpConfirm(PageTitleMixin, TemplateView):
    template_name = "users/signup_done.html"
    reset_url_token = "activate"  # noqa: S105
    token_generator = default_token_generator
    title = "Sign Up Complete"

    def get_user(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            user = UserModel._default_manager.get(pk=uid)  # noqa: SLF001
        except (
            TypeError,
            ValueError,
            OverflowError,
            UserModel.DoesNotExist,
            ValidationError,
        ):
            user = None
        return user

    @method_decorator(sensitive_post_parameters())
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        if "uidb64" not in kwargs or "token" not in kwargs:
            msg = "The URL path must contain 'uidb64' and 'token' parameters."
            raise ImproperlyConfigured(
                msg,
            )

        self.validlink = False
        self.user = self.get_user(kwargs["uidb64"])

        if self.user is not None:
            token = kwargs["token"]
            if token == self.reset_url_token:
                session_token = self.request.session.get(
                    os.getenv("INTERNAL_RESET_SESSION_TOKEN"),
                )
                if self.token_generator.check_token(
                    user=self.user,
                    token=session_token,
                ):
                    self.validlink = True

                    return super().dispatch(*args, **kwargs)
            else:
                if self.token_generator.check_token(
                    user=self.user,
                    token=token,
                ):
                    self.request.session[os.getenv("INTERNAL_RESET_SESSION_TOKEN")] = (
                        token
                    )

                    group = Group.objects.get(name="Users")
                    self.user.groups.add(group)
                    self.user.is_active = True
                    self.user.save()

                return redirect("login")

        return None


class UserSettings(PageTitleMixin, TemplateView):
    template_name = "users/settings.html"
    form_class = UpdateUserForm
    title = "User Settings"

    def get_context_data(self, **kwargs: dict) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["form"] = self.form_class(instance=self.request.user)

        return context

    def post(self, request: HttpRequest):
        user_form = self.form_class(request.POST, instance=request.user)

        if user_form.is_valid():
            user_form.save()
            messages.success(request, "Your profile is updated successfully")
            return redirect(reverse("settings"))

        messages.error(request, f"Error: {user_form.errors}")
        return redirect(reverse("settings"))


class SignUpDone(PageTitleMixin, TemplateView):
    template_name = "users/signup_done.html"
    title = "Sign Up Complete"


class UserRemoveShow(View):
    def post(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        models.UserAttendedShows.objects.filter(
            user_id=request.user.id,
            event_id=request.POST["event"],
        ).delete()

        return redirect(
            request.headers.get("referer", "redirect_if_referer_not_found"),
        )


class UserAddRemoveShow(View):
    def post(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        item = models.UserAttendedShows.objects.filter(
            user_id=request.POST["user"],
            event_id=request.POST["event"],
        )

        result = {}

        if item:
            models.UserAttendedShows.objects.filter(
                user_id=request.POST["user"],
                event_id=request.POST["event"],
            ).delete()

            result["action"] = "removed"
        else:
            models.UserAttendedShows.objects.create(
                user_id=request.user.id,
                event_id=request.POST["event"],
            )

            result["action"] = "added"

        count = models.UserAttendedShows.objects.filter(
            event_id=request.POST["event"],
        ).count()

        result["count"] = count

        return JsonResponse(result)


class EventDetail(PageTitleMixin, TemplateView):
    template_name = "databruce/events/detail.html"
    description = "Event Detail"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)

        context["id"] = self.kwargs["id"]

        context["event"] = get_object_or_404(
            models.Events.objects.select_related(
                "venue",
                "artist",
                "tour",
                "venue__city",
            ).prefetch_related("leg", "run", "archive_links", "nugs_event"),
            event_id=self.kwargs["id"],
        )

        context["title"] = (
            f"{context['event'].get_date()} - {context['event'].venue.name}"
        )

        context["description"] = (
            f"{context['event'].get_date()}<br>{context['event'].artist}<br>{context['event'].venue.name}"
        )

        try:
            context["scheduled_time"] = (
                context["event"]
                .scheduled_time.astimezone(
                    ZoneInfo(context["event"].venue.city.timezone),
                )
                .strftime("%I:%M%p")
                .lower()
            )
        except AttributeError:
            context["scheduled_time"] = None

        try:
            context["start_time"] = (
                context["event"]
                .start_time.astimezone(ZoneInfo(context["event"].venue.city.timezone))
                .strftime("%I:%M%p")
                .lower()
            )
        except AttributeError:
            context["start_time"] = None

        try:
            context["end_time"] = (
                context["event"]
                .end_time.astimezone(ZoneInfo(context["event"].venue.city.timezone))
                .strftime("%I:%M%p")
                .lower()
            )
        except AttributeError:
            context["end_time"] = None

        if context["event"].start_time and context["event"].end_time:
            timezone = ZoneInfo(context["event"].venue.city.timezone)

            context["duration"] = context["event"].end_time.astimezone(
                timezone,
            ) - context["event"].start_time.astimezone(
                timezone,
            )

        try:
            context["prev_event"] = (
                models.Events.objects.select_related("venue", "artist")
                .filter(event_id__lt=self.kwargs["id"])
                .order_by("-event_id")
                .first()
            )
        except models.Events.DoesNotExist:
            context["prev_event"] = None

        try:
            context["next_event"] = (
                models.Events.objects.select_related("venue", "artist")
                .filter(event_id__gt=self.kwargs["id"])
                .order_by("event_id")
                .first()
            )
        except models.Events.DoesNotExist:
            context["next_event"] = None

        if not context["event"].date:
            messages.info(
                self.request,
                "This is a placeholder date, actual date unknown.",
            )

        context["official"] = (
            models.Releases.objects.filter(
                event__event_id=self.kwargs["id"],
            )
            .prefetch_related("event")
            .order_by("date")
        )

        context["official_tracks"] = (
            models.ReleaseTracks.objects.filter(event__event_id=self.kwargs["id"])
            .select_related("release")
            .prefetch_related("event")
            .distinct("release_id", "release__date")
            .order_by("release__date")
        )

        context["title"] = (
            f"{format_fuzzy(context['event'].event_id)} {context['event'].venue.name}"
        )

        if self.request.user.is_authenticated:
            context["user_attended"] = models.UserAttendedShows.objects.filter(
                user=self.request.user.id,
                event__event_id=self.kwargs["id"],
            )

        context["user_count"] = models.UserAttendedShows.objects.filter(
            event__event_id=context["event"].event_id,
        ).count()

        return context


class Event(PageTitleMixin, TemplateView):
    template_name = "databruce/events/events.html"
    title = "Events"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)

        try:
            context["year"] = self.kwargs["year"]
        except KeyError:
            context["year"] = context["date"].year  # current year

        context["title"] = f"{context['year']} Events"
        context["description"] = f"{context['year']} Events"
        context["years"] = list(range(context["date"].year, 1964, -1))

        return context


class Venue(PageTitleMixin, TemplateView):
    template_name = "databruce/locations/venues/venues.html"
    title = "Venues"
    description = "List of Venues"

    def get_context_data(self, **kwargs: dict[str, Any]):
        return super().get_context_data(**kwargs)


class VenueDetail(PageTitleMixin, TemplateView):
    template_name = "databruce/locations/venues/detail.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)

        context["info"] = (
            models.Venues.objects.filter(
                uuid=self.kwargs["id"],
            )
            .annotate(
                aliases=ArraySubquery(
                    models.VenueAliases.objects.filter(
                        venue=OuterRef("id"),
                    ).values_list("name", flat=True),
                ),
            )
            .first()
        )

        context["title"] = f"{context['info'].name}"
        context["description"] = f"{context['info'].get_name()}"

        return context


class SongLyrics(PageTitleMixin, TemplateView):
    template_name = "databruce/songs/lyrics.html"
    title = "Lyrics"
    description = "List of Song Lyrics"

    def get_context_data(self, **kwargs: dict[str, Any]):
        return super().get_context_data(**kwargs)


class SongLyricDetail(PageTitleMixin, TemplateView):
    template_name = "databruce/songs/lyric_detail.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["lyrics"] = get_object_or_404(
            models.Lyrics.objects.filter().select_related("song"),
            uuid=self.kwargs["id"],
        )

        context["title"] = f"Lyrics for {context['lyrics'].song.name}"
        context["description"] = (
            f"Source: {context['lyrics'].source}<br>Language: {context['lyrics'].language}"
        )

        return context


class SubqueryCount(Subquery):
    # Custom Count function to just perform simple count on any queryset without grouping.
    # https://stackoverflow.com/a/47371514/1164966
    template = "(SELECT count(*) FROM (%(subquery)s) _count)"
    output_field = PositiveIntegerField()


class SongDetail(PageTitleMixin, TemplateView):
    template_name = "databruce/songs/detail.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)

        context["info"] = get_object_or_404(
            models.Songs.objects.prefetch_related(
                "album",
                "last_event",
            ),
            uuid=self.kwargs["id"],
        )

        context["title"] = f"{context['info'].name}"

        context["setlists"] = (
            models.Setlists.objects.filter(
                song_id=context["info"].id,
            )
            .select_related("event", "song")
            .prefetch_related("setlist_position")
        )

        context["positions"] = (
            context["setlists"]
            .filter(setlist_position__position__isnull=False)
            .values("setlist_position__position")
            .annotate(
                position=F("setlist_position__position"),
                count=Count("setlist_position__position"),
                num=Min("song_num"),
            )
        ).order_by("num")

        try:
            last_event = models.Events.objects.get(
                event_id=context["info"].last_event.event_id,
            ).event_id

            latest = (
                models.Events.objects.filter(
                    is_stats_eligible=True,
                    setlist_event__isnull=False,
                )
                .order_by("-event_id")
                .first()
                .event_id
            )

            print(last_event, latest)

            context["show_gap"] = models.Events.objects.filter(
                event_id__gt=last_event,
                event_id__lte=latest,
                is_stats_eligible=True,
            ).count()

        except (models.Songs.last_event.RelatedObjectDoesNotExist, AttributeError):
            context["show_gap"] = 0

        context["lyrics"] = models.Lyrics.objects.filter(
            song__uuid=self.kwargs["id"],
        ).order_by("id")

        if context["info"].num_plays_public > 0:
            # context["year_stats"] = (
            #     models.Setlists.objects.select_related("event")
            #     .filter(
            #         song__uuid=self.kwargs["id"],
            #         set_name__in=VALID_SET_NAMES,
            #         event__date__isnull=False,
            #     )
            #     .annotate(
            #         year=F("event__date__year"),
            #     )
            #     .values("year")
            #     .annotate(
            #         event_count=Count(
            #             "event",
            #             distinct=True,
            #             filter=Q(set_name__in=VALID_SET_NAMES),
            #         ),
            #     )
            #     .order_by("year")
            # )

            filter = Q(is_stats_eligible=True) & Q(
                event_id__gt=context["info"].first_event.event_id,
            )

            context["events_since_premiere"] = models.Events.objects.filter(
                filter,
            ).count()

            if context["events_since_premiere"] > 0:
                context["frequency"] = round(
                    (
                        (
                            context["info"].num_plays_public
                            / context["events_since_premiere"]
                        )
                        * 100
                    ),
                    2,
                )
            else:
                context["frequency"] = None

        return context


class EventSearch(PageTitleMixin, TemplateView):
    template_name = "databruce/search/search.html"
    title = "Event Search"


class Tour(PageTitleMixin, TemplateView):
    template_name = "databruce/tours/tours.html"
    title = "Tours"


class TourDetail(PageTitleMixin, TemplateView):
    template_name = "databruce/tours/detail.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["info"] = get_object_or_404(models.Tours, uuid=self.kwargs["id"])
        context["title"] = f"{context['info']}"

        return context


class Contact(PageTitleMixin, TemplateView):
    form_class = ContactForm
    template_name = "databruce/contact.html"
    title = "Contact"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form_class()
        return context

    def send_mail(self, context, from_email, to_email):
        subject = loader.render_to_string(self.subject_template_name, context).strip()
        body = loader.render_to_string(self.email_template_name, context)

        # This will now be intercepted by the test runner
        return send_mail(
            subject,
            body,
            from_email,
            [to_email],
            fail_silently=False,
        )

    def post(self, request: HttpRequest):
        form = self.form_class(request.POST)

        if form.is_valid():
            if form.cleaned_data["verification"] == os.environ.get(
                "VERIFICATION_ANSWER",
            ):
                use_https = False
                del form.cleaned_data["verification"]

                form.cleaned_data["is_user"] = UserModel.objects.filter(
                    email__iexact=form.cleaned_data["email"],
                ).exists()

                models.Contact.objects.create(**form.cleaned_data)

                context = {
                    "email": form.cleaned_data["email"],
                    "subject": form.cleaned_data["subject"],
                    "message": form.cleaned_data["message"],
                    "protocol": "https" if use_https else "http",
                }

                body = loader.render_to_string(
                    "databruce/email/contact_email.html",
                    context,
                )

                self.send_mail(
                    subject=form.cleaned_data["subject"],
                    message=body,
                    from_email=base.DEFAULT_FROM_EMAIL,
                    recipient_list=[base.NOTIFY_EMAIL],
                )

                messages.success(request, "Message Sent")

                return redirect(reverse("contact"))

            messages.error(request, "Incorrect verification answer")
            return render(
                request,
                template_name=self.template_name,
                context={"form": form, "verification_err": True},
            )

        messages.error(request, "Message not sent, see errors below")

        return render(request, template_name=self.template_name, context={"form": form})


class SetlistNotesSearch(PageTitleMixin, TemplateView):
    form_class = SetlistNoteSearch
    title = "Setlist Notes Search"
    description = "Search for setlist notes"
    template_name = "databruce/search/notes_search.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form_class(self.request.GET)

        if context["form"].is_valid():
            self.template_name = "databruce/search/notes_search_results.html"
            context["query"] = context["form"].cleaned_data["query"]

        context["form"] = self.form_class()

        return context


class AdvancedSearch(PageTitleMixin, TemplateView):
    form_class = AdvancedEventSearch
    formset_class = formset_factory(SetlistSearch)
    template_name = "databruce/search/advanced_search.html"
    title = "Advanced Search"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["form"] = self.form_class()
        context["formset"] = self.formset_class(
            {
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "0",
                "form-0-choice": "is",
                "form-0-position": "anywhere",
            },
        )

        return context


class AdvancedSearchResults(PageTitleMixin, TemplateView):
    template_name = "databruce/search/advanced_search_results.html"
    form_class = AdvancedEventSearch
    formset = SetlistSearch
    formset_class = formset_factory(formset)
    title = "Advanced Search Results"

    position_filters = {
        "show_opener": Q(is_opener=True),
        "in_show": Q(set_name="show"),
        "in_set_one": Q(set_name="set 1"),
        "set_one_opener": Q(set_name="set 1", is_set_opener=True),
        "set_one_closer": Q(set_name="set 1", is_set_closer=True),
        "in_set_two": Q(set_name="set 2"),
        "set_two_opener": Q(set_name="set 2", is_set_opener=True),
        "set_two_closer": Q(set_name="set 2", is_set_closer=True),
        "main_set_closer": Q(is_main_set_closer=True),
        "encore_opener": Q(set_name="encore", is_set_opener=True),
        "in_encore": Q(set_name="encore"),
        "in_preshow": Q(set_name="pre-show"),
        "in_recording": Q(set_name="recording"),
        "in_soundcheck": Q(set_name="soundcheck"),
        "show_closer": Q(is_closer=True),
        "anywhere": Q(),  # No additional filters
        "premiere": Q(premiere=True),
        "debut": Q(debut=True),
        "nobruce": Q(nobruce=True),
        "request": Q(sign_request=True),
    }

    def get(self, request, *args, **kwargs):
        event_form = self.form_class(self.request.GET)
        formset = self.formset_class(self.request.GET)

        if not event_form.has_changed() and not formset.has_changed():
            messages.warning(self.request, "Please fill out at least one field")
            return redirect(reverse("adv_search"))

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["danger_event_types"] = ["Cancelled", "Rescheduled", "Relocated"]

        # Create a mutable copy of the GET data
        mutable_data = self.request.GET.copy()

        # Strip stray single quotes from every submitted value
        for key in mutable_data:
            value = mutable_data.get(key)
            mutable_data[key] = value.strip("'")

        event_form = self.form_class(mutable_data)
        formset = self.formset_class(mutable_data)

        pos_choices = dict(self.formset_class.form.base_fields["position"].choices)

        next_song = (
            models.Setlists.objects.select_related("song")
            .filter(
                set_name=OuterRef("set_name"),
                event__id=OuterRef("event__id"),
                song_num__gt=OuterRef("song_num"),
            )
            .order_by("event", "song_num")
            .values("song__id")[:1]
        )

        setlist_qs = (
            models.Setlists.objects.all()
            .select_related("event", "song")
            .values("event_id")
            .annotate(
                next_song=Subquery(next_song),
            )
        )

        setlist_anywhere_qs = (
            models.Setlists.objects.all()
            .select_related("event", "song")
            .values("event_id")
            .annotate(
                songs_list=ArrayAgg(
                    "song__id",
                    filter=Q(set_name__in=VALID_SET_NAMES),
                    distinct=True,
                ),
            )
        )

        event_filter = event_form.get_filters()
        sl_filter = Q()
        event_queries = []
        display_queries = []

        for f in event_filter.children:
            sl_filter &= Q(**{f"event__{f[0]}": f[1]})

        if formset.is_valid() and formset.has_changed():
            song_ids = [
                str(f["song1"]).replace("'", "")
                for f in formset.cleaned_data
                if f.get("song1")
            ]
            song_ids.extend(
                [
                    str(f["song2"]).replace("'", "")
                    for f in formset.cleaned_data
                    if f.get("song2")
                ],
            )

            song_map = {
                str(s.id): s.name for s in models.Songs.objects.filter(id__in=song_ids)
            }

            for form in formset.cleaned_data:
                if not form.get("song1"):
                    continue

                choice = form.get("choice", True)
                pos = form.get("position")
                s1_name = song_map.get(str(form["song1"]).replace("'", ""))

                choice_str = "is" if choice else "not"

                condition = Q(song=form["song1"])

                summary = f"{s1_name} ({choice_str} anywhere)"

                if pos == "followed_by" and form.get("song2"):
                    s2_name = song_map.get(str(form["song2"]).replace("'", ""))

                    song2_condition = Q(
                        next_song=form["song2"],
                    )

                    if not choice:
                        song2_condition = ~song2_condition

                    condition &= song2_condition

                    summary = f"{s1_name} ({choice_str} followed by) {s2_name}"

                elif pos == "anywhere":
                    condition = Q(
                        songs_list__contains=[int(form["song1"].replace("'", ""))],
                    )

                    if not choice or choice is None:
                        condition = ~Q(
                            songs_list__contains=[int(form["song1"].replace("'", ""))],
                        )

                else:
                    pos_filter = self.position_filters.get(pos)
                    pos_display = pos_choices.get(pos)

                    if not choice:
                        condition &= ~pos_filter
                    else:
                        condition &= pos_filter

                    summary = f"{s1_name} ({choice_str} {pos_display})"

                # use different queryset for the anywhere position
                if pos == "anywhere":
                    matched_events = set(
                        setlist_anywhere_qs.filter(condition).values_list(
                            "event_id",
                            flat=True,
                        ),
                    )

                else:
                    matched_events = set(
                        setlist_qs.filter(condition).values_list("event_id", flat=True),
                    )

                event_queries.append(matched_events)
                display_queries.append(summary)

        final_events = set()

        if event_queries:
            conjunction = event_form.cleaned_data["conjunction"]
            if conjunction == "or":
                final_events = set.union(*event_queries)
            else:
                final_events = set.intersection(*event_queries)

            event_filter &= Q(id__in=final_events)

        context["events"] = (
            models.Events.objects.filter(event_filter)
            .select_related(
                "venue",
                "venue__city",
                "venue__city__country",
                "artist",
                "tour",
                "type",
            )
            .prefetch_related("venue__city__state")
        ).order_by("event_id")

        context["display_fields"] = []

        for f in event_form.changed_data:
            if "_exclude" not in f and f != "conjunction":
                display = {
                    "label": event_form[f].label,
                    "data": event_form.cleaned_data[f],
                }

                if type(event_form.cleaned_data[f]) is list:
                    display["data"] = " OR ".join(event_form.cleaned_data[f])
                elif type(event_form.cleaned_data[f]) is QuerySet:
                    display["data"] = " OR ".join(
                        event_form.cleaned_data[f].values_list("name", flat=True),
                    )

                context["display_fields"].append(display)

        context["search_summary"] = display_queries

        context["conjunction"] = event_form.cleaned_data.get(
            "conjunction",
            "and",
        )

        query_display = f" {context['conjunction']} ".join(display_queries)
        field_display = ",".join(
            [f"{f['label']}: {f['data']}" for f in context["display_fields"]],
        )

        context["description"] = f"Songs: {query_display}, {field_display}"

        return context


class ShortenURL(PageTitleMixin, TemplateView):
    def get(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        user = UserModel.objects.first()
        short_url = shortener.create(user, request.GET["url"])

        return HttpResponse(
            json.dumps({"short_url": f"https://{request.get_host()}/s/{short_url}"}),
            content_type="application/json",
        )


class Relation(PageTitleMixin, TemplateView):
    template_name = "databruce/relations/relations.html"
    title = "Relations"


class RelationDetail(PageTitleMixin, TemplateView):
    template_name = "databruce/relations/detail.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)

        context["info"] = get_object_or_404(models.Relations, uuid=self.kwargs["id"])
        context["title"] = f"{context['info']}"
        context["bands"] = (
            models.Onstage.objects.filter(relation=context["info"].id)
            .select_related("band")
            .distinct("band")
        )

        return context


class Band(PageTitleMixin, TemplateView):
    template_name = "databruce/bands/bands.html"
    title = "Bands"


class BandDetail(PageTitleMixin, TemplateView):
    template_name = "databruce/bands/detail.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["info"] = get_object_or_404(models.Bands, uuid=self.kwargs["id"])
        context["title"] = f"{context['info']}"

        return context


class Release(PageTitleMixin, TemplateView):
    template_name = "databruce/releases/releases.html"
    title = "Releases"


class ReleaseDetail(PageTitleMixin, TemplateView):
    template_name = "databruce/releases/detail.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        queryset = models.Releases.objects.all()
        context["info"] = get_object_or_404(queryset, uuid=self.kwargs["id"])
        context["title"] = f"{context['info'].name}"

        return context


class City(PageTitleMixin, TemplateView):
    template_name = "databruce/locations/cities/cities.html"
    title = "Cities"


class CityDetail(PageTitleMixin, TemplateView):
    template_name = "databruce/locations/cities/detail.html"
    queryset = models.Cities.objects.all().select_related("country")

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["info"] = get_object_or_404(self.queryset, uuid=self.kwargs["id"])
        context["title"] = f"{context['info']}"

        return context


class State(PageTitleMixin, TemplateView):
    template_name = "databruce/locations/states/states.html"
    title = "States"


class StateDetail(PageTitleMixin, TemplateView):
    template_name = "databruce/locations/states/detail.html"
    queryset = models.States.objects.select_related("country")

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["info"] = get_object_or_404(self.queryset, uuid=self.kwargs["id"])
        context["title"] = f"{context['info']}"

        return context


class Country(PageTitleMixin, TemplateView):
    template_name = "databruce/locations/countries/countries.html"
    title = "Countries"


class CountryDetail(PageTitleMixin, TemplateView):
    template_name = "databruce/locations/countries/detail.html"
    queryset = models.Countries.objects.select_related(
        "first_event",
        "last_event",
    )

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["info"] = get_object_or_404(self.queryset, uuid=self.kwargs["id"])
        context["title"] = f"{context['info']}"

        return context


class EventRun(PageTitleMixin, TemplateView):
    template_name = "databruce/events/runs.html"
    title = "Event Runs"


class EventType(PageTitleMixin, TemplateView):
    template_name = "databruce/events/type.html"
    title = "Events by Type"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        try:
            context["type"] = get_object_or_404(
                models.EventTypes,
                slug=self.kwargs["type"],
            )
        except KeyError:
            context["type"] = "Concert"

        context["title"] = f"Event Type '{context['type']}'"

        context["types"] = models.EventTypes.objects.values(
            "id",
            "name",
            "uuid",
            "slug",
        )

        return context


class RunDetail(PageTitleMixin, TemplateView):
    template_name = "databruce/events/run_detail.html"
    queryset = (
        models.Runs.objects.all()
        .select_related(
            "first_event",
            "last_event",
            "band",
            "venue",
        )
        .order_by("first_event__event_id")
    )

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["info"] = get_object_or_404(self.queryset, uuid=self.kwargs["id"])
        context["title"] = f"{context['info']}"

        return context


class TourLeg(PageTitleMixin, TemplateView):
    template_name = "databruce/tours/legs.html"
    title = "Tour Legs"


class TourLegDetail(PageTitleMixin, TemplateView):
    template_name = "databruce/tours/leg_detail.html"
    queryset = models.TourLegs.objects.all()

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        self.leg = get_object_or_404(self.queryset, uuid=self.kwargs["id"])
        context["info"] = self.leg
        context["title"] = f"{context['info']}"

        return context


class NugsRelease(PageTitleMixin, TemplateView):
    template_name = "databruce/releases/nugs.html"
    title = "Nugs Releases"


class Bootleg(PageTitleMixin, TemplateView):
    template_name = "databruce/releases/bootlegs.html"
    title = "Bootlegs"


class Updates(PageTitleMixin, TemplateView):
    template_name = "databruce/updates.html"
    title = "Updates"


class Blog(PageTitleMixin, TemplateView):
    template_name = "blog/blog.html"
    title = "Blog"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        posts = models.BlogPosts.objects.all().order_by("-published_at", "-created_at")
        paginator = Paginator(posts, 10)
        page_number = self.request.GET.get("page", 1)
        context["page"] = paginator.get_page(page_number)

        return context


import nh3


class BlogPost(PageTitleMixin, TemplateView):
    template_name = "blog/post_detail.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        queryset = (
            models.BlogPosts.objects.filter(published=True)
            .select_related("author")
            .prefetch_related(
                "categories",
                "tags",
            )
        )

        context["post"] = get_object_or_404(queryset, slug=self.kwargs["slug"])
        context["title"] = f"{context['post']}"

        value = nh3.clean(
            context["post"].body,
            tags={"figure", "div", "br", "code", "blockquote", "p", "a", "img"},
            attributes={
                "div": {"class"},
                "figure": {"class"},
                "a": {"href"},
                "img": {"src"},
            },
        )

        md = markdown.Markdown(extensions=["fenced_code", "toc"])
        post = md.convert(value)

        template_obj = template.Template(post)

        context_new = Context({"body": context["post"].body})

        # Use the existing context (which is already a Context object)
        context["body"] = mark_safe(template_obj.render(context_new))  # noqa: S308
        context["toc"] = md.toc

        print(md.toc_tokens)

        return context


class BlogCategories(PageTitleMixin, TemplateView):
    template_name = "blog/categories.html"
    title = "Blog Categories"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["categories"] = (
            models.BlogCategory.objects.all()
            .prefetch_related(
                "post_categories",
            )
            .order_by("name")
        )

        return context


class BlogTags(PageTitleMixin, TemplateView):
    template_name = "blog/tags.html"
    title = "Blog Tags"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["tags"] = (
            models.BlogTags.objects.all()
            .prefetch_related(
                "post_tags",
            )
            .order_by("name")
        )

        return context


class BlogPostByCategory(PageTitleMixin, TemplateView):
    template_name = "blog/posts_by_category.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        category = self.kwargs["slug"]

        queryset = (
            models.BlogPosts.objects.filter(categories__slug=category, published=True)
            .select_related("author")
            .prefetch_related(
                "categories",
                "tags",
            )
            .order_by("-published_at", "-created_at")
        )

        paginator = Paginator(queryset, 10)
        page_number = self.request.GET.get("page", 1)
        context["page"] = paginator.get_page(page_number)

        context["title"] = "Posts By Category"
        context["category"] = category

        return context


class BlogPostByTag(PageTitleMixin, TemplateView):
    template_name = "blog/posts_by_tag.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        tag = self.kwargs["slug"]

        queryset = (
            models.BlogPosts.objects.filter(tags__slug=tag, published=True)
            .select_related("author")
            .prefetch_related(
                "categories",
                "tags",
            )
            .order_by("-published_at", "-created_at")
        )

        paginator = Paginator(queryset, 10)
        page_number = self.request.GET.get("page", 1)
        context["page"] = paginator.get_page(page_number)

        context["title"] = "Posts By Category"
        context["tag"] = tag

        return context
