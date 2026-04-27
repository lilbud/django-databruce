# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
import re
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F, Func, Value
from django.db.models.functions import Lower, Trim
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from requests.packages import mod

from .templatetags.filters import format_fuzzy


class CustomUser(AbstractUser):
    uuid = models.UUIDField(default=uuid4, unique=True, editable=False)

    groups = models.ManyToManyField(
        "auth.Group",
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        blank=True,
    )

    def __str__(self):
        return self.username

    class Meta:
        db_table = "auth_user"  # Directs Django to the existing table
        verbose_name_plural = "Users"


class RegexpReplace(Func):
    function = "regexp_replace"
    # Optional: ensure correct argument count
    arg_joiner = ", "


class BaseModel(models.Model):
    created_at = models.DateTimeField(db_index=True, default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        managed = True


class ArchiveLinks(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    event = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        db_column="event_id",
        related_name="archive_links",
        null=True,
    )

    url = models.TextField(null=True, db_column="archive_url")

    class Meta:
        db_table = "archive_links"
        verbose_name_plural = "archive_links"

    def __str__(self) -> str:
        return self.url


class Bands(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    brucebase_url = models.TextField(default=None, blank=True, null=True)
    name = models.TextField(default=None, blank=True)
    num_events = models.IntegerField(default=0)

    first_event = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="band_first",
        db_column="first_event",
        default=None,
        null=True,
        blank=True,
    )

    last_event = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="band_last",
        db_column="last_event",
        default=None,
        null=True,
        blank=True,
    )

    springsteen_band = models.BooleanField(default=False)
    mbid = models.UUIDField(default=None, editable=False, null=True, blank=True)
    note = models.TextField(default=None, blank=True, null=True)

    class Meta:
        db_table = "bands"
        verbose_name_plural = "bands"

    def __str__(self) -> str:
        return self.name


class Bootlegs(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    slid = models.IntegerField(default=None, blank=True, null=True)
    mbid = models.UUIDField(default=None, editable=False)

    event = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        db_column="event_id",
        default=None,
    )

    category = models.TextField(default=None, blank=True, null=True)
    title = models.TextField(default=None, blank=True, null=True)
    label = models.TextField(default=None, blank=True, null=True)
    source = models.TextField(default=None, blank=True, null=True)
    source_info = models.TextField(default=None, blank=True, null=True)
    version_info = models.TextField(default=None, blank=True, null=True)
    transfer = models.TextField(default=None, blank=True, null=True)
    editor = models.TextField(default=None, blank=True, null=True)
    type = models.TextField(default=None, blank=True, null=True)
    catalog_number = models.TextField(default=None, blank=True, null=True)
    media_type = models.TextField(default=None, blank=True, null=True)
    has_info = models.BooleanField()
    has_artwork = models.BooleanField()
    archive = models.ForeignKey(
        to=ArchiveLinks,
        on_delete=models.DO_NOTHING,
        db_column="archive_id",
        default=None,
    )

    class Meta:
        db_table = "bootlegs"
        verbose_name_plural = "bootlegs"


class Cities(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    mbid = models.UUIDField(default=None, editable=False)
    name = models.TextField(default=None, db_column="name")

    state = models.ForeignKey(
        to="States",
        on_delete=models.DO_NOTHING,
        related_name="city_state",
        db_column="state",
        default=None,
        blank=True,
        null=True,
    )

    country = models.ForeignKey(
        to="Countries",
        on_delete=models.DO_NOTHING,
        related_name="city_country",
        db_column="country",
        default=None,
        blank=True,
        null=True,
    )

    num_events = models.IntegerField(default=None, blank=True, null=True)
    aliases = models.TextField(default=None, blank=True, null=True)

    first_event = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="city_first",
        db_column="first_event",
        default=None,
    )

    last_event = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="city_last",
        db_column="last_event",
        default=None,
    )

    timezone = models.TextField(default=None, blank=True, null=True)

    class Meta:
        db_table = "cities"
        verbose_name_plural = "cities"
        unique_together = (("name", "state"),)

    def __str__(self) -> str:
        if self.country_id in [6, 37] and self.state_id:
            return f"{self.name}, {self.state.abbrev}"

        return f"{self.name}, {self.country}"


class Continents(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    name = models.TextField(default=None, db_column="continent_name")
    num_events = models.IntegerField(default=0)

    class Meta:
        db_table = "continents"
        verbose_name_plural = "continents"

    def __str__(self) -> str:
        return self.name


class Countries(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    name = models.TextField(unique=True, default=None)
    num_events = models.IntegerField(default=None, blank=True, null=True)

    continent = models.ForeignKey(
        to="Continents",
        on_delete=models.DO_NOTHING,
        db_column="continent",
        default=None,
    )

    alpha_2 = models.TextField(default=None, max_length=2)
    aliases = models.TextField(default=None, blank=True, null=True)
    mbid = models.UUIDField(default=None, editable=False)

    first_event = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="country_first",
        db_column="first_event",
        default=None,
    )

    last_event = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="country_last",
        db_column="last_event",
        default=None,
    )

    class Meta:
        db_table = "countries"
        verbose_name_plural = "countries"

    def __str__(self) -> str:
        return self.name


class Covers(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    event_date = models.TextField(default=None, blank=True, null=True)
    url = models.TextField(unique=True, default=None, db_column="cover_url")

    event = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        db_column="event_id",
        default=None,
    )

    class Meta:
        db_table = "covers"
        verbose_name_plural = "covers"


