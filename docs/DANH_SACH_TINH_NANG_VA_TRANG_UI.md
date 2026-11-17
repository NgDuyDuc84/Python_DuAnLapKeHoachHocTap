# Nhịp Học — Danh sách tính năng và các trang UI

Ngày rà soát: **16/11/2026**. Nội dung đối chiếu với URL, view và template trong mã nguồn hiện tại.

Các URL bên dưới là đường dẫn trong ứng dụng; khi chạy local, thêm `http://127.0.0.1:8000` phía trước. `<id>` là ID của bản ghi thuộc tài khoản đang đăng nhập. Tên template được tính từ thư mục `templates` của dự án. Những trang dùng chung template vẫn có thể là các màn hình khác nhau.

## 1. Bảng tổng hợp tính năng và UI theo từng phần

| STT | Phần | Tính năng hiện có | Trang hoặc UI tương ứng |
| --- | --- | --- | --- |
| 1 | Tài khoản và phân quyền | Đăng ký, đăng nhập, đăng xuất, xem thông tin, đổi mật khẩu; giới hạn dữ liệu theo chủ sở hữu | Đăng ký, Đăng nhập, Tài khoản của bạn, Đổi mật khẩu, Xác nhận đổi mật khẩu; menu tài khoản |
| 2 | Tổng quan | Buổi hôm nay, phút học 7 ngày, việc quá hạn, thông báo chưa đọc, buổi sắp tới, việc cần chú ý, tiếp tục Pomodoro | Tổng quan sau đăng nhập tại `/`; trang giới thiệu trước đăng nhập cũng dùng URL này |
| 3 | Môn học | Thêm/sửa/xóa, học kỳ, màu nhận diện, lưu trữ, tìm kiếm và lọc | Thanh bên Môn học trong Lịch tuần; các trang Danh sách, Thêm, Sửa, Xóa môn học |
| 4 | Công việc và deadline | Môn, mô tả, deadline, ưu tiên, ước tính, phút còn lại, chia buổi, trạng thái, tiến độ, tìm kiếm và lọc | Thanh bên Công việc trong Lịch tuần; các trang Danh sách, Thêm, Sửa, Cập nhật tiến độ, Xóa công việc |
| 5 | Tài liệu | Lưu URL HTTP/HTTPS, ghi chú, liên kết môn/công việc, tìm kiếm, lọc, thêm/sửa/xóa | Thanh bên Tài liệu trong Lịch tuần; các trang Danh sách, Thêm, Sửa, Xóa tài liệu |
| 6 | Lịch bận và tùy chọn học | Lịch bận một lần/lặp tuần/qua đêm; ngày học, khung giờ chung, giới hạn phút/ngày, độ dài buổi và nghỉ | Danh sách, Thêm, Sửa, Xóa lịch bận; Giờ học |
| 7 | Lịch tuần | Lịch 7 ngày chia Sáng/Chiều/Tối; lịch bận, buổi học và deadline; chọn/chuyển tuần; quản lý học tập trong thanh bên | Lịch tuần tại `/planner/` |
| 8 | Tạo kế hoạch tự động | Python xếp theo deadline rồi ưu tiên; tìm khoảng trống, chia buổi, chừa nghỉ, báo phần thiếu; xem trước và áp dụng | Tạo kế hoạch tuần; Chi tiết kế hoạch/Bản xem trước; kết quả trên Lịch tuần |
| 9 | Điều chỉnh và cảnh báo | Bổ sung/xếp lại; chỉnh giờ, khóa/mở khóa, ghi nhận/hủy buổi; cảnh báo quá hạn, thiếu lịch, xung đột và chưa ghi nhận | Chi tiết kế hoạch, Chỉnh giờ buổi học, Ghi nhận buổi học, Cảnh báo |
| 10 | Pomodoro | Học 25 phút, nghỉ 5 phút, tạm dừng/tiếp tục, kết thúc sớm, lưu hoặc hủy; giữ phiên khi tải lại trang | Bắt đầu tập trung; Chi tiết phiên tập trung |
| 11 | Nhật ký và thống kê | Nhật ký Pomodoro/nhập tay, sửa/xóa, lọc ngày; tổng phút, số bản ghi/ngày học, trung bình, biểu đồ và phân bổ theo môn/nguồn | Nhật ký học tập, Thêm/Sửa/Xóa nhật ký, Thống kê |
| 12 | Thông báo và email | Nhắc deadline/buổi học, tùy chọn kênh và độ nhắc sớm, đọc/chưa đọc, lịch sử email, yêu cầu gửi lại | Chuông thông báo, Hộp thông báo, Lịch sử email, Tùy chọn nhắc |
| 13 | Google Calendar và AI | Đồng bộ một chiều có xem trước/xác nhận; phân tích Python 14 ngày, yêu cầu AI có đồng ý, căn cứ và lịch sử | Google Calendar, Chi tiết yêu cầu đồng bộ; AI hỗ trợ, Chi tiết báo cáo AI |
| 14 | Quản trị và vận hành | Quản lý tài khoản/quyền; trang lỗi; cấu hình database, triển khai, worker, health check, demo và kiểm thử | Django Admin, các trang lỗi 403/404/500; công cụ vận hành chạy bằng lệnh hoặc cấu hình |

