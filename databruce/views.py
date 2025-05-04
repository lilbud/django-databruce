import datetime

from django.db.models import (
    Case,
    Q,
    Value,
    When,
)
from django.http import HttpRequest
from django.shortcuts import redirect, render

from . import forms, models

DATE = datetime.datetime.today()


def index(request: HttpRequest):
    events = (
        models.Events.objects.filter(
            date__month=DATE.month,
            date__day=DATE.day,
        )
        .select_related(
            "artist",
            "venue",
            "venue__city",
            "venue__state",
            "venue__country",
        )
        .order_by("-id")
    )[:10]

    recent_events = (
        models.Events.objects.filter(date__lte=DATE)
        .order_by("-date")
        .select_related(
            "artist",
            "venue",
            "venue__city",
            "venue__state",
            "venue__country",
        )
    )[:10]

    upcoming_events = (
        models.Events.objects.filter(date__gte=DATE)
        .order_by("date")
        .select_related(
            "artist",
            "venue",
            "venue__city",
            "venue__state",
            "venue__country",
        )
    )[:10]

    return render(
        request,
        "databruce/index.html",
        {
            "events": events,
            "recent": recent_events,
            "date": DATE,
            "upcoming": upcoming_events,
        },
    )


def test(request: HttpRequest):
    return render(request, "databruce/test.html")


def songs(request: HttpRequest):
    songs = (
        models.Songs.objects.all()
        .filter(Q(num_plays_public__gte=1) | Q(num_plays_snippet__gte=1))
        .select_related("first", "last")
        .order_by("name")
    )

    context = {
        "songs": songs,
    }

    return render(request, "databruce/songs/songs.html", context)


def event_details(request: HttpRequest, event: str):
    event_info = models.Events.objects.filter(id=event).first()

    setlist = (
        models.Setlists.objects.filter(event__id=event)
        .annotate(separator=Case(When(segue=True, then=Value(">")), default=Value(",")))
        .select_related("song")
        .order_by("event", "song_num")
    )

    on_stage = (
        models.Onstage.objects.filter(event__id=event)
        .select_related("relation")
        .order_by("band_id", "relation__name")
    )

    notes = models.SetlistNotes.objects.filter(event__id=event).order_by("num")
    footnotes = notes.distinct("num")

    try:
        prev_event = models.Events.objects.filter(id__lt=event).order_by("id").last()
    except AttributeError:  # if this is the first event, loop to most recent
        prev_event = models.Events.objects.order_by("id").last()

    try:
        next_event = models.Events.objects.filter(id__gt=event).order_by("id").first()
    except AttributeError:  # if this is the most recent event, loop to first event
        next_event = models.Events.objects.order_by("id").first()

    context = {
        "event": event_info,
        "eventid": event,
        "setlist": setlist,
        "notes": notes,
        "footnotes": footnotes,
        "onstage": on_stage,
        "last_event": prev_event,
        "next_event": next_event,
    }

    return render(request, "databruce/events/event_details.html", context)


def events(request: HttpRequest, year: int = DATE.year):
    years = list(range(1965, DATE.year + 1))

    event_info = (
        models.Events.objects.filter(id__startswith=year)
        .select_related(
            "venue",
            "tour",
            "artist",
            "venue__city",
            "venue__state",
            "venue__country",
        )
        .distinct("id")
        .order_by("id")
    )

    print(len(event_info))

    context = {
        "year": year,
        "years": years,
        "event_info": event_info,
    }

    return render(request, "databruce/events/events.html", context)


def venues(request: HttpRequest):
    venues = (
        models.Venues.objects.all()
        .filter(Q(name__isnull=False) & Q(num_events__gte=1))
        .order_by("name")
        .select_related(
            "first",
            "last",
            "city",
            "city__state",
            "city__country",
            "state",
            "state__country",
            "country",
        )
    )

    context = {"venues": venues}
    return render(request, "databruce/locations/venues/venues.html", context)


def venue(request: HttpRequest, id: int):  # noqa: A002
    events = models.Events.objects.filter(venue__id=id)

    venue_info = models.Venues.objects.get(id=id)

    songs = (
        models.Setlists.objects.filter(
            event__venue__city__id=id,
            set_name__in=["Show", "Set 1", "Set 2", "Pre-Show", "Encore", "Post-Show"],
        )
        .order_by("song", "event")
        .select_related("song", "event")
    )

    context = {"venue_info": venue_info, "events": events, "songs": songs}
    return render(request, "databruce/locations/venues/venue_details.html", context)


