from django.urls import path

from . import views

app_name = "notifications"
urlpatterns = [
    path("", views.InboxView.as_view(), name="inbox"),
    path("email/", views.EmailHistoryView.as_view(), name="email_history"),
    path("preferences/", views.PreferenceView.as_view(), name="preferences"),
    path("read-all/", views.ReadAllView.as_view(), name="read_all"),
    path("<int:pk>/read/", views.ReadView.as_view(), name="read"),
    path("<int:pk>/retry-email/", views.RetryEmailView.as_view(), name="retry_email"),
]
