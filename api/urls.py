from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api import views

app_name = "api"

router = DefaultRouter()
router.register(r"archives", views.ArchiveViewSet, basename="archive")
router.register(r"bands", views.BandViewSet, basename="band")
router.register(r"bootlegs", views.BootlegViewSet, basename="bootleg")
router.register(r"cities", views.CitiesViewSet, basename="city")
router.register(r"countries", views.CountriesViewSet, basename="country")
router.register(r"continents", views.ContinentsViewSet, basename="continent")
router.register(r"covers", views.CoversViewSet, basename="cover")
router.register(r"venuestext", views.VenuesTextViewSet, basename="venue_text")
router.register(r"venues", views.VenuesViewSet, basename="venue")
router.register(r"events", views.EventViewSet, basename="event")
router.register(r"runs", views.EventRunViewSet, basename="runs")
router.register(r"nugs_releases", views.NugsViewSet, basename="nugs_release")
router.register(r"relations", views.RelationsViewSet, basename="relation")
router.register(r"onstage", views.OnstageViewSet, basename="onstage")
router.register(
    r"onstage_events",
    views.OnstageEventsViewSet,
    basename="onstage_events",
)
router.register(r"onstageband", views.OnstageBandViewSet, basename="onstageband")
router.register(
    r"release_tracks",
    views.ReleaseTracksViewSet,
    basename="release_tracks",
)
router.register(r"releases", views.ReleasesViewSet, basename="release")
router.register(r"setlists", views.SetlistViewSet, basename="setlist")
router.register(r"snippets", views.SnippetViewSet, basename="snippet")
router.register(r"states", views.StatesViewSet, basename="state")
router.register(r"songs", views.SongsViewSet, basename="songs")
router.register(r"tours", views.ToursViewSet, basename="tour")
router.register(r"tour_legs", views.TourLegsViewSet, basename="tour_leg")
router.register(r"songspage", views.SongsPageViewSet, basename="songs_page")
router.register(r"lyrics", views.LyricsViewSet, basename="lyrics")
router.register(
    r"setlist_entries",
    views.SetlistEntriesViewSet,
    basename="setlist_entries",
)
router.register(
    r"advanced_search",
    views.AdvancedSearch,
    basename="advanced_search",
)
router.register(
    r"index",
    views.IndexViewSet,
    basename="index",
)
router.register(
    r"event_setlist",
    views.EventSetlist,
    basename="event_setlist",
)
router.register(
    r"setlist_notes",
    views.SetlistNotesViewSet,
    basename="setlist_notes",
)
router.register(
    r"updates",
    views.UpdatesViewSet,
    basename="updates",
)
router.register(
    r"calendar",
    views.EventCalendar,
    basename="calendar",
)


# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("api/v1/", include(router.urls)),
]
