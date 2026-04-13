import calendar
import datetime
import re
from typing import Any

import django_filters
from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)
from django.db.models import F, Q, QuerySet

from . import models

DATE = datetime.datetime.today()
User = get_user_model()


class CustomCharField(forms.CharField):
    def __init__(self, *args, lookup_path=None, **kwargs) -> None:
        self.lookup_path = lookup_path
        super().__init__(*args, **kwargs)


class CustomChoiceField(forms.ChoiceField):
    def __init__(self, *args, lookup_path=None, **kwargs) -> None:
        self.lookup_path = lookup_path
        super().__init__(*args, **kwargs)


class CustomMultipleChoiceField(forms.MultipleChoiceField):
    def valid_value(self, value):
        # This bypasses the 'Select a valid choice' check against self.choices
        return True

    def __init__(self, *args, lookup_path=None, **kwargs) -> None:
        self.lookup_path = lookup_path
        super().__init__(*args, **kwargs)


class AdvancedEventSearch(forms.Form):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        ignore = [
            "first_date",
            "last_date",
            "month",
            "day",
            "conjunction",
            "event_type",
        ]

        for field_name in list(self.fields.keys()):
            if field_name.endswith("_exclude") or field_name in ignore:
                continue

            toggle_name = f"{field_name}_exclude"

            self.fields[toggle_name] = forms.NullBooleanField(
                required=False,
                initial=False,
                label="",
                widget=forms.Select(
                    attrs={
                        "class": "form-select form-select-sm col-3",
                    },
                    choices=((False, "is"), (True, "not")),
                ),
            )

    def iterate_field(self, field: list, value: str, lookup_path: str) -> Q:
        val_id = getattr(
            value,
            "id",
            value.get("id") if isinstance(value, dict) else value,
        )

        # print(field, lookup_path, val_id)

        q_obj = Q(**{lookup_path: val_id})

        # check if the field should be excluded
        exclude_val = self.cleaned_data.get(f"{field}_exclude")

        if exclude_val is True:
            q_obj = ~q_obj

        return q_obj

    def get_filters(self):
        total_filter = Q()

        if not self.is_valid():
            return total_filter

        for field in self.changed_data:
            if field.endswith("_exclude") or field == "conjunction":
                continue

            value = self.cleaned_data.get(field)

            # print(value, type(value))

            if not value:
                continue

            # custom lookup_path variable on field, used to specify queryset lookup
            field_instance = self.fields[field]
            lookup_path = getattr(field_instance, "lookup_path", field)

            if type(value) is list or type(value) is QuerySet:
                lookup_path = f"{lookup_path}__in"

            q_obj = self.iterate_field(field, value, lookup_path)

            # Add the query object to the total filter
            total_filter &= q_obj

        return total_filter

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

    first_date = CustomCharField(
        label="Start Date",
        lookup_path="date__gte",
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

    last_date = CustomCharField(
        label="Last Date",
        lookup_path="date__lte",
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

    month = CustomChoiceField(
        label="Month",
        lookup_path="date__month",
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

    day = CustomChoiceField(
        label="Day",
        lookup_path="date__day",
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

    day_of_week = CustomChoiceField(
        label="Day of Week",
        lookup_path="date__week_day",
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

    event_type = CustomMultipleChoiceField(
        label="Event Type",
        lookup_path="type_id",
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-select form-select-sm select2-multi",
                "id": "type",
                "name": "event_type",
                "placeholder": "Choose multiple",
            },
        ),
    )

    city = CustomCharField(
        label="City",
        lookup_path="venue__city__id",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm select2",
                "id": "city",
                "name": "event_city",
            },
        ),
    )

    state = CustomCharField(
        label="State",
        lookup_path="venue__city__state__id",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm select2",
                "id": "state",
                "name": "event_state",
            },
        ),
    )

    country = CustomCharField(
        label="Country",
        lookup_path="venue__city__country__id",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm select2",
                "id": "country",
                "name": "event_country",
            },
        ),
    )

    venue = CustomCharField(
        label="Venue",
        lookup_path="venue__id",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm select2",
                "id": "venue",
                "name": "event_venue",
            },
        ),
    )

    tour = CustomCharField(
        label="Tour",
        lookup_path="tour__id",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm select2",
                "id": "tour",
                "name": "event_tour",
            },
        ),
    )

    tour_leg = CustomCharField(
        label="Tour Leg",
        lookup_path="leg__id",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm select2",
                "id": "tour-leg",
                "name": "event_tour_leg",
            },
        ),
    )

    relation = CustomCharField(
        label="Relation",
        lookup_path="onstage__relation_id",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-sm select2",
                "id": "relation",
                "name": "event_relation",
            },
        ),
    )

    band = CustomCharField(
        label="Band",
        lookup_path="artist_id",
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
        if self.cleaned_data["first_date"]:
            # partial date, get first of month
            if re.search(r"^\d{4}-\d{2}$", self.cleaned_data["first_date"]):
                date = (
                    datetime.datetime.strptime(self.cleaned_data["first_date"], "%Y-%m")
                    .replace(day=1)
                    .date()
                )

                return {
                    "id": date,
                    "value": date.strftime("%Y-%m-%d"),
                }

            # specific date
            if re.search(r"^\d{4}-\d{2}-\d{2}$", self.cleaned_data["first_date"]):
                date = datetime.datetime.strptime(
                    self.cleaned_data["first_date"],
                    "%Y-%m-%d",
                ).date()

                return {
                    "id": date,
                    "value": date.strftime("%Y-%m-%d"),
                }

        return None

    def clean_last_date(self):
        # default end date is last day of current year
        if self.cleaned_data["last_date"]:
            # partial date
            if re.search(r"^\d{4}-\d{2}$", self.cleaned_data["last_date"]):
                dt = datetime.datetime.strptime(
                    self.cleaned_data["last_date"],
                    "%Y-%m",
                )

                last = calendar.monthrange(dt.year, dt.month)[1]

                return {
                    "id": dt.replace(day=last).date(),
                    "value": dt.replace(day=last).date().strftime("%Y-%m-%d"),
                }

            # specific date
            if re.search(r"^\d{4}-\d{2}-\d{2}$", self.cleaned_data["last_date"]):
                date = datetime.datetime.strptime(
                    self.cleaned_data["last_date"],
                    "%Y-%m-%d",
                ).date()

                return {
                    "id": date,
                    "value": date.strftime("%Y-%m-%d"),
                }

        return None

    def clean_month(self):
        if self.cleaned_data["month"]:
            return {
                "id": self.cleaned_data["month"],
                "value": calendar.month_name[int(self.cleaned_data["month"])],
            }

        return None

    def clean_city(self):
        if self.cleaned_data["city"]:
            return models.Cities.objects.get(id=self.cleaned_data["city"])

        return None

    def clean_event_type(self):
        if self.cleaned_data["event_type"]:
            if isinstance(self.cleaned_data["event_type"], list):
                return models.EventTypes.objects.filter(
                    id__in=self.cleaned_data["event_type"],
                )

            return models.EventTypes.objects.get(id=self.cleaned_data["event_type"])

        return None

    def clean_state(self):
        if self.cleaned_data["state"]:
            return models.States.objects.get(id=self.cleaned_data["state"])

        return None

    def clean_country(self):
        if self.cleaned_data["country"]:
            return models.Countries.objects.get(id=self.cleaned_data["country"])

        return None

    def clean_venue(self):
        if self.cleaned_data["venue"]:
            return models.Venues.objects.get(id=self.cleaned_data["venue"])

        return None

    def clean_tour(self):
        if self.cleaned_data["tour"]:
            return models.Tours.objects.get(id=self.cleaned_data["tour"])

        return None

    def clean_tour_leg(self):
        if self.cleaned_data["tour_leg"]:
            return models.TourLegs.objects.get(id=self.cleaned_data["tour_leg"])

        return None

    def clean_relation(self):
        data = self.cleaned_data["relation"].replace("'", "")

        if data:
            return models.Relations.objects.get(id=data)

        return None

    def clean_band(self):
        if self.cleaned_data["band"]:
            return models.Bands.objects.get(id=self.cleaned_data["band"])

        return None

    def clean_day_of_week(self):
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

            return {
                "id": self.cleaned_data["day_of_week"],
                "value": days.get(int(self.cleaned_data["day_of_week"])),
            }

        return None

    def clean_day(self):
        if self.cleaned_data["day"]:
            return {
                "id": self.cleaned_data["day"],
                "value": self.cleaned_data["day"],
            }

        return None


class SetlistSearch(forms.Form):
    def __init__(self, *args: dict, **kwargs: dict) -> None:
        """Initialize form."""
        super().__init__(*args, **kwargs)
        self.empty_permitted = True

    song1 = forms.CharField(
        label="Song:",
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm song1 select2"},
        ),
    )

    choice = forms.NullBooleanField(
        label=None,
        initial=True,
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select form-select-sm choice"},
            choices=((True, "is"), (False, "not")),
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
            ("premiere", "Premiere"),
            ("debut", "Tour Debut"),
            ("nobruce", "No Bruce"),
            ("request", "Sign Request"),
        ],
        required=False,
        initial="anywhere",
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
        if self.cleaned_data["song1"]:
            return self.cleaned_data["song1"]

        return None

    def clean_song2(self):
        if self.cleaned_data["song2"]:
            return self.cleaned_data["song2"]

        return None

    def clean_position(self):
        if self.cleaned_data["position"]:
            return self.cleaned_data["position"]

        return None

    def clean_choice(self):
        if self.cleaned_data["choice"]:
            return self.cleaned_data["choice"]

        return False


class EventSearch(forms.Form):
    def __init__(self, *args: dict, **kwargs: dict) -> None:
        """Initialize form."""
        super().__init__(*args, **kwargs)

    date = CustomCharField(
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

    query = CustomCharField(
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
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
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


class LoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(),
        label="Remember Me?",
    )


class CustomSetPasswordForm(SetPasswordForm):
    # Add custom fields or override __init__ to change styling
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control form-control-sm"})