class States(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    abbrev = models.TextField(
        unique=True,
        default=None,
        db_column="state_abbrev",
    )
    name = models.TextField(default=None, blank=True, null=True)
    country = models.ForeignKey(Countries, models.DO_NOTHING, db_column="country")
    num_events = models.IntegerField(default=0)
    mbid = models.UUIDField(default=None, editable=False)

    first_event = models.ForeignKey(
        "Events",
        models.DO_NOTHING,
        related_name="state_first",
        db_column="first_event",
    )

    last_event = models.ForeignKey(
        "Events",
        models.DO_NOTHING,
        related_name="state_last",
        db_column="last_event",
    )

    class Meta:
        db_table = "states"
        verbose_name_plural = "states"

    def __str__(self) -> str:
        return self.name


class Venues(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    brucebase_url = models.TextField(default=None, blank=True, null=True)
    name = models.TextField(default=None, blank=True, null=True)
    detail = models.TextField(default=None, blank=True, null=True)

    city = models.ForeignKey(
        Cities,
        on_delete=models.CASCADE,
        db_column="city",
        related_name="venue_city",
        null=True,
        default=None,
    )

    num_events = models.IntegerField(default=0)
    note = models.TextField(default=None, blank=True, null=True)
    mbid = models.UUIDField(default=None, editable=False, blank=True, null=True)

    first_event = models.ForeignKey(
        "Events",
        models.DO_NOTHING,
        db_column="first_event",
        related_name="venues_first",
        default=None,
        null=True,
        blank=True,
    )

    last_event = models.ForeignKey(
        "Events",
        models.DO_NOTHING,
        db_column="last_event",
        related_name="venues_last",
        default=None,
        null=True,
        blank=True,
    )

    address = models.TextField(null=True)

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
    )

    class Meta:
        db_table = "venues"
        verbose_name_plural = "venues"

    def __str__(self) -> str:
        name = self.name

        if self.id in [351]:
            name = "Pierre's Good Citizens Ballpark"

        if self.id in [2040, 2844]:
            name = "The Big Joint"

        if self.detail:
            name = f"{self.name}, {self.detail}"

        # if self.city:
        #     name += f" ({self.city.name})"

        return name

    def get_name(self) -> str:
        name = self.name

        if self.id == 351:
            name = "Pierre's Good Citizens Ballpark (Citizens Bank Park)"

        if self.id == 2040:
            name = "The Big Joint (Wells Fargo Center)"

        if self.id == 2844:
            name = "The Big Joint (Xfinity Mobile Arena)"

        if self.detail:
            return f"{name}, {self.detail}"

        return name

    @property
    def country(self):
        # Since the City always knows its Country, we just grab it from there
        try:
            return self.city.country
        except AttributeError:
            return None

    @property
    def state(self):
        # This will return the State object or None if it's London/Paris/etc.

        try:
            state = self.city.state

            if self.city.country.id in [2, 6, 37]:
                return state.abbrev

        except AttributeError:
            return None
        else:
            return self.city.state.name


class VenuesText(models.Model):
    id = models.OneToOneField(
        Venues,
        models.DO_NOTHING,
        related_name="venues_text",
        primary_key=True,
        db_column="id",
    )

    location = models.TextField()
    formatted = models.TextField(db_column="full_location")

    class Meta:
        managed = False
        db_table = "venues_text"


class VenueAliases(BaseModel):
    id = models.UUIDField(primary_key=True)
    venue = models.ForeignKey("Venues", models.DO_NOTHING, null=True)
    name = models.TextField()
    note = models.TextField(null=True)

    class Meta:
        db_table = "venue_aliases"


class Events(BaseModel):
    id = models.AutoField(primary_key=True)
    num = models.IntegerField(
        db_column="event_num",
        blank=True,
        null=True,
        default=None,
    )
    event_id = models.CharField(max_length=11, db_column="event_id", unique=True)
    date = models.DateField(default=None, db_column="event_date", blank=True, null=True)
    uuid = models.UUIDField(default=uuid4, editable=False)

    early_late_choices = [
        ("Evening", "Evening"),
        ("Late", "Late"),
        ("Third", "Third"),
        ("Early", "Early"),
        ("Afternoon", "Afternoon"),
        ("Morning", "Morning"),
    ]

    early_late = models.CharField(
        choices=early_late_choices,
        default=None,
        blank=True,
        null=True,
    )

    public = models.BooleanField(default=False)

    artist = models.ForeignKey(
        to=Bands,
        on_delete=models.DO_NOTHING,
        db_column="artist",
        default=None,
        blank=True,
        null=True,
    )

    brucebase_url = models.CharField(default=None, blank=True, null=True)

    venue = models.ForeignKey(
        to=Venues,
        on_delete=models.DO_NOTHING,
        related_name="event_venue",
        db_column="venue_id",
        default=None,
        blank=True,
        null=True,
    )

    tour = models.ForeignKey(
        to="Tours",
        on_delete=models.DO_NOTHING,
        db_column="tour_id",
        default=None,
        blank=True,
        null=True,
    )

    leg = models.ForeignKey(
        to="TourLegs",
        on_delete=models.DO_NOTHING,
        default=None,
        db_column="tour_leg",
        blank=True,
        null=True,
    )

    run = models.ForeignKey(
        to="Runs",
        on_delete=models.DO_NOTHING,
        default=None,
        db_column="run",
        blank=True,
        null=True,
    )

    type = models.ForeignKey(
        to="EventTypes",
        on_delete=models.DO_NOTHING,
        db_column="event_type",
        default=None,
        blank=True,
        null=True,
    )

    title = models.CharField(
        default=None,
        db_column="event_title",
        blank=True,
        null=True,
    )

    event_certainty_choices = (
        ("Unknown Date", "Unknown Date"),
        ("Confirmed", "Confirmed"),
        ("Rumored", "Rumored"),
        ("Probable", "Probable"),
        ("Unknown Location", "Unknown Location"),
    )

    setlist_certainty_choices = (
        ("Unknown", "Unknown"),
        ("Confirmed", "Confirmed"),
        ("Probable", "Probable"),
    )

    event_certainty = models.CharField(
        choices=event_certainty_choices,
        default=None,
        blank=True,
        null=True,
    )

    setlist_certainty = models.CharField(
        choices=setlist_certainty_choices,
        default=None,
        blank=True,
        null=True,
    )

    note = models.TextField(default=None, blank=True, null=True)
    bootleg = models.BooleanField(default=False)
    is_stats_eligible = models.BooleanField(default=True)

    official = models.ForeignKey(
        to="Releases",
        on_delete=models.DO_NOTHING,
        default=None,
        db_column="official_id",
        blank=True,
        null=True,
    )

    nugs = models.ForeignKey(
        to="NugsReleases",
        on_delete=models.DO_NOTHING,
        default=None,
        db_column="nugs_id",
        blank=True,
        null=True,
    )

    start_time = models.DateTimeField(blank=True, null=True, default=None)
    end_time = models.DateTimeField(blank=True, null=True, default=None)
    scheduled_time = models.DateTimeField(blank=True, null=True, default=None)

    class Meta:
        db_table = "events"
        verbose_name_plural = "events"
        ordering = ["id", "event_id"]
        get_latest_by = "event_id"

    def __str__(self) -> str:
        try:
            event = self.date.strftime("%Y-%m-%d")
            if self.early_late:
                event += f" ({self.early_late})"
        except AttributeError:
            event = format_fuzzy(self.event_id)

        return event

    def filter_date(self) -> str:
        return f"{self.event_id[0:4]}-{self.event_id[4:6]}-{self.event_id[6:8]}"

    def get_date(self) -> str:
        try:
            if self.early_late:
                return f"{self.date.strftime('%Y-%m-%d [%a]')} ({self.early_late})"

            return self.date.strftime("%Y-%m-%d [%a]")

        except AttributeError:
            event = format_fuzzy(self.event_id)

            if self.early_late:
                return f"{event} ({self.early_late})"

            return event

    def get_last(self):
        return (
            Events.objects.select_related("venue", "artist")
            .filter(event_id__lt=self.event_id)
            .order_by("-event_id")
            .first()
        )

    def get_next(self):
        return (
            Events.objects.select_related("venue", "artist")
            .filter(event_id__gt=self.event_id)
            .order_by("event_id")
            .first()
        )

    @property
    def has_setlist(self):
        return self.setlist_event.exists()


class NugsReleases(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    nugs_id = models.IntegerField(default=None, blank=True, null=True)
    event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        db_column="event_id",
        related_name="nugs_event",
    )
    date = models.DateTimeField(default=None, db_column="release_date")
    url = models.TextField(default=None, db_column="nugs_url")
    thumbnail = models.TextField(default=None, db_column="thumbnail_url")
    name = models.TextField(default=None, blank=True, null=True)
    first_friday = models.BooleanField(default=False, db_column="first_friday")

    class Meta:
        db_table = "nugs_releases"
        verbose_name_plural = "Nugs Releases"
        ordering = ["-event__id"]

    def __str__(self) -> str:
        return str(self.nugs_id)


class Relations(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    mbid = models.UUIDField(default=None, editable=False, null=True, blank=True)
    brucebase_url = models.TextField(default=None, blank=True, null=True)
    name = models.TextField(default=None, blank=True, null=True)
    appearances = models.IntegerField(default=0)
    first_event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="relation_first",
        db_column="first_event",
        default=None,
        blank=True,
        null=True,
    )
    last_event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="relation_last",
        db_column="last_event",
        default=None,
        blank=True,
        null=True,
    )

    instruments = models.TextField(default=None, blank=True, null=True)
    start_date = models.DateField(default=None, blank=True, null=True)
    end_date = models.DateField(default=None, blank=True, null=True)
    show_cal = models.BooleanField(default=False, db_column="show_calendar")

    class Meta:
        db_table = "relations"
        verbose_name_plural = "relations"

    def __str__(self) -> str:
        return self.name


