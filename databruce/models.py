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
from django.db import models
from django.utils import timezone
from requests.packages import mod

from .templatetags.filters import format_fuzzy

UserModel = get_user_model()


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
        blank=True,
        null=True,
    )

    url = models.TextField(blank=True, null=True, db_column="archive_url")  # noqa: DJ001

    class Meta:
        db_table = "archive_links"
        verbose_name_plural = "archive_links"

    def __str__(self) -> str:
        return self.url


class Bands(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    brucebase_url = models.TextField(blank=True, default=None)
    name = models.TextField(blank=True, default=None)
    num_events = models.IntegerField(default=0)

    first_event = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="band_first",
        db_column="first_event",
        blank=True,
        default=None,
    )

    last_event = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="band_last",
        db_column="last_event",
        blank=True,
        default=None,
    )

    springsteen_band = models.BooleanField()
    mbid = models.UUIDField(default=None, editable=False)

    class Meta:
        db_table = "bands"
        verbose_name_plural = "bands"

    def __str__(self) -> str:
        return self.name


class Bootlegs(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    slid = models.IntegerField(blank=True, default=None)
    mbid = models.UUIDField(default=None, editable=False)

    event = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        db_column="event_id",
        blank=True,
        default=None,
    )

    category = models.TextField(blank=True, default=None)
    title = models.TextField(blank=True, default=None)
    label = models.TextField(blank=True, default=None)
    source = models.TextField(blank=True, default=None)
    source_info = models.TextField(blank=True, default=None)
    version_info = models.TextField(blank=True, default=None)
    transfer = models.TextField(blank=True, default=None)
    editor = models.TextField(blank=True, default=None)
    type = models.TextField(blank=True, default=None)
    catalog_number = models.TextField(blank=True, default=None)
    media_type = models.TextField(blank=True, default=None)
    has_info = models.BooleanField()
    has_artwork = models.BooleanField()
    archive = models.ForeignKey(
        to=ArchiveLinks,
        on_delete=models.DO_NOTHING,
        db_column="archive_id",
        blank=True,
        default=None,
    )

    class Meta:
        db_table = "bootlegs"
        verbose_name_plural = "bootlegs"


class Cities(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    mbid = models.UUIDField(default=None, editable=False)
    name = models.TextField(blank=True, default=None, db_column="name")

    state = models.ForeignKey(
        to="States",
        on_delete=models.DO_NOTHING,
        related_name="city_state",
        db_column="state",
        blank=True,
        default=None,
    )

    country = models.ForeignKey(
        to="Countries",
        on_delete=models.DO_NOTHING,
        related_name="city_country",
        db_column="country",
        blank=True,
        default=None,
    )

    num_events = models.IntegerField(blank=True, default=None)
    aliases = models.TextField(blank=True, default=None)

    first_event = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="city_first",
        db_column="first_event",
        blank=True,
        default=None,
    )

    last_event = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="city_last",
        db_column="last_event",
        blank=True,
        default=None,
    )

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
    name = models.TextField(blank=True, default=None, db_column="continent_name")
    num_events = models.IntegerField(default=0)

    class Meta:
        db_table = "continents"
        verbose_name_plural = "continents"

    def __str__(self) -> str:
        return self.name