## 2. Danh sách các trang UI chi tiết

### 2.1. Trang chủ, tổng quan và tài khoản

| Trang UI | URL | Nội dung/thao tác chính | Template | Quyền truy cập |
| --- | --- | --- | --- | --- |
| Trang chủ giới thiệu | `/` | Giới thiệu ứng dụng, liên kết đăng ký/đăng nhập | `core/home.html` | Khách chưa đăng nhập |
| Tổng quan cá nhân | `/` | Số liệu cá nhân, buổi sắp tới, việc cần chú ý, tiếp tục phiên tập trung, hướng dẫn bắt đầu khi chưa có dữ liệu | `core/dashboard.html` | Đã đăng nhập |
| Đăng ký | `/accounts/register/` | Tạo tài khoản bằng tên đăng nhập, email và mật khẩu | `accounts/register.html` | Khách; người đã đăng nhập được chuyển về Tổng quan |
| Đăng nhập | `/accounts/login/` | Đăng nhập bằng tên đăng nhập và mật khẩu | `accounts/login.html` | Khách; người đã đăng nhập được chuyển tiếp |
| Tài khoản của bạn | `/accounts/profile/` | Xem tên đăng nhập, email, vai trò; liên kết đổi mật khẩu và quản trị khi có quyền | `accounts/profile.html` | Đã đăng nhập |
| Đổi mật khẩu | `/accounts/password-change/` | Nhập mật khẩu hiện tại và mật khẩu mới | `accounts/password_change.html` | Đã đăng nhập |
| Đổi mật khẩu thành công | `/accounts/password-change/done/` | Xác nhận đã đổi mật khẩu | `accounts/password_change_done.html` | Đã đăng nhập |

### 2.2. Môn học

| Trang/UI | URL | Nội dung/thao tác chính | Template |
| --- | --- | --- | --- |
| Thanh bên Môn học | `/planner/?panel=subjects` | Danh sách, tìm kiếm, phân trang, mở biểu mẫu thêm/sửa/xóa trong Lịch tuần | `planner/week.html` + `planner/study_sidebar.html` |
| Danh sách môn học riêng | `/studies/subjects/` | Tìm theo tên/học kỳ; lọc đang học, đã lưu trữ hoặc tất cả | `studies/subject_list.html` |
| Thêm môn học | `/studies/subjects/add/` | Tên, học kỳ, màu và trạng thái lưu trữ | `studies/form.html` |
| Sửa môn học | `/studies/subjects/<id>/edit/` | Chỉnh thông tin; lưu trữ hoặc bỏ lưu trữ môn | `studies/form.html` |
| Xác nhận xóa môn học | `/studies/subjects/<id>/delete/` | Cảnh báo ảnh hưởng và xác nhận xóa; giữ công việc/tài liệu, bỏ liên kết môn | `studies/confirm_delete.html` |

### 2.3. Công việc và tiến độ

