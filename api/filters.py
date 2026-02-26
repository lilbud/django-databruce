import django_filters
from django import forms
from django.core.exceptions import FieldDoesNotExist
from django.db.models import (
    F,
    Q,
)
from django_filters import rest_framework as filters
from rest_framework.filters import BaseFilterBackend

from databruce import models

# from .views import VALID_SET_NAMES
VALID_SET_NAMES = [
    "Show",
    "Set 1",
    "Set 2",
    "Encore",
    "Pre-Show",
    "Post-Show",
]


class DataTablesFilterBackend(BaseFilterBackend):
    def get_sb_filter(
        self,
        column: str,
        condition: str,
        value: str = "",
        value2: str = "",
        sb_type: str = "",
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

        if sb_type == "num":
            filter_types["null"] = Q(**{f"{column}__isnull": True})
            filter_types["!null"] = Q(**{f"{column}__isnull": False})

        if sb_type == "boolean":
            filter_types["null"] = Q(**{f"{column}": False})
            filter_types["!null"] = Q(**{f"{column}": True})

        return filter_types.get(condition)

    def verify_fields(self, model, fields):
        valid_fields = []

        for path in fields:
            current_model = model
            parts = path.split("__")
            is_valid = True

            try:
                for i, part in enumerate(parts):
                    # 1. Try checking for a database field via _meta
                    try:
                        field = current_model._meta.get_field(part)
                        if i < len(parts) - 1:
                            if field.is_relation:
                                current_model = field.related_model
                            else:
                                is_valid = False
                                break
                    except FieldDoesNotExist:
                        # 2. Check if it's a @property on the model class
                        # Properties only work at the end of a path for filtering/display
                        if i == len(parts) - 1 and hasattr(current_model, part):
                            attr = getattr(current_model, part)
                            is_valid = bool(isinstance(attr, property))
                        else:
                            is_valid = False
                        break

                if is_valid:
                    valid_fields.append(path)
            except Exception:  # noqa: BLE001, S112
                continue

        return valid_fields

    def filter_queryset(self, request, queryset, view):
        # --- 1. PRE-PROCESS COLUMN METADATA ---
        column_configs = []
        col_index = 0

        while True:
            col_prefix = f"columns[{col_index}]"
            name_param = request.query_params.get(f"{col_prefix}[name]")

            if name_param is None:
                break

            fields = [f.strip().replace(".", "__") for f in name_param.split(",")]

            # filter invalid field names
            # fields = self.verify_fields(queryset.model, fields)

            config = {
                "index": str(col_index),
                "fields": fields,
                "data": request.query_params.get(f"{col_prefix}[data]"),
                "searchable": request.query_params.get(f"{col_prefix}[searchable]")
                == "true",
                "orderable": request.query_params.get(f"{col_prefix}[orderable]")
                == "true",
                "order_value": request.query_params.get(f"{col_prefix}[orderable]")
                == "true",
                "order_dir": request.query_params.get(
                    f"[order][{col_prefix}][dir]",
                ),
                "search_value": request.query_params.get(
                    f"{col_prefix}[search][value]",
                ),
                "search_regex": request.query_params.get(
                    f"{col_prefix}[search][regex]",
                )
                == "true",
            }

            if config["orderable"] and fields:
                config["order_value"] = fields[0]

            column_configs.append(config)

            col_index += 1

        # --- 2. SEARCHING LOGIC ---
        global_search_value = request.query_params.get("search[value]")
        global_search_regex = request.query_params.get("search[regex]")

        is_filtered = False
        global_q = Q()
        column_q = Q()
        search_type = "icontains"

        for config in column_configs:
            if not config["searchable"]:
                continue

            if global_search_value:
                is_filtered = True

                # if global_search_regex:
                #     search_type = "iregex"

                for field in config["fields"]:
                    global_q |= Q(**{f"{field}__{search_type}": global_search_value})

            if config["search_value"]:
                is_filtered = True
                col_specific_q = Q()

                if config["search_regex"]:
                    search_type = "iregex"

                for field in config["fields"]:
                    col_specific_q |= Q(
                        **{f"{field}__{search_type}": config["search_value"]},
                    )

                column_q &= col_specific_q

        # --- 3. ORDERING LOGIC ---
        order_list = []
        order_index = 0

        while True:
            order_prefix = f"order[{order_index}]"
            col_idx_param = request.query_params.get(f"{order_prefix}[column]")

            if col_idx_param is None:
                break

            # Find the config matching this index
            target_config = next(
                (c for c in column_configs if c["index"] == col_idx_param),
                None,
            )

            if target_config and target_config["orderable"]:
                direction = request.query_params.get(f"{order_prefix}[dir]", "asc")

                if direction == "asc":
                    order_list.append(
                        F(f"{target_config['fields'][0]}").asc(nulls_last=True),
                    )
                else:
                    order_list.append(
                        F(f"{target_config['fields'][0]}").desc(nulls_last=True),
                    )

            order_index += 1

        sb_index = 0
        sb_filter = Q()

        # searchbuilder
        while True:
            searchbuilder_prefix = f"searchBuilder[criteria][{sb_index}]"
            col_idx_param = request.query_params.get(
                f"{searchbuilder_prefix}[origData]",
            )

            if col_idx_param is None:
                break

            name = next(c for c in column_configs if c["data"] == col_idx_param)

            for field in name["fields"]:
                sb_filter &= self.get_sb_filter(
                    column=field,
                    condition=request.query_params.get(
                        f"{searchbuilder_prefix}[condition]",
                    ),
                    value=request.query_params.get(f"{searchbuilder_prefix}[value1]"),
                    value2=request.query_params.get(f"{searchbuilder_prefix}[value2]"),
                    sb_type=request.query_params.get(
                        f"{searchbuilder_prefix}[type]",
                        "text",
                    ),
                )

            sb_index += 1

        if is_filtered:
            print(global_q)
            queryset = queryset.filter(global_q & column_q)

        if sb_filter:
            queryset = queryset.filter(sb_filter)

        if is_filtered or order_list:
            print(order_list)
            return queryset.order_by(*order_list).distinct()

        return queryset


class ArchiveFilter(filters.FilterSet):
    event = filters.CharFilter(field_name="event__event_id")
    date = filters.CharFilter(field_name="event__event_date")


class BootlegFilter(filters.FilterSet):
    archive = filters.BooleanFilter(field_name="archive", lookup_expr="isnull")


class CitiesFilter(filters.FilterSet):
    id = filters.NumberFilter(lookup_expr="exact")
    name = filters.CharFilter(lookup_expr="istartswith")


class EventSetlistFilter(filters.FilterSet):
    id = filters.CharFilter(lookup_expr="exact")


class CoversFilter(filters.FilterSet):
    event = filters.CharFilter(field_name="event")
    date = filters.CharFilter(field_name="event__event_date")


class VenuesFilter(filters.FilterSet):
    id = filters.CharFilter(lookup_expr="exact")
    city = filters.NumberFilter(field_name="city__id", lookup_expr="exact")
    state = filters.NumberFilter(field_name="state__id", lookup_expr="exact")
    country = filters.NumberFilter(field_name="country__id", lookup_expr="exact")

    city_name = filters.CharFilter(field_name="city__name", lookup_expr="icontains")
    state_name = filters.CharFilter(field_name="state__name", lookup_expr="icontains")
    country_name = filters.CharFilter(
        field_name="country__name",
        lookup_expr="icontains",
    )

    name = filters.CharFilter(lookup_expr="istartswith")


class IndexFilter(filters.FilterSet):
    date = filters.CharFilter(field_name="date", lookup_expr="startswith")
    month = filters.CharFilter(field_name="date__month", lookup_expr="exact")
    day = filters.CharFilter(field_name="date__day", lookup_expr="exact")


class EventRunFilter(filters.FilterSet):
    start_date = filters.DateTimeFilter(
        field_name="first_event__date",
        lookup_expr="gte",
    )
    end_date = filters.DateTimeFilter(field_name="last_event__date", lookup_expr="lte")
    id = filters.NumberFilter(lookup_expr="exact")

    class Meta:
        model = models.Runs
        fields = ["start_date", "end_date", "id"]


class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    pass


class EventsFilter(filters.FilterSet):
    year = filters.CharFilter(
        field_name="event_id",
        lookup_expr="startswith",
        label="year",
    )

    id = filters.CharFilter(field_name="event_id", lookup_expr="exact")

    start_date = filters.DateTimeFilter(field_name="date", lookup_expr="gte")
    end_date = filters.DateTimeFilter(field_name="date", lookup_expr="lte")

    day_of_week = filters.NumberFilter(
        field_name="date__week_day",
        lookup_expr="exact",
        label="day of week",
    )

    date = filters.CharFilter(field_name="date", lookup_expr="startswith")

    month = filters.NumberFilter(
        field_name="date__month",
        lookup_expr="exact",
        label="month",
    )

    day = filters.NumberFilter(field_name="date__day", lookup_expr="exact", label="day")

    venue = filters.NumberFilter(
        field_name="venue__id",
        lookup_expr="exact",
        label="venue",
    )

    city = filters.NumberFilter(
        field_name="venue__city__id",
        lookup_expr="exact",
        label="city",
    )
    state = filters.NumberFilter(
        field_name="venue__city__state__id",
        lookup_expr="exact",
        label="state",
    )
    country = filters.NumberFilter(
        field_name="venue__city__country__id",
        lookup_expr="exact",
        label="country",
    )
    run = filters.NumberFilter(
        field_name="run__id",
        lookup_expr="exact",
        label="event run",
    )
    artist = filters.NumberFilter(
        field_name="artist__id",
        lookup_expr="exact",
        label="artist",
    )
    tour = filters.NumberFilter(
        field_name="tour__id",
        lookup_expr="exact",
        label="tour",
    )
    leg = filters.NumberFilter(
        field_name="leg__id",
        lookup_expr="exact",
        label="tour_leg",
    )

    relation = django_filters.BaseInFilter(
        field_name="onstage__relation_id",
        label="onstage relation",
    )

    band = django_filters.BaseInFilter(
        field_name="onstage__band_id",
        distinct=True,
        label="onstage band",
    )

    user = filters.NumberFilter(
        field_name="user_event__user_id",
    )

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
            "relation",
            "band",
        ]


