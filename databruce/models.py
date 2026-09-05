import re
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.db import models
from django.db.models import F, Func, Value
from django.db.models.functions import Lower, Trim
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from timezone_field import TimeZoneField

from .templatetags.filters import format_fuzzy
from .utils import generate_unique_slug


class CustomUser(AbstractUser):
  uuid = models.UUIDField(default=uuid4, unique=True, editable=False)
  discord_name = models.CharField(
    default=None,
    blank=True,
    null=True,
    db_column="discord_name",
  )

  groups = models.ManyToManyField(
    "auth.Group",
    blank=True,
  )
  user_permissions = models.ManyToManyField(
    "auth.Permission",
    blank=True,
  )

  def __str__(self) -> str:
    return self.username

  class Meta:
    db_table = "auth_user"  # Directs Django to the existing table
    verbose_name = "User"
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
    to="Event",
    on_delete=models.CASCADE,
    db_column="event_id",
    related_name="archive_links",
    null=True,
  )

  url = models.CharField(
    db_column="archive_url",
    blank=True,
    default=None,
    max_length=255,
  )

  class Meta:
    db_table = "archive_links"
    verbose_name = "archive link"
    verbose_name_plural = "archive links"

  def __str__(self) -> str:
    if not self.url:
      return ""

    return self.url


class Band(BaseModel):
  id = models.AutoField(primary_key=True)
  uuid = models.UUIDField(default=uuid4, editable=False)
  brucebase_url = models.CharField(default=None, blank=True, max_length=255)
  name = models.CharField(default=None, blank=True, max_length=255)
  num_events = models.IntegerField(default=0)

  first_event = models.ForeignKey(
    to="Event",
    on_delete=models.SET_NULL,
    related_name="band_first",
    db_column="first_event",
    default=None,
    null=True,
    blank=True,
  )

  last_event = models.ForeignKey(
    to="Event",
    on_delete=models.SET_NULL,
    related_name="band_last",
    db_column="last_event",
    default=None,
    null=True,
    blank=True,
  )

  bruce_band = models.BooleanField(default=False, db_column="springsteen_band")
  mbid = models.UUIDField(default=None, editable=True, null=True)
  note = models.CharField(default=None, blank=True, max_length=255)

  class Meta:
    db_table = "bands"
    verbose_name = "band"
    verbose_name_plural = "bands"

  def __str__(self) -> str:
    if not self.name:
      return ""

    return self.name


class Bootleg(BaseModel):
  id = models.AutoField(primary_key=True)
  uuid = models.UUIDField(default=uuid4, editable=False)
  slid = models.IntegerField(default=0)
  mbid = models.UUIDField(default=None, editable=True, null=True)

  event = models.ForeignKey(
    to="Event",
    on_delete=models.SET_NULL,
    db_column="event_id",
    related_name="bootleg_event",
    default=None,
    null=True,
    blank=True,
  )

  category = models.CharField(default=None, blank=True, max_length=255)
  title = models.CharField(default=None, blank=True, max_length=255)
  label = models.CharField(default=None, blank=True, max_length=255)
  source = models.CharField(default=None, blank=True, max_length=255)
  source_info = models.CharField(default=None, blank=True, max_length=255)
  version_info = models.CharField(default=None, blank=True, max_length=255)
  transfer = models.CharField(default=None, blank=True, max_length=255)
  editor = models.CharField(default=None, blank=True, max_length=255)
  type = models.CharField(default=None, blank=True, max_length=255)
  catalog_number = models.CharField(default=None, blank=True, max_length=255)
  media_type = models.CharField(default=None, blank=True, max_length=255)
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
    verbose_name = "bootleg"
    verbose_name_plural = "bootlegs"

  def __str__(self) -> str:
    if not self.title:
      return ""

    return self.title


class City(BaseModel):
  id = models.AutoField(primary_key=True)
  uuid = models.UUIDField(default=uuid4, editable=False)
  mbid = models.UUIDField(default=None, editable=True, null=True)
  name = models.CharField(default=None, max_length=255)

  state = models.ForeignKey(
    to="State",
    on_delete=models.CASCADE,
    related_name="city_state",
    db_column="state",
    default=None,
    blank=True,
    null=True,
  )

  country = models.ForeignKey(
    to="Country",
    on_delete=models.CASCADE,
    related_name="city_country",
    db_column="country",
    default=None,
    blank=True,
    null=True,
  )

  num_events = models.IntegerField(default=0)
  aliases = models.CharField(default=None, blank=True, max_length=255)

  first_event = models.ForeignKey(
    to="Event",
    on_delete=models.SET_NULL,
    related_name="city_first",
    db_column="first_event",
    default=None,
    blank=True,
    null=True,
  )

  last_event = models.ForeignKey(
    to="Event",
    on_delete=models.SET_NULL,
    related_name="city_last",
    db_column="last_event",
    default=None,
    blank=True,
    null=True,
  )

  timezone = TimeZoneField(use_pytz=False, default="UTC")

  class Meta:
    db_table = "cities"
    verbose_name = "city"
    verbose_name_plural = "cities"
    unique_together = (("name", "state"),)

  def __str__(self) -> str:
    if self.country_id in [6, 37] and self.state_id:  # type: ignore
      return f"{self.name}, {self.state.abbrev}"  # type: ignore

    return f"{self.name}, {self.country}"


class Continent(BaseModel):
  id = models.AutoField(primary_key=True)
  uuid = models.UUIDField(default=uuid4, editable=False)
  name = models.CharField(default=None, db_column="continent_name", max_length=255)
  num_events = models.IntegerField(default=0)

  class Meta:
    db_table = "continents"
    verbose_name = "continent"
    verbose_name_plural = "continents"

  def __str__(self) -> str:
    return self.name


class Country(BaseModel):
  id = models.AutoField(primary_key=True)
  uuid = models.UUIDField(default=uuid4, editable=False)
  name = models.CharField(unique=True, default=None, max_length=255)
  num_events = models.IntegerField(default=0)

  continent = models.ForeignKey(
    to="Continent",
    on_delete=models.SET_NULL,
    db_column="continent",
    default=None,
    blank=True,
    null=True,
  )

  alpha_2 = models.CharField(default=None, max_length=2)
  aliases = models.CharField(default=None, blank=True, max_length=255)
  mbid = models.UUIDField(default=None, editable=True, null=True)

  first_event = models.ForeignKey(
    to="Event",
    on_delete=models.SET_NULL,
    related_name="country_first",
    db_column="first_event",
    default=None,
    blank=True,
    null=True,
  )

  last_event = models.ForeignKey(
    to="Event",
    on_delete=models.SET_NULL,
    related_name="country_last",
    db_column="last_event",
    default=None,
    blank=True,
    null=True,
  )

  class Meta:
    db_table = "countries"
    verbose_name = "country"
    verbose_name_plural = "countries"

  def __str__(self) -> str:
    return self.name


