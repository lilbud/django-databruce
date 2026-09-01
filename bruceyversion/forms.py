from typing import Any

from django import forms

from databruce import models


class SubmitForm(forms.Form):
  def __init__(self, *args: Any, **kwargs: Any) -> None:
    """Initialize form."""
    super().__init__(*args, **kwargs)

    # Check if form has POST data (args[0] is typically request.POST)
    if self.is_bound:
      # Extract the event ID submitted by the user
      song_id = self.data.get("song")
      if song_id:
        # Query the actual songs matching that event
        # Example assuming a Song model:
        songs = models.Songs.objects.filter(id=song_id)
        self.fields["song"].choices = [(s.id, str(s.name)) for s in songs]

    if self.is_bound:
      event_id = self.data.get("event")
    else:
      event_id = self.initial.get("event")

    # 2. If a value exists, inject it as a valid choice so validation passes
    if event_id:
      try:
        event_obj = models.Events.objects.get(pk=event_id)
        # CRITICAL FIX: Clear choices completely to prevent duplication
        self.fields["event"].choices = []

        # If you use a Select2 placeholder, prepend an empty choice:
        # self.fields["event"].choices = [("", "")]

        # Append the singular, valid choice item
        self.fields["event"].choices += [
          (event_obj.pk, f"{event_obj.date} - {event_obj.venue}"),
        ]

      except (models.Events.DoesNotExist, ValueError):
        self.fields["event"].choices = [(event_id, event_id)]

  event = forms.ChoiceField(
    label="Event",
    required=True,
    choices=[],
    widget=forms.Select(
      attrs={"class": "form-select form-select-sm event select2", "id": "event"},
    ),
  )

  song = forms.ChoiceField(
    label="Song",
    required=True,
    choices=[],
    widget=forms.Select(
      attrs={
        "class": "form-select form-select-sm",
        "id": "song",
        "placeholder": "Select an event first",
      },
    ),
  )

  comment = forms.CharField(
    label="Comment",
    required=True,
    max_length=5000,
    help_text="5000 character limit",
    widget=forms.Textarea(
      attrs={
        "class": "form-control form-control-sm",
        "id": "comment",
        "name": "text",
      },
    ),
  )

  def clean_event(self):
    data = self.cleaned_data.get("event")
    if data:
      try:
        return models.Events.objects.get(id=data)
      except models.Events.DoesNotExist:
        raise forms.ValidationError("Select a valid event.")
    return None

  def clean_song(self):
    data = self.cleaned_data.get("song")
    if data:
      try:
        return models.Songs.objects.get(id=data)
      except models.Songs.DoesNotExist:
        raise forms.ValidationError("Select a valid song.")
    return None

  def clean_comment(self):
    # .get() prevents KeyError if data is completely missing
    return self.cleaned_data.get("comment")


class CommentForm(forms.Form):
  def __init__(self, *args: Any, **kwargs: Any) -> None:
    """Initialize form."""
    super().__init__(*args, **kwargs)

  comment = forms.CharField(
    label="Comment",
    required=True,
    max_length=255,
    help_text="255 character limit",
    widget=forms.Textarea(
      attrs={
        "class": "form-control form-control-sm",
        "id": "text",
        "name": "text",
      },
    ),
  )

  def clean_comment(self):
    # .get() prevents KeyError if data is completely missing
    return self.cleaned_data.get("comment")
