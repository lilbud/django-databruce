import datetime

from debug_toolbar.toolbar import debug_toolbar_urls
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, re_path, reverse_lazy
from django.views.generic.base import TemplateView
from drf_spectacular.views import (
  SpectacularAPIView,
  SpectacularRedocView,
  SpectacularSwaggerView,
)

from .config import base as settings
from .forms import CustomSetPasswordForm
from .sitemap import StaticViewSitemap
from .views import (
  AboutView,
  AdvancedSearchView,
  AdvSearchView,
  BandDetailView,
  BandView,
  BootlegView,
  CalendarView,
  CityDetailView,
  CityView,
  ContactView,
  CountryDetailView,
  CountryView,
  EventDetailMobileView,
  EventDetailTestView,
  EventDetailView,
  EventRunView,
  EventSearchView,
  EventTagView,
  EventTypeView,
  EventView,
  IndexView,
  LinksView,
  LoginView,
  LyricDetailView,
  LyricsView,
  NugsReleaseView,
  RelationDetailView,
  RelationView,
  ReleaseDetailView,
  ReleaseView,
  RoadmapView,
  RunDetailView,
  SetlistNotesSearchView,
  ShortenURLView,
  SignUpConfirmView,
  SignUpDoneView,
  SignUpView,
  SongDetailView,
  SongView,
  StateDetailView,
  StateView,
  TestEventView,
  TestTableView,
  TestView,
  TourDetailView,
  TourLegDetailView,
  TourLegView,
  TourView,
  UpdateView,
  UserAddRemoveShowView,
  UserChangePasswordView,
  UserProfileView,
  UserRemoveShowView,
  UserSettingsView,
  UserView,
  VenueDetailView,
  VenueView,
  event_search,
)

sitemaps = {
  "static": StaticViewSitemap,
}

date = datetime.datetime.today()

