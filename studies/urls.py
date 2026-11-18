from django.urls import path

from . import views

app_name = "studies"
urlpatterns = [
    path("subjects/", views.SubjectListView.as_view(), name="subject_list"),
    path("subjects/add/", views.SubjectCreateView.as_view(), name="subject_create"),
    path("subjects/<int:pk>/edit/", views.SubjectUpdateView.as_view(), name="subject_update"),
    path("subjects/<int:pk>/delete/", views.SubjectDeleteView.as_view(), name="subject_delete"),
    path("tasks/", views.TaskListView.as_view(), name="task_list"),
    path("tasks/add/", views.TaskCreateView.as_view(), name="task_create"),
    path("tasks/<int:pk>/edit/", views.TaskUpdateView.as_view(), name="task_update"),
    path("tasks/<int:pk>/progress/", views.TaskProgressView.as_view(), name="task_progress"),
    path("tasks/<int:pk>/delete/", views.TaskDeleteView.as_view(), name="task_delete"),
    path("materials/", views.MaterialListView.as_view(), name="material_list"),
    path("materials/add/", views.MaterialCreateView.as_view(), name="material_create"),
    path("materials/<int:pk>/edit/", views.MaterialUpdateView.as_view(), name="material_update"),
    path("materials/<int:pk>/delete/", views.MaterialDeleteView.as_view(), name="material_delete"),
    path("materials/<int:pk>/download/", views.MaterialDownloadView.as_view(), name="material_download"),
]
