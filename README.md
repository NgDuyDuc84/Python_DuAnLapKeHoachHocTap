# Python_DuAnLapKeHoachHocTap

Ứng dụng lập kế hoạch học tập cá nhân có AI gợi ý lịch, định hướng Django với Python xử lý nghiệp vụ chính.

- [Kế hoạch phát triển](docs/KE_HOACH_PHAT_TRIEN.md)
- [Thiết kế ban đầu](docs/THIET_KE_BAN_DAU.md)
- [Hướng dẫn kiểm thử từng bước](HD_Test.md)

Hiện tại: **mốc 04 — lịch bận, tùy chọn học và lịch tuần**, đang chờ người dùng kiểm thử và push GitHub. Tên hiển thị tạm thời của ứng dụng là **Nhịp Học**.

Cần Python 3.12–3.14. Từ PowerShell tại thư mục dự án:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path -LiteralPath .env)) {
    Copy-Item -LiteralPath .env.example -Destination .env
}
& .\.venv\Scripts\python.exe manage.py migrate
& .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Mở [trang chủ local](http://127.0.0.1:8000/). Nếu `.venv` đã tồn tại, bỏ qua lệnh tạo môi trường. Không cần kích hoạt môi trường hoặc đổi Execution Policy. Nếu lệnh `python` lỗi WindowsApps, xem đường dẫn Python thay thế trong `HD_Test.md`.

Mốc này dùng SQLite; PostgreSQL và cấu hình triển khai online được thực hiện ở mốc sau. Đã có tài khoản, quản lý học tập, lịch bận, tùy chọn thời gian học và lịch tuần. Thuật toán tự tạo buổi học được triển khai ở mốc 05.

Các trang chính:

- [Đăng ký](http://127.0.0.1:8000/accounts/register/): tên đăng nhập duy nhất, email và mật khẩu.
- [Đăng nhập](http://127.0.0.1:8000/accounts/login/): dùng tên đăng nhập.
- [Tài khoản của bạn](http://127.0.0.1:8000/accounts/profile/): yêu cầu đăng nhập, có liên kết đổi mật khẩu.
- [Môn học](http://127.0.0.1:8000/studies/subjects/): thêm/sửa/xóa, màu, học kỳ và lưu trữ.
- [Công việc](http://127.0.0.1:8000/studies/tasks/): deadline, ưu tiên, thời lượng, trạng thái và lọc quá hạn.
- [Tài liệu](http://127.0.0.1:8000/studies/materials/): liên kết HTTP/HTTPS theo môn hoặc công việc.
- [Lịch tuần](http://127.0.0.1:8000/planner/): lịch bận, deadline và khoảng trống từ hiện tại.
- [Lịch bận](http://127.0.0.1:8000/planner/busy/): một lần/lặp hằng tuần, hỗ trợ qua đêm.
- [Giờ học](http://127.0.0.1:8000/planner/preferences/): ngày được học, khung giờ chung, giới hạn phút/ngày, độ dài buổi và nghỉ.
- [Quản trị](http://127.0.0.1:8000/admin/): tài khoản quản trị có quyền phù hợp.

Tạo quản trị viên bằng `& .\.venv\Scripts\python.exe manage.py createsuperuser`, nhập thông tin trực tiếp trong terminal. Đăng xuất qua nút trên giao diện dùng POST, không mở URL đăng xuất bằng GET.

Chạy kiểm thử tự động:

```powershell
& .\.venv\Scripts\python.exe manage.py test accounts studies planner --noinput
```

Các kiểm thử dùng database riêng trong bộ nhớ, không sửa tài khoản đang lưu ở `db.sqlite3`. Xem checklist đầy đủ và cách kiểm tra khóa/mở tài khoản trong `HD_Test.md`.

Mốc 03 có migration mới: chạy `manage.py migrate` trước khi mở phần Học tập. Mỗi người chỉ xem/sửa/xóa dữ liệu mình sở hữu. Xóa môn/công việc gỡ liên kết nhưng giữ lại tài liệu; lưu trữ môn giữ nguyên các liên kết. Công việc mới có thời lượng còn lại bằng ước tính; chọn Hoàn thành đưa thời lượng còn lại về 0.

Mốc 04 thêm migration `planner/0001_initial.py`; tiếp tục chạy `manage.py migrate` khi cập nhật. Lịch tuần dựng bằng Python/Django Templates, tuần bắt đầu thứ Hai và dùng giờ Việt Nam. Lịch bận chồng nhau được gộp khi tính khoảng trống; deadline chỉ là mốc hạn, không chiếm một khoảng thời gian. Quỹ phút hiển thị là giới hạn tối đa có thể bố trí, chưa phải lịch học được sinh tự động.
