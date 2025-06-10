import datetime

from debug_toolbar.toolbar import debug_toolbar_urls
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, reverse_lazy

from . import settings, views

date = datetime.datetime.today()

app_name = "databruce"
urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("admin/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),
    # path("", include("api.urls")),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="users/login.html"),
        name="login",
    ),
    path(
        "accounts/profile/",
        views.UserProfile.as_view(),
        name="profile",
    ),
    path(
        "accounts/settings/",
        views.UserSettings.as_view(),
        name="settings",
    ),
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(template_name="users/logout.html"),
        name="logout",
    ),
    path(
        "accounts/password_change/",
        auth_views.PasswordChangeView.as_view(
            template_name="users/change_password.html",
        ),
        name="password_change",
    ),
    path(
        "accounts/password_change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="users/change_password_done.html",
        ),
        name="password_change_done",
    ),
    path(
        "accounts/password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="users/reset_password.html",
            success_url=reverse_lazy("password_reset_done"),
            email_template_name="users/reset_password_email.html",
        ),
        name="password_reset",
    ),
    path(
        "accounts/password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="users/reset_password_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "accounts/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="users/reset_password_confirm.html",
            success_url=reverse_lazy("password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "accounts/reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="users/reset_password_done.html",
        ),
        name="password_reset_complete",
    ),
    path(
        "accounts/create/",
        views.SignUp.as_view(),
        name="signup",
    ),
    # path(
    #     "accounts/create/",
    #     views.SignUpConfirm.as_view(),
    #     name="signup_confirm",
    # ),
    path("events", views.Event.as_view(), name="events"),
    path("events/<int:year>", views.Event.as_view(), name="events_year"),
    path("events/<str:id>/", views.EventDetail.as_view(), name="event_details"),
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
        views.SetlistNotesSearch.as_view(),
        name="note_search",
    ),
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
    path("releases/nugs", views.NugsRelease.as_view(), name="nugs"),
    path("releases/bootleg", views.Bootleg.as_view(), name="bootlegs"),
    path("accounts/profile/add-show", views.UserAddShow.as_view(), name="add_show"),
]

if not settings.TESTING:
    urlpatterns = [*urlpatterns, *debug_toolbar_urls()]
