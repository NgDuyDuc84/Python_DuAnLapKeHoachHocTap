# Báo cáo sửa điều hướng sau Pha 1

Các quyết định mới của chủ dự án ghi đè kế hoạch cũ; không triển khai Pha 2. Nhánh làm việc: `ui-redesign`.

## Kết quả

- Lịch bận/Giờ học thuộc Lịch học tập. Tất cả trang phụ của Lịch dùng cùng 5 tab theo thứ tự Lịch tuần | Tạo kế hoạch | Cảnh báo | Lịch bận | Giờ học. Trang chi tiết kế hoạch active Tạo kế hoạch; chỉnh giờ/ghi nhận buổi active Lịch tuần; toàn bộ các trang này active Lịch học tập trên thanh trên.
- Lịch tuần không có thanh tab phụ mới. Giữ nguyên block planner_heading/planner_content và thêm điều kiện bỏ header/tab cho URL week ngay tại base để giữ đúng hợp đồng này.
- Cài đặt chỉ gồm 3 tab pill Tài khoản | Nhắc việc | Kết nối Google. Link Cài đặt trong avatar về Tài khoản. Đổi mật khẩu và chi tiết đồng bộ giữ tab cha tương ứng.
- Link Điều chỉnh giờ học đã trỏ đúng URL hiện có nên giữ nguyên đích; đổi chữ link ở Cảnh báo thành Cài đặt nhắc việc.
- Trang Tài khoản bỏ nút vào không gian học tập; chỉ staff thấy Vai trò.
- Tạo page_header dùng chung: tiêu đề, một dòng mô tả và tối đa một link chính bên phải. Bỏ các eyebrow trên các trang có thể sửa, thống nhất header Cài đặt ngoài thẻ nội dung. Không đổi bố cục dữ liệu Tổng quan hay gộp các trang studies.
- Google chưa cấu hình có nút kết nối bị vô hiệu và lời giải thích thân thiện. Thông tin cấu hình Google, backend email và dịch vụ nền chỉ hiện cho staff hoặc DEBUG; áp dụng tương tự cho dòng cấu hình AI có sẵn.
- Các backend console/locmem/filebased/dummy không gửi tới hộp thư được nhận diện chỉ để trình bày UI. Checkbox email nằm trong fieldset disabled, có chú thích; hidden input giữ giá trị bật đã lưu khi người dùng lưu các tùy chọn còn lại. Không đổi form validation hay xử lý POST.
- Môn & Việc có thứ tự Công việc | Môn học | Tài liệu, link chính mặc định về Công việc. Xác nhận số 7 là Subject.semester; hiển thị Học kỳ 7 và tránh lặp nhãn khi dữ liệu đã bắt đầu bằng Học kỳ.
- Tập trung dùng nhãn rỗng Chọn công việc…; queryset và kiểm tra chủ sở hữu không đổi. Mô tả đầu trang còn một câu.
- Tạo kế hoạch đặt form trước giải thích; phần giải thích gập trong details. Mô tả chế độ nằm ngay dưới select, có nội dung ban đầu từ server và cập nhật bằng JS thuần khi đổi lựa chọn. Cùng partial cung cấp nội dung cho mô tả và khối giải thích. Cảnh báo cũng gập phần giải thích.

## Điểm kế hoạch / mã thật không khớp và cách xử lý

| Điểm lệch | Xử lý |
| --- | --- |
| Kế hoạch và Pha 1 đưa Lịch bận/Giờ học vào Cài đặt; planner/base vẫn có link tới chúng | Cập nhật các mục 2, 3, 4.4, 8.2; chuyển template về planner/base, sửa bảng active theo tên URL. |
| Cài đặt có sidebar 4 nhóm và avatar dẫn tới Giờ học | Thay bằng component section_tabs gồm đúng 3 mục; avatar dẫn tới accounts:profile, không tạo URL mới. |
| Lịch tuần đã ghi đè planner_heading, còn các trang Lịch bận đang qua planner/settings_base | Giữ block tương thích; bỏ wrapper settings_base đã hết nơi dùng. Không sửa template hoặc view Lịch tuần. |
| Cảnh báo không có bộ đếm rẻ dùng chung cho mọi trang | Không thêm badge. build_alerts tải và phân tích nhiều dữ liệu; không gọi thêm service ở header hay context processor. |
| Link Điều chỉnh giờ học đã đúng | Chỉ giữ đích planner:preferences và kiểm thử liên kết; không đổi URL/view. |
| Email chỉ có mô tả backend, không có kiểm tra kết nối SMTP thật | Dùng cùng phân loại backend kiểm thử đã thấy trong email_mode để khóa UI khi biết chắc không gửi ra hộp thư; không suy đoán SMTP hoặc gọi mạng. |
| Học kỳ là chuỗi, có dữ liệu đã kèm nhãn | Thêm nhãn khi còn thiếu, không đổi dữ liệu/model. |
| Không có /studies/ và endpoint mặc định riêng | Giữ Môn & Việc dẫn tới studies:task_list; chỉ đổi thứ tự tab, không làm redirect/gộp trang của Pha 2. |

## Kiểm tra

