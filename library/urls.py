from django.urls import path

from . import views

app_name = "library"
urlpatterns = [
    path("articles/", views.Articles.as_view(), name="articles"),
    path("article/<str:slug>/", views.ArticleDetail.as_view(), name="article_detail"),
    path(
        "categories/<slug:slug>",
        views.ArticlesByCategory.as_view(),
        name="article_category",
    ),
    path(
        "search/",
        views.ArticleSearch.as_view(),
        name="article_search",
    ),
]
