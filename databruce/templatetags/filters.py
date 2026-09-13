import re
import string

import bleach
import markdown
import nh3
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


@register.filter(name="format_event_id")
def event_id_format(event_id: str) -> str:
  event_num = event_id[-2:]
  num = int(event_num)

  cnt = string.ascii_lowercase[num - 1]

  return f"{event_id[0:4]}{event_id[4:6]}{event_id[6:8]}{cnt}"


@register.filter(name="format_event_note")
def event_note_format(text: str) -> str:

  text = text.replace("\r\n", "\n")

  # Step 2: Use regex to replace single newlines with a space.
  # This matches a newline only if it is NOT preceded or followed by another newline.
  text = re.sub(r"\n{1,}", " ", text)

  # Step 3: Clean up any accidental double spaces created by the merge
  text = re.sub(r" +", " ", text)

  raw_html = markdown.markdown(text)

  return bleach.clean(raw_html, tags=[], strip=True)


@register.filter(name="markdown")
def markdown_convert(note: str) -> str | None:
  if note and note != "":
    raw_html = markdown.markdown(note)

    # 2. Define safe elements
    allowed_tags = [
      "p",
      "strong",
      "em",
      "a",
      "h1",
      "h2",
      "h3",
      "h4",
      "ul",
      "ol",
      "li",
      "br",
      "code",
      "pre",
      "blockquote",
    ]

    # 3. Clean the HTML (strips script tags, onerror events, etc.)
    cleaned_html = nh3.clean(
      raw_html,
      tags=set(allowed_tags),
    )

    return mark_safe(cleaned_html)

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
def format_fuzzy(value) -> str:
  """Format event_id as YYYY-MM-DD for events with no date."""
  year, month, day = value[0:4], value[4:6], value[6:8]

  if month == "00":
    month = "01"

  if day == "00":
    day = "01"

  return f"{year}-{month}-{day}"


@register.filter
def currency(value):
  try:
    if value == int(value):
      return f"${value:,.0f}"

  except (TypeError, ValueError):
    return value
  else:
    return f"${value:,.2f}"


@register.filter(name="markdown_safe")
def markdown_safe(value):
  """Converts markdown to HTML and thoroughly sanitizes it against XSS.

  Automatically marks the output as safe for Django templates.
  """
  if not value:
    return ""

  # 1. Convert Markdown text to raw HTML
  raw_html = markdown.markdown(value)

  # 2. Define safe elements
  allowed_tags = [
    "p",
    "strong",
    "em",
    "a",
    "h1",
    "h2",
    "h3",
    "h4",
    "ul",
    "ol",
    "li",
    "br",
    "code",
    "pre",
    "blockquote",
  ]
  allowed_attributes = {
    "a": ["href", "title", "target", "rel"],
  }

  # 3. Clean the HTML (strips script tags, onerror events, etc.)
  cleaned_html = bleach.clean(
    raw_html,
    tags=allowed_tags,
    attributes=allowed_attributes,
    strip=True,
  )

  # 4. Mark as safe so you don't need to append |safe in the template
  return mark_safe(cleaned_html)


@register.inclusion_tag("databruce/partials/star_rating.html")
def render_stars(rating):
  """Safely converts a number (integer or float) into a 5-star array.

  Converts the number and sends it to an isolated HTML partial template.
  """
  try:
    rating = float(rating)
  except (ValueError, TypeError):
    rating = 0.0

  star_list = []
  for i in range(5, 0, -1):
    if rating >= i:
      star_list.append("fill")
    else:
      star_list.append("empty")

  return {
    "star_list": star_list,
    "rating": rating,
  }
