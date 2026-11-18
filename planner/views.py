from datetime import timedelta
from urllib.parse import urlencode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count
from django.core.paginator import Paginator
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, TemplateView, UpdateView

from studies.views import OwnedFormMixin, OwnedObjectMixin
from studies.forms import MaterialForm, SubjectForm, TaskForm
from studies.models import Material, Subject, Task

from .forms import (BusyEventForm, PlanWeekForm, SessionLockForm, SessionMoveForm,
                    SessionRecordForm, StudyPreferenceForm, WeekForm)
from .models import BusyEvent, StudyPlan, StudyPreference, StudySession
from .services.alerts import build_alerts
from .services.availability import build_week, get_preferences
from .services.scheduling import PlanError, apply_plan, create_draft
from .services.sessions import move_session, record_session, set_session_lock


class WeekView(LoginRequiredMixin, TemplateView):
    template_name = "planner/week.html"
    page_title = "Lịch tuần của bạn"
    panels = {
        "tasks": (Task, TaskForm, "công việc"),
        "subjects": (Subject, SubjectForm, "môn học"),
        "materials": (Material, MaterialForm, "tài liệu"),
    }

    def sidebar_object(self, model, pk):
        if not pk.isdecimal() or len(pk) > 18:
            raise Http404
        return get_object_or_404(model, owner=self.request.user, pk=int(pk))

    def sidebar_url(self, week, panel):
        return reverse("planner:week") + "?" + urlencode({"week": week.isoformat(), "panel": panel})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = WeekForm({"week": self.request.GET.get("week", timezone.localdate().isoformat())})
        context["week_form"] = form
        panel = self.request.GET.get("panel", "tasks")
        if panel not in self.panels:
            raise Http404
        model, form_class, label = self.panels[panel]
        mode = kwargs.get("sidebar_mode", self.request.GET.get("action", ""))
        if mode not in ("", "new", "edit", "delete"):
            raise Http404
        obj = kwargs.get("sidebar_object")
        if obj is None and mode in ("edit", "delete"):
            obj = self.sidebar_object(model, self.request.GET.get("id", ""))
        sidebar_form = kwargs.get("sidebar_form")
        if sidebar_form is None and mode in ("new", "edit"):
            sidebar_form = form_class(user=self.request.user, instance=obj)
        query = self.request.GET.get("q", "").strip()[:200]
        objects = model.objects.filter(owner=self.request.user)
        if panel == "materials":
            objects = objects.defer("file_data")
        if panel != "subjects":
            objects = objects.select_related("subject")
        if query:
            objects = objects.filter(**{("name" if panel == "subjects" else "title") + "__icontains": query})
        page = Paginator(objects, 8).get_page(self.request.GET.get("page"))
        context.update({"sidebar_panel": panel, "sidebar_label": label, "sidebar_mode": mode,
                        "sidebar_form": sidebar_form, "sidebar_object": obj,
                        "sidebar_page": page, "sidebar_query": query})
        if form.is_valid():
            monday = form.cleaned_data["week"]
            preferences = get_preferences(self.request.user)
            context.update({
                "week_start": monday, "week_end": monday + timedelta(days=6),
                "previous_week": (monday - timedelta(days=7)).isoformat(),
                "next_week": (monday + timedelta(days=7)).isoformat(),
                "preferences": preferences,
                "days": build_week(self.request.user, monday, preferences),
                "sidebar_url": self.sidebar_url(monday, panel),
            })
        return context

    def post(self, request, *args, **kwargs):
        week_form = WeekForm({"week": request.GET.get("week", timezone.localdate().isoformat())})
        panel = request.GET.get("panel", "tasks")
        if panel not in self.panels or not week_form.is_valid():
            return HttpResponseBadRequest("Tuần hoặc mục học tập không hợp lệ.")
        model, form_class, label = self.panels[panel]
        pk = request.POST.get("object_id", "")
        obj = self.sidebar_object(model, pk) if pk else None
        operation = request.POST.get("operation")
        if operation == "delete" and obj is not None:
            obj.delete()
            messages.success(request, f"Đã xóa {label}.")
        elif operation == "save":
            form = form_class(request.POST, request.FILES, user=request.user, instance=obj)
            if not form.is_valid():
                return self.render_to_response(self.get_context_data(
                    sidebar_mode="edit" if obj else "new", sidebar_object=obj, sidebar_form=form,
                ))
            form.save()
            messages.success(request, f"Đã lưu {label}.")
        else:
            return HttpResponseBadRequest("Thao tác không hợp lệ.")
        return redirect(self.sidebar_url(week_form.cleaned_data["week"], panel) + "#hoc-tap")


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
        return {"week": self.request.GET.get("week", timezone.localdate().isoformat()), "mode": StudyPlan.Mode.ADD}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recent_plans"] = StudyPlan.objects.filter(owner=self.request.user).annotate(
            session_count=Count("sessions"),
        ).order_by("-created_at", "-pk")[:10]
        return context

    def form_valid(self, form):
        plan = create_draft(self.request.user, form.cleaned_data["week"], mode=form.cleaned_data["mode"])
        return redirect("planner:plan_detail", pk=plan.pk)


