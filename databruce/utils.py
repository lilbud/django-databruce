from datetime import datetime, time, timedelta

from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.cache import cache_page


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


def get_seconds_until_midnight():
  """Calculates how many seconds are left until the next midnight."""
  # Uses Django's timezone-aware datetime or local time depending on your settings
  now = timezone.now() if timezone.is_aware(timezone.now()) else datetime.now()

  # Target midnight tonight (technically tomorrow at 00:00:00)
  midnight = datetime.combine(now.date() + timedelta(days=1), time.min)
  if timezone.is_aware(now):
    midnight = timezone.make_aware(midnight, now.tzinfo)

  return int((midnight - now).total_seconds())


def cache_until_midnight(view_func):
  """Decorator that wraps cache_page with a dynamically evaluated timeout."""

  def _wrapped_view(request, *args, **kwargs):
    timeout = get_seconds_until_midnight()
    # Dynamically generate the cache page wrapper for this specific request timeout
    return cache_page(timeout)(view_func)(request, *args, **kwargs)

  return _wrapped_view
