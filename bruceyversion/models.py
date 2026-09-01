from uuid import uuid4

from django.db import models as dj_models

from databruce.models import BaseModel, CustomUser, Events, Songs


class Entries(BaseModel):
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
    Songs,
    on_delete=dj_models.DO_NOTHING,
    related_name="entry_song",
  )
  event = dj_models.ForeignKey(
    Events,
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
    unique_together = (("song", "event"),)

  def __str__(self) -> str:
    return self.comment


class EntryComments(BaseModel):
  id = dj_models.AutoField(primary_key=True)
  entry = dj_models.ForeignKey(Entries, on_delete=dj_models.DO_NOTHING)
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
    db_table = "bv_entry_comments"

  def __str__(self):
    return self.comment


class EntryVotes(BaseModel):
  id = dj_models.AutoField(primary_key=True)
  entry = dj_models.ForeignKey(
    Entries,
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
    db_table = "bv_entry_votes"

  def __str__(self):
    return self.entry.comment
