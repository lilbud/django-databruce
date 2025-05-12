import datetime
from typing import Any

from django.db.models import (
    Case,
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

    def get_context_data(self, **kwargs):
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
            date__gte=self.date,
        ).order_by("id")[:5]

        return context


class Songs(TemplateView):
    template_name = "databruce/songs/songs.html"
    queryset = (
        models.Songs.objects.all().prefetch_related("first", "last").order_by("name")
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["songs"] = self.queryset
        return context


class EventDetail(TemplateView):
    template_name = "databruce/events/detail.html"
    queryset = models.Events.objects.all().select_related(
        "venue",
        "artist",
        "tour",
        "venue__city",
        "venue__state",
        "venue__country",
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.event = get_object_or_404(models.Events, id=self.kwargs["event"])
        context["event"] = self.queryset.filter(id=self.event.id).first()

        context["setlist"] = (
            models.Setlists.objects.filter(event__id=self.event.id)
            .annotate(
                separator=Case(When(segue=True, then=Value(">")), default=Value(",")),
            )
            .select_related("song")
            .order_by("song_num")
        )

        context["onstage"] = (
            models.Onstage.objects.filter(event__id=self.event.id)
            .select_related("relation")
            .order_by("band_id", "relation__name")
        )

        context["guests"] = context["onstage"].filter(guest=True)

        context["notes"] = models.SetlistNotes.objects.filter(
            event__id=self.event.id,
        ).order_by("num")
        context["footnotes"] = context["notes"].distinct("num")

        context["prev_event"] = self.queryset.filter(id__lt=self.event.id).last()
        context["next_event"] = self.queryset.filter(id__gt=self.event.id).first()

        if not context["prev_event"]:
            context["prev_event"] = self.queryset.last()

        if not context["next_event"]:
            context["next_event"] = self.queryset.first()

        return context


class Events(TemplateView):
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            self.year = self.kwargs["year"]
        except KeyError:
            self.year = self.date.year

        context["year"] = self.year
        context["years"] = list(range(1965, self.year + 1))
        context["event_info"] = self.queryset.filter(id__startswith=self.year)

        return context


class Venues(TemplateView):
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["venues"] = self.queryset
        return context


class VenueDetail(TemplateView):
    template_name = "databruce/locations/venues/detail.html"

    def get_context_data(self, **kwargs):
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

    def get_context_data(self, **kwargs: dict):
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

        context["first_release"] = (
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

    def post(self, request, *args, **kwargs):
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


class Tours(TemplateView):
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tours"] = self.queryset

        return context


class TourDetail(TemplateView):
    template_name = "databruce/tours/detail.html"

    def get_context_data(self, **kwargs):
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


class AdvancedSearch(View):
    form_class = forms.AdvancedEventSearch
    initial = {"form-TOTAL_FORMS": "1", "form-INITIAL_FORMS": "0"}
    formset_class = formset_factory(forms.SetlistSearch)

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial={"month": "5", "day": "10"})
        setlist_formset = self.formset_class(self.initial)

        return render(
            request,
            "databruce/search/advanced_search.html",
            context={"form": form, "formset": setlist_formset},
        )

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, initial={"month": "5", "day": "10"})
        formset = self.formset_class(data=request.POST)

        if form.is_valid():
            print(form.cleaned_data)
            event_filter = (
                Q(date__gte=form.cleaned_data["first_date"])
                & Q(date__lte=form.cleaned_data["last_date"])
                & Q(date__month__in=form.cleaned_data["month"])
                & Q(date__day__in=form.cleaned_data["day"])
                & Q(venue__city__id__in=form.cleaned_data["city"])
                & Q(venue__country__id__in=form.cleaned_data["country"])
            )

            onstage_band_filter = Q(band__in=form.cleaned_data["band"])
            onstage_relation_filter = Q(relation__in=form.cleaned_data["musician"])

            if len(form.cleaned_data["day_of_week"]) == 1:
                day_filter = Q(
                    date__week_day__in=form.cleaned_data["day_of_week"],
                )

                if int(form.cleaned_data["day_of_week"][0]) > 7:
                    day_filter = (
                        ~Q(
                            date__week_day__in=[
                                int(form.cleaned_data["day_of_week"][0]) - 7,
                            ],
                        ),
                    )

                event_filter.add(
                    day_filter,
                    Q.AND,
                )

            events = (
                models.Onstage.objects.filter(
                    onstage_relation_filter & onstage_band_filter,
                )
                .distinct("event")
                .values_list("event")
            )

            event_filter.add(Q(id__in=events), Q.AND)

        results = []
        event_results = []

        if formset.is_valid():
            for form in formset.cleaned_data:
                try:
                    song = models.Songs.objects.get(id=form["song1"]).name

                    if form["position"] != "Followed By":
                        setlist_filter = Q(current__song__id=form["song1"])

                        if form["position"] != "Anywhere":
                            position_filter = Q(current__position=form["position"])

                        if form["choice"] == "not":
                            position_filter = ~Q(current__position=form["position"])

                        setlist_filter.add(position_filter, Q.AND)

                        qs = models.SongsPage.objects.filter(
                            setlist_filter,
                            current__set_name__in=[
                                "Show",
                                "Set 1",
                                "Set 2",
                                "Encore",
                                "Pre-Show",
                                "Post-Show",
                            ],
                        )
                        events_list = qs.values_list("current__event", flat=True)
                        results.append(
                            f"Song: {song} ({form['choice']} {form['position']})",
                        )
                    else:
                        song2 = models.Songs.objects.get(id=form["song2"]).name

                        setlist_filter = Q(current__song__id=form["song1"])

                        if form["choice"] == "not":
                            setlist_filter.add(~Q(next__song__id=form["song2"]), Q.AND)

                        qs = models.SongsPage.objects.filter(
                            setlist_filter,
                            current__set_name__in=[
                                "Show",
                                "Set 1",
                                "Set 2",
                                "Encore",
                                "Pre-Show",
                                "Post-Show",
                            ],
                        )
                        events_list = qs.values_list("current__event", flat=True)
                        results.append(
                            f"Song: {song} ({form['choice']} followed by) {song2}",
                        )

                    event_results.append(list(events_list))

                # ran into an issue where if the setlist form was empty, the page would error
                # this fixes it, not sure if it's correct
                except ValueError:
                    break
                else:
                    # adds the current list of events on each loop of the form
                    # only adds those that intersect with the previous loops results
                    event_filter.add(
                        Q(id__in=list(set.intersection(*map(set, event_results)))),
                        Q.AND,
                    )

        result = (
            models.Events.objects.filter(
                event_filter,
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
            context={"events": result.order_by("id"), "results": results},
        )


class Relations(TemplateView):
    template_name = "databruce/relations/relations.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["relations"] = models.Relations.objects.all().select_related(
            "first",
            "last",
        )
        return context


class Bands(TemplateView):
    template_name = "databruce/bands/bands.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["bands"] = (
            models.Bands.objects.filter()
            .select_related("first", "last")
            .order_by("name")
        )
        return context


