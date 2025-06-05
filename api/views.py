import json

from django.http import HttpRequest, HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from api import filters, serializers
from databruce import models

permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ArchiveViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.ArchiveLinks.objects.all()
    serializer_class = serializers.ArchiveLinksSerializer
    permission_classes = permission_classes
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.ArchiveFilter
    ordering = ["created_at", "event"]


class BandViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Bands.objects.all().order_by("name")
    serializer_class = serializers.BandsSerializer
    permission_classes = permission_classes
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["name"]
    ordering = ["name"]


class BootlegViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Bootlegs.objects.all()
    serializer_class = serializers.BootlegsSerializer
    permission_classes = permission_classes
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = filters.BootlegFilter
    ordering = ["event", "title"]


class CitiesViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Cities.objects.all().order_by("name")
    serializer_class = serializers.CitiesSerializer
    permission_classes = permission_classes
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.CitiesFilter
    ordering = ["name", "first", "last"]


class ContinentsViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Continents.objects.all()
    serializer_class = serializers.ContinentsSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    permission_classes = permission_classes
    filterset_fields = ["name"]
    ordering = ["name", "num_events"]


class CountriesViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Countries.objects.all().order_by("name")
    serializer_class = serializers.CountriesSerializer
    permission_classes = permission_classes
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["name"]
    ordering = ["name", "num_events"]


class CoversViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Covers.objects.all()
    serializer_class = serializers.CoversSerializer
    permission_classes = permission_classes
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.CoversFilter
    ordering = ["event"]


class VenuesViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Venues.objects.all()
    serializer_class = serializers.VenuesSerializer
    permission_classes = permission_classes
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.VenuesFilter
    ordering = ["name", "first", "last"]


class EventViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Events.objects.all()
    serializer_class = serializers.EventsSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.EventsFilter
    ordering_fields = ["id", "event_date"]
    permission_classes = permission_classes


class NugsViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.NugsReleases.objects.all()
    serializer_class = serializers.NugsSerializer
    permission_classes = permission_classes


class RelationsViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Relations.objects.all()
    serializer_class = serializers.RelationsSerializer
    permission_classes = permission_classes
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    search_fields = ["name", "aliases"]
    ordering_fields = ["name"]


class OnstageBandViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Onstage.objects.distinct("event").order_by("event")

    serializer_class = serializers.OnstageSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["event", "relation", "band"]
    search_fields = ["event", "relation", "band"]
    ordering_fields = ["id"]
    permission_classes = permission_classes


class OnstageViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Onstage.objects.all()
    serializer_class = serializers.OnstageSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.OnstageFilter
    ordering_fields = ["id", "event"]
    permission_classes = permission_classes


class ReleaseTracksViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.ReleaseTracks.objects.all().order_by("track")
    serializer_class = serializers.ReleaseTracksSerializer
    permission_classes = permission_classes
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.ReleaseTracksFilter
    ordering_fields = ["id", "event"]


class ReleasesViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Releases.objects.all()
    serializer_class = serializers.ReleasesSerializer
    permission_classes = permission_classes
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.ReleaseFilter


class SetlistViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Setlists.objects.all()
    serializer_class = serializers.SetlistSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.SetlistFilter
    permission_classes = permission_classes


class SnippetViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Snippets.objects.all()
    serializer_class = serializers.SnippetSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.SnippetFilter
    permission_classes = permission_classes


class StatesViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.States.objects.all()
    serializer_class = serializers.StatesSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.StateFilter
    permission_classes = permission_classes


class ToursViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Tours.objects.all()
    serializer_class = serializers.ToursSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.TourFilter
    permission_classes = permission_classes


class TourLegsViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.TourLegs.objects.all()
    serializer_class = serializers.TourLegsSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = filters.TourLegFilter
    permission_classes = permission_classes


def event_search(request: HttpRequest):
    data = None

    if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
        q = request.GET.get("term", "")
        results = []

        search_qs = models.Events.objects.filter(date__startswith=q).order_by("date")

        for r in search_qs:
            result = {
                "id": r.id,
                "value": f"{r.date.strftime('%Y-%m-%d [%a]')} - {r.venue.city}",
                "date": r.date.strftime("%Y-%m-%d"),
            }

            if r.early_late:
                result["value"] = (
                    f"{r.date.strftime('%Y-%m-%d [%a]')} {r.early_late} - {r.venue.city}"
                )

            results.append(result)

        data = json.dumps(results)
        print(data)

    mimetype = "application/json"
    return HttpResponse(data, mimetype)
