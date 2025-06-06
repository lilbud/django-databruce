from .forms import EventSearch


def base_data(request):  # noqa: ARG001
    data = {}
    data["form"] = EventSearch()
    return data
