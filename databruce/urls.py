import datetime

from django.urls import include, path

from databruce import models

from . import views

date = datetime.datetime.today()

app_name = "databruce"
urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("events", views.Event.as_view(), name="events"),
    path("events/<int:year>", views.Event.as_view(), name="events_year"),
    path("events/<str:event>/", views.EventDetail.as_view(), name="event_details"),
    path("songs", views.Song.as_view(), name="songs"),
    path("songs/<int:id>", views.SongDetail.as_view(), name="song_details"),
    path("venues", views.Venue.as_view(), name="venues"),
    path("venues/<int:id>", views.VenueDetail.as_view(), name="venue_details"),
    path("tours", views.Tour.as_view(), name="tours"),
    path("tours/<int:id>", views.TourDetail.as_view(), name="tour_details"),
    path("search/results", views.EventSearch.as_view(), name="search"),
    path(
        "advanced_search/",
        views.AdvancedSearch.as_view(),
        name="adv_search",
    ),
    path(
        "notes_search/",
        views.SetlistSearch.as_view(),
        name="note_search",
    ),
    path("", include("api.urls")),
    path("relations", views.Relation.as_view(), name="relations"),
    path("relations/<int:id>", views.RelationDetail.as_view(), name="relation_details"),
    path("bands", views.Band.as_view(), name="bands"),
    path("bands/<int:id>", views.BandDetail.as_view(), name="band_details"),
    path("releases/", views.Release.as_view(), name="releases"),
    path("releases/<int:id>", views.ReleaseDetail.as_view(), name="release_details"),
    path("cities/", views.City.as_view(), name="cities"),
    path("cities/<int:id>", views.CityDetail.as_view(), name="city_details"),
    path("states/", views.State.as_view(), name="states"),
    path("states/<int:id>", views.StateDetail.as_view(), name="state_details"),
    path("countries/", views.Country.as_view(), name="countries"),
    path("countries/<int:id>", views.CountryDetail.as_view(), name="country_details"),
    path("events/runs", views.EventRun.as_view(), name="runs"),
    path("events/runs/<int:id>", views.RunDetail.as_view(), name="run_details"),
    path("tours/legs", views.TourLeg.as_view(), name="tour_legs"),
    path("tours/legs/<int:id>", views.TourLegDetail.as_view(), name="leg_details"),
]
