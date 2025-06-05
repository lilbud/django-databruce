from databruce.forms import EventSearch


def base_data(request):  # noqa: ARG001
    data = {}
    data["my_form"] = EventSearch()
    return data