class Countries(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    name = models.TextField(unique=True, blank=True, default=None)
    num_events = models.IntegerField(blank=True, default=None)

    continent = models.ForeignKey(
        to="Continents",
        on_delete=models.DO_NOTHING,
        db_column="continent",
        blank=True,
        default=None,
    )

    alpha_2 = models.TextField(blank=True, default=None, max_length=2)
    aliases = models.TextField(blank=True, default=None)
    mbid = models.UUIDField(default=None, editable=False)

    first_event = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="country_first",
        db_column="first_event",
        blank=True,
        default=None,
    )

    last_event = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="country_last",
        db_column="last_event",
        blank=True,
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
    event_date = models.TextField(blank=True, default=None)
    url = models.TextField(unique=True, blank=True, default=None, db_column="cover_url")

    event = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        db_column="event_id",
        blank=True,
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
        blank=True,
        default=None,
        db_column="state_abbrev",
    )
    name = models.TextField(blank=True, default=None)
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
    brucebase_url = models.TextField(blank=True, default=None)
    name = models.TextField(blank=True, default=None)
    detail = models.TextField(blank=True, default=None)

    city = models.ForeignKey(
        Cities,
        on_delete=models.CASCADE,
        db_column="city",
        related_name="venue_city",
        null=True,
        default=None,
    )

    num_events = models.IntegerField(default=0)
    note = models.TextField(blank=True, default=None)
    mbid = models.UUIDField(default=None, editable=False)

    first_event = models.ForeignKey(
        "Events",
        models.DO_NOTHING,
        db_column="first_event",
        related_name="venues_first",
        blank=True,
        default=None,
    )

    last_event = models.ForeignKey(
        "Events",
        models.DO_NOTHING,
        db_column="last_event",
        related_name="venues_last",
        blank=True,
        default=None,
    )

    address = models.CharField(max_length=500, null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "venues"
        verbose_name_plural = "venues"

    def __str__(self) -> str:
        name = self.name

        if self.id == 351:
            name = "Pierre's Good Citizens Ballpark"

        if self.id == 2040:
            name = "The Big Joint"

        if self.detail:
            name = f"{self.name}, {self.detail}"

        if self.city:
            name += f" ({self.city.name})"

        return name

    def get_name(self) -> str:
        name = self.name

        if self.id == 351:
            name = "Pierre's Good Citizens Ballpark (Citizens Bank Park)"

        if self.id == 2040:
            name = "The Big Joint (Wells Fargo Center)"

        if self.detail:
            return f"{name}, {self.detail}"

        return name

    @property
    def country(self):
        # Since the City always knows its Country, we just grab it from there
        return self.city.country

    @property
    def state(self):
        # This will return the State object or None if it's London/Paris/etc.

        try:
            state = self.city.state

            if self.city.country.id in [2, 6, 37]:
                return state.abbrev

            return state.name
        except AttributeError:
            return None


class VenueAliases(BaseModel):
    id = models.UUIDField(primary_key=True)
    venue = models.ForeignKey("Venues", models.DO_NOTHING, blank=True, null=True)
    name = models.TextField()
    note = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "venue_aliases"


class Events(BaseModel):
    id = models.AutoField(primary_key=True)
    num = models.IntegerField(db_column="event_num")

    event_id = models.SlugField(max_length=11, db_column="event_id", unique=True)

    date = models.DateField(blank=True, default=None, db_column="event_date")

    early_late_choices = [
        ("Evening", "Evening"),
        ("Late", "Late"),
        ("Third", "Third"),
        ("Early", "Early"),
        ("Afternoon", "Afternoon"),
        ("Morning", "Morning"),
    ]

    early_late = models.CharField(blank=True, choices=early_late_choices, default=None)

    public = models.BooleanField(blank=True, default=False)

    artist = models.ForeignKey(
        to=Bands,
        on_delete=models.DO_NOTHING,
        db_column="artist",
    )

    brucebase_url = models.TextField(blank=True, default=None)

    venue = models.ForeignKey(
        to=Venues,
        on_delete=models.DO_NOTHING,
        related_name="event_venue",
        db_column="venue_id",
        blank=True,
        default=None,
    )

    tour = models.ForeignKey(
        to="Tours",
        on_delete=models.DO_NOTHING,
        blank=True,
        default=None,
        db_column="tour_id",
    )

    leg = models.ForeignKey(
        to="TourLegs",
        on_delete=models.DO_NOTHING,
        blank=True,
        default=None,
        db_column="tour_leg",
    )

    run = models.ForeignKey(
        to="Runs",
        on_delete=models.DO_NOTHING,
        blank=True,
        default=None,
        db_column="run",
    )

    types = (
        ("Anniversary", "Anniversary"),
        ("Award Ceremony", "Award Ceremony"),
        ("Benefit Concert", "Benefit Concert"),
        ("Birthday", "Birthday"),
        ("Cancelled", "Cancelled"),
        ("Celebration", "Celebration"),
        ("Concert", "Concert"),
        ("Concert for TV Broadcast", "Concert for TV Broadcast"),
        ("Filmshoot", "Filmshoot"),
        ("Funeral", "Funeral"),
        ("Interview", "Interview"),
        ("Jam Session", "Jam Session"),
        ("Keynote Speech", "Keynote Speech"),
        ("Memorial", "Memorial"),
        ("Music Festival", "Music Festival"),
        ("No Gig", "No Gig"),
        ("Politics", "Politics"),
        ("Recording", "Recording"),
        ("Rehearsal", "Rehearsal"),
        ("Relocated", "Relocated"),
        ("Rescheduled", "Rescheduled"),
        ("Wedding", "Wedding"),
    )

    type = models.CharField(
        blank=True,
        default=None,
        choices=types,
        db_column="event_type",
    )

    title = models.TextField(blank=True, default=None, db_column="event_title")

    event_certainty_choices = (
        ("Unknown Date", "Unknown Date"),
        ("Confirmed", "Confirmed"),
        ("Unknown Location", "Unknown Location"),
    )

    setlist_certainty_choices = (
        ("Unknown", "Unknown"),
        ("Confirmed", "Confirmed"),
        ("Probable", "Probable"),
    )

    event_certainty = models.CharField(
        blank=True,
        choices=event_certainty_choices,
        default=None,
    )
    setlist_certainty = models.CharField(
        blank=True,
        choices=setlist_certainty_choices,
        default=None,
    )

    note = models.TextField(blank=True, default=None)
    bootleg = models.BooleanField(blank=True, default=False)
    is_stats_eligible = models.BooleanField(default=True)

    official = models.ForeignKey(
        to="Releases",
        on_delete=models.DO_NOTHING,
        blank=True,
        default=None,
        db_column="official_id",
    )

    nugs = models.ForeignKey(
        to="NugsReleases",
        on_delete=models.DO_NOTHING,
        blank=True,
        default=None,
        db_column="nugs_id",
    )

    # objects = EventManager()

    class Meta:
        db_table = "events"
        verbose_name_plural = "events"
        ordering = ["id"]

    def __str__(self) -> str:
        try:
            event = self.date.strftime("%Y-%m-%d")
            if self.early_late:
                event += f" ({self.early_late})"
        except AttributeError:
            event = format_fuzzy(self.event_id)

        # event += f" {self.venue}"

        return event

    def filter_date(self) -> str:
        return f"{self.event_id[0:4]}-{self.event_id[4:6]}-{self.event_id[6:8]}"

    def get_date(self) -> str:
        try:
            event = self.date.strftime("%Y-%m-%d [%a]")
            if self.early_late:
                event += f" ({self.early_late})"

        except AttributeError:
            event = f"{self.event_id[0:4]}-{self.event_id[4:6]}-{self.event_id[6:8]}"

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
        return self.setlist_certainty in ("Confirmed", "Probable")


class NugsReleases(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    nugs_id = models.IntegerField(blank=True, default=None)
    event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        db_column="event_id",
    )
    date = models.DateTimeField(blank=True, default=None, db_column="release_date")
    url = models.TextField(blank=True, default=None, db_column="nugs_url")
    thumbnail = models.TextField(blank=True, default=None, db_column="thumbnail_url")
    name = models.TextField(blank=True, default=None)
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
    mbid = models.UUIDField(default=None, editable=False)
    brucebase_url = models.TextField(blank=True, default=None)
    name = models.TextField(blank=True, default=None)
    appearances = models.IntegerField(default=0)
    first_event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="relation_first",
        db_column="first_event",
        blank=True,
        default=None,
    )
    last_event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="relation_last",
        db_column="last_event",
        blank=True,
        default=None,
    )

    instruments = models.TextField(blank=True, default=None)

    class Meta:
        db_table = "relations"
        verbose_name_plural = "relations"

    def __str__(self) -> str:
        return self.name


