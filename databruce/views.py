import datetime
from typing import Any

from django.db.models import (
    Case,
    Count,
    Max,
    Q,
    Value,
    When,
)
from django.forms import formset_factory
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import TemplateView

from . import forms, models


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


class EventDetail(TemplateView):
    template_name = "databruce/events/detail copy.html"
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
        self.event = get_object_or_404(self.queryset, id=self.kwargs["event"])
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
                .values("song__id"),
            )
            .values("category", "album")
            .annotate(num=Count("id"))
            .order_by("-num")
        )

        context["setlist_unique"] = (
            models.Setlists.objects.filter(
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
            .distinct("song__id")
            .select_related("song")
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
            venue__id=self.venue,
        ).select_related("artist", "tour")

        context["venue_info"] = (
            models.Venues.objects.filter(
                id=self.venue,
            )
            .select_related("city", "city__state", "city__country")
            .first()
        )

        context["songs"] = (
            models.Setlists.objects.filter(
                event__venue__id=self.venue,
            )
            .order_by("song", "event")
            .select_related("song", "event")
        )

        return context


class SongDetail(TemplateView):
    template_name = "databruce/songs/detail.html"
    model = models.Songs

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        self.song = get_object_or_404(self.model, id=self.kwargs["id"])
        context["song_info"] = self.song
        context["songs"] = models.SongsPage.objects.filter(
            id=self.song.id,
        ).select_related(
            "prev",
            "prev__song",
            "current__event",
            "current__song",
            "current__event__venue",
            "current__event__venue__city",
            "current__event__venue__city__state",
            "current__event__venue__city__country",
            "current__event__artist",
            "current__event__tour",
            "next",
            "next__song",
        )

        filter = Q(event_certainty__in=["Confirmed", "Probable"])

        if context["song_info"].num_plays_public > 0:
            filter.add(
                Q(
                    id__gt=context["song_info"].first.id,
                ),
                Q.AND,
            )

        context["events"] = models.Events.objects.filter(filter).count()

        context["frequency"] = round(
            ((context["song_info"].num_plays_public / context["events"]) * 100),
            2,
        )

        context["release"] = (
            models.ReleaseTracks.objects.filter(song__id=self.song.id)
            .order_by("release__date")
            .first()
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
                "venue__city__country",
                "venue__state",
                "venue__country",
            )
        )

        context["tour_legs"] = models.TourLegs.objects.filter(
            tour__id=self.tour.id,
        ).order_by(
            "first",
        )

        context["songs"] = (
            models.Setlists.objects.filter(
                event__tour__id=self.tour.id,
                set_name__in=[
                    "Show",
                    "Set 1",
                    "Set 2",
                    "Pre-Show",
                    "Encore",
                    "Post-Show",
                ],
            )
            .order_by("song", "event")
            .select_related("song", "event")
        )

        return context


class SetlistSearch(View):
    form_class = forms.SetlistNoteSearch

    def get(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
        form = self.form_class()

        return render(
            request,
            "databruce/search/notes_search.html",
            context={"form": form},
        )

    def post(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):
        form = self.form_class(request.POST)

        if form.is_valid():
            results = models.SetlistNotes.objects.filter(
                note__iregex=rf"{form.cleaned_data['query']}",
            ).select_related(
                "id",
                "last",
                "id__song",
                "last__artist",
                "last__venue",
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

    def check_field_choice(self, choice: str, filter: Q) -> Q:
        """Every field has a IS/NOT choice on it. Depending on that choice, the filter can be negated or not. This checks for that value and returns the correct filter."""
        if choice == "is":
            return filter

        return ~filter

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

    def post(self, request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]):  # noqa: ARG002
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
            models.Events.objects.filter(id__in=context["bands"].values_list("event"))
            .select_related(
                "venue",
                "artist",
                "venue__city",
                "venue__country",
                "venue__city__state",
                "venue__city__country",
                "tour",
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
            .select_related("relation", "relation__first", "relation__last")
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
                event__venue__city__id=self.city.id,
                set_name__in=[
                    "Show",
                    "Set 1",
                    "Set 2",
                    "Pre-Show",
                    "Encore",
                    "Post-Show",
                ],
            )
            .order_by("song", "event")
            .select_related("song", "event")
        )
        context["events"] = (
            models.Events.objects.filter(venue__city=self.city.id)
            .select_related("venue__city", "venue__state", "artist", "tour")
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
        self.state = get_object_or_404(self.queryset, id=self.kwargs["id"])
        context["info"] = self.state
        context["events"] = models.Events.objects.filter(
            venue__state=self.state.id,
        ).select_related(
            "venue__city",
            "venue__country",
            "artist",
            "tour",
        )

        context["songs"] = (
            models.Setlists.objects.filter(
                event__venue__state__id=self.state.id,
                set_name__in=[
                    "Show",
                    "Set 1",
                    "Set 2",
                    "Pre-Show",
                    "Encore",
                    "Post-Show",
                ],
            )
            .order_by("song", "event")
            .select_related("song", "event")
        )

        context["venues"] = models.Venues.objects.filter(state__id=self.state.id)

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
        self.country = get_object_or_404(self.queryset, id=self.kwargs["id"])
        context["info"] = self.country
        context["events"] = (
            models.Events.objects.filter(venue__country=self.country.id)
            .select_related("venue__state", "artist", "venue__city")
            .order_by("id")
        )
        context["songs"] = (
            models.Setlists.objects.filter(
                event__venue__country__id=self.country.id,
                set_name__in=[
                    "Show",
                    "Set 1",
                    "Set 2",
                    "Pre-Show",
                    "Encore",
                    "Post-Show",
                ],
            )
            .order_by("song", "event")
            .select_related("song", "event")
        )
        context["venues"] = models.Venues.objects.filter(country__id=self.country.id)
        return context


class EventRun(TemplateView):
    template_name = "databruce/events/runs.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["runs"] = (
            models.Runs.objects.all()
            .select_related("first", "last", "band", "first__venue", "last__venue")
            .order_by("first")
        )
        return context


class RunDetail(TemplateView):
    template_name = "databruce/events/run_detail.html"
    queryset = (
        models.Runs.objects.all()
        .select_related("first", "last", "band", "venue")
        .order_by("first")
    )

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        self.run = get_object_or_404(self.queryset, id=self.kwargs["id"])
        context["info"] = self.run
        context["events"] = models.Events.objects.filter(run__id=self.run.id).order_by(
            "id",
        )
        context["songs"] = (
            models.Setlists.objects.filter(
                event__run__id=self.run.id,
                set_name__in=[
                    "Show",
                    "Set 1",
                    "Set 2",
                    "Pre-Show",
                    "Encore",
                    "Post-Show",
                ],
            )
            .order_by("song")
            .select_related("song")
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
                event__leg__id=self.leg.id,
                set_name__in=[
                    "Show",
                    "Set 1",
                    "Set 2",
                    "Pre-Show",
                    "Encore",
                    "Post-Show",
                ],
            )
            .order_by("song")
            .select_related("song")
        )
        context["venues"] = models.Venues.objects.filter(
            id__in=context["events"].values_list("venue"),
        )

        return context
