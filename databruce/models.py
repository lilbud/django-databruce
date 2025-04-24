# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
import datetime

from django.db import models


class ArchiveLinks(models.Model):
    id = models.AutoField(primary_key=True, blank=True)
    event = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        db_column="event_id",
        blank=True,
        null=True,
    )

    archive_url = models.TextField(blank=True, null=True)  # noqa: DJ001
    updated_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        managed = False
        db_table = "archive_links"
        verbose_name_plural = db_table


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = "auth_group"


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
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
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(auto_now_add=True, blank=True)
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
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "auth_user_groups"
        unique_together = (("user", "group"),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "auth_user_user_permissions"
        unique_together = (("user", "permission"),)


class Bands(models.Model):
    id = models.AutoField(primary_key=True)
    brucebase_url = models.TextField(unique=True, blank=True, default="")
    name = models.TextField(blank=True, default="")
    appearances = models.IntegerField()

    first = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="band_first",
        db_column="first_appearance",
        blank=True,
        default="",
    )

    last = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="band_last",
        db_column="last_appearance",
        blank=True,
        default="",
    )

    springsteen_band = models.BooleanField()
    mbid = models.TextField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        managed = False
        db_table = "bands"
        verbose_name_plural = db_table

    def __str__(self):
        return self.name


class Bootlegs(models.Model):
    id = models.AutoField(primary_key=True)
    slid = models.IntegerField(blank=True, default="")
    mbid = models.TextField(blank=True, default="")

    event = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        db_column="event_id",
        blank=True,
        default="",
    )

    category = models.TextField(blank=True, default="")
    title = models.TextField(blank=True, default="")
    label = models.TextField(blank=True, default="")
    source = models.TextField(blank=True, default="")
    source_info = models.TextField(blank=True, default="")
    version_info = models.TextField(blank=True, default="")
    transfer = models.TextField(blank=True, default="")
    editor = models.TextField(blank=True, default="")
    type = models.TextField(blank=True, default="")
    catalog_number = models.TextField(blank=True, default="")
    media_type = models.TextField(blank=True, default="")
    has_info = models.BooleanField()
    has_artwork = models.BooleanField()
    archive_id = models.TextField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        managed = False
        db_table = "bootlegs"
        verbose_name_plural = db_table


class BootlegsByDate(models.Model):
    event = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        db_column="event_id",
        blank=True,
        default="",
    )
    date = models.TextField(blank=True, default="")
    venue_location = models.TextField(blank=True, default="")
    count = models.BigIntegerField(blank=True, default="")

    class Meta:
        managed = False  # Created from a view. Don't remove.
        db_table = "bootlegs_by_date"
        verbose_name_plural = "Bootlegs By Date"


class Cities(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField(blank=True, default="", db_column="name")

    state = models.ForeignKey(
        to="States",
        on_delete=models.DO_NOTHING,
        related_name="city_state",
        db_column="state",
        blank=True,
        default="",
    )

    country = models.ForeignKey(
        to="Countries",
        on_delete=models.DO_NOTHING,
        related_name="city_country",
        db_column="country",
        blank=True,
        default="",
    )

    num_events = models.IntegerField(blank=True, default="")
    aliases = models.TextField(blank=True, default="")

    first = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="city_first",
        db_column="first_played",
        blank=True,
        default="",
    )

    last = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="city_last",
        db_column="last_played",
        blank=True,
        default="",
    )

    updated_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        managed = False
        db_table = "cities"
        verbose_name_plural = db_table
        unique_together = (("name", "state"),)

    def __str__(self):
        try:
            state = f"{self.name}, {self.state}"
        except Cities.state.RelatedObjectDoesNotExist:
            state = f"{self.name}, {self.country}"
        except Cities.country.RelatedObjectDoesNotExist:
            state = self.name

        return state


class Continents(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField(blank=True, default="", db_column="continent_name")
    num_events = models.IntegerField()

    updated_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        managed = False

        db_table = "continents"
        verbose_name_plural = db_table

    def __str__(self):
        return self.name


class Countries(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField(unique=True, blank=True, default="")
    num_events = models.IntegerField(blank=True, default="")

    continent = models.ForeignKey(
        to="Continents",
        on_delete=models.DO_NOTHING,
        db_column="continent",
        blank=True,
        default="",
    )

    alpha_2 = models.TextField(blank=True, default="", max_length=2)
    alpha_3 = models.TextField(blank=True, default="", max_length=3)
    aliases = models.TextField(blank=True, default="")
    mbid = models.TextField(blank=True, default="")

    first = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="country_first",
        db_column="first_played",
        blank=True,
        default="",
    )

    last = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        related_name="country_last",
        db_column="last_played",
        blank=True,
        default="",
    )

    updated_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        managed = False
        db_table = "countries"
        verbose_name_plural = db_table

    def __str__(self):
        return self.name


