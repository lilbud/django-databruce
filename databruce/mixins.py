import datetime
from typing import Any

from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from django.views.generic.base import ContextMixin


class PageTitleMixin(ContextMixin):
  def get_page_title(self, _context) -> Any | None:
    return getattr(self, "title", None)

  def get_page_description(self, _context) -> Any | None:
    return getattr(self, "description", None)

  def get_context_data(self, **kwargs) -> dict[str, Any]:
    context = super().get_context_data(**kwargs)
    context["title"] = self.get_page_title(context)
    context["description"] = self.get_page_description(context)
    context["date"] = datetime.datetime.today()

    return context


class GroupRequiredMixin(AccessMixin):
  """CBV mixin to restrict access by group names."""

  allowed_groups = ["Beta Testers", "Admin"]

  def dispatch(self, request, *args, **kwargs):
    if not request.user.is_authenticated:
      return self.handle_no_permission()

    # Check if the user belongs to any group in allowed_groups
    in_group = request.user.groups.filter(name__in=self.allowed_groups).exists()

    if not in_group and not request.user.is_superuser:
      raise PermissionDenied

    return super().dispatch(request, *args, **kwargs)  # type: ignore
