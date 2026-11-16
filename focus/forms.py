import uuid
from datetime import timedelta

from django import forms
from django.utils import timezone

from studies.forms import OwnedModelForm
from studies.models import Task

from .models import StudyLog
from .services import task_labels


class FocusStartForm(forms.Form):
    task = forms.ModelChoiceField(label="Công việc cần tập trung", queryset=Task.objects.none(), empty_label="Chọn công việc…")
    request_key = forms.UUIDField(widget=forms.HiddenInput, initial=uuid.uuid4)

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["task"].queryset = Task.objects.filter(owner=user).exclude(status=Task.Status.DONE)


class FinishForm(forms.Form):
    notes = forms.CharField(label="Ghi chú buổi học", required=False, max_length=1000,
                           widget=forms.Textarea(attrs={"rows": 2}))


class StudyLogForm(OwnedModelForm):
    entry_key = forms.UUIDField(widget=forms.HiddenInput, initial=uuid.uuid4)

    class Meta:
        model = StudyLog
        fields = ("task", "studied_on", "minutes", "notes")
        labels = {"task": "Công việc"}
        widgets = {"studied_on": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
                   "notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["task"].required = not self.instance.pk
        if self.instance.pk:
            self.fields.pop("entry_key")

    def save(self, commit=True):
        log = super().save(commit=False)
        if log.task_id:
            for key, value in task_labels(log.task).items():
                setattr(log, key, value)
        if commit:
            log.save()
        return log


class LogNotesForm(OwnedModelForm):
    class Meta:
        model = StudyLog
        fields = ("notes",)
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class LogRangeForm(forms.Form):
    start = forms.DateField(label="Từ ngày", widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    end = forms.DateField(label="Đến ngày", widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("start"), cleaned.get("end")
        if start and end:
            if start > end or (end - start).days > 365:
                raise forms.ValidationError("Chọn khoảng từ 1 đến 366 ngày, ngày kết thúc không trước ngày bắt đầu.")
            if end > timezone.localdate():
                raise forms.ValidationError("Chọn ngày kết thúc không nằm trong tương lai.")
        return cleaned


def default_range():
    today = timezone.localdate()
    return {"start": (today - timedelta(days=6)).isoformat(), "end": today.isoformat()}
