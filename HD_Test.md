**Hướng dẫn kiểm thử theo từng mốc**

Sau mỗi mốc, người dùng kiểm thử, ghi nhận kết quả rồi commit/push GitHub. Chỉ chuyển mốc khi người dùng xác nhận. Khi có mốc mới, bổ sung vào tài liệu và giữ lịch sử các mốc cũ.

**Mốc 01 — Thiết kế và bộ khung Django chạy local**

Trạng thái: chờ người dùng kiểm thử và push GitHub.

Phạm vi đã làm: tài liệu thiết kế, cấu hình Django, trang chủ Nhịp Học, template chung, CSS responsive, đọc `.env`, SQLite và `.gitignore`. `/admin/` là trang quản trị mặc định của Django; chưa xây giao diện tài khoản cho người dùng. Chưa có công việc, lịch tuần, thuật toán, Pomodoro, AI hoặc bản online.

1. **Chuẩn bị môi trường**

   Mở PowerShell:

   ```powershell
   Set-Location -LiteralPath 'D:\Python_DuAnLapKeHoachHocTap'
   ```

   Cần Python 3.12–3.14. Môi trường `.venv` đã được tạo trên máy hiện tại với Python 3.14.7. Nếu `.venv` đã có, đi tiếp phần cài thư viện. Khi clone mới, tạo bằng:

   ```powershell
   python -m venv .venv
   ```

   Nếu `python`/`py` trỏ WindowsApps và không chạy, máy hiện tại có thể dùng trực tiếp đường dẫn sau, chỉ thực hiện nếu chưa có `.venv`:

   ```powershell
   & 'C:\Users\84ndd\AppData\Local\Python\pythoncore-3.14-64\python.exe' -m venv .venv
   ```

   Đường dẫn này phụ thuộc máy. Máy khác dùng đường dẫn Python đã cài trên máy đó. Không cần kích hoạt môi trường hoặc thay Execution Policy; các lệnh bên dưới gọi thẳng Python trong `.venv`.

2. **Cài thư viện và cấu hình local**

   ```powershell
   & .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   if (-not (Test-Path -LiteralPath .env)) {
       Copy-Item -LiteralPath .env.example -Destination .env
   }
   & .\.venv\Scripts\python.exe -m django --version
   & .\.venv\Scripts\python.exe -m pip check
   ```

   Mong đợi: Django `5.2.19`, và `No broken requirements found.` Cài lần đầu cần Internet tới PyPI. File `.env` giữ ở máy, không push. Các giá trị mẫu phục vụ phát triển local; chưa dùng để triển khai online.

3. **Kiểm tra cấu hình và tạo database**

   ```powershell
   & .\.venv\Scripts\python.exe manage.py check
   & .\.venv\Scripts\python.exe manage.py migrate
   & .\.venv\Scripts\python.exe manage.py migrate --check
   & .\.venv\Scripts\python.exe manage.py shell -c "from django.conf import settings; print(settings.LANGUAGE_CODE); print(settings.TIME_ZONE)"
   ```

   Mong đợi: `System check identified no issues (0 silenced).`; migration được áp dụng hoặc `No migrations to apply.`; `migrate --check` kết thúc thành công; ngôn ngữ `vi`, múi giờ `Asia/Ho_Chi_Minh`. Database `db.sqlite3` được tạo ở gốc dự án và không đưa lên GitHub.

