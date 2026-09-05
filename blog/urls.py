from django.urls import path

from .views import (
  Blog,
  BlogCategoryView,
  BlogPostByCategory,
  BlogPostByTag,
  BlogPostDetail,
  BlogTagView,
)

app_name = "blog"
urlpatterns = [
  path("blog/", Blog.as_view(), name="blog"),
  path(
    "blog/<slug:slug>/",
    BlogPostDetail.as_view(),
    name="blog_post",
  ),
  path(
    "blog/categories/<slug:slug>",
    BlogPostByCategory.as_view(),
    name="blog_post_category",
  ),
  path(
    "blog/categories/",
    BlogCategoryView.as_view(),
    name="blog_categories",
  ),
  path(
    "blog/tags/<slug:slug>",
    BlogPostByTag.as_view(),
    name="blog_post_tag",
  ),
  path(
    "blog/tags",
    BlogTagView.as_view(),
    name="blog_tags",
  ),
]
