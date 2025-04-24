import re
from datetime import datetime

import markdown
from django import template

from databruce.models import SetlistNotes, SetlistsBySetAndDate, Venues, VenuesText

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


@register.filter(name="notes")
def setlist_notes(setlist_id):
    return SetlistNotes.objects.filter(id=setlist_id).order_by("num")

    # note = []

    # for n in value:
    #     if n.id.id == songid:
    #         note.append(f"<sup title='{n.note.replace("'", '"')}'>[{n.num}]</sup>")

    # return "".join(note).strip()


@register.filter(name="event_notes_filter")
def event_notes(note_list):
    notes = []

    for note in note_list:
        current = {
            "num": note.num,
            "note": note.note,
            "last": note.last,
            "last_date": "",
            "gap": note.gap,
        }

        if note.last_date:
            current["last_date"] = datetime.strftime(note.last_date, "%Y-%m-%d")

        if current not in notes:
            notes.append(current)

    print(notes)
    return notes


@register.filter(name="type_color")
def get_event_color(event_type: str = "Concert"):
    if re.search("rescheduled|no gig", event_type, flags=re.IGNORECASE):
        return "cancelled"

    return ""


@register.filter(name="mdlink")
def md_link(note: str):
    link = re.search(r"(.*)\[(.*)\]\((.*)\)", note)
    if link:
        return re.sub(r"</?p>", "", markdown.markdown(note))
    return note


@register.filter(name="venue")
def get_venue(venue):
    if venue.state:
        return f"{venue.name}, {venue.city.name}, {venue.state.state_abbrev}"

    return f"{venue.name}, {venue.city.name}, {venue.country.name}"

    # return VenuesText.objects.get(id=venue_id).formatted_loc


@register.filter(name="get_date")
def get_date(date: datetime = None, event: str = ""):
    """Date to return if it is null or unknown."""
    if date:
        return date.strftime("%Y-%m-%d [%a]")

    return f"{event[0:4]}-{event[4:6]}-{event[6:8]}"
