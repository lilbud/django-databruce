import calendar
import datetime
import json
import logging
import os
import re
from typing import Any

import requests
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, User
from django.contrib.auth.tokens import (
    default_token_generator,
)
from django.contrib.auth.views import LoginView
from django.contrib.postgres.expressions import ArraySubquery
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.mail import send_mail
from django.db.models import (
    Case,
    Count,
    ExpressionWrapper,
    F,
    IntegerField,
    Max,
    Min,
    OuterRef,
    PositiveIntegerField,
    Prefetch,
    Q,
    Subquery,
    Value,
    When,
    Window,
)
from django.db.models.functions import JSONObject, Lag, Lead
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
from django.views.generic import DetailView, ListView, TemplateView
from django_filters.filterset import filterset_factory
from django_filters.views import FilterView
from shortener import shortener

from api.filters import AdvancedEventSearchFilter, EventsFilter
from databruce import models, settings
from databruce.forms import (
    AdvancedEventSearch,
    ContactForm,
    LoginForm,
    SetlistNoteSearch,
    SetlistSearch,
    UpdateUserForm,
    UserForm,
)

from .templatetags.filters import format_fuzzy

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

        onstage_qs = models.Onstage.objects.select_related("relation").prefetch_related(
            "band",
        )

        queryset = (
            models.Events.objects.all()
            .select_related(
                "venue",
                "artist",
                "tour",
                "venue__city",
                "venue__city__country",
            )
            .prefetch_related(
                "run",
                "venue__city__state",
                "leg",
                Prefetch("onstage", queryset=onstage_qs),
            )
        ).order_by("event_id")

        if not self.request.GET:
            context["filter"] = AdvancedEventSearchFilter()
            context["results"] = None
        else:
            context["filter"] = AdvancedEventSearchFilter(
                self.request.GET,
                queryset=queryset,
            )
            context["results"] = context["filter"].qs

        return context


class PageTitleMixin:
    def get_page_title(self, context):
        return getattr(self, "title", None)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.get_page_title(context)
        context["date"] = datetime.datetime.today()

        return context


class Index(PageTitleMixin, TemplateView):
    template_name = "databruce/index.html"
    title = "Home"

    queryset = (
        models.Events.objects.all()
        .select_related("venue", "artist", "venue__city", "venue__city__country")
        .prefetch_related("venue__city__state")
    )

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)

        context["updates"] = models.SiteUpdates.objects.all().order_by("-created_at")[
            :10
        ]

        context["latest_event"] = (
            models.Events.objects.select_related(
                "artist",
                "venue",
                "venue__city",
            )
            .prefetch_related("venue__city__state")
            .get(event_id="20260117-01")
        )

        return context


class Song(PageTitleMixin, TemplateView):
    template_name = "databruce/songs/songs.html"
    title = "Songs"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["songs"] = (
            models.Songs.objects.all()
            .select_related("first_event", "last_event")
            .order_by("name")
        )

        return context


class About(PageTitleMixin, TemplateView):
    template_name = "databruce/about.html"
    title = "About"


class Roadmap(PageTitleMixin, TemplateView):
    template_name = "databruce/roadmap.html"
    title = "Roadmap"


class Links(PageTitleMixin, TemplateView):
    template_name = "databruce/links.html"
    title = "Links"


# class Test(PageTitleMixin, TemplateView):
#     template_name = "databruce/test.html"
#     title = "Test"


class Calendar(PageTitleMixin, TemplateView):
    template_name = "databruce/calendar.html"
    title = "Event Calendar"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)

        context["years"] = list(range(context["date"].year, 1964, -1))

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

    def get_context_data(self, **kwargs: dict) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["users"] = UserModel.objects.filter(is_active=True)
        return context