class RelationAliases(BaseModel):
    id = models.UUIDField(primary_key=True)
    relation = models.ForeignKey(Relations, models.DO_NOTHING, null=True)
    name = models.TextField()
    type = models.TextField()

    class Meta:
        db_table = "relation_aliases"


class Onstage(BaseModel):
    id = models.AutoField(primary_key=True)

    uuid = models.UUIDField(default=uuid4, editable=False)

    event = models.ForeignKey(
        to=Events,
        on_delete=models.DO_NOTHING,
        db_column="event_id",
        related_name="onstage",
        default=None,
        db_index=True,
    )

    relation = models.ForeignKey(
        to=Relations,
        on_delete=models.DO_NOTHING,
        db_column="relation_id",
        default=None,
    )

    band = models.ForeignKey(
        to=Bands,
        on_delete=models.DO_NOTHING,
        db_column="band_id",
        related_name="onstage_band",
        to_field="id",
        default=None,
        blank=True,
    )

    note = models.TextField(default=None, blank=True, null=True)
    guest = models.BooleanField(default=False)

    class Meta:
        db_table = "onstage"
        verbose_name_plural = "onstage"
        unique_together = ("event", "relation", "band")

    def __str__(self) -> str:
        try:
            return f"Relation: [{self.relation_id}] {self.relation.name} / {self.band.name}"
        except Onstage.band.RelatedObjectDoesNotExist:
            return f"Relation: [{self.relation_id}] {self.relation.name}"


