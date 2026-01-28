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
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import Group, User
from django.contrib.auth.tokens import (
    default_token_generator,
)
from django.contrib.auth.views import LoginView
from django.contrib.postgres.aggregates import ArrayAgg, JSONBAgg
from django.contrib.postgres.expressions import ArraySubquery
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.mail import send_mail
from django.db.models import (
    Case,
    Count,
    Exists,
    ExpressionWrapper,
    F,
    IntegerField,
    Max,
    Min,
    OuterRef,
    PositiveIntegerField,
    Q,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import JSONObject, TruncYear
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
from shortener import shortener

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

UserModel = get_user_model()
logger = logging.getLogger("django.contrib.auth")
date = datetime.datetime.today()

VALID_SET_NAMES = [
    "Show",
    "Set 1",
    "Set 2",
    "Encore",
    "Pre-Show",
    "Post-Show",
]


class Index(TemplateView):
    template_name = "databruce/index.html"

    queryset = (
        models.Events.objects.all()
        .select_related("venue", "artist", "venue__city", "venue__city__country")
        .prefetch_related("venue__city__state")
    )

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["title"] = "Home"
        context["date"] = datetime.datetime.today()

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
            .get(id="20260117-01")
        )

        return context


class Song(TemplateView):
    template_name = "databruce/songs/songs.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["title"] = "Songs"
        context["songs"] = (
            models.Songs.objects.all().select_related("first", "last").order_by("name")
        )

        return context


class About(TemplateView):
    template_name = "databruce/about.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        return super().get_context_data(**kwargs)


class Roadmap(TemplateView):
    template_name = "databruce/roadmap.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        return super().get_context_data(**kwargs)


class Links(TemplateView):
    template_name = "databruce/links.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        return super().get_context_data(**kwargs)


class Test(TemplateView):
    template_name = "databruce/test.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        return super().get_context_data(**kwargs)


class Calendar(TemplateView):
    template_name = "databruce/calendar.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)

        try:
            if re.search(
                r"^\d{4}-\d{2}-\d{2}|^\d{4}-\d{2}$|^\d{4}$",
                self.request.GET["start"],
            ):
                context["start_date"] = self.request.GET["start"]
        except MultiValueDictKeyError:
            context["start_date"] = date.strftime("%Y-%m-%d")

        context["years"] = list(range(date.year, 1964, -1))
        context["months"] = [
            {
                "start": f"{date.year}-{str(i).zfill(2)}",
                "display": f"{calendar.month_name[i]} {date.year}",
            }
            for i in range(1, 13)
        ]

        return context


class Users(TemplateView):
    template_name = "users/users.html"

    def get_context_data(self, **kwargs: dict) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Users"
        context["users"] = models.AuthUser.objects.filter(is_active=True)
        return context


class UserProfile(TemplateView):
    template_name = "users/profile.html"

    def get_context_data(self, **kwargs: dict) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "User Profile"

        context["user_info"] = models.AuthUser.objects.get(
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
            ).select_related("song", "song__first", "event")

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


# class Login(LoginView):
#     """Display the login form and handle the login action."""

#     template_name = "users/login.html"


class Login(LoginView):
    form_class = LoginForm
    template_name = "users/login.html"

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


class SignUp(TemplateView):
    template_name = "users/signup.html"
    email_template_name = "users/signup_email.html"
    subject_template_name = "users/signup_confirm_subject.txt"
    token_generator = default_token_generator
    form_class = UserForm
    extra_email_context = None
    from_email = None
    html_email_template_name = None

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["title"] = "Signup"
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


class SignUpConfirm(TemplateView):
    template_name = "users/signup_done.html"
    reset_url_token = "activate"  # noqa: S105
    token_generator = default_token_generator

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


class UserSettings(TemplateView):
    template_name = "users/settings.html"
    form_class = UpdateUserForm

    def get_context_data(self, **kwargs: dict) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "User Settings"
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