class UserProfile(PageTitleMixin, TemplateView):
    template_name = "users/profile.html"
    title = "User Profile"

    def get_context_data(self, **kwargs: dict) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["user_info"] = UserModel.objects.get(
            username__iexact=self.kwargs["username"],
        )

        context["user_shows"] = (
            models.UserAttendedShows.objects.filter(
                user__id=context["user_info"].id,
            )
            .order_by("event__id")
            .select_related(
                "event",
                "event__tour",
                "event__venue",
                "event__artist",
                "event__venue__city",
                "event__venue__city__country",
            )
            .prefetch_related(
                "event__venue__city__state",
            )
            .annotate(
                setlist=Case(
                    When(
                        Q(event__setlist_certainty__in=["Confirmed", "Probable"]),
                        then=True,
                    ),
                    default=False,
                ),
            )
        )

        if context["user_shows"].count() > 0:
            context["user_songs"] = models.Setlists.objects.filter(
                event__id__in=context["user_shows"].values_list("event__id"),
                set_name__in=VALID_SET_NAMES,
            ).select_related("song", "song__first_event", "event")

            context["user_seen"] = (
                context["user_songs"]
                .values("song")
                .annotate(
                    name=F("song__name"),
                    count=Count("event"),
                    first=Min("event__id"),
                    category=F("song__category"),
                )
                .order_by("-count", "name")
            )

            context["user_not_seen"] = (
                models.Songs.objects.exclude(
                    id__in=context["user_songs"].values_list("song__id"),
                )
                .filter(num_plays_public__gte=100)
                .order_by("-num_plays_public", "name")
            )

            context["user_rare_songs"] = models.Songs.objects.filter(
                id__in=context["user_songs"].values("song__id"),
                num_plays_public__lte=100,
            ).order_by("num_plays_public", "name")

        return context


class Login(LoginView):
    form_class = LoginForm
    template_name = "users/login.html"
    title = "Login"

    def form_valid(self, form):
        print(form.cleaned_data)
        remember_me = form.cleaned_data[
            "remember_me"
        ]  # get remember me data from cleaned_data of form
        if not remember_me:
            self.request.session.set_expiry(0)  # if remember me is
            self.request.session.modified = True

        self.request.session.set_expiry(1209600)
        return super().form_valid(form)


