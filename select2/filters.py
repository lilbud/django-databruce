from django.db.models import Q
from django_filters import rest_framework as filters

from databruce import models


class CitySelect2Filter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="istartswith", label="Name")
    state = filters.CharFilter(field_name="state__name", lookup_expr="istartswith")
    country = filters.CharFilter(field_name="country__name", lookup_expr="istartswith")

    class Meta:
        model = models.Cities
        fields = ["name", "state", "country"]


class StateSelect2Filter(filters.FilterSet):
    name = filters.CharFilter(
        method="filter_name",
        lookup_expr="istartswith",
        label="Name/Abbrev",
    )

    country = filters.CharFilter(
        field_name="country__name",
        lookup_expr="istartswith",
        label="Country",
    )

    def filter_name(self, queryset, name, value):
        filter = Q(name__istartswith=value) | Q(abbrev__iexact=value)
        return queryset.filter(filter)

    class Meta:
        model = models.States
        fields = ["name", "country"]


class CountrySelect2Filter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="istartswith", label="Name")

    class Meta:
        model = models.Countries
        fields = ["name"]


class VenueSelect2Filter(filters.FilterSet):
    name = filters.CharFilter(method="filter_name", label="Name/Detail")

    def filter_name(self, queryset, name, value):
        filter = Q(name__istartswith=value) | Q(detail__istartswith=value)
        return queryset.filter(filter)

    class Meta:
        model = models.Venues
        fields = ["name"]


class TourSelect2Filter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="istartswith", label="Name")

    class Meta:
        model = models.Tours
        fields = ["name"]


class RelationSelect2Filter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="istartswith", label="Name")

    class Meta:
        model = models.Relations
        fields = ["name"]


class BandSelect2Filter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="istartswith", label="Name")

    class Meta:
        model = models.Bands
        fields = ["name"]


class SongSelect2Filter(filters.FilterSet):
    # Use a method filter instead of a raw lookup expression
    name = filters.CharFilter(
        method="filter_name",
        label="Name",
    )

    class Meta:
        model = models.Songs
        fields = ["name"]

    def filter_name(self, queryset, name, value):
        if not value:
            return queryset

        # 1. Build an unaccented full-text search query from user input
        # 2. Build an unaccented search vector from the 'name' database column
        return queryset.filter(
            name__unaccent__icontains=value,
        )


class TagSelect2Filter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="istartswith", label="Name")

    class Meta:
        model = models.Tags
        fields = ["name"]


class TypeSelect2Filter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="istartswith", label="Name")

    class Meta:
        model = models.Types
        fields = ["name"]
