from django.shortcuts import render
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.http import require_safe


def home(request):
    return render(request, "core/home.html")


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
