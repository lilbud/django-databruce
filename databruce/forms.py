import calendar
import datetime

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
        label_suffix=":",
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
        label_suffix=":",
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

    month_choice = forms.ChoiceField(
        label=None,
        choices=[("is", "is"), ("not", "not")],
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm", "id": "monthChoice"},
        ),
    )

    month = forms.ChoiceField(
        label="Month",
        label_suffix=":",
        choices=get_months(),
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm", "id": "month"},
        ),
    )

    day_choice = forms.ChoiceField(
        label=None,
        choices=[("is", "is"), ("not", "not")],
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm", "id": "dayChoice"},
        ),
    )

    day = forms.ChoiceField(
        label="Day",
        label_suffix=":",
        choices=get_days(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select form-select-sm", "id": "day"}),
    )

    dow_choice = forms.ChoiceField(
        label=None,
        choices=[("is", "is"), ("not", "not")],
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm", "id": "dowChoice"},
        ),
    )

    day_of_week = forms.ChoiceField(
        label="Day of Week",
        label_suffix=":",
        choices=days_of_week,
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm", "id": "day-of-week"},
        ),
    )

    city_choice = forms.ChoiceField(
        label=None,
        choices=[("is", "is"), ("not", "not")],
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm", "id": "cityChoice"},
        ),
    )

    city = forms.ChoiceField(
        label="City",
        label_suffix=":",
        required=False,
        choices=get_cities(),
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm select2", "id": "citySelect"},
        ),
    )

    state_choice = forms.ChoiceField(
        label=None,
        choices=[("is", "is"), ("not", "not")],
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm", "id": "stateChoice"},
        ),
    )

    state = forms.ChoiceField(
        label="State",
        label_suffix=":",
        choices=get_states(),
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm select2", "id": "stateSelect"},
        ),
    )

    country_choice = forms.ChoiceField(
        label=None,
        choices=[("is", "is"), ("not", "not")],
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm", "id": "countryChoice"},
        ),
    )

    country = forms.ChoiceField(
        label="Country",
        label_suffix=":",
        choices=get_countries(),
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm select2",
                "id": "countrySelect",
            },
        ),
    )

    tour_choice = forms.ChoiceField(
        label=None,
        choices=[("is", "is"), ("not", "not")],
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm", "id": "tourChoice"},
        ),
    )

    tour = forms.ChoiceField(
        label="Tour",
        label_suffix=":",
        choices=get_tours(),
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm select2", "id": "tourSelect"},
        ),
    )

    musician_choice = forms.ChoiceField(
        label=None,
        choices=[("is", "is"), ("not", "not")],
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm", "id": "musician-choice"},
        ),
    )

    musician = forms.ChoiceField(
        label="Musician",
        label_suffix=":",
        choices=get_musicians(),
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm select2",
                "id": "musicianSelect",
            },
        ),
    )

    band_choice = forms.ChoiceField(
        label=None,
        choices=[("is", "is"), ("not", "not")],
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm", "id": "band-choice"},
        ),
    )

    band = forms.ChoiceField(
        label="Band",
        label_suffix=":",
        choices=get_bands(),
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm select2", "id": "bandSelect"},
        ),
    )

    conjunction = forms.ChoiceField(
        label="Conjunction",
        label_suffix=":",
        choices=[("and", "AND"), ("or", "OR")],
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm", "id": "conjunctionSelect"},
        ),
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

        return (
            models.Events.objects.filter(date__isnull=False)
            .order_by("date")
            .first()
            .date
        )

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
            models.Events.objects.filter(date__isnull=False)
            .order_by("-date")
            .first()
            .date
        )


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
        self.helper.form_method = "post"
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
