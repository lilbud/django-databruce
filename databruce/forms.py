import calendar
import datetime

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Reset, Submit
from django import forms
from django.urls import reverse_lazy
from django.utils.dates import MONTHS

from . import models

DATE = datetime.datetime.today()


class AdvancedEventSearch(forms.Form):
    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003, D107
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "get"

        self.helper.add_input(Submit("submit", "Go", css_class="btn-primary"))
        self.helper.add_input(Reset("reset", "Clear", css_class="btn-secondary"))

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
    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003, D107
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "get"

        self.helper.add_input(Submit("submit", "Go", css_class="btn-primary"))
        self.helper.add_input(Reset("reset", "Clear", css_class="btn-secondary"))

    songs = [("", "")]

    songs.extend(
        models.Songs.objects.filter(num_plays_public__gte=1)
        .order_by("song_name")
        .values_list("id", "song_name"),
    )

    song = forms.ChoiceField(
        label="Song:",
        choices=songs,
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select", "id": "songSelect"},
        ),
    )

    choice = forms.ChoiceField(
        label=None,
        choices=[("is", "is"), ("not", "not")],
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select", "id": "isNotSelect"},
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
            ("followed_by", "Followed By"),
        ],
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select", "id": "positionSelect"},
        ),
    )

    song2 = forms.ChoiceField(
        label="",
        choices=songs,
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "song2Select",
            },
        ),
    )

    def clean_position(self):
        positions = {
            "anywhere": "Anywhere",
            "show_opener": "Show Opener",
            "set_one_closer": "Set 1 Closer",
            "set_two_opener": "Set 2 Opener",
            "main_set_closer": "Main Set Closer",
            "encore_opener": "Encore Opener",
            "show_closer": "Show Closer",
            "followed_by": "Followed By",
        }

        return positions.get(self.cleaned_data["position"])