class Covers(models.Model):
    id = models.AutoField(primary_key=True)
    event_date = models.TextField(blank=True, default="")
    cover_url = models.TextField(unique=True, blank=True, default="")

    event = models.ForeignKey(
        to="Events",
        on_delete=models.DO_NOTHING,
        db_column="event_id",
        blank=True,
        default="",
    )

    updated_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        managed = False
        db_table = "covers"
        verbose_name_plural = db_table


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, default="")
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey(
        "DjangoContentType",
        models.DO_NOTHING,
        blank=True,
        default="",
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


class Venues(models.Model):
    id = models.AutoField(primary_key=True)
    brucebase_url = models.TextField(unique=True, blank=True, default="")
    name = models.TextField(blank=True, default="")
    detail = models.TextField(unique=True, blank=True, default="")

    city = models.ForeignKey(
        Cities,
        on_delete=models.CASCADE,
        db_column="city",
        related_name="venue_city",
        null=True,
        default="",
    )

    state = models.ForeignKey(
        "States",
        on_delete=models.CASCADE,
        db_column="state",
        related_name="venue_state",
        null=True,
        default="",
    )

    country = models.ForeignKey(
        Countries,
        on_delete=models.CASCADE,
        db_column="country",
        related_name="venue_country",
        null=True,
        default="",
    )

    continent = models.ForeignKey(
        Continents,
        on_delete=models.CASCADE,
        db_column="continent",
        related_name="venue_continent",
        null=True,
        default="",
    )

    num_events = models.IntegerField()
    aliases = models.TextField(blank=True, default="")
    mb_id = models.TextField(blank=True, default="")

    first = models.ForeignKey(
        "Events",
        models.DO_NOTHING,
        db_column="first_played",
        related_name="venues_first",
        blank=True,
        default="",
    )

    last = models.ForeignKey(
        "Events",
        models.DO_NOTHING,
        db_column="last_played",
        related_name="venues_last",
        blank=True,
        default="",
    )

    updated_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        managed = False
        db_table = "venues"
        verbose_name_plural = db_table

    def __str__(self):
        venue = self.name

        if self.detail:
            venue += f", {self.detail}"

        return venue


class SetlistsByDate(models.Model):
    event = models.OneToOneField(
        to="Events",
        on_delete=models.DO_NOTHING,
        blank=True,
        default="",
        primary_key=True,
        db_column="event_id",
    )

    setlist = models.TextField(blank=True, default="")

    class Meta:
        managed = False  # Created from a view. Don't remove.
        db_table = "setlists_by_date"
        verbose_name_plural = db_table


class Events(models.Model):
    event_num = models.IntegerField()
    id = models.TextField(primary_key=True, db_column="event_id")
    event_date = models.DateField(blank=True, default="", db_column="event_date")
    early_late = models.TextField(blank=True, default="")
    public = models.BooleanField(blank=True, default=False)

    artist = models.ForeignKey(
        to=Bands,
        on_delete=models.DO_NOTHING,
        db_column="artist",
    )

    brucebase_url = models.TextField(blank=True, default="")

    venue = models.ForeignKey(
        to="Venues",
        on_delete=models.DO_NOTHING,
        related_name="event_venue",
        db_column="venue_id",
        blank=True,
        default="",
    )

    tour = models.ForeignKey(
        to="Tours",
        on_delete=models.DO_NOTHING,
        blank=True,
        default="",
        db_column="tour_id",
    )

    leg = models.ForeignKey(
        to="TourLegs",
        on_delete=models.DO_NOTHING,
        blank=True,
        default="",
        db_column="tour_leg",
    )

    event_type = models.TextField(blank=True, default="")
    event_title = models.TextField(blank=True, default="")
    event_certainty = models.TextField(blank=True, default="")
    setlist_certainty = models.TextField(blank=True, default="")
    event_date_note = models.TextField(blank=True, default="")
    bootleg = models.BooleanField(blank=True, default=False)
    official = models.BooleanField(blank=True, default=False)

    official_id = models.ForeignKey(
        to="Releases",
        on_delete=models.DO_NOTHING,
        blank=True,
        default="",
        db_column="official_id",
    )

    nugs = models.BooleanField(blank=True, default=False)
    nugs_id = models.ForeignKey(
        to="NugsReleases",
        on_delete=models.DO_NOTHING,
        blank=True,
        default="",
        db_column="nugs_id",
    )

    updated_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        managed = False
        db_table = "events"
        verbose_name_plural = db_table
        unique_together = (("id", "event_date", "brucebase_url"),)

    def __str__(self):
        try:
            event = self.event_date.strftime("%Y-%m-%d [%a]")
            if self.early_late:
                event += f" {self.early_late}"
        except AttributeError:
            event = f"{self.id[0:4]}-{self.id[4:6]}-{self.id[6:8]}"

        return event


class EventsWithInfo(models.Model):
    id = models.TextField(blank=True, db_column="event_id", primary_key=True)
    event_date = models.DateField(blank=True, default="", verbose_name="Date")
    event_type = models.TextField(blank=True, default="")
    event_title = models.TextField(blank=True, default="", verbose_name="Title")
    formatted_date = models.TextField(blank=True, default="")

    venue = models.ForeignKey(
        to="Venues",
        on_delete=models.DO_NOTHING,
        db_column="venue_id",
        blank=True,
        default="",
    )

    name = models.TextField(blank=True, default="")
    city = models.TextField(blank=True, default="")
    state_name = models.TextField(blank=True, default="")
    state = models.TextField(blank=True, default="")
    country = models.TextField(blank=True, default="")
    event_url = models.TextField(blank=True, default="")
    venue_loc = models.TextField(blank=True, default="")
    venue_url = models.TextField(blank=True, default="")
    artist_url = models.TextField(blank=True, default="")

    artist = models.ForeignKey(
        to="Bands",
        on_delete=models.DO_NOTHING,
        db_column="artist",
        blank=True,
        default="",
    )

    event_certainty = models.TextField(blank=True, default="")
    setlist_certainty = models.TextField(blank=True, default="")

    tour = models.ForeignKey(
        to="Tours",
        on_delete=models.DO_NOTHING,
        db_column="tour",
        blank=True,
        default="",
    )

    note = models.TextField(blank=True, default="")
    nugs_release = models.BooleanField(blank=True, default="")
    nugs_id = models.TextField(blank=True, default="")
    archive_url = models.TextField(blank=True, default="")

    class Meta:
        managed = False  # Created from a view. Don't remove.
        db_table = "events_with_info"
        verbose_name_plural = db_table


class EveryTimePlayed(models.Model):
    event_date = models.DateField(blank=True, default="")
    day = models.TextField(blank=True, default="")
    venue_loc = models.TextField(blank=True, default="")
    ssn = models.IntegerField(blank=True, default="")
    set_name = models.TextField(blank=True, default="")
    last = models.TextField(blank=True, default="")
    prev = models.TextField(blank=True, default="")
    song = models.TextField(blank=True, default="")
    next = models.TextField(blank=True, default="")
    pos = models.IntegerField(blank=True, default="")
    total = models.IntegerField(blank=True, default="")
    rel_pos = models.DecimalField(
        max_digits=10,
        decimal_places=5,
        blank=True,
        default="",
    )  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float

    class Meta:
        managed = False  # Created from a view. Don't remove.
        db_table = "every_time_played"
        verbose_name_plural = db_table


class NugsReleases(models.Model):
    id = models.AutoField(primary_key=True)
    nugs_id = models.IntegerField(blank=True, default="")
    event = models.ForeignKey(Events, models.DO_NOTHING, db_column="event_id")
    release_date = models.TextField(blank=True, default="")
    nugs_url = models.TextField(blank=True, default="")
    thumbnail_url = models.TextField(blank=True, default="")
    name = models.TextField(blank=True, default="")

    updated_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        managed = False
        db_table = "nugs_releases"
        verbose_name_plural = db_table


class OpenersClosers(models.Model):
    song_id = models.TextField(blank=True, default="")
    position = models.TextField(blank=True, default="")
    num = models.BigIntegerField(blank=True, default="")

    class Meta:
        managed = False  # Created from a view. Don't remove.
        db_table = "openers_closers"
        verbose_name_plural = db_table


# Unable to inspect table 'pg_stat_statements'
# The error was: pg_stat_statements must be loaded via shared_preload_libraries
# Unable to inspect table 'pg_stat_statements_info'
# The error was: pg_stat_statements must be loaded via shared_preload_libraries


class PremiereDebut(models.Model):
    song_name = models.TextField(blank=True, default="")
    debuts = models.TextField(blank=True, default="")  # This field type is a guess.
    premiere = models.IntegerField(blank=True, default="")

    class Meta:
        managed = False  # Created from a view. Don't remove.
        db_table = "premiere_debut"
        verbose_name_plural = db_table


class Relations(models.Model):
    id = models.AutoField(primary_key=True)
    brucebase_url = models.TextField(unique=True, blank=True, default="")
    name = models.TextField(blank=True, default="", db_column="relation_name")
    appearances = models.IntegerField()
    first = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="relation_first",
        db_column="first_appearance",
        blank=True,
        default="",
    )
    last = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="relation_last",
        db_column="last_appearance",
        blank=True,
        default="",
    )
    aliases = models.TextField(blank=True, default="")
    fts = models.TextField(blank=True, default="")  # This field type is a guess.
    instruments = models.TextField(blank=True, default="")

    updated_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        managed = False
        db_table = "relations"
        verbose_name_plural = db_table

    def __str__(self):
        return self.name


