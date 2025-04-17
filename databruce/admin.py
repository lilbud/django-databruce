from datetime import datetime

from django import forms
from django.contrib import admin
from nonrelated_inlines.admin import NonrelatedTabularInline

from . import models


@admin.register(models.ArchiveLinks)
class ArchiveLinksAdmin(admin.ModelAdmin):
    list_display = ["event_id", "event_date_view", "archive_url"]

    @admin.display(empty_value="unknown")
    def event_date_view(self, obj):
        return datetime.strftime(obj.event_id.event_date, "%Y-%m-%d")


admin.site.register(models.Bands)
admin.site.register(models.Bootlegs)
admin.site.register(models.Cities)
admin.site.register(models.Continents)
admin.site.register(models.Countries)
admin.site.register(models.Covers)
admin.site.register(models.Events)
admin.site.register(models.NugsReleases)
admin.site.register(models.Onstage)
admin.site.register(models.Relations)
admin.site.register(models.ReleaseTracks)
admin.site.register(models.Releases)
admin.site.register(models.Setlists)
admin.site.register(models.Snippets)
admin.site.register(models.Songs)
admin.site.register(models.States)
admin.site.register(models.Tags)
admin.site.register(models.Tours)
admin.site.register(models.Venues)
