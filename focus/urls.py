from django.urls import path

from . import views

app_name = "focus"
urlpatterns = [
    path("", views.FocusHomeView.as_view(), name="home"),
    path("sessions/<int:pk>/", views.FocusDetailView.as_view(), name="session"),
    path("sessions/<int:pk>/state/", views.FocusStateView.as_view(), name="state"),
    *[path(f"sessions/<int:pk>/{action}/", views.FocusActionView.as_view(), {"action": action}, name=action)
      for action in ("pause", "resume", "finish", "cancel", "break")],
    path("logs/", views.LogListView.as_view(), name="logs"),
    path("logs/add/", views.LogCreateView.as_view(), name="log_create"),
    path("logs/<int:pk>/edit/", views.LogUpdateView.as_view(), name="log_update"),
    path("logs/<int:pk>/delete/", views.LogDeleteView.as_view(), name="log_delete"),
    path("statistics/", views.StatisticsView.as_view(), name="statistics"),
]
