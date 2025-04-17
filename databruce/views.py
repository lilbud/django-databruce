import contextlib
import datetime
import re

from django.db.models import Avg, Count, F, Q, RowRange, Sum, Window
from django.db.models.functions import Lag, Lead
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render

from . import models
from .forms import AdvancedEventSearch, SetlistSearch, yearDropdown

DATE = datetime.datetime.today()


def index(request: HttpRequest):
    events = (
        models.Events.objects.filter(
            event_date__month=DATE.month,
            event_date__day=DATE.day,
        )
        .select_related(
            "artist",
            "venue",
            "venue__city",
            "venue__state",
            "venue__country",
        )
        .order_by("-id")
    )

    recent_events = (
        models.Events.objects.filter(event_date__lte=DATE)
        .order_by("-event_date")
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
        {"events": events, "recent": recent_events, "date": DATE},
    )


def test(request: HttpRequest):
    return render(request, "databruce/test.html")


def songs(request: HttpRequest):
    songs = (
        models.Songs.objects.all()
        .filter(Q(num_plays_public__gte=1) | Q(num_plays_snippet__gte=1))
        .select_related("first", "last")
        .order_by("song_name")
    )

    context = {
        "songs": songs,
    }

    return render(request, "databruce/songs/songs.html", context)


def event_details(request: HttpRequest, event: str):
    event_info = models.Events.objects.filter(id=event).first()

    setlist = (
        models.Setlists.objects.filter(event__id=event)
        .select_related("song")
        .order_by("event", "song_num")
    )

    on_stage = (
        models.Onstage.objects.filter(event__id=event)
        .select_related("relation")
        .order_by("band_id", "relation")
    )

    notes = (
        models.SetlistNotes.objects.filter(event__id=event)
        .order_by("event", "num")
        .select_related("id")
    )

    try:
        prev_event = (
            models.Events.objects.filter(id__lt=event).order_by("id").last()
        ).id
    except AttributeError:
        prev_event = None

    try:
        next_event = (
            models.Events.objects.filter(id__gt=event).order_by("id").first()
        ).id
    except AttributeError:
        next_event = None

    context = {
        "event": event_info,
        "eventid": event,
        "setlist": setlist,
        "notes": notes,
        "relations": on_stage,
        "last_event": prev_event,
        "next_event": next_event,
    }

    return render(request, "databruce/events/event_details.html", context)


