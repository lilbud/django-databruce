from __future__ import annotations

import re
from typing import TYPE_CHECKING

import markdown
from django import template

if TYPE_CHECKING:
    from datetime import datetime

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


@register.filter(name="get_date")
def get_date(date: datetime | None, event: str = ""):
    """Date to return if it is null or unknown."""
    if date:
        return date.strftime("%Y-%m-%d")

    return f"{event[0:4]}-{event[4:6]}-{event[6:8]}"


@register.filter()
def setlist_note(notes):
    if len(notes) > 1:
        return "; ".join([md_link(note.note) for note in notes])

    return md_link(notes[0].note)


@register.filter()
def album_percent(num: int, maxnum: int):
    return int((num / maxnum) * 100)
