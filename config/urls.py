from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("studies/", include("studies.urls")),
    path("planner/", include("planner.urls")),
    path("focus/", include("focus.urls")),
    path("notifications/", include("notifications.urls")),
    path("integrations/", include("integrations.urls")),
    path("", include("core.urls")),
]
