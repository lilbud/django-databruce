import datetime
import re

from django.db.models import F, Manager, Q, QuerySet
from django.db.models.manager import BaseManager
from django.http import HttpRequest
from django_filters import rest_framework as filters
from querystring_parser import parser
from rest_framework.filters import BaseFilterBackend

from databruce import models


def get_sb_filter(
    column: str,
    condition: str,
    value: str = "",
    value2: str = "",
    type: str = "",  # noqa: A002
):
    filter_types = {
        "=": Q(**{f"{column}__iexact": value}),
        "!=": ~Q(**{f"{column}__iexact": value}),
        "starts": Q(**{f"{column}__istartswith": value}),
        "!starts": ~Q(**{f"{column}__istartswith": value}),
        "contains": Q(**{f"{column}__icontains": value}),
        "!contains": ~Q(**{f"{column}__icontains": value}),
        "ends": Q(**{f"{column}__iendswith": value}),
        "!ends": ~Q(**{f"{column}__iendswith": value}),
        "null": Q(**{f"{column}__exact": ""}) | Q(**{f"{column}__isnull": True}),
        "!null": ~Q(**{f"{column}__exact": ""}) & Q(**{f"{column}__isnull": False}),
        "<": Q(**{f"{column}__lt": value}),
        "<=": Q(**{f"{column}__lte": value}),
        ">=": Q(**{f"{column}__gte": value}),
        ">": Q(**{f"{column}__gt": value}),
        "between": Q(**{f"{column}__gte": value}) & Q(**{f"{column}__lte": value2}),
        "!between": ~Q(
            Q(**{f"{column}__gte": value}) & Q(**{f"{column}__lte": value2}),
        ),
    }

    if type == "num":
        filter_types["null"] = Q(**{f"{column}__isnull": True})
        filter_types["!null"] = Q(**{f"{column}__isnull": False})

    return filter_types.get(condition)


from django.http import QueryDict


class AdvFilter(BaseFilterBackend):
    def lookups(self, param: str, value: str):
        lookups = {
            "first_date": Q(date__gte=value),
            "last_date": Q(date__lte=value),
            "month": Q(date__month=value),
            "day": Q(date__day=value),
            "city": Q(venue__city__id=value),
            "state": Q(venue__state__id=value),
            "country": Q(venue__country__id=value),
            "tour": Q(tour__id=value),
            "musician": Q(relation__id=value),
            "band": Q(band__id=value),
            "day_of_week": Q(date__week_day=value),
        }

        return lookups.get(param)

    positions = {
        "anywhere": "Anywhere",
        "followed_by": "Followed By",
        "show_opener": "Show Opener",
        "in_show": "Show",
        "in_set_one": "Set 1",
        "set_one_opener": "Set 1 Opener",
        "set_one_closer": "Set 1 Closer",
        "in_set_two": "Set 2",
        "set_two_opener": "Set 2 Opener",
        "set_two_closer": "Set 2 Closer",
        "main_set_closer": "Main Set Closer",
        "encore_opener": "Encore Opener",
        "in_encore": "Encore",
        "in_preshow": "Pre-Show",
        "in_recording": "Recording",
        "in_soundcheck": "Soundcheck",
        "show_closer": "Show Closer",
    }

    def filter_queryset(self, request, queryset, view):
        params = QueryDict(request.GET["param"])
        event_filter = Q()
        setlist_event_filter = Q()
        event_results = []

        print(params)

        total_setlist_forms = int(params.get("form-TOTAL_FORMS", "0"))
        initial_setlist_forms = int(
            params.get("form-INITIAL_FORMS", "0"),
        )
        event_params = [
            item
            for item in params
            if not re.match(r"form-(\d)?|^.*_choice$", item) and params[item] != ""
        ]

        setlist_params = [item for item in params if re.match(r"form-\d", item)]

        for item in event_params:
            lookup = self.lookups(item, params[item])

            if lookup:
                if item in ("musician", "band"):
                    events = models.Onstage.objects.filter(lookup)
                    lookup = Q(id__in=events.values("event__id"))

                try:
                    if params[f"{item}_choice"] == "is":
                        event_filter.add(lookup, Q.AND)
                    elif params[f"{item}_choice"] == "not":
                        event_filter.add(~lookup, Q.AND)
                except KeyError:
                    event_filter.add(lookup, Q.AND)

        for i in range(total_setlist_forms):
            song1 = params.get(f"form-{i}-song1")
            choice = params.get(f"form-{i}-choice")  # is/not
            position = params.get(f"form-{i}-position")
            song2 = params.get(f"form-{i}-song2")

            filter = Q(song=song1)

            match position:
                case "anywhere":
                    if choice != "is":
                        filter = ~Q(song=song1)
                case "followed_by":
                    if choice == "is":
                        filter &= Q(next=song2)
                    else:
                        filter &= ~Q(next=song2)
                case _:
                    position = self.positions.get(position)

                    if choice == "is":
                        filter &= Q(position=position)
                    else:
                        filter &= ~Q(position=position)

            events = models.Songspagenew.objects.filter(filter).select_related(
                "event",
            )

            event_results.append(list(events.values_list("event__id", flat=True)))

            match params["conjunction"]:
                case "or":
                    setlist_event_filter.add(
                        Q(
                            id__in=list(
                                set.union(
                                    *map(
                                        set,
                                        event_results,
                                    ),
                                ),
                            ),
                        ),
                        Q.OR,
                    )

                case "and":
                    setlist_event_filter.add(
                        Q(
                            id__in=list(
                                set.intersection(
                                    *map(
                                        set,
                                        event_results,
                                    ),
                                ),
                            ),
                        ),
                        Q.AND,
                    )

            # event_filter.add(Q(id__in=events.values("event__id")), Q.AND)

        return queryset.filter(event_filter & setlist_event_filter)


