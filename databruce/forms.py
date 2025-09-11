import calendar
import datetime
import re

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Reset, Submit
from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from . import models

DATE = datetime.datetime.today()


class AdvancedEventSearch(forms.Form):
    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003, D107
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"

        self.helper.add_input(Submit("submit", "Go", css_class="btn-primary"))
        self.helper.add_input(Reset("reset", "Clear", css_class="btn-secondary"))

    class FormChoiceSelect(forms.ChoiceField):
        def __init__(self, widget_id, *args, **kwargs):
            kwargs["choices"] = [("is", "is"), ("not", "not")]
            kwargs["required"] = False
            kwargs["widget"] = forms.Select(
                attrs={"class": "form-select form-select-sm", "id": widget_id},
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
            .prefetch_related("country")
            .distinct("name")
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
                .select_related("state", "country")
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
                "name": "start_date",
                "placeholder": "YYYY-MM-DD",
                "maxlength": 10,
                "class": "form-control form-control-sm",
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
                "name": "end_date",
                "placeholder": "YYYY-MM-DD",
                "maxlength": 10,
                "class": "form-control form-control-sm",
            },
        ),
    )

    month_choice = FormChoiceSelect(widget_id="monthChoice")

    month = forms.ChoiceField(
        label="Month",
        choices=get_months(),
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm", "id": "month"},
        ),
    )

    day_choice = FormChoiceSelect(widget_id="dayChoice")

    day = forms.ChoiceField(
        label="Day",
        choices=get_days(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select form-select-sm", "id": "day"}),
    )

    dow_choice = FormChoiceSelect(widget_id="dowChoice")

    day_of_week = forms.ChoiceField(
        label="Day of Week",
        choices=days_of_week,
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm", "id": "day-of-week"},
        ),
    )

    city_choice = FormChoiceSelect(widget_id="cityChoice")

    city = forms.ChoiceField(
        label="City",
        required=False,
        choices=get_cities(),
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm select2", "id": "citySelect"},
        ),
    )

    state_choice = FormChoiceSelect(widget_id="stateChoice")

    state = forms.ChoiceField(
        label="State",
        choices=get_states(),
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm select2", "id": "stateSelect"},
        ),
    )

    country_choice = FormChoiceSelect(widget_id="countryChoice")

    country = forms.ChoiceField(
        label="Country",
        choices=get_countries(),
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm select2",
                "id": "countrySelect",
            },
        ),
    )

    tour_choice = FormChoiceSelect(widget_id="tourChoice")

    tour = forms.ChoiceField(
        label="Tour",
        choices=get_tours(),
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm select2", "id": "tourSelect"},
        ),
    )

    musician_choice = FormChoiceSelect(widget_id="musicianChoice")

    musician = forms.ChoiceField(
        label="Musician",
        choices=get_musicians(),
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm select2",
                "id": "musicianSelect",
            },
        ),
    )

    band_choice = FormChoiceSelect(widget_id="dayChoice")

    band = forms.ChoiceField(
        label="Band",
        choices=get_bands(),
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm select2", "id": "bandSelect"},
        ),
    )

    conjunction = forms.ChoiceField(
        label="Conjunction",
        choices=[("and", "AND"), ("or", "OR")],
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm", "id": "conjunctionSelect"},
        ),
    )

    def clean_first_date(self):
        if self.cleaned_data["first_date"]:
            if re.search(r"^\d{4}-\d{2}$", self.cleaned_data["first_date"]):
                return (
                    datetime.datetime.strptime(
                        self.cleaned_data["first_date"],
                        "%Y-%m",
                    )
                    .replace(day=1)
                    .date()
                )

            if re.search(r"^\d{4}-\d{2}-\d{2}$", self.cleaned_data["first_date"]):
                return datetime.datetime.strptime(
                    self.cleaned_data["first_date"],
                    "%Y-%m-%d",
                ).date()

        return datetime.datetime.strptime("1965-01-01", "%Y-%m-%d").date()

    def clean_last_date(self):
        if self.cleaned_data["last_date"]:
            if re.search(r"^\d{4}-\d{2}$", self.cleaned_data["last_date"]):
                dt = datetime.datetime.strptime(
                    self.cleaned_data["last_date"],
                    "%Y-%m",
                )

                last = calendar.monthrange(dt.year, dt.month)[1]

                return dt.replace(day=last).date()

            if re.search(r"^\d{4}-\d{2}-\d{2}$", self.cleaned_data["last_date"]):
                return datetime.datetime.strptime(
                    self.cleaned_data["last_date"],
                    "%Y-%m-%d",
                ).date()

        return datetime.datetime.strptime(f"{DATE.year}-12-31", "%Y-%m-%d").date()


class SetlistSearch(forms.Form):
    def __init__(self, *args: dict, **kwargs: dict) -> None:
        """Initialize form."""
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Go", css_class="btn-primary"))
        self.helper.add_input(Reset("reset", "Clear", css_class="btn-secondary"))

    songs = [("", "")]

    songs.extend(
        models.Songs.objects.filter(num_plays_public__gte=1)
        .order_by("name")
        .values_list("id", "name"),
    )

    song1 = forms.ChoiceField(
        label="Song:",
        choices=songs,
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

    song2 = forms.ChoiceField(
        label="",
        choices=songs,
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm song2 select2",
            },
        ),
    )

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
        self.helper = FormHelper()
        self.helper.form_method = "get"
        self.helper.add_input(Submit("submit", "Go", css_class="btn-primary"))

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
                "class": "form-control",
            },
        ),
    )


class SetlistNoteSearch(forms.Form):
    def __init__(self, *args: dict, **kwargs: dict) -> None:
        """Initialize form."""
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Go", css_class="btn-primary"))

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
    username = forms.CharField(widget=forms.TextInput())
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(),
        help_text=password_validation.password_validators_help_text_html(),
    )

    password2 = forms.CharField(
        label="Enter the same password as before, for verification.",
        widget=forms.PasswordInput(),
        help_text=password_validation.password_validators_help_text_html(),
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
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_input(
            Submit("submit", "Update", css_class="btn btn-sm btn-success"),
        )

    username = forms.CharField(
        label="Username:",
        widget=forms.TextInput(
            attrs={
                "id": "username",
                "type": "text",
                "name": "username",
                "class": "form-control mb-3",
            },
        ),
    )

    email = forms.EmailField(
        label="Email:",
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "id": "email",
                "type": "email",
                "name": "email",
                "class": "form-control mb-3",
            },
        ),
    )

    class Meta:
        model = User
        fields = ["username", "email"]
