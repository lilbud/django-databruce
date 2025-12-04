import calendar
import datetime
import re
from typing import Any

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import F

from . import models

DATE = datetime.datetime.today()


class AdvancedEventSearch(forms.Form):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    class FormChoiceSelect(forms.ChoiceField):
        def __init__(self, widget_id, *args: tuple, **kwargs: dict[str, Any]) -> None:
            kwargs["initial"] = "is"
            kwargs["label"] = ""
            kwargs["choices"] = [("is", "is"), ("not", "not")]
            kwargs["required"] = False
            kwargs["widget"] = forms.Select(
                attrs={
                    "class": "form-select form-select-sm col-3",
                    "id": widget_id,
                },
            )
            super().__init__(*args, **kwargs)

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
            .select_related("country")
            .order_by("name")
            .values_list("id", "name"),
        )

        return states

    def get_cities():
        cities = [("", "")]

        cities.extend(
            [
                (item.id, item)
                for item in models.Cities.objects.all()
                .prefetch_related("state", "state__country")
                .select_related("country")
                .order_by("name")
            ],
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

    def get_tours():
        tours = [("", "")]

        tours.extend(
            models.Tours.objects.all().order_by("name").values_list("id", "name"),
        )

        return tours

    first_date = forms.CharField(
        label="Start Date",
        required=False,
        widget=forms.TextInput(
            attrs={
                "id": "start_date",
                "type": "search",
                "name": "event_start_date",
                "placeholder": "YYYY-MM-DD",
                "maxlength": 10,
                "class": "form-control form-control-sm date-form col-6",
            },
        ),
    )

    last_date = forms.CharField(
        label="Last Date",
        required=False,
        widget=forms.TextInput(
            attrs={
                "id": "end_date",
                "type": "search",
                "name": "event_end_date",
                "placeholder": "YYYY-MM-DD",
                "maxlength": 10,
                "class": "form-control form-control-sm date-form col-6",
            },
        ),
    )

    month = forms.ChoiceField(
        label="Month",
        choices=get_months(),
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm",
                "id": "month",
                "name": "event_month",
            },
        ),
    )

    day = forms.ChoiceField(
        label="Day",
        choices=get_days(),
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm",
                "id": "day",
                "name": "event_day",
            },
        ),
    )

    day_of_week_choice = FormChoiceSelect(widget_id="dow_choice")

    day_of_week = forms.ChoiceField(
        label="Day of Week",
        choices=days_of_week,
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm",
                "id": "day_of_week",
                "name": "event_day_of_week",
            },
        ),
    )

    city_choice = FormChoiceSelect(widget_id="city_choice")

    # city = forms.ModelChoiceField(
    #     label="City",
    #     required=False,
    #     queryset=models.Cities.objects.all()
    #     .prefetch_related("state", "state__country")
    #     .select_related("country")
    #     .order_by("name"),
    #     widget=forms.Select(
    #         attrs={
    #             "class": "form-select form-select-sm select2",
    #             "id": "city",
    #             "name": "event_city",
    #         },
    #     ),
    # )
    #

    city = forms.CharField(
        label="City",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm select2",
                "id": "city",
                "name": "event_city",
            },
        ),
    )

    state_choice = FormChoiceSelect(widget_id="state_choice")

    state = forms.CharField(
        label="State",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm select2",
                "id": "state",
                "name": "event_state",
            },
        ),
    )

    country_choice = FormChoiceSelect(widget_id="country_choice")

    country = forms.CharField(
        label="Country",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm select2",
                "id": "country",
                "name": "event_country",
            },
        ),
    )

    tour_choice = FormChoiceSelect(widget_id="tour_choice")

    tour = forms.CharField(
        label="Tour",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm select2",
                "id": "tour",
                "name": "event_tour",
            },
        ),
    )

    musician_choice = FormChoiceSelect(widget_id="musician_choice")

    musician = forms.CharField(
        label="Musician",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm select2",
                "id": "musician",
                "name": "event_musician",
            },
        ),
    )

    band_choice = FormChoiceSelect(widget_id="band_choice")

    band = forms.CharField(
        label="Band",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm select2",
                "id": "band",
                "name": "event_band",
            },
        ),
    )

    conjunction = forms.ChoiceField(
        label="Conjunction",
        choices=[("and", "AND"), ("or", "OR")],
        initial="and",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm",
                "id": "conjunctionSelect",
                "name": "setlist_conjunction",
            },
        ),
    )

    def clean_first_date(self):
        # the first year tracked in the database is 1965, so that is the start date
        data = {
            "id": self.cleaned_data["first_date"],
            "value": datetime.date(1965, 1, 1),
        }

        if self.cleaned_data["first_date"]:
            # partial date, get first of month
            if re.search(r"^\d{4}-\d{2}$", self.cleaned_data["first_date"]):
                return (
                    datetime.datetime.strptime(
                        self.cleaned_data["first_date"],
                        "%Y-%m",
                    )
                    .replace(day=1)
                    .date()
                )

            # specific date
            if re.search(r"^\d{4}-\d{2}-\d{2}$", self.cleaned_data["first_date"]):
                return datetime.datetime.strptime(
                    self.cleaned_data["first_date"],
                    "%Y-%m-%d",
                ).date()

        return data

    def clean_last_date(self):
        # default end date is last day of current year
        data = {
            "id": self.cleaned_data["last_date"],
            "value": datetime.date(DATE.year, 12, 31),
        }

        if self.cleaned_data["last_date"]:
            # partial date
            if re.search(r"^\d{4}-\d{2}$", self.cleaned_data["last_date"]):
                dt = datetime.datetime.strptime(
                    self.cleaned_data["last_date"],
                    "%Y-%m",
                )

                last = calendar.monthrange(dt.year, dt.month)[1]

                data["value"] = dt.replace(day=last).date()

            # specific date
            if re.search(r"^\d{4}-\d{2}-\d{2}$", self.cleaned_data["last_date"]):
                data["value"] = datetime.datetime.strptime(
                    self.cleaned_data["last_date"],
                    "%Y-%m-%d",
                ).date()

        return data

    def clean_month(self):
        data = {
            "id": self.cleaned_data["month"],
            "value": self.cleaned_data["month"],
        }

        if self.cleaned_data["month"]:
            data["value"] = calendar.month_name[int(self.cleaned_data["month"])]

        return data

    def clean_city(self):
        data = {
            "id": self.cleaned_data["city"],
            "value": self.cleaned_data["city"],
        }

        if self.cleaned_data["city"]:
            return (
                models.Cities.objects.filter(id=self.cleaned_data["city"])
                .values(
                    "id",
                    value=F("name"),
                )
                .first()
            )

        return data

    def clean_state(self):
        data = {
            "id": self.cleaned_data["state"],
            "value": self.cleaned_data["state"],
        }

        if self.cleaned_data["state"]:
            return (
                models.States.objects.filter(id=self.cleaned_data["state"])
                .values(
                    "id",
                    value=F("name"),
                )
                .first()
            )

        return data

    def clean_country(self):
        data = {
            "id": self.cleaned_data["country"],
            "value": self.cleaned_data["country"],
        }

        if self.cleaned_data["country"]:
            return (
                models.Countries.objects.filter(id=self.cleaned_data["country"])
                .values(
                    "id",
                    value=F("name"),
                )
                .first()
            )

        return data

    def clean_tour(self):
        data = {
            "id": self.cleaned_data["tour"],
            "value": self.cleaned_data["tour"],
        }

        if self.cleaned_data["tour"]:
            return (
                models.Tours.objects.filter(id=self.cleaned_data["tour"])
                .values(
                    "id",
                    value=F("name"),
                )
                .first()
            )

        return data

    def clean_musician(self):
        data = {
            "id": self.cleaned_data["musician"],
            "value": self.cleaned_data["musician"],
        }

        if self.cleaned_data["musician"]:
            return (
                models.Relations.objects.filter(id=self.cleaned_data["musician"])
                .values(
                    "id",
                    value=F("name"),
                )
                .first()
            )

        return data

    def clean_band(self):
        data = {
            "id": self.cleaned_data["band"],
            "value": self.cleaned_data["band"],
        }

        if self.cleaned_data["band"]:
            return (
                models.Bands.objects.filter(id=self.cleaned_data["band"])
                .values(
                    "id",
                    value=F("name"),
                )
                .first()
            )

        return data

    def clean_day_of_week(self):
        data = {
            "id": self.cleaned_data["day_of_week"],
            "value": self.cleaned_data["day_of_week"],
        }

        if self.cleaned_data["day_of_week"]:
            days = {
                1: "Sunday",
                2: "Monday",
                3: "Tuesday",
                4: "Wednesday",
                5: "Thursday",
                6: "Friday",
                7: "Saturday",
            }

            data["value"] = days.get(int(self.cleaned_data["day_of_week"]))

        return data


