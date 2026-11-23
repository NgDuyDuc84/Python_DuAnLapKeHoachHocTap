from django.utils import timezone

from studies.models import Task

from .models import Reminder


def header_notifications(request):
    if not request.user.is_authenticated:
        return {}
    reminders = Reminder.objects.filter(
        owner=request.user, channel=Reminder.Channel.IN_APP, status=Reminder.Status.SENT,
    )
    return {
        "shell_overdue_count": lambda: Task.objects.filter(owner=request.user, deadline__lt=timezone.now()).exclude(
            status=Task.Status.DONE,
        ).count(),
        "header_unread_count": reminders.filter(read_at__isnull=True).count(),
        "header_reminders": reminders[:5],
    }