class RelationAliases(BaseModel):
    id = models.UUIDField(primary_key=True)
    relation = models.ForeignKey(Relations, models.DO_NOTHING, blank=True, null=True)
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
        blank=True,
        default=None,
        db_index=True,
    )

    relation = models.ForeignKey(
        to=Relations,
        on_delete=models.DO_NOTHING,
        db_column="relation_id",
        blank=True,
        default=None,
    )

    band = models.ForeignKey(
        to=Bands,
        on_delete=models.DO_NOTHING,
        db_column="band_id",
        related_name="onstage_band",
        to_field="id",
        blank=True,
        default=None,
    )

    note = models.TextField(blank=True, default=None)
    guest = models.BooleanField(default=False)

    class Meta:
        db_table = "onstage"
        verbose_name_plural = "onstage"
        unique_together = ("event", "relation", "band")

    def __str__(self):
        return f"Relation {self.relation_id} / Band {self.band_id}"


class ReleaseTracks(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    release = models.ForeignKey("Releases", models.DO_NOTHING, db_column="release_id")
    discnum = models.IntegerField(db_column="disc_num")
    discid = models.ForeignKey(
        "ReleaseDiscs",
        to_field="uuid",
        on_delete=models.DO_NOTHING,
        db_column="disc_id",
    )
    track = models.IntegerField(db_column="track_num")

    song = models.ForeignKey(
        to="Songs",
        on_delete=models.DO_NOTHING,
        db_column="song_id",
        blank=True,
        default=None,
    )

    event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        blank=True,
        default=None,
    )
    note = models.TextField(blank=True, default=None)

    setlist = models.ForeignKey(
        to="Setlists",
        on_delete=models.DO_NOTHING,
        db_column="setlist_id",
        to_field="id",
        blank=True,
        default=None,
    )

    length = models.TimeField(blank=True, default=None)

    class Meta:
        db_table = "release_tracks"
        verbose_name_plural = "Release Tracks"
        ordering = ["release__name", "track"]