class OnstageFilter(filters.FilterSet):
    relation = filters.NumberFilter(field_name="relation__id", lookup_expr="exact")
    band = filters.NumberFilter(field_name="band__id", lookup_expr="exact")
    event = filters.CharFilter(field_name="event__event_id", lookup_expr="exact")


class OnstageBandFilter(filters.FilterSet):
    relation = filters.NumberFilter(field_name="relation__id", lookup_expr="exact")
    band = filters.NumberFilter(field_name="band__id", lookup_expr="exact")
    first = filters.CharFilter(field_name="first_event__event_id", lookup_expr="exact")
    last = filters.CharFilter(field_name="last_event__event_id", lookup_expr="exact")


class ReleaseTracksFilter(filters.FilterSet):
    release = filters.CharFilter(field_name="release__id", lookup_expr="exact")


class RelationFilter(filters.FilterSet):
    id = filters.NumberFilter(lookup_expr="exact")
    name = filters.CharFilter(lookup_expr="istartswith")


class BandsFilter(filters.FilterSet):
    id = filters.NumberFilter(lookup_expr="exact")
    name = filters.CharFilter(lookup_expr="istartswith")


class ReleaseFilter(filters.FilterSet):
    id = filters.NumberFilter(lookup_expr="exact")
    type = filters.CharFilter(lookup_expr="icontains")
    start_date = filters.DateTimeFilter(field_name="date", lookup_expr="gte")
    end_date = filters.DateTimeFilter(field_name="date", lookup_expr="lte")


