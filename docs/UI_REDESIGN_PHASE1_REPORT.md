# Nhịp Học — Báo cáo Pha 1: Nền & điều hướng

Ngày thực hiện: 16/11/2026. Nhánh: `ui-redesign`.

## Kết quả

- Thanh trên có đúng 5 mục: Tổng quan, Lịch học tập, Môn & Việc, Tập trung, Thống kê.
- Active được tính từ tên URL đã resolve. Nhật ký/AI thuộc Thống kê; giờ học/lịch bận/nhắc việc/Google thuộc Cài đặt, được đánh dấu ở avatar; hộp thông báo/email được đánh dấu ở chuông.
- Giữ chuông và nguồn 5 thông báo gần nhất đã có. Avatar có Tài khoản, Cài đặt, Quản trị khi là staff, Đăng xuất bằng POST kèm CSRF.
- Component tab dùng chung cho Biểu đồ / Nhật ký / AI hỗ trợ và Thông báo / Email đã gửi. Trang bắt đầu/phiên tập trung không còn tab trộn với Thống kê.
- Layout Cài đặt có 4 nhóm, dùng cho hồ sơ, đổi mật khẩu, giờ học, danh sách/thêm/sửa/xóa lịch bận, tùy chọn nhắc, Google và chi tiết yêu cầu đồng bộ.
- Trang giới thiệu/đăng nhập/đăng ký dùng layout riêng chỉ có thương hiệu, không có menu.
- GET trang đổi mật khẩu thành công chuyển về Tài khoản, hiển thị thông báo thành công một lần. POST đổi mật khẩu vẫn dùng view Django và success URL cũ.
- Nút 404/500 đổi thành “Về Tổng quan”. Không sửa trang 403 hay Django Admin.

## Đối chiếu kế hoạch với mã thật

| Điểm khác | Cách xử lý ít rủi ro |
| --- | --- |
| Repo chưa có `docs/UI_REDESIGN_PLAN.md` | Chép nguyên bản đính kèm từ Downloads vào đường dẫn được yêu cầu. Đã đọc danh sách tính năng đang có trong `docs/`. |
| `/studies/` mới chỉ là URL đề xuất cho Pha 2 | Môn & Việc dẫn đến `studies:task_list` tại `/studies/tasks/`; giữ toàn bộ URL và trang quản lý riêng. |
| Thống kê/nhật ký nằm trong app focus, AI nằm trong insights; giờ học/lịch bận nằm trong planner | Tính active theo tên URL, không gán active chỉ theo app. Không đổi view nghiệp vụ. |
| Không có URL Cài đặt chung | Avatar “Cài đặt” dẫn tới `planner:preferences`, một trang trong layout Cài đặt. “Tài khoản” dẫn tới `accounts:profile`. Không thêm route. |
| `planner/week.html` kế thừa planner/base, có block `main_class`, `planner_heading`, `planner_content` | Không sửa planner/base, week, study_sidebar, calendar_item, view tuần hoặc CSS của Lịch. Dùng wrapper `planner/settings_base.html` cho các trang cài đặt của planner. |
| insights/base chưa có thanh tab riêng | Thêm component tab chung tại base này, giữ nguyên nội dung các trang AI. |
| Form đăng nhập/đăng ký/đổi mật khẩu dùng chung accounts/form_page | Tách phần form thành partial chung, giữ CSRF, next, lỗi và help text; đổi mật khẩu dùng layout Cài đặt. |
| URL thành công hiện dùng PasswordChangeDoneView và POST đổi mật khẩu đang dẫn tới đó | Chỉ thay GET của view thành công bằng redirect có messages; giữ tên URL, bảo vệ đăng nhập, POST và phiên đăng nhập cũ. |
| Repo có sẵn nhiều thay đổi chưa commit, gồm chuông/avatar và Lịch tuần | Tái sử dụng chuông/avatar đã có. Commit chỉ lấy UI Pha 1 và các phụ thuộc header cần thiết; để ngoài commit các sửa thuật toán, view tuần, thân Lịch, storage, dashboard, tài liệu khác và việc gỡ hướng dẫn/footer. |

## File theo mục đích

### Điều hướng và tab

Tạo:

- `core/templatetags/__init__.py`
- `core/templatetags/navigation.py`
- `templates/components/section_tabs.html`
- `static/css/navigation.css`

Sửa:

