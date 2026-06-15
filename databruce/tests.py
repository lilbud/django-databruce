import datetime
import os
import re

from django.contrib.auth.models import Group
from django.core import mail
from django.db import transaction
from django.test import TransactionTestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from databruce.models import (
    Bands,
    Cities,
    Countries,
    CustomUser,
    Events,
    Setlists,
    Songs,
    States,
    Tours,
    UserAttendedShows,
    Venues,
)


class BaseDataTest(TransactionTestCase):
    """Centralized testing suite configuration.

    Inheriting from this automatically seeds your database records per class block.
    """

    def setUp(self):
        # 1. Core Global Records Seeding
        self.country = Countries.objects.create(name="United States", alpha_2="US")
        self.state = States.objects.create(
            name="New York",
            abbrev="NY",
            country=self.country,
        )
        self.city = Cities.objects.create(name="New York City", state=self.state)

        # 2. Build your core models, linking the venue to your new city path
        self.artist = Bands.objects.create(name="The E Street Band")

        self.venue = Venues.objects.create(
            name="Bottom Line",
            detail="",
            city=self.city,
        )

        self.tour = Tours.objects.create(name="Born In The U.S.A.")

        self.event = Events.objects.create(
            event_id="19750815-01",
            date=datetime.datetime(
                year=1975,
                month=8,
                day=15,
                tzinfo=datetime.UTC,
            ).date(),
            venue=self.venue,
            note="Test Note",
            artist=self.artist,
            tour=self.tour,
            public=True,
        )

        self.user_active = CustomUser.objects.create(
            username="testuser",
            email="testuser@example.com",
            password="faiasd87gf9s",  # noqa: S106
            is_active=True,
        )

        self.user_inactive = CustomUser.objects.create(
            username="testuser1",
            email="testuser1@example.com",
            password="faiasd87gf9s",  # noqa: S106
            is_active=False,
        )

        self.user_event = UserAttendedShows.objects.create(
            user=self.user_active,
            event=self.event,
        )

        self.song_a = Songs.objects.create(
            name="Song A",
            original_artist="Bruce Springsteen",
        )

        self.song_b = Songs.objects.create(
            name="Song B",
            original_artist="Goose",
        )

        self.song_c = Songs.objects.create(
            name="Song C",
            original_artist="The Grateful Dead",
        )

        self.event1 = Events.objects.create(
            event_id="19780919-01",
            date=datetime.datetime(
                year=1978,
                month=9,
                day=19,
                tzinfo=datetime.UTC,
            ).date(),
            venue=self.venue,
            artist=self.artist,
            tour=self.tour,
            public=True,
        )

        self.event2 = Events.objects.create(
            event_id="19780919-02",
            date=datetime.datetime(
                year=1978,
                month=9,
                day=19,
                tzinfo=datetime.UTC,
            ).date(),
            venue=self.venue,
            artist=self.artist,
            tour=self.tour,
            public=True,
        )

        # 2. Setup Event 1: A is followed by C (Matches "A NOT followed by B")
        self.setlist1 = Setlists.objects.create(
            event=self.event1,
            song=self.song_a,
            song_num=1,
            set_name="Set 1",
            is_opener=True,
        )

        self.setlist2 = Setlists.objects.create(
            event=self.event1,
            song=self.song_c,
            song_num=2,
            set_name="Set 1",
        )

        # 3. Setup Event 2: A is followed by B (Fails "A NOT followed by B")
        self.setlist3 = Setlists.objects.create(
            event=self.event2,
            song=self.song_a,
            song_num=1,
            set_name="Set 1",
        )

        self.setlist4 = Setlists.objects.create(
            event=self.event2,
            song=self.song_b,
            song_num=2,
            set_name="Set 1",
        )

        # Flush base tables to disk
        transaction.commit()


class ContactTests(BaseDataTest):
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_contact(self):
        contact_url = reverse("contact")
        data = {
            "email": "test@example.com",
            "message": "Test Message",
            "protocol": "http",
            "subject": "problem",
            "verification": os.getenv("VERIFICATION_ANSWER"),
        }

        response = self.client.post(path=contact_url, data=data)

        assert response.status_code == 302  # noqa: PLR2004
        assert len(mail.outbox) == 1