class SetlistFilter(filters.FilterSet):
    event = filters.CharFilter(field_name="event__event_id", lookup_expr="exact")
    run = filters.NumberFilter(field_name="event__run__id", lookup_expr="exact")
    leg = filters.NumberFilter(field_name="event__leg__id", lookup_expr="exact")
    tour = filters.NumberFilter(
        field_name="event__tour__id",
        lookup_expr="exact",
    )

    song = filters.NumberFilter(
        field_name="song__id",
        lookup_expr="exact",
        distinct=True,
    )

    venue = filters.NumberFilter(field_name="event__venue__id", lookup_expr="exact")

    city = filters.NumberFilter(
        field_name="event__venue__city__id",
        lookup_expr="exact",
    )

    state = filters.NumberFilter(
        field_name="event__venue__city__state__id",
        lookup_expr="exact",
    )

    country = filters.NumberFilter(
        field_name="event__venue__city__country__id",
        lookup_expr="exact",
    )

    user = filters.NumberFilter(
        field_name="event__user_event__id",
        lookup_expr="exact",
    )

    def filter_song_num(self, queryset, name, value):
        lookup = f"{name}__isnull"
        return queryset.filter(**{lookup: False})

    def filter_show_only(self, queryset, name, value):
        lookup = "set_name__in"

        lookup = Q(set_name__in=VALID_SET_NAMES) & Q(event__public=True)
        return queryset.filter(lookup)

    song_num = filters.BooleanFilter(
        method="filter_song_num",
    )

    show_only = filters.BooleanFilter(
        method="filter_show_only",
    )

    class Meta:
        model = models.Setlists
        fields = "__all__"