class Cover(BaseModel):
  id = models.AutoField(primary_key=True)
  uuid = models.UUIDField(default=uuid4, editable=False)
  url = models.CharField(unique=True, default=None, max_length=255)

  event = models.ForeignKey(
    to="Event",
    on_delete=models.SET_NULL,
    db_column="event_id",
    default=None,
    blank=True,
    null=True,
  )

  class Meta:
    db_table = "covers"
    verbose_name = "cover"
    verbose_name_plural = "covers"

  def __str__(self) -> str:
    return self.url


class State(BaseModel):
  id = models.AutoField(primary_key=True)
  uuid = models.UUIDField(default=uuid4, editable=False)

  abbrev = models.CharField(
    unique=True,
    default=None,
    db_column="state_abbrev",
    max_length=2,
  )

  name = models.CharField(default=None, blank=True, max_length=255)

  country = models.ForeignKey(
    to=Country,
    on_delete=models.CASCADE,
    db_column="country",
  )

  num_events = models.IntegerField(default=0)
  mbid = models.UUIDField(default=None, editable=True, null=True)

  first_event = models.ForeignKey(
    to="Event",
    on_delete=models.SET_NULL,
    related_name="state_first",
    db_column="first_event",
    default=None,
    blank=True,
    null=True,
  )

  last_event = models.ForeignKey(
    to="Event",
    on_delete=models.SET_NULL,
    related_name="state_last",
    db_column="last_event",
    default=None,
    blank=True,
    null=True,
  )

  class Meta:
    db_table = "states"
    verbose_name = "state"
    verbose_name_plural = "states"

  def __str__(self) -> str:
    if not self.name:
      return ""

    return self.name


class Venue(BaseModel):
  id = models.AutoField(primary_key=True)
  uuid = models.UUIDField(default=uuid4, editable=False)
  brucebase_url = models.CharField(default=None, blank=True, max_length=255)
  name = models.CharField(default=None, max_length=255)
  detail = models.CharField(default=None, blank=True, max_length=255)

  city = models.ForeignKey(
    to=City,
    on_delete=models.CASCADE,
    db_column="city",
    related_name="venue_city",
    null=True,
    default=None,
  )

  num_events = models.IntegerField(default=0)
  note = models.CharField(default=None, blank=True, max_length=255)
  mbid = models.UUIDField(default=None, editable=True, null=True)

  first_event = models.ForeignKey(
    to="Event",
    on_delete=models.SET_NULL,
    db_column="first_event",
    related_name="venues_first",
    default=None,
    null=True,
    blank=True,
  )

  last_event = models.ForeignKey(
    to="Event",
    on_delete=models.SET_NULL,
    db_column="last_event",
    related_name="venues_last",
    default=None,
    null=True,
    blank=True,
  )

  address = models.CharField(max_length=255)

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

  parent = models.ForeignKey(
    to="self",
    on_delete=models.CASCADE,
    db_column="parent_id",
    default=None,
    null=True,
    blank=True,
  )

  class Meta:
    db_table = "venues"
    verbose_name = "venue"
    verbose_name_plural = "venues"

  def __str__(self) -> str:
    name = self.name

    if self.id == 351:  # noqa: PLR2004
      name = "Pierre's Good Citizens Ballpark"

    if self.id in [2040, 2844]:
      name = "The Big Joint"

    if self.detail:
      name = f"{self.name}, {self.detail}"

    return name

  def get_name(self) -> str:
    name = self.name

    if self.id == 351:  # noqa: PLR2004
      name = "Pierre's Good Citizens Ballpark"

    if self.id in (2040, 2844):
      name = "The Big Joint"

    if not name:
      return "N/A"

    return name


class VenueText(models.Model):
  id = models.OneToOneField(
    Venue,
    on_delete=models.DO_NOTHING,
    related_name="venues_text",
    primary_key=True,
    db_column="id",
  )

  location = models.CharField(max_length=255)
  formatted = models.CharField(db_column="full_location", max_length=255)

  class Meta:
    managed = False
    db_table = "venues_text"

  def __str__(self) -> str:
    return self.formatted


class VenueAlias(BaseModel):
  id = models.AutoField(primary_key=True)
  uuid = models.UUIDField(default=uuid4, editable=False)
  venue = models.ForeignKey(to=Venue, on_delete=models.CASCADE, null=True)
  name = models.CharField(max_length=255)
  note = models.CharField(max_length=255)

  class Meta:
    db_table = "venue_aliases"

  def __str__(self) -> str:
    return self.name


