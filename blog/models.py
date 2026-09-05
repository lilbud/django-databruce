from uuid import uuid4

from django.db import models as dj_models
from django.urls import reverse

from databruce.models import BaseModel, CustomUser
from databruce.utils import generate_unique_slug


class BlogCategory(BaseModel):
  id = dj_models.AutoField(primary_key=True)
  name = dj_models.CharField(max_length=100)
  slug = dj_models.SlugField(unique=True, blank=True)
  uuid = dj_models.UUIDField(default=uuid4, editable=False)
  created_at = dj_models.DateTimeField(auto_now_add=True)
  updated_at = dj_models.DateTimeField(auto_now=True)

  class Meta:
    db_table = "blog_category"
    verbose_name = "blog category"
    verbose_name_plural = "blog categories"

  def __str__(self) -> str:
    return self.name

  def save(self, *args, **kwargs):
    # Pass the instance and specify the source field name
    generate_unique_slug(self, source_field="name")
    super().save(*args, **kwargs)


class BlogTag(BaseModel):
  id = dj_models.AutoField(primary_key=True)
  name = dj_models.CharField(max_length=100)
  slug = dj_models.SlugField(unique=True, blank=True)

  class Meta:
    db_table = "blog_tags"
    verbose_name = "blog tag"
    verbose_name_plural = "blog tags"

  def __str__(self) -> str:
    return self.name

  def save(self, *args, **kwargs):
    # Pass the instance and specify the source field name
    generate_unique_slug(self, source_field="name")
    super().save(*args, **kwargs)


class BlogPost(BaseModel):
  id = dj_models.AutoField(primary_key=True)
  title = dj_models.CharField(max_length=255)
  slug = dj_models.SlugField(unique=True, blank=True)
  author = dj_models.ForeignKey(CustomUser, on_delete=dj_models.CASCADE)
  body = dj_models.TextField()
  excerpt = dj_models.CharField(max_length=255, blank=True)

  categories = dj_models.ManyToManyField(
    "BlogCategory",
    through="BlogPostCategory",
    related_name="posts",
  )

  tags = dj_models.ManyToManyField(
    "BlogTag",
    through="BlogPostTag",
    related_name="posts",
  )

  published = dj_models.BooleanField(default=False)
  published_at = dj_models.DateTimeField(blank=True, default=None, null=True)

  class Meta:
    db_table = "blog_posts"
    verbose_name = "blog post"
    verbose_name_plural = "blog posts"

  def __str__(self) -> str:
    return self.title

  def save(self, *args, **kwargs):
    # Pass the instance and specify the source field name
    generate_unique_slug(self, source_field="title")

    if not self.published_at:
      self.published_at = self.created_at

    super().save(*args, **kwargs)

  def get_absolute_url(self):
    return reverse(
      "blog:blog_post",
      args=[
        self.slug,
      ],
    )


class BlogPostTag(dj_models.Model):
  post = dj_models.ForeignKey(
    to=BlogPost,
    on_delete=dj_models.CASCADE,
    related_name="blog_post_tags",
    db_column="post_id",
  )

  tag = dj_models.ForeignKey(
    to=BlogTag,
    on_delete=dj_models.CASCADE,
    db_column="tag_id",
    related_name="post_tags",
  )

  class Meta:
    managed = True
    db_table = "blog_post_tags"
    verbose_name = "Blog Post Tag"
    verbose_name_plural = "Blog Post Tags"
    unique_together = (("post", "tag"),)

  def __str__(self) -> str:
    return f"{self.post} - {self.tag}"


class BlogPostCategory(dj_models.Model):
  post = dj_models.ForeignKey(
    to=BlogPost,
    on_delete=dj_models.CASCADE,
    related_name="blog_post_categories",
    db_column="post_id",
  )

  category = dj_models.ForeignKey(
    to=BlogCategory,
    on_delete=dj_models.CASCADE,
    db_column="category_id",
    related_name="post_categories",
  )

  class Meta:
    managed = True
    db_table = "blog_post_categories"
    verbose_name = "Blog Post Category"
    verbose_name_plural = "Blog Post Categories"
    unique_together = (("post", "category"),)

  def __str__(self) -> str:
    return f"{self.post} - {self.category}"


class BlogAuthor(BaseModel):
  author = dj_models.ForeignKey(CustomUser, on_delete=dj_models.DO_NOTHING)
  uuid = dj_models.UUIDField(default=uuid4, editable=False)

  class Meta:
    db_table = "blog_authors"
    verbose_name = "blog author"
    verbose_name_plural = "blog authors"

  def __str__(self) -> str:
    return f"{self.author}"
