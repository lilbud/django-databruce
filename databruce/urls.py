from django.urls import include, path

from databruce import models

from . import views

app_name = "databruce"
urlpatterns = [
    path("", views.index, name="index"),
    path("events", views.events, name="events"),
    path("events/<int:year>", views.events, name="events_year"),
    path("events/<str:event>/", views.event_details, name="event_details"),
    path("songs", views.songs, name="songs"),
    path("songs/<int:id>", views.song, name="song_details"),
    path("venues", views.venues, name="venues"),
    path("venues/<int:id>", views.venue, name="venue_details"),
    path("tours", views.tours, name="tours"),
    path("tours/<int:id>", views.tour_details, name="tour_details"),
    path("search/results", views.event_search, name="search"),
    path("advanced_search/", views.advanced_search, name="adv_search"),
    path("setlist_search/", views.setlist_search, name="setlist_search"),
    path(
        "setlist_search/results",
        views.setlist_search_results,
        name="setlist_search_results",
    ),
    path(
        "advanced_search/results",
        views.advanced_search_results,
        name="adv_search_results",
    ),
    path("", include("api.urls")),
    path("relations", views.relations, name="relations"),
    path("relations/<int:id>", views.relation_details, name="relation_details"),
    path("bands", views.bands, name="bands"),
    path("bands/<int:id>", views.band_details, name="band_details"),
    path("test/", views.test, name="test"),
    path("releases/", views.releases, name="releases"),
    path("releases/<int:id>", views.release_details, name="release_details"),
    path("cities/", views.cities, name="cities"),
    path("cities/<int:id>", views.city_details, name="city_details"),
    path("states/", views.states, name="states"),
    path("states/<int:id>", views.state_details, name="state_details"),
    path("countries/", views.countries, name="countries"),
    path("countries/<int:id>", views.country_details, name="country_details"),
    path("events/runs", views.event_runs, name="runs"),
]
