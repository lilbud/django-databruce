# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Runs(models.Model):
    band = models.ForeignKey('Bands', models.DO_NOTHING, db_column='band', blank=True, null=True)
    name = models.TextField()
    num_shows = models.IntegerField(blank=True, null=True)
    num_songs = models.IntegerField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField()
    first_event = models.ForeignKey('Events', models.DO_NOTHING, db_column='first_event', blank=True, null=True)
    last_event = models.ForeignKey('Events', models.DO_NOTHING, db_column='last_event', related_name='runs_last_event_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'runs'
