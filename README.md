# Python_DuAnLapKeHoachHocTap

Ứng dụng lập kế hoạch học tập cá nhân có AI gợi ý lịch, định hướng Django với Python xử lý nghiệp vụ chính.

- [Kế hoạch phát triển](docs/KE_HOACH_PHAT_TRIEN.md)
- [Thiết kế ban đầu](docs/THIET_KE_BAN_DAU.md)
- [Hướng dẫn kiểm thử từng bước](HD_Test.md)

Hiện tại: **mốc 02 — tài khoản và phân quyền**, đang chờ người dùng kiểm thử và push GitHub. Tên hiển thị tạm thời của ứng dụng là **Nhịp Học**.

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

Mốc này dùng SQLite; PostgreSQL và cấu hình triển khai online được thực hiện ở mốc sau. Đã có đăng ký, đăng nhập, đăng xuất, đổi mật khẩu và trang thông tin tài khoản riêng. Chức năng quản lý học tập và lập lịch được triển khai ở các mốc tiếp theo.

Các trang chính:

- [Đăng ký](http://127.0.0.1:8000/accounts/register/): tên đăng nhập duy nhất, email và mật khẩu.
- [Đăng nhập](http://127.0.0.1:8000/accounts/login/): dùng tên đăng nhập.
- [Tài khoản của bạn](http://127.0.0.1:8000/accounts/profile/): yêu cầu đăng nhập, có liên kết đổi mật khẩu.
- [Quản trị](http://127.0.0.1:8000/admin/): tài khoản quản trị có quyền phù hợp.

Tạo quản trị viên bằng `& .\.venv\Scripts\python.exe manage.py createsuperuser`, nhập thông tin trực tiếp trong terminal. Đăng xuất qua nút trên giao diện dùng POST, không mở URL đăng xuất bằng GET.

Chạy kiểm thử tự động:

```powershell
& .\.venv\Scripts\python.exe manage.py test accounts --noinput
```

Các kiểm thử dùng database riêng trong bộ nhớ, không sửa tài khoản đang lưu ở `db.sqlite3`. Xem checklist đầy đủ và cách kiểm tra khóa/mở tài khoản trong `HD_Test.md`.