class ReleaseTracks(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    release = models.OneToOneField(
        "Releases",
        models.DO_NOTHING,
        db_column="release_id",
        related_name="release_tracks",
    )
    discnum = models.IntegerField(db_column="disc_num")

    discid = models.ForeignKey(
        "ReleaseDiscs",
        to_field="uuid",
        on_delete=models.DO_NOTHING,
        db_column="disc_id",
        default=None,
        blank=True,
        null=True,
    )

    track = models.CharField(db_column="track")

    position = models.IntegerField()

    song = models.OneToOneField(
        to="Songs",
        on_delete=models.DO_NOTHING,
        db_column="song_id",
        related_name="release_track_song",
    )

    event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        default=None,
        blank=True,
        null=True,
    )
    note = models.TextField(default=None, blank=True, null=True)

    setlist = models.ForeignKey(
        to="Setlists",
        on_delete=models.DO_NOTHING,
        db_column="setlist_id",
        to_field="id",
        default=None,
    )

    length = models.TimeField(default=None, blank=True, null=True)

    class Meta:
        db_table = "release_tracks"
        verbose_name_plural = "Release Tracks"
        ordering = ["release__name", "track"]

    def __str__(self) -> str:
        try:
            return f"{self.discid.name} - {self.song.name}"
        except AttributeError:
            return f"Disc {self.discnum} - {self.song.name}"


class Releases(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    brucebase_id = models.TextField(default=None, blank=True, null=True)
    name = models.TextField(default=None, blank=True, null=True)
    length = models.TimeField(default=None, blank=True, null=True)
    spotify_link = models.TextField(
        default=None,
        blank=True,
        null=True,
        db_column="spotify_url",
    )

    release_types = (
        ("Live", "Live"),
        ("Compilation", "Compilation"),
        ("Studio", "Studio"),
        ("Podcast", "Podcast"),
        ("Retrospective", "Retrospective"),
    )

    type = models.CharField(default=None, choices=release_types)

    format_types = (
        ("audio", "audio"),
        ("video", "video"),
    )

    format = models.CharField(default=None, choices=format_types)
    date = models.DateField(
        default=None,
        db_column="release_date",
        verbose_name="Release Date",
    )
    short_name = models.TextField(default=None, blank=True, null=True)
    thumb = models.TextField(default=None, blank=True, null=True)
    note = models.TextField(default=None, blank=True, null=True)
    mbid = models.UUIDField(
        default=None,
        verbose_name="MusicBrainz ID",
        blank=True,
        null=True,
    )
    event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="release_event",
        db_column="event_id",
        default=None,
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "releases"
        verbose_name_plural = "releases"

    def __str__(self) -> str:
        return self.name


class SetlistNotes(models.Model):
    setlist = models.ForeignKey(
        "Setlists",
        models.DO_NOTHING,
        related_name="setlist_notes",
        db_column="setlist_id",
        primary_key=True,
    )

    event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="notes_event",
        db_column="event_id",
    )

    num = models.IntegerField(blank=False)
    note = models.TextField(default=None, blank=True, null=True)

    class Meta:
        managed = False  # Created from a view. Don't remove.
        db_table = "setlist_notes_new"
        verbose_name_plural = "Setlist Notes"

    def __str__(self) -> str:
        return self.note


