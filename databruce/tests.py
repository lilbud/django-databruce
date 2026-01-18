# Create your tests here.
from datetime import datetime

from django.test import TestCase

from databruce.models import Events, Songs


class EventsTestCase(TestCase):
    def setUp(self):
        Events.objects.create(
            id="19780919-01",
            date=datetime.strptime("1978-09-19", "%Y-%m-%d"),
        )

    def test_event_get_date(self):
        """Check create event and date."""
        event = Events.objects.get(id="19780919-01")
        self.assertEqual(event.get_date(), "1978-09-19 [Tue]")
