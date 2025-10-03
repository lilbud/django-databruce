from __future__ import annotations

import calendar
import re
import string

import markdown
from django import template
from markdown_it import MarkdownIt

from databruce import models

register = template.Library()


@register.filter(name="color")
def color(value):
    match value:
        case "No Gig" | "Rescheduled Due to Illness":
            return "text-danger"
        case "Concert":
            return "text-success-emphasis"
        case "Rehearsal" | "Recording" | "Interview":
            return "text-primary"
        case _:
            return "text-light"


@register.filter(name="type_color")
def get_event_color(event_type: str = "Concert"):
    if re.search("rescheduled|no gig", event_type, flags=re.IGNORECASE):
        return "cancelled"

    return ""


@register.filter(name="mdlink")
def md_link(note: str):
    link = re.search(r"(.*)\[(.*)\]\((.*)\)", note)

    if link:
        return re.sub("</?p>", "", markdown.markdown(note))
    return note


@register.filter(name="markdown")
def markdown_convert(note: str) -> str:
    md = MarkdownIt()
    return md.render(note.strip())


@register.filter(name="get_date")
def get_date(event: str):
    """Date to return if it is null or unknown."""
    return f"{event[0:4]}-{event[4:6]}-{event[6:8]}"


@register.filter()
def setlist_note(notes):
    return "; ".join([md_link(note.note) for note in notes])


@register.filter()
def brucebase_url(event: str):
    if int(event[-1]) > 1:
        d = dict(enumerate(string.ascii_lowercase, 1))
        return f"{event[0:4]}#{event[6:8]}{event[4:6]}{event[2:4]}{d[int(event[-1])]}"

    return f"{event[0:4]}#{event[6:8]}{event[4:6]}{event[2:4]}"


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
        8: "Not Sunday",
        9: "Not Monday",
        10: "Not Tuesday",
        11: "Not Wednesday",
        12: "Not Thursday",
        13: "Not Friday",
        14: "Not Saturday",
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


@register.filter(name="get_tour")
def get_tour(tour: int):
    return models.Tours.objects.get(id=tour).name


@register.filter(name="get_ordinal")
def make_ordinal(n: int):
    """Convert an integer into its ordinal representation::.

    make_ordinal(0)   => '0th'
    make_ordinal(3)   => '3rd'
    make_ordinal(122) => '122nd'
    make_ordinal(213) => '213th'
    """
    n = int(n)
    if 11 <= (n % 100) <= 13:  # noqa: PLR2004
        suffix = "th"
    else:
        suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]
    return str(n) + suffix


@register.filter(name="note_format")
def event_note_format(note: str) -> str:
    """Cuts note at first paragraph boundary."""
    return note.splitlines()[0]