class Event(BaseModel):
  class EarlyLate(models.TextChoices):
    EVENING = "Evening", _("Evening")
    LATE = "Late", _("Late")
    THIRD = "Third", _("Third")
    EARLY = "Early", _("Early")
    AFTERNOON = "Afternoon", _("Afternoon")
    MORNING = "Morning", _("Morning")

  id = models.AutoField(primary_key=True)
  num = models.IntegerField(
    db_column="event_num",
    blank=True,
    null=True,
    default=None,
  )
  event_id = models.CharField(max_length=11, db_column="event_id", unique=True)
  date = models.DateField(default=None, db_column="event_date", blank=True)
  uuid = models.UUIDField(default=uuid4, editable=False)

  early_late = models.CharField(
    choices=EarlyLate.choices,
    default=None,
    blank=True,
    null=True,
  )

  public = models.BooleanField(default=False)

  artist = models.ForeignKey(
    to=Band,
    on_delete=models.SET_NULL,
    db_column="artist",
    default=None,
    blank=True,
    null=True,
  )

  brucebase_url = models.CharField(default=None, blank=True, max_length=255)

  venue = models.ForeignKey(
    to=Venue,
    on_delete=models.SET_NULL,
    related_name="event_venue",
    db_column="venue_id",
    default=None,
    blank=True,
    null=True,
  )

  tour = models.ForeignKey(
    to="Tour",
    on_delete=models.SET_NULL,
    db_column="tour_id",
    default=None,
    blank=True,
    null=True,
  )

  leg = models.ForeignKey(
    to="TourLeg",
    on_delete=models.SET_NULL,
    default=None,
    db_column="tour_leg",
    blank=True,
    null=True,
  )

  run = models.ForeignKey(
    to="Run",
    on_delete=models.SET_NULL,
    default=None,
    db_column="run",
    blank=True,
    null=True,
  )

  title = models.CharField(
    default=None,
    db_column="event_title",
    blank=True,
    null=True,
  )

  class EventCertainty(models.TextChoices):
    UNKNOWN_DATE = "Unknown Date", _("Unknown Date")
    CONFIRMED = "Confirmed", _("Confirmed")
    RUMORED = "Rumored", _("Rumored")
    PROBABLE = "Probable", _("Probable")
    UNKNOWN_LOCATION = "Unknown Location", _("Unknown Location")

  class SetlistCertainty(models.TextChoices):
    UNKNOWN = "Unknown", _("Unknown")
    CONFIRMED = "Confirmed", _("Confirmed")
    PROBABLE = "Probable", _("Probable")

  event_certainty = models.CharField(
    choices=EventCertainty.choices,
    default=None,
    blank=True,
    null=True,
  )

  setlist_certainty = models.CharField(
    choices=SetlistCertainty.choices,
    default=None,
    blank=True,
    null=True,
  )

  note = models.CharField(default=None, blank=True, max_length=255)
  summary = models.CharField(max_length=255, blank=True)

  bootleg = models.BooleanField(default=False)
  is_stats_eligible = models.BooleanField(default=True)

  start_time = models.DateTimeField(blank=True, default=None, null=True)
  end_time = models.DateTimeField(blank=True, default=None, null=True)
  scheduled_time = models.DateTimeField(blank=True, default=None, null=True)
  length = models.TimeField(blank=True, default=None, null=True)

  sales = models.BigIntegerField(blank=True, default=None, null=True)
  capacity = models.BigIntegerField(blank=True, default=None, null=True)
  gross = models.BigIntegerField(blank=True, default=None, null=True)
  ticket_min = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    blank=True,
    null=True,
    default=None,
  )
  ticket_max = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    blank=True,
    null=True,
    default=None,
  )
  box_office_source = models.CharField(blank=True, max_length=255, default=None)
  box_office_note = models.CharField(blank=True, max_length=255, default=None)
  sellout = models.BooleanField(blank=True, null=True, default=None)
  ticket_range = models.CharField(blank=True, max_length=255, default=None)
  promo_company = models.CharField(blank=True, max_length=255, default=None)

  type = models.ManyToManyField(
    "Type",
    through="EventType",
    related_name="types",
  )

  tags = models.ManyToManyField("Tag", through="EventTag", related_name="tags")

  class Meta:
    db_table = "events"
    verbose_name = "event"
    verbose_name_plural = "events"
    ordering = ["id", "event_id"]
    get_latest_by = "event_id"

  def __str__(self) -> str:
    if self.date:
      if self.early_late:
        return f"{self.date.strftime('%Y-%m-%d [%a]')} ({self.early_late})"

      return f"{self.date.strftime('%Y-%m-%d [%a]')}"

    return format_fuzzy(self.event_id)

  def save(self, *args, **kwargs):
    if self.note:
      # Strip out any raw HTML tag patterns
      text = re.sub(r"<[^>]*>", "", self.note)
      # Strip out markdown link formats like [anchor](url) -> anchor
      text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
      # Normalize internal multi-space gaps into single spaces
      text = re.sub(r"\s+", " ", text).strip()

      # Truncate string to 250 characters and append trailing ellipses
      if len(text) > 250:  # noqa: PLR2004
        self.summary = text[:250] + "..."
      else:
        self.summary = text
    else:
      self.summary = ""

    super().save(*args, **kwargs)

  def get_date(self) -> str:
    if self.date:
      if self.early_late:
        return f"{self.date.strftime('%Y-%m-%d')} ({self.early_late})"

      return f"{self.date.strftime('%Y-%m-%d')}"

    return format_fuzzy(self.event_id)

  def get_last(self):
    return (
      Event.objects.select_related("venue", "artist")
      .filter(event_id__lt=self.event_id)
      .order_by("-event_id")
      .first()
    )

  def get_next(self):
    return (
      Event.objects.select_related("venue", "artist")
      .filter(event_id__gt=self.event_id)
      .order_by("event_id")
      .first()
    )


class NugsRelease(BaseModel):
  id = models.AutoField(primary_key=True)
  uuid = models.UUIDField(default=uuid4, editable=False)
  nugs_id = models.IntegerField(default=0)

  event = models.ForeignKey(
    to=Event,
    on_delete=models.SET_NULL,
    db_column="event_id",
    related_name="nugs_event",
    blank=True,
    null=True,
  )

  date = models.DateTimeField(
    default=None,
    db_column="release_date",
    blank=True,
    null=True,
  )

  url = models.CharField(default=None, db_column="nugs_url", max_length=255)

  thumbnail = models.CharField(default=None, db_column="thumbnail_url", max_length=255)

  name = models.CharField(default=None, blank=True, max_length=255)

  first_friday = models.BooleanField(default=False, db_column="first_friday")

  class Meta:
    db_table = "nugs_releases"
    verbose_name = "nugs release"
    verbose_name_plural = "nugs releases"
    ordering = ["-event__id"]

  def __str__(self) -> str:
    return str(self.nugs_id)


class Relation(BaseModel):
  id = models.AutoField(primary_key=True)
  uuid = models.UUIDField(default=uuid4, editable=False)
  mbid = models.UUIDField(default=None, editable=True, null=True)
  brucebase_url = models.CharField(default=None, blank=True, max_length=255)
  name = models.CharField(default=None, blank=True, max_length=255)
  num_events = models.IntegerField(default=0)
  first_event = models.ForeignKey(
    to=Event,
    on_delete=models.SET_NULL,
    related_name="relation_first",
    db_column="first_event",
    default=None,
    blank=True,
    null=True,
  )
  last_event = models.ForeignKey(
    to=Event,
    on_delete=models.SET_NULL,
    related_name="relation_last",
    db_column="last_event",
    default=None,
    blank=True,
    null=True,
  )

  instruments = models.CharField(default=None, blank=True, max_length=255)
  start_date = models.DateField(default=None, blank=True)
  end_date = models.DateField(default=None, blank=True)
  show_cal = models.BooleanField(default=False, db_column="show_calendar")

  aliases = models.ManyToManyField(to="Relation", through="RelationAlias")

  class Meta:
    db_table = "relations"
    verbose_name = "relation"
    verbose_name_plural = "relations"

  def __str__(self) -> str:
    if not self.name:
      return ""

    return self.name


