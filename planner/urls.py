from django.urls import path

from . import views

app_name = "planner"
urlpatterns = [
    path("", views.WeekView.as_view(), name="week"),
    path("preferences/", views.PreferenceView.as_view(), name="preferences"),
    path("busy/", views.BusyListView.as_view(), name="busy_list"),
    path("busy/add/", views.BusyCreateView.as_view(), name="busy_create"),
    path("busy/<int:pk>/edit/", views.BusyUpdateView.as_view(), name="busy_update"),
    path("busy/<int:pk>/delete/", views.BusyDeleteView.as_view(), name="busy_delete"),
]
