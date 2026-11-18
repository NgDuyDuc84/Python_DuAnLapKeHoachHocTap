from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator, URLValidator
from django.db import models
from django.utils import timezone


class Subject(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField("Tên môn học", max_length=150)
    semester = models.CharField("Học kỳ", max_length=50, blank=True)
    color = models.CharField(
        "Màu nhận diện",
        max_length=7,
        default="#176b58",
        validators=[RegexValidator(r"^#[0-9a-fA-F]{6}$", "Chọn màu dạng #RRGGBB.")],
    )
    is_archived = models.BooleanField("Lưu trữ môn học", default=False)

    class Meta:
        ordering = ["name", "pk"]

    def __str__(self):
        label = f"{self.name} — {self.semester}" if self.semester else self.name
        return f"{label} (đã lưu trữ)" if self.is_archived else label


class Task(models.Model):
    class Priority(models.IntegerChoices):
        LOW = 1, "Thấp"
        NORMAL = 2, "Trung bình"
        HIGH = 3, "Cao"

    class Status(models.TextChoices):
        TODO = "todo", "Chưa bắt đầu"
        IN_PROGRESS = "in_progress", "Đang thực hiện"
        DONE = "done", "Hoàn thành"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.ForeignKey(
        Subject, verbose_name="Môn học", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="tasks",
    )
    title = models.CharField("Tên công việc", max_length=200)
    description = models.TextField("Mô tả", blank=True)
    deadline = models.DateTimeField("Hạn hoàn thành")
    priority = models.PositiveSmallIntegerField(
        "Mức ưu tiên", choices=Priority.choices, default=Priority.NORMAL
    )
    estimated_minutes = models.PositiveIntegerField(
        "Thời lượng ước tính (phút)", validators=[MinValueValidator(1)]
    )
    remaining_minutes = models.PositiveIntegerField("Thời lượng còn lại (phút)")
    can_split = models.BooleanField("Cho phép chia thành nhiều buổi", default=True)
    status = models.CharField(
        "Trạng thái", max_length=20, choices=Status.choices, default=Status.TODO
    )

    class Meta:
        ordering = ["deadline", "-priority", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(estimated_minutes__gt=0), name="task_estimate_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(priority__in=[1, 2, 3]), name="task_priority_valid"
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(status="done", remaining_minutes=0)
                    | models.Q(status__in=["todo", "in_progress"], remaining_minutes__gt=0)
                ),
                name="task_status_remaining_consistent",
            ),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        errors = {}
        if self.subject_id and self.subject.owner_id != self.owner_id:
            errors["subject"] = "Môn học phải thuộc tài khoản của bạn."
        if self.status == self.Status.DONE and self.remaining_minutes not in (None, 0):
            errors["remaining_minutes"] = "Công việc hoàn thành phải còn 0 phút."
        if self.status in (self.Status.TODO, self.Status.IN_PROGRESS) and self.remaining_minutes == 0:
            errors["remaining_minutes"] = "Nhập thời lượng còn lại lớn hơn 0 hoặc chọn Hoàn thành."
        if errors:
            raise ValidationError(errors)

    @property
    def is_overdue(self):
        return self.status != self.Status.DONE and self.deadline < timezone.now()


class Material(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.ForeignKey(
        Subject, verbose_name="Môn học", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="materials",
    )
    task = models.ForeignKey(
        Task, verbose_name="Công việc", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="materials",
    )
    title = models.CharField("Tên tài liệu", max_length=200)
    url = models.URLField(
        "Đường dẫn", max_length=2048, blank=True,
        validators=[URLValidator(schemes=["http", "https"])],
    )
    file_name = models.CharField("Tên tệp", max_length=255, blank=True, editable=False)
    file_data = models.BinaryField("Nội dung tệp", null=True, blank=True, editable=False)
    description = models.TextField("Ghi chú", blank=True)

    class Meta:
        ordering = ["title", "pk"]
        constraints = [models.CheckConstraint(
            condition=~models.Q(url="") | models.Q(file_data__isnull=False),
            name="material_has_link_or_file",
        )]

    def __str__(self):
        return self.title

    def clean(self):
        errors = {}
        if not self.url and self.file_data is None:
            errors["url"] = "Nhập đường dẫn hoặc tải lên một tệp tài liệu."
        for name in ("subject", "task"):
            related = getattr(self, name)
            if related is not None and related.owner_id != self.owner_id:
                errors[name] = "Chỉ được liên kết dữ liệu thuộc tài khoản của bạn."
        if errors:
            raise ValidationError(errors)