class RelationAlias(BaseModel):
  class AliasType(models.TextChoices):
    ALIAS = "alias", _("Alias")
    NICKNAME = "nickname", _("Nickname")

  id = models.UUIDField(primary_key=True)

  relation = models.ForeignKey(to=Relation, on_delete=models.CASCADE, null=True)

  name = models.CharField(max_length=255)

  type = models.CharField(
    choices=AliasType.choices,
    default=AliasType.ALIAS,
    max_length=50,
  )

  class Meta:
    db_table = "relation_aliases"

  def __str__(self) -> str:
    return self.name


class Onstage(BaseModel):
  id = models.AutoField(primary_key=True)

  uuid = models.UUIDField(default=uuid4, editable=False)

  event = models.ForeignKey(
    to=Event,
    on_delete=models.CASCADE,
    db_column="event_id",
    related_name="onstage_event",
    default=None,
    blank=True,
    null=True,
    db_index=True,
  )

  relation = models.ForeignKey(
    to=Relation,
    on_delete=models.CASCADE,
    db_column="relation_id",
    default=None,
  )

  band = models.ForeignKey(
    to=Band,
    on_delete=models.SET_NULL,
    db_column="band_id",
    related_name="onstage_band",
    to_field="id",
    default=None,
    blank=True,
    null=True,
  )

  note = models.CharField(default=None, blank=True, max_length=255)
  guest = models.BooleanField(default=False)

  class Meta:
    db_table = "onstage"
    verbose_name = "onstage"
    verbose_name_plural = "onstage"
    unique_together = ("event", "relation", "band")

  def __str__(self) -> str:
    name = getattr(self.relation, "name", None)

    try:
      band = getattr(self.band, "name", None)

      if band:
        return f"Relation: [{self.relation_id}] {name} / {band}"  # type: ignore
    except Onstage.band.RelatedObjectDoesNotExist:
      pass

    return f"Relation: [{self.relation_id}] {name}"  # type: ignore


class ReleaseTrack(BaseModel):
  id = models.AutoField(primary_key=True)
  uuid = models.UUIDField(default=uuid4, editable=False)

  release = models.ForeignKey(
    to="Release",
    on_delete=models.CASCADE,
    db_column="release_id",
    related_name="release_tracks",
  )

  discnum = models.IntegerField(db_column="disc_num")

  disc = models.ForeignKey(
    "ReleaseDisc",
    to_field="uuid",
    on_delete=models.SET_NULL,
    db_column="disc_id",
    default=None,
    blank=True,
    null=True,
  )

  track = models.CharField(db_column="track", max_length=255)

  position = models.IntegerField(default=1)

  song = models.ForeignKey(
    to="Song",
    on_delete=models.CASCADE,
    db_column="song_id",
    related_name="release_track_song",
  )

  event = models.ForeignKey(
    to=Event,
    on_delete=models.SET_NULL,
    related_name="release_track_event",
    db_column="event_id",
    default=None,
    blank=True,
    null=True,
  )

  note = models.CharField(default=None, blank=True, max_length=255)

  setlist = models.ForeignKey(
    to="Setlist",
    on_delete=models.SET_NULL,
    db_column="setlist_id",
    to_field="id",
    default=None,
    blank=True,
    null=True,
  )

  length = models.TimeField(default=None, blank=True)

  class Meta:
    db_table = "release_tracks"
    verbose_name = "release track"
    verbose_name_plural = "release tracks"
    ordering = ["release__name", "track"]

  def __str__(self) -> str:
    if self.disc:
      return f"{self.disc.name} - {self.song.name}"

    return f"Disc {self.discnum} - {self.song.name}"


class Release(BaseModel):
  class ReleaseType(models.TextChoices):
    LIVE = "Live", _("Live")
    COMPILATION = "Compilation", _("Compilation")
    STUDIO = "Studio", _("Studio")
    PODCAST = "Podcast", _("Podcast")
    RETROSPECTIVE = "Retrospective", _("Retrospective")

  class ReleaseFormat(models.TextChoices):
    AUDIO = "Audio", _("Audio")
    VIDEO = "Video", _("Video")

  id = models.AutoField(primary_key=True)
  uuid = models.UUIDField(default=uuid4, editable=False)
  brucebase_id = models.CharField(default=None, blank=True, max_length=255)
  name = models.CharField(default=None, blank=True, max_length=255)
  length = models.TimeField(default=None, blank=True)
  spotify_link = models.CharField(
    default=None,
    blank=True,
    null=True,
    db_column="spotify_url",
  )

  type = models.CharField(default=None, choices=ReleaseType.choices, max_length=50)

  format = models.CharField(
    default=None,
    choices=ReleaseFormat.choices,
    max_length=50,
  )
  date = models.DateField(
    default=None,
    db_column="release_date",
    verbose_name="Release Date",
  )
  short_name = models.CharField(default=None, blank=True, max_length=255)
  thumb = models.CharField(default=None, blank=True, max_length=255)
  note = models.CharField(default=None, blank=True, max_length=255)
  mbid = models.UUIDField(
    default=None,
    verbose_name="MusicBrainz ID",
    blank=True,
    null=True,
  )
  event = models.ForeignKey(
    to=Event,
    on_delete=models.SET_NULL,
    related_name="release_event",
    db_column="event_id",
    default=None,
    blank=True,
    null=True,
  )
  slug = models.SlugField(unique=True, blank=True)

  class Meta:
    db_table = "releases"
    verbose_name = "release"
    verbose_name_plural = "releases"

  def __str__(self) -> str:
    if not self.name:
      return ""

    return self.name

  def save(self, *args, **kwargs):
    # Pass the instance and specify the source field name
    generate_unique_slug(self, source_field="name")
    super().save(*args, **kwargs)


class SetlistNote(models.Model):
  id = models.AutoField(primary_key=True)

  setlist = models.ForeignKey(
    "Setlist",
    on_delete=models.CASCADE,
    db_column="setlist_id",
    related_name="setlist_notes",
  )

  event = models.ForeignKey(
    to=Event,
    on_delete=models.CASCADE,
    related_name="notes_event",
    db_column="event_id",
  )

  num = models.IntegerField(blank=False)
  note = models.CharField(default=None, blank=True, max_length=255)

  class Meta:
    managed = True
    db_table = "setlist_notes"
    verbose_name = "setlist note"
    verbose_name_plural = "setlist notes"

  def __str__(self) -> str:
    if not self.note:
      return ""

    return self.note