class Releases(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    brucebase_id = models.TextField(blank=True, default=None)
    name = models.TextField(blank=True, default=None)

    release_types = (
        ("Live", "Live"),
        ("Compilation", "Compilation"),
        ("Studio", "Studio"),
    )

    type = models.CharField(blank=True, default=None, choices=release_types)

    format_types = (
        ("audio", "audio"),
        ("video", "video"),
    )

    format = models.CharField(blank=True, default=None, choices=format_types)
    date = models.DateField(
        blank=True,
        default=None,
        db_column="release_date",
        verbose_name="Release Date",
    )
    short_name = models.TextField(blank=True, default=None)
    thumb = models.TextField(blank=True, default=None)
    note = models.TextField(blank=True, default=None)
    mbid = models.UUIDField(default=None, blank=True, verbose_name="MusicBrainz ID")
    event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="release_event",
        db_column="event_id",
        default=None,
        blank=True,
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
        db_column="id",
        primary_key=True,
    )

    event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        to_field="event_id",
        related_name="notes_event",
        db_column="event_id",
    )

    num = models.IntegerField(blank=False)
    note = models.TextField(blank=True, default=None)

    class Meta:
        managed = False  # Created from a view. Don't remove.
        db_table = "setlist_notes_new"
        verbose_name_plural = "Setlist Notes"

    def __str__(self):
        return self.note