class SignUp(PageTitleMixin, TemplateView):
    template_name = "users/signup.html"
    email_template_name = "users/signup_email.html"
    subject_template_name = "users/signup_confirm_subject.txt"
    title = "Signup"
    token_generator = default_token_generator
    form_class = UserForm
    extra_email_context = None
    from_email = None
    html_email_template_name = None

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
            extra_email_context = None

            context = {
                "email": user.email,
                "domain": current_site.domain,
                "site_name": current_site.name,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "user": user,
                "token": self.token_generator.make_token(user),
                "protocol": "https" if use_https else "http",
                **(extra_email_context or {}),
            }

            self.send_mail(
                context=context,
                from_email=os.getenv("MAILGUN_EMAIL"),
                to_email=user.email,
            )

            return redirect(reverse("signup_done"))

        return render(request, template_name=self.template_name, context={"form": form})

    def send_mail(
        self,
        context: dict,
        from_email: str,
        to_email: str,
    ):
        subject_template_name = "users/signup_confirm_subject.txt"
        email_template_name = "users/signup_email.html"

        # Email subject *must not* contain newlines
        subject = "".join(
            loader.render_to_string(subject_template_name, context).splitlines(),
        )
        body = loader.render_to_string(email_template_name, context)

        return requests.post(
            url=os.getenv("MAILGUN_URL"),
            auth=("api", os.getenv("MAILGUN_API")),
            data={
                "from": f"Databruce <{from_email}>",
                "to": f"{context['user']} <{to_email}>",
                "subject": subject,
                "text": body,
            },
            timeout=10,
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

                    user_group = User.objects.get(username=self.user)
                    group = Group.objects.get(name="Users")
                    user_group.groups.add(group)

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

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)

        context["id"] = self.kwargs["id"]

        archive = models.ArchiveLinks.objects.filter(
            event=OuterRef("id"),
        ).values("url")

        bootleg = models.Bootlegs.objects.filter(
            event=OuterRef("id"),
        ).values("id")

        nugs = models.NugsReleases.objects.filter(
            event=OuterRef("id"),
        ).values(json=JSONObject(id="id", url="url"))

        context["event"] = (
            models.Events.objects.select_related(
                "venue",
                "artist",
                "tour",
                "venue__city",
            )
            .prefetch_related(
                "leg",
                "run",
                "venue__city__state",
                "venue__city__state__country",
            )
            .annotate(
                archive=ArraySubquery(archive),
                boot=ArraySubquery(bootleg),
                nugs_rel=Subquery(nugs),
                next_event=Window(Lead("event_id"), order_by=F("id").asc()),
                prev_event=Window(Lag("event_id"), order_by=F("id").desc()),
            )
            .get(event_id=self.kwargs["id"])
        )

        context["official"] = (
            models.ReleaseTracks.objects.filter(
                event__event_id=self.kwargs["id"],
            )
            .distinct("release__id")
            .select_related("release", "event")
            .order_by("release__id")
        )

        context["title"] = (
            f"{format_fuzzy(context['event'].event_id)} {context['event'].venue.name}"
        )

        # notes = models.SetlistNotes.objects.filter(
        #     id=OuterRef("pk"),
        # ).select_related("event", "id")

        # snippets = (
        #     models.Snippets.objects.order_by("position")
        #     .select_related("snippet", "setlist")
        #     .filter(
        #         setlist=OuterRef("pk"),
        #     )
        #     .values(
        #         json=JSONObject(
        #             id="snippet__id",
        #             name="snippet__name",
        #             note="note",
        #             position="position",
        #             setlist="setlist__id",
        #         ),
        #     )
        # )

        if self.request.user.is_authenticated:
            context["user_attended"] = models.UserAttendedShows.objects.filter(
                user=self.request.user.id,
                event__event_id=self.kwargs["id"],
            )

        context["user_count"] = models.UserAttendedShows.objects.filter(
            event__event_id=context["event"].event_id,
        ).count()

        # # CURRENT BELOW
        context["setlist_unique"] = (
            models.Setlists.objects.filter(event__event_id=self.kwargs["id"])
            .select_related("song")
            .filter(
                set_name__in=VALID_SET_NAMES,
            )
            .order_by("song__category", "song_num")
        )

        context["album_breakdown"] = (
            models.Songs.objects.filter(
                id__in=context["setlist_unique"].values("song__id"),
            )
            .values("category")
            .annotate(num=Count("id"))
            .order_by("-num")
        )

        if context["album_breakdown"]:
            context["album_max"] = context["album_breakdown"].aggregate(
                max=Max("num"),
            )

            context["album_breakdown"] = context["album_breakdown"].annotate(
                max=Value(context["album_max"]["max"]),
                percent=ExpressionWrapper(
                    (F("num") / Value(1.0 * context["album_max"]["max"])) * 100,
                    output_field=IntegerField(),
                ),
            )

        return context


class Event(PageTitleMixin, TemplateView):
    template_name = "databruce/events/events.html"
    title = "Events"

    queryset = (
        models.Events.objects.all()
        .select_related(
            "venue",
            "tour",
            "artist",
            "venue__city",
            "venue__country",
            "venue__city__country",
        )
        .prefetch_related("venue__city__state")
        .order_by("id")
    )

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)

        try:
            context["year"] = self.kwargs["year"]
        except KeyError:
            context["year"] = context["date"].year  # current year

        context["years"] = list(range(context["date"].year, 1964, -1))

        context["event_info"] = self.queryset.filter(id__startswith=context["year"])

        return context


class Venue(PageTitleMixin, TemplateView):
    template_name = "databruce/locations/venues/venues.html"
    title = "Venues"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)

        context["venues"] = (
            models.Venues.objects.all()
            .order_by("name")
            .select_related("city", "country", "first_event", "last_event")
            .prefetch_related("state")
        )

        return context