class Songs(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    brucebase_url = models.TextField(default=None, blank=True, null=True)
    name = models.TextField(
        default=None,
        verbose_name="Name",
        db_column="song_name",
    )
    short_name = models.TextField(
        default=None,
        verbose_name="Short Name",
        blank=True,
        null=True,
    )

    first_event = models.ForeignKey(
        to=Events,
        on_delete=models.DO_NOTHING,
        related_name="song_first",
        verbose_name="First Played",
        db_column="first_event",
        default=None,
        blank=True,
        null=True,
    )

    last_event = models.ForeignKey(
        to=Events,
        on_delete=models.DO_NOTHING,
        related_name="song_last",
        verbose_name="Last Played",
        db_column="last_event",
        default=None,
        blank=True,
        null=True,
    )

    num_plays_public = models.IntegerField(default=0, db_column="num_plays_public")
    num_plays_private = models.IntegerField(default=0, db_column="num_plays_private")
    num_plays_snippet = models.IntegerField(default=0, db_column="num_plays_snippet")

    opener = models.IntegerField(default=0)
    closer = models.IntegerField(default=0)

    sniponly = models.IntegerField(default=0)

    original_artist = models.TextField(
        default=None,
        verbose_name="Original Artist",
        blank=True,
        null=True,
    )

    original = models.BooleanField(default=False)
    lyrics = models.BooleanField(default=False)

    category = models.TextField(default=None, blank=True, null=True)
    spotify_id = models.TextField(default=None, blank=True, null=True)

    mbid = models.UUIDField(default=None, editable=False, null=True, blank=True)

    length = models.TimeField(default=None, blank=True, null=True)

    album = models.ForeignKey(
        to=Releases,
        on_delete=models.DO_NOTHING,
        db_column="album",
        default=None,
        blank=True,
        null=True,
    )

    aliases = models.TextField(default=None, blank=True, null=True)

    sort_song_name = models.GeneratedField(
        expression=Trim(
            Lower(
                RegexpReplace(
                    F("name"),
                    Value(r'^[\("“‘]*(The |An ) ??|^[\("“‘]+'),
                    Value(""),
                    Value("i"),
                ),
            ),
        ),
        output_field=models.TextField(),
        db_persist=True,
    )

    class Meta:
        db_table = "songs"
        ordering = ["name"]
        verbose_name_plural = "songs"

    def __str__(self) -> str:
        if not self.original:
            return f"{self.name} ({self.original_artist})"

        return f"{self.name}"


class Setlists(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)

    event = models.ForeignKey(
        to=Events,
        on_delete=models.DO_NOTHING,
        db_column="event_id",
        related_name="setlist_event",
        default=None,
        db_index=True,
    )

    sets = (
        ("Soundcheck", "Soundcheck"),
        ("Interview", "Interview"),
        ("Post-Show", "Post-Show"),
        ("Set 1", "Set 1"),
        ("Set 2", "Set 2"),
        ("Encore", "Encore"),
        ("Pre-Show", "Pre-Show"),
        ("Show", "Show"),
        ("Recording", "Recording"),
        ("Rehearsal", "Rehearsal"),
    )

    set_name = models.CharField(default="Show", choices=sets)

    song_num = models.IntegerField(
        default=1,
        blank=True,
        null=True,
    )

    song = models.ForeignKey(
        to=Songs,
        on_delete=models.DO_NOTHING,
        db_column="song_id",
        default=None,
        to_field="id",
    )

    note = models.TextField(default=None, db_column="song_note", blank=True, null=True)
    segue = models.BooleanField(default=False)
    premiere = models.BooleanField(default=False)
    debut = models.BooleanField(default=False)
    instrumental = models.BooleanField(default=False)
    nobruce = models.BooleanField(default=False)
    position = models.TextField(default=None, blank=True, null=True)

    last = models.IntegerField(default=None, blank=True, null=True)
    next = models.IntegerField(default=None, blank=True, null=True)

    tour_num = models.IntegerField(default=None, blank=True, null=True)
    tour_total = models.IntegerField(default=None, blank=True, null=True)

    ltp = models.ForeignKey(
        to=Events,
        on_delete=models.DO_NOTHING,
        db_column="last_time_played",
        related_name="ltp_event",
        default=None,
        blank=True,
        null=True,
    )

    sign_request = models.BooleanField(default=False)

    is_opener = models.BooleanField(default=False)
    is_closer = models.BooleanField(default=False)
    is_set_opener = models.BooleanField(default=False)
    is_set_closer = models.BooleanField(default=False)
    is_last_in_show = models.BooleanField(default=False)
    is_main_set_closer = models.BooleanField(default=False)

    class Meta:
        db_table = "setlists"
        verbose_name_plural = "setlists"

    def __str__(self) -> str:
        event_id = self.event_id
        return f"[{self.id}] {self.event.event_id} - {self.set_name} - {self.song.name} ({self.song_id})"

    VALID_SET_NAMES = [
        "Show",
        "Set 1",
        "Set 2",
        "Encore",
        "Pre-Show",
        "Post-Show",
    ]

    # @property
    # def prev_song(self):
    #     try:
    #         return (
    #             Setlists.objects.select_related("song", "event")
    #             .filter(
    #                 set_name=self.set_name,
    #                 event=self.event.id,
    #                 song_num__isnull=False,
    #                 song_num__lt=self.song_num,
    #             )
    #             .order_by("event__event_id", "song_num")
    #             .last()
    #             .song
    #         )
    #     except (AttributeError, ValueError):
    #         return None

    # @property
    # def next_song(self):
    #     try:
    #         return (
    #             Setlists.objects.select_related("song", "event")
    #             .filter(
    #                 set_name=self.set_name,
    #                 event=self.event.id,
    #                 song_num__isnull=False,
    #                 song_num__gt=self.song_num,
    #             )
    #             .order_by("event__event_id", "song_num")
    #             .first()
    #             .song
    #         )
    #     except (AttributeError, ValueError):
    #         return None


class SetlistsBySetAndDate(models.Model):
    id = models.AutoField(primary_key=True)
    set_order = models.IntegerField(default=None, blank=True, null=True)

    event = models.ForeignKey(
        "Events",
        on_delete=models.DO_NOTHING,
        default=None,
        db_column="event_id",
    )

    set_name = models.TextField(default=None, blank=True, null=True)
    setlist = models.TextField(default=None, blank=True, null=True)
    setlist_no_note = models.TextField(default=None, blank=True, null=True)

    class Meta:
        managed = False  # Created from a view. Don't remove.
        db_table = "setlists_by_set_and_date"
        verbose_name_plural = "setlists_by_set_and_date"


class Snippets(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)

    setlist = models.ForeignKey(
        Setlists,
        models.DO_NOTHING,
        db_column="setlist_id",
    )

    snippet = models.ForeignKey(
        to=Songs,
        on_delete=models.DO_NOTHING,
        related_name="snippet",
        db_column="snippet_id",
        default=None,
    )

    position = models.IntegerField(db_column="snippet_pos", default=1)
    note = models.TextField(
        default=None,
        db_column="snippet_note",
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "snippets"
        verbose_name_plural = "snippets"


class SongsAfterRelease(models.Model):
    song_id = models.TextField(default=None, blank=True, null=True)
    first_release = models.DateField(default=None, blank=True, null=True)
    first_event = models.TextField(default=None, blank=True, null=True)
    num_post_release = models.BigIntegerField(default=None, blank=True, null=True)

    class Meta:
        managed = False  # Created from a view. Don't remove.
        db_table = "songs_after_release"
        verbose_name_plural = "songs_after_release"


class Tours(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    brucebase_id = models.TextField(default=None, null=True, blank=True)
    brucebase_tag = models.TextField(default=None, null=True, blank=True)

    band = models.ForeignKey(
        Bands,
        models.DO_NOTHING,
        related_name="tour_band",
        db_column="band_id",
    )

    name = models.TextField(default=None, db_column="tour_name")
    slug = models.TextField(default=None, null=True, blank=True)
    note = models.TextField(default=None, null=True, blank=True)

    first_event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="tour_first",
        db_column="first_event",
        default=None,
    )

    last_event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="tour_last",
        db_column="last_event",
        default=None,
    )

    num_shows = models.IntegerField(default=0)
    num_songs = models.IntegerField(default=0)
    num_legs = models.IntegerField(default=0)

    class Meta:
        db_table = "tours"
        verbose_name_plural = "tours"

    def __str__(self) -> str:
        return self.name


class TourLegs(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)

    tour = models.ForeignKey(
        Tours,
        models.DO_NOTHING,
        related_name="tour_id",
        db_column="tour_id",
    )

    name = models.TextField(default=None, blank=True, null=True)

    first_event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="tourleg_first",
        db_column="first_event",
    )
    last_event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="tourleg_last",
        db_column="last_event",
    )

    num_shows = models.IntegerField(default=0)
    num_songs = models.IntegerField(default=0)
    note = models.TextField(default=None, blank=True, null=True)

    class Meta:
        db_table = "tour_legs"
        verbose_name_plural = "tour_legs"

    def __str__(self) -> str:
        return self.name


