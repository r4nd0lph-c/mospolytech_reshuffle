from django.utils.translation import gettext_lazy as _
from django import forms
from django.contrib.auth.forms import AuthenticationForm


class AuthForm(AuthenticationForm):
    username = forms.CharField(
        label=_("Username"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "*"
            }
        )
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "*"
            }
        )
    )
    remember_me = forms.BooleanField(
        label=_("Remember me") + "?",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "type": "checkbox"
            }
        )
    )


class CreationForm(forms.Form):
    __MIN = 1
    __MAX = 100

    def __init__(self, subject_choices, *args, **kwargs):
        super(CreationForm, self).__init__(*args, **kwargs)
        self.fields["subject"].queryset = subject_choices

    subject = forms.ModelChoiceField(
        queryset=None,
        empty_label=_("Choose a subject"),
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "style": "padding: 1rem .75rem"
            }
        )
    )
    date = forms.DateField(
        input_formats=["%d.%m.%Y"],
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "style": "padding: 1rem .75rem",
                "placeholder": _("Exam date") + ": dd.mm.yyyy",
                "autocomplete": "off"
            }
        )
    )
    amount = forms.IntegerField(
        min_value=__MIN,
        max_value=__MAX,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "style": "padding: 1rem .75rem",
                "placeholder": _("Number of variants") + f": {__MIN} – {__MAX}",
                "type": "number",
                "min": __MIN,
                "max": __MAX
            }
        )
    )
