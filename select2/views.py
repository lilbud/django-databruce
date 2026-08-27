from django.contrib.auth import get_user_model
from django_filters import rest_framework as rest_filters
from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from databruce import models

from . import filters, serializers

UserModel = get_user_model()


class Select2Pagination(LimitOffsetPagination):
  default_limit = 20
  max_limit = 50


class BaseSelect2View(viewsets.ReadOnlyModelViewSet):
  pagination_class = Select2Pagination
  filter_backends = [rest_filters.DjangoFilterBackend]


class Select2CityViewset(BaseSelect2View):
  queryset = (
    models.Cities.objects.all()
    .select_related("country")
    .prefetch_related("state")
    .only("id", "name", "state", "country")
  )
  serializer_class = serializers.CitySelect2Serializer
  filterset_class = filters.CitySelect2Filter


class Select2StateViewset(BaseSelect2View):
  queryset = (
    models.States.objects.all().select_related("country").only("id", "name", "country")
  )
  serializer_class = serializers.StateSelect2Serializer
  filterset_class = filters.StateSelect2Filter


class Select2CountryViewset(BaseSelect2View):
  queryset = models.Countries.objects.all().only("id", "name")
  serializer_class = serializers.CountrySelect2Serializer
  filterset_class = filters.CountrySelect2Filter


class Select2ContinentViewset(BaseSelect2View):
  queryset = models.Continents.objects.all().only("id", "name")
  serializer_class = serializers.ContinentSelect2Serializer
  filterset_class = filters.ContinentSelect2Filter


class Select2VenueViewset(BaseSelect2View):
  queryset = models.Venues.objects.all().only("id", "name")
  serializer_class = serializers.VenueSelect2Serializer
  filterset_class = filters.VenueSelect2Filter


class Select2TourViewset(BaseSelect2View):
  queryset = models.Tours.objects.all().only("id", "name")
  serializer_class = serializers.TourSelect2Serializer
  filterset_class = filters.TourSelect2Filter


class Select2RelationViewset(BaseSelect2View):
  queryset = models.Relations.objects.all().only("id", "name")
  serializer_class = serializers.RelationSelect2Serializer
  filterset_class = filters.RelationSelect2Filter


class Select2BandViewset(BaseSelect2View):
  queryset = models.Bands.objects.all().only("id", "name")
  serializer_class = serializers.BandSelect2Serializer
  filterset_class = filters.BandSelect2Filter


class Select2SongViewset(BaseSelect2View):
  queryset = models.Songs.objects.all().only("id", "name")
  serializer_class = serializers.SongSelect2Serializer
  filterset_class = filters.SongSelect2Filter


class Select2TagsViewset(BaseSelect2View):
  queryset = models.Tags.objects.all().only("id", "name")
  serializer_class = serializers.TagSelect2Serializer
  filterset_class = filters.TagSelect2Filter


class Select2TypesViewset(BaseSelect2View):
  queryset = models.Types.objects.all().only("id", "name")
  serializer_class = serializers.TypeSelect2Serializer
  filterset_class = filters.TypeSelect2Filter