class Song(BaseModel):
  id = models.AutoField(primary_key=True)
  uuid = models.UUIDField(default=uuid4, editable=False)
  brucebase_url = models.CharField(default=None, blank=True, max_length=255)
  name = models.CharField(
    default=None,
    verbose_name="Name",
    db_column="song_name",
  )
  short_name = models.CharField(
    default=None,
    verbose_name="Short Name",
    blank=True,
    null=True,
  )

  slug = models.SlugField(unique=True, blank=True)

  first_event = models.ForeignKey(
    to=Event,
    on_delete=models.SET_NULL,
    related_name="song_first",
    verbose_name="First Played",
    db_column="first_event",
    default=None,
    blank=True,
    null=True,
  )

  last_event = models.ForeignKey(
    to=Event,
    on_delete=models.SET_NULL,
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

  original_artist = models.CharField(
    default=None,
    verbose_name="Original Artist",
    blank=True,
    null=True,
  )

  original = models.BooleanField(default=False)
  lyrics = models.BooleanField(default=False)

  category = models.CharField(default=None, blank=True, max_length=255)

  category_slug = models.SlugField(
    unique=True,
    blank=True,
    db_column="category_slug",
  )

  spotify_id = models.CharField(default=None, blank=True, max_length=255)

  mbid = models.UUIDField(default=None, editable=True, null=True)

  length = models.TimeField(default=None, blank=True, null=True)

  album = models.ForeignKey(
    to=Release,
    on_delete=models.SET_NULL,
    db_column="album",
    default=None,
    blank=True,
    null=True,
  )

  aliases = models.CharField(default=None, blank=True, max_length=255)

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
    output_field=models.CharField(max_length=255),
    db_persist=True,
  )

  search_vector = models.GeneratedField(
    expression=SearchVector("name", config="unaccent"),
    output_field=SearchVectorField(),
    db_persist=True,
    db_column="fts_name_vector",
  )

  class Meta:
    db_table = "songs"
    ordering = ["name"]
    verbose_name = "song"
    verbose_name_plural = "songs"

  def __str__(self) -> str:
    if not self.original:
      return f"{self.name} ({self.original_artist})"

    return f"{self.name}"

  def save(self, *args, **kwargs):
    # Pass the instance and specify the source field name
    generate_unique_slug(self, source_field="name")
    super().save(*args, **kwargs)


class SetType(models.TextChoices):
  SOUNDCHECK = "Soundcheck", _("Soundcheck")
  INTERVIEW = "Interview", _("Interview")
  POST_SHOW = "Post-Show", _("Post-Show")
  SET_1 = "Set 1", _("Set 1")
  SET_2 = "Set 2", _("Set 2")
  ENCORE = "Encore", _("Encore")
  PRE_SHOW = "Pre-Show", _("Pre-Show")
  SHOW = "Show", _("Show")
  RECORDING = "Recording", _("Recording")
  REHEARSAL = "Rehearsal", _("Rehearsal")

  @classmethod
  def valid_sets(cls) -> list[str]:
    return [
      cls.SHOW,
      cls.SET_1,
      cls.SET_2,
      cls.ENCORE,
      cls.PRE_SHOW,
      cls.POST_SHOW,
      cls.REHEARSAL,
    ]


