from typing import Any

from django import forms

from databruce import models


class SubmitForm(forms.Form):
  def __init__(self, *args: Any, **kwargs: Any) -> None:
    """Initialize form."""
    super().__init__(*args, **kwargs)

    # Check if form has POST data (args[0] is typically request.POST)
    if args and isinstance(args[0], dict):
      data = args[0]

      # If an event ID was submitted, dynamically validate it
      if data.get("event"):
        self.fields["event"].choices = [(data["event"], data["event"])]

      # If a song ID was submitted, dynamically validate it
      if data.get("song"):
        self.fields["song"].choices = [(data["song"], data["song"])]

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
        "disabled": "disabled",
      },
    ),
  )

  comment = forms.CharField(
    label="Comment",
    required=True,
    widget=forms.Textarea(
      attrs={
        "class": "form-control form-control-sm",
        "id": "text",
        "name": "text",
        "disabled": "disabled",
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
