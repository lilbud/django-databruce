import json

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


from django.core.exceptions import FieldError
from django.db.models import Q
from rest_framework import filters as dj_filters
from rest_framework_datatables.django_filters.backends import DatatablesFilterBackend


class SongsPageViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    from querystring_parser import parser

    def create_filter(
        self,
        column: str,
        condition: str,
        value: str = "",
        value2: str = "",
    ):
        filter_types = {
            "=": Q(**{f"{column}__iexact": value}),
            "!=": ~Q(**{f"{column}__iexact": value}),
            "starts": Q(**{f"{column}__istartswith": value}),
            "!starts": ~Q(**{f"{column}__istartswith": value}),
            "contains": Q(**{f"{column}__icontains": value}),
            "!contains": ~Q(**{f"{column}__icontains": value}),
            "ends": Q(**{f"{column}__iendswith": value}),
            "!ends": ~Q(**{f"{column}__iendswith": value}),
            "null": Q(**{f"{column}__exact": ""}) | Q(**{f"{column}__isnull": True}),
            "!null": ~Q(**{f"{column}__exact": ""}) & Q(**{f"{column}__isnull": False}),
            "<": Q(**{f"{column}__lt": value}),
            "<=": Q(**{f"{column}__lte": value}),
            ">=": Q(**{f"{column}__gte": value}),
            ">": Q(**{f"{column}__gt": value}),
            "between": Q(**{f"{column}__gte": value}) & Q(**{f"{column}__lte": value2}),
            "!between": ~Q(
                Q(**{f"{column}__gte": value}) & Q(**{f"{column}__lte": value2}),
            ),
        }

        return filter_types.get(condition)

    def get_queryset(self):
        filter = Q()
        post_dict = self.parser.parse(self.request.GET.urlencode())

        song = post_dict.get("song")

        qs = models.Songspagenew.objects.select_related(
            "event",
        ).filter(song=song)

        try:
            search = post_dict["searchBuilder"]["criteria"]

            for item in search:
                param = search[item]

                print(param)

                data = next(
                    item["name"]
                    for item in dict(post_dict["columns"]).values()
                    if item["data"] == param["origData"]
                )

                try:
                    search_filter = self.create_filter(
                        column=data,
                        value=param["value1"],
                        value2=param["value2"],
                        condition=param["condition"],
                    )
                except KeyError:
                    search_filter = self.create_filter(
                        column=data,
                        condition=param["condition"],
                    )

                if post_dict["searchBuilder"]["logic"] == "AND":
                    filter.add(
                        search_filter,
                        Q.AND,
                    )
                else:
                    filter.add(
                        search_filter,
                        Q.OR,
                    )

            print(filter)

            return qs.filter(filter).order_by("event")
        except KeyError as e:
            print(e)
            return qs.order_by("event")

    serializer_class = serializers.SongsPageSerializer
    # permission_classes = permission_classes
    # filter_backends = (DatatablesFilterBackend,)
    # filterset_class = filters.SongsPageFilter


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


class VenuesTextViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.VenuesText.objects.all()
    serializer_class = serializers.VenuesTextSerializer
    permission_classes = permission_classes
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    # filterset_class = filters.VenuesTextFilter
    ordering = ["formatted_loc"]


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
    ordering_fields = ["id", "date"]
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
    # filterset_class = filters.SetlistFilter
    permission_classes = permission_classes
    filterset_fields = ["song", "event"]


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


class SongsViewSet(viewsets.ModelViewSet):
    """ViewSet automatically provides `list`, `create`, `retrieve`, `update`, and `destroy` actions."""

    queryset = models.Songs.objects.all()
    serializer_class = serializers.SongsSerializer
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