class Setlist(BaseModel):
  class Position(models.TextChoices):
    ENCORE_OPENER = "Encore Opener", _("Encore Opener")
    SHOW_OPENER = "Show Opener", _("Show Opener")
    SET_2_OPENER = "Set 2 Opener", _("Set 2 Opener")
    SET_1_CLOSER = "Set 1 Closer", _("Set 1 Closer")
    MAIN_SET_CLOSER = "Main Set Closer", _("Main Set Closer")
    SET_2_CLOSER = "Set 2 Closer", _("Set 2 Closer")
    PRE_SHOW_OPENER = "Pre-Show Opener", _("Pre-Show Opener")
    PRE_SHOW_CLOSER = "Pre-Show Closer", _("Pre-Show Closer")

  id = models.AutoField(primary_key=True)
  uuid = models.UUIDField(default=uuid4, editable=False)

  event = models.ForeignKey(
    to=Event,
    on_delete=models.CASCADE,
    db_column="event_id",
    related_name="setlist_event",
    default=None,
    db_index=True,
  )

  set_name = models.CharField(
    max_length=50,
    choices=SetType.choices,
    default=SetType.SHOW,
  )

  song_num = models.IntegerField(
    default=1,
    blank=True,
    null=True,
  )

  song = models.ForeignKey(
    to=Song,
    on_delete=models.CASCADE,
    db_column="song_id",
    default=None,
    to_field="id",
  )

  note = models.CharField(
    default=None,
    db_column="song_note",
    blank=True,
    null=True,
    max_length=255,
  )
  segue = models.BooleanField(default=False)
  premiere = models.BooleanField(default=False)
  debut = models.BooleanField(default=False)
  instrumental = models.BooleanField(default=False)
  nobruce = models.BooleanField(default=False)

  position = models.CharField(
    default=None,
    blank=True,
    null=True,
    choices=Position.choices,
    max_length=50,
  )

  last = models.IntegerField(default=0)
  next = models.IntegerField(default=0)

  tour_num = models.IntegerField(default=0)
  tour_total = models.IntegerField(default=0)

  ltp = models.ForeignKey(
    to=Event,
    on_delete=models.SET_NULL,
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
    managed = True
    db_table = "setlists"
    ordering = ["set_name", "song_num"]
    verbose_name = "setlist"
    verbose_name_plural = "setlists"

    constraints = [
      # Enforces that set_name must strictly be one of the defined values
      models.CheckConstraint(
        condition=models.Q(set_name__in=SetType.values),
        name="valid_set_name",
      ),
    ]

  def __str__(self) -> str:
    event = getattr(self.event, "event_id", None)

    return f"{event} - {self.set_name} - {self.song}"


class SetlistsBySetAndDate(models.Model):
  id = models.AutoField(primary_key=True)
  set_order = models.IntegerField(default=0)

  event = models.ForeignKey(
    to="Event",
    on_delete=models.DO_NOTHING,
    default=None,
    db_column="event_id",
  )

  set_name = models.CharField(default=None, blank=True, max_length=255)
  setlist = models.CharField(default=None, blank=True, max_length=255)
  setlist_no_note = models.CharField(default=None, blank=True, max_length=255)

  class Meta:
    managed = False  # Created from a view. Don't remove.
    db_table = "setlists_by_set_and_date"
    ordering = ["set_order"]
    verbose_name = "setlist by set and date"
    verbose_name_plural = "setlists by set and date"

  def __str__(self) -> str:
    return f"{self.event} - {self.set_name}"


class Snippet(BaseModel):
  id = models.AutoField(primary_key=True)
  uuid = models.UUIDField(default=uuid4, editable=False)

  setlist = models.ForeignKey(
    to=Setlist,
    on_delete=models.CASCADE,
    db_column="setlist_id",
  )

  snippet = models.ForeignKey(
    to=Song,
    on_delete=models.SET_NULL,
    related_name="snippet",
    db_column="snippet_id",
    default=None,
    blank=True,
    null=True,
  )

  position = models.IntegerField(db_column="snippet_pos", default=1)

  note = models.CharField(
    default=None,
    db_column="snippet_note",
    blank=True,
    null=True,
  )

  class Meta:
    db_table = "snippets"
    ordering = ["position"]
    verbose_name = "snippet"
    verbose_name_plural = "snippets"

  def __str__(self) -> str:
    return f"{self.setlist} - {self.snippet}"


class Tour(BaseModel):
  id = models.AutoField(primary_key=True)
  uuid = models.UUIDField(default=uuid4, editable=False)
  brucebase_id = models.CharField(default=None, blank=True, max_length=255)
  brucebase_tag = models.CharField(default=None, blank=True, max_length=255)

  band = models.ForeignKey(
    to=Band,
    on_delete=models.SET_NULL,
    related_name="tour_band",
    db_column="band_id",
    default=None,
    blank=True,
    null=True,
  )

  name = models.CharField(default=None, db_column="tour_name", max_length=255)
  slug = models.SlugField(unique=True, blank=True)
  note = models.CharField(default=None, blank=True, max_length=255)

  first_event = models.ForeignKey(
    to=Event,
    on_delete=models.SET_NULL,
    related_name="tour_first",
    db_column="first_event",
    default=None,
    blank=True,
    null=True,
  )

  last_event = models.ForeignKey(
    to=Event,
    on_delete=models.SET_NULL,
    related_name="tour_last",
    db_column="last_event",
    default=None,
    blank=True,
    null=True,
  )

  num_events = models.IntegerField(default=0)
  num_songs = models.IntegerField(default=0)
  num_legs = models.IntegerField(default=0)

  class Meta:
    db_table = "tours"
    ordering = ["name"]
    verbose_name = "tour"
    verbose_name_plural = "tours"

  def __str__(self) -> str:
    return self.name

  def save(self, *args, **kwargs):
    # Pass the instance and specify the source field name
    generate_unique_slug(self, source_field="name")
    super().save(*args, **kwargs)


class TourLeg(BaseModel):
  id = models.AutoField(primary_key=True)
  uuid = models.UUIDField(default=uuid4, editable=False)

  tour = models.ForeignKey(
    Tour,
    on_delete=models.CASCADE,
    related_name="tour_id",
    db_column="tour_id",
  )

  name = models.CharField(default=None, blank=True, max_length=255)

  first_event = models.ForeignKey(
    to=Event,
    on_delete=models.SET_NULL,
    related_name="tourleg_first",
    db_column="first_event",
    default=None,
    blank=True,
    null=True,
  )
  last_event = models.ForeignKey(
    to=Event,
    on_delete=models.SET_NULL,
    related_name="tourleg_last",
    db_column="last_event",
    default=None,
    blank=True,
    null=True,
  )

  num_events = models.IntegerField(default=0)
  num_songs = models.IntegerField(default=0)
  note = models.CharField(default=None, blank=True, max_length=255)

  class Meta:
    db_table = "tour_legs"
    ordering = ["name"]
    verbose_name = "tour leg"
    verbose_name_plural = "tour legs"

  def __str__(self) -> str:
    if not self.name:
      return ""

    return self.name


class Run(BaseModel):
  id = models.AutoField(primary_key=True)
  uuid = models.UUIDField(default=uuid4, editable=False)

  band = models.ForeignKey(
    Band,
    on_delete=models.SET_NULL,
    db_column="band",
    null=True,
    blank=True,
    default=None,
  )

  venue = models.ForeignKey(
    Venue,
    on_delete=models.SET_NULL,
    db_column="venue",
    null=True,
    blank=True,
    default=None,
  )

  name = models.CharField(max_length=255)

  num_events = models.IntegerField(
    default=0,
  )

  num_songs = models.IntegerField(
    default=0,
  )

  first_event = models.ForeignKey(
    to=Event,
    on_delete=models.SET_NULL,
    db_column="first_event",
    related_name="event_run_first",
    null=True,
    blank=True,
    default=None,
  )
  last_event = models.ForeignKey(
    to=Event,
    on_delete=models.SET_NULL,
    db_column="last_event",
    related_name="event_run_last",
    null=True,
    blank=True,
    default=None,
  )
  note = models.CharField(default=None, blank=True, max_length=255)
  total_sales = models.IntegerField(blank=True)
  total_capacity = models.IntegerField(blank=True)
  total_gross = models.BigIntegerField(blank=True)
  ticket_min = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    blank=True,
    null=True,
  )
  ticket_max = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    blank=True,
    null=True,
  )
  ticket_range = models.CharField(blank=True, max_length=255)
  box_office_source = models.CharField(blank=True, max_length=255)
  box_office_note = models.CharField(blank=True, max_length=255)
  sellout = models.BooleanField(blank=True)
  promo_company = models.CharField(blank=True, max_length=255)
  num_sellout = models.IntegerField(blank=True)

  class Meta:
    db_table = "runs"
    ordering = ["name"]
    verbose_name = "run"
    verbose_name_plural = "runs"

  def __str__(self) -> str:
    if not self.name:
      return ""

    return self.name


class EventRankStat(models.Model):
  event = models.OneToOneField(
    Event,
    on_delete=models.DO_NOTHING,
    primary_key=True,
    db_column="id",
    related_name="rank_stats",
  )

  # Tour Stats
  tour_num = models.IntegerField()
  tour_total = models.IntegerField()

  # Leg Stats
  tour_leg_num = models.IntegerField(blank=True)
  tour_leg_total = models.IntegerField(blank=True)

  # Run Stats
  run_num = models.IntegerField(blank=True)
  run_total = models.IntegerField(blank=True)

  # Venue Stats
  venue_num = models.IntegerField()
  venue_total = models.IntegerField()

  # City Stats
  city_num = models.IntegerField()
  city_total = models.IntegerField()

  # Length Rank
  length_rank = models.IntegerField(blank=True)

  class Meta:
    managed = True
    db_table = "event_rank_stats"

  def __str__(self) -> str:
    return f"{self.event}"