def song(request: HttpRequest, id: int):  # noqa: A002
    song_info = models.Songs.objects.filter(id=id).first()

    songs = models.Setlists.objects.filter(song=id).order_by("event", "song_num")

    songs = models.SongsPage.objects.filter(id=id).select_related(
        "prev",
        "prev__song",
        "current__event",
        "current__song",
        "current__event__venue",
        "next",
        "next__song",
    )

    if song_info.num_plays_public > 0:
        filter = Q(event_certainty__in=["Confirmed", "Probable"]) & Q(
            id__gt=song_info.first.id,
        )
    else:
        filter = Q(event_certainty__in=["Confirmed", "Probable"])

    events = models.Events.objects.filter(filter).count()

    frequency = round(((song_info.num_plays_public / events) * 100), 2)

    first_release = (
        models.ReleaseTracks.objects.filter(song__id=id)
        .order_by("release__date")
        .first()
    )

    context = {
        "song_info": song_info,
        "songs": songs,
        "frequency": frequency,
        "release": first_release,
    }

    return render(request, "databruce/songs/song_details.html", context)


def advanced_search_results(request: HttpRequest):
    form = forms.AdvancedEventSearch(request.GET)

    if form.is_valid():
        if len(form.cleaned_data["musician"]) == 1:
            events = models.Onstage.objects.filter(
                relation__in=form.cleaned_data["musician"],
            ).values_list("event")

            result = models.Events.objects.filter(
                Q(id__in=events)
                & Q(date__gte=form.cleaned_data["first_date"])
                & Q(date__lte=form.cleaned_data["last_date"])
                & Q(date__month__in=form.cleaned_data["month"])
                & Q(date__day__in=form.cleaned_data["day"])
                & Q(venue__city__id__in=form.cleaned_data["city"])
                & Q(venue__country__id__in=form.cleaned_data["country"]),
            )

        elif len(form.cleaned_data["band"]) == 1:
            events = models.Onstage.objects.filter(
                band__in=form.cleaned_data["band"],
            ).values_list("event")

            result = models.Events.objects.filter(
                Q(id__in=events)
                & Q(date__gte=form.cleaned_data["first_date"])
                & Q(date__lte=form.cleaned_data["last_date"])
                & Q(date__month__in=form.cleaned_data["month"])
                & Q(date__day__in=form.cleaned_data["day"])
                & Q(venue__city__id__in=form.cleaned_data["city"])
                & Q(venue__country__id__in=form.cleaned_data["country"]),
            )
        else:
            result = models.Events.objects.filter(
                Q(date__gte=form.cleaned_data["first_date"])
                & Q(date__lte=form.cleaned_data["last_date"])
                & Q(date__month__in=form.cleaned_data["month"])
                & Q(date__day__in=form.cleaned_data["day"])
                & Q(venue__city__id__in=form.cleaned_data["city"])
                & Q(venue__country__id__in=form.cleaned_data["country"]),
            )

        result = result.select_related(
            "artist",
            "venue",
            "tour",
            "venue__city",
            "venue__state",
            "venue__country",
        )

    return render(
        request,
        "databruce/search/advanced_search_results.html",
        {"events": result.order_by("id"), "fields": form},
    )


def event_search(request: HttpRequest):
    query = request.GET.get("event_date")

    result = models.Events.objects.filter(date=query).order_by("id")

    if len(result) == 1:
        return redirect(f"/events/{result.first().id}")

    return render(request, "databruce/search/search.html", {"events": result})


def advanced_search(request: HttpRequest):
    form = forms.AdvancedEventSearch(request.GET)

    return render(request, "databruce/search/advanced_search.html", {"form": form})


def tours(request: HttpRequest):
    tours = models.Tours.objects.all().order_by("-last").select_related("first", "last")

    return render(request, "databruce/tours/tours.html", {"tours": tours})


