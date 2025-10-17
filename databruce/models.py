# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.

from uuid import uuid4

from django.db import models


class ArchiveLinks(models.Model):
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
    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "archive_links"
        verbose_name_plural = "archive_links"


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = "auth_group"


class AuthGroupPermissions(models.Model):
    id = models.AutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey("AuthPermission", models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "auth_group_permissions"
        unique_together = (("group", "permission"),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey("DjangoContentType", models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = "auth_permission"
        unique_together = (("content_type", "codename"),)


class AuthUser(models.Model):
    id = models.AutoField(primary_key=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "auth_user"


class AuthUserGroups(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "auth_user_groups"
        unique_together = (("user", "group"),)


class AuthUserUserPermissions(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "auth_user_user_permissions"
        unique_together = (("user", "permission"),)


class Bands(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    brucebase_url = models.TextField(blank=True, default=None)
    name = models.TextField(blank=True, default=None)
    appearances = models.IntegerField(default=0)

    first = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="band_first",
        db_column="first_appearance",
        blank=True,
        default=None,
    )

    last = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="band_last",
        db_column="last_appearance",
        blank=True,
        default=None,
    )

    springsteen_band = models.BooleanField()
    mbid = models.UUIDField(default=None, editable=False)
    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "bands"
        verbose_name_plural = "bands"

    def __str__(self) -> str:
        return self.name


class Bootlegs(models.Model):
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
    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "bootlegs"
        verbose_name_plural = "bootlegs"


class BootlegsByDate(models.Model):
    event = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        db_column="event_id",
        blank=True,
        default=None,
    )
    date = models.TextField(blank=True, default=None)
    venue_location = models.TextField(blank=True, default=None)
    count = models.BigIntegerField(blank=True, default=None)

    class Meta:
        managed = False  # Created from a view. Don't remove.
        db_table = "bootlegs_by_date"
        verbose_name_plural = "Bootlegs By Date"


class Cities(models.Model):
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

    first = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="city_first",
        db_column="first_played",
        blank=True,
        default=None,
    )

    last = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="city_last",
        db_column="last_played",
        blank=True,
        default=None,
    )

    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "cities"
        verbose_name_plural = "cities"
        unique_together = (("name", "state"),)

    def __str__(self) -> str:
        try:
            if self.country.name == "United States":
                return f"{self.name}, {self.state.abbrev}"

            return f"{self.name}, {self.state}"  # noqa: TRY300

        except States.DoesNotExist:
            return f"{self.name}, {self.country}"


class Continents(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    name = models.TextField(blank=True, default=None, db_column="continent_name")
    num_events = models.IntegerField(default=0)

    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "continents"
        verbose_name_plural = "continents"

    def __str__(self) -> str:
        return self.name


class Countries(models.Model):
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
    alpha_3 = models.TextField(blank=True, default=None, max_length=3)
    aliases = models.TextField(blank=True, default=None)
    mbid = models.UUIDField(default=None, editable=False)

    first = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="country_first",
        db_column="first_played",
        blank=True,
        default=None,
    )

    last = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="country_last",
        db_column="last_played",
        blank=True,
        default=None,
    )

    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "countries"
        verbose_name_plural = "countries"

    def __str__(self) -> str:
        return self.name


class Covers(models.Model):
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

    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "covers"
        verbose_name_plural = "covers"


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, default=None)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey(
        "DjangoContentType",
        models.DO_NOTHING,
        blank=True,
        default=None,
    )
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "django_admin_log"


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = "django_content_type"
        unique_together = (("app_label", "model"),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "django_migrations"


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "django_session"


class States(models.Model):
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

    first = models.ForeignKey(
        "Events",
        models.DO_NOTHING,
        related_name="state_first",
        db_column="first_played",
    )

    last = models.ForeignKey(
        "Events",
        models.DO_NOTHING,
        related_name="state_last",
        db_column="last_played",
    )

    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "states"
        verbose_name_plural = "states"

    def __str__(self) -> str:
        if self.country.id not in [2, 6, 37]:
            return f"{self.name}, {self.country}"

        return self.name


class VenuesText(models.Model):
    id = models.ForeignKey(
        "Venues",
        on_delete=models.DO_NOTHING,
        primary_key=True,
        db_column="id",
    )

    name = models.TextField()
    location = models.TextField()
    formatted_loc = models.TextField()

    class Meta:
        managed = False
        db_table = "venues_text"
        verbose_name_plural = "venues_text"

    def __str__(self) -> str:
        return self.formatted_loc


class Venues(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    brucebase_url = models.TextField(unique=True, blank=True, default=None)
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

    state = models.ForeignKey(
        States,
        on_delete=models.CASCADE,
        db_column="state",
        related_name="venue_state",
        null=True,
        default=None,
    )

    country = models.ForeignKey(
        Countries,
        on_delete=models.CASCADE,
        db_column="country",
        related_name="venue_country",
        null=True,
        default=None,
    )

    continent = models.ForeignKey(
        Continents,
        on_delete=models.CASCADE,
        db_column="continent",
        related_name="venue_continent",
        null=True,
        default=None,
    )

    num_events = models.IntegerField(default=0)
    aliases = models.TextField(blank=True, default=None)
    mbid = models.UUIDField(default=None, editable=False)

    first = models.ForeignKey(
        "Events",
        models.DO_NOTHING,
        db_column="first_played",
        related_name="venues_first",
        blank=True,
        default=None,
    )

    last = models.ForeignKey(
        "Events",
        models.DO_NOTHING,
        db_column="last_played",
        related_name="venues_last",
        blank=True,
        default=None,
    )

    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "venues"
        verbose_name_plural = "venues"

    def __str__(self) -> str:
        name = self.name

        if self.detail:
            name = f"{self.name}, {self.detail}"

        if self.city:
            name += f", {self.city}"

        return name

    def get_name(self) -> str:
        if self.detail:
            return f"{self.name}, {self.detail}"

        return self.name


class SetlistsByDate(models.Model):
    event = models.OneToOneField(
        to="Events",
        on_delete=models.DO_NOTHING,
        blank=True,
        default=None,
        primary_key=True,
        db_column="event_id",
    )

    setlist = models.TextField(blank=True, default=None)

    class Meta:
        managed = False  # Created from a view. Don't remove.
        db_table = "setlists_by_date"
        verbose_name_plural = "setlists_by_date"


class Events(models.Model):
    num = models.IntegerField(db_column="event_num")
    id = models.TextField(primary_key=True, db_column="event_id")
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

    official_id = models.ForeignKey(
        to="Releases",
        on_delete=models.DO_NOTHING,
        blank=True,
        default=None,
        db_column="official_id",
    )

    nugs_id = models.ForeignKey(
        to="NugsReleases",
        on_delete=models.DO_NOTHING,
        blank=True,
        default=None,
        db_column="nugs_id",
    )

    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "events"
        verbose_name_plural = "events"
        unique_together = (("id", "date", "brucebase_url"),)
        ordering = ["id"]

    def __str__(self) -> str:
        try:
            event = self.date.strftime("%Y-%m-%d")
            if self.early_late:
                event += f" ({self.early_late})"
        except AttributeError:
            event = f"{self.id[0:4]}-{self.id[4:6]}-{self.id[6:8]}"

        return event

    def filter_date(self) -> str:
        return f"{self.id[0:4]}-{self.id[4:6]}-{self.id[6:8]}"

    def get_date(self) -> str:
        try:
            event = self.date.strftime("%Y-%m-%d")
            if self.early_late:
                event += f" ({self.early_late})"

        except AttributeError:
            event = f"{self.id[0:4]}-{self.id[4:6]}-{self.id[6:8]}"

        return event

    def get_last(self):
        return (
            Events.objects.select_related("venue", "artist")
            .filter(id__lt=self.id)
            .order_by("-id")
            .first()
        )

    def get_next(self):
        return (
            Events.objects.select_related("venue", "artist")
            .filter(id__gt=self.id)
            .order_by("id")
            .first()
        )


class NugsReleases(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    nugs_id = models.IntegerField(blank=True, default=None)
    event = models.ForeignKey(Events, models.DO_NOTHING, db_column="event_id")
    date = models.DateField(blank=True, default=None, db_column="release_date")
    url = models.TextField(blank=True, default=None, db_column="nugs_url")
    thumbnail = models.TextField(blank=True, default=None, db_column="thumbnail_url")
    name = models.TextField(blank=True, default=None)

    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "nugs_releases"
        verbose_name_plural = "nugs_releases"
        ordering = ["-event__id"]

    def __str__(self) -> str:
        return self.event.id


class OpenersClosers(models.Model):
    song_id = models.TextField(blank=True, default=None)
    position = models.TextField(blank=True, default=None)
    num = models.BigIntegerField(blank=True, default=None)

    class Meta:
        managed = False  # Created from a view. Don't remove.
        db_table = "openers_closers"
        verbose_name_plural = "openers_closers"


class PremiereDebut(models.Model):
    song_name = models.TextField(blank=True, default=None)
    debuts = models.TextField(blank=True, default=None)  # This field type is a guess.
    premiere = models.IntegerField(blank=True, default=None)

    class Meta:
        managed = False  # Created from a view. Don't remove.
        db_table = "premiere_debut"
        verbose_name_plural = "premiere_debut"


class Relations(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    mbid = models.UUIDField(default=None, editable=False)
    brucebase_url = models.TextField(blank=True, default=None)
    name = models.TextField(blank=True, default=None)
    appearances = models.IntegerField(default=0)
    first = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="relation_first",
        db_column="first_appearance",
        blank=True,
        default=None,
    )
    last = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="relation_last",
        db_column="last_appearance",
        blank=True,
        default=None,
    )
    aliases = models.TextField(blank=True, default=None)

    instruments = models.TextField(blank=True, default=None)

    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "relations"
        verbose_name_plural = "relations"

    def __str__(self) -> str:
        return self.name


class Onstage(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    event = models.ForeignKey(
        to=Events,
        on_delete=models.DO_NOTHING,
        db_column="event_id",
        blank=True,
        default=None,
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
        to_field="id",
        blank=True,
        default=None,
    )

    note = models.TextField(blank=True, default=None)
    guest = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "onstage"
        verbose_name_plural = "onstage"


class ReleaseTracks(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    release = models.ForeignKey("Releases", models.DO_NOTHING, db_column="release_id")
    track = models.IntegerField(db_column="track_num")

    song = models.ForeignKey(
        to="Songs",
        on_delete=models.DO_NOTHING,
        db_column="song_id",
        blank=True,
        default=None,
    )

    event = models.ForeignKey(Events, models.DO_NOTHING)
    note = models.TextField(blank=True, default=None)

    setlist = models.ForeignKey(
        to="Setlists",
        on_delete=models.DO_NOTHING,
        db_column="setlist_id",
        to_field="id",
        blank=True,
        default=None,
    )

    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "release_tracks"
        verbose_name_plural = "release_tracks"
        ordering = ["release__name", "track"]


class Releases(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    brucebase_id = models.TextField(blank=True, default=None)
    name = models.TextField(blank=True, default=None)
    type = models.TextField(blank=True, default=None)
    format = models.TextField(blank=True, default=None)
    date = models.DateField(blank=True, default=None, db_column="release_date")
    short_name = models.TextField(blank=True, default=None)
    thumb = models.TextField(blank=True, default=None)
    note = models.TextField(blank=True, default=None)
    mbid = models.UUIDField(default=None, editable=False)
    event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="release_event",
        db_column="event_id",
    )
    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "releases"
        verbose_name_plural = "releases"

    def __str__(self) -> str:
        return self.name


class SetlistNotes(models.Model):
    id = models.OneToOneField(
        "Setlists",
        models.DO_NOTHING,
        related_name="notes_setlist",
        db_column="id",
        primary_key=True,
    )

    event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="notes_event",
        db_column="event_id",
    )

    num = models.TextField(blank=True, default=None)
    note = models.TextField(blank=True, default=None)
    gap = models.TextField(blank=True, default=None)

    last = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="notes_last_event",
        db_column="last",
    )

    last_date = models.TextField(blank=True, default=None)

    class Meta:
        managed = False  # Created from a view. Don't remove.
        db_table = "setlist_notes"
        verbose_name_plural = "setlist_notes"


class Songs(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    brucebase_url = models.TextField(unique=True)
    name = models.TextField(
        blank=True,
        default=None,
        verbose_name="Name",
        db_column="song_name",
    )
    short_name = models.TextField(blank=True, default=None, verbose_name="Short Name")

    first = models.ForeignKey(
        to=Events,
        on_delete=models.DO_NOTHING,
        related_name="song_first",
        verbose_name="First Played",
        db_column="first_played",
        blank=True,
        default=None,
    )

    last = models.ForeignKey(
        to=Events,
        on_delete=models.DO_NOTHING,
        related_name="song_last",
        verbose_name="Last Played",
        db_column="last_played",
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
    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "songs"
        ordering = ["name"]
        verbose_name_plural = "songs"

    def __str__(self) -> str:
        name = self.name

        if self.short_name:
            name = self.short_name

        if not self.original:
            return f"{name} ({self.original_artist})"

        return self.name


class Setlists(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)

    event = models.ForeignKey(
        to=Events,
        on_delete=models.DO_NOTHING,
        db_column="event_id",
        blank=True,
        default=None,
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

    tour_num = models.IntegerField(blank=True, default=0)
    tour_total = models.IntegerField(blank=True, default=0)

    ltp = models.ForeignKey(
        to=Events,
        on_delete=models.DO_NOTHING,
        db_column="last_time_played",
        related_name="ltp_event",
        blank=True,
        default=None,
        to_field="id",
    )

    sign_request = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "setlists"
        verbose_name_plural = "setlists"
        unique_together = (("event_id", "song_num", "set_name", "song_id"),)
        ordering = ("-event_id", "song_num")

    def __str__(self) -> str:
        return f"{self.event.id} - {self.set_name} - {self.song} ({self.id})"

    def notes(self) -> str:
        noteslist = list(
            SetlistNotes.objects.filter(id=self.id).values_list("note", flat=True),
        )

        if noteslist:
            return "; ".join(noteslist)

        return ""


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


class Snippets(models.Model):
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

    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "snippets"
        verbose_name_plural = "snippets"


class SongGaps(models.Model):
    event_num = models.IntegerField(blank=True, default=None)
    last = models.TextField(blank=True, default=None)
    next = models.TextField(blank=True, default=None)
    last_time_played = models.TextField(blank=True, default=None)

    class Meta:
        managed = False  # Created from a view. Don't remove.
        db_table = "song_gaps"
        verbose_name_plural = "song_gaps"


class SongsAfterRelease(models.Model):
    song_id = models.TextField(blank=True, default=None)
    first_release = models.DateField(blank=True, default=None)
    first_event = models.TextField(blank=True, default=None)
    num_post_release = models.BigIntegerField(blank=True, default=None)

    class Meta:
        managed = False  # Created from a view. Don't remove.
        db_table = "songs_after_release"
        verbose_name_plural = "songs_after_release"


class Tags(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    event = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        to_field="id",
        db_column="event_id",
    )
    tags = models.TextField(blank=True, default=None)

    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "tags"
        verbose_name_plural = "tags"


class Tours(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    brucebase_id = models.TextField(blank=True, default=None, unique=True)
    brucebase_tag = models.TextField()

    band = models.ForeignKey(
        Bands,
        models.DO_NOTHING,
        related_name="tour_band",
        db_column="band_id",
    )

    name = models.TextField(blank=True, default=None, db_column="tour_name")
    slug = models.TextField(blank=True, default=None)

    first = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="tour_first",
        db_column="first_show",
    )

    last = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="tour_last",
        db_column="last_show",
    )

    num_shows = models.IntegerField(default=0)
    num_songs = models.IntegerField(default=0)
    num_legs = models.IntegerField(default=0)

    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "tours"
        verbose_name_plural = "tours"

    def __str__(self) -> str:
        return self.name


class TourLegs(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)

    tour = models.ForeignKey(
        Tours,
        models.DO_NOTHING,
        related_name="tour_id",
        db_column="tour_id",
    )

    name = models.TextField(blank=True, default=None)

    first = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="tourleg_first",
        db_column="first_show",
    )
    last = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="tourleg_last",
        db_column="last_show",
    )

    num_shows = models.IntegerField(default=0)
    num_songs = models.IntegerField(default=0)
    note = models.TextField(blank=True, default=None)

    class Meta:
        managed = False
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


class Runs(models.Model):
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
    name = models.TextField()
    num_shows = models.IntegerField(blank=True, null=True)
    num_songs = models.IntegerField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    first = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        db_column="first_event",
        blank=True,
        null=True,
    )
    last = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        db_column="last_event",
        related_name="runs_last_event_set",
        blank=True,
        null=True,
    )

    class Meta:
        managed = False
        db_table = "runs"
        verbose_name_plural = "runs"

    def __str__(self) -> str:
        return self.name