| Trang/UI | URL | Nội dung/thao tác chính | Template |
| --- | --- | --- | --- |
| Thanh bên Công việc | `/planner/?panel=tasks` | Danh sách, deadline, phút còn lại, trạng thái, tìm kiếm, phân trang và thêm/sửa/xóa trong Lịch tuần | `planner/week.html` + `planner/study_sidebar.html` |
| Danh sách công việc riêng | `/studies/tasks/` | Tìm kiếm; lọc môn, ưu tiên, trạng thái và quá hạn | `studies/task_list.html` |
| Thêm công việc | `/studies/tasks/add/` | Tên, môn, mô tả, deadline, ưu tiên, thời lượng ước tính, cho chia buổi và trạng thái | `studies/form.html` |
| Sửa công việc | `/studies/tasks/<id>/edit/` | Chỉnh thông tin, deadline và thời lượng còn lại | `studies/form.html` |
| Cập nhật tiến độ | `/studies/tasks/<id>/progress/` | Cập nhật trạng thái và số phút thực tế còn cần; hoàn thành đưa phút còn lại về 0 | `studies/form.html` |
| Xác nhận xóa công việc | `/studies/tasks/<id>/delete/` | Xác nhận xóa việc và các buổi học của việc; giữ tài liệu, nhật ký và Pomodoro, bỏ liên kết việc | `studies/confirm_delete.html` |

### 2.4. Tài liệu

| Trang/UI | URL | Nội dung/thao tác chính | Template |
| --- | --- | --- | --- |
| Thanh bên Tài liệu | `/planner/?panel=materials` | Danh sách, tìm kiếm, phân trang, thêm/sửa/xóa và mở tài liệu | `planner/week.html` + `planner/study_sidebar.html` |
| Danh sách tài liệu riêng | `/studies/materials/` | Tìm theo tên/ghi chú; lọc theo môn và công việc | `studies/material_list.html` |
| Thêm tài liệu | `/studies/materials/add/` | Tên, URL HTTP/HTTPS, môn/công việc liên quan và ghi chú | `studies/form.html` |
| Sửa tài liệu | `/studies/materials/<id>/edit/` | Chỉnh thông tin và liên kết | `studies/form.html` |
| Xác nhận xóa tài liệu | `/studies/materials/<id>/delete/` | Xóa liên kết đã lưu trong ứng dụng; tệp ở website gốc được giữ nguyên | `studies/confirm_delete.html` |

### 2.5. Lịch tuần, lịch bận và giờ học

| Trang UI | URL | Nội dung/thao tác chính | Template |
| --- | --- | --- | --- |
| Lịch tuần | `/planner/` | Tuần thứ Hai–Chủ nhật, Sáng/Chiều/Tối, lịch bận/buổi học/deadline, chuyển tuần và mở thanh bên học tập | `planner/week.html` |
| Danh sách lịch bận | `/planner/busy/` | Xem lịch bận và mở thao tác thêm/sửa/xóa | `planner/busyevent_list.html` |
| Thêm lịch bận | `/planner/busy/add/` | Tên, bắt đầu/kết thúc, lặp tuần, ngày dừng lặp; hỗ trợ qua đêm | `planner/form.html` |
| Sửa lịch bận | `/planner/busy/<id>/edit/` | Chỉnh lịch bận và quy tắc lặp | `planner/form.html` |
| Xác nhận xóa lịch bận | `/planner/busy/<id>/delete/` | Xác nhận xóa bản ghi lịch bận | `planner/confirm_delete.html` |
| Giờ học | `/planner/preferences/` | Ngày học, khung giờ chung, phút tối đa/ngày, độ dài buổi và nghỉ | `planner/form.html` |

### 2.6. Kế hoạch, buổi học và cảnh báo