class Runs(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)

    band = models.ForeignKey(
        Bands,
        models.DO_NOTHING,
        db_column="band",
        null=True,
        blank=True,
        default=None,
    )
    venue = models.ForeignKey(
        Venues,
        models.DO_NOTHING,
        db_column="venue",
        null=True,
        blank=True,
        default=None,
    )
    name = models.TextField(null=True, max_length=255)

    num_shows = models.IntegerField(
        null=True,
        blank=True,
        default=None,
    )

    num_songs = models.IntegerField(
        null=True,
        blank=True,
        default=None,
    )

    first_event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        db_column="first_event",
        related_name="event_run_first",
        null=True,
        blank=True,
        default=None,
    )
    last_event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        db_column="last_event",
        related_name="event_run_last",
        null=True,
        blank=True,
        default=None,
    )
    note = models.TextField(default=None, blank=True, null=True)

    class Meta:
        db_table = "runs"
        verbose_name_plural = "runs"

    def __str__(self) -> str:
        return self.name


class StudioSessions(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    band = models.ForeignKey(
        "Bands",
        models.DO_NOTHING,
        db_column="band",
        null=True,
    )
    name = models.TextField()
    num_events = models.IntegerField(null=True)
    num_songs = models.IntegerField(null=True)

    first_event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        db_column="first_event",
        related_name="session_first_event",
        null=True,
    )

    last_event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        db_column="last_event",
        related_name="session_last_event",
        null=True,
    )

    release = models.ForeignKey(
        Releases,
        models.DO_NOTHING,
        null=True,
        db_column="album",
    )

    class Meta:
        db_table = "studio_sessions"
        verbose_name_plural = "studio_sessions"


class UserAttendedShows(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.DO_NOTHING,
        db_column="user_id",
        related_name="user_attended_shows",
    )

    event = models.OneToOneField(
        Events,
        models.DO_NOTHING,
        db_column="event_id",
        related_name="user_event",
    )

    class Meta:
        db_table = "user_attended_shows"
        verbose_name_plural = "user_attended_shows"
        unique_together = ("user", "event")


class Guests(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)

    setlist = models.ForeignKey(
        to=Setlists,
        on_delete=models.DO_NOTHING,
        db_column="setlist_id",
    )

    guest = models.ForeignKey(
        to=Relations,
        on_delete=models.DO_NOTHING,
        db_column="guest_id",
    )

    # event = models.ForeignKey(
    #     Events,
    #     models.DO_NOTHING,
    #     db_column="event_id",
    # )

    note = models.TextField(null=True, blank=True, default=None)

    class Meta:
        db_table = "guests"
        verbose_name_plural = "guests"


