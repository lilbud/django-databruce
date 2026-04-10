import string

import markdown
import nh3
from django import template
from django.template import Context
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

register = template.Library()


class EMarkdown(markdown.Markdown):
    def convert(self, text):
        # Call the standard conversion
        html = super().convert(text)
        # Manually strip the wrapping <p> tags
        return html.removeprefix("<p>").removesuffix("</p>")


md = EMarkdown()


@register.simple_tag(takes_context=True)
def render_includes(context, value):
    """Render a string as a Django template within the current context."""
    if not value:
        return ""

    value = nh3.clean(
        value,
        tags={"figure", "div", "br", "code", "blockquote", "p", "a", "img"},
        attributes={
            "div": {"class"},
            "figure": {"class"},
            "a": {"href"},
            "img": {"src"},
        },
    )

    value = markdown.markdown(value, extensions=["fenced_code"])

    # Create the template object from your database string
    template_obj = template.Template(value)

    context_new = Context({"body": context.get("post").body})

    # Use the existing context (which is already a Context object)
    return mark_safe(template_obj.render(context_new))


@register.filter(name="markdown")
def markdown_convert(note: str) -> str:
    if note:
        return md.convert(note.strip())

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
