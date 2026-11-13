from django.urls import path

from . import views

app_name = "planner"
urlpatterns = [
    path("", views.WeekView.as_view(), name="week"),
    path("preferences/", views.PreferenceView.as_view(), name="preferences"),
    path("alerts/", views.AlertView.as_view(), name="alerts"),
    path("sessions/<int:pk>/edit/", views.SessionMoveView.as_view(), name="session_move"),
    path("sessions/<int:pk>/record/", views.SessionRecordView.as_view(), name="session_record"),
    path("sessions/<int:pk>/lock/", views.SessionLockView.as_view(), name="session_lock"),
    path("plans/new/", views.PlanGenerateView.as_view(), name="plan_generate"),
    path("plans/<int:pk>/", views.PlanDetailView.as_view(), name="plan_detail"),
    path("plans/<int:pk>/apply/", views.PlanApplyView.as_view(), name="plan_apply"),
    path("busy/", views.BusyListView.as_view(), name="busy_list"),
    path("busy/add/", views.BusyCreateView.as_view(), name="busy_create"),
    path("busy/<int:pk>/edit/", views.BusyUpdateView.as_view(), name="busy_update"),
    path("busy/<int:pk>/delete/", views.BusyDeleteView.as_view(), name="busy_delete"),
]
