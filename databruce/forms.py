import calendar
import datetime
import re

from django import forms
from django.forms import ModelChoiceField
from django.utils.dates import MONTHS

from . import models

DATE = datetime.datetime.today()


class VenueModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.formatted_loc


class MyModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


def get_bands():
    return models.Bands.objects.filter(springsteen_band=True).order_by("name")


class yearDropdown(forms.Form):
    year = forms.ChoiceField(
        choices=[(i, i) for i in range(1965, DATE.year + 1)],
        widget=forms.Select(
            attrs={
                "onchange": "form.submit();",
                "class": "form-control form-control-sm",
            },
        ),
        required=False,
        label="All Events from",
    )


class AdvancedEventSearch(forms.Form):
    def get_months():
        months = [("", "")]
        months.extend([(i, calendar.month_name[i]) for i in range(1, 13)])
        return months

    def get_days():
        days = [("", "")]
        days.extend([(i, i) for i in range(1, 32)])
        return days

    days_of_week = [
        ("", ""),
        ("1", "Sunday"),
        ("2", "Monday"),
        ("3", "Tuesday"),
        ("4", "Wednesday"),
        ("5", "Thursday"),
        ("6", "Friday"),
        ("7", "Saturday"),
    ]

    def get_states():
        states = [("", "")]

        states.extend(
            models.States.objects.all()
            .distinct("name")
            .order_by("name")
            .values_list("id", "name"),
        )

        return states

    def get_cities():
        cities = [("", "")]
        cities.extend(
            models.Cities.objects.all().order_by("name").values_list("id", "name"),
        )
        return cities

    def get_countries():
        countries = [("", "")]
        countries.extend(
            models.Countries.objects.all().order_by("name").values_list("id", "name"),
        )
        return countries

    def get_musicians():
        musicians = [("", "")]

        musicians.extend(
            models.Relations.objects.filter(appearances__gte=1)
            .distinct("name")
            .order_by("name")
            .values_list("id", "name"),
        )

        return musicians

    def get_bands():
        bands = [("", "")]

        bands.extend(
            models.Bands.objects.filter(appearances__gte=1)
            .distinct("name")
            .order_by("name")
            .values_list("id", "name"),
        )

        return bands

    first_date = forms.CharField(
        label="Start Date:",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "start_date",
                "type": "search",
                "name": "start_date",
                "placeholder": "YYYY-MM-DD",
                "maxlength": 10,
            },
        ),
    )

    last_date = forms.CharField(
        label="Last Date:",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "end_date",
                "type": "search",
                "name": "end_date",
                "placeholder": "YYYY-MM-DD",
                "maxlength": 10,
            },
        ),
    )

    month = forms.ChoiceField(
        label="Month:",
        choices=get_months(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    day = forms.ChoiceField(
        label="Day:",
        choices=get_days(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    day_of_week = forms.ChoiceField(
        label="Day of Week:",
        choices=days_of_week,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    city = forms.ChoiceField(
        label="City:",
        choices=get_cities(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "citySelect"}),
    )

    state = forms.ChoiceField(
        label="State:",
        choices=get_states(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "stateSelect"}),
    )

    country = forms.ChoiceField(
        label="Country:",
        choices=get_countries(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "countrySelect"}),
    )

    musician = forms.ChoiceField(
        label="Musician:",
        choices=get_musicians(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "musicianSelect"}),
    )

    band = forms.ChoiceField(
        label="Band:",
        choices=get_bands(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "bandSelect"}),
    )

    def form_display(self):
        form = {}

        form["start_date"] = {
            "label": "Start Date:",
            "data": self.cleaned_data["first_date"],
        }

        return form

    def clean_first_date(self):
        # found on stackoverflow, probably not the "best" way to do this
        try:
            for i in ("%Y-%m-%d", "%Y-%m"):
                try:
                    return datetime.datetime.strptime(
                        self.cleaned_data["first_date"],
                        i,
                    ).strftime("%Y-%m-%d")
                except ValueError:
                    pass
        except ValueError:
            pass

        return models.Events.objects.all().order_by("event_date").first().event_date

    def clean_last_date(self):
        # found on stackoverflow, probably not the "best" way to do this
        try:
            for i in ("%Y-%m-%d", "%Y-%m"):
                try:
                    return datetime.datetime.strptime(
                        self.cleaned_data["last_date"],
                        i,
                    ).strftime("%Y-%m-%d")
                except ValueError:
                    pass
        except ValueError:
            pass

        return (
            models.Events.objects.filter(event_date__isnull=False)
            .order_by("-event_date")
            .first()
            .event_date
        )

    def clean_month(self):
        month = self.cleaned_data["month"]

        if month:
            return [month]

        return list(range(1, 13))

    def clean_day(self):
        day = self.cleaned_data["day"]

        if day:
            return [day]

        return list(range(1, 32))

    def clean_band(self):
        band = self.cleaned_data["band"]

        if band:
            return [band]

        return models.Bands.objects.all().values_list("id")

    def clean_city(self):
        city = self.cleaned_data["city"]

        if city:
            return [city]

        return models.Cities.objects.all().values_list("id")

    def clean_country(self):
        country = self.cleaned_data["country"]

        if country:
            return [country]

        return models.Countries.objects.all().values_list("id")

    def clean_musician(self):
        musician = self.cleaned_data["musician"]

        if musician:
            return [musician]

        return models.Relations.objects.all().values_list("id")


class SetlistSearch(forms.Form):
    songs = [("", "")]

    for s in models.Songs.objects.filter(num_plays_public__gte=1).order_by("song_name"):
        songs.append((s.id, s.song_name))

    song = forms.ChoiceField(
        label="Song:",
        choices=songs,
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm", "id": "songSelect"},
        ),
    )

    choice = forms.ChoiceField(
        label=None,
        choices=[("is", "is"), ("not", "not")],
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm", "id": "isNotSelect"},
        ),
    )

    position = forms.ChoiceField(
        label=None,
        choices=[
            ("anywhere", "Anywhere"),
            ("show_opener", "Show Opener"),
            ("set_one_closer", "Set 1 Closer"),
            ("set_two_opener", "Set 2 Opener"),
            ("main_set_closer", "Main Set Closer"),
            ("encore_opener", "Encore Opener"),
            ("show_closer", "Show Closer"),
            # ("followed_by", "Followed By"),
        ],
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm", "id": "positionSelect"},
        ),
    )

    # song2 = forms.ChoiceField(
    #     label="",
    #     choices=songs,
    #     required=False,
    #     widget=forms.Select(
    #         attrs={
    #             "class": "form-select form-select-sm",
    #             "id": "song2Select",
    #             "style": "visibility: hidden;",
    #         },
    #     ),
    # )