| Trang UI | URL | Nội dung/thao tác chính | Template |
| --- | --- | --- | --- |
| Tạo kế hoạch tuần | `/planner/plans/new/` | Chọn tuần, chế độ Bổ sung/Xếp lại, tạo bản xem trước; xem 10 kế hoạch gần đây | `planner/plan_form.html` |
| Chi tiết kế hoạch / Bản xem trước | `/planner/plans/<id>/` | Các buổi đề xuất, báo cáo phân bổ/phần thiếu/lý do, buổi cũ sẽ thay; áp dụng hoặc quản lý các buổi đã áp dụng | `planner/plan_detail.html` |
| Chỉnh giờ buổi học | `/planner/sessions/<id>/edit/` | Đổi giờ và độ dài buổi chưa bắt đầu; kiểm tra ràng buộc hiện tại | `planner/session_form.html` |
| Ghi nhận buổi học | `/planner/sessions/<id>/record/` | Chọn Đã học hoặc Hủy/bỏ qua; nhập thời lượng công việc còn lại | `planner/session_form.html` |
| Cảnh báo và việc cần rà soát | `/planner/alerts/` | Việc quá hạn/thiếu lịch, buổi xung đột, buổi đã kết thúc chưa ghi nhận | `planner/alerts.html` |

Khóa/mở khóa được thực hiện bằng nút trên trang chi tiết kế hoạch. Bổ sung/Xếp lại được chọn trên trang tạo kế hoạch. Hai trạng thái xem trước và đã áp dụng dùng chung trang chi tiết kế hoạch.

### 2.7. Pomodoro, nhật ký và thống kê

| Trang UI | URL | Nội dung/thao tác chính | Template |
| --- | --- | --- | --- |
| Bắt đầu tập trung | `/focus/` | Chọn công việc, bắt đầu phiên 25 phút, quay lại phiên đang hoạt động, xem các phiên gần đây | `focus/start.html` |
| Chi tiết phiên tập trung | `/focus/sessions/<id>/` | Đồng hồ, tạm dừng/tiếp tục, lưu kết thúc, hủy, ghi chú; bắt đầu nghỉ 5 phút sau phiên học đã kết thúc | `focus/session.html` |
| Nhật ký học tập | `/focus/logs/` | Nhật ký Pomodoro/nhập tay, lọc khoảng ngày và phân trang | `focus/log_list.html` |
| Thêm nhật ký | `/focus/logs/add/` | Chọn công việc, ngày học, số phút và ghi chú | `focus/log_form.html` |
| Sửa nhật ký | `/focus/logs/<id>/edit/` | Nhật ký nhập tay sửa ngày/phút/việc/ghi chú; nhật ký Pomodoro chỉ sửa ghi chú | `focus/log_form.html` |
| Xác nhận xóa nhật ký | `/focus/logs/<id>/delete/` | Xác nhận xóa bản ghi; thống kê thay đổi theo nhật ký còn lưu | `focus/log_delete.html` |
| Thống kê thời gian học | `/focus/statistics/` | Tổng phút, số bản ghi, ngày có học, trung bình, biểu đồ theo ngày và phân bổ theo môn/nguồn | `focus/statistics.html` |

### 2.8. Thông báo và email

| Trang/UI | URL hoặc vị trí | Nội dung/thao tác chính | Template |
| --- | --- | --- | --- |
| Chuông thông báo | Thanh đầu trang sau đăng nhập | Số chưa đọc, 5 thông báo gần nhất; mở đúng thông báo trong hộp thông báo | `base.html` |
| Hộp thông báo | `/notifications/` | Danh sách thông báo, lọc chưa đọc, đánh dấu đọc từng mục hoặc tất cả | `notifications/inbox.html` |
| Lịch sử email nhắc | `/notifications/email/` | Nội dung và trạng thái gửi, lỗi, yêu cầu gửi lại khi phù hợp | `notifications/email_history.html` |
| Tùy chọn nhắc việc | `/notifications/preferences/` | Bật/tắt web/email; nhắc deadline trước 1/3/24 giờ, buổi học trước 5/15/30 phút | `notifications/preferences.html` |

### 2.9. Google Calendar

| Trang UI | URL | Nội dung/thao tác chính | Template |
| --- | --- | --- | --- |
| Google Calendar | `/integrations/google/` | Trạng thái kết nối, kết nối/cấp lại quyền/ngắt kết nối, chọn tuần, xem trước và xác nhận đồng bộ, lịch sử yêu cầu | `integrations/google.html` |
| Chi tiết yêu cầu đồng bộ | `/integrations/google/jobs/<id>/` | Tuần xử lý, trạng thái, kết quả và lỗi của yêu cầu | `integrations/job.html` |

