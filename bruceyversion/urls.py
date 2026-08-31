from django.urls import path

from . import views

app_name = "bruceyversion"
urlpatterns = [
  path("submit/", views.Submit.as_view(), name="submit"),
  path("", views.EntriesList.as_view(), name="entries"),
  path("entries/", views.EntriesList.as_view(), name="entries"),
  path("entries/<uuid:id>/", views.EntryDetail.as_view(), name="entry_details"),
  path("song/<uuid:id>/", views.EntriesBySong.as_view(), name="entry_by_song"),
  path(
    "event/<str:id>/",
    views.EntriesByEvent.as_view(),
    name="entry_by_event",
  ),
  path("entry/vote/", views.EntryVote.as_view(), name="entry_vote"),
  path(
    "entry/comment/submit", views.SubmitComment.as_view(), name="entry_comment_submit"
  ),
  path(
    "entry/comment/update", views.UpdateComment.as_view(), name="entry_comment_update"
  ),
  path("songs/", views.SongList.as_view(), name="songs_list"),
]