class SetlistSearch(forms.Form):
    def __init__(self, *args: dict, **kwargs: dict) -> None:
        """Initialize form."""
        super().__init__(*args, **kwargs)

    song1 = forms.CharField(
        label="Song:",
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm song1 select2"},
        ),
    )

    choice = forms.ChoiceField(
        label=None,
        choices=[("is", "is"), ("not", "not")],
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm choice"},
        ),
    )

    position = forms.ChoiceField(
        label=None,
        choices=[
            ("anywhere", "Anywhere"),
            ("followed_by", "Followed By"),
            ("show_opener", "Show Opener"),
            ("in_show", "in Main Set"),
            ("in_set_one", "in Set 1"),
            ("set_one_opener", "Set 1 Opener"),
            ("set_one_closer", "Set 1 Closer"),
            ("in_set_two", "in Set 2"),
            ("set_two_opener", "Set 2 Opener"),
            ("set_two_closer", "Set 2 Closer"),
            ("main_set_closer", "Main Set Closer"),
            ("encore_opener", "Encore Opener"),
            ("in_encore", "Encore"),
            ("in_preshow", "Pre-Show"),
            ("in_recording", "Recording"),
            ("in_soundcheck", "Soundcheck"),
            ("show_closer", "Show Closer"),
        ],
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm position"},
        ),
    )

    song2 = forms.CharField(
        label="",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm song2 select2",
            },
        ),
    )

    def clean_song1(self):
        data = {
            "id": "",
            "value": "",
        }

        if self.cleaned_data["song1"]:
            return (
                models.Songs.objects.filter(id=self.cleaned_data["song1"])
                .values(
                    "id",
                    value=F("name"),
                )
                .first()
            )

        return data

    def clean_song2(self):
        data = {
            "id": "",
            "value": "",
        }

        if self.cleaned_data["song2"]:
            return (
                models.Songs.objects.filter(id=self.cleaned_data["song2"])
                .values(
                    "id",
                    value=F("name"),
                )
                .first()
            )

        return data

    def clean_position(self):
        positions = {
            "anywhere": "Anywhere",
            "followed_by": "Followed By",
            "show_opener": "Show Opener",
            "in_show": "Show",
            "in_set_one": "Set 1",
            "set_one_opener": "Set 1 Opener",
            "set_one_closer": "Set 1 Closer",
            "in_set_two": "Set 2",
            "set_two_opener": "Set 2 Opener",
            "set_two_closer": "Set 2 Closer",
            "main_set_closer": "Main Set Closer",
            "encore_opener": "Encore Opener",
            "in_encore": "Encore",
            "in_preshow": "Pre-Show",
            "in_recording": "Recording",
            "in_soundcheck": "Soundcheck",
            "show_closer": "Show Closer",
        }

        return positions.get(self.cleaned_data["position"])


