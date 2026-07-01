import datetime
import json
import logging
import os
import re
import zoneinfo
from typing import Any

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group, User
from django.contrib.auth.tokens import (
    default_token_generator,
)
from django.contrib.auth.views import LoginView
from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.postgres.expressions import ArraySubquery
from django.contrib.postgres.search import SearchRank, SearchVector
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.mail import send_mail
from django.db.models import (
    Count,
    Exists,
    F,
    Min,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    Window,
)
from django.db.models.functions import DenseRank, RowNumber
from django.forms import formset_factory
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template import loader
from django.urls import reverse, reverse_lazy
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import TemplateView
from django.views.generic.base import ContextMixin
from shortener import shortener

from databruce import models
from databruce.config import base
from databruce.forms import (
    AdvancedEventSearch,
    ContactForm,
    CustomPasswordChangeForm,
    LoginForm,
    SetlistNoteSearch,
    SetlistSearch,
    UpdateUserForm,
    UserForm,
)

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
        context = super().get_context_data(**kwargs)
        context["year"] = "2023"

        return context


def event_search(request):
    query = request.GET.get("q", "")

    results = (
        models.Events.objects.select_related("artist", "venue")
        .annotate(
            search=SearchVector("event_id", weight="A")
            + SearchVector("date", weight="B")
            + SearchVector("early_late", weight="B")
            + SearchVector("artist__name", weight="C")
            + SearchVector("venue__name", weight="D"),
        )
        .filter(search=query)
        .annotate(rank=SearchRank(search, query))
        .values()
    )

    return JsonResponse(
        {
            "results": list(results)[:10],
            "query": query,
        },
        safe=False,
    )


class PageTitleMixin(ContextMixin):
    def get_page_title(self, _context):
        return getattr(self, "title", None)

    def get_page_description(self, _context):
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
            .values_list("event_id", flat=True)
            .first()
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

        user_events = models.Events.objects.filter(
            user_event__user_id=context["info"].pk,
        )

        context["user_event_count"] = user_events.count()

        context["user_songs_count"] = (
            models.Setlists.objects.filter(
                event__event_id__in=user_events.values("event_id"),
                set_name__in=VALID_SET_NAMES,
            )
            .distinct("song_id")
            .order_by("song_id")
        ).count()

        context["first_event"] = user_events.order_by("event_id").first()
        context["last_event"] = user_events.order_by("-event_id").first()

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
            self.request.session.set_expiry(1209600)  # 2 weeks

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
            if form.cleaned_data["verification"] == os.environ.get(
                "SIGNUP_VERIFICATION_ANSWER",
            ):
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

            messages.error(request, "Incorrect verification answer")
            return render(
                request,
                template_name=self.template_name,
                context={"form": form},
            )

        messages.error(request, "Signup Failed, see errors below")
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
            raise ImproperlyConfigured(msg)

        # 1. Fetch and validate the env key early so the type checker knows it's a strict 'str'
        token_key = os.getenv("INTERNAL_RESET_SESSION_TOKEN")
        if not token_key:
            msg = "The 'INTERNAL_RESET_SESSION_TOKEN' environment variable is not configured."
            raise ImproperlyConfigured(msg)

        self.validlink = False
        self.user = self.get_user(kwargs["uidb64"])

        if self.user is not None:
            token = kwargs["token"]
            if token == self.reset_url_token:
                # 2. Used safely here as a guaranteed string
                session_token = self.request.session.get(token_key)

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
                    # 3. Used safely here as a guaranteed string
                    self.request.session[token_key] = token

                    group = Group.objects.get(name="Users")
                    self.user.groups.add(group)
                    self.user.is_active = True
                    self.user.save()

                return redirect("login")

        return None


