from typing import Any

import markdown
import nh3
import strip_markdown
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView

from databruce import forms

from .models import Article, Collection


class ArticleListView(TemplateView):
  template_name = "library/articles.html"
  title = "Articles"

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context["title"] = self.title
    context["categories"] = Article.ArticleCategory.choices
    context["languages"] = Article.ArticleLanguage.choices

    return context


class ArticleDetailView(TemplateView):
  template_name = "library/article_detail.html"
  title = "Article"

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)

    context["article"] = get_object_or_404(
      Article,
      slug=self.kwargs["slug"],
    )

    context["title"] = f"{context['article'].title}"
    context["description"] = (
      f"{strip_markdown.strip_markdown(context['article'].content)[:100]}"
    )
    try:
      context["category"] = Article.ArticleCategory(
        context["article"].category,
      ).label
    except ValueError:
      context["category"] = None

    # Step 1: Convert raw Markdown into raw HTML first
    # Includes common extensions for blockquotes, code, and lists
    raw_html = markdown.markdown(
      context["article"].content,
      extensions=["fenced_code", "tables", "sane_lists"],
    )

    # Step 2: Sanitize the generated HTML output
    cleaned_html = nh3.clean(
      raw_html,
      tags={
        "figure",
        "figcaption",
        "div",
        "br",
        "code",
        "pre",
        "blockquote",
        "p",
        "a",
        "img",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "ul",
        "ol",
        "li",
        "strong",
        "em",
        "hr",
      },
      attributes={
        "div": {"class"},
        "figure": {"class"},
        "a": {"href", "title", "target", "rel"},
        "img": {"src", "alt", "title"},
        "code": {"class"},
      },
      link_rel=None,
    )

    # Step 3: Mark safe for rendering in Django templates
    context["body"] = mark_safe(cleaned_html)
    return context


class ArticleCategoryView(TemplateView):
  template_name = "library/articles_by_category.html"

  def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
    context = super().get_context_data(**kwargs)
    category = self.kwargs["slug"]

    queryset = Article.objects.filter(
      category=category,
    ).order_by("-published_at", "-created_at")

    paginator = Paginator(queryset, 10)
    page_number = self.request.GET.get("page", 1)
    context["page"] = paginator.get_page(page_number)

    context["title"] = "Articles By Category"
    context["category"] = Article.ArticleCategory(category).label

    return context


class ArticleCollectionView(TemplateView):
  template_name = "library/articles_by_collection.html"

  def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
    context = super().get_context_data(**kwargs)
    slug = self.kwargs["slug"]

    collection = get_object_or_404(Collection, slug=slug)

    context["collection"] = collection

    queryset = Article.objects.filter(
      collection__slug=slug,
    ).order_by("-published_at", "-created_at")

    paginator = Paginator(queryset, 10)
    page_number = self.request.GET.get("page", 1)
    context["page"] = paginator.get_page(page_number)

    context["title"] = "Articles By Collection"

    return context


class ArticleSearchView(TemplateView):
  template_name = "library/article_search.html"
  form_class = forms.ArticleSearch
  title = "Article Search"
  description = "Search for articles"

  def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
    context = super().get_context_data(**kwargs)
    context["form"] = self.form_class()
    context["title"] = self.title
    context["description"] = self.description

    return context
