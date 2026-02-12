from rest_framework.pagination import LimitOffsetPagination
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response


class DatatablesLimitOffsetPagination(LimitOffsetPagination):
    limit_query_param = "length"  # Default DataTables param
    custom_limit_query_param = "limit"  # Custom param
    offset_query_param = "start"

    def get_limit(self, request):
        # 1. Check if 'limit' is in the URL
        if self.custom_limit_query_param in request.query_params:
            try:
                return int(request.query_params[self.custom_limit_query_param])
            except (ValueError, TypeError):
                pass

        # 2. Fall back to the default 'length' (limit_query_param)
        return super().get_limit(request)

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
    format = "custom"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is not None and "data" not in data:
            data = {"data": data}

        return super().render(data, accepted_media_type, renderer_context)