class SignUpDone(TemplateView):
    template_name = "users/signup_done.html"

    def get_context_data(self, **kwargs: dict) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Sign Up Complete"
        return context


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


from collections import namedtuple


class EventDetail(TemplateView):
    template_name = "databruce/events/detail.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)

        context["id"] = self.kwargs["id"]

        archive = (
            models.ArchiveLinks.objects.select_related("event")
            .filter(
                event=OuterRef("id"),
            )
            .values("url")
        )

        bootleg = (
            models.Bootlegs.objects.select_related("event")
            .filter(
                event=OuterRef("id"),
            )
            .values("id")
        )

        nugs = (
            models.NugsReleases.objects.select_related("event")
            .filter(
                event=OuterRef("id"),
            )
            .values(json=JSONObject(id="id", url="url"))
        )

        context["event"] = (
            models.Events.objects.filter(id=self.kwargs["id"])
            .select_related(
                "venue",
                "artist",
                "tour",
                "venue__city",
                "venue__country",
            )
            .prefetch_related(
                "leg",
                "run",
                "venue__city__state",
                "venue__city__country",
            )
            .annotate(
                archive=ArraySubquery(archive),
                boot=ArraySubquery(bootleg),
                nugs=Subquery(nugs),
            )
        ).first()

        context["official"] = (
            models.ReleaseTracks.objects.filter(
                event__id=self.kwargs["id"],
            )
            .distinct("release__id")
            .select_related("release")
            .prefetch_related("event")
            .order_by("release__id")
        )

        context["title"] = f"{context['event']} {context['event'].venue.name}"

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

        context["setlist_exists"] = (
            models.Setlists.objects.select_related("song", "event")
            .filter(event__id=context["event"].id)
            .exists()
        )

        # setlist = (
        #     models.Setlists.objects.filter(event__id=context["event"].id)
        #     .annotate(
        #         separator=Case(
        #             When(segue=True, then=Value(">")),
        #         ),
        #     )
        #     .select_related("song", "event")
        #     .prefetch_related("ltp")
        # )

        # context["setlist"] = setlist.exclude(set_name="Soundcheck").order_by("song_num")

        context["setlist_copy"] = (
            models.Setlists.objects.filter(
                event__id=context["event"].id,
                song_num__isnull=False,
            )
            .order_by("song_num")
            .values_list(
                "song__name",
                flat=True,
            )
        )

        # context["soundcheck"] = models.Setlists.objects.filter(
        #     event__id=context["event"].id,
        #     set_name="Soundcheck",
        # ).select_related("song")

        context["onstage"] = models.Onstage.objects.filter(
            event=context["event"].id,
        ).exists()

        # context["onstage"] = onstage.filter(band=None)

        # context["bands"] = onstage.exclude(band=None)

        if self.request.user.is_authenticated:
            context["user_attended"] = models.UserAttendedShows.objects.filter(
                user=self.request.user.id,
                event=self.kwargs["id"],
            )

        context["user_count"] = models.UserAttendedShows.objects.filter(
            event=context["event"].id,
        ).count()

        # CURRENT BELOW
        context["setlist_unique"] = (
            models.Setlists.objects.filter(event=self.kwargs["id"])
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


class Event(TemplateView):
    template_name = "databruce/events/events.html"

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
        context["title"] = "Events"

        try:
            context["year"] = self.kwargs["year"]
        except KeyError:
            context["year"] = date.year  # current year

        context["years"] = list(range(date.year, 1964, -1))

        context["event_info"] = self.queryset.filter(id__startswith=context["year"])

        return context


class Venue(TemplateView):
    template_name = "databruce/locations/venues/venues.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["title"] = "Venues"

        context["venues"] = (
            models.Venues.objects.all()
            .order_by("name")
            .select_related("city", "country", "first", "last")
            .prefetch_related("state")
        )

        return context


class VenueDetail(TemplateView):
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
            .order_by("id")
        )

        context["venue_info"] = (
            models.Venues.objects.filter(
                id=self.kwargs["id"],
            )
            .annotate(
                formatted=Subquery(
                    models.VenuesText.objects.filter(id=OuterRef("id")).values(
                        "formatted",
                    ),
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


class SongLyrics(TemplateView):
    template_name = "databruce/songs/lyrics.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["lyrics"] = (
            models.Lyrics.objects.all().order_by("song__name").select_related("song")
        )
        return context


class SongLyricDetail(TemplateView):
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

        return context


class SubqueryCount(Subquery):
    # Custom Count function to just perform simple count on any queryset without grouping.
    # https://stackoverflow.com/a/47371514/1164966
    template = "(SELECT count(*) FROM (%(subquery)s) _count)"
    output_field = PositiveIntegerField()


class SongDetail(TemplateView):
    template_name = "databruce/songs/detail.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)

        context["song_info"] = (
            models.Songs.objects.filter(id=self.kwargs["id"])
            .prefetch_related(
                "album",
            )
            .first()
        )

        context["show_gap"] = models.Events.objects.filter(
            id__gt=context["song_info"].last.id,
            public=True,
        ).count()

        context["title"] = f"{context['song_info'].name}"

        context["setlists"] = models.Setlists.objects.filter(
            song__id=self.kwargs["id"],
        ).annotate(
            public=SubqueryCount(
                models.Setlists.objects.filter(
                    song=OuterRef("song"),
                    set_name__in=VALID_SET_NAMES,
                ),
            ),
            private=SubqueryCount(
                models.Setlists.objects.filter(
                    song=OuterRef("song"),
                ).exclude(set_name__in=VALID_SET_NAMES),
            ),
        )

        try:
            context["counts"] = context["setlists"].values("public", "private")[0]
        except IndexError:
            context["counts"] = {"public": 0, "private": 0}

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

        snippets = models.Snippets.objects.filter(
            snippet=self.kwargs["id"],
        ).order_by("position")

        context["snippet_count"] = snippets.count()

        filter = Q(event_certainty__in=["Confirmed", "Probable"])

        if context["song_info"].num_plays_public > 0:
            context["year_stats"] = (
                models.Setlists.objects.select_related("event")
                .filter(
                    song_id=self.kwargs["id"],
                    set_name__in=VALID_SET_NAMES,
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

            filter.add(
                Q(
                    id__gt=context["song_info"].first.id,
                ),
                Q.AND,
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


def event_search(request: HttpRequest):
    data = None

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        q = request.GET.get("term", "")
        results = []

        search_qs = models.Events.objects.filter(date__startswith=q).order_by("id")

        for r in search_qs:
            result = {
                "id": r.id,
                "value": f"{r.get_date()} - {r.venue}",
                "date": r.get_date(),
            }

            results.append(result)

        data = json.dumps(results)

    return HttpResponse(data, "application/json")


class EventSearch(TemplateView):
    template_name = "databruce/search/search.html"

    def get(self, request, *args, **kwargs):
        date = self.request.GET["date"]

        queryset = models.Events.objects.all()

        result = queryset.filter(
            date=date,
        ).order_by(
            "id",
        )

        if result.count() == 1:
            return redirect(f"/events/{result.first().id}")

        return render(
            request,
            self.template_name,
        )


class Tour(TemplateView):
    template_name = "databruce/tours/tours.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)

        context["tours"] = (
            models.Tours.objects.all()
            .order_by("-last")
            .select_related("first", "last", "band")
        )

        context["title"] = "Tours"

        return context


class TourDetail(TemplateView):
    template_name = "databruce/tours/detail.html"

    sets = [
        "Show",
        "Set 1",
        "Set 2",
        "Encore",
    ]

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["tour"] = (
            models.Tours.objects.filter(id=self.kwargs["id"])
            .select_related("band")
            .first()
        )

        context["title"] = f"{context['tour']}"

        context["events"] = (
            models.Events.objects.filter(tour=context["tour"].id)
            .order_by("id")
            .select_related(
                "artist",
                "tour",
                "venue",
                "venue__city",
                "venue__city__country",
            )
            .prefetch_related("venue__city__state", "venue__city__state__country")
        )

        if context["tour"].num_legs > 0:
            context["tour_legs"] = (
                models.TourLegs.objects.filter(
                    tour__id=context["tour"].id,
                )
                .order_by(
                    "first",
                )
                .select_related("first", "last")
            )

        songfilter = Q(event__tour__id=context["tour"].id)

        if context["tour"].id != 49:
            songfilter.add(Q(set_name__in=VALID_SET_NAMES), Q.AND)

        context["songs"] = (
            models.Setlists.objects.filter(
                songfilter,
            )
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

        if context["songs"].count() > 0:
            context["slots"] = (
                models.SetlistEntries.objects.select_related("event")
                .prefetch_related(
                    "show_opener",
                    "s1_closer",
                    "s2_opener",
                    "main_closer",
                    "encore_opener",
                    "show_closer",
                )
                .filter(
                    event__tour__id=context["tour"].id,
                )
                .order_by("event")
            )

        return context


class Contact(View):
    form_class = ContactForm
    template_name = "databruce/contact.html"

    def get(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        return render(
            request,
            self.template_name,
            context={"form": self.form_class()},
        )

    def post(self, request: HttpRequest):
        form = self.form_class(request.POST)

        if form.is_valid():
            if form.cleaned_data["verification"] == "1975":
                use_https = False

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


class SetlistNotesSearch(View):
    form_class = SetlistNoteSearch

    def get(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        form = self.form_class(request.GET)

        if form.is_valid():
            results = (
                models.SetlistNotes.objects.filter(
                    note__search=form.cleaned_data["query"],
                )
                .select_related(
                    "id",
                    "id__song",
                    "event",
                    "event__venue",
                    "id__event",
                    "event__venue",
                    "event__artist",
                    "event__tour",
                    "event__venue__city",
                    "event__venue__country",
                    "event__venue__first",
                    "event__venue__last",
                )
                .prefetch_related(
                    "event__venue__state",
                    "event__run",
                    "event__venue__city__state",
                    "event__venue__city__country",
                )
            )

            return render(
                request,
                "databruce/search/notes_search_results.html",
                context={
                    # "results": results.order_by("id"),
                    "query": form.cleaned_data["query"],
                },
            )

        return render(
            request,
            "databruce/search/notes_search.html",
            context={"form": self.form_class()},
        )

    def post(self, request: HttpRequest):
        form = self.form_class(request.POST)

        if form.is_valid():
            results = models.SetlistNotes.objects.filter(
                note__search=form.cleaned_data["query"],
            ).select_related(
                "id",
                "id__song",
                "id__event",
                "event",
                "id__event__venue",
                "event__venue",
            )

        return render(
            request,
            "databruce/search/notes_search_results.html",
            context={
                "results": results.order_by("id"),
                "query": form.cleaned_data["query"],
            },
        )


class SetlistNotesSearchResults(TemplateView):
    template_name = "databruce/search/notes_search_results.html"
    form_class = SetlistNoteSearch

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = self.form_class(self.request.GET)

        if form.is_valid():
            context["query"] = form.cleaned_data["query"]

        return context


class AdvancedSearch(View):
    form_class = AdvancedEventSearch
    formset_class = formset_factory(SetlistSearch)

    def get(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        form = self.form_class()

        setlist_formset = self.formset_class(
            {
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "0",
                "form-0-choice": "is",
                "form-0-position": "anywhere",
            },
        )

        return render(
            request,
            "databruce/search/advanced_search.html",
            context={"form": form, "formset": setlist_formset},
        )


class AdvancedSearchResults(View):
    template_name = "databruce/search/advanced_search_results.html"
    form_class = AdvancedEventSearch
    formset_class = formset_factory(SetlistSearch)

    def check_field_choice(self, choice: str, field_filter: Q) -> Q:
        """Every field has a IS/NOT choice on it. Depending on that choice, the filter can be negated or not. This checks for that value and returns the correct filter."""
        if choice == "not":
            return ~field_filter

        return field_filter

    def get_lookup(self, data: dict, field: dict) -> Q | None:
        fields = {
            "first_date": "date__gte",
            "last_date": "date__lte",
            "month": "date__month",
            "day": "date__day",
            "venue": "venue__id",
            "city": "venue__city__id",
            "state": "venue__state__id",
            "country": "venue__country__id",
            "tour": "tour__id",
            "musician": "relation__id",
            "band": "band__id",
            "day_of_week": "date__week_day",
        }

        lookup = fields.get(field)

        if lookup:
            try:
                return Q(**{f"{lookup}": data[field].id})
            except AttributeError:
                return Q(**{f"{lookup}": data[field]["id"]})
            except TypeError:
                return None

        return None

    def get(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        event_form = self.form_class(request.GET)
        formset = self.formset_class(request.GET)

        setlist = models.Setlists.objects.filter(
            set_name=OuterRef("set_name"),
            event__id=OuterRef("event__id"),
        ).select_related("song")

        setlist_qs = (
            models.Setlists.objects.filter(
                set_name__in=VALID_SET_NAMES,
            )
            .select_related("event", "song")
            .annotate(
                next_song=Subquery(
                    setlist.filter(song_num__gt=OuterRef("song_num"))
                    .order_by("event", "song_num")
                    .values("song__id")[:1],
                ),
            )
        )

        song_results = []
        event_results = []
        event_list = []
        display_fields = []

        setlist = ""

        setlist_event_filter = Q()
        event_filter = Q()

        if not event_form.has_changed() and not formset.has_changed():
            messages.warning(request, "Please fill out at least one field")
            return redirect(reverse("adv_search"))

        if event_form.is_valid() and event_form.has_changed():
            data = event_form.cleaned_data

            fields = [
                x
                for x in event_form.changed_data
                if "_choice" not in x and x != "conjunction"
            ]

            for field in fields:
                display = {
                    "label": event_form[field].label,
                    "data": data[field],
                }

                try:
                    choice = data[f"{field}_choice"]
                    lookup = self.get_lookup(data, field)

                    display["choice"] = choice

                    filter_to_add = self.check_field_choice(choice, lookup)

                    if field in ("musician", "band"):
                        events = models.Onstage.objects.filter(filter_to_add).values(
                            "event_id",
                        )
                        filter_to_add = Q(id__in=events)

                    event_filter &= self.check_field_choice(choice, filter_to_add)
                except KeyError:
                    event_filter &= self.get_lookup(data, field)

                display_fields.append(display)

        if formset.is_valid() and formset.has_changed():
            setlist = formset.cleaned_data
            form_fields = []

            for form in formset.cleaned_data:
                form_fields.append(form)

                if form["choice"] == "not" and form["position"] == "Followed By":
                    f = {
                        "song1": form["song2"],
                        "choice": "is",
                        "position": "Anywhere",
                        "hidden": "true",
                    }
                    form_fields.append(f)

            for form in form_fields:
                setlist_filter = Q()

                try:
                    song1 = form["song1"]["value"]

                    match form["position"]:
                        case "Followed By":
                            song2 = form["song2"]["value"]

                            song2_filter = self.check_field_choice(
                                form["choice"],
                                Q(next_song=form["song2"]["id"]),
                            )

                            setlist_filter = Q(
                                Q(song=form["song1"]["id"]) & song2_filter,
                            )

                            events = setlist_qs.filter(setlist_filter).values_list(
                                "event__id",
                                flat=True,
                            )

                            song_results.append(
                                f"{song1} ({form['choice']} followed by) {song2}",
                            )

                        case "Anywhere":
                            setlist_filter = self.check_field_choice(
                                form["choice"],
                                Q(song__id=form["song1"]["id"]),
                            )

                            events = setlist_qs.filter(setlist_filter).values_list(
                                "event__id",
                                flat=True,
                            )

                            try:
                                if not form["hidden"]:
                                    song_results.append(
                                        f"{song1} ({form['choice']} anywhere)",
                                    )
                            except KeyError:
                                song_results.append(
                                    f"{song1} ({form['choice']} anywhere)",
                                )
                        case _:
                            # all others except anywhere and followed by
                            position_filter = self.check_field_choice(
                                form["choice"],
                                Q(position=form["position"]),
                            )

                            setlist_filter = Q(
                                Q(song__id=form["song1"]["id"]) & position_filter,
                            )

                            events = setlist_qs.filter(setlist_filter).values_list(
                                "event__id",
                                flat=True,
                            )

                            song_results.append(
                                f"{song1} ({form['choice']} {form['position']})",
                            )

                    event_results.append(list(events))

                    match event_form.cleaned_data["conjunction"]:
                        case "or":
                            event_list = list(set.union(*map(set, event_results)))

                        case "and":
                            event_list = list(
                                set.intersection(*map(set, event_results)),
                            )

                except ValueError:
                    break
                except AttributeError:
                    break

        if event_list:
            setlist_event_filter = Q(id__in=event_list)

        result = (
            models.Events.objects.filter(
                event_filter & setlist_event_filter,
            )
            .select_related(
                "venue",
                "venue__first",
                "venue__last",
                "venue__state",
                "venue__country",
                "venue__city",
                "venue__city__country",
                "artist",
                "tour",
            )
            .prefetch_related(
                "venue__city__state",
                "venue__city__state__country",
            )
            .annotate(
                setlist=Case(
                    When(Q(setlist_certainty__in=["Confirmed", "Probable"]), then=True),
                    default=False,
                ),
            )
            .order_by("id")
        )

        description = ""
        description += ",".join(
            [f"{item['label']}: {item['data']}" for item in display_fields],
        )
        description += f"Songs: {', '.join(song_results)}"

        return render(
            request=request,
            template_name=self.template_name,
            context={
                "title": "Advanced Search",
                "events": result,
                "description": description,
                "conjunction": event_form.cleaned_data["conjunction"],
                "setlist_form": setlist,
                "display_fields": display_fields,
            },
        )


class ShortenURL(TemplateView):
    def get(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        user = User.objects.first()
        short_url = shortener.create(user, request.GET["url"])

        return HttpResponse(
            json.dumps({"short_url": f"https://{request.get_host()}/s/{short_url}"}),
            content_type="application/json",
        )


class Relation(TemplateView):
    template_name = "databruce/relations/relations.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["title"] = "Relations"
        context["relations"] = (
            models.Relations.objects.all()
            .select_related(
                "first",
                "last",
            )
            .order_by("name")
        )
        return context


class Band(TemplateView):
    template_name = "databruce/bands/bands.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["title"] = "Bands"
        context["bands"] = (
            models.Bands.objects.filter()
            .select_related("first", "last")
            .order_by("name")
        )
        return context


class RelationDetail(TemplateView):
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

        context["events"] = (
            models.Events.objects.filter(
                id__in=models.Onstage.objects.filter(
                    relation=context["info"].id,
                ).values("event__id"),
            )
            .select_related(
                "venue",
                "artist",
                "venue__city",
                "venue__city__country",
                "tour",
            )
            .prefetch_related(
                "venue__city__state",
                "venue__city__state__country",
            )
            .order_by("id")
        )

        return context


class BandDetail(TemplateView):
    template_name = "databruce/bands/detail.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)

        context["info"] = get_object_or_404(models.Bands, id=self.kwargs["id"])
        context["title"] = f"{context['info']}"

        context["members"] = (
            models.Onstage.objects.filter(band=self.kwargs["id"])
            .select_related("relation", "event", "relation__first", "relation__last")
            .distinct("relation")
            .order_by("relation")
        )

        self.onstage_events = (
            models.Onstage.objects.filter(band=self.kwargs["id"])
            .select_related("relation", "relation__first", "relation__last")
            .order_by("relation")
        )

        context["events"] = (
            models.Events.objects.filter(
                id__in=self.onstage_events.values_list("event"),
            )
            .order_by(
                "id",
            )
            .select_related(
                "venue",
                "tour",
                "artist",
                "venue__city",
                "venue__city__country",
            )
            .prefetch_related(
                "venue__city__state",
                "venue__city__state__country",
            )
        )

        return context


class Release(TemplateView):
    template_name = "databruce/releases/releases.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["releases"] = models.Releases.objects.all().order_by("date")
        context["title"] = "Releases"
        return context


class ReleaseDetail(TemplateView):
    template_name = "databruce/releases/detail.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["info"] = get_object_or_404(models.Releases, id=self.kwargs["id"])
        context["title"] = f"{context['info'].name}"

        context["tracks"] = (
            models.ReleaseTracks.objects.filter(release=self.kwargs["id"])
            .prefetch_related("discid", "event", "setlist")
            .select_related("song")
            .order_by("discnum", "track")
        )

        return context


class City(TemplateView):
    template_name = "databruce/locations/cities/cities.html"
    queryset = (
        models.Cities.objects.all()
        .prefetch_related("state")
        .select_related("country", "first", "last")
        .order_by("name")
    )

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Cities"
        context["cities"] = self.queryset
        return context


class CityDetail(TemplateView):
    template_name = "databruce/locations/cities/detail.html"
    queryset = models.Cities.objects.all().select_related("country", "first", "last")

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        self.city = get_object_or_404(self.queryset, id=self.kwargs["id"])
        context["info"] = self.city
        context["title"] = f"{context['info']}"

        context["songs"] = (
            models.Setlists.objects.filter(
                event__venue__city__id=self.kwargs["id"],
                set_name__in=VALID_SET_NAMES,
            )
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
        context["events"] = (
            models.Events.objects.filter(venue__city=self.city.id)
            .select_related(
                "venue__city",
                "venue__city__country",
                "artist",
                "tour",
            )
            .prefetch_related("venue__city__state")
            .order_by("id")
        )
        context["venues"] = models.Venues.objects.filter(city__id=self.city.id)

        return context


class State(TemplateView):
    template_name = "databruce/locations/states/states.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "States"
        context["states"] = (
            models.States.objects.all()
            .select_related("country", "first", "last")
            .order_by("name")
        )
        return context


class StateDetail(TemplateView):
    template_name = "databruce/locations/states/detail.html"
    queryset = models.States.objects.select_related(
        "country",
        "first__venue",
        "last__venue",
    )

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["info"] = get_object_or_404(self.queryset, id=self.kwargs["id"])
        context["title"] = f"{context['info']}"

        context["events"] = (
            models.Events.objects.filter(
                venue__state=self.kwargs["id"],
            )
            .select_related(
                "venue__city",
                "venue__city__state",
                "venue__city__country",
                "venue__country",
                "artist",
                "tour",
            )
            .order_by("id")
        )

        context["songs"] = (
            models.Setlists.objects.filter(
                event__venue__state__id=self.kwargs["id"],
                set_name__in=VALID_SET_NAMES,
            )
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

        context["venues"] = models.Venues.objects.filter(state__id=self.kwargs["id"])

        return context


class Country(TemplateView):
    template_name = "databruce/locations/countries/countries.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Countries"
        context["countries"] = (
            models.Countries.objects.all()
            .select_related("first", "last")
            .order_by("name")
        )
        return context


class CountryDetail(TemplateView):
    template_name = "databruce/locations/countries/detail.html"
    queryset = models.Countries.objects.select_related(
        "first",
        "last",
    )

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["info"] = get_object_or_404(self.queryset, id=self.kwargs["id"])
        context["title"] = f"{context['info']}"

        context["events"] = (
            models.Events.objects.filter(venue__country=context["info"].id)
            .select_related(
                "artist",
                "tour",
                "venue__city",
                "venue__city__country",
            )
            .prefetch_related(
                "venue__city__state",
            )
            .order_by("id")
        )

        context["songs"] = (
            models.Setlists.objects.filter(
                event__id__in=context["events"].values("id"),
                set_name__in=VALID_SET_NAMES,
            )
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
            )
        )

        context["venues"] = models.Venues.objects.filter(
            country__id=self.kwargs["id"],
        ).order_by("name")

        return context


class EventRun(TemplateView):
    template_name = "databruce/events/runs.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Event Runs"
        context["runs"] = (
            models.Runs.objects.all()
            .select_related(
                "first",
                "last",
                "band",
                "venue",
                "venue__city",
                "venue__city__country",
            )
            .prefetch_related("venue__city__state", "venue__city__state__country")
            .order_by("first")
        )

        return context


class RunDetail(TemplateView):
    template_name = "databruce/events/run_detail.html"
    queryset = (
        models.Runs.objects.all()
        .select_related(
            "first",
            "last",
            "band",
            "venue",
        )
        .order_by("first")
    )

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["info"] = get_object_or_404(self.queryset, id=self.kwargs["id"])
        context["title"] = f"{context['info']}"
        context["events"] = (
            models.Events.objects.filter(run__id=context["info"].id)
            .order_by(
                "id",
            )
            .select_related(
                "artist",
                "venue",
                "tour",
                "venue__city",
                "venue__city__country",
            )
            .prefetch_related("venue__city__state", "venue__state")
        )

        context["songs"] = (
            models.Setlists.objects.filter(
                event__id__in=context["events"].values("id"),
                set_name__in=VALID_SET_NAMES,
            )
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


class TourLeg(TemplateView):
    template_name = "databruce/tours/legs.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Tour Legs"
        context["legs"] = (
            models.TourLegs.objects.all()
            .select_related("first", "last", "tour")
            .order_by("-last")
        )
        return context


class TourLegDetail(TemplateView):
    template_name = "databruce/tours/leg_detail.html"
    queryset = (
        models.TourLegs.objects.all()
        .select_related("first", "last", "tour")
        .order_by("first")
    )

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        self.leg = get_object_or_404(self.queryset, id=self.kwargs["id"])
        context["info"] = self.leg
        context["title"] = f"{context['info']}"
        context["events"] = (
            models.Events.objects.filter(leg__id=self.leg.id)
            .order_by(
                "id",
            )
            .select_related(
                "venue",
                "artist",
                "tour",
                "venue__city",
                "venue__country",
                "venue__city__country",
            )
            .prefetch_related("venue__city__state", "venue__city__state__country")
        )

        context["songs"] = (
            models.Setlists.objects.filter(
                event__leg=self.leg.id,
                set_name__in=VALID_SET_NAMES,
            )
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
        context["venues"] = models.Venues.objects.filter(
            id__in=context["events"].values_list("venue"),
        ).order_by("name")

        return context


class NugsRelease(TemplateView):
    template_name = "databruce/releases/nugs.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["title"] = "Nugs Releases"

        context["releases"] = (
            models.NugsReleases.objects.all()
            .select_related(
                "event",
                "event__venue",
                "event__venue__first",
                "event__venue__last",
                "event__venue__state",
                "event__venue__country",
            )
            .prefetch_related(
                "event__venue__city",
                "event__venue__city__state",
                "event__venue__city__country",
            )
            .order_by("date")
        )

        return context


class Bootleg(TemplateView):
    template_name = "databruce/releases/bootlegs.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["title"] = "Bootlegs"

        context["bootlegs"] = (
            models.Bootlegs.objects.exclude(archive=None)
            .prefetch_related(
                "event",
            )
            .select_related("archive")
            .order_by("event")
        )

        return context


class Updates(TemplateView):
    template_name = "databruce/updates.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["title"] = "Updates"

        context["updates"] = models.Updates.objects.all().order_by("-created_at")

        return context
