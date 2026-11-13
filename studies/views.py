from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import (
    MaterialFilterForm, MaterialForm, SubjectFilterForm, SubjectForm,
    TaskFilterForm, TaskForm, TaskProgressForm,
)
from .models import Material, Subject, Task


class OwnedObjectMixin(LoginRequiredMixin):
    def get_queryset(self):
        return super().get_queryset().filter(owner=self.request.user)


class OwnedFormMixin(SuccessMessageMixin, OwnedObjectMixin):
    template_name = "studies/form.html"
    success_message = "Đã lưu thay đổi."

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "user": self.request.user}


class FilteredListMixin(OwnedObjectMixin):
    def get_queryset(self):
        self.filter_form = self.filter_form_class(self.request.GET, user=self.request.user)
        queryset = super().get_queryset()
        if not self.filter_form.is_valid():
            return queryset.none()
        return self.filter_queryset(queryset, self.filter_form.cleaned_data)

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), "filter_form": self.filter_form}


class SubjectListView(FilteredListMixin, ListView):
    model = Subject
    filter_form_class = SubjectFilterForm
    page_title = "Môn học của bạn"

    def filter_queryset(self, queryset, data):
        if data["state"] != "all":
            queryset = queryset.filter(is_archived=data["state"] == "archived")
        if data["q"]:
            queryset = queryset.filter(Q(name__icontains=data["q"]) | Q(semester__icontains=data["q"]))
        return queryset


class SubjectCreateView(OwnedFormMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    success_url = reverse_lazy("studies:subject_list")
    page_title = "Thêm môn học"


class SubjectUpdateView(OwnedFormMixin, UpdateView):
    model = Subject
    form_class = SubjectForm
    success_url = reverse_lazy("studies:subject_list")
    page_title = "Sửa môn học"


class SubjectDeleteView(SuccessMessageMixin, OwnedObjectMixin, DeleteView):
    model = Subject
    template_name = "studies/confirm_delete.html"
    success_url = reverse_lazy("studies:subject_list")
    success_message = "Đã xóa môn học. Công việc và tài liệu liên quan vẫn được giữ."
    page_title = "Xóa môn học"
    delete_warning = "Công việc và tài liệu vẫn được giữ, nhưng sẽ không còn liên kết với môn này. Bạn cũng có thể sửa môn và chọn Lưu trữ để giữ nguyên các liên kết."


class TaskListView(FilteredListMixin, ListView):
    model = Task
    filter_form_class = TaskFilterForm
    page_title = "Công việc của bạn"

    def filter_queryset(self, queryset, data):
        queryset = queryset.select_related("subject")
        if data["q"]:
            queryset = queryset.filter(Q(title__icontains=data["q"]) | Q(description__icontains=data["q"]))
        if data["subject"]:
            queryset = queryset.filter(subject=data["subject"])
        if data["priority"]:
            queryset = queryset.filter(priority=data["priority"])
        if data["status"] == "overdue":
            queryset = queryset.exclude(status=Task.Status.DONE).filter(deadline__lt=timezone.now())
        elif data["status"]:
            queryset = queryset.filter(status=data["status"])
        return queryset


class TaskCreateView(OwnedFormMixin, CreateView):
    model = Task
    form_class = TaskForm
    success_url = reverse_lazy("studies:task_list")
    page_title = "Thêm công việc"


class TaskUpdateView(OwnedFormMixin, UpdateView):
    model = Task
    form_class = TaskForm
    success_url = reverse_lazy("studies:task_list")
    page_title = "Sửa công việc"


class TaskProgressView(OwnedFormMixin, UpdateView):
    model = Task
    form_class = TaskProgressForm
    success_url = reverse_lazy("studies:task_list")
    page_title = "Cập nhật tiến độ công việc"


class TaskDeleteView(SuccessMessageMixin, OwnedObjectMixin, DeleteView):
    model = Task
    template_name = "studies/confirm_delete.html"
    success_url = reverse_lazy("studies:task_list")
    success_message = "Đã xóa công việc và các buổi học của công việc. Tài liệu liên quan vẫn được giữ."
    page_title = "Xóa công việc"
    delete_warning = "Các buổi học của công việc này cũng sẽ bị xóa khỏi kế hoạch và lịch tuần. Tài liệu vẫn được giữ, nhưng sẽ không còn liên kết với công việc này."


class MaterialListView(FilteredListMixin, ListView):
    model = Material
    filter_form_class = MaterialFilterForm
    page_title = "Tài liệu của bạn"

    def filter_queryset(self, queryset, data):
        queryset = queryset.select_related("subject", "task")
        if data["q"]:
            queryset = queryset.filter(Q(title__icontains=data["q"]) | Q(description__icontains=data["q"]))
        for name in ("subject", "task"):
            if data[name]:
                queryset = queryset.filter(**{name: data[name]})
        return queryset


class MaterialCreateView(OwnedFormMixin, CreateView):
    model = Material
    form_class = MaterialForm
    success_url = reverse_lazy("studies:material_list")
    page_title = "Thêm tài liệu"


class MaterialUpdateView(OwnedFormMixin, UpdateView):
    model = Material
    form_class = MaterialForm
    success_url = reverse_lazy("studies:material_list")
    page_title = "Sửa tài liệu"


class MaterialDeleteView(SuccessMessageMixin, OwnedObjectMixin, DeleteView):
    model = Material
    template_name = "studies/confirm_delete.html"
    success_url = reverse_lazy("studies:material_list")
    success_message = "Đã xóa liên kết tài liệu."
    page_title = "Xóa tài liệu"
    delete_warning = "Chỉ xóa liên kết đã lưu trong Nhịp Học; tệp ở website gốc không bị xóa."
