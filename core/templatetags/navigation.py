from django import template
from django.conf import settings

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
PLANNER_TABS = (
    {"key": "week", "url": "planner:week", "label": "Lịch tuần"},
    {"key": "plans", "url": "planner:plan_generate", "label": "Tạo kế hoạch"},
    {"key": "alerts", "url": "planner:alerts", "label": "Cảnh báo"},
    {"key": "busy", "url": "planner:busy_list", "label": "Lịch bận"},
    {"key": "preferences", "url": "planner:preferences", "label": "Giờ học"},
)
SETTINGS_TABS = (
    {"key": "account", "url": "accounts:profile", "label": "Tài khoản"},
    {"key": "reminders", "url": "notifications:preferences", "label": "Nhắc việc"},
    {"key": "google", "url": "integrations:google", "label": "Kết nối Google"},
)
STUDIES_TABS = (
    {"key": "tasks", "url": "studies:task_list", "label": "Công việc"},
    {"key": "subjects", "url": "studies:subject_list", "label": "Môn học"},
    {"key": "materials", "url": "studies:material_list", "label": "Tài liệu"},
)
SETTINGS_ROUTES = {
    "accounts:profile": "account",
    "accounts:password_change": "account",
    "accounts:password_change_done": "account",
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
        "planner:preferences", "planner:busy_list", "planner:busy_create",
        "planner:busy_update", "planner:busy_delete",
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
PAGE_TITLES = {
    "accounts:profile": "Tài khoản", "accounts:password_change": "Đổi mật khẩu",
    "accounts:login": "Chào mừng bạn trở lại", "accounts:register": "Bắt đầu với Nhịp Học",
    "integrations:google": "Google Calendar", "integrations:job": "Yêu cầu đồng bộ",
    "insights:home": "Hiểu nhịp học của bạn", "insights:report": "Kết quả phân tích",
}
PAGE_DESCRIPTIONS = {
    "accounts:profile": "Xem thông tin tài khoản và quản lý mật khẩu của bạn.",
    "accounts:password_change": "Nhập mật khẩu hiện tại và chọn mật khẩu mới cho tài khoản.",
    "accounts:login": "Đăng nhập bằng tên tài khoản và mật khẩu của bạn.",
    "accounts:register": "Tạo tài khoản để có không gian học tập riêng; điền đầy đủ các trường bên dưới.",
    "planner:plan_generate": "Chọn tuần và cách xếp lịch để tạo bản xem trước.",
    "planner:plan_detail": "Xem các buổi học đề xuất và kiểm tra trước khi áp dụng.",
    "planner:alerts": "Rà soát deadline, xung đột và các buổi học chưa ghi nhận.",
    "planner:preferences": "Chọn ngày, khung giờ và thời lượng học phù hợp với bạn.",
    "planner:busy_list": "Quản lý lịch lên lớp, ca làm và hoạt động cá nhân.",
    "planner:busy_create": "Thêm khoảng thời gian bạn không thể dành cho việc học.",
    "planner:busy_update": "Cập nhật thời gian và quy tắc lặp của lịch bận.",
    "planner:busy_delete": "Kiểm tra lịch bận trước khi xác nhận xóa.",
    "planner:session_move": "Điều chỉnh giờ và thời lượng của buổi học.",
    "planner:session_record": "Ghi nhận kết quả buổi học và thời lượng còn cần.",
    "studies:task_list": "Ghi việc cần làm, theo dõi hạn nộp và thời gian còn lại.",
    "studies:subject_list": "Tổ chức các môn đang học và lưu trữ môn cũ.",
    "studies:material_list": "Lưu liên kết bài giảng và tài liệu theo môn hoặc công việc.",
    "focus:home": "Học 25 phút rồi nghỉ 5 phút; bạn có thể tạm dừng hoặc kết thúc sớm.",
    "focus:session": "Theo dõi thời gian và lưu kết quả phiên tập trung của bạn.",
    "focus:logs": "Xem thời gian học từ phiên tập trung và nhật ký nhập tay.",
    "focus:statistics": "Theo dõi thời gian học và phân bổ theo môn trong khoảng ngày đã chọn.",
    "notifications:inbox": "Theo dõi thông báo về deadline và các buổi học của bạn.",
    "notifications:email_history": "Xem lịch sử và trạng thái các email nhắc việc.",
    "notifications:preferences": "Chọn cách nhận nhắc việc và thời điểm phù hợp với bạn.",
    "integrations:google": "Đưa buổi học sang lịch Google riêng mang tên Nhịp Học.",
    "integrations:job": "Theo dõi kết quả yêu cầu đồng bộ lịch học của bạn.",
    "insights:home": "Đọc số liệu thực tế, nhận gợi ý và quyết định bước tiếp theo.",
    "insights:report": "Đối chiếu nhận xét AI với dữ liệu học tập của bạn.",
}
PAGE_ACTIONS = {
    "studies:task_list": {"url": "studies:task_create", "label": "Thêm công việc"},
    "studies:subject_list": {"url": "studies:subject_create", "label": "Thêm môn học"},
    "studies:material_list": {"url": "studies:material_create", "label": "Thêm tài liệu"},
    "planner:busy_list": {"url": "planner:busy_create", "label": "Thêm lịch bận"},
    "focus:logs": {"url": "focus:log_create", "label": "Thêm nhật ký"},
}
# A rejected AI request renders the home template at the existing POST URL.
PAGE_TITLES["insights:generate"] = PAGE_TITLES["insights:home"]
PAGE_DESCRIPTIONS["insights:generate"] = PAGE_DESCRIPTIONS["insights:home"]


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
    elif section == "planner":
        tabs = PLANNER_TABS
        if name in ("planner:plan_generate", "planner:plan_detail", "planner:plan_apply"):
            current_tab = "plans"
        elif name in ("planner:busy_list", "planner:busy_create", "planner:busy_update", "planner:busy_delete"):
            current_tab = "busy"
        else:
            current_tab = {"planner:preferences": "preferences", "planner:alerts": "alerts"}.get(name, "week")
    elif section == "settings":
        tabs, current_tab = SETTINGS_TABS, settings_item
    elif section == "studies":
        tabs = STUDIES_TABS
        current_tab = next(tab["key"] for tab in tabs if name.split(":")[1].startswith(tab["key"][:-1]))
    return {
        "main_tabs": MAIN_TABS, "section": section, "settings_item": settings_item,
        "tabs": tabs, "current_tab": current_tab,
        "tabs_label": {"statistics": "Thống kê", "notifications": "Thông báo", "planner": "Quản lý lịch",
                       "settings": "Cài đặt", "studies": "Nội dung học tập"}.get(section, ""),
        "title": PAGE_TITLES.get(name, ""),
        "description": PAGE_DESCRIPTIONS.get(name, "Xem và cập nhật thông tin học tập của bạn."),
        "action": PAGE_ACTIONS.get(name),
        "show_technical_details": settings.DEBUG or bool(getattr(getattr(request, "user", None), "is_staff", False)),
        "email_available": not any(backend in settings.EMAIL_BACKEND for backend in (
            ".console.", ".locmem.", ".filebased.", ".dummy.",
        )),
    }
