import django_filters
from django import forms
from django.core.exceptions import FieldDoesNotExist
from django_filters import rest_framework as filters
from rest_framework.filters import BaseFilterBackend

from databruce import models


class AdvancedEventSearchFilter(filters.FilterSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. Loop through all filters defined in Meta.fields
        # We create a copy of the keys to avoid 'dictionary changed size during iteration'
        for field_name in list(self.filters.keys()):
            # 2. Skip existing exclude toggles to avoid infinite loops
            if field_name.endswith("_is_not"):
                continue

            # 3. Create a dynamic 'is not' toggle for this field
            toggle_name = f"{field_name}_is_not"
            self.filters[toggle_name] = django_filters.BooleanFilter(
                label="",
                widget=forms.Select(
                    attrs={
                        "class": "form-select form-select-sm col-3",
                    },
                    choices=((True, "is"), (False, "not")),
                ),
            )

    id = filters.CharFilter(field_name="event_id", lookup_expr="exact")

    day_of_week = filters.NumberFilter(
        field_name="date__week_day",
        label="day of week",
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm", "id": "dow"},
        ),
    )

    start_date = filters.DateFilter(
        field_name="date",
        required=False,
        lookup_expr="gte",
        label="start date",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    end_date = filters.DateFilter(
        field_name="date",
        required=False,
        lookup_expr="lte",
        label="end date",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    month = filters.NumberFilter(
        field_name="date__month",
        label="month",
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm", "id": "month"},
        ),
    )

    day = filters.NumberFilter(
        field_name="date__day",
        label="day",
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm select2", "id": "day"},
        ),
    )

    venue = filters.NumberFilter(
        field_name="venue__id",
        label="venue",
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm select2", "id": "venue"},
        ),
    )

    city = filters.NumberFilter(
        label="city",
        field_name="venue__city__id",
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm select2", "id": "city"},
        ),
    )

    state = filters.NumberFilter(
        field_name="venue__city__state__id",
        label="state",
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm select2", "id": "state"},
        ),
    )

    country = filters.NumberFilter(
        field_name="venue__city__country__id",
        label="country",
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm select2", "id": "country"},
        ),
    )

    run = filters.NumberFilter(
        field_name="run__id",
        label="event run",
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm select2", "id": "run"},
        ),
    )

    tour = filters.NumberFilter(
        field_name="tour__id",
        label="tour",
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm select2", "id": "tour"},
        ),
    )

    leg = filters.NumberFilter(
        field_name="leg__id",
        label="tour_leg",
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm select2", "id": "leg"},
        ),
    )

    def filter_queryset(self, queryset):
        """Global loop that stacks filters or exclusions based on the toggle state."""
        # Ensure form is valid before accessing cleaned_data
        if not self.form.is_valid():
            return queryset

        data = self.form.cleaned_data

        for name, value in data.items():
            # Skip empty inputs and the toggle fields themselves
            if value in [None, "", False, []] or name.endswith("_is_not"):
                continue

            # Get the model field path (e.g., 'venue__city')
            filter_obj = self.filters.get(name)
            model_path = filter_obj.field_name if filter_obj else name

            # Determine if we should .filter() or .exclude()
            is_exclude = data.get(f"{name}_is_not") is True

            if type(value) is str:
                lookup = f"{model_path}__iexact"
            else:
                lookup = f"{model_path}__exact"

            if is_exclude:
                queryset = queryset.exclude(**{lookup: value})
            else:
                queryset = queryset.filter(**{lookup: value})

        return queryset

    relation = django_filters.NumberFilter(
        field_name="onstage__relation_id",
        required=False,
        label="onstage relation",
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm select2", "id": "relation"},
        ),
    )

    band = django_filters.NumberFilter(
        field_name="onstage__band_id",
        distinct=True,
        required=False,
        label="onstage band",
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm select2", "id": "band"},
        ),
    )

    class Meta:
        model = models.Events
        fields = [
            # "start_date",
            # "end_date",
            # "day_of_week",
            # "month",
            # "day",
            "venue",
            "city",
            "state",
            "country",
            "run",
            "tour",
            "leg",
            "relation",
            "band",
        ]
