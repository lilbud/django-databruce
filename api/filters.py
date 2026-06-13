import datetime

import django_filters
from dateutil import parser
from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
)
from django.core.exceptions import FieldDoesNotExist
from django.db.models import (
    Case,
    CharField,
    F,
    Q,
    Subquery,
    TextField,
    Value,
    When,
)
from django_filters import rest_framework as filters
from rest_framework.filters import BaseFilterBackend

from databruce import models

VALID_SET_NAMES = [
    "Show",
    "Set 1",
    "Set 2",
    "Encore",
    "Pre-Show",
    "Post-Show",
]

date = datetime.datetime.now(tz=datetime.UTC).date()


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

    def get_final_field(self, model, path):
        """Traverses the model __ path and returns the final Django field object."""
        parts = path.split("__")
        current_model = model

        for i, part in enumerate(parts):
            try:
                field = current_model._meta.get_field(part)
                # If there are more parts and this is a relation, move to the next model
                if i < len(parts) - 1 and field.is_relation:
                    current_model = field.related_model
                else:
                    return field
            except FieldDoesNotExist:
                return None
        return None

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
                "sb_criteria": request.query_params.get(
                    "[searchBuilder][logic]",
                ),
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

        if global_search_regex == "true":
            search_type = "iregex"

        for config in column_configs:
            if not config["searchable"]:
                continue

            if global_search_value:
                is_filtered = True

                for field in config["fields"]:
                    lookup = f"{field}__{search_type}"

                    try:
                        field_obj = self.get_final_field(queryset.model, field)

                        if isinstance(field_obj, (CharField, TextField)):
                            lookup = f"{field}__unaccent__{search_type}"

                    except FieldDoesNotExist:
                        continue

                    global_q |= Q(
                        **{
                            lookup: global_search_value,
                        },
                    )

            if config["search_value"]:
                is_filtered = True

                if config["search_regex"]:
                    search_type = "iregex"

                for field in config["fields"]:
                    lookup = f"{field}__{search_type}"

                    try:
                        field_obj = self.get_final_field(queryset.model, field)

                        if isinstance(field_obj, (CharField, TextField)):
                            lookup = f"{field}__unaccent__{search_type}"

                    except FieldDoesNotExist:
                        continue

                    column_q &= Q(
                        **{lookup: config["search_value"]},
                    )

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

            criteria = request.query_params.get("searchBuilder[logic]")

            if col_idx_param is None:
                break

            name = next(c for c in column_configs if c["data"] == col_idx_param)

            for field in name["fields"]:
                sb_field_filter = self.get_sb_filter(
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

                if criteria == "OR":
                    sb_filter |= sb_field_filter
                else:
                    sb_filter &= sb_field_filter

            sb_index += 1

        if is_filtered:
            queryset = queryset.filter(global_q & column_q)

        if sb_filter:
            queryset = queryset.filter(sb_filter)

        if is_filtered or order_list:
            return queryset.order_by(*order_list).distinct()

        return queryset


class ArchiveFilter(filters.FilterSet):
    event = filters.CharFilter(field_name="event__event_id", label="event")
    date = filters.CharFilter(field_name="event__event_date", label="event date")


class BootlegFilter(filters.FilterSet):
    archive = filters.BooleanFilter(
        field_name="archive",
        lookup_expr="isnull",
        label="Has Archive.org upload",
    )


class CitiesFilter(filters.FilterSet):
    id = filters.NumberFilter(lookup_expr="exact")
    name = filters.CharFilter(lookup_expr="istartswith", label="Name")
    # state = filters.CharFilter(
    #     field_name="state__name", lookup_expr="istartswith", label="State"
    # )
    # country = filters.CharFilter(
    #     field_name="country__name", lookup_expr="istartswith", label="Country"
    # )


class CoversFilter(filters.FilterSet):
    event = filters.CharFilter(field_name="event")
    date = filters.CharFilter(field_name="event__event_date", label="event date")


class VenuesFilter(filters.FilterSet):
    id = filters.CharFilter(lookup_expr="exact")
    city = filters.NumberFilter(field_name="city__id", lookup_expr="exact")
    state = filters.NumberFilter(field_name="state__id", lookup_expr="exact")
    country = filters.NumberFilter(field_name="country__id", lookup_expr="exact")

    city_name = filters.CharFilter(
        field_name="city__name",
        lookup_expr="icontains",
        label="city name",
    )
    state_name = filters.CharFilter(
        field_name="state__name",
        lookup_expr="icontains",
        label="state name",
    )

    country_name = filters.CharFilter(
        field_name="country__name",
        lookup_expr="icontains",
    )

    name = filters.CharFilter(lookup_expr="istartswith", label="name")


class EventRunFilter(filters.FilterSet):
    id = filters.NumberFilter(lookup_expr="exact")
    start_date = filters.DateTimeFilter(
        field_name="first_event__date",
        lookup_expr="gte",
        label="start date",
    )
    end_date = filters.DateTimeFilter(
        field_name="last_event__date",
        lookup_expr="lte",
        label="end date",
    )

    class Meta:
        model = models.Runs
        fields = ["start_date", "end_date", "id"]


class EventsFilter(filters.FilterSet):
    time_frame = filters.ChoiceFilter(
        choices=[("latest", "Latest"), ("upcoming", "Upcoming")],
        method="filter_time_frame",
        label="Filter events by time frame",
    )

    year = filters.CharFilter(
        field_name="event_id",
        lookup_expr="exact",
        label="year",
    )

    id = filters.CharFilter(field_name="event_id", lookup_expr="exact")
    type = filters.CharFilter(field_name="type_id", lookup_expr="exact")

    start_date = filters.DateTimeFilter(
        field_name="date",
        lookup_expr="gte",
        label="start date",
    )

    end_date = filters.DateTimeFilter(
        field_name="date",
        lookup_expr="lte",
        label="end date",
    )

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
        field_name="venue_id",
        lookup_expr="exact",
        label="venue",
    )

    city = filters.NumberFilter(
        field_name="venue__city_id",
        lookup_expr="exact",
        label="city",
    )

    state = filters.NumberFilter(
        field_name="venue__city__state_id",
        lookup_expr="exact",
        label="state",
    )
    country = filters.NumberFilter(
        field_name="venue__city__country_id",
        lookup_expr="exact",
        label="country",
    )
    run = filters.NumberFilter(
        field_name="run_id",
        lookup_expr="exact",
        label="event run",
    )
    artist = filters.NumberFilter(
        field_name="artist_id",
        lookup_expr="exact",
        label="artist",
    )
    tour = filters.NumberFilter(
        field_name="tour_id",
        lookup_expr="exact",
        label="tour",
    )
    leg = filters.NumberFilter(
        field_name="leg_id",
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

    search = filters.CharFilter(
        method="filter_fulltext_search",
    )

    def filter_fulltext_search(self, queryset, name, value):
        if not value:
            return queryset

        # 1. Attempt to extract a valid year and/or month from the user's string
        parsed_year = None
        parsed_month = None

        try:
            # Use fuzzy=True so it ignores extraneous words like "events in Feb 1977"
            # default=datetime(1, 1, 1) prevents dateutil from filling missing parts with the current year/day
            parsed_date = parser.parse(
                value,
                fuzzy=True,
                default=datetime.datetime(1, 1, 1),
            )

            # Check if a valid year was provided (1 represents the unfilled fallback value)
            if parsed_date.year != 1:
                parsed_year = parsed_date.year
            if parsed_date.month != 1:
                parsed_month = parsed_date.month
        except (ValueError, OverflowError):
            # The input value isn't a recognizable date at all; pass silently
            pass

        date_conditions = Q()
        if parsed_year and parsed_month:
            # Matches exact year and month (e.g., "Feb 1977", "1977-02", "02/1977")
            date_conditions = Q(date__year=parsed_year, date__month=parsed_month)
        elif parsed_year:
            # Matches just the year (e.g., "1977")
            date_conditions = Q(date__year=parsed_year)

        query = SearchQuery(value, search_type="websearch")

        vector = (
            SearchVector("event_id", weight="A")
            + SearchVector("date", weight="B")
            + SearchVector("date__day", weight="B")
            + SearchVector("early_late", weight="B")
            + SearchVector("artist__name", weight="C")
            + SearchVector("venue__name", weight="B")
            + SearchVector("venue__city__name", weight="B")
            + SearchVector("run__name", weight="D")
        )

        return (
            queryset.annotate(
                search=vector,
                rank=Case(
                    # TIER 1: If the user explicitly typed a partial/full Event ID, force top priority
                    When(event_id__istartswith=value, then=Value(1.0)),
                    # TIER 2: Fall back to your standard postgres weighted text ranking
                    default=SearchRank(vector, query, weights=[0.1, 0.3, 0.6, 1.0]),
                ),
            )
            .filter(
                Q(event_id__startswith=str(value)) | date_conditions | Q(search=query),
                rank__gt=0.1,
            )
            .order_by("event_id")[:25]
        )

    def filter_time_frame(self, queryset, name, value):
        # FIX: Dynamic evaluation of the current date on every request
        current_date = datetime.datetime.now(datetime.UTC).date()

        if value == "latest":
            return queryset.filter(date__lte=current_date)
        if value == "upcoming":
            return queryset.filter(date__gt=current_date)

        return queryset

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
            "time_frame",
        ]


