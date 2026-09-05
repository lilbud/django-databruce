from uuid import uuid4

from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.db import models
from django.db.models import Value
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _

from databruce.models import BaseModel, Event
from databruce.utils import generate_unique_slug


class Collection(BaseModel):
  id = models.AutoField(primary_key=True)
  name = models.CharField(max_length=255, null=False, blank=False, default=None)
  slug = models.SlugField(unique=True, blank=True)
  uuid = models.UUIDField(default=uuid4, editable=False)
  description = models.TextField(default=None, blank=True)

  class Meta:
    managed = True
    db_table = "library_collection"

  def __str__(self) -> str:
    return self.name

  def save(self, *args, **kwargs):
    # Pass the instance and specify the source field name
    generate_unique_slug(self, source_field="name")
    super().save(*args, **kwargs)


class Article(BaseModel):
  class ArticleCategory(models.TextChoices):
    ALBUM_REVIEW = "album-review", _("Album Review")
    BOOK_EXCERPT = "book-excerpt", _("Book Excerpt")
    BOOK_REVIEW = "book-review", _("Book Review")
    COMMENTARY = "commentary", _("Commentary")
    CONCERT_REVIEW = "concert-review", _("Concert Review")
    COURT_CASE = "court-case", _("Court Case")
    ESSAY = "essay", _("Essay")
    EULOGY = "eulogy", _("Eulogy")
    FILM_REVIEW = "film-review", _("Film Review")
    INTERVIEW = "interview", _("Interview")
    NEWS = "news", _("News")
    OPINION = "opinion", _("Opinion")
    OTHER = "other", _("Other")
    SPEECH = "speech", _("Speech")
    THESIS = "thesis", _("Thesis")
    VIDEO_REVIEW = "video-review", _("Video Review")
    PRESS_RELEASE = "press-release", _("Press Release")
    HELP_WANTED = "help-wanted", _("Help Wanted")

  class ArticleLanguage(models.TextChoices):
    ENGLISH = "english", _("English")
    SPANISH = "spanish", _("Spanish")
    FRENCH = "french", _("French")
    GERMAN = "german", _("German")
    NORWEGIAN = "norwegian", _("Norwegian")
    SWEDISH = "swedish", _("Swedish")

  id = models.AutoField(primary_key=True)
  author = models.CharField(max_length=255)
  title = models.CharField(max_length=255)
  slug = models.SlugField(unique=True, blank=True)
  content = models.TextField()
  excerpt = models.CharField(max_length=255, blank=True, default=None)

  category = models.CharField(
    choices=ArticleCategory.choices,
    default=None,
    blank=True,
    max_length=255,
  )

  language = models.CharField(
    choices=ArticleLanguage.choices,
    default=None,
    blank=True,
    max_length=255,
  )

  published_at = models.DateField(
    blank=True,
    null=True,
    default=None,
    db_column="publish_date",
  )

  source = models.CharField(max_length=255)
  source_url = models.TextField(blank=True, default=None)

  collection = models.ForeignKey(
    to=Collection,
    on_delete=models.SET_NULL,
    blank=True,
    null=True,
    db_column="collection",
  )

  event = models.ForeignKey(
    Event,
    on_delete=models.DO_NOTHING,
    blank=True,
    null=True,
    related_name="event_article",
  )

  uuid = models.UUIDField(editable=False, default=uuid4)
  note = models.CharField(max_length=255, blank=True, default=None)

  fts_vector = models.GeneratedField(
    expression=(
      SearchVector(Coalesce("title", Value("")), weight="A", config="english")
      + SearchVector(Coalesce("author", Value("")), weight="B", config="english")
      + SearchVector(Coalesce("category", Value("")), weight="C", config="english")
      + SearchVector(Coalesce("content", Value("")), weight="D", config="english")
    ),
    output_field=SearchVectorField(),
    db_persist=True,
  )

  class Meta:
    managed = False
    db_table = "articles"
    verbose_name = "Article"
    verbose_name_plural = "Articles"
    indexes = [
      GinIndex(fields=["fts_vector"], name="idx_articles_fts_vector"),
    ]

  def __str__(self) -> str:
    return self.title

  def save(self, *args, **kwargs):
    # Pass the instance and specify the source field name
    generate_unique_slug(self, source_field="title")
    super().save(*args, **kwargs)
