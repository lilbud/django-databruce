from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response


class DatatablesLimitOffsetPagination(LimitOffsetPagination):
  # Standard DataTables param names
  dt_limit_query_param = "length"
  dt_offset_query_param = "start"

  # Default DRF param names
  default_limit_param = "limit"
  default_offset_param = "offset"

  # Cap maximum returned results when pagination is "disabled" to protect your database
  max_limit = 100000

  def get_limit(self, request: Request):
    if request.accepted_renderer.format == "custom":
      self.limit_query_param = self.dt_limit_query_param

      # 1. Intercept DataTables 'All' request (-1)
      raw_limit = request.query_params.get(self.dt_limit_query_param)
      if raw_limit == "-1":
        return self.max_limit

      if self.default_limit_param in request.query_params:
        try:
          return int(request.query_params[self.default_limit_param])  # type: ignore
        except (ValueError, TypeError):
          pass
    else:
      self.limit_query_param = self.default_limit_param

    return super().get_limit(request)

  def get_offset(self, request: Request):
    if request.accepted_renderer.format == "custom":
      self.offset_query_param = self.dt_offset_query_param
    else:
      self.offset_query_param = self.default_offset_param
    return super().get_offset(request)

  def get_paginated_response(self, data):
    if self.request.accepted_renderer.format == "custom":
      return Response(
        {
          "draw": int(self.request.query_params.get("draw", 0)),
          "recordsTotal": self.count,
          "recordsFiltered": self.count,
          "data": data,
        },
      )

    return super().get_paginated_response(data)


class DatatablesRenderer(JSONRenderer):
  media_type = "application/json"
  format = "custom"  # Triggered by ?format=custom

  def render(self, data, accepted_media_type=None, renderer_context=None):
    # Only apply the "data" wrapper if this specific format was selected
    if renderer_context and renderer_context.get("format") == "custom":  # noqa: SIM102
      if data is not None and "data" not in data:
        data = {"data": data}

    return super().render(data, accepted_media_type, renderer_context)


class EnvelopeOptionalPagination(PageNumberPagination):
  page_size_query_param = "page_size"
  page_size = 10
  max_page_size = 1000

  def paginate_queryset(self, queryset, request, view=None):
    # Detect if 'all' was requested
    if request.query_params.get(self.page_size_query_param) == "all":
      # Safely get the total record count (supports querysets and standard lists)
      try:
        self.count = queryset.count()
      except (AttributeError, TypeError):
        self.count = len(queryset)

      self.request = request

      # If the database table is empty, force a minimal default size to prevent division errors
      self.page_size = max(1, self.count)

      # Mock pagination properties so get_paginated_response() has what it needs
      self.page = self
      self.has_next = lambda: False
      self.has_previous = lambda: False

      return list(queryset)

    return super().paginate_queryset(queryset, request, view)

  def get_next_link(self):
    if self.request.query_params.get(self.page_size_query_param) == "all":
      return None
    return super().get_next_link()

  def get_previous_link(self):
    if self.request.query_params.get(self.page_size_query_param) == "all":
      return None
    return super().get_previous_link()
