from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "select2"
router = DefaultRouter()

router.register(
    r"cities",
    views.Select2CityViewset,
    basename="select2-city",
)
router.register(
    r"states",
    views.Select2StateViewset,
    basename="select2-state",
)
router.register(
    r"countries",
    views.Select2CountryViewset,
    basename="select2-country",
)
router.register(
    r"venues",
    views.Select2VenueViewset,
    basename="select2-venue",
)
router.register(
    r"tours",
    views.Select2TourViewset,
    basename="select2-tour",
)
router.register(
    r"relations",
    views.Select2RelationViewset,
    basename="select2-relation",
)
router.register(
    r"bands",
    views.Select2BandViewset,
    basename="select2-band",
)
router.register(
    r"songs",
    views.Select2SongViewset,
    basename="select2-song",
)
router.register(
    r"tags",
    views.Select2TagsViewset,
    basename="select2-tag",
)
router.register(
    r"types",
    views.Select2TypesViewset,
    basename="select2-type",
)


urlpatterns = [
    path("api/select2/", include(router.urls)),
]
