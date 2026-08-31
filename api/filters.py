import datetime
import re

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
  Model,
  Q,
  QuerySet,
  Subquery,
  TextField,
  Value,
  When,
)
from django_filters import ModelMultipleChoiceFilter
from django_filters import rest_framework as dj_filters
from rest_framework.filters import BaseFilterBackend
from rest_framework.request import Request
from rest_framework.views import APIView

from bruceyversion import models as bv_models
from databruce import models

date = datetime.datetime.now(tz=datetime.UTC).date()


class NumberInFilter(dj_filters.BaseInFilter, dj_filters.NumberFilter):
  pass


class NotEqualFilterBackend(BaseFilterBackend):
  def filter_queryset(self, request, queryset, view):
    # 1. Grab the FilterSet class assigned to this ViewSet
    filterset_class = getattr(view, "filterset_class", None)

    # 2. Extract out all declared filters to map names to actual database paths
    # (e.g., matching 'city' to field_name='venue__city_id')
    declared_filters = filterset_class.base_filters if filterset_class else {}

    for param, value in request.query_params.items():
      if param.endswith("__not"):
        # Strip out the suffix to find the form field name (e.g., 'city')
        filter_name = param.replace("__not", "")

        # Check if this field exists in your EventsFilter configuration
        if filter_name in declared_filters:
          # Resolve to the deep relationship path ('venue__city_id')
          orm_field_path = declared_filters[filter_name].field_name
        else:
          # Fallback to the parameter name if it isn't explicitly configured
          orm_field_path = filter_name

        # 3. Apply the database exclusion safely using the correct ORM pathway
        queryset = queryset.exclude(**{orm_field_path: value})

    return queryset