Bản xem trước xuất hiện ngay trên trang Google Calendar sau khi chọn tuần. Việc cấp quyền mở giao diện của Google rồi quay về callback của ứng dụng. Khi cần xác nhận cho tạo lịch đích mới, biểu mẫu xuất hiện có điều kiện ngay trên trang Google Calendar.

### 2.10. Phân tích Python và AI

| Trang UI | URL | Nội dung/thao tác chính | Template |
| --- | --- | --- | --- |
| AI hỗ trợ học tập | `/insights/` | Số liệu 14 ngày, nhận xét Python, công việc/cảnh báo, xem dữ liệu gửi, đồng ý yêu cầu AI và 10 yêu cầu gần nhất | `insights/home.html` |
| Chi tiết báo cáo AI | `/insights/reports/<id>/` | Kết quả/lỗi, tóm tắt, thói quen, gợi ý phân bổ, giải thích cảnh báo, căn cứ, dữ liệu đầu vào và dấu hiệu dữ liệu đã đổi | `insights/report.html` |

Nhận xét Python, xem trước dữ liệu gửi và lịch sử AI là các phần trong trang AI hỗ trợ. Chúng không có trang URL riêng.

### 2.11. Quản trị và các trang lỗi

| Trang UI | URL hoặc điều kiện xuất hiện | Nội dung/thao tác chính | Template |
| --- | --- | --- | --- |
| Trang quản trị | `/admin/` | Trang chủ Django Admin, các mục được phép quản lý | Django Admin tích hợp sẵn |
| Đăng nhập quản trị | `/admin/login/` | Đăng nhập khu vực quản trị | Django Admin tích hợp sẵn |
| Quản lý tài khoản | `/admin/auth/user/` | Danh sách, thêm/sửa/xóa tài khoản; email, trạng thái hoạt động và quyền theo quyền quản trị được cấp | Django Admin tích hợp sẵn |
| Quản lý nhóm quyền | `/admin/auth/group/` | Quản lý nhóm và quyền | Django Admin tích hợp sẵn |
| Lỗi 403 | Khi yêu cầu bị từ chối; có xử lý lỗi CSRF riêng | Thông báo truy cập/yêu cầu không hợp lệ | `403.html` |
| Lỗi 404 | Khi đường dẫn hoặc bản ghi không tồn tại/không được phép truy cập | Thông báo không tìm thấy | `404.html` |
| Lỗi 500 | Khi có lỗi máy chủ | Thông báo lỗi hệ thống | `500.html` |

Các trang Admin yêu cầu tài khoản staff đang hoạt động và quyền phù hợp. Mã hiện tại chưa đăng ký các model học tập, kế hoạch, Pomodoro, thông báo, đồng bộ hoặc AI vào Admin. Trang lỗi 404/500 tùy chỉnh được dùng khi tắt chế độ debug; ở chế độ debug Django có thể hiển thị trang chẩn đoán.

## 3. Các trạng thái UI ngay trong Lịch tuần

| UI | Ví dụ URL | Ý nghĩa |
| --- | --- | --- |
| Xem một tuần | `/planner/?week=2026-11-16` | Chọn một ngày trong tuần; hệ thống quy về thứ Hai đầu tuần |
| Mở Môn học | `/planner/?panel=subjects` | Mở danh sách môn trong thanh bên |
| Mở Công việc | `/planner/?panel=tasks` | Mở danh sách công việc trong thanh bên |
| Mở Tài liệu | `/planner/?panel=materials` | Mở danh sách tài liệu trong thanh bên |
| Thêm mới trong thanh bên | `/planner/?panel=tasks&action=new` | Mở biểu mẫu thêm công việc |
| Chỉnh sửa trong thanh bên | `/planner/?panel=tasks&action=edit&id=<id>` | Mở biểu mẫu sửa công việc |
| Xác nhận xóa trong thanh bên | `/planner/?panel=tasks&action=delete&id=<id>` | Mở phần xác nhận xóa công việc |
| Tìm kiếm và phân trang | `/planner/?panel=tasks&q=Python&page=1` | Tìm theo tên và chuyển trang danh sách |
| Giữ tuần khi mở biểu mẫu | `/planner/?week=2026-11-16&panel=tasks&action=new` | Thêm công việc trong khi giữ tuần đang xem |