- `templates/base.html`
- `templates/focus/base.html`
- `templates/notifications/base.html`
- `templates/insights/base.html`
- `templates/notifications/inbox.html` — link bánh răng tới tùy chọn nhắc.

Tái sử dụng nội dung đã có trước phiên làm việc và đưa các phần phụ thuộc header vào commit:

- `notifications/context_processors.py`, `notifications/test_header.py`, `static/js/header.js`
- Phần CSS header trong `static/css/app.css`.
- Dòng đăng ký context processor header trong `config/settings.py`.
- Anchor thông báo trong `templates/notifications/inbox.html`.

### Cài đặt và tài khoản

Tạo:

- `templates/components/settings_layout.html`
- `templates/planner/settings_base.html`
- `static/css/settings.css`
- `templates/accounts/form_fields.html`

Sửa:

- `templates/accounts/profile.html`, `templates/accounts/password_change.html`
- `templates/planner/form.html`, `templates/planner/confirm_delete.html`, `templates/planner/busyevent_list.html`
- `templates/notifications/preferences.html`
- `templates/integrations/google.html`, `templates/integrations/job.html`
- `accounts/views.py`, `accounts/urls.py` — chỉ GET trang thành công.

### Trang công khai và lỗi

Tạo `templates/components/public_layout.html`.

Sửa `templates/accounts/form_page.html`, `templates/accounts/login.html`, `templates/accounts/register.html`, `templates/core/home.html`, `templates/404.html`, `templates/500.html`.

### Kiểm thử và tài liệu

- Tạo `core/test_navigation.py`: active cho 42 tên URL trang, tab, layout, CSRF, staff, khách, quyền sở hữu và redirect mật khẩu.
- Sửa `accounts/tests.py`, `core/tests.py` theo hành vi UI mới. Trong index, sửa riêng assertion menu của `core/test_dashboard.py`; các thay đổi khác của file này từ trước vẫn để ngoài commit.
- Thêm `docs/UI_REDESIGN_PLAN.md` và báo cáo này.

Không xóa file nào.

## Kiểm tra

- Trước sửa: `manage.py check` qua; toàn bộ 291 test qua.
- Sau sửa: `.venv\Scripts\python.exe manage.py check` — không có lỗi.
- `.venv\Scripts\python.exe manage.py test --noinput` — **300 test qua**.
- Sau bổ sung kiểm tra CSS của layout planner: `manage.py test core.test_navigation accounts --noinput` — **25 test qua**.
- Đã xuất riêng nội dung index vào thư mục kiểm thử, chạy `check` và toàn bộ **284 test qua**. Số lượng khác workspace vì các test có sẵn nhưng chưa commit của chủ dự án được giữ ngoài snapshot Pha 1. Assertion cũ yêu cầu menu công khai được cập nhật riêng theo layout mới, giữ test route hướng dẫn cũ trong snapshot gốc.
- `git diff --check` không có lỗi khoảng trắng.
- Đã mở trên trình duyệt: giới thiệu, đăng ký, đăng nhập; toàn bộ 5 mục thanh trên; cả 3 tab Thống kê; chuông, hộp thông báo, Email đã gửi; Tài khoản, Đổi mật khẩu, Giờ học, Lịch bận, Nhắc việc, Google; các mục avatar Tài khoản/Cài đặt/Quản trị/Đăng xuất.
- Đã xem trực tiếp `/planner/`: thanh công cụ, lưới 7 ngày, sáng/chiều/tối, lịch bận, buổi học và deadline vẫn hiển thị; không có sidebar Cài đặt chèn vào Lịch. Không sửa cấu trúc block của planner/base.
- Rà trình duyệt dùng tài khoản tổng hợp trên bản sao SQLite riêng; không đổi tài khoản hay dữ liệu SQLite gốc, không kết nối Google hoặc gọi AI.

## Tồn đọng / giới hạn

- Không có quyết định bắt buộc còn chờ để hoàn tất Pha 1.
- Chưa làm Pha 2–4: không gộp studies, không thêm redirect studies, drawer/dialog, dashboard mới, stepper, chip Pomodoro hay chuẩn hóa ngày giờ.
- Kiểm tra trực quan thực hiện ở kích thước trình duyệt desktop; chưa nghiệm thu trên điện thoại thật.
- Các thay đổi đã tồn tại trong workspace trước phiên làm việc vẫn được giữ ngoài commit, trừ các phần header cần để commit Pha 1 chạy độc lập đã nêu trên.
