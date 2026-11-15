from django.urls import path

from . import views

app_name = "core"
urlpatterns = [
    path("", views.home, name="home"),
    path("huong-dan/", views.guide, name="guide"),
    path("health/", views.health, name="health"),
]
