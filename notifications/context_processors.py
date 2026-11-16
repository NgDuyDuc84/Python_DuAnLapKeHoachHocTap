from .models import Reminder


def header_notifications(request):
    if not request.user.is_authenticated:
        return {}
    reminders = Reminder.objects.filter(
        owner=request.user, channel=Reminder.Channel.IN_APP, status=Reminder.Status.SENT,
    )
    return {
        "header_unread_count": reminders.filter(read_at__isnull=True).count(),
        "header_reminders": reminders[:5],
    }
