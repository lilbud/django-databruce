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
router.register(r"venues", views.VenuesViewSet, basename="venue")
router.register(r"events", views.EventViewSet, basename="event")
router.register(r"nugs_releases", views.NugsViewSet, basename="nugs_release")
router.register(r"relations", views.RelationsViewSet, basename="relation")
router.register(r"onstage", views.OnstageViewSet, basename="onstage")
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
router.register(r"tours", views.ToursViewSet, basename="tour")
router.register(r"tour_legs", views.TourLegsViewSet, basename="tour_leg")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("api/", include(router.urls)),
    path("event_autocomplete", views.event_search, name="events_auto"),
]