class SetlistEntryFilter(filters.FilterSet):
    event = filters.CharFilter(field_name="event__event_id", lookup_expr="exact")
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


class SetlistSongsFilter(filters.FilterSet):
    event = filters.CharFilter(field_name="event__event_id", lookup_expr="exact")
    run = filters.NumberFilter(field_name="event__run__id", lookup_expr="exact")
    leg = filters.NumberFilter(field_name="event__leg__id", lookup_expr="exact")
    tour = filters.NumberFilter(field_name="event__tour__id", lookup_expr="exact")
    venue = filters.NumberFilter(field_name="event__venue__id", lookup_expr="exact")
    city = filters.NumberFilter(
        field_name="event__venue__city__id",
        lookup_expr="exact",
    )

    state = filters.NumberFilter(
        field_name="event__venue__city__state__id",
        lookup_expr="exact",
    )

    country = filters.NumberFilter(
        field_name="event__venue__city__country__id",
        lookup_expr="exact",
    )

    user = filters.NumberFilter(
        field_name="event__user_event__user_id",
        lookup_expr="exact",
    )

    user_unseen = filters.NumberFilter(
        field_name="event__user_event__user_id",
        method="filter_unseen",
        label="Unseen",
    )

    user_rare = filters.BooleanFilter(
        field_name="song__num_plays_public",
        method="filter_rare",
        label="Rare (<100 plays)",
    )

    public_plays = filters.NumberFilter(
        field_name="song__num_plays_public",
        lookup_expr="gte",
    )

    def filter_rare(self, queryset, name, value):
        lookup = "song__num_plays_public__lte"
        return queryset.filter(**{lookup: 100})

    def filter_unseen(self, queryset, name, value):
        songs = queryset.filter(**{name: value}).values_list(
            "song__id",
            flat=True,
        )

        return queryset.exclude(song__id__in=songs).filter(song__num_plays_public__gt=0)


class SnippetFilter(filters.FilterSet):
    snippet = filters.NumberFilter(field_name="snippet__id", lookup_expr="exact")


class StateFilter(filters.FilterSet):
    id = filters.NumberFilter(lookup_expr="exact")
    name = filters.CharFilter(lookup_expr="istartswith")


class CountryFilter(filters.FilterSet):
    id = filters.NumberFilter(lookup_expr="exact")
    name = filters.CharFilter(lookup_expr="istartswith")


class TourFilter(filters.FilterSet):
    id = filters.NumberFilter(lookup_expr="exact")
    name = filters.CharFilter(field_name="name", lookup_expr="istartswith")
    band = filters.CharFilter(field_name="band__name", lookup_expr="icontains")


class TourLegFilter(filters.FilterSet):
    tour = filters.NumberFilter(field_name="tour__id", lookup_expr="exact")


class SongsPageFilter(filters.FilterSet):
    song = filters.NumberFilter(field_name="song__id", lookup_expr="exact")
    next = filters.NumberFilter(field_name="next_song", lookup_expr="exact")


class SongsFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    lyrics = filters.BooleanFilter()


class SetlistNoteFilter(filters.FilterSet):
    id = filters.NumberFilter(field_name="setlist__id", lookup_expr="exact")
    event = filters.CharFilter(field_name="event__event_id", lookup_expr="exact")
    note = filters.CharFilter(lookup_expr="icontains")


class UserAttendedShowsFilter(filters.FilterSet):
    user = filters.NumberFilter(field_name="user__id", lookup_expr="exact")
    event = filters.CharFilter(field_name="event__event_id", lookup_expr="exact")


class SetlistBreakdownFilter(filters.FilterSet):
    event = filters.CharFilter(
        field_name="setlists__event__event_id",
        lookup_expr="exact",
    )