class Onstage(models.Model):
    id = models.AutoField(primary_key=True)
    event = models.ForeignKey(
        to=Events,
        on_delete=models.DO_NOTHING,
        db_column="event_id",
        blank=True,
        default="",
    )

    relation = models.ForeignKey(
        to=Relations,
        on_delete=models.DO_NOTHING,
        db_column="relation_id",
        blank=True,
        default="",
    )

    band = models.ForeignKey(
        to=Bands,
        on_delete=models.DO_NOTHING,
        db_column="band_id",
        to_field="id",
        blank=True,
        default="",
    )

    note = models.TextField(blank=True, default="")
    instruments = models.TextField(blank=True, default="")

    updated_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        managed = False
        db_table = "onstage"
        verbose_name_plural = db_table
        unique_together = (("event", "relation_id"),)


class ReleaseTracks(models.Model):
    id = models.AutoField(primary_key=True)
    release = models.ForeignKey("Releases", models.DO_NOTHING, db_column="release_id")
    track_num = models.IntegerField(db_column="track_num")

    song = models.ForeignKey(
        to="Songs",
        on_delete=models.DO_NOTHING,
        db_column="song_id",
        blank=True,
        default="",
    )

    event = models.ForeignKey(Events, models.DO_NOTHING)
    note = models.TextField(blank=True, default="")

    setlist_id = models.ForeignKey(
        to="Setlists",
        on_delete=models.DO_NOTHING,
        db_column="setlist_id",
        to_field="id",
        blank=True,
        default="",
    )

    updated_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        managed = False
        db_table = "release_tracks"
        verbose_name_plural = db_table