class StudioSession(BaseModel):
  id = models.AutoField(primary_key=True)
  uuid = models.UUIDField(default=uuid4, editable=False)

  band = models.ForeignKey(
    Band,
    on_delete=models.SET_NULL,
    db_column="band",
    null=True,
  )

  name = models.CharField(max_length=255)
  num_events = models.IntegerField(default=0)
  num_songs = models.IntegerField(default=0)

  first_event = models.ForeignKey(
    to=Event,
    on_delete=models.SET_NULL,
    db_column="first_event",
    related_name="session_first_event",
    null=True,
  )

  last_event = models.ForeignKey(
    to=Event,
    on_delete=models.SET_NULL,
    db_column="last_event",
    related_name="session_last_event",
    null=True,
  )

  release = models.ForeignKey(
    Release,
    on_delete=models.SET_NULL,
    null=True,
    db_column="album",
  )

  class Meta:
    db_table = "studio_sessions"
    verbose_name = "studio session"
    verbose_name_plural = "studio sessions"

  def __str__(self) -> str:
    if not self.name:
      return ""

    return self.name


class UserAttendedShow(BaseModel):
  id = models.AutoField(primary_key=True)
  uuid = models.UUIDField(default=uuid4, editable=False)

  user = models.ForeignKey(
    to=CustomUser,
    on_delete=models.CASCADE,
    db_column="user_id",
    related_name="user_attended_shows",
  )

  event = models.ForeignKey(
    to=Event,
    on_delete=models.CASCADE,
    db_column="event_id",
    related_name="user_event",
  )

  class Meta:
    db_table = "user_attended_shows"
    verbose_name = "User Attended Show"
    verbose_name_plural = "User Attended Shows"
    unique_together = ("user", "event")

  def __str__(self) -> str:
    return f"{self.event} - {self.user}"


class Guest(BaseModel):
  id = models.AutoField(primary_key=True)
  uuid = models.UUIDField(default=uuid4, editable=False)

  setlist = models.ForeignKey(
    to=Setlist,
    on_delete=models.CASCADE,
    db_column="setlist_id",
  )

  relation = models.ForeignKey(
    to=Relation,
    on_delete=models.CASCADE,
    db_column="guest_id",
  )

  note = models.CharField(blank=True, default=None, max_length=255)

  class Meta:
    db_table = "guests"
    verbose_name = "guest"
    verbose_name_plural = "guests"

  def __str__(self) -> str:
    return f"{self.relation}"


class Lyric(BaseModel):
  id = models.AutoField(primary_key=True)
  uuid = models.UUIDField(default=uuid4, editable=False)

  song = models.ForeignKey(
    Song,
    on_delete=models.CASCADE,
    null=True,
    db_column="song_id",
    related_name="lyrics_song",
  )

  version = models.CharField(
    db_column="version_info",
    null=True,
    blank=True,
    default=None,
  )

  num = models.CharField(
    db_column="version_num",
    blank=True,
    default=None,
    max_length=255,
  )

  source = models.CharField(
    db_column="source_info",
    null=True,
    blank=True,
    default=None,
  )

  text = models.CharField(db_column="lyrics", blank=True, default=None, max_length=255)

  language = models.CharField(blank=True, default=None, max_length=255)
  note = models.CharField(blank=True, default=None, max_length=255)
  translator = models.CharField(blank=True, default=None, max_length=255)

  class Meta:
    db_table = "lyrics"
    verbose_name = "lyric"
    verbose_name_plural = "lyrics"

  def __str__(self) -> str:
    return f"{self.song}"


class Update(models.Model):
  id = models.AutoField(primary_key=True)
  item_id = models.CharField(max_length=255)
  item = models.CharField(max_length=255)
  value = models.CharField(db_column="to_value", max_length=255)
  view = models.CharField(max_length=255)
  msg = models.CharField(max_length=255)
  created_at = models.DateTimeField()

  class Meta:
    managed = False
    db_table = "updates"

  def __str__(self) -> str:
    return f"{self.item}: {self.value}"


class SiteUpdates(BaseModel):
  id = models.AutoField(primary_key=True)
  description = models.CharField(max_length=255)

  uuid = models.UUIDField(default=uuid4, editable=False)

  class Meta:
    db_table = "update_table"

  def __str__(self) -> str:
    return f"{self.description}"


class OnstageBandMember(models.Model):
  id = models.IntegerField(primary_key=True)

  relation = models.ForeignKey(
    Relation,
    on_delete=models.DO_NOTHING,
    db_column="relation_id",
  )

  band = models.ForeignKey(
    Band,
    on_delete=models.DO_NOTHING,
    db_column="band_id",
    blank=True,
    default=None,
  )

  count = models.IntegerField()

  first = models.ForeignKey(
    to=Event,
    on_delete=models.SET_NULL,
    related_name="onstagebandfirst",
    db_column="first",
    blank=True,
    default=None,
    null=True,
  )

  last = models.ForeignKey(
    to=Event,
    on_delete=models.SET_NULL,
    related_name="onstagebandlast",
    db_column="last",
    blank=True,
    default=None,
    null=True,
  )

  class Meta:
    managed = False
    db_table = "onstage_band_members"

  def __str__(self) -> str:
    return f"{self.relation}: {self.count}"


class ReleaseDisc(BaseModel):
  id = models.AutoField(primary_key=True)
  release = models.ForeignKey(Release, on_delete=models.CASCADE, db_column="release_id")
  disc_num = models.IntegerField()
  name = models.CharField(blank=False, null=False, max_length=255)
  uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
  updated_at = models.DateTimeField(null=True)

  class Meta:
    db_table = "release_discs"
    verbose_name = "Release Disc"
    verbose_name_plural = "Release Discs"

  def __str__(self) -> str:
    return f"Disc {self.disc_num}: {self.name}"


class SetlistEntries(models.Model):
  id = models.AutoField(primary_key=True)

  event = models.OneToOneField(
    Event,
    on_delete=models.DO_NOTHING,
    db_column="event_id",
  )

  show_opener = models.OneToOneField(
    to=Song,
    on_delete=models.DO_NOTHING,
    related_name="show_opener",
    db_column="show_opener",
  )

  s1_closer = models.OneToOneField(
    to=Song,
    on_delete=models.DO_NOTHING,
    related_name="s1_closer",
    db_column="s1_closer",
  )

  s2_opener = models.OneToOneField(
    to=Song,
    on_delete=models.DO_NOTHING,
    related_name="s2_opener",
    db_column="s2_opener",
  )

  main_closer = models.OneToOneField(
    to=Song,
    on_delete=models.DO_NOTHING,
    related_name="main_closer",
    db_column="main_closer",
  )

  encore_opener = models.OneToOneField(
    to=Song,
    on_delete=models.DO_NOTHING,
    related_name="encore_opener",
    db_column="encore_opener",
  )

  show_closer = models.OneToOneField(
    to=Song,
    on_delete=models.DO_NOTHING,
    related_name="show_closer",
    db_column="show_closer",
  )

  class Meta:
    managed = False
    db_table = "setlist_entries"

  def __str__(self) -> str:
    return f"{self.event}"