class VenueDetail(PageTitleMixin, TemplateView):
    template_name = "databruce/locations/venues/detail.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)

        context["events"] = (
            models.Events.objects.filter(
                venue__id=self.kwargs["id"],
            )
            .select_related(
                "artist",
                "tour",
                "venue",
                "venue__city",
                "venue__city__country",
            )
            .prefetch_related("venue__city__state")
            .order_by("event_id")
        )

        context["venue_info"] = (
            models.Venues.objects.filter(
                id=self.kwargs["id"],
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

        context["title"] = f"{context['venue_info'].name}"

        context["songs"] = (
            models.Setlists.objects.filter(
                event__venue__id=self.kwargs["id"],
                set_name__in=VALID_SET_NAMES,
            )
            .select_related("song")
            .values(
                "song_id",
            )
            .annotate(
                plays=Count("event_id"),
                name=F("song__name"),
                category=F("song__category"),
            )
            .order_by(
                "-plays",
                "name",
            )
        )

        return context


class SongLyrics(PageTitleMixin, TemplateView):
    template_name = "databruce/songs/lyrics.html"
    title = "Lyrics"


class SongLyricDetail(PageTitleMixin, TemplateView):
    template_name = "databruce/songs/lyric_detail.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["lyrics"] = (
            models.Lyrics.objects.filter(
                uuid=self.kwargs["id"],
            )
            .select_related("song")
            .first()
        )

        context["song_info"] = models.Songs.objects.filter(
            id=context["lyrics"].song.id,
        ).first()

        context["title"] = f"Lyrics for {context['song_info'].name}"

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

        context["song_info"] = (
            models.Songs.objects.filter(id=self.kwargs["id"])
            .prefetch_related(
                "album",
                "last_event",
            )
            .first()
        )

        try:
            context["show_gap"] = models.Events.objects.filter(
                event_id__gt=context["song_info"].last_event.event_id,
                public=True,
            ).count()
        except models.Songs.last_event.RelatedObjectDoesNotExist:
            context["show_gap"] = 0

        context["title"] = f"{context['song_info'].name}"

        context["setlists"] = models.Setlists.objects.filter(
            song__id=self.kwargs["id"],
        )

        context["positions"] = (
            context["setlists"]
            .filter(set_name__in=VALID_SET_NAMES)
            .exclude(position=None)
            .values("position")
            .annotate(
                count=Count("position"),
                num=Min("song_num"),
            )
        ).order_by("num")

        context["lyrics"] = models.Lyrics.objects.filter(
            song__id=self.kwargs["id"],
        ).order_by("id")

        if context["song_info"].num_plays_public > 0:
            context["year_stats"] = (
                models.Setlists.objects.select_related("event")
                .filter(
                    song_id=self.kwargs["id"],
                    set_name__in=VALID_SET_NAMES,
                    event__date__isnull=False,
                )
                .annotate(
                    year=F("event__date__year"),
                )
                .values("year")
                .annotate(
                    event_count=Count(
                        "event",
                        distinct=True,
                        filter=Q(set_name__in=VALID_SET_NAMES),
                    ),
                )
                .order_by("year")
            )

            filter = Q(is_stats_eligible=True) & Q(
                event_id__gt=context["song_info"].first_event.event_id,
            )

            context["events_since_premiere"] = models.Events.objects.filter(
                filter,
            ).count()

            if context["events_since_premiere"] > 0:
                context["frequency"] = round(
                    (
                        (
                            context["song_info"].num_plays_public
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
        context["info"] = get_object_or_404(models.Tours, id=self.kwargs["id"])
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
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.NOTIFY_EMAIL],
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

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form_class(self.request.GET)
        self.template_name = "databruce/search/notes_search.html"

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

        event_form = self.form_class(self.request.GET)
        formset = self.formset_class(self.request.GET)

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
            .annotate(
                next_song=Subquery(next_song),
            )
        )

        event_filter = event_form.get_filters()
        event_queries = []
        display_queries = []

        if formset.is_valid() and formset.has_changed():
            song_ids = [f["song1"] for f in formset.cleaned_data if f.get("song1")]
            song_ids.extend(
                [f["song2"] for f in formset.cleaned_data if f.get("song2")],
            )

            song_map = {
                str(s.id): s.name for s in models.Songs.objects.filter(id__in=song_ids)
            }

            for form in formset.cleaned_data:
                if not form.get("song1"):
                    continue

                choice = form.get("choice", True)
                pos = form.get("position")
                s1_name = song_map.get(str(form["song1"]))

                choice_str = "is" if choice else "not"

                condition = Q(song=form["song1"])

                summary = f"{s1_name} ({choice_str} anywhere)"

                if pos == "followed_by" and form.get("song2"):
                    s2_name = song_map.get(str(form["song2"]))

                    song2_condition = Q(
                        next_song=form["song2"],
                    )

                    if not choice:
                        song2_condition = ~song2_condition

                    condition &= song2_condition

                    summary = f"{s1_name} ({choice_str} followed by) {s2_name}"

                elif pos == "anywhere":
                    if not choice:
                        condition = ~Q(
                            song=form["song1"],
                        )

                else:
                    pos_filter = self.position_filters.get(pos)
                    pos_display = pos_choices.get(pos)

                    if not choice:
                        condition &= ~pos_filter
                    else:
                        condition &= pos_filter

                    summary = f"{s1_name} ({choice_str} {pos_display})"

                print(condition)

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
            )
            .prefetch_related("venue__city__state")
        ).order_by("event_id")

        context["display_fields"] = [
            {"label": event_form[f].label, "data": event_form.cleaned_data[f]}
            for f in event_form.changed_data
            if "_exclude" not in f and f != "conjunction"
        ]

        context["search_summary"] = display_queries
        context["conjunction"] = event_form.cleaned_data.get(
            "conjunction",
            "and",
        ).upper()

        return context

    # def check_field_choice(self, choice: bool, field_filter: Q) -> Q:
    #     """Every field has a IS/NOT choice on it. Depending on that choice, the filter can be negated or not. This checks for that value and returns the correct filter."""
    #     if choice is False:
    #         return ~field_filter

    #     return field_filter

    # # def get_lookup(self, data: dict, field: dict) -> Q:

    # def get(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):
    #     event_form = self.form_class(request.GET)
    #     formset = self.formset_class(request.GET)

    #     setlist = models.Setlists.objects.filter(
    #         set_name=OuterRef("set_name"),
    #         event__id=OuterRef("event__id"),
    #     ).select_related("song")

    #     setlist_qs = (
    #         models.Setlists.objects.all()
    #         .select_related("event", "song")
    #         .annotate(
    #             next_song=Subquery(
    #                 setlist.filter(song_num__gt=OuterRef("song_num"))
    #                 .order_by("event", "song_num")
    #                 .values("song__id")[:1],
    #             ),
    #         )
    #     )

    #     song_results = []
    #     event_results = []
    #     event_list = []
    #     display_fields = []

    #     setlist = ""

    #     setlist_event_filter = Q()
    #     event_filter = Q()

    #     if formset.is_valid() and formset.has_changed():
    #         setlist = formset.cleaned_data
    #         form_fields = []

    #         for form in formset.cleaned_data:
    #             if form["choice"] and form["position"] == "Followed By":
    #                 f = {
    #                     "song1": form["song2"],
    #                     "choice": "is",
    #                     "position": "Anywhere",
    #                     "hidden": "true",
    #                 }
    #                 form_fields.append(f)
    #             else:
    #                 form_fields.append(form)

    #         for form in form_fields:
    #             setlist_filter = Q()

    #             try:
    #                 song1 = form["song1"]["value"]

    #                 match form["position"]:
    #                     case "Followed By":
    #                         song2 = form["song2"]["value"]

    #                         song2_filter = self.check_field_choice(
    #                             form["choice"],
    #                             Q(next_song=form["song2"]["id"]),
    #                         )

    #                         setlist_filter = Q(
    #                             Q(song=form["song1"]["id"]) & song2_filter,
    #                         )

    #                         events = setlist_qs.filter(setlist_filter).values_list(
    #                             "event__id",
    #                             flat=True,
    #                         )

    #                         song_results.append(
    #                             f"{song1} ({form['choice']} followed by) {song2}",
    #                         )

    #                     case "Anywhere":
    #                         print(form["choice"])
    #                         setlist_filter = self.check_field_choice(
    #                             form["choice"],
    #                             Q(song__id=form["song1"]["id"]),
    #                         )

    #                         events = setlist_qs.filter(setlist_filter).values_list(
    #                             "event__id",
    #                             flat=True,
    #                         )

    #                         print(setlist_filter)

    #                         try:
    #                             if not form["hidden"]:
    #                                 song_results.append(
    #                                     f"{song1} ({form['choice']} anywhere)",
    #                                 )
    #                         except KeyError:
    #                             song_results.append(
    #                                 f"{song1} ({form['choice']} anywhere)",
    #                             )
    #                     case _:
    #                         # all others except anywhere and followed by
    #                         position_filter = self.check_field_choice(
    #                             form["choice"],
    #                             Q(position=form["position"]),
    #                         )

    #                         setlist_filter = Q(
    #                             Q(song__id=form["song1"]["id"]) & position_filter,
    #                         )

    #                         events = setlist_qs.filter(setlist_filter).values_list(
    #                             "event__id",
    #                             flat=True,
    #                         )

    #                         song_results.append(
    #                             f"{song1} ({form['choice']} {form['position']})",
    #                         )

    #                 event_results.append(list(events))

    #                 match event_form.cleaned_data["conjunction"]:
    #                     case "or":
    #                         event_list = list(set.union(*map(set, event_results)))

    #                     case "and":
    #                         event_list = list(
    #                             set.intersection(*map(set, event_results)),
    #                         )

    #             except ValueError:
    #                 break
    #             except AttributeError:
    #                 break

    #     if event_list:
    #         setlist_event_filter = Q(id__in=event_list)

    #     qs_filter = Q()

    #     result = (
    #         models.Events.objects.all()
    #         .select_related(
    #             "venue",
    #             "venue__city",
    #             "venue__city__country",
    #             "artist",
    #             "tour",
    #         )
    #         .prefetch_related(
    #             "venue__city__state",
    #             "venue__city__state__country",
    #         )
    #         .annotate(
    #             setlist=Case(
    #                 When(Q(setlist_certainty__in=["Confirmed", "Probable"]), then=True),
    #                 default=False,
    #             ),
    #         )
    #         .order_by("event_id")
    #     )

    #     if setlist_event_filter.children:
    #         qs_filter &= setlist_event_filter

    #     if event_filter.children:
    #         qs_filter &= event_filter

    #     # only if filter is not empty
    #     if qs_filter.children:
    #         result = result.filter(qs_filter)
    #     else:
    #         result = None

    #     description = ""
    #     description += ",".join(
    #         [f"{item['label']}: {item['data']}" for item in display_fields],
    #     )
    #     description += f"Songs: {', '.join(song_results)}"

    #     return render(
    #         request=request,
    #         template_name=self.template_name,
    #         context={
    #             "title": "Advanced Search",
    #             "events": result,
    #             "description": description,
    #             "conjunction": event_form.cleaned_data["conjunction"],
    #             "setlist_form": setlist,
    #             "display_fields": display_fields,
    #         },
    #     )


