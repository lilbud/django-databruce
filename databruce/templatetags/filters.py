from __future__ import annotations

import re
import string

import markdown
from django import template

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
