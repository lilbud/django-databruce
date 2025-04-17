import django_tables2 as tables

from .models import *


class VenueTable(tables.Table):
    class Meta:
        model = Venues
        sequence = ("name", "city", "state", "country", "num_events")
        exclude = ("brucebase_url", "continent", "id")
        attrs = {
            "data-bs-theme": "dark",
        }
        template_name = "django_tables2/bootstrap5.html"


class EventTable(tables.Table):
    formatted_date = tables.TemplateColumn(
        template_code="<a class='{% load filters %} {{ record.event_type | color }}' href='{{ record.event_url }}'>{{ record.formatted_date }}</a>",
        attrs={"td": {"class": "col-1"}},
        verbose_name="Date",
    )

    venue_loc = tables.TemplateColumn(
        template_code="<a class='{% load filters %} {{ record.event_type | color }}' href='{{ record.venue_url }}'>{{ record.venue_loc }}</a>",
        attrs={"td": {"class": "col-2"}},
        verbose_name="Venue",
    )

    artist = tables.TemplateColumn(
        template_code="<a class='{% load filters %} {{ record.event_type | color }}' href='{{ record.artist_url }}'>{{ record.artist }}</a>",
        attrs={"td": {"class": "col-1"}},
        verbose_name="Artist",
    )

    setlist = tables.Column(
        attrs={"td": {"class": "col-6"}},
        verbose_name="Setlist",
    )

    class Meta:
        model = EventsTableList
        sequence = ("formatted_date", "venue_loc", "artist", "setlist")

        exclude = (
            "id",
            "event_id",
            "venue_url",
            "event_url",
            "artist_url",
            "event_type",
        )

        attrs = {
            "data-bs-theme": "dark",
        }

        template_name = "django_tables2/bootstrap5.html"


class SongTable(tables.Table):
    song_name = tables.TemplateColumn(
        template_code="<a href='{{ record.brucebase_url }}'>{{ record.song_name }}</a>",
        attrs={"td": {"class": "col-2"}},
        verbose_name="Name",
    )

    original_artist = tables.Column(
        attrs={"td": {"class": "col-2"}},
        verbose_name="Original Artist",
    )

    first_played = tables.TemplateColumn(
        template_code="<a href='{% url 'databruce:event_page' id=record.first_played %}'>{{ record.first_date }}</a>",
        attrs={"td": {"class": "col-1"}},
        verbose_name="First",
    )

    last_played = tables.TemplateColumn(
        template_code="<a href='{% url 'databruce:event_page' id=record.last_played %}'>{{ record.last_date }}</a>",
        attrs={"td": {"class": "col-1"}},
        verbose_name="Last",
    )

    num_plays_public = tables.Column(
        attrs={"td": {"class": "col-1"}},
        verbose_name="Public",
    )

    num_plays_private = tables.Column(
        attrs={"td": {"class": "col-1"}},
        verbose_name="Private",
    )

    class Meta:
        model = Songs
        sequence = (
            "song_name",
            "original_artist",
            "first_played",
            "last_played",
            "num_plays_public",
            "num_plays_private",
        )
        exclude = (
            "short_name",
            "opener",
            "closer",
            "cover",
            "sniponly",
            "aliases",
            "fts",
            "brucebase_url",
            "id",
        )
        attrs = {
            "data-bs-theme": "dark",
        }
        template_name = "django_tables2/bootstrap5-responsive.html"
