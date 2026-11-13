from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, TemplateView, UpdateView

from studies.views import OwnedFormMixin, OwnedObjectMixin

from .forms import BusyEventForm, PlanWeekForm, StudyPreferenceForm, WeekForm
from .models import BusyEvent, StudyPlan, StudyPreference
from .services.availability import build_week, get_preferences
from .services.scheduling import PlanError, apply_plan, create_draft


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


class PlanGenerateView(LoginRequiredMixin, FormView):
    form_class = PlanWeekForm
    template_name = "planner/plan_form.html"
    page_title = "Tạo kế hoạch tuần"

    def get_initial(self):
        return {"week": self.request.GET.get("week", timezone.localdate().isoformat())}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recent_plans"] = StudyPlan.objects.filter(owner=self.request.user).annotate(
            session_count=Count("sessions"),
        ).order_by("-created_at", "-pk")[:10]
        return context

    def form_valid(self, form):
        plan = create_draft(self.request.user, form.cleaned_data["week"])
        return redirect("planner:plan_detail", pk=plan.pk)


class PlanDetailView(OwnedObjectMixin, DetailView):
    model = StudyPlan
    context_object_name = "plan"
    template_name = "planner/plan_detail.html"
    page_title = "Kế hoạch tuần"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sessions"] = list(self.object.sessions.select_related("task", "task__subject"))
        context["scheduled_minutes"] = sum(s.duration_minutes for s in context["sessions"])
        context["unallocated_minutes"] = sum(row["unallocated_minutes"] for row in self.object.report)
        return context


class PlanApplyView(PlanDetailView):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            plan, applied = apply_plan(request.user, self.object.pk)
        except PlanError as error:
            return self.render_to_response(self.get_context_data(apply_error=str(error)), status=409)
        messages.success(request, "Đã áp dụng kế hoạch vào lịch tuần." if applied else "Kế hoạch này đã được áp dụng trước đó.")
        return redirect(f"{reverse('planner:week')}?week={plan.week_start.isoformat()}")