class OnstageFilter(filters.FilterSet):
    relation = filters.NumberFilter(
        field_name="relation__id",
        lookup_expr="exact",
        label="relation",
    )
    band = filters.NumberFilter(field_name="band__id", lookup_expr="exact")
    event = filters.CharFilter(
        field_name="event__event_id",
        lookup_expr="exact",
        label="event_id",
    )


class OnstageBandFilter(filters.FilterSet):
    relation = filters.NumberFilter(field_name="relation__id", lookup_expr="exact")
    band = filters.NumberFilter(field_name="band__id", lookup_expr="exact")
    first = filters.CharFilter(
        field_name="first_event__event_id",
        lookup_expr="exact",
        label="event_id",
    )
    last = filters.CharFilter(
        field_name="last_event__event_id",
        lookup_expr="exact",
        label="event_id",
    )


class ReleaseTracksFilter(filters.FilterSet):
    release = filters.CharFilter(field_name="release__id", lookup_expr="exact")


class RelationFilter(filters.FilterSet):
    id = filters.NumberFilter(lookup_expr="exact")
    name = filters.CharFilter(lookup_expr="istartswith")

    start_date = filters.DateTimeFilter(
        field_name="start_date",
        lookup_expr="gte",
        label="start date",
    )

    start_date_end = filters.DateTimeFilter(
        field_name="start_date",
        lookup_expr="lte",
        label="end date",
    )

    month = filters.NumberFilter(
        field_name="start_date__month",
        lookup_expr="exact",
        label="month",
    )

    day = filters.NumberFilter(
        field_name="start_date__day",
        lookup_expr="exact",
        label="day",
    )

    show_cal = filters.BooleanFilter(
        method="filter_show_cal",
        label="show on calendar",
    )

    def filter_show_cal(self, queryset, name, value):
        return queryset.filter(show_cal=value)


