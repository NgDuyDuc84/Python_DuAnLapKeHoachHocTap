from django.urls import path

from . import views

app_name = "integrations"
urlpatterns = [
    path("google/", views.home, name="google"),
    path("google/connect/", views.connect, name="connect"),
    path("google/callback/", views.callback, name="callback"),
    path("google/disconnect/", views.disconnect, name="disconnect"),
    path("google/sync/", views.sync, name="sync"),
    path("google/reset/", views.reset_calendar, name="reset"),
    path("google/jobs/<int:pk>/", views.job_detail, name="job"),
]