class UserChangePassword(View):
    template_name = "users/password_change.html"
    form_class = CustomPasswordChangeForm
    title = "Change Password"

    def post(self, request: HttpRequest):
        password_form = self.form_class(request.user, request.POST)

        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)  # Prevents logging out

            messages.success(request, "Your password is updated successfully")

            storage = messages.get_messages(request)

            msg_list = next(
                {"message": msg.message, "tags": msg.tags} for msg in storage
            )

            return JsonResponse(
                {
                    "success": True,
                    "messages": msg_list,
                },
            )

        err_msg = []

        for msg in password_form.errors.values():
            err_msg.append(str(msg[0]))

        msg_list = []

        return JsonResponse(
            {
                "success": False,
                "messages": {"message": "\n".join(err_msg), "tags": "error"},
            },
            status=400,
        )


class UserSettings(LoginRequiredMixin, PageTitleMixin, TemplateView):
    template_name = "users/settings.html"
    form_class = UpdateUserForm
    password_form_class = CustomPasswordChangeForm

    title = "User Settings"

    def get_context_data(self, **kwargs: dict) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["form"] = self.form_class(instance=self.request.user)
        context["password_form"] = self.password_form_class(self.request.user)

        return context

    def post(self, request: HttpRequest):
        user_form = self.form_class(request.POST, instance=request.user)

        if user_form.is_valid():
            user_form.save()
            messages.success(request, "Your profile is updated successfully")

            storage = messages.get_messages(request)
            msg_list = next(
                {"message": msg.message, "tags": msg.tags} for msg in storage
            )

            return JsonResponse(
                {
                    "success": True,
                    "messages": msg_list,
                },
            )

        return JsonResponse({"success": False, "errors": user_form.errors}, status=400)


class SignUpDone(PageTitleMixin, TemplateView):
    template_name = "users/signup_done.html"
    title = "Sign Up Complete"


class UserRemoveShow(View):
    def post(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        models.UserAttendedShows.objects.filter(
            user_id=request.user.pk,
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
                user_id=request.user.pk,
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
            )
            .prefetch_related("leg", "run", "archive_links", "nugs_event")
            .annotate(),
            event_id=self.kwargs["id"],
        )

        ranked_events = list(
            models.Events.objects.exclude(type_id__in=[21, 23, 6])
            .annotate(
                tour_num=Window(
                    expression=RowNumber(),
                    partition_by=F("tour__id"),
                    order_by=F("event_id").asc(),
                ),
                tour_total=Window(
                    expression=Count("id"),
                    partition_by=F("tour__id"),
                ),
                tour_leg_num=Window(
                    expression=RowNumber(),
                    partition_by=F("leg__id"),
                    order_by=F("event_id").asc(),
                ),
                tour_leg_total=Window(
                    expression=Count("id"),
                    partition_by=F("leg__id"),
                ),
                venue_num=Window(
                    expression=RowNumber(),
                    partition_by=F("venue__id"),
                    order_by=F("event_id").asc(),
                ),
                venue_total=Window(
                    expression=Count("id"),
                    partition_by=F("venue__id"),
                ),
                city_num=Window(
                    expression=RowNumber(),
                    partition_by=F("venue__city_id"),
                    order_by=F("event_id").asc(),
                ),
                city_total=Window(
                    expression=Count("id"),
                    partition_by=F("venue__city_id"),
                ),
            )
            .values(),
        )

        context["rank_stats"] = next(
            (e for e in ranked_events if e["event_id"] == self.kwargs["id"]),
            None,
        )

        all_ranked_events = list(
            models.Events.objects.filter(length__isnull=False)
            .annotate(
                rank=Window(
                    expression=DenseRank(),
                    order_by=F("length").desc(),
                ),
            )
            .filter(rank__lte=10)
            .values("event_id", "length", "rank"),
        )

        event_with_true_rank = next(
            (e for e in all_ranked_events if e["event_id"] == self.kwargs["id"]),
            None,
        )

        context["rank"] = event_with_true_rank["rank"] if event_with_true_rank else None

        event = context["event"]
        event_date = event.get_date()

        venue = event.venue
        venue_name = getattr(venue, "name", "Unknown Venue")

        context["title"] = f"{event_date} - {venue_name}"
        context["description"] = f"{event_date}<br>{event.artist}<br>{venue_name}"

        context["setlist_certainty"] = bool(
            context["event"].setlist_certainty not in (None, "", "Unknown"),
        )

        context["type_note"] = event.type.name in [  # type: ignore
            "Rescheduled",
            "Cancelled",
            "Relocated",
            "No Bruce",
            "No Gig",
            "Rumored",
        ]

        if venue and venue.city and venue.city.timezone:
            tz_target = venue.city.timezone
        else:
            tz_target = zoneinfo.ZoneInfo(base.TIME_ZONE)

        context["scheduled_time"] = None
        context["start_time"] = None
        context["end_time"] = None
        context["duration"] = None

        if event.scheduled_time:
            context["scheduled_time"] = (
                event.scheduled_time.astimezone(tz_target).strftime("%I:%M%p").lower()
            )

        if event.start_time:
            context["start_time"] = (
                event.start_time.astimezone(tz_target).strftime("%I:%M%p").lower()
            )

        if event.end_time:
            context["end_time"] = (
                event.end_time.astimezone(tz_target).strftime("%I:%M%p").lower()
            )

        neighbor_qs = models.Events.objects.select_related("venue", "artist", "tour")

        context["prev_event"] = (
            neighbor_qs.filter(event_id__lt=event.event_id)
            .order_by("-event_id")
            .first()
        )

        context["next_event"] = (
            neighbor_qs.filter(event_id__gt=event.event_id).order_by("event_id").first()
        )

        if not context["event"].date:
            messages.info(
                self.request,
                "This is a placeholder date, actual date unknown.",
            )

        context["official"] = (
            models.Releases.objects.filter(
                event__id=event.pk,
            )
            .prefetch_related("event")
            .order_by("date")
        )

        context["official_tracks"] = (
            models.ReleaseTracks.objects.filter(event__id=event.pk)
            .select_related("release")
            .prefetch_related("event")
            .distinct("release_id", "release__date")
            .order_by("release__date")
        )

        user = self.request.user

        if user.is_authenticated:
            context["user_attended"] = models.UserAttendedShows.objects.filter(
                user=user.pk,
                event__id=event.pk,
            )

        context["users"] = models.UserAttendedShows.objects.filter(
            event__id=event.pk,
        )

        return context