class BandsFilter(filters.FilterSet):
    id = filters.NumberFilter(lookup_expr="exact")
    name = filters.CharFilter(lookup_expr="istartswith")


class ReleaseFilter(filters.FilterSet):
    id = filters.NumberFilter(lookup_expr="exact")
    type = filters.CharFilter(lookup_expr="icontains")
    start_date = filters.DateTimeFilter(
        field_name="date",
        lookup_expr="gte",
        label="start date",
    )
    end_date = filters.DateTimeFilter(
        field_name="date",
        lookup_expr="lte",
        label="end date",
    )

    year = filters.NumberFilter(
        field_name="date__year",
        label="year",
    )

    current_year = filters.BooleanFilter(
        method="include_current_year",
        label="include current year?",
    )

    month = filters.NumberFilter(
        field_name="date__month",
        label="month",
    )

    day = filters.NumberFilter(field_name="date__day", label="day")

    def include_current_year(self, queryset, name, value):
        if value:
            return queryset.filter(date__year=date.year)

        return queryset.exclude(date__year=date.year)


class SetlistStatsFilter(filters.FilterSet):
    id = filters.NumberFilter(lookup_expr="exact")

    class Meta:
        model = models.SetlistStats
        fields = "__all__"


class SetlistFilter(filters.FilterSet):
    event = filters.CharFilter(
        field_name="event__event_id",
        lookup_expr="exact",
        label="event",
    )
    run = filters.NumberFilter(
        field_name="event__run__id",
        lookup_expr="exact",
        label="event run",
    )
    leg = filters.NumberFilter(
        field_name="event__leg__id",
        lookup_expr="exact",
        label="event tour leg",
    )
    tour = filters.NumberFilter(
        field_name="event__tour__id",
        lookup_expr="exact",
        label="tour",
    )

    song = filters.NumberFilter(
        field_name="song__id",
        lookup_expr="exact",
        label="song",
        distinct=True,
    )

    venue = filters.NumberFilter(
        field_name="event__venue__id",
        lookup_expr="exact",
        label="venue",
    )

    city = filters.NumberFilter(
        field_name="event__venue__city__id",
        lookup_expr="exact",
        label="city",
    )

    state = filters.NumberFilter(
        field_name="event__venue__city__state__id",
        lookup_expr="exact",
        label="state",
    )

    country = filters.NumberFilter(
        field_name="event__venue__city__country__id",
        lookup_expr="exact",
        label="country",
    )

    user = filters.NumberFilter(
        field_name="event__user_event__id",
        lookup_expr="exact",
        label="user",
    )

    debut = filters.BooleanFilter(label="debut")
    premiere = filters.BooleanFilter(label="premiere")
    sign_request = filters.BooleanFilter(label="sign_request")
    nobruce = filters.BooleanFilter(label="bruce not present")

    def filter_song_num(self, queryset, name, value):
        lookup = f"{name}__isnull"
        return queryset.filter(**{lookup: False})

    def filter_show_only(self, queryset, name, value):
        lookup = "set_name__in"

        lookup = Q(set_name__in=VALID_SET_NAMES) & Q(event__public=True)
        return queryset.filter(lookup)

    song_num = filters.BooleanFilter(
        method="filter_song_num",
        label="has song num",
    )

    show_only = filters.BooleanFilter(
        method="filter_show_only",
        label="show only",
    )

    class Meta:
        model = models.Setlists
        fields = "__all__"


