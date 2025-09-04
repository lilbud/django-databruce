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
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db.models import (
    Case,
    Count,
    F,
    Max,
    Min,
    Q,
    Sum,
    Value,
    When,
)
from django.db.models.functions import TruncYear
from django.forms import formset_factory
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template import loader
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import TemplateView
from shortener import shortener

from . import forms, models
from .templatetags import search_filters

UserModel = get_user_model()
logger = logging.getLogger("django.contrib.auth")


class Index(TemplateView):
    template_name = "databruce/index.html"
    queryset = models.Events.objects.all().select_related(
        "artist",
        "venue",
        "venue__city",
        "venue__city__country",
        "venue__city__state",
        "venue__state",
        "venue__country",
    )

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["title"] = "Home"
        context["date"] = datetime.datetime.today()
        context["events"] = self.queryset.filter(
            date__month=datetime.datetime.today().month,
            date__day=datetime.datetime.today().day,
        ).order_by("-id")[:5]

        context["recent"] = self.queryset.filter(
            date__lte=datetime.datetime.today(),
        ).order_by("-id")[:5]

        context["upcoming"] = self.queryset.filter(
            date__gt=datetime.datetime.today(),
        ).order_by("id")[:5]

        context["updates"] = models.Updates.objects.all().order_by("-created_at")[:10]

        context["latest_event"] = (
            models.Setlists.objects.all()
            .select_related(
                "event",
                "event__artist",
                "event__venue",
                "event__venue__city",
                "event__venue__city__state",
                "event__venue__city__country",
                "event__venue__state",
                "event__venue__state__country",
            )
            .order_by("-event")
            .first()
        )

        context["latest_show"] = (
            models.Setlists.objects.filter(event__id=context["latest_event"].event.id)
            .annotate(
                separator=Case(When(segue=True, then=Value(">")), default=Value(",")),
            )
            .select_related("song")
            .order_by("song_num")
        )

        return context


class Song(TemplateView):
    template_name = "databruce/songs/songs.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["title"] = "Songs"
        context["songs"] = (
            models.Songs.objects.all()
            .prefetch_related("first", "last")
            .order_by("name")
        )

        return context


class About(TemplateView):
    template_name = "databruce/about.html"

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

        context["user_shows"] = models.UserAttendedShows.objects.filter(
            user__username__iexact=self.kwargs["username"],
        ).select_related(
            "event",
            "event__tour",
            "event__venue",
            "event__artist",
            "event__venue__city",
            "event__venue__city__state",
            "event__venue__city__country",
        )

        if context["user_shows"].count() > 0:
            context["user_songs"] = models.Setlists.objects.filter(
                event__id__in=context["user_shows"].values_list("event__id"),
                set_name__in=[
                    "Show",
                    "Set 1",
                    "Set 2",
                    "Encore",
                    "Pre-Show",
                    "Post-Show",
                ],
            ).select_related("song")

            context["user_seen"] = (
                context["user_songs"]
                .values("song__id")
                .annotate(
                    songid=F("song__id"),
                    name=F("song__name"),
                    count=Count("event"),
                    first=Min("event"),
                    firstdate=Min("event__date"),
                )
                .order_by("-count", "name")
            )

            context["user_not_seen"] = (
                models.Songs.objects.exclude(
                    id__in=context["user_songs"].values_list("song__id"),
                )
                .filter(num_plays_public__gte=100)
                .order_by("-num_plays_public")
            )

            context["user_rare_songs"] = models.Songs.objects.filter(
                id__in=context["user_songs"].values("song__id"),
                num_plays_public__lte=100,
            ).order_by("num_plays_public")

        return context


