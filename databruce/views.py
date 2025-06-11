import datetime
import logging
from typing import Any

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.models import Group, User
from django.contrib.auth.tokens import (
    PasswordResetTokenGenerator,
    default_token_generator,
)
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.mail import EmailMultiAlternatives
from django.db.models import Case, Count, F, Max, Q, Sum, Value, When
from django.db.models.functions import TruncYear
from django.forms import formset_factory
from django.http import HttpRequest
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

from . import forms, models

UserModel = get_user_model()
logger = logging.getLogger("django.contrib.auth")
INTERNAL_RESET_SESSION_TOKEN = "_password_reset_token"


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
    date = datetime.datetime.today()

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["date"] = self.date
        context["events"] = self.queryset.filter(
            date__month=self.date.month,
            date__day=self.date.day,
        ).order_by("-id")[:5]

        context["recent"] = self.queryset.filter(
            date__lte=self.date,
        ).order_by("-id")[:5]

        context["upcoming"] = self.queryset.filter(
            date__gt=self.date,
        ).order_by("id")[:5]

        context["latest_show"] = (
            models.Setlists.objects.filter(event__id=context["recent"].first().id)
            .annotate(
                separator=Case(When(segue=True, then=Value(">")), default=Value(",")),
            )
            .select_related("song")
            .order_by("song_num")
        )

        return context


class Song(TemplateView):
    template_name = "databruce/songs/songs.html"
    queryset = (
        models.Songs.objects.all().prefetch_related("first", "last").order_by("name")
    )

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["songs"] = self.queryset
        return context


class Users(TemplateView):
    template_name = "users/users.html"

    def get_context_data(self, **kwargs: dict) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["users"] = models.AuthUser.objects.all()

        return context


class UserProfile(TemplateView):
    template_name = "users/profile.html"

    def get_context_data(self, **kwargs: dict) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["user_info"] = models.AuthUser.objects.get(
            username__iexact=self.kwargs["username"],
        )
        context["user_shows"] = models.UserAttendedShows.objects.filter(
            user__username__iexact=self.kwargs["username"],
        ).select_related("event")

        context["user_songs"] = (
            models.Setlists.objects.filter(
                event__id__in=context["user_shows"].values_list("event__id"),
                set_name__in=[
                    "Show",
                    "Set 1",
                    "Set 2",
                    "Encore",
                    "Pre-Show",
                    "Post-Show",
                ],
            )
            .select_related("song")
            .order_by("song__id")
        )

        return context


@method_decorator(
    login_not_required,
    name="dispatch",
)
class SignUp(TemplateView):
    template_name = "users/signup.html"
    email_template_name = "users/signup_email.html"
    subject_template_name = "users/signup_confirm_subject.txt"
    token_generator = PasswordResetTokenGenerator()
    form_class = forms.UserForm
    extra_email_context = None
    from_email = None
    html_email_template_name = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form_class
        return context

    def post(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):
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

            self.send_mail(context=context, from_email=None, to_email=user.email)

            return redirect(reverse("login"))

        return render(request, template_name=self.template_name, context={"form": form})

    def send_mail(
        self,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        subject_template_name = "users/signup_confirm_subject.txt"
        email_template_name = "users/signup_email.html"

        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = "".join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
        if html_email_template_name is not None:
            html_email = loader.render_to_string(html_email_template_name, context)
            email_message.attach_alternative(html_email, "text/html")

        try:
            email_message.send()
        except Exception:
            logger.exception(
                "Failed to send activation email to %s",
                context["user"].pk,
            )


class SignUpConfirm(TemplateView):
    template_name = "users/signup_done.html"
    reset_url_token = "activate"
    token_generator = default_token_generator

    def get_user(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            user = UserModel._default_manager.get(pk=uid)
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
                session_token = self.request.session.get(INTERNAL_RESET_SESSION_TOKEN)
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
                    self.request.session[INTERNAL_RESET_SESSION_TOKEN] = token

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
        return super().get_context_data(**kwargs)


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
        )
        .prefetch_related("tour", "venue__state")
    )

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        self.event = get_object_or_404(self.queryset, id=self.kwargs["id"])
        context["event"] = self.queryset.filter(id=self.event.id).first()

        context["setlist"] = (
            models.Setlists.objects.filter(event__id=self.event.id)
            .annotate(
                separator=Case(When(segue=True, then=Value(">")), default=Value(",")),
            )
            .select_related("song")
            .order_by("song_num")
        )

        self.onstage = (
            models.Onstage.objects.filter(event__id=self.event.id)
            .exclude(relation__id=255)
            .select_related("relation")
            .order_by("band_id", "relation__name")
        )

        context["onstage"] = self.onstage.filter(guest=False)

        context["guests"] = self.onstage.filter(guest=True)

        context["notes"] = models.SetlistNotes.objects.filter(
            event__id=self.event.id,
        ).order_by("num")

        context["prev_event"] = self.queryset.filter(id__lt=self.event.id).last()
        context["next_event"] = self.queryset.filter(id__gt=self.event.id).first()

        if not context["prev_event"]:
            context["prev_event"] = self.queryset.last()

        if not context["next_event"]:
            context["next_event"] = self.queryset.first()

        context["official"] = (
            models.ReleaseTracks.objects.filter(
                event__id=self.event.id,
            )
            .distinct("release__id")
            .select_related("release")
            .order_by("release__id")
        )

        context["bootleg"] = models.Bootlegs.objects.filter(event__id=self.event.id)
        context["archive"] = models.ArchiveLinks.objects.filter(
            event__id=self.event.id,
        ).distinct("url")

        print(context["archive"])

        context["nugs"] = models.NugsReleases.objects.filter(
            event__id=self.event.id,
        ).first()

        if self.request.user.is_authenticated:
            context["user_shows"] = models.UserAttendedShows.objects.filter(
                user=self.request.user.id,
                event=self.event.id,
            ).values_list("event__id", flat=True)

            context["user_count"] = (
                models.UserAttendedShows.objects.filter(
                    event=self.event.id,
                )
                .distinct("user__id")
                .count()
            )

        if self.event.tour.id not in [23, 43]:
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
                event__id=self.event.id,
                set_name__in=[
                    "Show",
                    "Set 1",
                    "Set 2",
                    "Pre-Show",
                    "Encore",
                    "Post-Show",
                ],
            )

            context["album_max"] = context["album_breakdown"].aggregate(max=Max("num"))

        return context


