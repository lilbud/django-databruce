from uuid import uuid4

from django.db import models as dj_models

from databruce.models import BaseModel, CustomUser, Event, Song


class Entry(BaseModel):
  class ModerationStatus(dj_models.TextChoices):
    PENDING = "PENDING", "Pending Review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"

  id = dj_models.AutoField(primary_key=True)
  user = dj_models.ForeignKey(
    CustomUser,
    on_delete=dj_models.DO_NOTHING,
    related_name="user_entry",
  )
  song = dj_models.ForeignKey(
    Song,
    on_delete=dj_models.DO_NOTHING,
    related_name="entry_song",
  )
  event = dj_models.ForeignKey(
    Event,
    on_delete=dj_models.DO_NOTHING,
    related_name="entry_event",
  )
  votes = dj_models.IntegerField(default=0)
  comment = dj_models.TextField(default="", blank=False)
  uuid = dj_models.UUIDField(editable=False, default=uuid4)
  hidden = dj_models.BooleanField(default=False)
  status = dj_models.CharField(
    max_length=10,
    choices=ModerationStatus.choices,
    default=ModerationStatus.PENDING,
    db_index=True,
  )

  class Meta:
    managed = True
    db_table = "bv_entries"
    verbose_name_plural = "Entries"
    unique_together = (("song", "event"),)

  def __str__(self) -> str:
    return self.comment


class EntryComment(BaseModel):
  id = dj_models.AutoField(primary_key=True)
  entry = dj_models.ForeignKey(
    Entry,
    on_delete=dj_models.DO_NOTHING,
    related_name="entry_comment",
  )
  user = dj_models.ForeignKey(
    CustomUser,
    on_delete=dj_models.DO_NOTHING,
    related_name="user_entry_comments",
  )
  comment = dj_models.CharField(default="", blank=False, max_length=255)
  uuid = dj_models.UUIDField(editable=False, default=uuid4)
  hidden = dj_models.BooleanField(default=False)

  class Meta:
    managed = True
    verbose_name_plural = "Entry Comments"
    db_table = "bv_entry_comments"

  def __str__(self):
    return self.comment


class EntryVote(BaseModel):
  id = dj_models.AutoField(primary_key=True)
  entry = dj_models.ForeignKey(
    Entry,
    on_delete=dj_models.DO_NOTHING,
    related_name="entry_votes",
  )
  user = dj_models.ForeignKey(
    CustomUser,
    on_delete=dj_models.DO_NOTHING,
    related_name="user_entry_votes",
  )
  uuid = dj_models.UUIDField(editable=False, default=uuid4)
  hidden = dj_models.BooleanField(default=False)

  class Meta:
    managed = True
    verbose_name_plural = "Entry Votes"
    db_table = "bv_entry_votes"

  def __str__(self):
    return self.entry.comment