class RelationDetail(TemplateView):
    template_name = "databruce/relations/detail.html"

    def get_context_data(self, **kwargs):
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
                "venue__city__state__country",
                "venue__city__country",
                "tour",
            )
            .order_by("id")
        )

        return context


class BandDetail(TemplateView):
    template_name = "databruce/bands/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["info"] = get_object_or_404(models.Bands, id=self.kwargs["id"])

        context["members"] = (
            models.Onstage.objects.filter(band=self.kwargs["id"])
            .select_related("relation", "relation__first", "relation__last")
            .order_by("relation")
        )

        context["events"] = (
            models.Events.objects.filter(id__in=context["members"].values_list("event"))
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


class Releases(TemplateView):
    template_name = "databruce/releases/releases.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["releases"] = models.Releases.objects.all().order_by("date")
        return context


class ReleaseDetail(TemplateView):
    template_name = "databruce/releases/detail.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
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


def cities(request: HttpRequest):
    cities = (
        models.Cities.objects.all()
        .prefetch_related("state")
        .select_related("country", "first", "last")
        .order_by("name")
    )

    return render(
        request,
        "databruce/locations/cities/cities.html",
        context={"cities": cities},
    )


def city_details(request: HttpRequest, id: int):
    city_info = (
        models.Cities.objects.filter(id=id)
        .select_related(
            "country",
            "first",
            "last",
        )
        .first()
    )

    events = (
        models.Events.objects.filter(venue__city=id)
        .select_related("venue__city", "venue__state", "artist", "tour")
        .order_by("id")
    )

    songs = (
        models.Setlists.objects.filter(
            event__venue__city__id=id,
            set_name__in=["Show", "Set 1", "Set 2", "Pre-Show", "Encore", "Post-Show"],
        )
        .order_by("song", "event")
        .select_related("song", "event")
    )

    venues = models.Venues.objects.filter(city__id=id)

    return render(
        request,
        "databruce/locations/cities/detail.html",
        context={"info": city_info, "events": events, "songs": songs, "venues": venues},
    )


def states(request: HttpRequest):
    states = (
        models.States.objects.all()
        .select_related("country", "first", "last")
        .order_by("name")
    )

    return render(
        request,
        "databruce/locations/states/states.html",
        context={"states": states},
    )


def state_details(request: HttpRequest, id: int):
    state_info = (
        models.States.objects.filter(id=id)
        .select_related(
            "country",
            "first__venue",
            "last__venue",
        )
        .first()
    )

    events = models.Events.objects.filter(venue__state=id).select_related(
        "venue__city",
        "venue__country",
        "artist",
        "tour",
    )

    songs = (
        models.Setlists.objects.filter(
            event__venue__state__id=id,
            set_name__in=["Show", "Set 1", "Set 2", "Pre-Show", "Encore", "Post-Show"],
        )
        .order_by("song", "event")
        .select_related("song", "event")
    )

    venues = models.Venues.objects.filter(state__id=id)

    return render(
        request,
        "databruce/locations/states/detail.html",
        context={
            "info": state_info,
            "events": events,
            "songs": songs,
            "venues": venues,
        },
    )


def countries(request: HttpRequest):
    countries = (
        models.Countries.objects.all().select_related("first", "last").order_by("name")
    )

    return render(
        request,
        "databruce/locations/countries/countries.html",
        context={"countries": countries},
    )


def country_details(request: HttpRequest, id: int):
    country_info = (
        models.Countries.objects.filter(id=id)
        .select_related(
            "first",
            "last",
        )
        .first()
    )

    events = (
        models.Events.objects.filter(venue__country=id)
        .select_related("venue__state", "artist", "venue__city")
        .order_by("id")
    )

    songs = (
        models.Setlists.objects.filter(
            event__venue__country__id=id,
            set_name__in=["Show", "Set 1", "Set 2", "Pre-Show", "Encore", "Post-Show"],
        )
        .order_by("song", "event")
        .select_related("song", "event")
    )

    venues = models.Venues.objects.filter(country__id=id)

    return render(
        request,
        "databruce/locations/countries/detail.html",
        context={
            "info": country_info,
            "events": events,
            "songs": songs,
            "venues": venues,
        },
    )


def event_runs(request: HttpRequest):
    runs = (
        models.Runs.objects.all()
        .select_related("first", "last", "band", "first__venue", "last__venue")
        .order_by("first")
    )

    return render(
        request,
        "databruce/events/runs.html",
        context={"runs": runs},
    )
