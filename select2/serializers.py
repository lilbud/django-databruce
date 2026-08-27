from rest_framework import serializers

from databruce import models


class CitySelect2Serializer(serializers.ModelSerializer):
  text = serializers.SerializerMethodField()

  def get_text(self, obj):
    try:
      if obj.state:
        if getattr(obj.country, "alpha_2", "").upper() == "US":
          return f"{obj.name}, {obj.state.abbrev}"

        return f"{obj.name}, {obj.country.name}"

    except AttributeError:
      return None
    else:
      return f"{obj.name}, {obj.country.name}"

  class Meta:
    model = models.Cities
    fields = ["id", "text"]


class StateSelect2Serializer(serializers.ModelSerializer):
  text = serializers.SerializerMethodField()

  def get_text(self, obj):
    return obj.name

  class Meta:
    model = models.States
    fields = ["id", "text"]


class CountrySelect2Serializer(serializers.ModelSerializer):
  text = serializers.SerializerMethodField()

  def get_text(self, obj):
    return obj.name

  class Meta:
    model = models.Countries
    fields = ["id", "text"]


class ContinentSelect2Serializer(serializers.ModelSerializer):
  text = serializers.SerializerMethodField()

  def get_text(self, obj):
    return obj.name

  class Meta:
    model = models.Continents
    fields = ["id", "text"]


class VenueSelect2Serializer(serializers.ModelSerializer):
  text = serializers.SerializerMethodField()

  def get_text(self, obj):
    try:
      if obj.detail:
        return f"{obj.name}, {obj.detail}"

      return obj.name
    except AttributeError:
      return None

  class Meta:
    model = models.Venues
    fields = ["id", "text"]


class TourSelect2Serializer(serializers.ModelSerializer):
  text = serializers.SerializerMethodField()

  def get_text(self, obj):
    return obj.name

  class Meta:
    model = models.Tours
    fields = ["id", "text"]


class RelationSelect2Serializer(serializers.ModelSerializer):
  text = serializers.SerializerMethodField()

  def get_text(self, obj):
    return obj.name

  class Meta:
    model = models.Relations
    fields = ["id", "text"]


class BandSelect2Serializer(serializers.ModelSerializer):
  text = serializers.SerializerMethodField()

  def get_text(self, obj):
    return obj.name

  class Meta:
    model = models.Bands
    fields = ["id", "text"]


class SongSelect2Serializer(serializers.ModelSerializer):
  text = serializers.SerializerMethodField()

  def get_text(self, obj):
    if not obj.original:
      return f"{obj.name} ({obj.original_artist})"

    return obj.name

  class Meta:
    model = models.Songs
    fields = ["id", "text"]


class TagSelect2Serializer(serializers.ModelSerializer):
  text = serializers.SerializerMethodField()

  def get_text(self, obj):
    return obj.name

  class Meta:
    model = models.Tags
    fields = ["id", "text"]


class TypeSelect2Serializer(serializers.ModelSerializer):
  text = serializers.SerializerMethodField()

  def get_text(self, obj):
    return obj.name

  class Meta:
    model = models.Types
    fields = ["id", "text"]
