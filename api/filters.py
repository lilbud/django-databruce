import re

from django.db.models import F, Q
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

                search_filter = Q()

                for field in fields:
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
    event = filters.CharFilter(field_name="event__id")
    date = filters.CharFilter(field_name="event__event_date")


class BootlegFilter(filters.FilterSet):
    archive = filters.BooleanFilter(field_name="archive", lookup_expr="isnull")


class CitiesFilter(filters.FilterSet):
    id = filters.NumberFilter(lookup_expr="exact")


class EventSetlistFilter(filters.FilterSet):
    id = filters.CharFilter(lookup_expr="exact")


class CoversFilter(filters.FilterSet):
    event = filters.CharFilter(field_name="event")
    date = filters.CharFilter(field_name="event__event_date")


class VenuesFilter(filters.FilterSet):
    id = filters.CharFilter(lookup_expr="exact")
    city = filters.CharFilter(field_name="city__id", lookup_expr="exact")


class IndexFilter(filters.FilterSet):
    date = filters.CharFilter(field_name="date", lookup_expr="startswith")
    month = filters.CharFilter(field_name="date__month", lookup_expr="exact")
    day = filters.CharFilter(field_name="date__day", lookup_expr="exact")


class EventRunFilter(filters.FilterSet):
    start_date = filters.DateTimeFilter(field_name="first__date", lookup_expr="gte")
    end_date = filters.DateTimeFilter(field_name="last__date", lookup_expr="lte")
    id = filters.NumberFilter(lookup_expr="exact")

    class Meta:
        model = models.Runs
        fields = ["start_date", "end_date", "id"]


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    pass


class EventsFilter(filters.FilterSet):
    year = filters.CharFilter(
        field_name="id",
        lookup_expr="startswith",
        label="year",
    )

    id__in = CharInFilter(field_name="id", lookup_expr="in")

    start_date = filters.DateTimeFilter(field_name="date", lookup_expr="gte")
    end_date = filters.DateTimeFilter(field_name="date", lookup_expr="lte")

    day_of_week = filters.NumberFilter(field_name="date__week_day", lookup_expr="exact")

    date = filters.CharFilter(field_name="date", lookup_expr="startswith")
    month = filters.NumberFilter(
        field_name="date__month",
        lookup_expr="exact",
        label="month",
    )
    day = filters.NumberFilter(field_name="date__day", lookup_expr="exact", label="day")
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
    id = filters.NumberFilter(lookup_expr="exact")


class BandsFilter(filters.FilterSet):
    id = filters.NumberFilter(lookup_expr="exact")


class ReleaseFilter(filters.FilterSet):
    id = filters.NumberFilter(lookup_expr="exact")
    type = filters.CharFilter(lookup_expr="icontains")


class SetlistFilter(filters.FilterSet):
    event = filters.CharFilter(field_name="event__id", lookup_expr="exact")
    run = filters.NumberFilter(field_name="event__run__id", lookup_expr="exact")
    leg = filters.NumberFilter(field_name="event__leg__id", lookup_expr="exact")
    tour = filters.NumberFilter(field_name="event__tour__id", lookup_expr="exact")
    song = filters.NumberFilter(field_name="song__id", lookup_expr="exact")
    venue = filters.NumberFilter(field_name="event__venue__id", lookup_expr="exact")
    city = filters.NumberFilter(
        field_name="event__venue__city__id",
        lookup_expr="exact",
    )
    state = filters.NumberFilter(
        field_name="event__venue__state__id",
        lookup_expr="exact",
    )
    country = filters.NumberFilter(
        field_name="event__venue__country__id",
        lookup_expr="exact",
    )

    def filter_song_num(self, queryset, name, value):
        lookup = f"{name}__isnull"
        return queryset.filter(**{lookup: False})

    song_num = filters.BooleanFilter(
        method="filter_song_num",
    )

    class Meta:
        model = models.Setlists
        fields = "__all__"


class SetlistEntryFilter(filters.FilterSet):
    event = filters.CharFilter(field_name="event__id", lookup_expr="exact")
    run = filters.NumberFilter(field_name="event__run__id", lookup_expr="exact")
    leg = filters.NumberFilter(field_name="event__leg__id", lookup_expr="exact")
    tour = filters.NumberFilter(field_name="event__tour__id", lookup_expr="exact")
    venue = filters.NumberFilter(field_name="event__venue__id", lookup_expr="exact")
    city = filters.NumberFilter(
        field_name="event__venue__city__id",
        lookup_expr="exact",
    )
    state = filters.NumberFilter(
        field_name="event__venue__state__id",
        lookup_expr="exact",
    )
    country = filters.NumberFilter(
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
    id = filters.NumberFilter(lookup_expr="exact")
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    band = filters.CharFilter(field_name="band__name", lookup_expr="icontains")


class TourLegFilter(filters.FilterSet):
    tour = filters.NumberFilter(field_name="tour__id", lookup_expr="exact")


class SongsPageFilter(filters.FilterSet):
    song = filters.NumberFilter(field_name="song__id", lookup_expr="exact")
    next = filters.NumberFilter(field_name="next_song", lookup_expr="exact")


class SongsFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")


class SetlistNoteFilter(filters.FilterSet):
    id = filters.NumberFilter(field_name="setlist__id", lookup_expr="exact")
    event = filters.CharFilter(field_name="event__id", lookup_expr="exact")
    note = filters.CharFilter(lookup_expr="icontains")