class EventDetailMobile(PageTitleMixin, TemplateView):
    template_name = "databruce/event_mobile.html"
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

        event = context["event"]
        event_date = event.get_date()

        venue = event.venue
        venue_name = getattr(venue, "name", "Unknown Venue")

        context["title"] = f"{event_date} - {venue_name}"

        context["description"] = (
            f"{event_date}<br>{context['event'].artist}<br>{venue_name}"
        )

        if venue and venue.city and venue.city.timezone:
            tz_target = venue.city.timezone
        else:
            tz_target = zoneinfo.ZoneInfo(base.TIME_ZONE)

        if event.scheduled_time:
            context["scheduled_time"] = (
                event.scheduled_time.astimezone(tz_target).strftime("%I:%M%p").lower()
            )

        if event.start_time:
            context["start_time"] = (
                event.start_time.astimezone(tz_target).strftime("%I:%M%p").lower()
            )

        if event.end_time:
            context["end_time"] = (
                event.end_time.astimezone(tz_target).strftime("%I:%M%p").lower()
            )

        if event.start_time and event.end_time and not event.length:
            context["duration"] = event.end_time.astimezone(
                tz_target,
            ) - event.start_time.astimezone(tz_target)
        elif event.length:
            context["duration"] = event.length

        neighbor_qs = models.Events.objects.select_related("venue", "artist")

        context["prev_event"] = (
            neighbor_qs.filter(event_id__lt=event.event_id)
            .order_by("-event_id")
            .first()
        )

        context["next_event"] = (
            neighbor_qs.filter(event_id__gt=event.event_id).order_by("event_id").first()
        )

        if not context["event"].date:
            messages.info(
                self.request,
                "This is a placeholder date, actual date unknown.",
            )

        context["official"] = (
            models.Releases.objects.filter(
                event__id=event.pk,
            )
            .prefetch_related("event")
            .order_by("date")
        )

        context["official_tracks"] = (
            models.ReleaseTracks.objects.filter(event__id=event.pk)
            .select_related("release")
            .prefetch_related("event")
            .distinct("release_id", "release__date")
            .order_by("release__date")
        )

        return context