- `.venv\Scripts\python.exe manage.py check`: không có vấn đề.
- `.venv\Scripts\python.exe manage.py test --noinput`: **309 test qua**.
- Bộ test điều hướng/UI sau rà cuối: **18 test qua**, gồm đủ 10 loại trang phụ của Lịch, 3 tab Cài đặt, active, quyền hiển thị kỹ thuật, checkbox email, học kỳ, nhãn lựa chọn và form giải thích.
- Snapshot riêng của commit: `check` và **293 test qua**; khác số lượng workspace vì các test chưa commit có sẵn của chủ dự án được để ngoài snapshot.
- Kiểm tra thêm nhánh từ chối yêu cầu AI: vẫn có tiêu đề trong header khi home được render ở URL POST generate; giữ nguyên xử lý và mã 400.
- `git diff --check`: không lỗi khoảng trắng.
- Đối chiếu checksum **40 file được bảo vệ** (model, migration, URL, view và 3 template Lịch tuần) với snapshot đầu lượt sửa: không đổi, kể cả các thay đổi chưa commit đã tồn tại trước đó.
- So sánh HTML trong main của Lịch tuần trước/sau với cùng dữ liệu và thời điểm, chuẩn hóa riêng CSRF: khớp hoàn toàn ở 4 trạng thái mặc định, panel=tasks, panel=subjects&action=new, panel=materials.
- Rà trình duyệt trên bản sao SQLite riêng: Lịch tuần; Tạo kế hoạch → Điều chỉnh giờ học → Lịch bận → Cảnh báo → Cài đặt nhắc việc; Tài khoản; Tập trung; Môn & Việc. Đã đổi Bổ sung sang Xếp lại và thấy mô tả cập nhật ngay, phần giải thích mặc định gập. Không tạo kế hoạch, gọi Google/AI hoặc sửa dữ liệu gốc trong lượt rà này.

## File thay đổi trong lượt này

Danh sách dưới đây so với snapshot đầu lượt sửa, không gộp các sửa có sẵn của chủ dự án.

### Khu Lịch học tập

- Sửa: `templates/planner/alerts.html`
- Sửa: `templates/planner/base.html`
- Sửa: `templates/planner/busyevent_list.html`
- Sửa: `templates/planner/confirm_delete.html`
- Sửa: `templates/planner/form.html`
- Sửa: `templates/planner/plan_form.html`
- Xóa: `templates/planner/settings_base.html`

### Cài đặt và tài khoản

- Sửa: `templates/accounts/form_page.html`
- Sửa: `templates/accounts/login.html`
- Sửa: `templates/accounts/password_change.html`
- Sửa: `templates/accounts/password_change_done.html`
- Sửa: `templates/accounts/profile.html`
- Sửa: `templates/accounts/register.html`
- Sửa: `templates/components/settings_layout.html`
- Sửa: `static/css/settings.css`

### Thông báo, Google và AI

- Sửa: `templates/insights/home.html`
- Sửa: `templates/insights/report.html`
- Sửa: `templates/integrations/google.html`
- Sửa: `templates/integrations/job.html`
- Sửa: `templates/notifications/base.html`
- Sửa: `templates/notifications/email_history.html`
- Sửa: `templates/notifications/inbox.html`
- Sửa: `templates/notifications/preferences.html`

### Môn & Việc và Tập trung

- Sửa: `templates/focus/base.html`
- Sửa: `templates/focus/log_list.html`
- Sửa: `templates/focus/session.html`
- Sửa: `templates/focus/start.html`
- Sửa: `templates/studies/base.html`
- Sửa: `templates/studies/material_list.html`
- Sửa: `templates/studies/subject_list.html`
- Sửa: `templates/studies/task_list.html`
- Sửa: `focus/forms.py`

### Thành phần chung và header

- Sửa: `templates/403.html`
- Sửa: `templates/404.html`
- Sửa: `templates/500.html`
- Sửa: `templates/base.html`
- Sửa: `templates/core/dashboard.html`
- Sửa: `templates/core/home.html`
- Sửa: `static/css/navigation.css`
- Sửa: `core/templatetags/navigation.py`
- Tạo: `templates/components/page_header.html`
- Tạo: `templates/components/plan_mode_description.html`
- Tạo: `static/js/plan_form.js`

### Kiểm thử và tài liệu

- Sửa: `core/test_navigation.py`
- Sửa: `notifications/tests.py`
- Sửa: `insights/tests.py`
- Sửa: `integrations/tests.py`
- Sửa: `docs/UI_REDESIGN_PLAN.md`
- Tạo: `core/test_ui_cleanup.py`

- Tạo: `docs/UI_NAVIGATION_FIX_REPORT.md` — báo cáo này.

## Giới hạn / tồn đọng

- Không có quyết định bắt buộc đang chờ. Badge Cảnh báo được bỏ theo lựa chọn đã cho phép.
- Không làm Pha 2: không gộp studies, drawer, redirect URL cũ, dialog xóa mới, stepper hoặc thuật toán mới.
- Chưa nghiệm thu trên điện thoại thật, không xác minh gửi email/Google/AI thật vì lượt sửa chỉ thay UI.
- Các thay đổi không liên quan đã tồn tại trước phiên làm việc được giữ nguyên và để ngoài commit. Block planner_heading hiện có được tái sử dụng trong planner/base để bảo toàn khả năng ghi đè của Lịch tuần.
