import datetime

from debug_toolbar.toolbar import debug_toolbar_urls
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, reverse_lazy
from django.views.generic.base import TemplateView

from databruce import models

from . import views
from .config import base as settings
from .forms import CustomSetPasswordForm
from .sitemap import StaticViewSitemap

sitemaps = {
    "static": StaticViewSitemap,
}

date = datetime.datetime.today()


app_name = "databruce"
urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("__reload__/", include("django_browser_reload.urls")),
    path("about/", views.About.as_view(), name="about"),
    path("roadmap/", views.Roadmap.as_view(), name="roadmap"),
    path("links/", views.Links.as_view(), name="links"),
    path("s/", include("shortener.urls")),
    path("", include("api.urls", namespace="api")),
    path("benner/", admin.site.urls),
    path("test/", views.Test.as_view(), name="test"),
    path("calendar/", views.Calendar.as_view(), name="calendar"),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path(
        "login/",
        views.Login.as_view(),
        name="login",
    ),
    path(
        "profile/<uuid:id>",
        views.UserProfile.as_view(),
        name="profile",
    ),
    path(
        "contact/",
        views.Contact.as_view(),
        name="contact",
    ),
    path(
        "settings/",
        views.UserSettings.as_view(),
        name="settings",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(
            template_name="users/logout.html",
            next_page=reverse_lazy("login"),
        ),
        name="logout",
    ),
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="users/reset_password.html",
            success_url=reverse_lazy("password_reset_done"),
            email_template_name="databruce/email/reset_password_email.html",
            subject_template_name="users/reset_password_confirm_subject.txt",
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="users/reset_password_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            form_class=CustomSetPasswordForm,
            template_name="users/reset_password_confirm.html",
            success_url=reverse_lazy("login"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="users/reset_password_done.html",
        ),
        name="password_reset_complete",
    ),
    path(
        "signup/",
        views.SignUp.as_view(),
        name="signup",
    ),
    path(
        "signup/done/",
        views.SignUpDone.as_view(),
        name="signup_done",
    ),
    path(
        "signup/<uidb64>/<token>/",
        views.SignUpConfirm.as_view(),
        name="signup_confirm",
    ),
    path(
        "users",
        views.Users.as_view(),
        name="users",
    ),
    path("events", views.Event.as_view(), name="events"),
    path("events/<int:year>", views.Event.as_view(), name="events_year"),
    path("events/<str:id>/", views.EventDetail.as_view(), name="event_details"),
    path("events/type/<uuid:type>/", views.EventType.as_view(), name="events_by_type"),
    path("events/type", views.EventType.as_view(), name="events_type"),
    path("songs", views.Song.as_view(), name="songs"),
    path("songs/<uuid:id>", views.SongDetail.as_view(), name="song_details"),
    path("lyrics", views.SongLyrics.as_view(), name="song_lyrics"),
    path(
        "lyrics/<uuid:id>",
        views.SongLyricDetail.as_view(),
        name="lyric_detail",
    ),
    path("venues", views.Venue.as_view(), name="venues"),
    path("venues/<uuid:id>", views.VenueDetail.as_view(), name="venue_details"),
    path("tours", views.Tour.as_view(), name="tours"),
    path("tours/<uuid:id>", views.TourDetail.as_view(), name="tour_details"),
    path("search/results", views.EventSearch.as_view(), name="search"),
    path(
        "search/advanced/",
        views.AdvancedSearch.as_view(),
        name="adv_search",
    ),
    path(
        "search/advanced/results",
        views.AdvancedSearchResults.as_view(),
        name="adv_search_results",
    ),
    path(
        "short_url/",
        views.ShortenURL.as_view(),
        name="short_url",
    ),
    path(
        "search/notes/",
        views.SetlistNotesSearch.as_view(),
        name="note_search",
    ),
    path("relations", views.Relation.as_view(), name="relations"),
    path(
        "relations/<uuid:id>",
        views.RelationDetail.as_view(),
        name="relation_details",
    ),
    path("bands", views.Band.as_view(), name="bands"),
    path("bands/<uuid:id>", views.BandDetail.as_view(), name="band_details"),
    path("releases/", views.Release.as_view(), name="releases"),
    path("releases/<uuid:id>", views.ReleaseDetail.as_view(), name="release_details"),
    path("cities/", views.City.as_view(), name="cities"),
    path("cities/<uuid:id>", views.CityDetail.as_view(), name="city_details"),
    path("states/", views.State.as_view(), name="states"),
    path("states/<uuid:id>", views.StateDetail.as_view(), name="state_details"),
    path("countries/", views.Country.as_view(), name="countries"),
    path("countries/<uuid:id>", views.CountryDetail.as_view(), name="country_details"),
    path("events/runs", views.EventRun.as_view(), name="runs"),
    path("events/runs/<uuid:id>", views.RunDetail.as_view(), name="run_details"),
    path("tours/legs", views.TourLeg.as_view(), name="tour_legs"),
    path("tours/legs/<uuid:id>", views.TourLegDetail.as_view(), name="leg_details"),
    path("releases/nugs", views.NugsRelease.as_view(), name="nugs"),
    path("releases/bootlegs", views.Bootleg.as_view(), name="bootlegs"),
    path(
        "profile/add-show/",
        views.UserAddRemoveShow.as_view(),
        name="add_show",
    ),
    path(
        "profile/remove-show/",
        views.UserRemoveShow.as_view(),
        name="remove_show",
    ),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path("updates", views.Updates.as_view(), name="updates"),
]


if not settings.TESTING:
    urlpatterns = [*urlpatterns, *debug_toolbar_urls()]