class EventDetailTest(PageTitleMixin, TemplateView):
    template_name = "databruce/event_test.html"
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
            )
            .prefetch_related("leg", "run", "archive_links", "nugs_event")
            .annotate(),
            event_id=self.kwargs["id"],
        )

        ranked_events = list(
            models.Events.objects.exclude(type_id__in=[21, 23, 6])
            .annotate(
                tour_num=Window(
                    expression=RowNumber(),
                    partition_by=F("tour__id"),
                    order_by=F("event_id").asc(),
                ),
                tour_total=Window(
                    expression=Count("id"),
                    partition_by=F("tour__id"),
                ),
                tour_leg_num=Window(
                    expression=RowNumber(),
                    partition_by=F("leg__id"),
                    order_by=F("event_id").asc(),
                ),
                tour_leg_total=Window(
                    expression=Count("id"),
                    partition_by=F("leg__id"),
                ),
                venue_num=Window(
                    expression=RowNumber(),
                    partition_by=F("venue__id"),
                    order_by=F("event_id").asc(),
                ),
                venue_total=Window(
                    expression=Count("id"),
                    partition_by=F("venue__id"),
                ),
            )
            .values(),
        )

        context["rank_stats"] = next(
            (e for e in ranked_events if e["event_id"] == self.kwargs["id"]),
            None,
        )

        all_ranked_events = list(
            models.Events.objects.filter(length__isnull=False)
            .annotate(
                rank=Window(
                    expression=DenseRank(),
                    order_by=F("length").desc(),
                ),
            )
            .filter(rank__lte=10)
            .values("event_id", "length", "rank"),
        )

        event_with_true_rank = next(
            (e for e in all_ranked_events if e["event_id"] == self.kwargs["id"]),
            None,
        )

        context["rank"] = event_with_true_rank["rank"] if event_with_true_rank else None

        event = context["event"]
        event_date = event.get_date()

        venue = event.venue
        venue_name = getattr(venue, "name", "Unknown Venue")

        context["title"] = f"{event_date} - {venue_name}"
        context["description"] = f"{event_date}<br>{event.artist}<br>{venue_name}"

        if context["event"].setlist_certainty in (None, "", "Unknown"):
            context["setlist_certainty"] = False
        else:
            context["setlist_certainty"] = True

        if venue and venue.city and venue.city.timezone:
            tz_target = venue.city.timezone
        else:
            tz_target = zoneinfo.ZoneInfo(base.TIME_ZONE)

        if event.scheduled_time:
            context["scheduled_time"] = (
                event.scheduled_time.astimezone(tz_target).strftime("%I:%M%p").lower()
            )

        if event.start_time:
            context["start_time"] = (
                event.start_time.astimezone(tz_target).strftime("%I:%M%p").lower()
            )

        if event.end_time:
            context["end_time"] = (
                event.end_time.astimezone(tz_target).strftime("%I:%M%p").lower()
            )

        if event.start_time and event.end_time and not event.length:
            context["duration"] = event.end_time.astimezone(
                tz_target,
            ) - event.start_time.astimezone(tz_target)
        elif event.length:
            context["duration"] = event.length

        neighbor_qs = models.Events.objects.select_related("venue", "artist", "tour")

        context["prev_event"] = (
            neighbor_qs.filter(event_id__lt=event.event_id)
            .order_by("-event_id")
            .first()
        )

        context["next_event"] = (
            neighbor_qs.filter(event_id__gt=event.event_id).order_by("event_id").first()
        )

        if not context["event"].date:
            messages.info(
                self.request,
                "This is a placeholder date, actual date unknown.",
            )

        context["official"] = (
            models.Releases.objects.filter(
                event__id=event.pk,
            )
            .prefetch_related("event")
            .order_by("date")
        )

        context["official_tracks"] = (
            models.ReleaseTracks.objects.filter(event__id=event.pk)
            .select_related("release")
            .prefetch_related("event")
            .distinct("release_id", "release__date")
            .order_by("release__date")
        )

        user = self.request.user

        if user.is_authenticated:
            context["user_attended"] = models.UserAttendedShows.objects.filter(
                user=user.pk,
                event__id=event.pk,
            )

        context["users"] = models.UserAttendedShows.objects.filter(
            event__id=event.pk,
        )

        return context


