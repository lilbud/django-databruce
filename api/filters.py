import datetime

from django.db.models import F, Manager, Q, QuerySet
from django.db.models.manager import BaseManager
from django_filters import rest_framework as filters

from databruce import models


def sb_filter_types(
    column: str,
    condition: str,
    value: str = "",
    value2: str = "",
    type: str = "",
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


def queryset_sb_filter(query_params: dict) -> Q:
    """Create filter using searchbuilder query params.

    This is a server side version of the searchbuilder
    filtering usually done in DOM.
    """
    filter = Q()

    try:
        criteria = query_params["searchBuilder"]["criteria"]

        for item in criteria:
            param = criteria[item]

            data = next(
                item["name"]
                for item in dict(query_params["columns"]).values()
                if item["data"] == param["origData"]
            )

            if param["condition"] in ["between", "!between"]:
                search_filter = sb_filter_types(
                    column=data,
                    value=param["value1"],
                    value2=param["value2"],
                    condition=param["condition"],
                    type=param["type"],
                )
            elif param["condition"] in ["null", "!null"]:
                search_filter = sb_filter_types(
                    column=data,
                    condition=param["condition"],
                    type=param["type"],
                )
            else:
                search_filter = sb_filter_types(
                    column=data,
                    value=param["value1"],
                    condition=param["condition"],
                    type=param["type"],
                )

            if query_params["searchBuilder"]["logic"] == "AND":
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

    return filter


def order_queryset(order: dict):
    order_params = []

    for i in order:
        dir = order[i]["dir"]
        column = order[i]["name"]

        if dir == "asc":
            order_params.append(F(f"{column}").asc(nulls_last=True))
        else:
            order_params.append(F(f"{column}").desc(nulls_last=True))

    return order_params


def search_queryset(params: dict, search_query: str = ""):
    filter = Q()
    columns = params["columns"]

    for item in columns:
        column = columns[item]
        search_type = "icontains"

        if column["search"]["value"]:
            query = column["search"]["value"]

            if column["search"]["regex"] == "true":
                search_type = "iregex"

            filter.add(
                Q(**{f"{column['name']}__{search_type}": query}),
                Q.AND,
            )

        if search_query != "":
            if params["search"]["regex"] == "true":
                search_type = "iregex"

            filter.add(
                Q(**{f"{column['name']}__{search_type}": search_query}),
                Q.OR,
            )

    print(filter)

    return filter


class ArchiveFilter(filters.FilterSet):
    event = filters.CharFilter(field_name="event")
    date = filters.CharFilter(field_name="event__event_date")


class BootlegFilter(filters.FilterSet):
    date = filters.CharFilter(field_name="event__event_date")
    title = filters.CharFilter(lookup_expr="icontains")
    label = filters.CharFilter(lookup_expr="icontains")
    source = filters.CharFilter(lookup_expr="icontains")
    type = filters.CharFilter(lookup_expr="icontains")


class CitiesFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")
    state = filters.CharFilter(field_name="state__name", lookup_expr="icontains")


class CoversFilter(filters.FilterSet):
    event = filters.CharFilter(field_name="event")
    date = filters.CharFilter(field_name="event__event_date")


class VenuesFilter(filters.FilterSet):
    name = filters.CharFilter(method="name_filter")
    city = filters.CharFilter(field_name="city__name", lookup_expr="icontains")
    state = filters.CharFilter(method="state_filter")
    country = filters.CharFilter(method="country_filter")

    def name_filter(self, queryset, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(aliases__icontains=value),
        )

    def state_filter(self, queryset, value):
        return queryset.filter(
            Q(state__name__icontains=value) | Q(state__abbrev__iexact=value),
        )

    def country_filter(self, queryset, value):
        return queryset.filter(
            Q(country__name__icontains=value)
            | Q(country__alpha_2__iexact=value)
            | Q(country__alpha_3__iexact=value),
        )


class EventsFilter(filters.FilterSet):
    date = filters.CharFilter("event_date")
    venue = filters.CharFilter(field_name="venue__name", lookup_expr="icontains")
    city = filters.CharFilter(field_name="venue__city__name", lookup_expr="icontains")
    state = filters.CharFilter(method="state_filter")
    country = filters.CharFilter(method="country_filter")

    def state_filter(self, queryset, value):
        return queryset.filter(
            Q(venue__state__name__icontains=value)
            | Q(venue__state__abbrev__iexact=value),
        )

    def country_filter(self, queryset, value):
        return queryset.filter(
            Q(venue__country__name__icontains=value)
            | Q(venue__country__alpha_2__iexact=value)
            | Q(venue__country__alpha_3__iexact=value),
        )


class OnstageFilter(filters.FilterSet):
    relation = filters.CharFilter(field_name="relation__name", lookup_expr="icontains")
    event = filters.CharFilter(method="event_filter")

    def event_filter(self, queryset, value):
        return queryset.filter(
            Q(event__id__iexact=value) | Q(event__event_date__iexact=value),
        )


class ReleaseTracksFilter(filters.FilterSet):
    release = filters.CharFilter(field_name="release__name", lookup_expr="icontains")


class ReleaseFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")
    type = filters.CharFilter(lookup_expr="icontains")


class SetlistFilter(filters.FilterSet):
    event = filters.CharFilter()
    date = filters.CharFilter(field_name="event__event_date", lookup_expr="icontains")
    song = filters.CharFilter(method="song_filter")

    def song_filter(self, queryset, value):
        return queryset.filter(
            song=value,
        )


class SnippetFilter(filters.FilterSet):
    song = filters.CharFilter(field_name="setlist__song__song_name")
    snippet = filters.CharFilter(field_name="snippet__name")
    event = filters.CharFilter(field_name="setlist__event")


class StateFilter(filters.FilterSet):
    name = filters.CharFilter(method="state_filter")
    country = filters.CharFilter(method="country_filter")

    def state_filter(self, queryset, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(state_abbrev__iexact=value),
        )

    def country_filter(self, queryset, value):
        return queryset.filter(
            Q(country__name__icontains=value)
            | Q(country__alpha_2__iexact=value)
            | Q(country__alpha_3__iexact=value),
        )


class TourFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="tour_name", lookup_expr="icontains")
    band = filters.CharFilter(field_name="band__name", lookup_expr="icontains")


class TourLegFilter(filters.FilterSet):
    tour = filters.CharFilter(field_name="tour__name", lookup_expr="icontains")
    name = filters.CharFilter()