class DTFilter(BaseFilterBackend):
    def get_searching(self, params):
        filter = Q()
        search_filter = Q()

        search_type = "icontains"

        try:
            for f in params["columns"].values():
                fields = [n.replace(".", "__").strip() for n in f["data"].split(",")]

                if f["name"]:
                    fields = [n.strip() for n in f["name"].split(",")]

                if f["searchable"] != "false":
                    for field in fields:
                        if f["search"]["regex"] == "true":
                            search_type = "iregex"

                        if f["search"]["value"]:
                            filter.add(
                                Q(**{f"{field}__{search_type}": f["search"]["value"]}),
                                Q.OR,
                            )

                        try:
                            re.compile(params["search"]["value"])
                            search_type = "iregex"
                        except re.error:
                            search_type = "icontains"

                        if params["search"]["value"]:
                            search_filter.add(
                                Q(
                                    **{
                                        f"{field}__{search_type}": params["search"][
                                            "value"
                                        ],
                                    },
                                ),
                                Q.OR,
                            )

            filter.add(search_filter, Q.AND)

        except KeyError:
            pass

        return filter

    def get_ordering(self, params):
        order = []

        try:
            for item in params["order"].values():
                field = item["name"].split(",")[0].strip()

                if item["dir"] == "asc":
                    order.append(F(f"{field}").asc(nulls_last=True))
                else:
                    order.append(F(f"{field}").desc(nulls_last=True))

        except KeyError:
            pass

        return order

    def get_searchbuilder(self, params):
        filter = Q()

        try:
            criteria = params["searchBuilder"]["criteria"]

            for param in criteria.values():
                name = next(
                    item["name"]
                    for item in params["columns"].values()
                    if item["data"] == param["origData"]
                )

                # if name isn't present, use data instead
                if not name:
                    name = next(
                        item["data"]
                        for item in params["columns"].values()
                        if item["data"] == param["origData"]
                    )

                fields = [i.strip() for i in name.split(",")]

                for field in fields:
                    search_filter = Q()

                    if "between" in param["condition"]:
                        field_filter = get_sb_filter(
                            column=field,
                            value=param["value1"],
                            value2=param["value2"],
                            condition=param["condition"],
                            type=param["type"],
                        )
                    elif "null" in param["condition"]:
                        field_filter = get_sb_filter(
                            column=field,
                            condition=param["condition"],
                            type=param["type"],
                        )
                    else:
                        field_filter = get_sb_filter(
                            column=field,
                            value=param["value1"],
                            condition=param["condition"],
                            type=param["type"],
                        )

                    search_filter.add(field_filter, Q.OR)

                if params["searchBuilder"]["logic"] == "AND":
                    filter.add(
                        search_filter,
                        Q.AND,
                    )
                else:
                    filter.add(
                        search_filter,
                        Q.OR,
                    )
        except KeyError:
            pass
        else:
            return filter

    def filter_queryset(self, request, queryset, view):
        params = parser.parse(request.GET.urlencode())

        ordering = self.get_ordering(params)
        q = self.get_searching(params)
        sb = self.get_searchbuilder(params)

        if q:
            queryset = queryset.filter(q)

        if ordering:
            queryset = queryset.order_by(*ordering)

        if sb:
            queryset = queryset.filter(sb)

        return queryset


