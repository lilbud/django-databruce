from django.urls import include, path

from databruce import models

from . import views

app_name = "databruce"
urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("events", views.Events.as_view(), name="events"),
    path("events/<int:year>", views.Events.as_view(), name="events_year"),
    path("events/<str:event>/", views.EventDetail.as_view(), name="event_details"),
    path("songs", views.Songs.as_view(), name="songs"),
    path("songs/<int:id>", views.SongDetail.as_view(), name="song_details"),
    path("venues", views.Venues.as_view(), name="venues"),
    path("venues/<int:id>", views.VenueDetail.as_view(), name="venue_details"),
    path("tours", views.Tours.as_view(), name="tours"),
    path("tours/<int:id>", views.TourDetail.as_view(), name="tour_details"),
    path("search/results", views.EventSearch.as_view(), name="search"),
    path("advanced_search/", views.AdvancedSearch.as_view(), name="adv_search"),
    path(
        "advanced_search/results",
        views.AdvancedSearch.as_view(),
        name="adv_search_results",
    ),
    path("", include("api.urls")),
    path("relations", views.Relations.as_view(), name="relations"),
    path("relations/<int:id>", views.RelationDetail.as_view(), name="relation_details"),
    path("bands", views.Bands.as_view(), name="bands"),
    path("bands/<int:id>", views.BandDetail.as_view(), name="band_details"),
    path("releases/", views.Releases.as_view(), name="releases"),
    path("releases/<int:id>", views.ReleaseDetail.as_view(), name="release_details"),
    path("cities/", views.cities, name="cities"),
    path("cities/<int:id>", views.city_details, name="city_details"),
    path("states/", views.states, name="states"),
    path("states/<int:id>", views.state_details, name="state_details"),
    path("countries/", views.countries, name="countries"),
    path("countries/<int:id>", views.country_details, name="country_details"),
    path("events/runs", views.event_runs, name="runs"),
]
