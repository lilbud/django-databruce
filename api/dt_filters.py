import operator
import re
from functools import reduce

from django.db.models import Q, QuerySet
from rest_framework.filters import BaseFilterBackend
from rest_framework.request import Request
from rest_framework.views import APIView


def is_valid_regex(regex):
    """Helper function that checks regex for validity."""
    try:
        re.compile(regex)
    except re.error:
        return False
    else:
        return True


def f_search_q(f, search_value: str, search_regex=False):  # noqa: FBT002
    """Helper function that returns a Q-object for a search value."""
    qs = []

    if search_value and search_value != "false":
        if search_regex:
            if is_valid_regex(search_value):
                for x in f["name"]:
                    qs.append(Q(**{f"{x}__iregex": search_value}))
        else:
            for x in f["name"]:
                qs.append(Q(**{f"{x}__icontains": search_value}))

    return reduce(operator.or_, qs, Q())


class DataTablesBaseFilterBackend(BaseFilterBackend):
    """Base class for definining your own DatatablesFilterBackend classes."""

    def check_renderer_format(self, request):
        return request.accepted_renderer.format == "custom"

    def get_param(self, request: Request, param: str, default=None) -> str | None:
        return request.query_params.get(param, default)

    def parse_datatables_query(self, request: Request, view: APIView):
        """Parse request.query_params into a list of fields and orderings and global search parameters (value and regex)."""
        ret = {}
        ret["fields"] = self.get_fields(request)
        ret["search_value"] = self.get_param(request, "search[value]")
        ret["search_regex"] = self.get_param(request, "search[regex]") == "true"
        return ret

    def get_fields(self, request):
        """Called by parse_query_params to get the list of fields."""
        fields = []
        i = 0
        while True:
            col = "columns[%d][%s]"
            data = self.get_param(request, col % (i, "data"))
            if data == "":  # null or empty string on datatables (JS) side
                fields.append({"searchable": False, "orderable": False})
                i += 1
                continue
            # break out only when there are no more fields to get.
            if data is None:
                break
            name = self.get_param(request, col % (i, "name"))
            if not name:
                name = data
            search_col = col % (i, "search")
            # to be able to search across multiple fields (e.g. to search
            # through concatenated names), we create a list of the name field,
            # replacing dot notation with double-underscores and splitting
            # along the commas.
            field = {
                "name": [n.lstrip() for n in name.replace(".", "__").split(",")],
                "data": data,
                "searchable": self.get_param(
                    request,
                    col % (i, "searchable"),
                )
                == "true",
                "orderable": self.get_param(
                    request,
                    col % (i, "orderable"),
                )
                == "true",
                "search_value": self.get_param(
                    request,
                    "{}[{}]".format(search_col, "value"),
                ),
                "search_regex": self.get_param(
                    request,
                    "{}[{}]".format(search_col, "regex"),
                )
                == "true",
            }
            fields.append(field)

            # print(field)
            i += 1

        return fields

    def get_ordering_fields(self, request: Request, view: APIView, fields):  # noqa: ARG002
        """Called by parse_query_params to get the ordering.

        return value must be a list of tuples.
        (field, dir)

        field is the field to order by and dir is the direction of the
        ordering ('asc' or 'desc').

        """
        ret = []
        i = 0
        while True:
            col = "order[%d][%s]"
            idx = self.get_param(request, col % (i, "column"))
            if idx is None:
                break
            try:
                field = fields[int(idx)]
            except IndexError:
                i += 1
                continue
            if not field["orderable"]:
                i += 1
                continue
            dir = self.get_param(request, col % (i, "dir"), "asc")
            ret.append((field, dir))
            i += 1

        print(ret)
        return ret

    def set_count_before(self, view, total_count):
        view._datatables_total_count = total_count  # noqa: SLF001

    def set_count_after(self, view, filtered_count):
        """Called by filter_queryset to store the ordering after the filter operations."""
        view._datatables_filtered_count = filtered_count  # noqa: SLF001

    def append_additional_ordering(self, ordering, view):
        if len(ordering) and hasattr(view, "datatables_additional_order_by"):
            additional = view.datatables_additional_order_by
            # Django will actually only take the first occurrence if the
            # same column is added multiple times in an order_by, but it
            # feels cleaner to double check for duplicate anyway.
            if not any((o[1:] if o[0] == "-" else o) == additional for o in ordering):
                ordering.append(additional)


class DataTablesFilterBackend(DataTablesBaseFilterBackend):
    """Filter that works with datatables params."""

    def filter_queryset(self, request: Request, queryset: QuerySet, view: APIView):
        """Filter the queryset.

        subclasses overriding this method should make sure to do all
        necessary steps

        -  Return unfiltered queryset if accepted renderer format is
           not 'datatables' (via `check_renderer_format`)

        - store the counts before and after filtering with
          `set_count_before` and `set_count_after`

        - respect ordering (in `ordering` key of parsed datatables
          query)

        """
        if not self.check_renderer_format(request):
            return queryset

        total_count = view.get_queryset().count()  # type: ignore
        self.set_count_before(view, total_count)

        if len(getattr(view, "filter_backends", [])) > 1:
            # case of a view with more than 1 filter backend
            filtered_count_before = queryset.count()
        else:
            filtered_count_before = total_count

        datatables_query = self.parse_datatables_query(request, view)

        q = self.get_q(datatables_query)

        if q:
            queryset = queryset.filter(q).distinct()
            filtered_count = queryset.count()
        else:
            filtered_count = filtered_count_before
        self.set_count_after(view, filtered_count)

        ordering = self.get_ordering(request, view, datatables_query["fields"])
        if ordering:
            queryset = queryset.order_by(*ordering)

        return queryset

    def get_q(self, datatables_query):
        q = Q()
        initial_q = Q()
        for f in datatables_query["fields"]:
            if not f["searchable"]:
                continue
            q |= f_search_q(
                f,
                datatables_query["search_value"],
                datatables_query["search_regex"],
            )
            initial_q &= f_search_q(
                f,
                f.get("search_value"),
                f.get("search_regex", False),
            )
        q &= initial_q
        return q

    def get_ordering(self, request, view, fields):
        """Called by parse_query_params to get the ordering.

        return value must be a valid list of arguments for order_by on
        a queryset

        """
        ordering = []
        for field, dir_ in self.get_ordering_fields(request, view, fields):
            ordering.append(
                "{}{}".format(
                    "-" if dir_ == "desc" else "",
                    field["name"][0],
                ),
            )
        self.append_additional_ordering(ordering, view)
        return ordering