class SignUp(TemplateView):
    template_name = "users/signup.html"
    email_template_name = "users/signup_email.html"
    subject_template_name = "users/signup_confirm_subject.txt"
    token_generator = default_token_generator
    form_class = forms.UserForm
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
            use_https = False
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

            return redirect(reverse("login"))

        return render(request, template_name=self.template_name, context={"form": form})

    def send_mail(
        self,
        context: dict,
        from_email: str,
        to_email: str,
    ):
        subject_template_name = "users/signup_confirm_subject.txt"
        email_template_name = "users/signup_email.html"

        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = "".join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        return requests.post(
            "https://api.mailgun.net/v3/databruce.com/messages",
            auth=("api", os.getenv("MAILGUN_API", "MAILGUN_API")),
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
    form_class = forms.UpdateUserForm

    def get_context_data(self, **kwargs: dict) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "User Settings"
        context["form"] = self.form_class(instance=self.request.user)

        return context

    def post(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):
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


class UserAddShow(View):
    def post(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        models.UserAttendedShows.objects.create(
            user_id=request.user.id,
            event_id=request.POST["event"],
        )

        print(f"{request.POST['event']} added to user profile")

        return redirect(
            request.META.get("HTTP_REFERER", "redirect_if_referer_not_found"),
        )


class UserRemoveShow(View):
    def post(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        models.UserAttendedShows.objects.filter(
            user_id=request.user.id,
            event_id=request.POST["event"],
        ).delete()

        print(f"{request.POST['event']} added to user profile")

        return redirect(
            request.META.get("HTTP_REFERER", "redirect_if_referer_not_found"),
        )


class EventDetail(TemplateView):
    template_name = "databruce/events/detail.html"
    queryset = (
        models.Events.objects.all()
        .select_related(
            "venue",
            "artist",
            "venue__city",
            "venue__country",
            "tour",
        )
        .prefetch_related("venue__state")
    )

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["event"] = self.queryset.filter(id=self.kwargs["id"]).first()

        context["title"] = f"{context['event']} {context['event'].venue}"
        context["setlist"] = (
            models.Setlists.objects.filter(event__id=context["event"].id)
            .annotate(
                separator=Case(When(segue=True, then=Value(">")), default=Value(",")),
            )
            .select_related("song", "event")
            .prefetch_related("ltp")
            .order_by("song_num")
        )

        onstage = (
            models.Onstage.objects.filter(event__id=context["event"].id)
            .select_related("relation")
            .order_by("band_id", "relation__name")
        )

        context["musicians"] = onstage.filter(band=None)

        context["bands"] = onstage.exclude(band=None).select_related("band")

        context["notes"] = (
            models.SetlistNotes.objects.filter(
                event__id=context["event"].id,
            )
            .select_related("id", "event")
            .order_by("num")
        )

        context["prev_event"] = self.queryset.filter(id__lt=context["event"].id).last()
        context["next_event"] = self.queryset.filter(id__gt=context["event"].id).first()

        if not context["prev_event"]:
            context["prev_event"] = self.queryset.last()

        if not context["next_event"]:
            context["next_event"] = self.queryset.first()

        context["official"] = (
            models.ReleaseTracks.objects.filter(
                event__id=context["event"].id,
            )
            .distinct("release__id")
            .select_related("release")
            .order_by("release__id")
        )

        context["bootleg"] = models.Bootlegs.objects.filter(
            event__id=context["event"].id,
        )
        context["archive"] = models.ArchiveLinks.objects.filter(
            event__id=context["event"].id,
        ).distinct("url")

        context["nugs"] = models.NugsReleases.objects.filter(
            event__id=context["event"].id,
        ).first()

        if self.request.user.is_authenticated:
            context["user_shows"] = models.UserAttendedShows.objects.filter(
                user=self.request.user.id,
                event=context["event"].id,
            ).values_list("event__id", flat=True)

        context["user_count"] = (
            models.UserAttendedShows.objects.filter(
                event=context["event"].id,
            )
            .distinct("user__id")
            .count()
        )

        if context["event"].artist.springsteen_band:
            context["album_breakdown"] = (
                models.Songs.objects.filter(
                    id__in=context["setlist"]
                    .filter(
                        set_name__in=[
                            "Show",
                            "Set 1",
                            "Set 2",
                            "Pre-Show",
                            "Encore",
                            "Post-Show",
                        ],
                    )
                    .values_list("song__id")
                    .values("song__id"),
                )
                .values("category", "album")
                .annotate(num=Count("id"))
                .order_by("-num")
            )

            context["setlist_unique"] = models.Setlists.objects.filter(
                event__id=context["event"].id,
                set_name__in=[
                    "Show",
                    "Set 1",
                    "Set 2",
                    "Pre-Show",
                    "Encore",
                    "Post-Show",
                ],
            ).select_related("song")

            context["album_max"] = context["album_breakdown"].aggregate(max=Max("num"))

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
            "venue__city__state",
            "venue__city__country",
            "venue__state",
            "venue__country",
        )
        .order_by("id")
    )
    date = datetime.datetime.today()

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["title"] = "Events"

        try:
            self.year = self.kwargs["year"]
        except KeyError:
            self.year = self.date.year

        context["year"] = self.year
        context["years"] = list(range(1965, self.date.year + 1))
        context["event_info"] = self.queryset.filter(id__startswith=self.year)

        return context


class Venue(TemplateView):
    template_name = "databruce/locations/venues/venues.html"
    queryset = (
        models.Venues.objects.all()
        .order_by("name")
        .select_related(
            "city",
            "city__state",
            "city__state__country",
            "city__country",
            "state",
            "country",
            "first",
            "last",
        )
    )

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["title"] = "Venues"
        context["venues"] = self.queryset
        return context


class VenueDetail(TemplateView):
    template_name = "databruce/locations/venues/detail.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)

        context["events"] = models.Events.objects.filter(
            venue__id=self.kwargs["id"],
        ).select_related("artist", "tour")

        context["venue_info"] = (
            models.Venues.objects.filter(
                id=self.kwargs["id"],
            )
            .select_related("city", "city__state", "city__country")
            .first()
        )

        context["title"] = f"{context['venue_info'].name}"

        context["songs"] = (
            models.Setlists.objects.filter(
                event__venue__id=self.kwargs["id"],
            )
            .values(
                "song_id",
            )
            .annotate(
                plays=Count("event_id"),
                name=F("song__name"),
                show_opener=Sum(
                    Case(
                        When(position="Show Opener", then=Value(1)),
                        default=Value(0),
                    ),
                ),
                main_set_closer=Sum(
                    Case(
                        When(position="Main Set Closer", then=Value(1)),
                        default=Value(0),
                    ),
                ),
                encore_opener=Sum(
                    Case(
                        When(position="Encore Opener", then=Value(1)),
                        default=Value(0),
                    ),
                ),
                show_closer=Sum(
                    Case(
                        When(position="Show Closer", then=Value(1)),
                        default=Value(0),
                    ),
                ),
            )
            .order_by(
                "song_id",
            )
        )

        return context


class SongLyrics(TemplateView):
    template_name = "databruce/songs/lyrics.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["lyrics"] = models.Lyrics.objects.all().select_related("song")
        return context


class SongLyricDetail(TemplateView):
    template_name = "databruce/songs/lyric_detail.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
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


class SongDetail(TemplateView):
    template_name = "databruce/songs/detail.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)

        context["songs"] = (
            models.SongsPage.objects.filter(
                id=self.kwargs["id"],
            )
            .select_related(
                "current__event",
                "current__event__venue",
                "current__event__venue__city",
                "current__event__venue__city__country",
                "current__event__venue__city__state",
                "current__event__venue__city__state__country",
                "current__event__artist",
                "current__event__tour",
            )
            .prefetch_related("next__song", "prev__song")
        )

        valid_set_names = [
            "Show",
            "Set 1",
            "Set 2",
            "Encore",
            "Pre-Show",
            "Post-Show",
        ]

        context["song_info"] = (
            models.Songs.objects.filter(id=self.kwargs["id"])
            .prefetch_related(
                "album",
            )
            .first()
        )

        context["title"] = f"{context['song_info'].name}"

        setlists = models.Setlists.objects.filter(song__id=self.kwargs["id"])

        context["public_count"] = setlists.filter(
            set_name__in=valid_set_names,
        ).count()

        context["private_count"] = setlists.exclude(
            set_name__in=valid_set_names,
        ).count()

        context["snippet_count"] = setlists.filter(
            snippet=True,
        ).count()

        context["positions"] = (
            setlists.filter(set_name__in=valid_set_names)
            .exclude(position=None)
            .values("position")
            .annotate(
                count=Count("position"),
                num=Min("song_num"),
            )
        ).order_by("num")

        if context["song_info"].lyrics:
            context["lyrics"] = models.Lyrics.objects.filter(
                song__id=self.kwargs["id"],
            ).order_by("id")

        context["snippets"] = (
            models.Snippets.objects.filter(
                snippet=self.kwargs["id"],
            )
            .select_related("setlist", "setlist__event", "snippet", "setlist__song")
            .order_by("setlist__event", "position")
        )

        filter = Q(event_certainty__in=["Confirmed", "Probable"])

        valid_set_names = [
            "Show",
            "Set 1",
            "Set 2",
            "Encore",
            "Pre-Show",
            "Post-Show",
        ]

        if context["song_info"].num_plays_public > 0:
            context["year_stats"] = (
                models.Setlists.objects.filter(
                    song_id=self.kwargs["id"],
                    set_name__in=valid_set_names,
                )
                .annotate(
                    year=TruncYear("event__date"),
                )
                .values("year")
                .annotate(
                    event_count=Count(
                        "event_id",
                        distinct=True,
                        filter=Q(set_name__in=valid_set_names),
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

        return context


def event_search(request: HttpRequest):
    data = None

    if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
        q = request.GET.get("term", "")
        results = []

        search_qs = models.Events.objects.filter(date__startswith=q).order_by("id")

        for r in search_qs:
            result = {
                "id": r.id,
                "value": f"{r.date.strftime('%Y-%m-%d')} - {r.venue}",
                "date": r.date.strftime("%Y-%m-%d"),
            }

            if r.early_late:
                result["value"] = (
                    f"{r.date.strftime('%Y-%m-%d')} {r.early_late} - {r.venue}"
                )

            results.append(result)

        data = json.dumps(results)

    return HttpResponse(data, "application/json")


class EventSearch(TemplateView):
    template_name = "databruce/search/search.html"
    form = forms.EventSearch
    queryset = models.Events.objects.all().select_related(
        "venue",
        "venue__city",
        "venue__city__country",
        "venue__city__state",
        "artist",
        "tour",
    )

    def get(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        form = self.form(request.GET)

        if form.is_valid():
            print(form.cleaned_data)
            try:
                result = self.queryset.filter(
                    date=form.cleaned_data["date"],
                ).order_by(
                    "id",
                )
            except ValidationError:
                date = re.sub(r"\-", "", form.cleaned_data["date"])

                result = self.queryset.filter(
                    id__contains=date,
                ).order_by(
                    "id",
                )

            if len(result) == 1:
                return redirect(f"/events/{result.first().id}")

            return render(
                request,
                self.template_name,
                context={"events": result},
            )
        return None


class Tour(TemplateView):
    template_name = "databruce/tours/tours.html"
    queryset = (
        models.Tours.objects.all()
        .order_by("-last")
        .select_related(
            "first",
            "last",
            "band",
            "first__venue",
            "last__venue",
        )
    )

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["tours"] = self.queryset
        context["title"] = "Tours"

        return context


class TourDetail(TemplateView):
    template_name = "databruce/tours/detail.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["tour"] = (
            models.Tours.objects.filter(id=self.kwargs["id"])
            .select_related("band")
            .first()
        )
        context["title"] = f"{context['tour']}"
        context["events"] = (
            models.Events.objects.filter(tour=self.kwargs["id"])
            .order_by("id")
            .select_related(
                "venue",
                "tour",
                "artist",
                "venue__city",
                "venue__city__state",
                "venue__city__state__country",
                "venue__city__country",
                "venue__state",
                "venue__country",
            )
        )

        context["tour_legs"] = (
            models.TourLegs.objects.filter(
                tour__id=self.kwargs["id"],
            )
            .order_by(
                "first",
            )
            .select_related("first", "last")
        )

        valid_set_names = [
            "Show",
            "Set 1",
            "Set 2",
            "Encore",
            "Pre-Show",
            "Post-Show",
        ]

        context["songs"] = (
            models.Setlists.objects.filter(
                event__tour__id=self.kwargs["id"],
                set_name__in=valid_set_names,
            )
            .values(
                "song__id",
            )
            .annotate(
                plays=Count("event_id"),
                name=F("song__name"),
                show_opener=Sum(
                    Case(
                        When(position="Show Opener", then=Value(1)),
                        default=Value(0),
                    ),
                ),
                main_set_closer=Sum(
                    Case(
                        When(position="Main Set Closer", then=Value(1)),
                        default=Value(0),
                    ),
                ),
                encore_opener=Sum(
                    Case(
                        When(position="Encore Opener", then=Value(1)),
                        default=Value(0),
                    ),
                ),
                show_closer=Sum(
                    Case(
                        When(position="Show Closer", then=Value(1)),
                        default=Value(0),
                    ),
                ),
            )
            .order_by(
                "song_id",
            )
        )

        if len(context["songs"]) > 0:
            context["slots"] = (
                models.Setlists.objects.filter(
                    event__tour__id=self.kwargs["id"],
                    position__isnull=False,
                )
                .values("event__id")
                .annotate(
                    event_date=F("event__date"),
                    show_opener_id=Min(
                        Case(
                            When(position="Show Opener", then=F("song")),
                        ),
                    ),
                    show_opener_name=Min(
                        Case(
                            When(position="Show Opener", then=F("song__name")),
                        ),
                    ),
                    main_set_closer_id=Min(
                        Case(
                            When(position="Main Set Closer", then=F("song")),
                        ),
                    ),
                    main_set_closer_name=Min(
                        Case(
                            When(position="Main Set Closer", then=F("song__name")),
                        ),
                    ),
                    encore_opener_id=Min(
                        Case(
                            When(position="Encore Opener", then=F("song")),
                        ),
                    ),
                    encore_opener_name=Min(
                        Case(
                            When(position="Encore Opener", then=F("song__name")),
                        ),
                    ),
                    show_closer_id=Min(
                        Case(
                            When(
                                position="Show Closer",
                                then=F("song"),
                            ),
                        ),
                    ),
                    show_closer_name=Min(
                        Case(
                            When(
                                position="Show Closer",
                                then=F("song__name"),
                            ),
                        ),
                    ),
                )
            ).order_by("event")

        return context


class SetlistNotesSearch(View):
    form_class = forms.SetlistNoteSearch

    def get(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        form = self.form_class()

        return render(
            request,
            "databruce/search/notes_search.html",
            context={"form": form},
        )

    def post(self, request: HttpRequest):
        form = self.form_class(request.POST)

        if form.is_valid():
            results = (
                models.SetlistNotes.objects.filter(
                    note__icontains=form.cleaned_data["query"],
                )
                .select_related(
                    "id",
                    "id__song",
                    "event",
                )
                .prefetch_related("last", "last__artist", "last__venue")
            )

        return render(
            request,
            "databruce/search/notes_search_results.html",
            context={
                "results": results.order_by("id"),
                "query": form.cleaned_data["query"],
            },
        )


class AdvancedSearch(View):
    form_class = forms.AdvancedEventSearch
    formset_class = formset_factory(forms.SetlistSearch)
    date = datetime.datetime.today()

    def get(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        form = self.form_class()

        if request.GET.get("current", None):
            form = self.form_class(
                initial={
                    "month": self.date.month,
                    "day": self.date.day,
                },
            )

        setlist_formset = self.formset_class(
            {"form-TOTAL_FORMS": "1", "form-INITIAL_FORMS": "0"},
        )

        return render(
            request,
            "databruce/search/advanced_search.html",
            context={"form": form, "formset": setlist_formset},
        )


class AdvancedSearchResults(View):
    template_name = "databruce/search/advanced_search_results.html"
    form_class = forms.AdvancedEventSearch
    formset_class = formset_factory(forms.SetlistSearch)
    date = datetime.datetime.today()

    def check_field_choice(self, choice: str, field_filter: Q) -> Q:
        """Every field has a IS/NOT choice on it. Depending on that choice, the filter can be negated or not. This checks for that value and returns the correct filter."""
        if choice == "is":
            return field_filter

        return ~field_filter

    def get(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        event_form = self.form_class(request.GET)
        formset = self.formset_class(data=request.GET)
        song_results = []
        results = []

        if event_form.is_valid():
            form = event_form
            event_filter = Q(date__gte=event_form.cleaned_data["first_date"]) & Q(
                date__lte=event_form.cleaned_data["last_date"],
            )

            if (
                event_form.cleaned_data["first_date"].strftime("%Y-%m-%d")
                != "1965-01-01"
            ):
                results.append(f"Start Date: {event_form.cleaned_data['first_date']}")

            if (
                event_form.cleaned_data["last_date"].strftime("%Y-%m-%d")
                != f"{datetime.datetime.today().year}-12-31"
            ):
                results.append(f"End Date: {event_form.cleaned_data['last_date']}")

            if event_form.cleaned_data["month"]:
                event_filter.add(
                    self.check_field_choice(
                        event_form.cleaned_data["month_choice"],
                        Q(date__month=event_form.cleaned_data["month"]),
                    ),
                    Q.AND,
                )

                results.append(
                    f"Month: ({event_form.cleaned_data['month_choice']}) {search_filters.get_month_from_num(event_form.cleaned_data['month'])}",
                )

            if event_form.cleaned_data["day"]:
                event_filter.add(
                    self.check_field_choice(
                        event_form.cleaned_data["day_choice"],
                        Q(date__day=event_form.cleaned_data["day"]),
                    ),
                    Q.AND,
                )

                results.append(
                    f"Day: ({event_form.cleaned_data['day_choice']}) {event_form.cleaned_data['day']}",
                )

            if event_form.cleaned_data["city"]:
                event_filter.add(
                    self.check_field_choice(
                        event_form.cleaned_data["city_choice"],
                        Q(venue__city__id=event_form.cleaned_data["city"]),
                    ),
                    Q.AND,
                )

                results.append(
                    f"City: ({event_form.cleaned_data['city_choice']}) {search_filters.get_city(event_form.cleaned_data['city'])}",
                )

            if event_form.cleaned_data["state"]:
                event_filter.add(
                    self.check_field_choice(
                        event_form.cleaned_data["state_choice"],
                        Q(venue__state__id=event_form.cleaned_data["state"]),
                    ),
                    Q.AND,
                )
                results.append(
                    f"State: ({event_form.cleaned_data['state_choice']}) {search_filters.get_state(event_form.cleaned_data['state'])}",
                )

            if event_form.cleaned_data["country"]:
                event_filter.add(
                    self.check_field_choice(
                        event_form.cleaned_data["country_choice"],
                        Q(venue__country__id=event_form.cleaned_data["country"]),
                    ),
                    Q.AND,
                )
                results.append(
                    f"Country: ({event_form.cleaned_data['country_choice']}) {search_filters.get_country(event_form.cleaned_data['country'])}",
                )

            if event_form.cleaned_data["tour"]:
                event_filter.add(
                    self.check_field_choice(
                        event_form.cleaned_data["tour_choice"],
                        Q(tour__id=event_form.cleaned_data["tour"]),
                    ),
                    Q.AND,
                )

                results.append(
                    f"Tour: ({event_form.cleaned_data['tour_choice']}) {search_filters.get_tour(event_form.cleaned_data['tour'])}",
                )

            # musician and band query a different model, and have to be handled separately
            # I tried combining these into one Q filter, and it would instead look for events
            # where MUSICIAN was listed as part of BAND, rather than events with both which is the intended result
            if event_form.cleaned_data["musician"]:
                filter = self.check_field_choice(
                    event_form.cleaned_data["musician_choice"],
                    Q(relation__id=event_form.cleaned_data["musician"]),
                )

                events = models.Onstage.objects.filter(
                    filter,
                ).values_list("event")

                event_filter.add(Q(id__in=events), Q.AND)

                results.append(
                    f"Musician: ({event_form.cleaned_data['musician_choice']}) {search_filters.get_relation(event_form.cleaned_data['musician'])}",
                )

            if event_form.cleaned_data["band"]:
                filter = self.check_field_choice(
                    event_form.cleaned_data["band_choice"],
                    Q(band__id=event_form.cleaned_data["band"]),
                )

                events = models.Onstage.objects.filter(
                    filter,
                ).values_list("event")

                event_filter.add(Q(id__in=events), Q.AND)

                results.append(
                    f"Band: ({event_form.cleaned_data['band_choice']}) {search_filters.get_band(event_form.cleaned_data['band'])}",
                )

            if event_form.cleaned_data["day_of_week"]:
                event_filter.add(
                    self.check_field_choice(
                        event_form.cleaned_data["dow_choice"],
                        Q(date__week_day=event_form.cleaned_data["day_of_week"]),
                    ),
                    Q.AND,
                )

                results.append(
                    f"Day of Week: ({event_form.cleaned_data['dow_choice']}) {search_filters.get_day_from_num(event_form.cleaned_data['day_of_week'])}",
                )

        event_results = []
        setlist_event_filter = Q()

        if formset.is_valid():
            for form in formset.cleaned_data:
                try:
                    song1 = models.Songs.objects.get(id=form["song1"])
                    setlist_filter = Q(current__song__id=song1.id)

                    if form["position"] == "Followed By":
                        song2 = models.Songs.objects.get(id=form["song2"])

                        followed_filter = Q(next__song__id=song2.id)

                        if form["choice"] == "is":
                            setlist_filter.add(followed_filter, Q.AND)
                        else:
                            setlist_filter.add(~followed_filter, Q.AND)

                        song_results.append(
                            f"{song1} ({form['choice']} followed by) {song2}",
                        )

                        qs = models.SongsPage.objects.filter(
                            setlist_filter,
                        )

                        event_results.append(
                            list(qs.values_list("current__event", flat=True)),
                        )

                    elif form["position"] not in ["Anywhere", "Followed By"]:
                        # all others except anywhere and followed by
                        setlist_filter = Q(
                            set_name__in=[
                                "Show",
                                "Set 1",
                                "Set 2",
                                "Encore",
                                "Pre-Show",
                                "Post-Show",
                            ],
                        )

                        song_events = models.Setlists.objects.filter(
                            song__id=song1.id,
                        ).values("event__id")

                        if form["choice"] == "is":
                            setlist_filter.add(Q(song__id=song1.id), Q.AND)
                            setlist_filter.add(Q(position=form["position"]), Q.AND)
                            setlist_filter.add(Q(event__id__in=song_events), Q.AND)
                        else:
                            setlist_filter.add(~Q(song__id=song1.id), Q.AND)
                            setlist_filter.add(~Q(position=form["position"]), Q.AND)
                            setlist_filter.add(~Q(event__id__in=song_events), Q.AND)

                        song_results.append(
                            f"{song1} ({form['choice']} {form['position']})",
                        )

                        qs = models.Setlists.objects.filter(
                            setlist_filter,
                        )

                        event_results.append(
                            list(qs.values_list("event__id", flat=True)),
                        )

                    else:
                        setlist_filter = Q(
                            set_name__in=[
                                "Show",
                                "Set 1",
                                "Set 2",
                                "Encore",
                                "Pre-Show",
                                "Post-Show",
                            ],
                        )

                        song_events = models.Setlists.objects.filter(
                            song__id=song1.id,
                        ).values("event__id")

                        if form["choice"] == "is":
                            setlist_filter.add(Q(song__id=song1.id), Q.AND)
                            setlist_filter.add(Q(event__id__in=song_events), Q.AND)
                        else:
                            setlist_filter.add(~Q(song__id=song1.id), Q.AND)
                            setlist_filter.add(~Q(event__id__in=song_events), Q.AND)

                        qs = models.Setlists.objects.filter(
                            setlist_filter,
                        )

                        event_results.append(
                            list(qs.values_list("event__id", flat=True)),
                        )

                        song_results.append(
                            f"{song1} ({form['choice']} anywhere)",
                        )

                    if event_form.cleaned_data["conjunction"] == "and":
                        setlist_event_filter.add(
                            Q(
                                id__in=list(
                                    set.intersection(*map(set, event_results)),
                                ),
                            ),
                            Q.AND,
                        )

                    else:
                        setlist_event_filter.add(
                            Q(id__in=list(set.union(*map(set, event_results)))),
                            Q.OR,
                        )

                except ValueError:
                    break

        result = (
            models.Events.objects.filter(
                event_filter & setlist_event_filter,
            )
            .select_related(
                "venue",
                "artist",
                "venue__city",
                "venue__country",
                "tour",
            )
            .prefetch_related(
                "venue__city__state",
                "venue__city__country",
                "venue__city__state__country",
                "venue__state",
            )
        )

        description = ""
        event_des = song_des = ""

        if results:
            event_des = ", ".join(results)

        if song_results:
            song_des = f"Songs: {', '.join(song_results)}"

        description += event_des + song_des

        return render(
            request=request,
            template_name=self.template_name,
            context={
                "events": result.order_by("id"),
                "title": "Advanced Search",
                "description": description,
                "results": results,
                "song_results": song_results,
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
        context["relations"] = models.Relations.objects.all().select_related(
            "first",
            "last",
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
            models.Onstage.objects.filter(relation=context["info"].id)
            .select_related(
                "event__venue",
                "event__artist",
                "event__venue__city",
                "event__venue__city__state",
                "event__venue__city__state__country",
                "event__venue__city__country",
                "event__tour",
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
                "venue__city__state",
                "venue__city__state__country",
                "venue__city__country",
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
            .order_by(
                "track",
            )
            .prefetch_related("song__first", "song__last", "event")
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
            )
            .values(
                "song_id",
            )
            .annotate(
                plays=Count("event_id"),
                name=F("song__name"),
                show_opener=Sum(
                    Case(
                        When(position="Show Opener", then=Value(1)),
                        default=Value(0),
                    ),
                ),
                main_set_closer=Sum(
                    Case(
                        When(position="Main Set Closer", then=Value(1)),
                        default=Value(0),
                    ),
                ),
                encore_opener=Sum(
                    Case(
                        When(position="Encore Opener", then=Value(1)),
                        default=Value(0),
                    ),
                ),
                show_closer=Sum(
                    Case(
                        When(position="Show Closer", then=Value(1)),
                        default=Value(0),
                    ),
                ),
            )
            .order_by(
                "song_id",
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

        context["events"] = models.Events.objects.filter(
            venue__state=self.kwargs["id"],
        ).select_related(
            "venue__city",
            "venue__city__state",
            "venue__city__country",
            "venue__country",
            "artist",
            "tour",
        )

        context["songs"] = (
            models.Setlists.objects.filter(
                event__venue__state__id=self.kwargs["id"],
            )
            .values(
                "song_id",
            )
            .annotate(
                plays=Count("event_id"),
                name=F("song__name"),
                show_opener=Sum(
                    Case(
                        When(position="Show Opener", then=Value(1)),
                        default=Value(0),
                    ),
                ),
                main_set_closer=Sum(
                    Case(
                        When(position="Main Set Closer", then=Value(1)),
                        default=Value(0),
                    ),
                ),
                encore_opener=Sum(
                    Case(
                        When(position="Encore Opener", then=Value(1)),
                        default=Value(0),
                    ),
                ),
                show_closer=Sum(
                    Case(
                        When(position="Show Closer", then=Value(1)),
                        default=Value(0),
                    ),
                ),
            )
            .order_by(
                "song_id",
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
            models.Events.objects.filter(venue__country=self.kwargs["id"])
            .select_related(
                "venue__state",
                "venue__state__country",
                "artist",
                "tour",
                "venue__city",
                "venue__city__country",
                "venue__city__state",
            )
            .order_by("id")
        )

        context["songs"] = (
            models.Setlists.objects.filter(
                event__venue__country__id=self.kwargs["id"],
            )
            .values(
                "song_id",
            )
            .annotate(
                plays=Count("event_id"),
                name=F("song__name"),
                show_opener=Sum(
                    Case(
                        When(position="Show Opener", then=Value(1)),
                        default=Value(0),
                    ),
                ),
                main_set_closer=Sum(
                    Case(
                        When(position="Main Set Closer", then=Value(1)),
                        default=Value(0),
                    ),
                ),
                encore_opener=Sum(
                    Case(
                        When(position="Encore Opener", then=Value(1)),
                        default=Value(0),
                    ),
                ),
                show_closer=Sum(
                    Case(
                        When(position="Show Closer", then=Value(1)),
                        default=Value(0),
                    ),
                ),
            )
            .order_by(
                "song_id",
            )
        )

        context["venues"] = models.Venues.objects.filter(country__id=self.kwargs["id"])
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
                "venue__city__state",
                "venue__city__state__country",
                "venue__city__country",
            )
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
        self.run = get_object_or_404(self.queryset, id=self.kwargs["id"])
        context["info"] = self.run
        context["title"] = f"{context['info']}"
        context["events"] = (
            models.Events.objects.filter(run__id=self.run.id)
            .order_by(
                "id",
            )
            .select_related(
                "artist",
                "venue",
                "tour",
                "venue__city",
                "venue__city__state",
                "venue__city__country",
                "venue__city__state__country",
            )
        )

        context["songs"] = (
            models.Setlists.objects.filter(
                event__run=self.run.id,
            )
            .values(
                "song_id",
            )
            .annotate(
                plays=Count("event_id"),
                name=F("song__name"),
                show_opener=Sum(
                    Case(
                        When(position="Show Opener", then=Value(1)),
                        default=Value(0),
                    ),
                ),
                main_set_closer=Sum(
                    Case(
                        When(position="Main Set Closer", then=Value(1)),
                        default=Value(0),
                    ),
                ),
                encore_opener=Sum(
                    Case(
                        When(position="Encore Opener", then=Value(1)),
                        default=Value(0),
                    ),
                ),
                show_closer=Sum(
                    Case(
                        When(position="Show Closer", then=Value(1)),
                        default=Value(0),
                    ),
                ),
            )
            .order_by(
                "song_id",
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
            .select_related("first", "last")
            .order_by("first")
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
            .select_related("venue", "artist")
            .prefetch_related(
                "venue__city",
                "venue__city__state",
                "venue__city__country",
            )
        )

        context["songs"] = (
            models.Setlists.objects.filter(
                event__leg=self.leg.id,
            )
            .values(
                "song_id",
            )
            .annotate(
                plays=Count("event_id"),
                name=F("song__name"),
                show_opener=Sum(
                    Case(
                        When(position="Show Opener", then=Value(1)),
                        default=Value(0),
                    ),
                ),
                main_set_closer=Sum(
                    Case(
                        When(position="Main Set Closer", then=Value(1)),
                        default=Value(0),
                    ),
                ),
                encore_opener=Sum(
                    Case(
                        When(position="Encore Opener", then=Value(1)),
                        default=Value(0),
                    ),
                ),
                show_closer=Sum(
                    Case(
                        When(position="Show Closer", then=Value(1)),
                        default=Value(0),
                    ),
                ),
            )
            .order_by(
                "song_id",
            )
        )
        context["venues"] = models.Venues.objects.filter(
            id__in=context["events"].values_list("venue"),
        )

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
                "event__venue__city",
                "event__venue__city__state",
                "event__venue__city__state__country",
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