class ShortenURL(PageTitleMixin, TemplateView):
    def get(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        user = User.objects.first()
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
        context["info"] = models.Relations.objects.get(id=self.kwargs["id"])
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
        context["info"] = get_object_or_404(models.Bands, id=self.kwargs["id"])
        context["title"] = f"{context['info']}"

        return context


class Release(PageTitleMixin, TemplateView):
    template_name = "databruce/releases/releases.html"
    title = "Releases"


class ReleaseDetail(PageTitleMixin, TemplateView):
    template_name = "databruce/releases/detail.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["info"] = get_object_or_404(models.Releases, id=self.kwargs["id"])
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
        self.city = get_object_or_404(self.queryset, id=self.kwargs["id"])
        context["info"] = self.city
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
        context["info"] = get_object_or_404(self.queryset, id=self.kwargs["id"])
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
        context["info"] = get_object_or_404(self.queryset, id=self.kwargs["id"])
        context["title"] = f"{context['info']}"

        return context


class EventRun(PageTitleMixin, TemplateView):
    template_name = "databruce/events/runs.html"
    title = "Event Runs"


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
        context["info"] = get_object_or_404(self.queryset, id=self.kwargs["id"])
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
        self.leg = get_object_or_404(self.queryset, id=self.kwargs["id"])
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