class Lyrics(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)

    song = models.OneToOneField(
        Songs,
        models.DO_NOTHING,
        null=True,
        db_column="song_id",
        related_name="lyrics_song",
    )

    version = models.TextField(
        db_column="version_info",
        null=True,
        blank=True,
        default=None,
    )
    num = models.TextField(db_column="version_num", null=True, blank=True, default=None)
    source = models.TextField(
        db_column="source_info",
        null=True,
        blank=True,
        default=None,
    )
    text = models.TextField(db_column="lyrics", null=True, blank=True, default=None)

    language = models.TextField(null=True, blank=True, default=None)
    note = models.TextField(null=True, blank=True, default=None)

    class Meta:
        db_table = "lyrics"
        verbose_name_plural = "lyrics"


class Updates(models.Model):
    id = models.AutoField(primary_key=True)
    item_id = models.TextField(null=True)
    item = models.TextField(null=True)
    value = models.TextField(null=True, db_column="to_value")
    view = models.TextField(null=True)
    msg = models.TextField(null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "updates"


class SiteUpdates(BaseModel):
    id = models.AutoField(primary_key=True)
    description = models.TextField(null=True)

    uuid = models.UUIDField(default=uuid4, editable=False)

    class Meta:
        db_table = "update_table"


class OnstageBandMembers(models.Model):
    id = models.IntegerField(primary_key=True)
    relation = models.ForeignKey(Relations, models.DO_NOTHING, db_column="relation_id")

    band = models.ForeignKey(
        Bands,
        models.DO_NOTHING,
        db_column="band_id",
        blank=True,
        default=None,
    )

    count = models.IntegerField()

    first = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="onstagebandfirst",
        db_column="first",
    )

    last = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="onstagebandlast",
        db_column="last",
    )

    class Meta:
        managed = False
        db_table = "onstage_band_members"


class ReleaseDiscs(BaseModel):
    id = models.AutoField(primary_key=True)
    release = models.ForeignKey(Releases, models.DO_NOTHING)
    disc_num = models.IntegerField()
    name = models.TextField(blank=False, null=False)
    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    updated_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "release_discs"
        verbose_name_plural = "Release Discs"

    def __str__(self) -> str:
        return f"Disc {self.disc_num}: {self.name}"


class SetlistEntries(models.Model):
    id = models.AutoField(primary_key=True)

    event = models.OneToOneField(
        Events,
        models.DO_NOTHING,
        db_column="event_id",
    )

    show_opener = models.OneToOneField(
        to=Songs,
        on_delete=models.DO_NOTHING,
        related_name="show_opener",
        db_column="show_opener",
    )

    s1_closer = models.OneToOneField(
        to=Songs,
        on_delete=models.DO_NOTHING,
        related_name="s1_closer",
        db_column="s1_closer",
    )

    s2_opener = models.OneToOneField(
        to=Songs,
        on_delete=models.DO_NOTHING,
        related_name="s2_opener",
        db_column="s2_opener",
    )

    main_closer = models.OneToOneField(
        to=Songs,
        on_delete=models.DO_NOTHING,
        related_name="main_closer",
        db_column="main_closer",
    )

    encore_opener = models.OneToOneField(
        to=Songs,
        on_delete=models.DO_NOTHING,
        related_name="encore_opener",
        db_column="encore_opener",
    )

    show_closer = models.OneToOneField(
        to=Songs,
        on_delete=models.DO_NOTHING,
        related_name="show_closer",
        db_column="show_closer",
    )

    class Meta:
        managed = False
        db_table = "setlist_entries"


class Notes(BaseModel):
    id = models.AutoField(primary_key=True)
    event = models.ForeignKey(
        Events,
        on_delete=models.CASCADE,
        db_column="event_id",
    )
    num = models.IntegerField()
    note = models.TextField()
    gap = models.TextField(null=True)
    last = models.TextField(null=True)
    last_date = models.TextField(null=True)
    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    updated_at = models.DateTimeField(null=True)

    setlist = models.ForeignKey(
        Setlists,
        on_delete=models.CASCADE,
        db_column="setlist_id",
    )

    class Meta:
        db_table = "notes"

    def __str__(self) -> str:
        return re.sub("'{2,}", "'", self.note)


class Contact(BaseModel):
    id = models.AutoField(primary_key=True)
    email = models.EmailField()

    subject_choices = [
        ("problem", "Bug/Problem"),
        ("suggestion", "Suggestion"),
        ("comment", "Comment"),
        ("comment", "Question"),
    ]

    is_user = models.BooleanField(default=False)

    subject = models.CharField(choices=subject_choices)
    message = models.TextField()

    class Meta:
        db_table = "contact"
        verbose_name_plural = "Contact"
        managed = True

    def __str__(self) -> str:
        return f"Message from {self.name} - {self.subject}"


class TourCount(models.Model):
    setlist = models.OneToOneField(
        "Setlists",
        on_delete=models.DO_NOTHING,
        primary_key=True,
        db_column="id",
        related_name="tour_stats_link",
    )

    num = models.IntegerField()
    total = models.IntegerField()

    class Meta:
        managed = False  # Critical: Tells Django not to try to create/delete this table
        db_table = "setlist_tour_count"


class SetlistPositions(models.Model):
    id = models.OneToOneField(
        "Setlists",
        on_delete=models.DO_NOTHING,
        primary_key=True,
        db_column="id",
        related_name="setlist_position",
    )

    position = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "setlist_positions"


