from django.conf import settings

from databruce.forms import EventSearch


def base_data(request):
    data = {}
    data["my_form"] = EventSearch()
    return data