class Event(PageTitleMixin, TemplateView):
    template_name = "databruce/events/events.html"
    title = "Events"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)

        try:
            if len(str(self.kwargs["year"])) == 4:
                context["year"] = int(self.kwargs["year"])
        except KeyError:
            context["year"] = int(context["date"].year)  # current year

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

        venue = context["info"]
        venue_name = getattr(venue, "name", None)
        venue_address = getattr(venue, "address", None)

        if venue_address:
            context["shared_loc"] = models.Venues.objects.exclude(id=venue.id).filter(
                address=venue_address,
            )[:5]

        context["child_venues"] = models.Venues.objects.filter(parent=venue)

        context["title"] = f"{venue_name}"
        context["description"] = f"{venue_name}"

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

        song = context["lyrics"].song
        song_name = getattr(song, "name", "Unknown Song")

        context["title"] = f"Lyrics for {song_name}"
        context["description"] = (
            f"Source: {context['lyrics'].source}<br>Language: {context['lyrics'].language}"
        )

        return context


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

        song = context["info"]
        song_name = getattr(song, "name", "Unknown Song")

        context["title"] = f"{song_name}"

        context["setlists"] = (
            models.Setlists.objects.filter(
                song_id=song.pk,
            )
            .select_related("event", "song")
            .prefetch_related("setlist_position")
        )

        context["positions"] = (
            context["setlists"]
            .filter(position__isnull=False)
            .values("position")
            .annotate(
                count=Count("position"),
                num=Min("song_num"),
            )
        ).order_by("num")

        first_event = getattr(context["info"], "first_event", None)
        first_event_id = first_event.event_id if first_event else None

        last_event = getattr(context["info"], "last_event", None)
        last_event_id = last_event.event_id if last_event else None

        latest_event = (
            models.Events.objects.filter(
                is_stats_eligible=True,
                setlist_event__isnull=False,
            )
            .order_by("-event_id")
            .first()
        )

        if last_event_id and latest_event:
            context["show_gap"] = models.Events.objects.filter(
                event_id__gt=last_event_id,
                event_id__lte=latest_event.event_id,
                is_stats_eligible=True,
            ).count()
        else:
            context["show_gap"] = 0

        context["lyrics"] = models.Lyrics.objects.filter(
            song_id=song.pk,
        ).order_by("id")

        if first_event:
            context["events_since_premiere"] = models.Events.objects.filter(
                event_id__gt=first_event_id,
            ).count()
        else:
            context["events_since_premiere"] = 0

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

                send_mail(
                    subject=form.cleaned_data["subject"],
                    message=body,
                    from_email=base.DEFAULT_FROM_EMAIL,
                    recipient_list=[base.NOTIFY_EMAIL] if base.NOTIFY_EMAIL else [],
                    fail_silently=False,
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

        event_form = self.form_class(self.request.GET)
        formset = self.formset_class(self.request.GET)

        pos_choices = dict(formset.form.base_fields["position"].choices)

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
                    pos_filter = self.position_filters.get(pos)  # type: ignore
                    pos_display = pos_choices.get(pos)

                    if not choice:
                        condition &= ~pos_filter  # type: ignore
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
            .prefetch_related("venue__city__state", "setlist_event")
            .annotate(
                has_setlist=Exists(
                    Subquery(models.Setlists.objects.filter(event_id=OuterRef("id"))),
                ),
            )
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
