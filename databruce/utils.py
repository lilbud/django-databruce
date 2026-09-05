from django.utils.text import slugify


def generate_unique_slug(instance, source_field="title", slug_field="slug"):
  """Generates a unique slug for a given model instance."""
  slug_value = getattr(instance, slug_field)

  # Only generate if the slug field is currently empty
  if not slug_value:
    source_text = getattr(instance, source_field)
    base_slug = slugify(source_text)
    slug = base_slug
    counter = 1
    klass = instance.__class__

    # Build dynamic lookup dictionary for the filter query
    while klass.objects.filter(**{slug_field: slug}).exclude(pk=instance.pk).exists():
      slug = f"{base_slug}-{counter}"
      counter += 1

    setattr(instance, slug_field, slug)
