from rest_framework.pagination import LimitOffsetPagination
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response


class DatatablesLimitOffsetPagination(LimitOffsetPagination):
    # Standard DataTables param names
    dt_limit_query_param = "length"
    dt_offset_query_param = "start"

    # Default DRF param names
    default_limit_param = "limit"
    default_offset_param = "offset"

    def get_limit(self, request):
        # Switch param key based on the format
        if request.accepted_renderer.format == "custom":
            self.limit_query_param = self.dt_limit_query_param

            if self.default_limit_param in request.query_params:
                try:
                    return int(request.query_params[self.default_limit_param])
                except (ValueError, TypeError):
                    pass
        else:
            self.limit_query_param = self.default_limit_param

        return super().get_limit(request)

    def get_offset(self, request):
        if request.accepted_renderer.format == "custom":
            self.offset_query_param = self.dt_offset_query_param
        else:
            self.offset_query_param = self.default_offset_param
        return super().get_offset(request)

    def get_paginated_response(self, data):
        # Only return the DataTables-specific JSON structure if format is custom
        if self.request.accepted_renderer.format == "custom":
            return Response(
                {
                    "draw": int(self.request.query_params.get("draw", 0)),
                    "recordsTotal": self.count,
                    "recordsFiltered": self.count,
                    "data": data,
                },
            )
        # Otherwise, return the standard DRF limit/offset response
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
