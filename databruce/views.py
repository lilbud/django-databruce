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
from django.contrib.postgres.aggregates import ArrayAgg, JSONBAgg
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
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import TemplateView
from shortener import shortener

from . import forms, models, settings

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


class Index(TemplateView):
    template_name = "databruce/index.html"

    queryset = models.Events.objects.all().annotate(
        venue_info=Subquery(
            models.VenuesText.objects.filter(id=OuterRef("venue")).values(
                json=JSONObject(id="id", value="formatted"),
            ),
        ),
        band=Subquery(
            models.Bands.objects.filter(id=OuterRef("artist")).values(
                json=JSONObject(id="id", name="name"),
            ),
        ),
    )

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["title"] = "Home"
        context["date"] = datetime.datetime.today()

        context["events"] = self.queryset.filter(
            date__month=datetime.datetime.today().month,
            date__day=datetime.datetime.today().day,
        ).order_by("id")[:5]

        context["recent"] = self.queryset.filter(
            date__lte=datetime.datetime.today(),
        ).order_by("-id")[:5]

        context["upcoming"] = self.queryset.filter(
            date__gt=datetime.datetime.today(),
        ).order_by("id")[:5]

        context["updates"] = models.SiteUpdates.objects.all().order_by("-created_at")[
            :10
        ]

        context["latest_setlist"] = (
            models.Setlists.objects.all().order_by("-event").first()
        )

        context["latest_event"] = self.queryset.get(
            id=context["latest_setlist"].event.id,
        )

        context["latest_show"] = (
            models.Setlists.objects.filter(event=context["latest_event"].id)
            .annotate(
                song_info=Subquery(
                    models.Songs.objects.filter(id=OuterRef("song")).values(
                        json=JSONObject(id="id", name="name"),
                    ),
                ),
                separator=Case(
                    When(segue=True, then=Value(">")),
                ),
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
        context = super().get_context_data(**kwargs)

        setlist = models.Setlists.objects.filter(
            set_name=OuterRef("set_name"),
            event__id=OuterRef("event__id"),
        ).select_related("song")

        context["songs"] = (
            models.Setlists.objects.select_related("event", "song")
            .filter(
                song=164,
            )
            .annotate(
                venue=Subquery(
                    models.VenuesText.objects.filter(
                        id=OuterRef("event__venue"),
                    ).values(json=JSONObject(id="id", name="name")),
                ),
                prev_song=Subquery(
                    setlist.filter(song_num__lt=OuterRef("song_num"))
                    .order_by("-song_num", "-event")
                    .values(json=JSONObject(id="song__id", name="song__name"))[:1],
                ),
                next_song=Subquery(
                    setlist.filter(song_num__gt=OuterRef("song_num"))
                    .order_by("event", "song_num")
                    .values(json=JSONObject(id="song__id", name="song__name"))[:1],
                ),
            )
            .order_by("event", "song_num")
        )

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
    form_class = forms.UpdateUserForm

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
            request.META.get("HTTP_REFERER", "redirect_if_referer_not_found"),
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

        archive = models.ArchiveLinks.objects.filter(
            event=OuterRef("id"),
        ).values("url")

        bootleg = models.Bootlegs.objects.filter(
            event=OuterRef("id"),
        ).values("id")

        context["event"] = (
            models.Events.objects.filter(id=self.kwargs["id"])
            .select_related(
                "venue",
                "venue__id",
                "artist",
                "tour",
            )
            .annotate(
                # venue_loc=Subquery(
                #     models.VenuesText.objects.filter(id=OuterRef("venue")).values(
                #         json=JSONObject(id="id", name="formatted"),
                #     ),
                # ),
                tourleg=Subquery(
                    models.TourLegs.objects.filter(id=OuterRef("leg")).values(
                        json=JSONObject(id="id", name="name"),
                    ),
                ),
                eventrun=Subquery(
                    models.Runs.objects.filter(id=OuterRef("run")).values(
                        json=JSONObject(id="id", name="name"),
                    ),
                ),
                archive=ArraySubquery(archive),
                boot=ArraySubquery(bootleg),
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

        notes = models.SetlistNotes.objects.filter(
            id=OuterRef("pk"),
        ).select_related("event", "id")

        snippets = (
            models.Snippets.objects.order_by("position")
            .select_related("snippet", "setlist")
            .filter(
                setlist=OuterRef("pk"),
            )
            .values(
                json=JSONObject(
                    id="snippet__id",
                    name="snippet__name",
                    note="note",
                    position="position",
                    setlist="setlist__id",
                ),
            )
        )

        setlist = (
            models.Setlists.objects.filter(event__id=context["event"].id)
            .annotate(
                separator=Case(
                    When(segue=True, then=Value(">")),
                ),
                notes=ArraySubquery(notes.values("note")),
                # snippet_list=ArraySubquery(
                #     snippets,
                # ),
            )
            .select_related("song", "event")
            .prefetch_related("ltp")
        )

        context["setlist"] = setlist.exclude(set_name="Soundcheck").order_by("song_num")

        context["setlist_copy"] = context["setlist"].values_list(
            "song__name",
            flat=True,
        )

        context["soundcheck"] = models.Setlists.objects.filter(
            event__id=context["event"].id,
            set_name="Soundcheck",
        ).select_related("song")

        onstage = (
            models.Onstage.objects.filter(event=context["event"].id)
            .select_related("relation")
            .prefetch_related("band")
            .order_by("band_id", "relation__name")
        )

        context["onstage"] = onstage.filter(band=None)

        context["bands"] = onstage.exclude(band=None)

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
            .values("category", "album")
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

    date = datetime.datetime.today()

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["title"] = "Events"

        try:
            context["year"] = self.kwargs["year"]
        except KeyError:
            context["year"] = self.date.year

        context["years"] = list(range(1965, self.date.year + 1))

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

        context["counts"] = context["setlists"].values("public", "private")[0]

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
                    year=TruncYear("event__date"),
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
                "value": f"{r.get_date()} - {r.venue}",
                "date": r.get_date(),
            }

            results.append(result)

        data = json.dumps(results)

    return HttpResponse(data, "application/json")


class EventSearch(TemplateView):
    template_name = "databruce/search/search.html"
    form = forms.EventSearch
    queryset = (
        models.Events.objects.all()
        .select_related(
            "venue",
            "venue__city",
            "venue__city__country",
            "artist",
            "tour",
        )
        .prefetch_related("venue__city__state")
    )

    def get(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        form = self.form(request.GET)

        if form.is_valid():
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

            if result.count() == 1:
                return redirect(f"/events/{result.first().id}")

            return render(
                request,
                self.template_name,
                context={"events": result},
            )
        return None


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
            # slots = models.Setlists.objects.filter(
            #     event__tour__id=context["tour"].id,
            #     set_name__in=VALID_SET_NAMES,
            #     position__isnull=False,
            # )

            context["slots"] = (
                models.Setlists.objects.filter(
                    event__tour__id=context["tour"].id,
                    set_name__in=VALID_SET_NAMES,
                    position__isnull=False,
                )
                .exclude(position=None)
                .values("event__id")
                .annotate(
                    show_opener_id=Min(
                        Case(
                            When(
                                position="Show Opener",
                                then=F("song"),
                            ),
                        ),
                    ),
                    show_opener_name=Min(
                        Case(
                            When(
                                position="Show Opener",
                                then=F("song__name"),
                            ),
                        ),
                    ),
                    set_1_closer_id=Min(
                        Case(
                            When(
                                position="Set 1 Closer",
                                then=F("song"),
                            ),
                        ),
                    ),
                    set_1_closer_name=Min(
                        Case(
                            When(
                                position="Set 1 Closer",
                                then=F("song__name"),
                            ),
                        ),
                    ),
                    set_2_opener_id=Min(
                        Case(
                            When(
                                position="Set 2 Opener",
                                then=F("song"),
                            ),
                        ),
                    ),
                    set_2_opener_name=Min(
                        Case(
                            When(
                                position="Set 2 Opener",
                                then=F("song__name"),
                            ),
                        ),
                    ),
                    main_set_closer_id=Min(
                        Case(
                            When(
                                position="Main Set Closer",
                                then=F("song"),
                            ),
                        ),
                    ),
                    main_set_closer_name=Min(
                        Case(
                            When(
                                position="Main Set Closer",
                                then=F("song__name"),
                            ),
                        ),
                    ),
                    encore_opener_id=Min(
                        Case(
                            When(
                                position="Encore Opener",
                                then=F("song"),
                            ),
                        ),
                    ),
                    encore_opener_name=Min(
                        Case(
                            When(
                                position="Encore Opener",
                                then=F("song__name"),
                            ),
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
                .order_by("event")
            )

            print(context["slots"])

            context["sets"] = context["slots"].values_list("position")

        return context


class Contact(View):
    form_class = forms.ContactForm
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
    form_class = forms.SetlistNoteSearch

    def get(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        return render(
            request,
            "databruce/search/notes_search.html",
            context={"form": self.form_class()},
        )

    def post(self, request: HttpRequest):
        form = self.form_class(request.POST)

        if form.is_valid():
            results = models.Setlists.objects.filter(
                note__search=form.cleaned_data["query"],
            ).select_related(
                "song",
                "event",
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

    start_date = datetime.date(year=1965, month=1, day=1)
    end_date = datetime.datetime.today().date()

    def get(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        form = self.form_class()

        setlist_formset = self.formset_class(
            {"form-TOTAL_FORMS": "1", "form-INITIAL_FORMS": "1"},
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
        if choice == "not":
            return ~field_filter

        return field_filter

    def get(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        event_form = self.form_class(request.GET)
        formset = self.formset_class(data=request.GET)
        queryset = models.Songspagenew.objects.all().select_related("event")

        song_results = []
        results = []
        event_results = []

        setlist_event_filter = Q()
        event_filter = Q()

        if event_form.is_valid():
            data = event_form.cleaned_data

            lookups = {
                "first_date": Q(date__gte=data["first_date"]["id"]),
                "last_date": Q(date__lte=data["last_date"]["id"]),
                "month": Q(date__month=data["month"]["id"]),
                "day": Q(date__day=data["day"]["id"]),
                "city": Q(venue__city__id=data["city"]["id"]),
                "state": Q(venue__state__id=data["state"]["id"]),
                "country": Q(venue__country__id=data["country"]["id"]),
                "tour": Q(tour__id=data["tour"]["id"]),
                "musician": Q(relation__id=data["musician"]["id"]),
                "band": Q(band__id=data["band"]["id"]),
                "day_of_week": Q(date__week_day=data["day_of_week"]["id"]),
            }

            fields = [
                x
                for x in event_form.changed_data
                if "_choice" not in x and x != "conjunction"
            ]

            for field in fields:
                try:  # fields that have an optional "choice" qualifier
                    choice = data[f"{field}_choice"]

                    filter_to_add = self.check_field_choice(
                        choice,
                        lookups[field],
                    )

                    if field in ("musician", "band"):
                        filter = self.check_field_choice(choice, lookups[field])
                        events = models.Onstage.objects.filter(filter).values(
                            "event_id",
                        )
                        filter_to_add = Q(id__in=events)

                    event_filter &= self.check_field_choice(choice, filter_to_add)

                    result = f"{event_form.fields[field].label}: ({choice}) {data[field]['value']}"

                except KeyError:
                    event_filter &= lookups[field]
                    result = f"{event_form.fields[field].label}: {data[field]['value']}"

                results.append(result)

        if formset.is_valid():
            for form in formset.cleaned_data:
                try:
                    song1 = models.Songs.objects.get(id=form["song1"]).name

                    setlist_filter = Q(set_name__in=VALID_SET_NAMES)

                    match form["position"]:
                        case "Followed By":
                            song2 = models.Songs.objects.get(id=form["song2"]).name

                            setlist_filter &= Q(song=form["song1"])
                            setlist_filter &= self.check_field_choice(
                                form["choice"],
                                Q(next=form["song2"]),
                            )

                            song_results.append(
                                f"{song1} ({form['choice']} followed by) {song2}",
                            )

                        case "Anywhere":
                            song_events = queryset.filter(
                                song=form["song1"],
                                set_name__in=VALID_SET_NAMES,
                            ).select_related("event")

                            setlist_filter &= self.check_field_choice(
                                form["choice"],
                                Q(event__id__in=song_events.values("event__id")),
                            )

                            song_results.append(
                                f"{song1} ({form['choice']} anywhere)",
                            )
                        case _:
                            # all others except anywhere and followed by
                            setlist_filter &= Q(song=form["song1"])
                            setlist_filter &= self.check_field_choice(
                                form["choice"],
                                Q(position=form["position"]),
                            )

                            song_results.append(
                                f"{song1} ({form['choice']} {form['position']})",
                            )

                    qs = queryset.filter(
                        setlist_filter,
                    )

                    event_results.append(list(qs.values_list("event__id", flat=True)))

                    match data["conjunction"]:
                        case "or":
                            setlist_event_filter.add(
                                Q(id__in=list(set.union(*map(set, event_results)))),
                                Q.OR,
                            )

                        case "and":
                            setlist_event_filter.add(
                                Q(
                                    id__in=list(
                                        set.intersection(*map(set, event_results)),
                                    ),
                                ),
                                Q.AND,
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
                "venue__city__country",
                "tour",
            )
            .prefetch_related(
                "venue__city__state",
                "venue__city__state__country",
            )
            .order_by("id")
        )

        # Used to set opengraph description text
        description = ""
        description += ", ".join(results)
        description += f"Songs: {', '.join(song_results)}"

        return render(
            request=request,
            template_name=self.template_name,
            context={
                "events": result.order_by("id"),
                "title": "Advanced Search",
                "description": description,
                "results": results,
                "song_results": song_results,
                "form": event_form,
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
                "event__venue__city",
                "event__venue__city__country",
            )
            .prefetch_related(
                "event__venue__city__state",
                "event__venue__city__state__country",
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
