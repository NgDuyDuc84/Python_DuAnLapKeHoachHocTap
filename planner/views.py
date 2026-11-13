from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from studies.views import OwnedFormMixin, OwnedObjectMixin

from .forms import BusyEventForm, StudyPreferenceForm, WeekForm
from .models import BusyEvent, StudyPreference
from .services.availability import build_week, get_preferences


class WeekView(LoginRequiredMixin, TemplateView):
    template_name = "planner/week.html"
    page_title = "Lịch tuần của bạn"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = WeekForm(self.request.GET or {"week": timezone.localdate().isoformat()})
        context["week_form"] = form
        if form.is_valid():
            monday = form.cleaned_data["week"]
            preferences = get_preferences(self.request.user)
            context.update({
                "week_start": monday, "week_end": monday + timedelta(days=6),
                "previous_week": (monday - timedelta(days=7)).isoformat(),
                "next_week": (monday + timedelta(days=7)).isoformat(),
                "preferences": preferences,
                "days": build_week(self.request.user, monday, preferences),
            })
        return context


class PreferenceView(OwnedFormMixin, UpdateView):
    model = StudyPreference
    form_class = StudyPreferenceForm
    template_name = "planner/form.html"
    success_url = reverse_lazy("planner:week")
    page_title = "Thời gian học của bạn"

    def get_object(self, queryset=None):
        return get_preferences(self.request.user)


class BusyListView(OwnedObjectMixin, ListView):
    model = BusyEvent
    page_title = "Lịch bận của bạn"


class BusyCreateView(OwnedFormMixin, CreateView):
    model = BusyEvent
    form_class = BusyEventForm
    template_name = "planner/form.html"
    success_url = reverse_lazy("planner:busy_list")
    page_title = "Thêm lịch bận"


class BusyUpdateView(OwnedFormMixin, UpdateView):
    model = BusyEvent
    form_class = BusyEventForm
    template_name = "planner/form.html"
    success_url = reverse_lazy("planner:busy_list")
    page_title = "Sửa lịch bận"


class BusyDeleteView(SuccessMessageMixin, OwnedObjectMixin, DeleteView):
    model = BusyEvent
    template_name = "planner/confirm_delete.html"
    success_url = reverse_lazy("planner:busy_list")
    success_message = "Đã xóa lịch bận."
    page_title = "Xóa lịch bận"