class UserTests(BaseDataTest):
    def test_user_login(self):
        # The login method requires credentials
        self.client.login(username="testuser", password="faiasd87gf9s")  # noqa: S106

    def test_user_add_show(self):
        UserAttendedShows.objects.create(user=self.user_active, event=self.event1)

    def test_user_remove_show(self):
        UserAttendedShows.objects.filter(
            user=self.user_active,
            event=self.event1,
        ).delete()

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_signup_and_email_confirmation_flow(self):
        # 1. Simulate Signup POST request
        signup_url = reverse("signup")  # Replace with your actual signup URL name

        user_data = {
            "username": "testuser2",
            "email": "test@example.com",
            "password1": "faiasd87gf9s",
            "password2": "faiasd87gf9s",
        }

        response = self.client.post(signup_url, user_data)
        Group.objects.create(name="Users")

        # Verify user was created but is inactive
        user = CustomUser.objects.get(email="test@example.com")
        assert not user.is_active

        # 2. Verify Email was sent to django.core.mail.outbox
        assert len(mail.outbox) == 1
        email_body = mail.outbox[0].body

        # 3. Extract the activation link from the email body
        link_match = re.search(r"https://example.com.*", email_body)
        assert link_match, "Activation link not found in email"
        activation_url = link_match.group(0)  # type: ignore

        # 4. Simulate clicking the link (GET request to the activation URL)
        response = self.client.get(activation_url, follow=True)

        # 5. Verify the user is now active
        user.refresh_from_db()
        assert user.is_active
        self.assertContains(response, "Login")


class AdvSearchTest(BaseDataTest):
    def get_search_results(
        self,
        client,
        song1_id,
        song2_id: int | None = None,
        position: str = "anywhere",
        choice: str = "True",
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
            choice="True",
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
            choice="True",
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
            choice="False",
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
            choice="False",
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
            choice="True",
        )

        events = response.context["events"]

        # Event 1 should be present because song A is present for event1
        assert self.event1 in events

        assert "Song A (is anywhere)" in response.context["search_summary"]


class EventSearch(BaseDataTest):
    def test_search(self):
        url = reverse("api:event_search-list")

        data = {
            "search": "bottom line 1975",
        }

        response = self.client.get(url, data)

        assert response.status_code == 200
        assert len(response.json()) == 3


class SitemapTestCase(BaseDataTest):
    def test_sitemap_loading(self):
        """Verify the sitemap URL loads successfully and contains XML data."""
        # Fetch the sitemap view
        response = self.client.get(reverse("django.contrib.sitemaps.views.sitemap"))

        # Assert the request was successful
        assert response.status_code == 200

        # Verify the custom content type header
        assert response["Content-Type"] == "application/xml"


class TestViews(BaseDataTest):
    def test_home(self):
        response = self.client.get(reverse("index"))
        assert response.status_code == 200

    def test_event(self):
        response = self.client.get(reverse("event_details", args=[self.event.event_id]))
        assert response.status_code == 200

    def test_event_mobile(self):
        response = self.client.get(
            reverse("event_details_mobile", args=[self.event.event_id])
        )
        assert response.status_code == 200

    def test_song(self):
        response = self.client.get(reverse("song_details", args=[self.song_a.uuid]))
        assert response.status_code == 200

    def test_venue(self):
        response = self.client.get(reverse("venue_details", args=[self.venue.uuid]))
        assert response.status_code == 200

    def test_artist(self):
        response = self.client.get(reverse("band_details", args=[self.artist.uuid]))
        assert response.status_code == 200

    def test_tour(self):
        response = self.client.get(reverse("tour_details", args=[self.tour.uuid]))
        assert response.status_code == 200

    def test_city(self):
        response = self.client.get(reverse("city_details", args=[self.city.uuid]))
        assert response.status_code == 200

    def test_state(self):
        response = self.client.get(reverse("state_details", args=[self.state.uuid]))
        assert response.status_code == 200

    def test_country(self):
        response = self.client.get(reverse("country_details", args=[self.country.uuid]))
        assert response.status_code == 200

    def test_user(self):
        response = self.client.get(reverse("profile", args=[self.user_active.uuid]))
        assert response.status_code == 200

    def test_calendar(self):
        response = self.client.get(reverse("calendar"))
        assert response.status_code == 200