class ArchiveFilter(filters.FilterSet):
    event = filters.CharFilter(field_name="event")
    date = filters.CharFilter(field_name="event__event_date")


class BootlegFilter(filters.FilterSet):
    archive = filters.BooleanFilter(field_name="archive", lookup_expr="isnull")


class CitiesFilter(filters.FilterSet):
    id = filters.NumberFilter(lookup_expr="exact")
    name = filters.CharFilter(lookup_expr="icontains")


class EventSetlistFilter(filters.FilterSet):
    id = filters.CharFilter(lookup_expr="exact")


class CoversFilter(filters.FilterSet):
    event = filters.CharFilter(field_name="event")
    date = filters.CharFilter(field_name="event__event_date")


class VenuesFilter(filters.FilterSet):
    name = filters.CharFilter(method="name_filter")
    city = filters.CharFilter(field_name="city__name", lookup_expr="icontains")
    state = filters.CharFilter(method="state_filter")
    country = filters.CharFilter(method="country_filter")


class IndexFilter(filters.FilterSet):
    date = filters.CharFilter(field_name="date", lookup_expr="startswith")
    month = filters.CharFilter(field_name="date__month", lookup_expr="exact")
    day = filters.CharFilter(field_name="date__day", lookup_expr="exact")
    # upcoming = filters.BooleanFilter(field_name="date", lookup_expr="gte")
    # recent = filters.BooleanFilter(field_name="date", lookup_expr="lte")


class EventRunFilter(filters.FilterSet):
    start = filters.DateTimeFilter(field_name="first__date", lookup_expr="gte")
    end = filters.DateTimeFilter(field_name="last__date", lookup_expr="lte")
    id = filters.NumberFilter(lookup_expr="exact")

    class Meta:
        model = models.Runs
        fields = ["start", "end", "id"]


class EventsFilter(filters.FilterSet):
    year = filters.CharFilter(
        field_name="id",
        lookup_expr="startswith",
        label="year",
    )

    start_date = filters.DateTimeFilter(field_name="date", lookup_expr="gte")
    end_date = filters.DateTimeFilter(field_name="date", lookup_expr="lte")

    date = filters.CharFilter(field_name="date", lookup_expr="startswith")
    month = filters.CharFilter(
        field_name="date__month",
        lookup_expr="exact",
        label="month",
    )
    day = filters.CharFilter(field_name="date__day", lookup_expr="exact", label="day")
    venue = filters.NumberFilter(field_name="venue__id", lookup_expr="exact")
    city = filters.NumberFilter(field_name="venue__city__id", lookup_expr="exact")
    state = filters.NumberFilter(field_name="venue__state__id", lookup_expr="exact")
    country = filters.NumberFilter(field_name="venue__country__id", lookup_expr="exact")
    run = filters.NumberFilter(field_name="run__id", lookup_expr="exact")
    artist = filters.NumberFilter(field_name="artist__id", lookup_expr="exact")
    tour = filters.NumberFilter(field_name="tour__id", lookup_expr="exact")
    leg = filters.NumberFilter(field_name="leg__id", lookup_expr="exact")

    class Meta:
        model = models.Events
        fields = [
            "year",
            "date",
            "month",
            "day",
            "venue",
            "city",
            "state",
            "country",
            "run",
            "artist",
            "tour",
            "leg",
        ]


