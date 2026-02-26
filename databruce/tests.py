import datetime

from django.test import Client, TestCase
from django.urls import reverse

from databruce.models import Bands, Events, Setlists, Songs, Venues


class AdvSearchTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create common infrastructure once
        cls.song_a = Songs.objects.create(
            name="Song A",
        )

        cls.song_b = Songs.objects.create(
            name="Song B",
        )

        cls.song_c = Songs.objects.create(
            name="Song C",
        )

        cls.venue = Venues.objects.create(name="Venue A")
        cls.artist = Bands.objects.create(name="Band A")

        cls.event1 = Events.objects.create(
            event_id="19780919-01",
            date=datetime.datetime(1978, 9, 19).date(),
            venue=cls.venue,
            artist=cls.artist,
        )

        cls.event2 = Events.objects.create(
            event_id="19780919-02",
            date=datetime.datetime(1978, 9, 19).date(),
            venue=cls.venue,
            artist=cls.artist,
        )

        # 2. Setup Event 1: A is followed by C (Matches "A NOT followed by B")
        Setlists.objects.create(
            event=cls.event1,
            song=cls.song_a,
            song_num=1,
            set_name="Set 1",
            is_opener=True,
        )

        Setlists.objects.create(
            event=cls.event1,
            song=cls.song_c,
            song_num=2,
            set_name="Set 1",
        )

        # 3. Setup Event 2: A is followed by B (Fails "A NOT followed by B")
        Setlists.objects.create(
            event=cls.event2,
            song=cls.song_a,
            song_num=1,
            set_name="Set 1",
        )

        Setlists.objects.create(
            event=cls.event2,
            song=cls.song_b,
            song_num=2,
            set_name="Set 1",
        )

    def get_search_results(
        self,
        client,
        song1_id,
        song2_id=None,
        position="anywhere",
        choice="True",
    ):
        """Simulate the Advanced Search GET request and return the dict object."""
        url = reverse("adv_search_results")

        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-0-song1": song1_id,
            "form-0-position": position,
            "form-0-choice": choice,
            "conjunction": "and",
        }

        # Add song2 if it's a 'followed_by' query
        if song2_id:
            data["form-0-song2"] = song2_id

        return client.get(url, data)

    def test_show_opener_filter(self):
        response = self.get_search_results(
            client=self.client,
            song1_id=self.song_a.id,
            position="show_opener",
            choice=True,
        )

        events = response.context["events"]

        # Event 1 should be included because Song A IS show opener
        assert self.event1 in events

        # Verify the summary string reflects the result above
        assert "Song A (is Show Opener)" in response.context["search_summary"]

        # Should be only one event
        assert events.count() == 1

    def test_followed_by(self):
        response = self.get_search_results(
            client=self.client,
            song1_id=self.song_a.id,
            song2_id=self.song_b.id,
            position="followed_by",
            choice=True,
        )

        events = response.context["events"]

        # Event 2 should be included because Song A IS followed by Song B
        assert self.event2 in events

        # Verify the summary string reflects the result above
        assert "Song A (is followed by) Song B" in response.context["search_summary"]

        # Should be only one event
        assert events.count() == 1

    def test_not_followed_by(self):
        response = self.get_search_results(
            client=self.client,
            song1_id=self.song_a.id,
            song2_id=self.song_b.id,
            position="followed_by",
            choice=False,
        )

        events = response.context["events"]

        # Event 1 should be present because Song A is NOT followed by Song B
        assert self.event1 in events

        # Verify the summary string reflects the result above
        assert "Song A (not followed by) Song B" in response.context["search_summary"]

        assert events.count() == 1

    def test_not_anywhere(self):
        response = self.get_search_results(
            client=self.client,
            song1_id=self.song_b.id,
            position="anywhere",
            choice=False,
        )

        events = response.context["events"]

        # Event 1 should be present because song B is not present for event1
        assert self.event1 in events

        assert "Song B (not anywhere)" in response.context["search_summary"]

    def test_is_anywhere(self):
        response = self.get_search_results(
            client=self.client,
            song1_id=self.song_a.id,
            position="anywhere",
            choice=True,
        )

        events = response.context["events"]

        # Event 1 should be present because song A is present for event1
        assert self.event1 in events

        assert "Song A (is anywhere)" in response.context["search_summary"]