class ModelStringTests(BaseDataTest):
    def test_model_string_representations(self):
        assert str(self.artist) == "The E Street Band"
        assert str(self.venue) == "Bottom Line (New York City)"
        assert str(self.tour) == "Born In The U.S.A."
        assert str(self.event) == "1975-08-15 [Fri]"
        assert str(self.song_a) == "Song A (Bruce Springsteen)"
        assert str(self.setlist1) == "19780919-01 - Set 1 - Song A (Bruce Springsteen)"
        assert str(self.user_active) == "testuser"


class DataTablesTest(BaseDataTest):
    def test_datatable_search_response(self):
        """Your actual test wrapper execution logic calling get_search_results."""
        response = self.get_search_results(self.client)
        self.assertEqual(response.status_code, 200)

    def get_search_results(
        self,
        client,
    ):
        """Simulate the Advanced Search GET request and return the dict object."""
        url = reverse("api:event-list")

        data = {
            "year": "1985",
            "draw": "2",
            "columns[0][data]": "date",
            "columns[0][name]": "event_id",
            "columns[0][searchable]": "true",
            "columns[0][orderable]": "true",
            "columns[0][search][value]": "",
            "columns[0][search][regex]": "false",
            "columns[1][data]": "has_setlist",
            "columns[1][name]": "has_setlist",
            "columns[1][searchable]": "false",
            "columns[1][orderable]": "false",
            "columns[1][search][value]": "",
            "columns[1][search][regex]": "false",
            "columns[2][data]": "artist",
            "columns[2][name]": "artist__name",
            "columns[2][searchable]": "true",
            "columns[2][orderable]": "true",
            "columns[2][search][value]": "",
            "columns[2][search][regex]": "false",
            "columns[3][data]": "venue",
            "columns[3][name]": "venue__name, venue__detail",
            "columns[3][searchable]": "true",
            "columns[3][orderable]": "true",
            "columns[3][search][value]": "",
            "columns[3][search][regex]": "false",
            "columns[4][data]": "venue.city",
            "columns[4][name]": "venue__city__name, venue__city__state__abbrev, venue__city__state__name, venue__city__country__name",
            "columns[4][searchable]": "true",
            "columns[4][orderable]": "true",
            "columns[4][search][value]": "",
            "columns[4][search][regex]": "false",
            "columns[5][data]": "tour",
            "columns[5][name]": "tour__name",
            "columns[5][searchable]": "true",
            "columns[5][orderable]": "true",
            "columns[5][search][value]": "",
            "columns[5][search][regex]": "false",
            "columns[6][data]": "title",
            "columns[6][name]": "title",
            "columns[6][searchable]": "true",
            "columns[6][orderable]": "true",
            "columns[6][search][value]": "",
            "columns[6][search][regex]": "false",
            "columns[7][data]": "public",
            "columns[7][name]": "public",
            "columns[7][searchable]": "true",
            "columns[7][orderable]": "false",
            "columns[7][search][value]": "",
            "columns[7][search][regex]": "false",
            "start": "0",
            "length": "100",
            "search[value]": "",
            "search[regex]": "true",
            "searchBuilder[criteria][0][condition]": "=",
            "searchBuilder[criteria][0][data]": "Band",
            "searchBuilder[criteria][0][origData]": "artist",
            "searchBuilder[criteria][0][type]": "string",
            "searchBuilder[criteria][0][value][]": "The E Street Band",
            "searchBuilder[criteria][0][value1]": "The E Street Band",
            "searchBuilder[criteria][1][condition]": "=",
            "searchBuilder[criteria][1][data]": "Tour",
            "searchBuilder[criteria][1][origData]": "tour",
            "searchBuilder[criteria][1][type]": "string",
            "searchBuilder[criteria][1][value][]": "Born In The U.S.A.",
            "searchBuilder[criteria][1][value1]": "Born In The U.S.A.",
            "searchBuilder[logic]": "AND",
            "_": "1781541333954",
        }

        api_client = APIClient()

        return api_client.get(url, data, format="custom")