def tour_details(request: HttpRequest, id: int):
    tour_info = models.Tours.objects.get(
        id=id,
    )

    events = (
        models.Events.objects.filter(tour=id)
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

    tour_legs = models.TourLegs.objects.filter(tour__id=id).order_by("first")

    valid_sets = ["Show", "Set 1", "Set 2", "Pre-Show", "Encore", "Post-Show"]

    songs = (
        models.Setlists.objects.filter(
            event__tour__id=id,
            set_name__in=valid_sets,
        )
        .order_by("song", "event")
        .select_related("song", "event")
    )

    return render(
        request,
        "databruce/tours/tour_details.html",
        {
            "tour": tour_info,
            "events": events,
            "tour_legs": tour_legs,
            "songs": songs,
        },
    )


def setlist_search(request: HttpRequest):
    form = forms.SetlistSearch(request.GET)
    return render(request, "databruce/search/setlist_search.html", {"form": form})


def setlist_search_results(request: HttpRequest):
    form = forms.SetlistSearch(request.GET)

    if form.is_valid():
        song = models.Songs.objects.get(id=form.cleaned_data["song"]).name

        if form.cleaned_data["position"] != "Followed By":
            position_filter = Q(position=form.cleaned_data["position"])
            if form.cleaned_data["position"] == "Anywhere":
                position_filter = Q(
                    set_name__in=[
                        "Show",
                        "Set 1",
                        "Set 2",
                        "Encore",
                        "Pre-Show",
                        "Post-Show",
                    ],
                )

            if form.cleaned_data["choice"] == "is":
                results = models.Setlists.objects.filter(
                    Q(song=form.cleaned_data["song"]) & position_filter,
                ).order_by("id")

            elif form.cleaned_data["choice"] == "not":
                results = models.Setlists.objects.exclude(
                    Q(song=form.cleaned_data["song"]) & position_filter,
                ).order_by("id")

            events = models.Events.objects.filter(
                id__in=results.values_list("event"),
            ).order_by("id")

            result = f"{song} ({form.cleaned_data['choice']} {form.cleaned_data['position']})"

        else:
            song2 = models.Songs.objects.get(id=form.cleaned_data["song2"]).name

            if form.cleaned_data["choice"] == "is":
                setlist_filter = Q(current__song__id=form.cleaned_data["song"]) & Q(
                    next__song__id=form.cleaned_data["song2"],
                )

            elif form.cleaned_data["choice"] == "not":
                setlist_filter = Q(current__song__id=form.cleaned_data["song"]) & ~Q(
                    next__song__id=form.cleaned_data["song2"],
                )

            results = models.SongsPage.objects.filter(
                setlist_filter,
            )

            events = models.Events.objects.filter(
                id__in=results.values_list("current__event"),
            ).order_by("id")

            result = f"{song} ({form.cleaned_data['choice']} followed by) {song2}"

    events = events.select_related(
        "venue",
        "venue__city",
        "venue__state",
        "venue__country",
        "artist",
        "tour",
    )

    context = {
        "events": events,
        "result": result,
    }

    return render(
        request,
        "databruce/search/setlist_search_results.html",
        context,
    )


def relations(request: HttpRequest):
    relations = models.Relations.objects.all().select_related("first", "last")

    return render(
        request,
        "databruce/relations/relations.html",
        {"relations": relations},
    )


def bands(request: HttpRequest):
    bands = (
        models.Bands.objects.filter().select_related("first", "last").order_by("name")
    ).annotate(
        bruce_band=Case(
            When(springsteen_band=True, then=Value("Yes")),
            default=Value("No"),
        ),
    )

    return render(
        request,
        "databruce/bands/bands.html",
        {"bands": bands},
    )


def relation_details(request: HttpRequest, id: int):
    rel_info = models.Relations.objects.filter(id=id).first()

    onstage = models.Onstage.objects.filter(relation=id).select_related("band")

    bands = onstage.distinct("band")

    events = (
        models.Events.objects.filter(id__in=onstage.values_list("event"))
        .select_related(
            "venue",
            "artist",
            "venue__city",
            "tour",
        )
        .order_by("id")
    )

    return render(
        request,
        "databruce/relations/relation_details.html",
        {"bands": bands, "info": rel_info, "events": events},
    )


def band_details(request: HttpRequest, id: int):
    band_info = models.Bands.objects.get(id=id)

    members = (
        models.Onstage.objects.filter(band=id)
        .select_related("relation", "relation__first", "relation__last")
        .order_by("relation")
    )

    print(members.query)

    events = (
        models.Events.objects.filter(id__in=members.values_list("event"))
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

    return render(
        request,
        "databruce/bands/band_details.html",
        {"members": members.distinct("relation"), "info": band_info, "events": events},
    )


def releases(request: HttpRequest):
    releases = models.Releases.objects.all().order_by("date")

    return render(
        request,
        "databruce/releases/releases.html",
        {
            "releases": releases,
        },
    )


def release_details(request: HttpRequest, id: int):
    release_info = models.Releases.objects.get(id=id)

    tracks = (
        models.ReleaseTracks.objects.filter(release=id)
        .order_by(
            "track",
        )
        .prefetch_related("song__first", "song__last")
    )

    return render(
        request,
        "databruce/releases/release_details.html",
        {"info": release_info, "tracks": tracks},
    )


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
        {"cities": cities},
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
        "databruce/locations/cities/city_details.html",
        {"info": city_info, "events": events, "songs": songs, "venues": venues},
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
        {"states": states},
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
        "databruce/locations/states/state_details.html",
        {"info": state_info, "events": events, "songs": songs, "venues": venues},
    )


def countries(request: HttpRequest):
    countries = (
        models.Countries.objects.all().select_related("first", "last").order_by("name")
    )

    return render(
        request,
        "databruce/locations/countries/countries.html",
        {"countries": countries},
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
        "databruce/locations/countries/country_details.html",
        {
            "info": country_info,
            "events": events,
            "songs": songs,
            "venues": venues,
        },
    )


def event_runs(request: HttpRequest):
    runs = (
        models.Runs.objects.all()
        .select_related("first", "last", "band", "first__venue")
        .order_by("first")
    )

    return render(
        request,
        "databruce/events/runs.html",
        {"runs": runs},
    )
