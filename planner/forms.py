from datetime import timedelta

from django import forms
from django.utils import timezone

from studies.forms import OwnedModelForm

from .models import DAY_CHOICES, BusyEvent, StudyPlan, StudyPreference, StudySession


class BusyEventForm(OwnedModelForm):
    class Meta:
        model = BusyEvent
        fields = ("title", "starts_at", "ends_at", "repeat_weekly", "repeat_until")
        widgets = {
            name: forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M")
            for name in ("starts_at", "ends_at")
        }
        widgets["repeat_until"] = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
        help_texts = {
            "starts_at": "Giờ Việt Nam. Với lịch lặp, đây là lần đầu tiên của chuỗi.",
            "ends_at": "Có thể chọn ngày hôm sau cho ca qua đêm.",
            "repeat_weekly": "Lặp đúng thứ và giờ của lần đầu. Tạo lịch riêng nếu bận nhiều thứ.",
            "repeat_until": "Tính cả ngày này. Để trống nếu chưa xác định ngày dừng lặp.",
        }

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("repeat_weekly"):
            cleaned["repeat_until"] = None
        return cleaned


class StudyPreferenceForm(OwnedModelForm):
    study_days = forms.TypedMultipleChoiceField(
        label="Ngày được học", choices=DAY_CHOICES, coerce=int, required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Khung giờ bên dưới áp dụng chung cho các ngày đã chọn. Có thể bỏ chọn tất cả.",
    )

    class Meta:
        model = StudyPreference
        fields = (
            "study_days", "study_start", "study_end", "max_daily_minutes",
            "session_minutes", "break_minutes",
        )
        widgets = {
            "study_start": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "study_end": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
        }
        help_texts = {
            "study_end": "Khung học trong cùng một ngày, giờ kết thúc lớn hơn giờ bắt đầu.",
            "max_daily_minutes": "Từ 1 đến 1440 phút; đây là giới hạn, không phải lượng thời gian bắt buộc học.",
            "session_minutes": "Dùng làm độ dài ưu tiên khi lập kế hoạch học tập.",
            "break_minutes": "Thời gian nghỉ cần chừa giữa các buổi tự học, từ 0 đến 1440 phút.",
        }


class WeekForm(forms.Form):
    week = forms.DateField(
        label="Chọn một ngày trong tuần",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )

    def clean_week(self):
        monday = self.cleaned_data["week"]
        monday -= timedelta(days=monday.weekday())
        try:
            monday - timedelta(days=7)
            monday + timedelta(days=14)
        except OverflowError:
            raise forms.ValidationError("Ngày nằm ngoài phạm vi lịch được hỗ trợ.")
        return monday


class PlanWeekForm(WeekForm):
    mode = forms.ChoiceField(label="Cách xếp lịch", choices=StudyPlan.Mode.choices, required=False)

    def clean_mode(self):
        return self.cleaned_data["mode"] or StudyPlan.Mode.ADD

    def clean_week(self):
        monday = super().clean_week()
        if monday + timedelta(days=7) <= timezone.localdate():
            raise forms.ValidationError("Chọn tuần hiện tại hoặc một tuần tương lai để xếp lịch.")
        return monday


class SessionMoveForm(forms.Form):
    starts_at = forms.DateTimeField(label="Bắt đầu mới", widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"))
    ends_at = forms.DateTimeField(label="Kết thúc mới", widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"))


class SessionRecordForm(forms.Form):
    result = forms.ChoiceField(label="Kết quả buổi học", choices=[
        (StudySession.Status.DONE, "Đã học"), (StudySession.Status.CANCELLED, "Hủy / bỏ qua"),
    ])
    remaining_minutes = forms.IntegerField(
        label="Công việc còn lại bao nhiêu phút?", min_value=0, max_value=2147483647,
        help_text="Nhập 0 nếu đã xong việc. Hủy/bỏ qua buổi thì giữ nguyên số phút còn lại.",
    )


class SessionLockForm(forms.Form):
    locked = forms.TypedChoiceField(choices=[("true", "Khóa"), ("false", "Mở khóa")], coerce=lambda value: value == "true")
