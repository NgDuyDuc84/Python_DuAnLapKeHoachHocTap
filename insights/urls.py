from django.urls import path

from . import views

app_name = "insights"
urlpatterns = [
    path("", views.home, name="home"),
    path("generate/", views.generate, name="generate"),
    path("reports/<int:pk>/", views.report_detail, name="report"),
]