class PlanDetailView(OwnedObjectMixin, DetailView):
    model = StudyPlan
    context_object_name = "plan"
    template_name = "planner/plan_detail.html"
    page_title = "Kế hoạch tuần"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sessions"] = list(self.object.sessions.select_related("task", "task__subject"))
        active = [s for s in context["sessions"] if s.status != StudySession.Status.CANCELLED]
        context["active_count"] = len(active)
        context["scheduled_minutes"] = sum(s.duration_minutes for s in active)
        context["replacement_sessions"] = StudySession.objects.filter(
            owner=self.request.user, pk__in=self.object.replacement_ids,
        ).select_related("task")
        context["can_apply"] = not self.object.applied_at and bool(active or self.object.replacement_ids)
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


class SessionFormView(LoginRequiredMixin, FormView):
    template_name = "planner/session_form.html"

    def get_initial(self):
        self.session = get_object_or_404(
            StudySession.objects.select_related("task", "plan"),
            owner=self.request.user, pk=self.kwargs["pk"], plan__applied_at__isnull=False,
        )
        return {"starts_at": self.session.starts_at, "ends_at": self.session.ends_at,
                "remaining_minutes": self.session.task.remaining_minutes}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["session"] = self.session
        return context

    def get_success_url(self):
        return reverse("planner:plan_detail", args=[self.session.plan_id])

    def form_valid(self, form):
        try:
            self.perform_action(form.cleaned_data)
        except PlanError as error:
            form.add_error(None, str(error))
            return self.form_invalid(form)
        messages.success(self.request, "Đã cập nhật buổi học.")
        return redirect(self.get_success_url())


class SessionMoveView(SessionFormView):
    form_class = SessionMoveForm
    page_title = "Chỉnh giờ buổi học"

    def perform_action(self, data):
        move_session(self.request.user, self.session.pk, data["starts_at"], data["ends_at"])


class SessionRecordView(SessionFormView):
    form_class = SessionRecordForm
    page_title = "Ghi nhận buổi học"

    def perform_action(self, data):
        record_session(self.request.user, self.session.pk, data["result"], data["remaining_minutes"])


class SessionLockView(SessionFormView):
    form_class = SessionLockForm
    page_title = "Khóa hoặc mở khóa buổi học"
    http_method_names = ["post"]

    def perform_action(self, data):
        set_session_lock(self.request.user, self.session.pk, data["locked"])


class AlertView(LoginRequiredMixin, TemplateView):
    template_name = "planner/alerts.html"
    page_title = "Cảnh báo và việc cần rà soát"

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), **build_alerts(self.request.user)}