Thay `panel=tasks` bằng `panel=subjects` hoặc `panel=materials` để thực hiện tương tự cho môn học và tài liệu. Các trạng thái này dùng chung `planner/week.html`, `planner/study_sidebar.html` và phần trường nhập `studies/form_fields.html`.

## 4. Các URL xử lý thao tác và dữ liệu

Các URL dưới đây được gọi từ nút/biểu mẫu hoặc JavaScript. Chúng không phải trang nội dung độc lập để mở như các bảng UI ở trên; khi có lỗi, một số thao tác có thể hiển thị lại giao diện nguồn.

| Nhóm | URL | Phương thức | Vai trò / UI nguồn |
| --- | --- | --- | --- |
| Tài khoản | `/accounts/logout/` | POST | Đăng xuất từ menu tài khoản |
| Kế hoạch | `/planner/plans/<id>/apply/` | POST | Áp dụng bản xem trước vào lịch |
| Buổi học | `/planner/sessions/<id>/lock/` | POST | Khóa/mở khóa từ chi tiết kế hoạch |
| Pomodoro | `/focus/sessions/<id>/state/` | GET | Trả JSON trạng thái đồng hồ cho JavaScript |
| Pomodoro | `/focus/sessions/<id>/pause/` | POST | Tạm dừng phiên |
| Pomodoro | `/focus/sessions/<id>/resume/` | POST | Tiếp tục phiên |
| Pomodoro | `/focus/sessions/<id>/finish/` | POST | Lưu và kết thúc phiên |
| Pomodoro | `/focus/sessions/<id>/cancel/` | POST | Hủy phiên |
| Pomodoro | `/focus/sessions/<id>/break/` | POST | Bắt đầu nghỉ ngắn từ phiên học đã kết thúc |
| Thông báo | `/notifications/read-all/` | POST | Đánh dấu tất cả đã đọc |
| Thông báo | `/notifications/<id>/read/` | POST | Đánh dấu một thông báo đã đọc |
| Email | `/notifications/<id>/retry-email/` | POST | Xếp hàng yêu cầu gửi lại email |
| Google | `/integrations/google/connect/` | POST | Bắt đầu cấp quyền, chuyển sang Google |
| Google | `/integrations/google/callback/` | GET | Nhận kết quả OAuth và chuyển về trang Google Calendar |
| Google | `/integrations/google/disconnect/` | POST | Ngắt kết nối Google |
| Google | `/integrations/google/sync/` | POST | Xác nhận và xếp hàng đồng bộ |
| Google | `/integrations/google/reset/` | POST | Xác nhận cho phép tạo lịch đích mới khi cần |
| AI | `/insights/generate/` | POST | Gửi yêu cầu phân tích sau bước xem trước/đồng ý |
| Vận hành | `/health/` | GET / HEAD | Trả JSON trạng thái ứng dụng/database; không có giao diện HTML |

Các trang biểu mẫu thêm/sửa/xóa, tạo kế hoạch, ghi nhận buổi và tùy chọn ở mục 2 còn xử lý POST tại chính URL của trang. Lịch tuần xử lý lưu/xóa dữ liệu thanh bên tại `/planner/` kèm các tham số tương ứng.

## 5. Các thành phần giao diện dùng chung

