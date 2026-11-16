from django import template

register = template.Library()

MAIN_TABS = (
    {"key": "overview", "url": "core:home", "label": "Tổng quan"},
    {"key": "planner", "url": "planner:week", "label": "Lịch học tập"},
    {"key": "studies", "url": "studies:task_list", "label": "Môn & Việc"},
    {"key": "focus", "url": "focus:home", "label": "Tập trung"},
    {"key": "statistics", "url": "focus:statistics", "label": "Thống kê"},
)
STATISTICS_TABS = (
    {"key": "charts", "url": "focus:statistics", "label": "Biểu đồ"},
    {"key": "logs", "url": "focus:logs", "label": "Nhật ký"},
    {"key": "ai", "url": "insights:home", "label": "AI hỗ trợ"},
)
NOTIFICATION_TABS = (
    {"key": "inbox", "url": "notifications:inbox", "label": "Thông báo"},
    {"key": "email", "url": "notifications:email_history", "label": "Email đã gửi"},
)
SETTINGS_ROUTES = {
    "accounts:profile": "account",
    "accounts:password_change": "account",
    "accounts:password_change_done": "account",
    "planner:preferences": "time",
    "planner:busy_list": "busy",
    "planner:busy_create": "busy",
    "planner:busy_update": "busy",
    "planner:busy_delete": "busy",
    "notifications:preferences": "reminders",
    "integrations:google": "google",
    "integrations:connect": "google",
    "integrations:callback": "google",
    "integrations:disconnect": "google",
    "integrations:sync": "google",
    "integrations:reset": "google",
    "integrations:job": "google",
}
STATISTICS_ROUTES = {
    "focus:statistics": "charts",
    "focus:logs": "logs",
    "focus:log_create": "logs",
    "focus:log_update": "logs",
    "focus:log_delete": "logs",
    "insights:home": "ai",
    "insights:report": "ai",
    "insights:generate": "ai",
}
SECTION_ROUTES = {
    "overview": ("core:home",),
    "planner": (
        "planner:week", "planner:plan_generate", "planner:plan_detail", "planner:plan_apply",
        "planner:session_move", "planner:session_record", "planner:session_lock", "planner:alerts",
    ),
    "studies": tuple(f"studies:{name}" for name in (
        "subject_list", "subject_create", "subject_update", "subject_delete",
        "task_list", "task_create", "task_update", "task_delete", "task_progress",
        "material_list", "material_create", "material_update", "material_delete",
    )),
    "focus": tuple(f"focus:{name}" for name in (
        "home", "session", "state", "pause", "resume", "finish", "cancel", "break",
    )),
    "statistics": STATISTICS_ROUTES,
    "notifications": (
        "notifications:inbox", "notifications:email_history", "notifications:read",
        "notifications:read_all", "notifications:retry_email",
    ),
    "settings": SETTINGS_ROUTES,
}


@register.simple_tag
def navigation_state(request):
    """Resolve presentation state from URL names without querying user data."""
    match = getattr(request, "resolver_match", None)
    name = match.view_name if match else ""
    section = next((key for key, names in SECTION_ROUTES.items() if name in names), "")
    tabs, current_tab = (), ""
    settings_item = SETTINGS_ROUTES.get(name, "")
    if section == "statistics":
        tabs, current_tab = STATISTICS_TABS, STATISTICS_ROUTES[name]
    elif section == "notifications":
        tabs = NOTIFICATION_TABS
        current_tab = "email" if name in ("notifications:email_history", "notifications:retry_email") else "inbox"
    return {
        "main_tabs": MAIN_TABS, "section": section, "settings_item": settings_item,
        "tabs": tabs, "current_tab": current_tab,
        "tabs_label": "Thống kê" if section == "statistics" else "Thông báo",
    }