class Songs(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    brucebase_url = models.TextField(blank=True, default=None)
    name = models.TextField(
        blank=True,
        default=None,
        verbose_name="Name",
        db_column="song_name",
    )
    short_name = models.TextField(blank=True, default=None, verbose_name="Short Name")

    first_event = models.ForeignKey(
        to=Events,
        on_delete=models.DO_NOTHING,
        related_name="song_first",
        verbose_name="First Played",
        db_column="first_event",
        blank=True,
        default=None,
    )

    last_event = models.ForeignKey(
        to=Events,
        on_delete=models.DO_NOTHING,
        related_name="song_last",
        verbose_name="Last Played",
        db_column="last_event",
        blank=True,
        default=None,
    )

    num_plays_public = models.IntegerField(default=0, db_column="num_plays_public")
    num_plays_private = models.IntegerField(default=0, db_column="num_plays_private")
    num_plays_snippet = models.IntegerField(default=0, db_column="num_plays_snippet")

    opener = models.IntegerField(default=0)
    closer = models.IntegerField(default=0)

    sniponly = models.IntegerField(default=0)

    original_artist = models.TextField(
        blank=True,
        default=None,
        verbose_name="Original Artist",
    )

    original = models.BooleanField(default=False)
    lyrics = models.BooleanField(default=False)

    category = models.TextField(blank=True, default=None)
    spotify_id = models.TextField(blank=True, default=None)

    mbid = models.UUIDField(default=None, editable=False)

    length = models.TimeField(blank=True, default=None)

    album = models.ForeignKey(
        to=Releases,
        on_delete=models.DO_NOTHING,
        db_column="album",
        blank=True,
        default=None,
    )

    aliases = models.TextField(blank=True, default=None)

    sort_song_name = models.CharField(default="")

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
        blank=True,
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

    set_name = models.CharField(blank=True, default="Show", choices=sets)

    song_num = models.IntegerField(
        default=1,
        blank=True,
    )

    song = models.ForeignKey(
        to=Songs,
        on_delete=models.DO_NOTHING,
        db_column="song_id",
        blank=True,
        default=None,
        to_field="id",
    )

    note = models.TextField(blank=True, default=None, db_column="song_note")
    segue = models.BooleanField(default=False)
    premiere = models.BooleanField(default=False)
    debut = models.BooleanField(default=False)
    instrumental = models.BooleanField(default=False)
    nobruce = models.BooleanField(default=False)
    position = models.TextField(blank=True, default=None)

    last = models.IntegerField(blank=True, default=None)
    next = models.IntegerField(blank=True, default=None)

    tour_num = models.IntegerField(blank=True, default=None)
    tour_total = models.IntegerField(blank=True, default=None)

    ltp = models.ForeignKey(
        to=Events,
        on_delete=models.DO_NOTHING,
        db_column="last_time_played",
        related_name="ltp_event",
        blank=True,
        default=None,
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
        return f"{event_id} - {self.set_name} - {self.song_id} ({self.id})"

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
    set_order = models.IntegerField(blank=True, default=None)

    event = models.ForeignKey(
        "Events",
        on_delete=models.DO_NOTHING,
        blank=True,
        default=None,
        db_column="event_id",
    )

    set_name = models.TextField(blank=True, default=None)
    setlist = models.TextField(blank=True, default=None)
    setlist_no_note = models.TextField(blank=True, default=None)

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
        blank=True,
        default=None,
    )

    position = models.IntegerField(db_column="snippet_pos")
    note = models.TextField(blank=True, default=None, db_column="snippet_note")

    class Meta:
        db_table = "snippets"
        verbose_name_plural = "snippets"


class SongsAfterRelease(models.Model):
    song_id = models.TextField(blank=True, default=None)
    first_release = models.DateField(blank=True, default=None)
    first_event = models.TextField(blank=True, default=None)
    num_post_release = models.BigIntegerField(blank=True, default=None)

    class Meta:
        managed = False  # Created from a view. Don't remove.
        db_table = "songs_after_release"
        verbose_name_plural = "songs_after_release"


class Tags(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        db_column="event_id",
    )
    tags = models.TextField(blank=True, default=None)

    class Meta:
        db_table = "tags"
        verbose_name_plural = "tags"


class Tours(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    brucebase_id = models.TextField(blank=True, default=None, unique=True)
    brucebase_tag = models.TextField(blank=True, default=None)

    band = models.ForeignKey(
        Bands,
        models.DO_NOTHING,
        related_name="tour_band",
        db_column="band_id",
    )

    name = models.TextField(blank=True, default=None, db_column="tour_name")
    slug = models.TextField(blank=True, default=None)

    first_event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="tour_first",
        db_column="first_event",
        blank=True,
        default=None,
    )

    last_event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="tour_last",
        db_column="last_event",
        blank=True,
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

    name = models.TextField(blank=True, default=None)

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
    note = models.TextField(blank=True, default=None)

    class Meta:
        db_table = "tour_legs"
        verbose_name_plural = "tour_legs"

    def __str__(self) -> str:
        return self.name


class SongsPage(models.Model):
    id = models.OneToOneField(
        Songs,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column="id",
    )

    prev = models.ForeignKey(
        to=Setlists,
        on_delete=models.DO_NOTHING,
        related_name="prev",
        db_column="prev",
        null=True,
        default=None,
    )

    current = models.ForeignKey(
        to=Setlists,
        on_delete=models.DO_NOTHING,
        related_name="current",
        db_column="current",
        blank=True,
        default=None,
    )

    next = models.ForeignKey(
        to=Setlists,
        on_delete=models.DO_NOTHING,
        related_name="songpage_next",
        db_column="next",
        null=True,
        default=None,
    )

    note = models.TextField(default=None, blank=True)

    class Meta:
        managed = False
        db_table = "songs_page"
        verbose_name_plural = "songs_page"


class Runs(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)

    band = models.ForeignKey(
        Bands,
        models.DO_NOTHING,
        db_column="band",
        blank=True,
        null=True,
    )
    venue = models.ForeignKey(
        Venues,
        models.DO_NOTHING,
        db_column="venue",
        blank=True,
        null=True,
    )
    name = models.TextField(blank=True, null=True, max_length=255)  # noqa: DJ001
    num_shows = models.IntegerField(blank=True, null=True)
    num_songs = models.IntegerField(blank=True, null=True)

    first_event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        db_column="first_event",
        blank=True,
        null=True,
    )
    last_event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        db_column="last_event",
        related_name="runs_last_event_set",
        blank=True,
        null=True,
    )

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
        blank=True,
        null=True,
    )
    name = models.TextField()
    num_events = models.IntegerField(blank=True, null=True)
    num_songs = models.IntegerField(blank=True, null=True)

    first_event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        db_column="first_event",
        related_name="session_first_event",
        blank=True,
        null=True,
    )

    last_event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        db_column="last_event",
        related_name="session_last_event",
        blank=True,
        null=True,
    )

    release = models.ForeignKey(
        Releases,
        models.DO_NOTHING,
        blank=True,
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
        UserModel,
        on_delete=models.DO_NOTHING,
        db_column="user_id",
    )

    event = models.OneToOneField(
        Events,
        models.DO_NOTHING,
        db_column="event_id",
        related_name="user_attended_shows",
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

    event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        db_column="event_id",
    )
    note = models.TextField(blank=True, null=True)  # noqa: DJ001

    class Meta:
        db_table = "guests"
        verbose_name_plural = "guests"