| Thành phần | Vị trí / phạm vi | Vai trò |
| --- | --- | --- |
| Khung trang, điều hướng, chuông và menu tài khoản | `base.html` | Điều hướng chung; thông báo nhanh; tài khoản, đổi mật khẩu, quản trị và đăng xuất |
| Khung biểu mẫu tài khoản | `accounts/form_page.html` | Bố cục dùng chung cho các biểu mẫu tài khoản |
| Khung quản lý học tập | `studies/base.html` | Điều hướng các trang quản lý môn/công việc/tài liệu riêng |
| Biểu mẫu học tập dùng chung | `studies/form.html`, `studies/form_fields.html` | Tái sử dụng các trường nhập cho nhiều loại dữ liệu và thanh bên |
| Bộ lọc và xác nhận xóa | `studies/filters.html`, `studies/confirm_delete.html` | Bộ lọc danh sách và cảnh báo trước khi xóa |
| Khung lập kế hoạch | `planner/base.html` | Khung và các tab quản lý lịch; trang Lịch tuần dùng bố cục riêng trong khung này |
| Thanh bên và mục lịch | `planner/study_sidebar.html`, `planner/calendar_item.html` | Quản lý học tập ngay trong lịch và hiển thị từng mục lịch |
| Khung tập trung và bộ lọc ngày | `focus/base.html`, `focus/range_filter.html` | Điều hướng Pomodoro/Nhật ký/Thống kê; chọn khoảng ngày |
| Khung thông báo và phân trang | `notifications/base.html`, `notifications/pagination.html` | Điều hướng hộp thông báo/lịch sử email/tùy chọn và chuyển trang |
| Khung và các mục phân tích | `insights/base.html`, `insights/sections.html` | Bố cục phân tích, các nhận xét và căn cứ |

## 6. Phạm vi và điều kiện sử dụng

| Hạng mục | Trạng thái / giới hạn |
| --- | --- |
| Quyền truy cập | Ngoại trừ trang giới thiệu, đăng ký/đăng nhập và endpoint health, các trang nghiệp vụ yêu cầu đăng nhập. Bản ghi được giới hạn theo chủ sở hữu; Admin có cơ chế quyền riêng. |
| Xếp lịch | Thuật toán tham lam Python, chưa chứng minh tối ưu toàn cục. Phần chưa xếp được hiển thị trong báo cáo. Thay đổi đầu vào chưa tự dời lịch; người dùng tạo phương án và áp dụng. |
| Tiến độ và nhật ký | Nhật ký/Pomodoro đo thời gian học; người dùng cập nhật riêng số phút công việc còn cần. |
| Tài liệu | Quản lý liên kết HTTP/HTTPS; chưa có trang tải tệp lên máy chủ. |
| Pomodoro | Chưa có tự lặp chu kỳ, nghỉ dài hoặc chuông báo. Hết giờ vẫn cần lưu và kết thúc phiên. |
| Nhắc việc | Cần chạy `process_reminders`; email thật cần SMTP. Mặc định email chỉ xuất nội dung ra terminal. |
| Google Calendar | Đồng bộ một chiều các buổi học đã áp dụng; cần OAuth, khóa mã hóa và worker `process_calendar_sync`. Không nhập lịch Google về ứng dụng. |
| AI | Phân tích Python dùng được khi thiếu API key. Gọi AI cần cấu hình OpenAI và người dùng đồng ý; kết quả không tự sửa lịch hoặc tiến độ. |
| Dịch vụ bên ngoài | Theo tài liệu hiện tại, SMTP, Google và OpenAI thật chưa được xác minh vì chưa có khóa; đã có mã tích hợp và kiểm thử giả lập. |
| Triển khai | Có cấu hình triển khai; website chưa được public. Database, worker, Docker, CI và lệnh demo không có trang UI nghiệp vụ riêng. |
| Trang hướng dẫn trong web | Trang hướng dẫn riêng đã được bỏ; mã hiện tại không có route `/guide/`. Hướng dẫn nằm trong tài liệu dự án và các nội dung hỗ trợ tại từng trang. |

Nguồn đối chiếu: các tệp `urls.py`, `views.py`, biểu mẫu và template của `core`, `accounts`, `studies`, `planner`, `focus`, `notifications`, `integrations`, `insights`; cấu hình URL chung và tài liệu báo cáo dự án. Bảng mô tả những gì có trong mã; lượt rà soát này không xác nhận kết nối nhà cung cấp thật hay nghiệm thu trực quan toàn bộ trang.
