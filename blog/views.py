from typing import Any

import markdown
import nh3
from django import template
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.template import Context
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView

from databruce.views import PageTitleMixin

from .models import BlogCategory, BlogPost, BlogTag


class Blog(PageTitleMixin, TemplateView):
  template_name = "blog/blog.html"
  title = "Blog"

  def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
    context = super().get_context_data(**kwargs)
    posts = BlogPost.objects.all().order_by("-published_at", "-created_at")
    paginator = Paginator(posts, 10)
    page_number = self.request.GET.get("page", 1)
    context["page"] = paginator.get_page(page_number)

    return context


class BlogPostDetail(PageTitleMixin, TemplateView):
  template_name = "blog/post_detail.html"

  def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
    context = super().get_context_data(**kwargs)

    queryset = (
      BlogPost.objects.filter(published=True)
      .select_related("author")
      .prefetch_related(
        "categories",
        "tags",
      )
    )

    context["post"] = get_object_or_404(queryset, slug=self.kwargs["slug"])
    context["title"] = f"{context['post'].title}"
    context["description"] = f"{context['post'].excerpt}"

    value = nh3.clean(
      context["post"].body,
      tags={"figure", "div", "br", "code", "blockquote", "p", "a", "img"},
      attributes={
        "div": {"class"},
        "figure": {"class"},
        "a": {"href"},
        "img": {"src"},
      },
    )

    md = markdown.Markdown(extensions=["fenced_code", "toc"])
    post = md.convert(value)

    template_obj = template.Template(post)

    context_new = Context({"body": context["post"].body})

    # Use the existing context (which is already a Context object)
    context["body"] = mark_safe(template_obj.render(context_new))  # noqa: S308
    context["toc"] = md.toc  # type: ignore

    return context


class BlogCategoryView(PageTitleMixin, TemplateView):
  template_name = "blog/categories.html"
  title = "Blog Categories"

  def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
    context = super().get_context_data(**kwargs)
    context["categories"] = (
      BlogCategory.objects.all()
      .prefetch_related(
        "post_categories",
      )
      .order_by("name")
    )

    return context


class BlogTagView(PageTitleMixin, TemplateView):
  template_name = "blog/tags.html"
  title = "Blog Tags"

  def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
    context = super().get_context_data(**kwargs)
    context["tags"] = (
      BlogTag.objects.all()
      .prefetch_related(
        "post_tags",
      )
      .order_by("name")
    )

    return context


class BlogPostByCategory(PageTitleMixin, TemplateView):
  template_name = "blog/posts_by_category.html"

  def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
    context = super().get_context_data(**kwargs)
    category = self.kwargs["slug"]

    queryset = (
      BlogPost.objects.filter(categories__slug=category, published=True)
      .select_related("author")
      .prefetch_related(
        "categories",
        "tags",
      )
      .order_by("-published_at", "-created_at")
    )

    paginator = Paginator(queryset, 10)
    page_number = self.request.GET.get("page", 1)
    context["page"] = paginator.get_page(page_number)

    context["title"] = "Posts By Category"
    context["category"] = category

    return context


class BlogPostByTag(PageTitleMixin, TemplateView):
  template_name = "blog/posts_by_tag.html"

  def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
    context = super().get_context_data(**kwargs)
    tag = self.kwargs["slug"]

    queryset = (
      BlogPost.objects.filter(tags__slug=tag, published=True)
      .select_related("author")
      .prefetch_related(
        "categories",
        "tags",
      )
      .order_by("-published_at", "-created_at")
    )

    paginator = Paginator(queryset, 10)
    page_number = self.request.GET.get("page", 1)
    context["page"] = paginator.get_page(page_number)

    context["title"] = "Posts By Category"
    context["tag"] = tag

    return context
