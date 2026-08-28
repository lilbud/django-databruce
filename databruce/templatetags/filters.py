import string

import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


class EMarkdown(markdown.Markdown):
  def convert(self, text):
    # Call the standard conversion and strip hidden whitespace/newlines
    html = super().convert(text).strip()

    # Safely remove wrapping tags even if formatting varies
    if html.startswith("<p>") and html.endswith("</p>"):
      html = html[3:-4]

    return html


md = EMarkdown()


@register.filter(name="markdown")
def markdown_convert(note: str) -> str | None:
  if note:
    # Wrap in mark_safe so Django renders the <a> tag as HTML
    return mark_safe(md.convert(note))
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


@register.filter
def currency(value):
  try:
    return f"${value:,.2f}"
  except (ValueError, TypeError):
    return value