class SetlistEntryFilter(filters.FilterSet):
    event = filters.CharFilter(
        field_name="event__event_id",
        lookup_expr="exact",
        label="event_id",
    )
    run = filters.NumberFilter(
        field_name="event__run__id",
        lookup_expr="exact",
        label="event run",
    )
    leg = filters.NumberFilter(
        field_name="event__leg__id",
        lookup_expr="exact",
        label="tour leg",
    )
    tour = filters.NumberFilter(
        field_name="event__tour__id",
        lookup_expr="exact",
        label="tour",
    )
    venue = filters.NumberFilter(
        field_name="event__venue__id",
        lookup_expr="exact",
        label="venue",
    )
    city = filters.NumberFilter(
        field_name="event__venue__city__id",
        lookup_expr="exact",
        label="city",
    )
    state = filters.NumberFilter(
        field_name="event__venue__state__id",
        lookup_expr="exact",
        label="state",
    )
    country = filters.NumberFilter(
        field_name="event__venue__country__id",
        lookup_expr="exact",
        label="country",
    )


class SetlistSongsFilter(filters.FilterSet):
    event = filters.CharFilter(
        field_name="event__event_id",
        lookup_expr="exact",
        label="event",
    )

    run = filters.NumberFilter(
        field_name="event__run__id",
        lookup_expr="exact",
        label="event run",
    )

    year = filters.NumberFilter(
        field_name="event__date__year",
        lookup_expr="exact",
        label="year",
    )

    leg = filters.NumberFilter(
        field_name="event__leg__id",
        lookup_expr="exact",
        label="tour leg",
    )
    tour = filters.NumberFilter(
        field_name="event__tour__id",
        lookup_expr="exact",
        label="tour",
    )
    venue = filters.NumberFilter(
        field_name="event__venue__id",
        lookup_expr="exact",
        label="venue",
    )

    city = filters.NumberFilter(
        field_name="event__venue__city__id",
        lookup_expr="exact",
        label="city",
    )

    state = filters.NumberFilter(
        field_name="event__venue__city__state__id",
        lookup_expr="exact",
        label="state",
    )

    country = filters.NumberFilter(
        field_name="event__venue__city__country__id",
        lookup_expr="exact",
        label="country",
    )

    user = filters.NumberFilter(
        field_name="event__user_event__user_id",
        lookup_expr="exact",
        label="User ID",
    )

    user_unseen = filters.NumberFilter(
        field_name="event__user_event__user_id",
        method="filter_unseen",
        label="Show songs this user hasn't seen",
    )

    user_rare = filters.BooleanFilter(
        field_name="song__num_plays_public",
        method="filter_rare",
        label="Rare (<100 plays)",
    )

    public_plays = filters.NumberFilter(
        field_name="song__num_plays_public",
        lookup_expr="gte",
        label="Public Plays (>=)",
    )

    def filter_rare(self, queryset, name, value):
        lookup = "song__num_plays_public__lte"
        return queryset.filter(**{lookup: 100})

    def filter_unseen(self, queryset, name, value):
        events = models.UserAttendedShows.objects.filter(user_id=value).values_list(
            "event_id",
        )

        if len(events) == 0:
            return queryset.none()

        songs = queryset.filter(**{name: value}).values_list(
            "song__id",
            flat=True,
        )

        return queryset.exclude(song__id__in=songs).filter(song__num_plays_public__gt=0)