class Releases(models.Model):
    id = models.AutoField(primary_key=True)
    brucebase_id = models.TextField(blank=True, default="")
    name = models.TextField(blank=True, default="")
    type = models.TextField(blank=True, default="")
    date = models.DateField(blank=True, default="", db_column="release_date")
    short_name = models.TextField(blank=True, default="")
    thumb = models.TextField(blank=True, default="")
    mbid = models.TextField(blank=True, default="")
    fts = models.TextField(blank=True, default="")  # This field type is a guess.

    updated_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        managed = False
        db_table = "releases"
        verbose_name_plural = db_table

    def __str__(self):
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

    num = models.TextField(blank=True, default="")
    note = models.TextField(blank=True, default="")
    gap = models.TextField(blank=True, default="")
    last = models.TextField(blank=True, default="")
    last_date = models.TextField(blank=True, default="")

    class Meta:
        managed = False  # Created from a view. Don't remove.
        db_table = "setlist_notes"
        verbose_name_plural = db_table


class Songs(models.Model):
    id = models.AutoField(primary_key=True)
    brucebase_url = models.TextField(unique=True)
    song_name = models.TextField(blank=True, default="", verbose_name="Name")
    short_name = models.TextField(blank=True, default="", verbose_name="Short Name")

    first = models.ForeignKey(
        to=Events,
        on_delete=models.DO_NOTHING,
        related_name="song_first",
        verbose_name="First Played",
        db_column="first_played",
        blank=True,
        default="",
    )

    last = models.ForeignKey(
        to=Events,
        on_delete=models.DO_NOTHING,
        related_name="song_last",
        verbose_name="Last Played",
        db_column="last_played",
        blank=True,
        default="",
    )

    num_plays_public = models.IntegerField(verbose_name="Public")
    num_plays_private = models.IntegerField(verbose_name="Private")
    num_plays_snippet = models.IntegerField()
    opener = models.IntegerField(verbose_name="Opener")
    closer = models.IntegerField(verbose_name="Closer")
    cover = models.IntegerField()
    sniponly = models.IntegerField()
    original_artist = models.TextField(
        blank=True,
        default="",
        verbose_name="Original Artist",
    )
    aliases = models.TextField(blank=True, default="")
    fts = models.TextField(blank=True, default="")  # This field type is a guess.

    updated_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        managed = False
        db_table = "songs"
        verbose_name_plural = db_table

    def __str__(self):
        return self.song_name


