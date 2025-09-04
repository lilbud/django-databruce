from django.db.models import Q
from django_filters import rest_framework as filters


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


from rest_framework_datatables.django_filters.filters import GlobalFilter
from rest_framework_datatables.django_filters.filterset import DatatablesFilterSet


class GlobalCharFilter(GlobalFilter, filters.CharFilter):
    pass


class SongsFilter(DatatablesFilterSet):
    name = GlobalCharFilter(field_name="name", lookup_expr="icontains")
    first = GlobalCharFilter(lookup_expr="icontains")
    last = GlobalCharFilter(lookup_expr="icontains")


class ReleaseFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")
    type = filters.CharFilter(lookup_expr="icontains")


class SongsPageFilter(filters.FilterSet):
    id = filters.NumberFilter(
        field_name="id",
        lookup_expr="exact",
    )
    date = filters.DateFilter(
        field_name="current__event__date",
        lookup_expr="icontains",
    )


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