class StudioSessions(models.Model):
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
    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    first = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        db_column="first_event",
        related_name="session_first_event",
        blank=True,
        null=True,
    )

    last = models.ForeignKey(
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
        managed = False
        db_table = "studio_sessions"
        verbose_name_plural = "studio_sessions"


class UserAttendedShows(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid4, editable=False)
    user = models.ForeignKey(
        to=AuthUser,
        on_delete=models.DO_NOTHING,
        db_column="user_id",
    )
    event = models.ForeignKey(Events, models.DO_NOTHING, db_column="event_id")
    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "user_attended_shows"
        verbose_name_plural = "user_attended_shows"
        unique_together = ("user", "event")


class Guests(models.Model):
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

    event = models.ForeignKey(Events, models.DO_NOTHING, db_column="event_id")
    note = models.TextField(blank=True, null=True)  # noqa: DJ001
    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "guests"
        verbose_name_plural = "guests"


class Lyrics(models.Model):
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
    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    language = models.TextField(blank=True, null=True)  # noqa: DJ001
    note = models.TextField(blank=True, null=True)  # noqa: DJ001

    class Meta:
        managed = False
        db_table = "lyrics"


class Updates(models.Model):
    id = models.AutoField(primary_key=True)
    item_id = models.IntegerField(blank=True, null=True)
    item = models.TextField(blank=True, null=True)  # noqa: DJ001
    value = models.TextField(blank=True, null=True, db_column="to_value")  # noqa: DJ001
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    view = models.TextField(blank=True, null=True)  # noqa: DJ001
    msg = models.TextField(blank=True, null=True)  # noqa: DJ001

    class Meta:
        managed = False
        db_table = "updates"


class SiteUpdates(models.Model):
    id = models.AutoField(primary_key=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    uuid = models.UUIDField(default=uuid4, editable=False)

    class Meta:
        managed = False
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
    gap = models.IntegerField(blank=True, null=True)
    set_name = models.TextField(blank=True, null=True)  # noqa: DJ001
    prev = models.IntegerField(blank=True, null=True, db_column="prev_id")
    prev_name = models.TextField(blank=True, null=True)  # noqa: DJ001
    next = models.IntegerField(blank=True, null=True, db_column="next_id")
    next_name = models.TextField(blank=True, null=True)  # noqa: DJ001
    note = models.TextField(blank=True, null=True)  # noqa: DJ001

    class Meta:
        managed = False
        db_table = "songspagenew"