class EventSearch(forms.Form):
    def __init__(self, *args: dict, **kwargs: dict) -> None:
        """Initialize form."""
        super().__init__(*args, **kwargs)

    date = forms.CharField(
        label="",
        required=False,
        widget=forms.TextInput(
            attrs={
                "id": "eventSearch",
                "type": "search",
                "name": "date",
                "placeholder": "YYYY-MM-DD",
                "maxlength": 10,
                "class": "form-control form-control-sm date-form",
            },
        ),
    )


class SetlistNoteSearch(forms.Form):
    def __init__(self, *args: dict, **kwargs: dict) -> None:
        """Initialize form."""
        super().__init__(*args, **kwargs)

    query = forms.CharField(
        label="",
        required=True,
        widget=forms.TextInput(
            attrs={
                "id": "noteSearch",
                "type": "search",
                "name": "note",
                "placeholder": "Enter query",
                "class": "form-control",
            },
        ),
    )


class UserForm(UserCreationForm):
    username = forms.CharField(
        label="Username",
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control form-control-sm"}),
    )

    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(
            attrs={"autocomplete": "email", "class": "form-control form-control-sm"},
        ),
    )

    password1 = forms.CharField(
        label="Password",
        required=True,
        widget=forms.PasswordInput(attrs={"class": "form-control form-control-sm"}),
        help_text=password_validation.password_validators_help_text_html(),
    )

    password2 = forms.CharField(
        required=True,
        label="Enter the same password as before, for verification.",
        widget=forms.PasswordInput(attrs={"class": "form-control form-control-sm"}),
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password1",
            "password2",
        ]


class UpdateUserForm(forms.ModelForm):
    def __init__(self, *args: dict, **kwargs: dict) -> None:
        """Initialize form."""
        super().__init__(*args, **kwargs)

    username = forms.CharField(
        label="Username:",
        required=True,
        widget=forms.TextInput(
            attrs={
                "id": "username",
                "type": "text",
                "name": "username",
                "class": "form-control form-control-sm",
            },
        ),
    )

    email = forms.EmailField(
        label="Email:",
        max_length=254,
        required=True,
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "id": "email",
                "type": "email",
                "name": "email",
                "class": "form-control form-control-sm",
            },
        ),
    )

    class Meta:
        model = User
        fields = ["username", "email"]


class ContactForm(forms.Form):
    def __init__(self, *args: dict, **kwargs: dict) -> None:
        """Initialize form."""
        super().__init__(*args, **kwargs)

    subject = forms.ChoiceField(
        label="Subject",
        choices=[
            ("problem", "Bug/Problem"),
            ("suggestion", "Suggestion"),
            ("comment", "Comment"),
            ("comment", "Question"),
        ],
        required=True,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm subject"},
        ),
    )

    email = forms.EmailField(
        label="Contact Email",
        max_length=254,
        required=True,
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "id": "email",
                "type": "email",
                "name": "email",
                "class": "form-control form-control-sm",
            },
        ),
    )

    message = forms.CharField(
        label="Message",
        required=True,
        widget=forms.Textarea(
            attrs={
                "id": "message",
                "name": "message",
                "placeholder": "Message",
                "class": "form-control form-control-sm",
            },
        ),
    )

    verification = forms.CharField(
        label="Verification",
        required=True,
        help_text="Enter the release year of Bruce's third album",
        widget=forms.TextInput(
            attrs={
                "id": "verification",
                "name": "verification",
                "placeholder": "-",
                "class": "form-control form-control-sm",
            },
        ),
    )
