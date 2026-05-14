from django.urls import path

from . import views

app_name = "blog"
urlpatterns = [
    path("blog/", views.Blog.as_view(), name="blog"),
    path(
        "blog/<slug:slug>/",
        views.BlogPost.as_view(),
        name="blog_post",
    ),
    path(
        "blog/categories/<slug:slug>",
        views.BlogPostByCategory.as_view(),
        name="blog_post_category",
    ),
    path(
        "blog/categories/",
        views.BlogCategories.as_view(),
        name="blog_categories",
    ),
    path(
        "blog/tags/<slug:slug>",
        views.BlogPostByTag.as_view(),
        name="blog_post_tag",
    ),
    path(
        "blog/tags",
        views.BlogTags.as_view(),
        name="blog_tags",
    ),
]
