import calendar

from django import template
from django.db.models import Count

from databruce import models

register = template.Library()


@register.simple_tag
def get_months():
    return [calendar.month_name[i] for i in range(1, 13)]


@register.filter(name="days")
def days(number: int):
    return range(1, number + 1)


@register.filter(name="get_day")
def get_day_from_num(num: int):
    days = {
        1: "Sunday",
        2: "Monday",
        3: "Tuesday",
        4: "Wednesday",
        5: "Thursday",
        6: "Friday",
        7: "Saturday",
    }

    return days.get(int(num))


@register.filter(name="get_month")
def get_month_from_num(num: int):
    return calendar.month_name[int(num)]


@register.filter(name="get_city")
def get_city(city: int):
    return models.Cities.objects.get(id=city).name


@register.filter(name="get_state")
def get_state(state: int):
    return models.States.objects.get(id=state).name


@register.filter(name="get_country")
def get_country(country: int):
    return models.Countries.objects.get(id=country).name


@register.filter(name="get_relation")
def get_relation(relation: int):
    return models.Relations.objects.get(id=relation).name


@register.filter(name="get_band")
def get_band(band: int):
    return models.Bands.objects.get(id=band).name


@register.simple_tag
def weekdays():
    return {
        1: "Sunday",
        2: "Monday",
        3: "Tuesday",
        4: "Wednesday",
        5: "Thursday",
        6: "Friday",
        7: "Saturday",
    }


@register.filter(name="get_ordinal")
def make_ordinal(n: int):
    """Convert an integer into its ordinal representation::.

    make_ordinal(0)   => '0th'
    make_ordinal(3)   => '3rd'
    make_ordinal(122) => '122nd'
    make_ordinal(213) => '213th'
    """
    n = int(n)
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]
    return str(n) + suffix