class SnippetFilter(filters.FilterSet):
    snippet = filters.NumberFilter(field_name="snippet__id", lookup_expr="exact")

    song = filters.NumberFilter(
        field_name="setlist__song_id",
        lookup_expr="exact",
        label="song",
    )

    unique = filters.BooleanFilter(
        field_name="snippet_id",
        method="filter_unique",
        label="unique",
    )

    def filter_unique(self, queryset, name, value):
        if value:
            # Get the IDs of only the first instance of each snippet
            unique_ids = (
                models.Snippets.objects.order_by("snippet_id", "id")
                .distinct("snippet_id")
                .values_list("id", flat=True)
            )
            return queryset.filter(id__in=Subquery(unique_ids))
        return queryset


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
    name = filters.CharFilter(lookup_expr="icontains")


class SongsPageFilter(filters.FilterSet):
    song = filters.NumberFilter(field_name="id__song_id", lookup_expr="exact")


class SongsPageNewFilter(filters.FilterSet):
    song = filters.NumberFilter(field_name="id__song_id", lookup_expr="exact")
    next = filters.NumberFilter(field_name="next__song_id", lookup_expr="exact")
    prev = filters.NumberFilter(field_name="prev__song_id", lookup_expr="exact")


class SongsFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="iregex")
    lyrics = filters.BooleanFilter()


class SetlistNoteFilter(filters.FilterSet):
    id = filters.NumberFilter(field_name="setlist_id", lookup_expr="exact")
    event = filters.CharFilter(
        field_name="event_id",
        lookup_expr="exact",
        label="event_id",
    )
    note = filters.CharFilter(lookup_expr="icontains")


class UserAttendedShowsFilter(filters.FilterSet):
    user = filters.NumberFilter(field_name="user__id", lookup_expr="exact")
    event = filters.CharFilter(
        field_name="event__event_id",
        lookup_expr="exact",
        label="event_id",
    )


class SetlistBreakdownFilter(filters.FilterSet):
    event = filters.CharFilter(
        field_name="setlists__event__event_id",
        lookup_expr="exact",
    )


class EventTypeFilter(filters.FilterSet):
    id = filters.NumberFilter(lookup_expr="exact")
    name = filters.CharFilter(
        lookup_expr="icontains",
    )


class UserAlbumBreakdownFilter(filters.FilterSet):
    user = filters.NumberFilter(
        field_name="event__user_event__user_id",
        lookup_expr="exact",
    )


class YearSongBreakdownFilter(filters.FilterSet):
    song = filters.NumberFilter(
        field_name="song_id",
        lookup_expr="exact",
    )