def events(request: HttpRequest, year: int = DATE.year):
    years = list(range(1965, DATE.year + 1))

    event_info = (
        models.Events.objects.filter(event_date__year=year)
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

    context = {
        "year": year,
        "years": years,
        "event_info": event_info,
    }

    return render(request, "databruce/events/events.html", context)


def venues(request: HttpRequest):
    filter = {
        "name__isnull": False,
        "num_events__gte": 1,
    }

    venues = (
        models.Venues.objects.all()
        .filter(**filter)
        .order_by("name")
        .select_related(
            "first",
            "last",
            "city",
            "state",
            "country",
        )
    )

    context = {"venues": venues}
    return render(request, "databruce/locations/venues/venues.html", context)


def venue(request: HttpRequest, id: int):
    events = models.Events.objects.filter(venue__id=id)
    print(events)

    venue_info = models.VenuesText.objects.get(id=id)

    context = {"venue_info": venue_info, "events": events}
    return render(request, "databruce/locations/venues/venue_details.html", context)


def song(request: HttpRequest, id: int):
    song_info = models.Songs.objects.get(id=id)

    songs = models.Setlists.objects.filter(song=id).order_by("event", "song_num")

    songs = models.SongsPageNew.objects.filter(id=id).select_related(
        "prev",
        "prev__song",
        "current__event",
        "current__song",
        "current__event__venue",
        "current__event__venue__city",
        "current__event__venue__state",
        "current__event__venue__country",
        "next",
        "next__song",
    )

    events = models.Events.objects.filter(
        event_certainty__in=["Confirmed", "Probable"],
    ).count()

    frequency = round(((song_info.num_plays_public / events) * 100), 2)

    snippets = (
        models.Snippets.objects.filter(
            snippet__id=id,
        )
        .select_related("event", "setlist", "snippet", "setlist__song")
        .order_by("event", "setlist", "position")
    )

    context = {
        "song_info": song_info,
        "songs": songs,
        "frequency": frequency,
        "snippets": snippets,
    }

    return render(request, "databruce/songs/song_details.html", context)


def advanced_search_results(request: HttpRequest):
    form = AdvancedEventSearch(request.GET)

    if form.is_valid():
        try:
            events = models.Onstage.objects.filter(
                relation__in=form.cleaned_data["musician"],
            ).values_list("event")

            result = models.Events.objects.filter(
                Q(id__in=events)
                & Q(event_date__gte=form.cleaned_data["first_date"])
                & Q(event_date__lte=form.cleaned_data["last_date"])
                & Q(event_date__month__in=form.cleaned_data["month"])
                & Q(event_date__day__in=form.cleaned_data["day"])
                & Q(artist__in=form.cleaned_data["band"])
                & Q(venue__city__id__in=form.cleaned_data["city"])
                & Q(venue__country__id__in=form.cleaned_data["country"]),
            ).select_related("artist", "venue", "tour")
        except ValueError:
            result = models.Events.objects.filter(
                Q(event_date__gte=form.cleaned_data["first_date"])
                & Q(event_date__lte=form.cleaned_data["last_date"])
                & Q(event_date__month__in=form.cleaned_data["month"])
                & Q(event_date__day__in=form.cleaned_data["day"])
                & Q(artist__in=form.cleaned_data["band"])
                & Q(venue__city__id__in=form.cleaned_data["city"])
                & Q(venue__country__id__in=form.cleaned_data["country"]),
            ).select_related("artist", "venue", "tour")

    return render(
        request,
        "databruce/search/advanced_search_results.html",
        {"events": result.order_by("id"), "fields": form.form_display()},
    )


def event_search(request: HttpRequest):
    query = request.GET.get("event_date")

    result = models.Events.objects.filter(event_date=query).order_by("id")

    if len(result) == 1:
        return redirect(f"/events/{result.first().id}")

    return render(request, "databruce/search/search.html", {"events": result})


def advanced_search(request: HttpRequest):
    if request.method == "GET":
        form = AdvancedEventSearch(request.GET)
    else:
        form = AdvancedEventSearch()

    return render(request, "databruce/search/advanced_search.html", {"form": form})


def tours(request: HttpRequest):
    tours = (
        models.Tours.objects.all().order_by("-first").select_related("first", "last")
    )

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

    tour_legs = models.TourLegs.objects.filter(tour_id__id=id).order_by("first")

    valid_sets = ["Show", "Set 1", "Set 2", "Pre-Show", "Encore", "Post-Show"]

    songs = (
        models.Setlists.objects.filter(
            event_id__in=events.values_list("id", flat=True),
            set_name__in=valid_sets,
        )
        .order_by("song", "event")
        .select_related("song", "event")
    )

    song_count = songs.distinct("song")
    event_count = events.filter(event_type="Concert")

    return render(
        request,
        "databruce/tours/tour_details.html",
        {
            "tour": tour_info,
            "events": events,
            "tour_legs": tour_legs,
            "songs": songs,
            "song_count": song_count,
            "event_count": event_count,
        },
    )


def setlist_search(request: HttpRequest):
    form = SetlistSearch(request.GET) if request.method == "GET" else SetlistSearch()

    return render(request, "databruce/search/setlist_search.html", {"form": form})


def setlist_search_results(request: HttpRequest):
    filter = {}
    setlist_filter = {}
    form = SetlistSearch(request.GET)

    if form.is_valid():
        print(form.cleaned_data)
        filter["song"] = form.cleaned_data["song"]
        filter["choice"] = form.cleaned_data["choice"]
        filter["position"] = form.cleaned_data["position"]

    song = models.Songs.objects.get(id=form.cleaned_data["song"]).song_name

    match form.cleaned_data["position"]:
        case "anywhere":
            setlist_filter["song"] = form.cleaned_data["song"]
            setlist_filter["set_name__in"] = [
                "Show",
                "Set 1",
                "Set 2",
                "Encore",
                "Pre-Show",
                "Post-Show",
            ]
        case "show_opener":
            setlist_filter["song"]
            setlist_filter["position"] = "Show Opener"
        case "set_one_closer":
            setlist_filter["song"]
            setlist_filter["position"] = "Set 1 Closer"

        case "set_two_opener":
            setlist_filter["song"]
            setlist_filter["position"] = "Set 2 Opener"
        case "main_set_closer":
            setlist_filter["song"]
            setlist_filter["position"] = "Main Set Closer"

        case "encore_opener":
            setlist_filter["song"]
            setlist_filter["position"] = "Encore Opener"
        case "show_closer":
            setlist_filter["song"]
            setlist_filter["position"] = "Show Closer"

    if filter["choice"] == "is":
        events = (
            models.Setlists.objects.filter(**setlist_filter)
            .select_related("event", "event__venue")
            .distinct("event")
        )
    elif filter["choice"] == "not":
        events = (
            models.Setlists.objects.exclude(**setlist_filter)
            .select_related("event", "event__venue")
            .distinct("event")
        )

    result = f"{song} ({filter['choice']} {filter['position'].replace('_', ' ')})"

    context = {
        "events": events.order_by("event"),
        "result": result,
    }

    return render(
        request,
        "databruce/search/setlist_search_results.html",
        context,
    )


def relations(request: HttpRequest):
    relations = (
        models.Relations.objects.all()
        .prefetch_related("first", "last")
        .order_by("name")
    )

    return render(
        request,
        "databruce/relations/relations.html",
        {"relations": relations},
    )


def bands(request: HttpRequest):
    bands = (
        models.Bands.objects.filter().select_related("first", "last").order_by("name")
    )

    return render(
        request,
        "databruce/bands/bands.html",
        {"bands": bands},
    )


def relation_details(request: HttpRequest, id: int):
    rel_info = models.Relations.objects.get(id=id)
    onstage = models.Onstage.objects.filter(relation=id)

    bands = onstage.distinct("band").select_related("band")

    events = (
        models.Events.objects.filter(id__in=onstage.values_list("event", flat=True))
        .select_related(
            "venue",
            "artist",
            "venue__city",
            "venue__state",
            "venue__country",
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
        .distinct("relation")
        .select_related("relation", "relation__first", "relation__last")
        .order_by("relation_id")
    )

    events = (
        models.Onstage.objects.filter(band=id)
        .distinct("event")
        .select_related(
            "event__venue",
            "event__artist",
            "event__venue__city",
            "event__venue__state",
            "event__venue__country",
            "event__tour",
        )
        .order_by("event")
    )

    return render(
        request,
        "databruce/bands/band_details.html",
        {"members": members, "info": band_info, "events": events},
    )


def releases(request: HttpRequest):
    releases = models.Releases.objects.all().order_by("date")

    return render(
        request,
        "databruce/releases/releases.html",
        {"releases": releases},
    )


def release_details(request: HttpRequest, id: int):
    release_info = models.Releases.objects.get(id=id)

    tracks = (
        models.ReleaseTracks.objects.filter(release=id)
        .order_by(
            "track_num",
        )
        .select_related("song__first", "song__last")
    )

    return render(
        request,
        "databruce/releases/release_details.html",
        {"info": release_info, "tracks": tracks},
    )


def cities(request: HttpRequest):
    cities = (
        models.Cities.objects.all()
        .select_related("state", "country", "first", "last")
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
            "state",
            "first",
            "last",
        )
        .first()
    )

    events = (
        models.Events.objects.filter(venue__city=id)
        .select_related("venue__city", "venue__state", "artist")
        .order_by("id")
    )

    return render(
        request,
        "databruce/locations/cities/city_details.html",
        {"info": city_info, "events": events},
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

    events = (
        models.Events.objects.filter(venue__state=id)
        .select_related("venue__city", "venue__country", "artist")
        .order_by("id")
    )

    return render(
        request,
        "databruce/locations/states/state_details.html",
        {"info": state_info, "events": events},
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

    return render(
        request,
        "databruce/locations/countries/country_details.html",
        {
            "info": country_info,
            "events": events,
        },
    )
