from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from studies.forms import OwnedModelForm

from .models import ReminderPreference


class ReminderPreferenceForm(OwnedModelForm):
    class Meta:
        model = ReminderPreference
        fields = ("in_app_enabled", "email_enabled", "deadline_minutes", "session_minutes")

    def clean_email_enabled(self):
        enabled = self.cleaned_data["email_enabled"]
        if enabled:
            try:
                validate_email(self.instance.owner.email)
            except ValidationError:
                raise forms.ValidationError("Tài khoản cần có email hợp lệ. Email lấy từ thông tin đăng ký; tài khoản quản trị có thể cập nhật trong Admin.")
        return enabled


class InboxFilterForm(forms.Form):
    state = forms.ChoiceField(label="Hiển thị", required=False,
                             choices=[("", "Tất cả"), ("unread", "Chưa đọc")])
