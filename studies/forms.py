from django import forms
from django.core.validators import FileExtensionValidator

from .models import Material, Subject, Task


class OwnedModelForm(forms.ModelForm):
    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.owner = user
        for name, model in (("subject", Subject), ("task", Task)):
            if name in self.fields:
                self.fields[name].queryset = model.objects.filter(owner=user)


class SubjectForm(OwnedModelForm):
    class Meta:
        model = Subject
        fields = ("name", "semester", "color", "is_archived")
        widgets = {"color": forms.TextInput(attrs={"type": "color"})}
        help_texts = {
            "is_archived": "Ẩn khỏi danh sách môn đang học; công việc và tài liệu vẫn được giữ."
        }


class TaskForm(OwnedModelForm):
    class Meta:
        model = Task
        fields = (
            "title", "subject", "description", "deadline", "priority",
            "estimated_minutes", "remaining_minutes", "can_split", "status",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "deadline": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }
        help_texts = {
            "deadline": "Giờ Việt Nam. Có thể nhập hạn đã qua để theo dõi việc quá hạn.",
            "estimated_minutes": "Lớn hơn 0. Khi tạo mới, thời lượng còn lại mặc định bằng ước tính.",
            "remaining_minutes": "Có thể tăng nếu việc phát sinh thêm; chọn Hoàn thành để đưa về 0.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields.pop("remaining_minutes")

    def clean(self):
        cleaned = super().clean()
        if not self.instance.pk:
            estimate = cleaned.get("estimated_minutes")
            cleaned["remaining_minutes"] = estimate if estimate is not None and estimate > 0 else None
        if cleaned.get("status") == Task.Status.DONE:
            cleaned["remaining_minutes"] = 0
        return cleaned


class MaterialForm(OwnedModelForm):
    attachment = forms.FileField(
        label="Tải tệp lên", required=False, max_length=255,
        validators=[FileExtensionValidator(["pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "txt", "csv", "png", "jpg", "jpeg"])],
        help_text="PDF, Word, PowerPoint, Excel, TXT/CSV hoặc ảnh PNG/JPG; tối đa 10 MB.",
        widget=forms.FileInput(attrs={"accept": ".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.csv,.png,.jpg,.jpeg"}),
    )
    remove_attachment = forms.BooleanField(label="Gỡ tệp hiện tại", required=False)

    class Meta:
        model = Material
        fields = ("title", "url", "subject", "task", "description")
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}
        help_texts = {"url": "Dùng đường dẫn HTTP hoặc HTTPS tới bài giảng, tài liệu hoặc tệp đã lưu."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields(("title", "url", "attachment", "remove_attachment", "subject", "task", "description"))
        if not self.instance.file_name:
            self.fields.pop("remove_attachment")

    def clean_attachment(self):
        uploaded = self.cleaned_data.get("attachment")
        if uploaded and uploaded.size > 10 * 1024 * 1024:
            raise forms.ValidationError("Tệp vượt quá giới hạn 10 MB.")
        return uploaded

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("remove_attachment"):
            self.instance.file_name, self.instance.file_data = "", None
        uploaded = cleaned.get("attachment")
        if uploaded:
            self.instance.file_name = uploaded.name.replace("\\", "/").rsplit("/", 1)[-1]
            self.instance.file_data = uploaded.read()
        return cleaned


class TaskProgressForm(OwnedModelForm):
    class Meta:
        model = Task
        fields = ("status", "remaining_minutes")
        help_texts = {"remaining_minutes": "Nhập thời gian thực tế còn cần. Chọn Hoàn thành để đưa về 0. Thay đổi tiến độ chưa tự dời hoặc hủy các buổi cũ; dùng Xếp lại lịch và kiểm tra cảnh báo."}

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("status") == Task.Status.DONE:
            cleaned["remaining_minutes"] = 0
        return cleaned


class StudyFilterForm(forms.Form):
    q = forms.CharField(label="Tìm kiếm", required=False, max_length=200)

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        for name, model in (("subject", Subject), ("task", Task)):
            if name in self.fields:
                self.fields[name].queryset = model.objects.filter(owner=user)


class SubjectFilterForm(StudyFilterForm):
    state = forms.ChoiceField(
        label="Danh sách", required=False,
        choices=[("", "Đang học"), ("archived", "Đã lưu trữ"), ("all", "Tất cả")],
    )


class TaskFilterForm(StudyFilterForm):
    subject = forms.ModelChoiceField(label="Môn học", queryset=Subject.objects.none(), required=False)
    status = forms.ChoiceField(
        label="Trạng thái", required=False,
        choices=[("", "Tất cả"), *Task.Status.choices, ("overdue", "Quá hạn")],
    )
    priority = forms.TypedChoiceField(
        label="Ưu tiên", required=False, coerce=int, empty_value=None,
        choices=[("", "Tất cả"), *Task.Priority.choices],
    )


class MaterialFilterForm(StudyFilterForm):
    subject = forms.ModelChoiceField(label="Môn học", queryset=Subject.objects.none(), required=False)
    task = forms.ModelChoiceField(label="Công việc", queryset=Task.objects.none(), required=False)