class OnstageFilter(filters.FilterSet):
    relation = filters.NumberFilter(field_name="relation__id", lookup_expr="exact")
    band = filters.NumberFilter(field_name="band__id", lookup_expr="exact")
    event = filters.CharFilter(field_name="event__id", lookup_expr="exact")


class ReleaseTracksFilter(filters.FilterSet):
    release = filters.CharFilter(field_name="release__id", lookup_expr="exact")


class RelationFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")


class BandsFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")


class ReleaseFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")
    type = filters.CharFilter(lookup_expr="icontains")


class SetlistFilter(filters.FilterSet):
    event = filters.CharFilter(field_name="event__id", lookup_expr="exact")
    run = filters.CharFilter(field_name="event__run__id", lookup_expr="exact")
    leg = filters.CharFilter(field_name="event__leg__id", lookup_expr="exact")
    tour = filters.CharFilter(field_name="event__tour__id", lookup_expr="exact")
    song = filters.CharFilter(field_name="song__id", lookup_expr="exact")
    venue = filters.CharFilter(field_name="event__venue__id", lookup_expr="exact")
    city = filters.CharFilter(field_name="event__venue__city__id", lookup_expr="exact")
    state = filters.CharFilter(
        field_name="event__venue__state__id",
        lookup_expr="exact",
    )
    country = filters.CharFilter(
        field_name="event__venue__country__id",
        lookup_expr="exact",
    )

    class Meta:
        model = models.Setlists
        fields = "__all__"


class SetlistEntryFilter(filters.FilterSet):
    event = filters.CharFilter(field_name="event__id", lookup_expr="exact")
    run = filters.CharFilter(field_name="event__run__id", lookup_expr="exact")
    leg = filters.CharFilter(field_name="event__leg__id", lookup_expr="exact")
    tour = filters.CharFilter(field_name="event__tour__id", lookup_expr="exact")
    venue = filters.CharFilter(field_name="event__venue__id", lookup_expr="exact")
    city = filters.CharFilter(field_name="event__venue__city__id", lookup_expr="exact")
    state = filters.CharFilter(
        field_name="event__venue__state__id",
        lookup_expr="exact",
    )
    country = filters.CharFilter(
        field_name="event__venue__country__id",
        lookup_expr="exact",
    )


class SnippetFilter(filters.FilterSet):
    snippet = filters.NumberFilter(field_name="snippet__id", lookup_expr="exact")


class StateFilter(filters.FilterSet):
    id = filters.NumberFilter(lookup_expr="exact")
    name = filters.CharFilter(lookup_expr="icontains")


class CountryFilter(filters.FilterSet):
    id = filters.NumberFilter(lookup_expr="exact")
    name = filters.CharFilter(lookup_expr="icontains")


class TourFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    band = filters.CharFilter(field_name="band__name", lookup_expr="icontains")


class TourLegFilter(filters.FilterSet):
    tour = filters.NumberFilter(field_name="tour__id", lookup_expr="exact")


from django.core.exceptions import FieldError


class SongsPageFilter(filters.FilterSet):
    song = filters.NumberFilter(field_name="song__id", lookup_expr="exact")


class SongsFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")


class SetlistNoteFilter(filters.FilterSet):
    id = filters.NumberFilter(field_name="setlist__id", lookup_expr="exact")
    event = filters.CharFilter(field_name="event__id", lookup_expr="exact")
    note = filters.CharFilter(lookup_expr="icontains")