class Lyrics(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    song = models.ForeignKey(
        Songs,
        models.DO_NOTHING,
        blank=True,
        null=True,
        db_column="song_id",
        related_name="lyrics_song",
    )
    version = models.TextField(db_column="version_info")
    num = models.TextField(db_column="version_num")
    source = models.TextField(db_column="source_info")
    text = models.TextField(db_column="lyrics")

    language = models.TextField(blank=True, null=True)  # noqa: DJ001
    note = models.TextField(blank=True, null=True)  # noqa: DJ001

    class Meta:
        db_table = "lyrics"
        verbose_name_plural = "lyrics"


class Updates(models.Model):
    id = models.AutoField(primary_key=True)
    item_id = models.TextField(blank=True, null=True)
    item = models.TextField(blank=True, null=True)  # noqa: DJ001
    value = models.TextField(blank=True, null=True, db_column="to_value")  # noqa: DJ001
    view = models.TextField(blank=True, null=True)  # noqa: DJ001
    msg = models.TextField(blank=True, null=True)  # noqa: DJ001
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "updates"


class SiteUpdates(BaseModel):
    id = models.AutoField(primary_key=True)
    description = models.TextField(blank=True, null=True)

    uuid = models.UUIDField(default=uuid4, editable=False)

    class Meta:
        db_table = "update_table"


class Songspagenew(models.Model):
    id = models.AutoField(primary_key=True)

    song = models.IntegerField(blank=True, null=True, db_column="song_id")

    num = models.IntegerField(blank=True, null=True, db_column="song_num")

    event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        blank=True,
        null=True,
        db_column="event_id",
        related_name="page_events",
    )

    artist = models.IntegerField(blank=True, null=True, db_column="artist_id")
    artist_name = models.TextField(blank=True, null=True)  # noqa: DJ001
    venue = models.IntegerField(blank=True, null=True, db_column="venue_id")
    venue_name = models.TextField(blank=True, null=True, db_column="venue")  # noqa: DJ001
    tour = models.IntegerField(blank=True, null=True, db_column="tour_id")
    tour_name = models.TextField(blank=True, null=True)  # noqa: DJ001
    position = models.TextField(blank=True, null=True)  # noqa: DJ001
    gap = models.IntegerField(null=True, default=0)
    set_name = models.TextField(blank=True, null=True)  # noqa: DJ001
    prev = models.IntegerField(blank=True, null=True, db_column="prev_id")
    prev_name = models.TextField(blank=True, null=True)  # noqa: DJ001
    next = models.IntegerField(blank=True, null=True, db_column="next_id")
    next_name = models.TextField(blank=True, null=True)  # noqa: DJ001
    note = models.TextField(blank=True, null=True)  # noqa: DJ001

    class Meta:
        managed = False
        db_table = "songspagenew"


class OnstageBandMembers(models.Model):
    id = models.IntegerField(primary_key=True)
    relation = models.ForeignKey(Relations, models.DO_NOTHING, db_column="relation_id")
    band = models.ForeignKey(Bands, models.DO_NOTHING, db_column="band_id")
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
    updated_at = models.DateTimeField(blank=True, null=True)

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
    gap = models.TextField(blank=True, null=True)  # noqa: DJ001
    last = models.TextField(blank=True, null=True)  # noqa: DJ001
    last_date = models.TextField(blank=True, null=True)  # noqa: DJ001
    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    updated_at = models.DateTimeField(blank=True, null=True)

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