class Contact(BaseModel):
  class Subjects(models.TextChoices):
    PROBLEM = "problem", _("Bug/Problem")
    SUGGESTION = "suggestion", _("Suggestion")
    COMMENT = "comment", _("Comment")
    QUESTION = "question", _("Question")

  id = models.AutoField(primary_key=True)
  email = models.EmailField()
  is_user = models.BooleanField(default=False)
  subject = models.CharField(choices=Subjects.choices, max_length=50)
  message = models.CharField(max_length=255)

  class Meta:
    db_table = "contact"
    verbose_name = "Contact"
    verbose_name_plural = "Contact"
    managed = True

  def __str__(self) -> str:
    return f"Message from {self.email} - {self.subject}"


class SetlistPosition(models.Model):
  id = models.OneToOneField(
    Setlist,
    on_delete=models.DO_NOTHING,
    primary_key=True,
    db_column="id",
    related_name="setlist_position",
  )

  position = models.CharField(blank=True, max_length=255)

  class Meta:
    managed = False
    db_table = "setlist_positions"

  def __str__(self) -> str:
    return f"{self.id} - {self.position}"


class SongPage(models.Model):
  id = models.ForeignKey(
    Setlist,
    on_delete=models.DO_NOTHING,
    primary_key=True,
    related_name="songs_page",
    db_column="id",
  )

  prev = models.ForeignKey(
    Setlist,
    on_delete=models.DO_NOTHING,
    blank=True,
    null=True,
    related_name="prev_setlist",
    db_column="prev",
  )

  next = models.ForeignKey(
    Setlist,
    on_delete=models.DO_NOTHING,
    blank=True,
    null=True,
    related_name="next_setlist",
    db_column="next",
  )

  class Meta:
    managed = False
    db_table = "songs_page"

  def __str__(self) -> str:
    return f"{self.id}"


class SetlistStats(models.Model):
  setlist = models.OneToOneField(
    Setlist,
    on_delete=models.DO_NOTHING,
    primary_key=True,
    related_name="setlist_stats",
    db_column="id",
  )
  song_num = models.IntegerField(blank=True)
  set_name = models.CharField(blank=True, max_length=255)

  event = models.ForeignKey(
    to=Event,
    on_delete=models.DO_NOTHING,
    blank=True,
    null=True,
    db_column="event_id",
    related_name="stats_event",
  )

  total_event_songs = models.IntegerField(blank=True)
  global_first = models.BooleanField(blank=True)
  global_last = models.BooleanField(blank=True)
  set_first = models.BooleanField(blank=True)
  set_last = models.BooleanField(blank=True)
  is_the_main_closer = models.BooleanField(blank=True)
  show_has_encore = models.BooleanField(blank=True)
  gap = models.IntegerField(blank=True, db_column="calc_gap")

  ltp = models.ForeignKey(
    to=Event,
    on_delete=models.DO_NOTHING,
    blank=True,
    null=True,
    db_column="calc_last_ev_id",
    related_name="stats_ltp",
  )

  premiere = models.BooleanField(blank=True, db_column="is_premiere")
  debut = models.BooleanField(blank=True, db_column="is_debut")
  band_premiere = models.BooleanField(
    blank=True,
    null=True,
    db_column="is_band_premiere",
  )
  tour_num = models.IntegerField(blank=True, db_column="tour_num")
  tour_total = models.IntegerField(blank=True, db_column="tour_total")

  class Meta:
    managed = False
    db_table = "setlist_stats"

  def __str__(self) -> str:
    return f"{self.setlist}"


class Type(BaseModel):
  id = models.AutoField(primary_key=True)
  name = models.CharField(max_length=255)
  slug = models.SlugField(unique=True, blank=True)
  uuid = models.UUIDField(default=uuid4, editable=False)

  class Meta:
    db_table = "types"
    managed = True
    verbose_name = "Type"
    verbose_name_plural = "Types"

  def __str__(self) -> str:
    return self.name

  def save(self, *args, **kwargs):
    # Pass the instance and specify the source field name
    generate_unique_slug(self, source_field="name")
    super().save(*args, **kwargs)


class EventType(models.Model):
  id = models.AutoField(primary_key=True)

  event = models.ForeignKey(
    to=Event,
    on_delete=models.CASCADE,
    related_name="event_type",
  )

  type = models.ForeignKey(Type, on_delete=models.CASCADE, db_column="type_id")

  class Meta:
    managed = True
    db_table = "event_types"

    unique_together = ("event", "type")
    verbose_name = "Event Type"
    verbose_name_plural = "Event Types"

  def __str__(self) -> str:
    return f"{self.type}"


class Tag(BaseModel):
  id = models.AutoField(primary_key=True)
  name = models.CharField(max_length=255)
  slug = models.SlugField(unique=True, blank=True)
  description = models.CharField(blank=True, max_length=255)
  uuid = models.UUIDField(default=uuid4, editable=False)

  class Meta:
    managed = True
    db_table = "tags"

  def __str__(self) -> str:
    return self.name

  def save(self, *args, **kwargs):
    # Pass the instance and specify the source field name
    generate_unique_slug(self, source_field="name")
    super().save(*args, **kwargs)


class EventTag(models.Model):
  id = models.AutoField(primary_key=True)

  event = models.ForeignKey(
    to=Event,
    on_delete=models.CASCADE,
    db_column="event_id",
    related_name="event_tag",
  )

  tag = models.ForeignKey(Tag, on_delete=models.CASCADE, db_column="tag_id")

  class Meta:
    managed = True
    verbose_name = "Event Tag"
    verbose_name_plural = "Event Tags"
    db_table = "event_tags"

  def __str__(self) -> str:
    return f"{self.event} - {self.tag}"


class ItemInsertLog(models.Model):
  id = models.BigAutoField(primary_key=True)
  source_id = models.CharField(max_length=255)
  item_name = models.CharField(max_length=255)
  django_view = models.CharField(max_length=255, blank=True)
  source_created_at = models.DateTimeField()
  logged_at = models.DateTimeField(auto_now_add=True)
  message = models.CharField(blank=True, max_length=255)

  class Meta:
    managed = True
    verbose_name = "Item Insert Log"
    db_table = "item_insert_log"
    ordering = ["-source_created_at"]

  def __str__(self) -> str:
    return f"{self.message} (ID: {self.source_id})"
