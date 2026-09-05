from django.urls import path

from .views import (
  EntryDetailView,
  EntryListView,
  EntrySubmit,
  EntryVote,
  EventEntryListView,
  SongEntryListView,
  SongListView,
  SubmitEntryComment,
  UpdateEntryComment,
)

app_name = "bruceyversion"
urlpatterns = [
  path("submit/", EntrySubmit.as_view(), name="submit"),
  path("", EntryListView.as_view(), name="entries"),
  path("entries/", EntryListView.as_view(), name="entries"),
  path("entries/<uuid:id>/", EntryDetailView.as_view(), name="entry_detail"),
  path("song/<uuid:id>/", SongEntryListView.as_view(), name="entry_by_song"),
  path(
    "event/<str:id>/",
    EventEntryListView.as_view(),
    name="entry_by_event",
  ),
  path("entry/vote/", EntryVote.as_view(), name="entry_vote"),
  path(
    "entry/comment/submit",
    SubmitEntryComment.as_view(),
    name="entry_comment_submit",
  ),
  path(
    "entry/comment/update",
    UpdateEntryComment.as_view(),
    name="entry_comment_update",
  ),
  path("songs/", SongListView.as_view(), name="songs_list"),
]
