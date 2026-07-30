from rest_framework.pagination import LimitOffsetPagination
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
                    return int(request.query_params[self.default_limit_param])
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
        if renderer_context and renderer_context.get("format") == "custom":
            if data is not None and "data" not in data:
                data = {"data": data}

        return super().render(data, accepted_media_type, renderer_context)