4. **Khởi chạy web**

   ```powershell
   & .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
   ```

   Giữ terminal này đang chạy. Mở [http://127.0.0.1:8000/](http://127.0.0.1:8000/). Dừng bằng `Ctrl+C`. Nếu cổng đang bận, dùng `127.0.0.1:8001` và thay cổng trong các URL kiểm thử bên dưới.

5. **Checklist kiểm thử thủ công**

   | ID | Thao tác | Kết quả mong đợi | Kết quả của bạn |
   |---|---|---|---|
   | TC01 | Mở trang chủ | HTTP 200; tiêu đề tab có Nhịp Học; tiếng Việt đúng dấu; thấy “Học có kế hoạch.” | Chưa kiểm thử |
   | TC02 | Mở `/static/css/app.css` hoặc xem Network | HTTP 200; CSS được tải; trang chủ có nền sáng, nút xanh và thẻ ghi chú | Chưa kiểm thử |
   | TC03 | Bấm “Cách sử dụng” và “Khám phá cách sử dụng” | Đến phần “Một kế hoạch bắt đầu từ đâu?” trên cùng trang | Chưa kiểm thử |
   | TC04 | Bấm logo và “Trang chủ” | Trở về trang chủ, không lỗi URL | Chưa kiểm thử |
   | TC05 | Dùng DevTools hoặc thu hẹp về 375 px và 320 px | Không cuộn ngang; nội dung dễ đọc; các thẻ xếp một cột | Chưa kiểm thử |
   | TC06 | Dùng Tab ngay từ đầu trang | Có liên kết đến nội dung chính; focus nhìn thấy; điều hướng/nút dùng được bằng bàn phím | Chưa kiểm thử |
   | TC07 | Mở `/duong-dan-khong-ton-tai/` | HTTP 404, không phải 500. DEBUG local có thể hiển thị trang chẩn đoán Django | Chưa kiểm thử |
   | TC08 | Mở `/admin/` khi chưa đăng nhập | Chuyển tới trang đăng nhập quản trị mặc định; không xem được quản trị trực tiếp | Chưa kiểm thử |
   | TC09 | Tắt server rồi chạy lại, tải trang chủ | Trang vẫn chạy; `migrate --check` vẫn thành công | Chưa kiểm thử |
   | TC10 | Kiểm tra nội dung trang và tài liệu thiết kế | Không có dữ liệu học tập giả được trình bày như dữ liệu thật; phạm vi mốc hiện tại được ghi rõ | Chưa kiểm thử |

6. **Kiểm tra Git trước khi push**

   Trong terminal thứ hai tại thư mục dự án:

   ```powershell
   git status --short
   git check-ignore .env .venv/Scripts/python.exe db.sqlite3
   git diff --check
   ```

   Mong đợi: các đường dẫn môi trường/database được ignore; `.env`, `.venv` và `db.sqlite3` không xuất hiện như file cần add. `git diff --check` không có lỗi whitespace. Cảnh báo LF/CRLF trên Windows không phải lỗi ứng dụng.

   Đọc [thiết kế ban đầu](docs/THIET_KE_BAN_DAU.md) và [kế hoạch](docs/KE_HOACH_PHAT_TRIEN.md), điền PASS/FAIL vào bảng thủ công trước khi commit. Giữ nguyên quy tắc trong `AGENTS.md`.

7. **Commit và push sau khi bạn xác nhận đạt**

   Nhánh hiện tại khi bắt đầu mốc này là `main`, remote là `origin`. Xem lại bằng `git branch --show-current` trước khi dùng lệnh push bên dưới; nếu bạn đã đổi nhánh thì thay `main` bằng nhánh muốn push.

   ```powershell
   git add .gitignore .env.example requirements.txt manage.py config core templates static docs HD_Test.md README.md AGENTS.md
   git diff --cached --stat
   git diff --cached --check
   git commit -m "feat: initialize Django project and local homepage"
   git push origin main
   ```

   Kiểm tra danh sách file đã stage trước commit. Không dùng `git add -f` để ép thêm file môi trường hoặc database. Agent chưa chạy lệnh stage, commit hay push ở mốc này.

8. **Kết quả kiểm tra kỹ thuật của agent**

   - Python chạy thực tế: `3.14.7`.
   - Django cài thực tế: `5.2.19`; các phiên bản được khóa trong `requirements.txt`.
   - `manage.py check`: PASS.
   - `manage.py migrate --noinput`: PASS, đã áp dụng migration mặc định Django.
   - `manage.py migrate --check` và `makemigrations --check --dry-run`: PASS, không thiếu migration và không có thay đổi model chưa lưu.
   - `pip check`: PASS, không có xung đột dependency.
   - Kiểm tra cú pháp Python bằng `compileall`: PASS.
   - HTTP thực tế: trang chủ 200, CSS 200, đường dẫn không tồn tại 404; `/admin/` chuyển tới đăng nhập quản trị.
   - Trình duyệt: giao diện desktop 1280 px; màn hình 375 px và 320 px không tràn ngang, bố cục một cột trên màn hình nhỏ.
   - Điều hướng tới phần cách sử dụng và trở lại trang chủ: PASS. Phím Tab đầu tiên làm hiện liên kết đến nội dung chính, có thể thao tác bằng bàn phím.
   - `.gitignore`: PASS cho `.env`, `.venv` và database. Kiểm tra whitespace: PASS.

   Kết quả trên là kiểm tra của agent; bảng thủ công vẫn giữ “Chưa kiểm thử” để bạn tự xác nhận. Server dùng cho kiểm tra đã được dừng khi bàn giao; chạy lệnh ở mục 4 để tự kiểm thử.

9. **Cách phản hồi để tiếp tục**

   Nếu đạt: báo mốc 01 đã PASS và đã push GitHub. Nếu lỗi: gửi ID test, thao tác, kết quả thực tế và thông báo lỗi terminal nếu có. Mốc tiếp theo là tài khoản và phân quyền; các lỗi của mốc 01 được sửa trước khi chuyển mốc.