class DataTablesFilterBackend(BaseFilterBackend):
  def get_sb_filter(
    self,
    column: str | None,
    condition: str | None,
    value: str | None,
    value2: str | None,
    sb_type: str | None,
  ) -> Q | None:
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

    if condition:
      return filter_types.get(condition)

    return None

  def get_final_field(self, model: Model, path: str):
    """Traverses the model __ path and returns the final Django field object."""
    parts = path.split("__")

    for i, part in enumerate(parts):
      try:
        field = model._meta.get_field(part)  # noqa: SLF001
        # If there are more parts and this is a relation, move to the next model
        if i < len(parts) - 1 and field.is_relation:
          model = field.related_model  # type: ignore
        else:
          return field
      except FieldDoesNotExist:
        return None

    return None

  def get_param(self, request: Request, param: str, default=None) -> str | None:
    return request.query_params.get(param, default)

  def parse_query(self, request: Request, view: APIView):
    ret = {}
    ret["fields"] = self.get_fields(request)
    ret["search_value"] = self.get_param(request, "search[value]")
    ret["search_regex"] = self.get_param(request, "search[regex]") == "true"
    return ret

  def get_ordering_fields(self, request, view, fields):
    order_list = []
    i = 0

    while True:
      col = f"order[{i}]"
      col_idx_param = self.get_param(request, f"{col}[column]")

      if col_idx_param is None:
        break

      try:
        field = fields[int(col_idx_param)]
      except IndexError:
        i += 1
        continue
      if not field["orderable"]:
        i += 1
        continue

      direction = self.get_param(request, f"{col}[dir]", "asc")
      order = F(f"{field['order_value']}").asc(nulls_last=True)

      if direction == "desc":
        order = F(f"{field['order_value']}").desc(nulls_last=True)

      order_list.append(order)
      i += 1

    return order_list

  def get_fields(self, request):
    fields = []
    i = 0

    while True:
      col = f"columns[{i}]"
      name = self.get_param(request, f"{col}[name]")

      if name is None:
        break

      field = [f.strip() for f in name.replace(".", "__").split(",")]

      config = {
        "name": field,
        "data": self.get_param(request, f"{col}[data]"),
        "searchable": self.get_param(request, f"{col}[searchable]") == "true",
        "orderable": self.get_param(request, f"{col}[orderable]") == "true",
        "order_value": field[0],
        "order_dir": self.get_param(
          request,
          f"order[{i}][dir]",
        ),
        "search_value": self.get_param(
          request,
          f"{col}[search][value]",
        ),
        "search_regex": self.get_param(
          request,
          f"{col}[search][regex]",
        )
        == "true",
        "sb_criteria": self.get_param(
          request,
          "[searchBuilder][logic]",
        ),
      }

      fields.append(config)
      i += 1

    return fields

  def is_valid_regex(self, regex: str):
    """Helper function that checks regex for validity."""
    try:
      re.compile(regex)
    except re.error:
      return False
    else:
      return True

  def check_renderer_format(self, request):
    return request.accepted_renderer.format == "custom"

  def filter_queryset(self, request: Request, queryset: QuerySet, view: APIView):

    if not self.check_renderer_format(request):
      return queryset

    query = self.parse_query(request, view)
    fields = query["fields"]

    search_value = query["search_value"]
    search_regex = query["search_regex"]

    is_filtered = False
    global_q = Q()
    column_q = Q()
    search_type = "icontains"

    if search_regex:
      search_type = "iregex"

    for config in fields:
      if not config["searchable"]:
        continue

      if search_value:
        is_filtered = True

        for field in config["name"]:
          lookup = f"{field}__{search_type}"

          try:
            field_obj = self.get_final_field(queryset.model, field)  # type: ignore

            if isinstance(field_obj, (CharField, TextField)):
              lookup = f"{field}__unaccent__{search_type}"

          except FieldDoesNotExist:
            continue

          global_q |= Q(**{lookup: search_value})

      if config["search_value"]:
        is_filtered = True

        if config["search_regex"]:
          search_type = "iregex"

        for field in config["name"]:
          lookup = f"{field}__{search_type}"

          try:
            field_obj = self.get_final_field(queryset.model, field)  # type: ignore

            if isinstance(field_obj, (CharField, TextField)):
              lookup = f"{field}__unaccent__{search_type}"

          except FieldDoesNotExist:
            continue

          column_q &= Q(**{lookup: config["search_value"]})

    # --- 3. ORDERING LOGIC ---
    order_list = self.get_ordering_fields(request, view, fields)

    sb_index = 0
    sb_filter = Q()

    # searchbuilder
    while True:
      searchbuilder_prefix = f"searchBuilder[criteria][{sb_index}]"

      col_idx_param = self.get_param(
        request,
        f"{searchbuilder_prefix}[origData]",
      )

      criteria = self.get_param(request, "searchBuilder[logic]")

      if not criteria:
        break

      if col_idx_param is None:
        break

      name = next(c for c in fields if c["data"] == col_idx_param)

      for field in name["name"]:
        sb_field_filter = self.get_sb_filter(
          column=field,
          condition=self.get_param(
            request,
            f"{searchbuilder_prefix}[condition]",
          ),
          value=self.get_param(request, f"{searchbuilder_prefix}[value1]"),
          value2=self.get_param(request, f"{searchbuilder_prefix}[value2]"),
          sb_type=self.get_param(
            request,
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

    if order_list:
      return queryset.order_by(*order_list).distinct()

    return queryset


class ArchiveFilter(dj_filters.FilterSet):
  event = dj_filters.NumberFilter(field_name="event_id", label="event")
  date = dj_filters.CharFilter(field_name="event__event_date", label="event date")


class BootlegFilter(dj_filters.FilterSet):
  archive = dj_filters.BooleanFilter(
    field_name="archive",
    lookup_expr="isnull",
    label="Has Archive.org upload",
  )


class CitiesFilter(dj_filters.FilterSet):
  id = dj_filters.NumberFilter(lookup_expr="exact")
  name = dj_filters.CharFilter(lookup_expr="istartswith", label="Name")


class CoversFilter(dj_filters.FilterSet):
  event = dj_filters.NumberFilter(field_name="event")


class VenuesFilter(dj_filters.FilterSet):
  id = dj_filters.CharFilter(lookup_expr="exact")
  city = dj_filters.NumberFilter(field_name="city_id", lookup_expr="exact")
  state = dj_filters.NumberFilter(field_name="state_id", lookup_expr="exact")
  country = dj_filters.NumberFilter(field_name="country_id", lookup_expr="exact")
  name = dj_filters.CharFilter(lookup_expr="istartswith", label="name")


class EventRunFilter(dj_filters.FilterSet):
  id = dj_filters.NumberFilter(lookup_expr="exact")

  start_date = dj_filters.DateTimeFilter(
    field_name="first_event__date",
    lookup_expr="gte",
    label="start date",
  )

  end_date = dj_filters.DateTimeFilter(
    field_name="last_event__date",
    lookup_expr="lte",
    label="end date",
  )

  class Meta:
    model = models.Runs
    fields = ["start_date", "end_date", "id"]


class EventsFilter(dj_filters.FilterSet):
  time_frame = dj_filters.ChoiceFilter(
    choices=[("latest", "Latest"), ("upcoming", "Upcoming")],
    method="filter_time_frame",
    label="Filter events by time frame",
  )

  year = dj_filters.CharFilter(
    field_name="event_id",
    lookup_expr="startswith",
    label="year",
  )

  id = dj_filters.NumberFilter(lookup_expr="exact")

  type = dj_filters.BaseInFilter(
    field_name="event_type__type_id",
    lookup_expr="exact",
    method="filter_by_event_type",
  )

  def filter_by_event_type(self, queryset, name, value):
    if type(value) == str:
      value = int(value)

      return queryset.filter(event_type__type_id=value)

    if type(value) == list:
      return queryset.filter(event_type__type_id__in=[int(x) for x in value])

    return queryset

  tag = dj_filters.BaseInFilter(
    field_name="event_tag__tag_id",
    lookup_expr="exact",
    label="event tag id",
    method="filter_by_tag",
  )

  tag_text = dj_filters.CharFilter(
    field_name="event_tag__tag__name",
    lookup_expr="icontains",
  )

  def filter_by_tag(self, queryset, name, value):
    if type(value) == str:
      value = int(value)

      return queryset.filter(event_tag__tag_id=value)

    if type(value) == list:
      return queryset.filter(event_tag__tag_id__in=[int(x) for x in value])

    return queryset

  start_date = dj_filters.DateTimeFilter(
    field_name="date",
    lookup_expr="gte",
    label="start date",
  )

  end_date = dj_filters.DateTimeFilter(
    field_name="date",
    lookup_expr="lte",
    label="end date",
  )

  day_of_week = dj_filters.NumberFilter(
    field_name="date__week_day",
    lookup_expr="exact",
    label="day of week",
  )

  date = dj_filters.CharFilter(field_name="date", lookup_expr="startswith")

  month = dj_filters.NumberFilter(
    field_name="date__month",
    lookup_expr="exact",
    label="month",
  )

  day = dj_filters.NumberFilter(
    field_name="date__day",
    lookup_expr="exact",
    label="day",
  )

  venue = dj_filters.NumberFilter(
    method="filter_by_venue_or_detail",
    label="venue",
  )

  venue_detail = dj_filters.CharFilter(
    field_name="venue__detail",
    lookup_expr="icontains",
    label="venue detail",
  )

  city = dj_filters.NumberFilter(
    field_name="venue__city_id",
    lookup_expr="exact",
    label="city",
  )

  state = dj_filters.NumberFilter(
    field_name="venue__city__state_id",
    lookup_expr="exact",
    label="state",
  )
  country = dj_filters.NumberFilter(
    field_name="venue__city__country_id",
    lookup_expr="exact",
    label="country",
  )

  continent = dj_filters.NumberFilter(
    field_name="venue__city__country__continent_id",
    lookup_expr="exact",
    label="continent",
  )

  run = dj_filters.NumberFilter(
    field_name="run_id",
    lookup_expr="exact",
    label="event run",
  )
  artist = dj_filters.NumberFilter(
    field_name="artist_id",
    lookup_expr="exact",
    label="artist",
  )
  tour = dj_filters.NumberFilter(
    field_name="tour_id",
    lookup_expr="exact",
    label="tour",
  )
  leg = dj_filters.NumberFilter(
    field_name="leg_id",
    lookup_expr="exact",
    label="tour_leg",
  )

  relation = dj_filters.BaseInFilter(
    field_name="onstage_event__relation_id",
    label="onstage relation",
  )

  band = dj_filters.BaseInFilter(
    field_name="onstage_event__band_id",
    distinct=True,
    label="onstage band",
  )

  user = dj_filters.NumberFilter(
    field_name="user_event__user_id",
  )

  search = dj_filters.CharFilter(
    method="filter_fulltext_search",
  )

  song = dj_filters.NumberFilter(
    field_name="setlist_event__song_id",
    lookup_expr="exact",
    label="song",
  )

  def filter_fulltext_search(self, queryset, name, value):
    if not value:
      return queryset

    parsed_year = None
    parsed_month = None
    parsed_day = None

    try:
      # Trick to detect if a day/month/year was explicitly provided:
      # Parse twice with different defaults. If the value changes between parses,
      # it means dateutil used the default fallback rather than user input.
      parsed_date_1 = parser.parse(
        value,
        fuzzy=True,
        default=datetime.datetime(1, 1, 1),
      )
      parsed_date_2 = parser.parse(
        value,
        fuzzy=True,
        default=datetime.datetime(2, 2, 2),
      )

      if parsed_date_1.year == parsed_date_2.year:
        parsed_year = parsed_date_1.year
      if parsed_date_1.month == parsed_date_2.month:
        parsed_month = parsed_date_1.month
      if parsed_date_1.day == parsed_date_2.day:
        parsed_day = parsed_date_1.day

    except (ValueError, OverflowError):
      pass

    # Build date conditions based on specificity
    date_conditions = Q()

    if parsed_year and parsed_month and parsed_day:
      # TIER 1: Exact Date Match (e.g., "1977-02-15")
      date_conditions = Q(
        date__year=parsed_year,
        date__month=parsed_month,
        date__day=parsed_day,
      )
    elif parsed_year and parsed_month:
      # TIER 2: Exact Month/Year Match (e.g., "Feb 1977")
      date_conditions = Q(date__year=parsed_year, date__month=parsed_month)
    elif parsed_year:
      # TIER 3: Exact Year Match (e.g., "1977")
      date_conditions = Q(date__year=parsed_year)

    query = SearchQuery(value, search_type="websearch")

    vector = (
      SearchVector("event_id", weight="B")
      + SearchVector("date", weight="A")
      + SearchVector("date__day", weight="B")
      + SearchVector("early_late", weight="B")
      + SearchVector("artist__name", weight="C")
      + SearchVector("venue__name", weight="B")
      + SearchVector("venue__city__name", weight="B")
      + SearchVector("run__name", weight="D")
    )

    # If the user provided a full exact date, boost it to the very top (similar to Event ID)
    exact_date_match = Q()

    # Build the conditional ranking cases dynamically
    ranking_cases = [
      When(event_id__istartswith=value, then=Value(1.0)),
    ]

    # Only inject the exact date boost if we actually have a full valid date
    if parsed_year and parsed_month and parsed_day:
      exact_date_match = Q(
        date__year=parsed_year,
        date__month=parsed_month,
        date__day=parsed_day,
      )
      ranking_cases.append(When(exact_date_match, then=Value(1.0)))

    event_exclude_filter = Q(
      Q(tour__num_songs=0)
      | Q(
        setlist_certainty__in=["Unknown", "Probable"],
      )
      | Q(public=False),
    )

    return (
      queryset.annotate(
        search=vector,
        rank=Case(
          *ranking_cases,  # Unpack the valid cases here safely
          default=SearchRank(vector, query, weights=[0.1, 0.3, 0.6, 1.0]),
        ),
      )
      .exclude(event_exclude_filter)
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

  def filter_by_venue_or_detail(self, queryset, name, value):
    if not value:
      return queryset

    try:
      return queryset.filter(
        Q(venue_id=value) | Q(venue__parent=value),
      )
    except models.Venues.DoesNotExist:
      # Fallback if the venue ID provided doesn't exist
      pass

    # 3. If no detail exists or venue wasn't found, just filter by the ID
    return queryset.filter(venue_id=value)

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


class AdvSearchFilter(dj_filters.FilterSet):
  year = dj_filters.CharFilter(
    field_name="event_id",
    lookup_expr="startswith",
    label="year",
  )

  type = ModelMultipleChoiceFilter(
    field_name="event_type__type_id",
    to_field_name="id",
    queryset=models.Types.objects.all(),
  )

  tag = ModelMultipleChoiceFilter(
    field_name="event_tag__tag_id",
    to_field_name="id",
    queryset=models.Tags.objects.all(),
  )

  start_date = dj_filters.DateFilter(
    field_name="date",
    lookup_expr="gte",
    label="start date",
  )

  end_date = dj_filters.DateFilter(
    field_name="date",
    lookup_expr="lte",
    label="end date",
  )

  day_of_week = dj_filters.NumberFilter(
    field_name="date__week_day",
    lookup_expr="exact",
    label="day of week",
  )

  date = dj_filters.CharFilter(field_name="date", lookup_expr="startswith")

  month = dj_filters.NumberFilter(
    field_name="date__month",
    lookup_expr="exact",
    label="month",
  )

  day = dj_filters.NumberFilter(
    field_name="date__day",
    lookup_expr="exact",
    label="day",
  )

  venue = dj_filters.NumberFilter(
    method="filter_by_venue_or_detail",
    label="venue",
  )

  venue_detail = dj_filters.CharFilter(
    field_name="venue__detail",
    lookup_expr="icontains",
    label="venue detail",
  )

  city = dj_filters.NumberFilter(
    field_name="venue__city_id",
    lookup_expr="exact",
    label="city",
  )

  state = dj_filters.NumberFilter(
    field_name="venue__city__state_id",
    lookup_expr="exact",
    label="state",
  )
  country = dj_filters.NumberFilter(
    field_name="venue__city__country_id",
    lookup_expr="exact",
    label="country",
  )
  continent = dj_filters.NumberFilter(
    field_name="venue__city__country__continent_id",
    lookup_expr="exact",
    label="continent",
  )
  run = dj_filters.NumberFilter(
    field_name="run_id",
    lookup_expr="exact",
    label="event run",
  )
  artist = dj_filters.NumberFilter(
    field_name="artist_id",
    lookup_expr="exact",
    label="artist",
  )
  tour = dj_filters.NumberFilter(
    field_name="tour_id",
    lookup_expr="exact",
    label="tour",
  )
  leg = dj_filters.NumberFilter(
    field_name="leg_id",
    lookup_expr="exact",
    label="tour_leg",
  )

  relation = dj_filters.BaseInFilter(
    field_name="onstage_event__relation_id",
    label="onstage relation",
  )

  band = dj_filters.BaseInFilter(
    field_name="onstage_event__band_id",
    distinct=True,
    label="onstage band",
  )

  user = dj_filters.NumberFilter(
    field_name="user_event__user_id",
  )

  song = dj_filters.NumberFilter(
    field_name="setlist_event__song_id",
    lookup_expr="exact",
    label="song",
  )

  def filter_by_venue_or_detail(self, queryset, name, value):
    if not value:
      return queryset

    try:
      return queryset.filter(
        Q(venue_id=value) | Q(venue__parent=value),
      )
    except models.Venues.DoesNotExist:
      # Fallback if the venue ID provided doesn't exist
      pass

    # 3. If no detail exists or venue wasn't found, just filter by the ID
    return queryset.filter(venue_id=value)

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


class OnstageFilter(dj_filters.FilterSet):
  relation = dj_filters.NumberFilter(
    field_name="relation_id",
    lookup_expr="exact",
    label="relation",
  )

  band = dj_filters.NumberFilter(field_name="band_id", lookup_expr="exact")

  event = dj_filters.NumberFilter(
    field_name="event_id",
    lookup_expr="exact",
    label="event_id",
  )


class OnstageBandFilter(dj_filters.FilterSet):
  relation = dj_filters.NumberFilter(
    field_name="relation_id",
    lookup_expr="exact",
    label="relation id",
  )

  band = dj_filters.NumberFilter(
    field_name="band_id",
    lookup_expr="exact",
    label="band id",
  )

  first = dj_filters.NumberFilter(
    field_name="first_event_id",
    lookup_expr="exact",
    label="event_id",
  )

  last = dj_filters.NumberFilter(
    field_name="last_event_id",
    lookup_expr="exact",
    label="event_id",
  )


class ReleaseTracksFilter(dj_filters.FilterSet):
  release = dj_filters.CharFilter(field_name="release_id", lookup_expr="exact")


class RelationFilter(dj_filters.FilterSet):
  id = dj_filters.NumberFilter(lookup_expr="exact")
  name = dj_filters.CharFilter(lookup_expr="istartswith")

  start_date = dj_filters.DateTimeFilter(
    field_name="start_date",
    lookup_expr="gte",
    label="start date",
  )

  start_date_end = dj_filters.DateTimeFilter(
    field_name="start_date",
    lookup_expr="lte",
    label="end date",
  )

  month = dj_filters.NumberFilter(
    field_name="start_date__month",
    lookup_expr="exact",
    label="month",
  )

  day = dj_filters.NumberFilter(
    field_name="start_date__day",
    lookup_expr="exact",
    label="day",
  )

  show_cal = dj_filters.BooleanFilter(
    method="filter_show_cal",
    label="show on calendar",
  )

  def filter_show_cal(self, queryset, name, value):
    return queryset.filter(show_cal=value)


class BandsFilter(dj_filters.FilterSet):
  id = dj_filters.NumberFilter(lookup_expr="exact")
  name = dj_filters.CharFilter(lookup_expr="istartswith")


class ReleaseFilter(dj_filters.FilterSet):
  id = dj_filters.NumberFilter(lookup_expr="exact")
  type = dj_filters.CharFilter(lookup_expr="icontains")
  start_date = dj_filters.DateTimeFilter(
    field_name="date",
    lookup_expr="gte",
    label="start date",
  )
  end_date = dj_filters.DateTimeFilter(
    field_name="date",
    lookup_expr="lte",
    label="end date",
  )

  year = dj_filters.NumberFilter(
    field_name="date__year",
    label="year",
  )

  current_year = dj_filters.BooleanFilter(
    method="include_current_year",
    label="include current year?",
  )

  month = dj_filters.NumberFilter(
    field_name="date__month",
    label="month",
  )

  day = dj_filters.NumberFilter(field_name="date__day", label="day")

  def include_current_year(self, queryset, name, value):
    if value:
      return queryset.filter(date__year=date.year)

    return queryset.exclude(date__year=date.year)


class SetlistStatsFilter(dj_filters.FilterSet):
  id = dj_filters.NumberFilter(lookup_expr="exact")

  class Meta:
    model = models.SetlistStats
    fields = "__all__"


class SetlistFilter(dj_filters.FilterSet):
  event = dj_filters.NumberFilter(
    field_name="event_id",
    lookup_expr="exact",
    label="event",
  )

  run = dj_filters.NumberFilter(
    field_name="event__run_id",
    lookup_expr="exact",
    label="event run",
  )

  leg = dj_filters.NumberFilter(
    field_name="event__leg_id",
    lookup_expr="exact",
    label="event tour leg",
  )

  tour = dj_filters.NumberFilter(
    field_name="event__tour_id",
    lookup_expr="exact",
    label="tour",
  )

  song = dj_filters.NumberFilter(
    field_name="song_id",
    lookup_expr="exact",
    label="song",
    distinct=True,
  )

  venue = dj_filters.NumberFilter(
    field_name="event__venue_id",
    lookup_expr="exact",
    label="venue",
  )

  city = dj_filters.NumberFilter(
    field_name="event__venue__city_id",
    lookup_expr="exact",
    label="city",
  )

  state = dj_filters.NumberFilter(
    field_name="event__venue__city__state_id",
    lookup_expr="exact",
    label="state",
  )

  country = dj_filters.NumberFilter(
    field_name="event__venue__city__country_id",
    lookup_expr="exact",
    label="country",
  )

  user = dj_filters.NumberFilter(
    field_name="event__user_event__user_id",
    lookup_expr="exact",
    label="user",
  )

  debut = dj_filters.BooleanFilter(label="debut")
  premiere = dj_filters.BooleanFilter(label="premiere")
  sign_request = dj_filters.BooleanFilter(label="sign_request")
  nobruce = dj_filters.BooleanFilter(label="bruce not present")

  def filter_song_num(self, queryset, name, value):
    lookup = f"{name}__isnull"
    return queryset.filter(**{lookup: False})

  def filter_show_only(self, queryset, name, value):
    lookup = "set_name__in"

    lookup = Q(set_name__in=models.SetTypes.valid_sets()) & Q(
      event__public=True,
    )

    return queryset.filter(lookup)

  def filter_song_list(self, queryset, name, value):
    return queryset.exclude(song_id__in=[689, 1021, 514])

  def filter_bv(self, queryset, name, value):
    assert self.data is not None
    event = self.data.get("event")

    check = bv_models.Entries.objects.filter(event=event)

    if check.exists():
      return queryset.exclude(event=event, song_id__in=check.values_list("song"))

    return queryset

  song_num = dj_filters.BooleanFilter(
    method="filter_song_num",
    label="has song num",
  )

  bv = dj_filters.BooleanFilter(
    method="filter_bv",
    label="no entry song",
  )

  show_only = dj_filters.BooleanFilter(
    method="filter_show_only",
    label="show only",
  )

  hide_non_songs = dj_filters.BooleanFilter(
    method="filter_song_list",
    label="hide non songs",
  )

  song = dj_filters.CharFilter(field_name="song__name", lookup_expr="icontains")

  class Meta:
    model = models.Setlists
    fields = "__all__"


class SetlistEntryFilter(dj_filters.FilterSet):
  event = dj_filters.NumberFilter(
    field_name="event_id",
    lookup_expr="exact",
    label="event_id",
  )

  run = dj_filters.NumberFilter(
    field_name="event__run_id",
    lookup_expr="exact",
    label="event run",
  )

  leg = dj_filters.NumberFilter(
    field_name="event__leg_id",
    lookup_expr="exact",
    label="tour leg",
  )
  tour = dj_filters.NumberFilter(
    field_name="event__tour_id",
    lookup_expr="exact",
    label="tour",
  )
  venue = dj_filters.NumberFilter(
    field_name="event__venue_id",
    lookup_expr="exact",
    label="venue",
  )
  city = dj_filters.NumberFilter(
    field_name="event__venue__city_id",
    lookup_expr="exact",
    label="city",
  )
  state = dj_filters.NumberFilter(
    field_name="event__venue__state_id",
    lookup_expr="exact",
    label="state",
  )
  country = dj_filters.NumberFilter(
    field_name="event__venue__country_id",
    lookup_expr="exact",
    label="country",
  )


class SetlistSongsFilter(dj_filters.FilterSet):
  event = dj_filters.NumberFilter(
    field_name="event_id",
    lookup_expr="exact",
    label="event",
  )

  run = dj_filters.NumberFilter(
    field_name="event__run_id",
    lookup_expr="exact",
    label="event run",
  )

  year = dj_filters.NumberFilter(
    field_name="event__date__year",
    lookup_expr="exact",
    label="year",
  )

  leg = dj_filters.NumberFilter(
    field_name="event__leg_id",
    lookup_expr="exact",
    label="tour leg",
  )
  tour = dj_filters.NumberFilter(
    field_name="event__tour_id",
    lookup_expr="exact",
    label="tour",
  )
  venue = dj_filters.NumberFilter(
    field_name="event__venue_id",
    lookup_expr="exact",
    label="venue",
  )

  city = dj_filters.NumberFilter(
    field_name="event__venue__city_id",
    lookup_expr="exact",
    label="city",
  )

  state = dj_filters.NumberFilter(
    field_name="event__venue__city__state_id",
    lookup_expr="exact",
    label="state",
  )

  country = dj_filters.NumberFilter(
    field_name="event__venue__city__country_id",
    lookup_expr="exact",
    label="country",
  )

  user = dj_filters.NumberFilter(
    field_name="event__user_event__user_id",
    lookup_expr="exact",
    label="User ID",
  )

  user_unseen = dj_filters.NumberFilter(
    field_name="event__user_event__user_id",
    method="filter_unseen",
    label="Show songs this user hasn't seen",
  )

  user_rare = dj_filters.BooleanFilter(
    field_name="song__num_plays_public",
    method="filter_rare",
    label="Rare (<100 plays)",
  )

  public_plays = dj_filters.NumberFilter(
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
      "song_id",
      flat=True,
    )

    return queryset.exclude(song_id__in=songs).filter(song__num_plays_public__gt=0)


class IncludedFilter(dj_filters.FilterSet):
  snippet = dj_filters.NumberFilter(field_name="snippet_id", lookup_expr="exact")

  song = dj_filters.NumberFilter(
    field_name="setlist__song_id",
    lookup_expr="exact",
    label="song",
  )

  unique = dj_filters.BooleanFilter(
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
        .values_list("snippet_id")
      )

      return queryset.filter(snippet_id__in=unique_ids).distinct("snippet_id")

    return queryset


class SnippetFilter(dj_filters.FilterSet):
  snippet = dj_filters.NumberFilter(field_name="snippet_id", lookup_expr="exact")

  song = dj_filters.NumberFilter(
    field_name="setlist__song_id",
    lookup_expr="exact",
    label="song",
  )

  unique = dj_filters.BooleanFilter(
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


class StateFilter(dj_filters.FilterSet):
  id = dj_filters.NumberFilter(lookup_expr="exact")
  name = dj_filters.CharFilter(lookup_expr="istartswith")


class CountryFilter(dj_filters.FilterSet):
  id = dj_filters.NumberFilter(lookup_expr="exact")
  name = dj_filters.CharFilter(lookup_expr="istartswith")


class TourFilter(dj_filters.FilterSet):
  id = dj_filters.NumberFilter(lookup_expr="exact")
  name = dj_filters.CharFilter(field_name="name", lookup_expr="istartswith")
  band = dj_filters.CharFilter(field_name="band__name", lookup_expr="icontains")


class TourLegFilter(dj_filters.FilterSet):
  tour = dj_filters.NumberFilter(field_name="tour_id", lookup_expr="exact")
  name = dj_filters.CharFilter(lookup_expr="icontains")


class SongsPageFilter(dj_filters.FilterSet):
  song = dj_filters.NumberFilter(field_name="id__song_id", lookup_expr="exact")


class SongsFilter(dj_filters.FilterSet):
  name = dj_filters.CharFilter(field_name="name", lookup_expr="iregex")
  lyrics = dj_filters.BooleanFilter()


class SetlistNoteFilter(dj_filters.FilterSet):
  id = dj_filters.NumberFilter(field_name="setlist_id", lookup_expr="exact")
  event = dj_filters.NumberFilter(
    field_name="event_id",
    lookup_expr="exact",
    label="event_id",
  )
  note = dj_filters.CharFilter(lookup_expr="icontains")


class UserAttendedShowsFilter(dj_filters.FilterSet):
  user = dj_filters.NumberFilter(field_name="user", lookup_expr="exact")

  event = dj_filters.NumberFilter(
    field_name="event__id",
    lookup_expr="exact",
    label="event_id",
  )


class TypeFilter(dj_filters.FilterSet):
  id = dj_filters.NumberFilter(lookup_expr="exact")
  name = dj_filters.CharFilter(lookup_expr="icontains")


class EventTypeFilter(dj_filters.FilterSet):
  id = dj_filters.NumberFilter(field_name="type_id", lookup_expr="exact")
  name = dj_filters.CharFilter(
    field_name="type__name",
    lookup_expr="icontains",
  )


class UserAlbumBreakdownFilter(dj_filters.FilterSet):
  user = dj_filters.NumberFilter(
    field_name="event__user_event__user_id",
    lookup_expr="exact",
    label="user",
  )


class YearSongBreakdownFilter(dj_filters.FilterSet):
  song = dj_filters.NumberFilter(
    field_name="song_id",
    lookup_expr="exact",
  )


class TagFilter(dj_filters.FilterSet):
  id = dj_filters.NumberFilter(lookup_expr="exact")
  name = dj_filters.CharFilter(lookup_expr="icontains")


class EventTagFilter(dj_filters.FilterSet):
  event = dj_filters.NumberFilter(field_name="event_id", lookup_expr="exact")
  tag = dj_filters.NumberFilter(field_name="tag_id", lookup_expr="exact")


class ArticleFilter(dj_filters.FilterSet):
  # Full-Text Search filter using the generated fts_vector column
  q = dj_filters.CharFilter(method="filter_by_fts", label="Search (FTS)")

  # Exact and multiple choice filters
  category = dj_filters.ChoiceFilter(choices=models.Articles.ArticleCategory.choices)
  author = dj_filters.CharFilter(lookup_expr="icontains")

  date_after = dj_filters.NumberFilter(
    field_name="published_at__year",
    lookup_expr="gte",
  )

  date_before = dj_filters.NumberFilter(
    field_name="published_at__year",
    lookup_expr="lte",
  )

  class Meta:
    model = models.Articles
    fields = [
      "q",
      "category",
      "author",
      "date_after",
      "date_before",
    ]

  def filter_by_fts(self, queryset, name, value):
    if not value:
      return queryset

    query = SearchQuery(value, config="english")

    return (
      queryset.filter(fts_vector=query)
      .annotate(
        # Checks if title contains the raw search term (icontains)
        # or matches via search query
        in_title=Q(title__icontains=value),
        rank=SearchRank("fts_vector", query, weights=[0.1, 0.2, 0.5, 1.0]),
      )
      .order_by("-in_title", "-rank")
    )


class SetlistBreakdownFilter(dj_filters.FilterSet):
  event = dj_filters.NumberFilter(field_name="event_id", lookup_expr="exact")
  user = dj_filters.NumberFilter(
    field_name="event__user_event__user_id",
    lookup_expr="exact",
  )
