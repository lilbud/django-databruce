import string

import markdown
from django import template

register = template.Library()


@register.filter(name="markdown")
def markdown_convert(note: str) -> str:
    if note:
        return markdown.markdown(note.strip())

    return None


@register.filter(name="get_date")
def get_date(event: str):
    """Date to return if it is null or unknown."""
    return f"{event[0:4]}-{event[4:6]}-{event[6:8]}"


@register.filter()
def brucebase_url(event: str):
    year, month, day = event[0:4], event[4:6], event[6:8]

    if int(event[-1]) > 1:
        d = dict(enumerate(string.ascii_lowercase, 1))
        return f"{year}#{day}{month}{year[2:]}{d[int(event[-1])]}"

    return f"{year}#{day}{month}{year[2:]}"


@register.filter
def format_fuzzy(value):
    year, month, day = value[0:4], value[4:6], value[6:8]

    if month == "00":
        month = "01"

    if day == "00":
        day = "01"

    return f"{year}-{month}-{day}"
