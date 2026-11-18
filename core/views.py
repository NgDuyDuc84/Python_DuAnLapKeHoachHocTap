from django.shortcuts import render
from django.contrib.auth.forms import AuthenticationForm
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.http import require_safe

from .dashboard import build_dashboard


def home(request):
    if request.user.is_authenticated:
        response = render(request, "core/dashboard.html", build_dashboard(request.user))
        response["Cache-Control"] = "no-store"
        return response
    return render(request, "accounts/login.html", {"form": AuthenticationForm(request)})


@require_safe
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        response = JsonResponse({"status": "ok"})
    except DatabaseError:
        response = JsonResponse({"status": "unavailable"}, status=503)
    response["Cache-Control"] = "no-store"
    return response


def csrf_failure(request, reason=""):
    return render(request, "403.html", status=403)
