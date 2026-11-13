from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import OperationalError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import DeleteView, DetailView, FormView, ListView, TemplateView, UpdateView
from django.http import JsonResponse

from studies.views import OwnedFormMixin, OwnedObjectMixin

from .forms import FinishForm, FocusStartForm, LogNotesForm, LogRangeForm, StudyLogForm, default_range
from .models import FocusSession, StudyLog
from .services import FocusError, active_session, add_manual_log, build_statistics, start_work, timer_action


def timer_state(session):
    elapsed = session.elapsed()
    return {"status": session.status, "status_label": session.get_status_display(),
            "remaining": session.duration_seconds - elapsed, "elapsed": elapsed}


def action_error_message(error):
    if isinstance(error, FocusError):
        return str(error)
    if "locked" in str(error).lower():
        return "Dữ liệu đang được lưu ở một yêu cầu khác. Hãy tải lại trạng thái rồi thử lại."
    raise error


class FocusHomeView(LoginRequiredMixin, FormView):
    template_name = "focus/start.html"
    form_class = FocusStartForm
    page_title = "Tập trung với Pomodoro"

    def get_initial(self):
        return {"task": self.request.GET.get("task")}

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "user": self.request.user}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active"] = active_session(self.request.user)
        context["recent_sessions"] = FocusSession.objects.filter(owner=self.request.user)[:10]
        return context

    def form_valid(self, form):
        try:
            session = start_work(self.request.user, form.cleaned_data["task"].pk, form.cleaned_data["request_key"])
        except (FocusError, OperationalError) as error:
            form.add_error(None, action_error_message(error))
            return self.form_invalid(form)
        return redirect("focus:session", pk=session.pk)


class FocusDetailView(OwnedObjectMixin, DetailView):
    model = FocusSession
    template_name = "focus/session.html"
    context_object_name = "session"
    page_title = "Phiên tập trung của bạn"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["timer_state"] = timer_state(self.object)
        context["remaining_label"] = f"{context['timer_state']['remaining'] // 60:02d}:{context['timer_state']['remaining'] % 60:02d}"
        context.setdefault("finish_form", FinishForm())
        context["study_log"] = StudyLog.objects.filter(owner=self.request.user, focus_session=self.object).first()
        return context


class FocusStateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        session = get_object_or_404(FocusSession, pk=pk, owner=request.user)
        response = JsonResponse(timer_state(session))
        response["Cache-Control"] = "no-store"
        return response


class FocusActionView(FocusDetailView):
    http_method_names = ["post"]

    def post(self, request, pk, action):
        self.object = self.get_object()
        form = FinishForm(request.POST) if action == "finish" else FinishForm()
        if action == "finish" and not form.is_valid():
            return self.render_to_response(self.get_context_data(finish_form=form), status=400)
        try:
            session = timer_action(request.user, pk, action, notes=form.cleaned_data["notes"] if action == "finish" else "")
        except (FocusError, OperationalError) as error:
            return self.render_to_response(self.get_context_data(action_error=action_error_message(error), finish_form=form), status=409)
        if action == "finish":
            messages.success(request, "Đã kết thúc phiên. Phút học đủ một phút trở lên được lưu một lần; phút nghỉ không ghi vào nhật ký.")
        return redirect("focus:session", pk=session.pk)


class LogListView(OwnedObjectMixin, ListView):
    model = StudyLog
    template_name = "focus/log_list.html"
    context_object_name = "logs"
    paginate_by = 20
    page_title = "Nhật ký học tập"

    def get_queryset(self):
        self.range_form = LogRangeForm(self.request.GET or default_range())
        queryset = super().get_queryset()
        if not self.range_form.is_valid():
            return queryset.none()
        return queryset.filter(studied_on__range=(self.range_form.cleaned_data["start"], self.range_form.cleaned_data["end"]))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.copy()
        query.pop("page", None)
        if self.range_form.is_valid():
            for key in ("start", "end"):
                query[key] = self.range_form.cleaned_data[key].isoformat()
        context.update({"range_form": self.range_form, "filter_query": query.urlencode()})
        return context


class LogCreateView(LoginRequiredMixin, FormView):
    form_class = StudyLogForm
    template_name = "focus/log_form.html"
    page_title = "Thêm nhật ký học"
    success_url = reverse_lazy("focus:logs")

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "user": self.request.user}

    def form_valid(self, form):
        try:
            add_manual_log(self.request.user, form.cleaned_data)
        except OperationalError as error:
            form.add_error(None, action_error_message(error))
            return self.form_invalid(form)
        messages.success(self.request, "Đã lưu nhật ký. Thời lượng công việc còn lại giữ nguyên.")
        return redirect(self.success_url)


class LogUpdateView(OwnedFormMixin, UpdateView):
    model = StudyLog
    template_name = "focus/log_form.html"
    success_url = reverse_lazy("focus:logs")
    page_title = "Sửa nhật ký học"

    def get_form_class(self):
        return StudyLogForm if self.object.source == StudyLog.Source.MANUAL else LogNotesForm


class LogDeleteView(OwnedObjectMixin, DeleteView):
    model = StudyLog
    template_name = "focus/log_delete.html"
    success_url = reverse_lazy("focus:logs")
    page_title = "Xóa nhật ký học"


class StatisticsView(LoginRequiredMixin, TemplateView):
    template_name = "focus/statistics.html"
    page_title = "Thống kê thời gian học"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = LogRangeForm(self.request.GET or default_range())
        context["range_form"] = form
        if form.is_valid():
            start, end = form.cleaned_data["start"], form.cleaned_data["end"]
            logs = StudyLog.objects.filter(owner=self.request.user, studied_on__range=(start, end))
            context.update(build_statistics(logs, start, end))
        return context