class Setlists(models.Model):
    id = models.AutoField(primary_key=True)

    event = models.ForeignKey(
        to=Events,
        on_delete=models.DO_NOTHING,
        db_column="event_id",
        blank=True,
        default="",
    )

    set_name = models.TextField(blank=True, default="")
    song_num = models.IntegerField()

    song = models.ForeignKey(
        to=Songs,
        on_delete=models.DO_NOTHING,
        db_column="song_id",
        blank=True,
        default="",
    )

    song_note = models.TextField(blank=True, default="")
    segue = models.BooleanField()
    premiere = models.BooleanField()
    debut = models.BooleanField()
    position = models.TextField(blank=True, default="")
    last = models.TextField(blank=True, default="")
    next = models.TextField(blank=True, default="")
    last_time_played = models.TextField(blank=True, default="")
    band_premiere = models.BooleanField()
    sign_request = models.BooleanField()

    updated_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        managed = False
        db_table = "setlists"
        verbose_name_plural = db_table
        unique_together = (("event_id", "song_num", "song_id"),)


class SetlistsBySetAndDate(models.Model):
    id = models.AutoField(primary_key=True)
    min = models.IntegerField(blank=True, default="")

    event = models.ForeignKey(
        "Events",
        on_delete=models.DO_NOTHING,
        blank=True,
        default="",
        db_column="event_id",
    )

    set_name = models.TextField(blank=True, default="")
    setlist = models.TextField(blank=True, default="")
    setlist_no_note = models.TextField(blank=True, default="")

    class Meta:
        managed = False  # Created from a view. Don't remove.
        db_table = "setlists_by_set_and_date"
        verbose_name_plural = db_table


class Snippets(models.Model):
    id = models.AutoField(primary_key=True)
    event = models.ForeignKey(Events, models.DO_NOTHING)

    setlist = models.ForeignKey(
        Setlists,
        models.DO_NOTHING,
        db_column="setlist_song_id",
    )

    snippet = models.ForeignKey(
        to=Songs,
        on_delete=models.DO_NOTHING,
        related_name="snippet",
        db_column="snippet_id",
        blank=True,
        default="",
    )

    position = models.IntegerField(db_column="snippet_pos")
    snippet_note = models.TextField(blank=True, default="")

    updated_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        managed = False
        db_table = "snippets"
        verbose_name_plural = db_table


class SongGaps(models.Model):
    event_num = models.IntegerField(blank=True, default="")
    last = models.TextField(blank=True, default="")
    next = models.TextField(blank=True, default="")
    last_time_played = models.TextField(blank=True, default="")

    class Meta:
        managed = False  # Created from a view. Don't remove.
        db_table = "song_gaps"
        verbose_name_plural = db_table


class SongsAfterRelease(models.Model):
    song_id = models.TextField(blank=True, default="")
    first_release = models.DateField(blank=True, default="")
    first_event = models.TextField(blank=True, default="")
    num_post_release = models.BigIntegerField(blank=True, default="")

    class Meta:
        managed = False  # Created from a view. Don't remove.
        db_table = "songs_after_release"
        verbose_name_plural = db_table


class SongsFirstRelease(models.Model):
    song_id = models.TextField(blank=True, default="")
    date = models.TextField(blank=True, default="")
    year = models.TextField(blank=True, default="")
    release_name = models.TextField(blank=True, default="")
    brucebase_id = models.TextField(blank=True, default="")
    release_thumb = models.TextField(blank=True, default="")
    mbid = models.TextField(blank=True, default="")

    class Meta:
        managed = False  # Created from a view. Don't remove.
        db_table = "songs_first_release"


