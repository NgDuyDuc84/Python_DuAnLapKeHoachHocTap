from django import forms
from django.contrib.auth.forms import UserCreationForm


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label="Email",
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    class Meta(UserCreationForm.Meta):
        fields = ("username", "email")
        labels = {"username": "Tên đăng nhập"}
        widgets = {
            "username": forms.TextInput(attrs={"autocomplete": "username"}),
        }