class SongsPage(models.Model):
    id = models.ForeignKey(
        Setlists,
        models.DO_NOTHING,
        primary_key=True,
        related_name="songs_page",
        db_column="id",
    )

    prev = models.ForeignKey(
        Setlists,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name="prev_setlist",
        db_column="prev",
    )

    next = models.ForeignKey(
        Setlists,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name="next_setlist",
        db_column="next",
    )

    class Meta:
        managed = False
        db_table = "songs_page"


class SongsPageNew(models.Model):
    id = models.OneToOneField(
        Setlists,
        models.DO_NOTHING,
        primary_key=True,
        related_name="songs_page_new",
        db_column="id",
    )

    prev = models.OneToOneField(
        Setlists,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name="prev_id",
        db_column="prev",
    )

    next = models.OneToOneField(
        Setlists,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name="next_id",
        db_column="next",
    )

    class Meta:
        managed = False
        db_table = "songs_page_new"


class SetlistStats(models.Model):
    setlist = models.OneToOneField(
        Setlists,
        on_delete=models.DO_NOTHING,
        primary_key=True,
        related_name="setlist_stats",
        db_column="id",
    )
    song_num = models.IntegerField(blank=True, null=True)
    set_name = models.TextField(blank=True, null=True)

    event = models.ForeignKey(
        Events,
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        db_column="event_id",
        related_name="stats_event",
    )

    # event_id = models.IntegerField(blank=True, null=True, db_column="event_id")

    total_event_songs = models.IntegerField(blank=True, null=True)
    global_first = models.BooleanField(blank=True, null=True)
    global_last = models.BooleanField(blank=True, null=True)
    set_first = models.BooleanField(blank=True, null=True)
    set_last = models.BooleanField(blank=True, null=True)
    is_the_main_closer = models.BooleanField(blank=True, null=True)
    show_has_encore = models.BooleanField(blank=True, null=True)
    gap = models.IntegerField(blank=True, null=True, db_column="calc_gap")

    ltp = models.ForeignKey(
        Events,
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        db_column="calc_last_ev_id",
        related_name="stats_ltp",
    )

    premiere = models.BooleanField(blank=True, null=True, db_column="is_premiere")
    debut = models.BooleanField(blank=True, null=True, db_column="is_debut")
    band_premiere = models.BooleanField(
        blank=True,
        null=True,
        db_column="is_band_premiere",
    )
    tour_num = models.IntegerField(blank=True, null=True, db_column="tour_num")
    tour_total = models.IntegerField(blank=True, null=True, db_column="tour_total")

    class Meta:
        managed = False
        db_table = "setlist_stats"


class EventTypes(BaseModel):
    id = models.AutoField(primary_key=True, db_column="id")
    name = models.TextField()
    slug = models.TextField()
    uuid = models.UUIDField(default=uuid4, editable=False)

    class Meta:
        db_table = "event_types"
        verbose_name_plural = "event types"

    def __str__(self):
        return self.name


class BlogCategory(BaseModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "blog_category"
        verbose_name_plural = "blog categories"

    def __str__(self):
        return self.name


class BlogTags(BaseModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        db_table = "blog_tags"
        verbose_name_plural = "blog tags"

    def __str__(self):
        return self.name


class BlogPosts(BaseModel):
    id = models.AutoField(primary_key=True)
    title = models.CharField()
    slug = models.SlugField(unique=True, blank=True)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    body = models.TextField()
    excerpt = models.CharField()

    categories = models.ManyToManyField(
        "BlogCategory",
        through="BlogPostCategories",
        related_name="posts",
    )

    tags = models.ManyToManyField(
        "BlogTags",
        through="BlogPostTags",
        related_name="posts",
    )

    published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True, default=None)

    class Meta:
        db_table = "blog_posts"
        verbose_name_plural = "blog posts"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            # Check if the slug already exists in the DB
            while BlogPosts.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        if not self.published_at:
            self.published_at = self.created_at

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "blog_post",
            args=[
                self.slug,
            ],
        )


class BlogPostTags(models.Model):
    post = models.ForeignKey(
        BlogPosts,
        models.DO_NOTHING,
        related_name="blog_post_tags",
        db_column="post_id",
    )

    tag = models.ForeignKey(
        BlogTags,
        models.DO_NOTHING,
        db_column="tag_id",
        related_name="post_tags",
    )

    class Meta:
        managed = True
        db_table = "blog_post_tags"
        verbose_name_plural = "Blog Post Tags"
        unique_together = (("post", "tag"),)


class BlogPostCategories(models.Model):
    post = models.ForeignKey(
        BlogPosts,
        models.DO_NOTHING,
        related_name="blog_post_categories",
        db_column="post_id",
    )

    category = models.ForeignKey(
        BlogCategory,
        models.DO_NOTHING,
        db_column="category_id",
        related_name="post_categories",
    )

    class Meta:
        managed = True
        db_table = "blog_post_categories"
        verbose_name_plural = "Blog Post Categories"
        unique_together = (("post", "category"),)


class BlogAuthors(BaseModel):
    author = models.ForeignKey(CustomUser, models.DO_NOTHING)
    uuid = models.UUIDField(default=uuid4, editable=False)

    class Meta:
        db_table = "blog_authors"
        verbose_name_plural = "blog authors"