app_name = "databruce"
urlpatterns = [
  path("", IndexView.as_view(), name="index"),
  path("__reload__/", include("django_browser_reload.urls")),
  path("about/", AboutView.as_view(), name="about"),
  path("roadmap/", RoadmapView.as_view(), name="roadmap"),
  path("links/", LinksView.as_view(), name="links"),
  path("s/", include("shortener.urls")),
  path("", include("api.urls", namespace="api")),
  path("", include("blog.urls", namespace="blog")),
  path("", include("select2.urls", namespace="select2")),
  path("library/", include("library.urls", namespace="library")),
  path("bruceyversion/", include("bruceyversion.urls", namespace="bruceyversion")),
  path("benner/", admin.site.urls),
  path("test/", TestView.as_view(), name="test"),
  path("calendar/", CalendarView.as_view(), name="calendar"),
  path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
  path(
    "login/",
    LoginView.as_view(),
    name="login",
  ),
  path(
    "profile/<uuid:id>",
    UserProfileView.as_view(),
    name="profile",
  ),
  path(
    "contact/",
    ContactView.as_view(),
    name="contact",
  ),
  path(
    "settings/",
    UserSettingsView.as_view(),
    name="settings",
  ),
  path(
    "event_search/",
    event_search,
    name="event_search",
  ),
  path(
    "change-password/",
    UserChangePasswordView.as_view(),
    name="change_password",
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
    SignUpView.as_view(),
    name="signup",
  ),
  path(
    "signup/done/",
    SignUpDoneView.as_view(),
    name="signup_done",
  ),
  path(
    "signup/<uidb64>/<token>/",
    SignUpConfirmView.as_view(),
    name="signup_confirm",
  ),
  re_path(
    "^users/?$",
    UserView.as_view(),
    name="users",
  ),
  re_path("^events/?$", EventView.as_view(), name="events"),
  path("events/<int:year>", EventView.as_view(), name="events_year"),
  path("events/<str:id>/", EventDetailView.as_view(), name="event_details"),
  path(
    "events_mobile/<str:id>/",
    EventDetailMobileView.as_view(),
    name="event_details_mobile",
  ),
  path(
    "events_test/<str:id>/",
    EventDetailTestView.as_view(),
    name="event_details_test",
  ),
  path("events/type/<str:slug>/", EventTypeView.as_view(), name="events_by_type"),
  path("events/tags/<str:slug>/", EventTagView.as_view(), name="events_by_tag"),
  path("events/tags", EventTagView.as_view(), name="events_tag"),
  path("events/type", EventTypeView.as_view(), name="events_type"),
  re_path("^songs/?$", SongView.as_view(), name="songs"),
  path("songs/<uuid:id>", SongDetailView.as_view(), name="song_details"),
  path("songs/<str:slug>", SongDetailView.as_view(), name="song_details"),
  re_path("^lyrics/?$", LyricsView.as_view(), name="song_lyrics"),
  path(
    "lyrics/<uuid:id>",
    LyricDetailView.as_view(),
    name="lyric_detail",
  ),
  re_path("^venues/?$", VenueView.as_view(), name="venues"),
  path("venues/<uuid:id>", VenueDetailView.as_view(), name="venue_details"),
  re_path("^tours/?$", TourView.as_view(), name="tours"),
  path("tours/<uuid:id>", TourDetailView.as_view(), name="tour_details"),
  path("search/results", EventSearchView.as_view(), name="search"),
  path(
    "search/advanced/",
    AdvancedSearchView.as_view(),
    name="adv_search",
  ),
  path(
    "test/search/",
    AdvSearchView.as_view(),
    name="adv_search_test",
  ),
  path(
    "test_table/",
    TestTableView.as_view(),
    name="test_table",
  ),
  path(
    "test_event/",
    TestEventView.as_view(),
    name="test_table",
  ),
  path(
    "search/advanced/results",
    AdvSearchView.as_view(),
    name="adv_search_results",
  ),
  path(
    "short_url/",
    ShortenURLView.as_view(),
    name="short_url",
  ),
  path(
    "search/notes/",
    SetlistNotesSearchView.as_view(),
    name="note_search",
  ),
  re_path("^relations/?$", RelationView.as_view(), name="relations"),
  path(
    "relations/<uuid:id>",
    RelationDetailView.as_view(),
    name="relation_details",
  ),
  re_path("^bands/?$", BandView.as_view(), name="bands"),
  path("bands/<uuid:id>", BandDetailView.as_view(), name="band_details"),
  path("releases/", ReleaseView.as_view(), name="releases"),
  path("releases/<uuid:id>", ReleaseDetailView.as_view(), name="release_details"),
  path("cities/", CityView.as_view(), name="cities"),
  path("cities/<uuid:id>", CityDetailView.as_view(), name="city_details"),
  path("states/", StateView.as_view(), name="states"),
  path("states/<uuid:id>", StateDetailView.as_view(), name="state_details"),
  path("countries/", CountryView.as_view(), name="countries"),
  path(
    "countries/<uuid:id>",
    CountryDetailView.as_view(),
    name="country_details",
  ),
  path("events/runs", EventRunView.as_view(), name="runs"),
  path("events/runs/<uuid:id>", RunDetailView.as_view(), name="run_details"),
  path("tours/legs", TourLegView.as_view(), name="tour_legs"),
  path("tours/legs/<uuid:id>", TourLegDetailView.as_view(), name="leg_details"),
  path("releases/nugs", NugsReleaseView.as_view(), name="nugs"),
  path("releases/bootlegs", BootlegView.as_view(), name="bootlegs"),
  path(
    "profile/add-show/",
    UserAddRemoveShowView.as_view(),
    name="add_show",
  ),
  path(
    "profile/remove-show/",
    UserRemoveShowView.as_view(),
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
  re_path("^updates/?$", UpdateView.as_view(), name="updates"),
]


if not settings.TESTING:
  urlpatterns = [*urlpatterns, *debug_toolbar_urls()]

if settings.DEBUG:
  urlpatterns += [
    # Downloads the raw schema file (YAML/JSON)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Optional UI interactive interfaces
    path(
      "api/schema/swagger-ui/",
      SpectacularSwaggerView.as_view(url_name="schema"),
      name="swagger-ui",
    ),
    path(
      "api/schema/redoc/",
      SpectacularRedocView.as_view(url_name="schema"),
      name="redoc",
    ),
  ]