class States(models.Model):
    id = models.AutoField(primary_key=True)
    state_abbrev = models.TextField(unique=True, blank=True, default="")
    name = models.TextField(blank=True, default="")
    country = models.ForeignKey(Countries, models.DO_NOTHING, db_column="country")
    num_events = models.IntegerField()
    mbid = models.TextField(blank=True, default="")

    first = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="state_first",
        db_column="first_played",
    )

    last = models.ForeignKey(
        Events,
        models.DO_NOTHING,
        related_name="state_last",
        db_column="last_played",
    )

    updated_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        managed = False
        db_table = "states"
        verbose_name_plural = db_table

    def __str__(self):
        if self.country.name != "United States":
            state = f"{self.name}, {self.country.name}"
        else:
            state = self.name

        return state


class Tags(models.Model):
    id = models.AutoField(primary_key=True)
    event_id = models.ForeignKey(Events, models.DO_NOTHING)
    tags = models.TextField(blank=True, default="")

    updated_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        managed = False
        db_table = "tags"
        verbose_name_plural = db_table


class Tours(models.Model):
    id = models.AutoField(primary_key=True)
    brucebase_id = models.TextField(blank=True, default="", unique=True)
    brucebase_tag = models.TextField()

    band = models.ForeignKey(
        Bands,
        models.DO_NOTHING,
        related_name="tour_band",
        db_column="band_id",
    )

    name = models.TextField(blank=True, default="", db_column="tour_name")

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

    num_shows = models.IntegerField()
    num_songs = models.IntegerField()
    num_legs = models.IntegerField()

    updated_at = models.DateTimeField(auto_now_add=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        managed = False
        db_table = "tours"
        verbose_name_plural = db_table


class SongsPage(models.Model):
    id = models.AutoField(primary_key=True)

    event = models.ForeignKey(
        to=Events,
        on_delete=models.DO_NOTHING,
        db_column="event_id",
        blank=True,
        default="",
    )

    venue_id = models.IntegerField()
    formatted_loc = models.TextField(blank=True, default="")
    gap = models.IntegerField()
    set_name = models.TextField(blank=True, default="")
    song_num = models.IntegerField()

    prev = models.ForeignKey(
        to=Setlists,
        on_delete=models.DO_NOTHING,
        related_name="prev_setlist",
        db_column="prev_id",
        blank=True,
        default="",
    )

    setlist_id = models.ForeignKey(
        to=Setlists,
        on_delete=models.DO_NOTHING,
        related_name="current_setlist",
        db_column="setlist_id",
        blank=True,
        default="",
    )

    next = models.ForeignKey(
        to=Setlists,
        on_delete=models.DO_NOTHING,
        related_name="next_setlist",
        db_column="next_id",
        blank=True,
        default="",
    )

    song_note = models.TextField(blank=True, default="")

    class Meta:
        managed = False
        db_table = "song_page"
        verbose_name_plural = db_table


class VenuesText(models.Model):
    id = models.OneToOneField(
        Venues,
        models.DO_NOTHING,
        db_column="id",
        primary_key=True,
    )
    brucebase_url = models.TextField(blank=True, default="")
    formatted_loc = models.TextField(blank=True, default="")
    name = models.TextField(blank=True, default="")
    city = models.TextField(blank=True, default="")
    state = models.TextField(blank=True, default="")
    country = models.TextField(blank=True, default="")
    aliases = models.TextField(blank=True, default="")
    num_events = models.IntegerField()

    class Meta:
        managed = False
        db_table = "venues_text"
        verbose_name_plural = db_table


class TourLegs(models.Model):
    id = models.AutoField(primary_key=True)

    tour = models.ForeignKey(
        Tours,
        models.DO_NOTHING,
        related_name="tour_id",
        db_column="tour_id",
    )

    name = models.TextField(blank=True, default="")

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

    num_shows = models.IntegerField()
    note = models.TextField(blank=True, default="")

    class Meta:
        managed = False
        db_table = "tour_legs"
        verbose_name_plural = db_table


class SongsPageNew(models.Model):
    id = models.OneToOneField(
        Songs,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column="id",
    )

    prev = models.ForeignKey(
        to=Setlists,
        on_delete=models.DO_NOTHING,
        related_name="new_prev",
        db_column="prev",
        null=True,
        default="",
    )

    current = models.ForeignKey(
        to=Setlists,
        on_delete=models.DO_NOTHING,
        related_name="new_current",
        db_column="current",
        blank=True,
        default="",
    )

    next = models.ForeignKey(
        to=Setlists,
        on_delete=models.DO_NOTHING,
        related_name="new_next",
        db_column="next",
        null=True,
        default="",
    )

    class Meta:
        managed = False
        db_table = "songs_page_new"
        verbose_name_plural = db_table
