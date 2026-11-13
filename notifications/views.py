from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, UpdateView

from studies.views import OwnedFormMixin, OwnedObjectMixin

from .forms import InboxFilterForm, ReminderPreferenceForm
from .models import Reminder, ReminderPreference
from .services import get_preferences


def email_mode():
    backend = settings.EMAIL_BACKEND
    if ".console." in backend:
        return "Thử nghiệm: email hiển thị ở terminal chạy worker, chưa gửi tới hộp thư."
    if any(name in backend for name in (".locmem.", ".filebased.", ".dummy.")):
        return "Email đang ở chế độ kiểm thử, chưa gửi tới hộp thư."
    return "Email dùng cấu hình máy chủ gửi. Đã bàn giao email chưa có nghĩa hộp thư đã nhận."


class InboxView(OwnedObjectMixin, ListView):
    model = Reminder
    template_name = "notifications/inbox.html"
    context_object_name = "reminders"
    paginate_by = 20
    page_title = "Thông báo của bạn"

    def get_queryset(self):
        self.filter_form = InboxFilterForm(self.request.GET)
        queryset = super().get_queryset().filter(channel=Reminder.Channel.IN_APP, status=Reminder.Status.SENT)
        if not self.filter_form.is_valid():
            return queryset.none()
        if self.filter_form.cleaned_data["state"] == "unread":
            queryset = queryset.filter(read_at__isnull=True)
        return queryset.select_related("task", "study_session__plan")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        context["unread_count"] = Reminder.objects.filter(owner=self.request.user, channel=Reminder.Channel.IN_APP,
            status=Reminder.Status.SENT, read_at__isnull=True).count()
        return context


class EmailHistoryView(OwnedObjectMixin, ListView):
    model = Reminder
    template_name = "notifications/email_history.html"
    context_object_name = "reminders"
    paginate_by = 20
    page_title = "Lịch sử email nhắc"

    def get_queryset(self):
        return super().get_queryset().filter(channel=Reminder.Channel.EMAIL).select_related("task", "study_session__plan")

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), "email_mode": email_mode()}


class PreferenceView(OwnedFormMixin, UpdateView):
    model = ReminderPreference
    form_class = ReminderPreferenceForm
    template_name = "notifications/preferences.html"
    success_url = reverse_lazy("notifications:preferences")
    page_title = "Tùy chọn nhắc việc"

    def get_object(self, queryset=None):
        return get_preferences(self.request.user)

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), "email_mode": email_mode()}


class ReadView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        reminder = get_object_or_404(Reminder, owner=request.user, pk=pk,
                                    channel=Reminder.Channel.IN_APP, status=Reminder.Status.SENT)
        Reminder.objects.filter(pk=reminder.pk, read_at__isnull=True).update(read_at=timezone.now())
        return redirect("notifications:inbox")


class ReadAllView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request):
        Reminder.objects.filter(owner=request.user, channel=Reminder.Channel.IN_APP,
            status=Reminder.Status.SENT, read_at__isnull=True).update(read_at=timezone.now())
        return redirect("notifications:inbox")


class RetryEmailView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        reminder = get_object_or_404(Reminder, owner=request.user, pk=pk, channel=Reminder.Channel.EMAIL)
        updated = Reminder.objects.filter(pk=reminder.pk, status__in=[Reminder.Status.FAILED, Reminder.Status.UNCERTAIN]).update(
            status=Reminder.Status.PENDING, attempts=0, next_attempt_at=timezone.now(), claim_token=None, claimed_at=None,
        )
        messages.success(request, "Đã xếp vào hàng đợi để worker kiểm tra và gửi lại." if updated else "Nhắc này không cần gửi lại hoặc đã được xếp vào hàng đợi.")
        return redirect("notifications:email_history")
