from .forms import EventSearch


def base_data(request):  # noqa: ARG001
    data = {}
    data["searchForm"] = EventSearch()
    return data
