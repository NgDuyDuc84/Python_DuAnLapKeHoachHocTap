# Nhịp Học

Web lập kế hoạch học tập cá nhân bằng Django/Python, giao diện tiếng Việt và giờ Việt Nam. Dữ liệu được tách riêng theo tài khoản.

## Tính năng hiện có

- Đăng ký, đăng nhập, đổi mật khẩu và quản lý tài khoản.
- Quản lý môn học, công việc, deadline, mức ưu tiên, tiến độ và tài liệu liên kết.
- Lịch tuần, lịch bận lặp lại, tùy chọn giờ học; tự xếp lịch theo deadline và thời gian rảnh, xem trước rồi áp dụng. Hỗ trợ bổ sung/xếp lại, chỉnh tay, khóa buổi, ghi nhận đã học hoặc hủy.
- Tổng quan hôm nay, cảnh báo quá hạn/xung đột; Pomodoro, nhật ký và thống kê theo ngày/môn/nguồn.
- Thông báo trong web và email nhắc; đồng bộ các buổi đã xác nhận lên Google Calendar.
- Phân tích học tập bằng Python; tùy chọn yêu cầu AI phân tích dữ liệu đã xem trước và đồng ý gửi.

## Chạy tại máy

Cần Python 3.12–3.14. Mở PowerShell tại thư mục dự án; bỏ qua bước tạo môi trường nếu đã có `.venv`:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path -LiteralPath .env)) { Copy-Item .env.example .env }
& .\.venv\Scripts\python.exe manage.py migrate
& .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Mở [Nhịp Học tại máy](http://127.0.0.1:8000/). Mặc định dùng SQLite; đặt `DATABASE_URL` trong `.env` để dùng PostgreSQL. Nếu lệnh `python` mở Windows Store, dùng `py -3.14 -m venv .venv` hoặc đường dẫn Python đã cài. Không cần kích hoạt venv.

Để chạy nhắc việc và xử lý hàng đợi Google Calendar, mở riêng từng terminal:

```powershell
& .\.venv\Scripts\python.exe -X utf8 manage.py process_reminders --watch
& .\.venv\Scripts\python.exe -X utf8 manage.py process_calendar_sync --watch
```

Mỗi lệnh chạy ở một terminal; Ctrl+C để dừng. Email mặc định chỉ xuất ra terminal. Gửi email thật cần các biến `EMAIL_*`; Google cần `GOOGLE_*` và callback đúng địa chỉ web; AI cần `OPENAI_API_KEY` và `OPENAI_MODEL` khả dụng. Xem tên biến trong `.env.example`. Khi chưa cấu hình dịch vụ ngoài, chức năng học tập và phân tích Python vẫn hoạt động. Khóa và mật khẩu chỉ lưu trong môi trường, không đưa lên Git.

## Demo cho giảng viên

Dữ liệu mẫu mô phỏng một học kỳ: 4 môn, 12 công việc đủ trạng thái, 8 tài liệu, 3 lịch bận, 10 buổi học, 14 nhật ký trong hai tuần (560 phút), 3 thông báo và lịch sử Pomodoro. Ngày tháng được tính theo ngày chạy lệnh. Dữ liệu này là giả lập, không phải kết quả gửi email/Google/AI thật.

Các tài khoản demo: `nguyen_van_a`, `tran_thi_b`, `le_van_c`; mật khẩu được trao riêng trong cuộc trò chuyện, không lưu trong repository. Trên Render, đặt biến bí mật `DEMO_ACCOUNT_PASSWORD` rồi deploy: launcher chạy `bootstrap_demo` sau migration để tạo ba tài khoản và nạp cùng bộ dữ liệu mẫu. Chạy lại giữ nguyên dữ liệu/tiến độ, không đặt lại mật khẩu. Có thể xóa biến này sau khi nạp thành công.

Để nạp mẫu cho một tài khoản thường đã đăng ký và còn trống:

```powershell
& .\.venv\Scripts\python.exe manage.py seed_demo --username nguyen_van_a
```

Lệnh không tạo tài khoản, không đổi mật khẩu, không ghi đè dữ liệu, chạy lại không tạo trùng và không gọi dịch vụ ngoài. Demo theo thứ tự: Tổng quan → Lịch tuần → công việc/deadline → tạo và áp dụng kế hoạch → Pomodoro/nhật ký → thống kê → thông báo. Đăng nhập tài khoản khác để kiểm tra dữ liệu được tách riêng.

## Kiểm thử và triển khai

```powershell
& .\.venv\Scripts\python.exe manage.py check
& .\.venv\Scripts\python.exe manage.py test --noinput
& .\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
& .\.venv\Scripts\python.exe manage.py collectstatic --noinput --settings=config.assets
```

Test dùng database riêng. Docker local: `docker compose up --build -d` chạy PostgreSQL, web và hai worker; mở cổng 8000. Dừng bằng `docker compose down` (giữ volume dữ liệu).

Render: tạo Blueprint từ nhánh `main`, dùng `render.yaml`; cấu hình lấy hostname, secret và PostgreSQL từ nền tảng, chạy migration rồi web cùng hai worker. Auto-deploy đang tắt; cập nhật bằng Manual Deploy của đúng nhánh. Web Free có thể ngủ và worker cũng dừng theo; database Free có thời hạn, xem [giới hạn Render](https://render.com/docs/free). Kiểm tra URL do Render cấp và `/health/` sau deploy. Production riêng dùng `config.production`, PostgreSQL, secret riêng, `SITE_URL` HTTPS, `DJANGO_ALLOWED_HOSTS` và reverse proxy; mẫu biến ở `deploy/production.env.example`.

Tài nguyên cục bộ: Lora/Inter từ Google Fonts (giấy phép OFL và nguồn/hash trong `static/fonts/`); Flatpickr 4.6.13 từ npm (MIT trong `static/vendor/flatpickr/LICENSE.md`, bản gốc không chỉnh sửa). Ảnh lịch/sách được tạo bằng ImageGen, lưu trong `static/images/auth/`. Giữ các giấy phép đi kèm khi phân phối.