class Event(TemplateView):
    template_name = "databruce/events/events.html"
    queryset = models.Events.objects.all().select_related(
        "venue",
        "tour",
        "artist",
        "venue__city",
        "venue__city__state",
        "venue__city__country",
        "venue__state",
        "venue__country",
    )
    date = datetime.datetime.today()

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)

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
            "city__country",
            "state",
            "country",
            "first",
            "last",
        )
    )

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["venues"] = self.queryset
        return context


class VenueDetail(TemplateView):
    template_name = "databruce/locations/venues/detail.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        self.venue = self.kwargs["id"]

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


class SongDetail(TemplateView):
    template_name = "databruce/songs/detail.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)

        self.song = (
            models.Songs.objects.filter(id=self.kwargs["id"])
            .prefetch_related(
                "album",
            )
            .first()
        )

        context["song_info"] = self.song

        context["songs"] = (
            models.SongsPage.objects.filter(
                id=self.kwargs["id"],
            )
            .select_related(
                "prev",
                "prev__song",
                "current__event",
                "current__song",
                "current__event__venue",
                "current__event__artist",
                "current__event__tour",
                "next",
                "next__song",
            )
            .prefetch_related(
                "current__event__venue__city",
                "current__event__venue__city__state",
                "current__event__venue__city__state__country",
                "current__event__venue__city__country",
            )
        )

        context["snippets"] = (
            models.Snippets.objects.filter(
                snippet=self.kwargs["id"],
            )
            .select_related("setlist", "event", "snippet", "setlist__song")
            .order_by("event", "position")
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

        context["year_stats"] = (
            models.Setlists.objects.filter(song_id=self.kwargs["id"])
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
            .order_by("year")  # 4. Order the results by year
        )

        if context["song_info"].num_plays_public > 0:
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

    def post(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        form = self.form(request.POST)

        if form.is_valid():
            result = self.queryset.filter(
                date=form.cleaned_data["date"],
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

        return context


class TourDetail(TemplateView):
    template_name = "databruce/tours/detail.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        self.tour = models.Tours.objects.get(id=self.kwargs["id"])
        context["tour"] = self.tour
        context["events"] = (
            models.Events.objects.filter(tour=self.tour.id)
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

        context["setlists"] = (
            models.SetlistsBySetAndDate.objects.filter(
                event__tour__id=self.tour.id,
            )
            .order_by("set_order")
            .select_related("event")
        )

        context["tour_legs"] = (
            models.TourLegs.objects.filter(
                tour__id=self.tour.id,
            )
            .order_by(
                "first",
            )
            .select_related("first", "last")
        )

        context["songs"] = (
            models.Setlists.objects.filter(
                event__tour__id=self.tour.id,
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

    def check_field_choice(self, choice: str, field_filter: Q) -> Q:
        """Every field has a IS/NOT choice on it. Depending on that choice, the filter can be negated or not. This checks for that value and returns the correct filter."""
        if choice == "is":
            return field_filter

        return ~field_filter

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

    def post(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002, C901, PLR0912, PLR0915
        event_form = self.form_class(request.POST)
        formset = self.formset_class(data=request.POST)
        results = []

        if event_form.is_valid():
            form = event_form
            event_filter = Q(date__gte=event_form.cleaned_data["first_date"]) & Q(
                date__lte=event_form.cleaned_data["last_date"],
            )

            if event_form.cleaned_data["month"]:
                event_filter.add(
                    self.check_field_choice(
                        event_form.cleaned_data["month_choice"],
                        Q(date__month=event_form.cleaned_data["month"]),
                    ),
                    Q.AND,
                )

            if event_form.cleaned_data["day"]:
                event_filter.add(
                    self.check_field_choice(
                        event_form.cleaned_data["day_choice"],
                        Q(date__day=event_form.cleaned_data["day"]),
                    ),
                    Q.AND,
                )

            if event_form.cleaned_data["city"]:
                event_filter.add(
                    self.check_field_choice(
                        event_form.cleaned_data["city_choice"],
                        Q(venue__city__id=event_form.cleaned_data["city"]),
                    ),
                    Q.AND,
                )

            if event_form.cleaned_data["state"]:
                event_filter.add(
                    self.check_field_choice(
                        event_form.cleaned_data["state_choice"],
                        Q(venue__state__id=event_form.cleaned_data["state"]),
                    ),
                    Q.AND,
                )

            if event_form.cleaned_data["country"]:
                event_filter.add(
                    self.check_field_choice(
                        event_form.cleaned_data["country_choice"],
                        Q(venue__country__id=event_form.cleaned_data["country"]),
                    ),
                    Q.AND,
                )

            if event_form.cleaned_data["tour"]:
                event_filter.add(
                    self.check_field_choice(
                        event_form.cleaned_data["tour_choice"],
                        Q(tour__id=event_form.cleaned_data["tour"]),
                    ),
                    Q.AND,
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

            if event_form.cleaned_data["band"]:
                filter = self.check_field_choice(
                    event_form.cleaned_data["band_choice"],
                    Q(band__id=event_form.cleaned_data["band"]),
                )

                events = models.Onstage.objects.filter(
                    filter,
                ).values_list("event")

                event_filter.add(Q(id__in=events), Q.AND)

            if event_form.cleaned_data["day_of_week"]:
                event_filter.add(
                    self.check_field_choice(
                        event_form.cleaned_data["dow_choice"],
                        Q(date__week_day=event_form.cleaned_data["day_of_week"]),
                    ),
                    Q.AND,
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

                        results.append(
                            f"{song1} ({form['choice']} followed by) {song2}",
                        )

                    elif form["position"] != "Anywhere":
                        # all others except anywhere and followed by
                        position_filter = Q(current__position=form["position"])

                        if form["choice"] == "is":
                            setlist_filter.add(position_filter, Q.AND)
                        else:
                            setlist_filter.add(~position_filter, Q.AND)

                        results.append(
                            f"{song1} ({form['choice']} {form['position']})",
                        )
                    else:
                        results.append(
                            f"{song1} ({form['choice']} anywhere)",
                        )

                    qs = models.SongsPage.objects.filter(
                        setlist_filter,
                    )

                    events_list = qs.values_list("current__event", flat=True)

                    event_results.append(list(events_list))

                    if event_form.cleaned_data["conjunction"] == "and":
                        setlist_event_filter.add(
                            Q(id__in=list(set.intersection(*map(set, event_results)))),
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

        return render(
            request,
            "databruce/search/advanced_search_results.html",
            context={
                "events": result.order_by("id"),
                "form": event_form,
                "results": results,
            },
        )


class Relation(TemplateView):
    template_name = "databruce/relations/relations.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        context["relations"] = models.Relations.objects.all().select_related(
            "first",
            "last",
        )
        return context


class Band(TemplateView):
    template_name = "databruce/bands/bands.html"

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
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
        return context


class ReleaseDetail(TemplateView):
    template_name = "databruce/releases/detail.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["info"] = get_object_or_404(models.Releases, id=self.kwargs["id"])

        context["tracks"] = (
            models.ReleaseTracks.objects.filter(release=self.kwargs["id"])
            .order_by(
                "track",
            )
            .prefetch_related("song__first", "song__last")
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
        context["cities"] = self.queryset
        return context


class CityDetail(TemplateView):
    template_name = "databruce/locations/cities/detail.html"
    queryset = models.Cities.objects.all().select_related("country", "first", "last")

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        self.city = get_object_or_404(self.queryset, id=self.kwargs["id"])
        context["info"] = self.city
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
                "venue__city__state",
                "venue__city__country",
                "artist",
                "tour",
            )
            .order_by("id")
        )
        context["venues"] = models.Venues.objects.filter(city__id=self.city.id)

        return context


class State(TemplateView):
    template_name = "databruce/locations/states/states.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
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

        context["events"] = (
            models.Events.objects.filter(venue__country=self.kwargs["id"])
            .select_related("venue__state", "artist", "venue__city")
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
        context["events"] = models.Events.objects.filter(leg__id=self.leg.id).order_by(
            "id",
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

        context["bootlegs"] = (
            models.Bootlegs.objects.all()
            .prefetch_related(
                "archive",
            )
            .select_related("event")
            .order_by("event")
        )

        return context
