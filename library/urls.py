from django.urls import path

from .views import (
  ArticleCategoryView,
  ArticleCollectionView,
  ArticleDetailView,
  ArticleListView,
  ArticleSearchView,
)

app_name = "library"
urlpatterns = [
  path("articles/", ArticleListView.as_view(), name="articles"),
  path("article/<str:slug>/", ArticleDetailView.as_view(), name="article_detail"),
  path(
    "category/<slug:slug>",
    ArticleCategoryView.as_view(),
    name="article_category",
  ),
  path(
    "collection/<slug:slug>",
    ArticleCollectionView.as_view(),
    name="article_collection",
  ),
  path(
    "search/",
    ArticleSearchView.as_view(),
    name="article_search",
  ),
]
