**Hướng dẫn kiểm thử theo từng mốc**

Sau mỗi mốc, người dùng kiểm thử, ghi nhận kết quả rồi commit/push GitHub. Chỉ chuyển mốc khi người dùng xác nhận. Khi có mốc mới, bổ sung vào tài liệu và giữ lịch sử các mốc cũ.

Mốc cần kiểm thử hiện tại: **mốc 10 — AI hỗ trợ từ dữ liệu học tập thực tế**, ở phần cuối tài liệu.

**Mốc 01 — Thiết kế và bộ khung Django chạy local**

Trạng thái: người dùng đã cho phép chuyển sang mốc 02. Giữ checklist và kết quả kỹ thuật bên dưới làm lịch sử của mốc 01.

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

---

**Mốc 02 — Tài khoản và phân quyền**

Trạng thái: người dùng đã cho phép chuyển sang mốc 03. Giữ các kết quả và checklist dưới đây làm lịch sử.

Phạm vi: đăng ký với username/email/mật khẩu; đăng nhập bằng username; đăng xuất; đổi mật khẩu; trang thông tin tài khoản riêng; giao diện điều hướng theo trạng thái đăng nhập; quản lý người dùng bằng Django Admin. Dùng User mặc định và cơ sở dữ liệu đang có; không đổi model User hoặc tạo lại database. Chưa có xác minh email, khôi phục mật khẩu qua email, sửa hồ sơ hay dữ liệu học tập.

1. **Chuẩn bị và chạy web**

   Trong PowerShell:

   ```powershell
   Set-Location -LiteralPath 'D:\Python_DuAnLapKeHoachHocTap'
   & .\.venv\Scripts\python.exe manage.py check
   & .\.venv\Scripts\python.exe manage.py migrate --check
   & .\.venv\Scripts\python.exe manage.py test accounts --noinput
   & .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
   ```

   Mong đợi: check không báo lỗi, không có migration còn thiếu, **16 tests / OK**. Các test tự tạo database trong bộ nhớ rồi hủy, không sửa dữ liệu của bạn ở `db.sqlite3`. Nếu clone mới chưa có database, chạy `manage.py migrate` trước `migrate --check`.

   Nếu server mốc 01 đang chạy, dừng bằng `Ctrl+C` rồi chạy lại để nạp module mới. Nếu cổng 8000 đang bận, chọn cổng khác và thay tương ứng trong các URL. Agent kiểm tra riêng ở cổng 8001 và dừng server đó trước khi bàn giao.

2. **Các URL để kiểm tra**

   | Trang | URL local |
   |---|---|
   | Trang chủ | http://127.0.0.1:8000/ |
   | Đăng ký | http://127.0.0.1:8000/accounts/register/ |
   | Đăng nhập | http://127.0.0.1:8000/accounts/login/ |
   | Thông tin tài khoản | http://127.0.0.1:8000/accounts/profile/ |
   | Đổi mật khẩu | http://127.0.0.1:8000/accounts/password-change/ |
   | Quản trị | http://127.0.0.1:8000/admin/ |

   `/accounts/logout/` chỉ nhận POST qua nút **Đăng xuất** trên giao diện. Mở URL đó trực tiếp bằng GET trả 405 là đúng.

3. **Chuẩn bị tài khoản kiểm thử của bạn**

   Đăng ký hai tài khoản khác nhau, chẳng hạn `sv_test_01` và `sv_test_02`, với email đúng định dạng. Tự chọn mật khẩu thử đáp ứng hướng dẫn trên form; không dùng mật khẩu của dịch vụ khác. Tên đăng nhập phải khác nhau; email ở mốc này chỉ dùng lưu hồ sơ, không gửi thư xác minh.

   Để kiểm tra quản trị, dùng superuser đã có hoặc mở terminal thứ hai để tạo:

   ```powershell
   & .\.venv\Scripts\python.exe manage.py createsuperuser
   ```

   Nhập username, email và mật khẩu khi được hỏi. Mật khẩu không hiển thị lúc gõ là bình thường. Không lưu mật khẩu thật vào tài liệu hay commit Git. Các tài khoản trong bộ test tự động chỉ tồn tại trong database test, không dùng chúng để đăng nhập bản local.

4. **Checklist thủ công**

   | ID | Thao tác | Kết quả mong đợi | Kết quả của bạn |
   |---|---|---|---|
   | M02-TC01 | Chưa đăng nhập, mở trang thông tin hoặc đổi mật khẩu | Chuyển tới đăng nhập, URL có `next` trỏ về trang đã yêu cầu | Chưa kiểm thử |
   | M02-TC02 | Đăng ký username mới, email hợp lệ và hai mật khẩu đủ mạnh giống nhau | Chuyển tới đăng nhập, có thông báo tạo tài khoản thành công; chưa tự đăng nhập | Chưa kiểm thử |
   | M02-TC03 | Đăng ký lại cùng username | Hiển thị lỗi ở tên đăng nhập; không tạo tài khoản thứ hai | Chưa kiểm thử |
   | M02-TC04 | Bỏ trống email hoặc nhập email sai định dạng | Trình duyệt hoặc form báo lỗi; không tạo tài khoản | Chưa kiểm thử |
   | M02-TC05 | Nhập hai mật khẩu khác nhau; thử mật khẩu ngắn/toàn số | Có lỗi tương ứng; không tạo tài khoản | Chưa kiểm thử |
   | M02-TC06 | Đăng nhập sai mật khẩu | Có lỗi đăng nhập; vẫn chưa truy cập được trang riêng | Chưa kiểm thử |
   | M02-TC07 | Đăng nhập đúng bằng username | Đến trang thông tin, hiển thị đúng username/email; vai trò Người dùng; có nút đổi mật khẩu và đăng xuất | Chưa kiểm thử |
   | M02-TC08 | Dùng hai cửa sổ thường/ẩn danh đăng nhập A và B; thêm `?user_id=ID_B` vào URL thông tin của A | Mỗi cửa sổ chỉ thấy tài khoản đang đăng nhập; query không đổi tài khoản được hiển thị | Chưa kiểm thử |
   | M02-TC09 | Đang đăng nhập, mở lại trang đăng ký hoặc đăng nhập | Chuyển về trang thông tin tài khoản | Chưa kiểm thử |
   | M02-TC10 | Đổi mật khẩu với mật khẩu cũ sai hoặc xác nhận mới không khớp | Có lỗi; mật khẩu cũ vẫn sử dụng được | Chưa kiểm thử |
   | M02-TC11 | Đổi mật khẩu hợp lệ, sau đó đăng xuất và thử lần lượt mật khẩu cũ/mới | Báo đổi thành công, phiên hiện tại vẫn đăng nhập; sau đăng xuất mật khẩu cũ bị từ chối, mật khẩu mới đăng nhập được | Chưa kiểm thử |
   | M02-TC12 | Bấm Đăng xuất rồi mở lại trang thông tin | Về trang chủ, menu hiện đăng nhập/đăng ký; trang riêng yêu cầu đăng nhập lại | Chưa kiểm thử |
   | M02-TC13 | Khi đã đăng xuất, mở `/accounts/login/?next=https://example.com/` rồi đăng nhập | Về trang thông tin nội bộ; không chuyển sang website bên ngoài | Chưa kiểm thử |
   | M02-TC14 | Đăng nhập người dùng thường, mở `/admin/` và `/admin/auth/user/` | Không xem được danh sách/tác vụ quản trị; chuyển tới đăng nhập quản trị | Chưa kiểm thử |
   | M02-TC15 | Đăng nhập superuser ở cửa sổ khác; mở danh sách người dùng, tìm và khóa/mở một tài khoản thử | Xem/tìm được user; khi khóa thì tài khoản bị từ chối, khi mở lại thì đăng nhập được | Chưa kiểm thử |
   | M02-TC16 | Đăng nhập cùng một tài khoản ở hai cửa sổ; đổi mật khẩu ở cửa sổ thứ nhất; tải lại trang riêng ở cửa sổ thứ hai | Cửa sổ thứ nhất vẫn đăng nhập; cửa sổ thứ hai phải đăng nhập lại bằng mật khẩu mới | Chưa kiểm thử |
   | M02-TC17 | Kiểm tra đăng ký/đăng nhập ở màn hình 375 px và 320 px, dùng Tab qua các ô/nút | Không tràn ngang; nhãn, lỗi và hướng dẫn đọc được; focus nhìn thấy | Chưa kiểm thử |
   | M02-TC18 | Mở trang chủ, dùng các liên kết cũ và kiểm tra CSS | Trang chủ và phần cách sử dụng vẫn hoạt động sau khi bổ sung menu tài khoản | Chưa kiểm thử |

   Cách khóa/mở trong Django Admin: vào **Người dùng**, chọn tài khoản thử, tại phần quyền bỏ/chọn ô **Kích hoạt** (`is_active`) rồi lưu. Không khóa chính superuser đang dùng. Tài khoản bị khóa cũng mất quyền truy cập ở phiên đã đăng nhập khi tải lại trang riêng.

   `is_staff` (nhãn **tình trạng nhân viên**) chỉ cho phép vào khu vực Admin; quyền xem/sửa user là quyền riêng. Superuser có đầy đủ quyền. Không cấp quyền quản trị cho tài khoản sinh viên để kiểm tra M02-TC14.

5. **Kiểm tra phương thức đăng xuất và CSRF, nếu muốn kiểm tra sâu hơn**

   Đang đăng nhập, mở `/accounts/logout/` bằng thanh địa chỉ: mong đợi 405 và phiên vẫn còn. Quay lại trang thông tin.

   Trong Console của DevTools tại trang đang đăng nhập, chạy:

   ```javascript
   fetch('/accounts/logout/', { method: 'POST' }).then(response => console.log(response.status))
   ```

   Mong đợi 403 vì không gửi CSRF token, phiên vẫn còn. Đăng xuất bằng nút giao diện phải thành công vì form có token. Bộ 16 test tự động cũng kiểm tra các POST đăng ký/đăng nhập/đổi mật khẩu/đăng xuất thiếu CSRF, cùng trường hợp login có token hợp lệ.

6. **Kết quả xác minh của agent**

   - `manage.py check`: PASS.
   - `manage.py test accounts --noinput`: **16/16 PASS**, dùng database test trong bộ nhớ.
   - Các nhóm đã kiểm tra: dữ liệu đăng ký sai; mật khẩu băm; không tự cấp quyền; login đúng/sai/tài khoản khóa; `next` an toàn; quyền trang riêng/quản trị; CSRF; đổi mật khẩu và phiên; khóa/mở user qua form Admin.
   - `makemigrations --check --dry-run` và `migrate --check`: PASS; không cần migration mới cho mốc này.
   - HTTP thực tế: trang chủ/đăng ký/đăng nhập/CSS trả 200; trang riêng và đổi mật khẩu yêu cầu đăng nhập; GET đăng xuất trả 405; POST thiếu CSRF trả 403.
   - Trình duyệt: đã kiểm tra đăng ký/đăng nhập ở desktop và màn hình 375/320 px; không tràn ngang; liên kết qua lại hoạt động; truy cập trang riêng khi chưa đăng nhập chuyển về login với `next` đúng.
   - Các tài khoản kiểm thử tự động không được tạo trong database local của bạn. Checklist thủ công vẫn chờ bạn điền PASS/FAIL.

7. **Commit/push sau khi kiểm thử đạt**

   ```powershell
   git status --short
   git diff --check
   git add accounts config/settings.py config/urls.py templates/base.html templates/accounts static/css/app.css HD_Test.md README.md docs/THIET_KE_BAN_DAU.md docs/KE_HOACH_PHAT_TRIEN.md
   git diff --cached --stat
   git diff --cached --check
   git commit -m "feat: add account authentication and permissions"
   git push origin main
   ```

   Lệnh push dùng nhánh `main` như khi bắt đầu mốc. Nếu bạn đã đổi nhánh thì thay bằng nhánh tương ứng. Xem file đã stage trước commit; `.env`, `.venv` và `db.sqlite3` tiếp tục bị ignore. Agent không chạy stage/commit/push thay bạn.

   Nếu có lỗi, gửi ID test cùng thao tác và kết quả thực tế. Khi bạn xác nhận mốc 02 đạt và đã push, mới thực hiện mốc tiếp theo.

---

**Mốc 03 — Quản lý môn học, công việc và tài liệu**

Trạng thái: người dùng đã cho phép chuyển sang mốc 04. Giữ kết quả và checklist mốc 03 làm lịch sử. PostgreSQL/triển khai online giữ cho mốc sau.

Phạm vi: môn học (màu, học kỳ, lưu trữ); công việc (deadline, ưu tiên, thời lượng, cho chia buổi, trạng thái); tài liệu dạng liên kết; thêm/sửa/xóa, tìm kiếm/lọc và quyền dữ liệu riêng. Chưa có lịch bận/lịch tuần, tự xếp lịch, nhắc việc, Pomodoro hay AI.

1. **Cập nhật database, chạy test và mở web**

   Mốc này có migration `studies/0001_initial.py` tạo ba bảng và constraint; không xóa hoặc thay model tài khoản. Agent đã áp dụng trên máy hiện tại, đồng thời tạo bản sao lưu cục bộ `db.sqlite3-before-m03` trước khi migrate. Database, bản sao lưu và môi trường ảo đều bị ignore, không push lên GitHub.

   Khi lấy mã về hoặc trước khi kiểm thử:

   ```powershell
   Set-Location -LiteralPath 'D:\Python_DuAnLapKeHoachHocTap'
   & .\.venv\Scripts\python.exe manage.py migrate
   & .\.venv\Scripts\python.exe manage.py check
   & .\.venv\Scripts\python.exe manage.py test accounts studies --noinput
   & .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
   ```

   Mong đợi: migration `studies.0001_initial` là OK hoặc không còn migration cần chạy; check không có lỗi; **37 tests / OK** (16 tài khoản + 21 học tập). Môi trường và thư viện giữ nguyên từ mốc 02. Nếu server đang chạy từ mốc cũ, dừng và chạy lại để nạp module mới.

   Kiểm thử tự động dùng database trong bộ nhớ. Kiểm tra trình duyệt của agent dùng database tạm riêng ở cổng 8001; dữ liệu mẫu đó không được thêm vào database của bạn. Server kiểm tra tạm được dừng khi bàn giao.

2. **Điểm vào và dữ liệu nên chuẩn bị**

   Đăng nhập bằng tài khoản mốc 02, chọn **Học tập** trên menu hoặc **Vào không gian học tập** từ trang tài khoản.

   | Trang | URL local |
   |---|---|
   | Môn học | http://127.0.0.1:8000/studies/subjects/ |
   | Công việc | http://127.0.0.1:8000/studies/tasks/ |
   | Tài liệu | http://127.0.0.1:8000/studies/materials/ |

   Dùng hai tài khoản A/B của bạn và hai cửa sổ thường/ẩn danh. Ở A tạo môn Python, một việc cần 180 phút có hạn trong tương lai và một liên kết tài liệu. Ở B tạo dữ liệu tên khác để kiểm tra quyền. Có thể tạo thêm một việc hạn hôm qua và một việc đã hoàn thành để kiểm tra bộ lọc.

3. **Checklist môn học và công việc**

   | ID | Thao tác | Kết quả mong đợi | Kết quả của bạn |
   |---|---|---|---|
   | M03-TC01 | Chưa đăng nhập, mở ba danh sách hoặc URL thêm/sửa/xóa | Chuyển tới đăng nhập; không xem được dữ liệu học tập | Chưa kiểm thử |
   | M03-TC02 | Thêm môn Python, học kỳ, chọn màu; sửa lại các thông tin | Lưu thành công; thẻ môn có tên/học kỳ/màu mới | Chưa kiểm thử |
   | M03-TC03 | Bỏ trống tên môn rồi lưu | Báo lỗi; không tạo môn rỗng | Chưa kiểm thử |
   | M03-TC04 | Sửa môn, chọn Lưu trữ; lọc Đã lưu trữ; bỏ lưu trữ lại | Môn ẩn khỏi Đang học, xuất hiện ở Đã lưu trữ; khôi phục được, các liên kết vẫn còn | Chưa kiểm thử |
   | M03-TC05 | Thêm việc cần 180 phút, ưu tiên cao, chọn môn, hạn 2 ngày tới và giờ cụ thể | Danh sách hiển thị đúng môn, ưu tiên, giờ Việt Nam; còn lại mặc định 180 phút | Chưa kiểm thử |
   | M03-TC06 | Nhập thời lượng ước tính 0, số âm hoặc bỏ trống | Trình duyệt/form báo lỗi; không tạo việc; không xuất hiện lỗi 500 | Chưa kiểm thử |
   | M03-TC07 | Sửa thời gian còn lại thành 120, trạng thái Đang thực hiện; sau đó tăng còn lại lên 240 | Lưu được các thay đổi; cho phép công việc phát sinh vượt ước tính | Chưa kiểm thử |
   | M03-TC08 | Chọn Hoàn thành trong form sửa, giữ nguyên số phút đang có rồi lưu | Trạng thái Hoàn thành, còn lại tự về 0 | Chưa kiểm thử |
   | M03-TC09 | Mở lại việc hoàn thành, chuyển Chưa bắt đầu/Đang thực hiện nhưng vẫn để còn lại 0 | Báo cần thời lượng dương; nhập 30 phút rồi lưu thì mở lại được | Chưa kiểm thử |
   | M03-TC10 | Tạo việc có hạn hôm qua; lọc Quá hạn; hoàn thành việc đó rồi lọc lại | Việc chưa xong có nhãn Quá hạn; việc đã hoàn thành không nằm trong Quá hạn | Chưa kiểm thử |
   | M03-TC11 | Kết hợp từ khóa, môn, ưu tiên và trạng thái rồi bấm Lọc; bấm Xóa bộ lọc | Kết quả đáp ứng đồng thời các điều kiện; xóa bộ lọc trả về danh sách đầy đủ của mình | Chưa kiểm thử |
   | M03-TC12 | Bật/tắt Cho phép chia thành nhiều buổi rồi lưu | Danh sách thể hiện Có thể chia buổi hoặc Làm liên tục; chưa sinh lịch tự động | Chưa kiểm thử |

4. **Checklist tài liệu, xóa và quyền sở hữu**

   | ID | Thao tác | Kết quả mong đợi | Kết quả của bạn |
   |---|---|---|---|
   | M03-TC13 | Thêm tài liệu có tên, URL HTTPS, chọn môn và/hoặc công việc; sửa ghi chú | Lưu được; hiển thị đúng các liên kết và ghi chú | Chưa kiểm thử |
   | M03-TC14 | Bấm Mở tài liệu | Mở đường dẫn ở tab mới; trang Nhịp Học vẫn giữ nguyên | Chưa kiểm thử |
   | M03-TC15 | Nhập URL sai định dạng hoặc dùng `javascript:`/`ftp:` | Trình duyệt/form từ chối; chỉ nhận HTTP/HTTPS | Chưa kiểm thử |
   | M03-TC16 | Tìm tài liệu theo từ khóa, môn và công việc | Chỉ hiện tài liệu phù hợp của người đang đăng nhập | Chưa kiểm thử |
   | M03-TC17 | Bấm Xóa ở một đối tượng rồi chọn Hủy, giữ lại | Có trang xác nhận và cảnh báo đúng loại; chỉ mở trang xóa không xóa dữ liệu | Chưa kiểm thử |
   | M03-TC18 | Xác nhận xóa một môn thử có công việc/tài liệu | Chỉ môn bị xóa; công việc và tài liệu còn, liên kết môn được bỏ trống | Chưa kiểm thử |
   | M03-TC19 | Xác nhận xóa một công việc thử có tài liệu | Công việc bị xóa; tài liệu còn, không còn gắn công việc; liên kết môn của tài liệu vẫn giữ nếu môn còn | Chưa kiểm thử |
   | M03-TC20 | Xóa một liên kết tài liệu thử | Chỉ liên kết trong Nhịp Học bị xóa; môn/công việc và tệp ở website gốc không bị tác động | Chưa kiểm thử |
   | M03-TC21 | Ở B sao chép URL sửa/xóa một đối tượng, mở URL đó trong cửa sổ A | Trả 404; không thấy dữ liệu B, không sửa/xóa được | Chưa kiểm thử |
   | M03-TC22 | Ở A mở danh sách và các ô chọn môn/công việc trong form | Không có dữ liệu B trong danh sách hoặc lựa chọn liên kết | Chưa kiểm thử |
   | M03-TC23 | Thay ID môn/công việc trong URL bộ lọc bằng ID thuộc B hoặc chuỗi không hợp lệ | Báo lựa chọn không hợp lệ, danh sách trống; không lộ dữ liệu và không lỗi 500 | Chưa kiểm thử |
   | M03-TC24 | Thu hẹp màn hình 375/320 px; dùng Tab qua bộ lọc và form | Không cuộn ngang cả trang; các ô dùng được; focus rõ ràng | Chưa kiểm thử |
   | M03-TC25 | Khởi động lại server, đăng nhập và mở lại dữ liệu đã tạo | Dữ liệu vẫn được lưu; đăng nhập/đăng xuất/đổi mật khẩu của mốc 02 vẫn hoạt động | Chưa kiểm thử |

   Để kiểm tra URL bộ lọc, có thể dùng `/studies/tasks/?subject=ID_B` hoặc `/studies/materials/?task=ID_B`. ID thật lấy từ URL sửa của đối tượng bên B; không cần đoán. URL với ID người khác trả 404 ở trang sửa/xóa là hành vi bảo vệ quyền.

   Xóa chỉ thực hiện trên dữ liệu thử bạn đồng ý bỏ. Nếu muốn ẩn môn và giữ nguyên các liên kết, dùng Lưu trữ. Môn đã lưu trữ vẫn có thể được chọn khi quản lý công việc/tài liệu; việc lưu trữ chỉ thay đổi danh sách môn đang học.

5. **Kết quả xác minh của agent**

   - `manage.py check`: PASS.
   - `manage.py test accounts studies --noinput`: **37/37 PASS**, bao gồm các kiểm thử tài khoản cũ.
   - `makemigrations --check --dry-run` và `migrate --check`: PASS; migration mới đã được tạo và áp dụng.
   - Đã kiểm tra tạo/cập nhật/xóa, archive/khôi phục, thời lượng sai, hoàn thành/mở lại, deadline theo múi giờ Việt Nam, lọc quá hạn, tìm kiếm kết hợp, URL tài liệu, quan hệ liên kết và dữ liệu còn lại sau xóa.
   - Đã kiểm tra GET/POST với ID người khác bị từ chối; owner giả trong POST bị bỏ qua; không gắn được môn/công việc của người khác; CSRF bảo vệ các thao tác ghi; constraint database chặn dữ liệu thời lượng/ưu tiên/trạng thái mâu thuẫn.
   - Trình duyệt trên database tạm: đăng nhập → tạo môn → tạo việc → thêm tài liệu liên quan → sửa số phút còn lại/trạng thái → lọc kết hợp thành công. Biểu mẫu/danh sách ở 320/375 px không tràn ngang.
   - Dữ liệu trong ảnh kiểm tra là dữ liệu mẫu trên database tạm, không phải dữ liệu được thêm vào tài khoản của bạn.

6. **Commit và push sau khi bạn kiểm thử đạt**

   ```powershell
   git status --short
   git diff --check
   git check-ignore .env .venv/Scripts/python.exe db.sqlite3 db.sqlite3-before-m03
   git add studies config/settings.py config/urls.py templates/base.html templates/accounts/profile.html templates/core/home.html templates/studies static/css/studies.css README.md HD_Test.md docs/KE_HOACH_PHAT_TRIEN.md docs/THIET_KE_BAN_DAU.md
   git diff --cached --stat
   git diff --cached --check
   git commit -m "feat: manage subjects tasks and study materials"
   git push origin main
   ```

   Giữ file migration `studies/migrations/0001_initial.py` trong commit. Không thêm database, bản sao lưu hoặc `.env`. Nhánh khi bắt đầu mốc là `main`; nếu bạn đã đổi nhánh thì thay tên nhánh khi push. Agent không stage/commit/push thay bạn.

   Khi có lỗi, gửi ID test, thao tác và kết quả thực tế. Chỉ tiếp tục mốc sau khi bạn xác nhận mốc 03 đạt và đã push GitHub. Mốc 04 dự kiến làm lịch bận, tùy chọn học và lịch tuần.

---

**Mốc 04 — Lịch bận, tùy chọn học và lịch tuần**

Trạng thái: người dùng đã cho phép chuyển sang mốc 05. Giữ kết quả và checklist mốc 04 làm lịch sử.

Phạm vi: tạo/sửa/xóa lịch bận một lần hoặc lặp hằng tuần, ca qua đêm; lưu các ngày được học và một khung giờ học chung; giới hạn phút/ngày, độ dài buổi mong muốn và thời gian nghỉ. Lịch tuần từ thứ Hai đến Chủ nhật hiển thị lịch bận, deadline và các khoảng trống từ hiện tại. Chưa tự sinh hoặc lưu buổi tự học; đó là mốc 05.

1. **Cập nhật database và chạy**

   Mốc này có migration `planner/0001_initial.py`, tạo hai bảng mới, không xóa dữ liệu các mốc trước. Agent đã tạo bản sao lưu cục bộ `db.sqlite3-before-m04` trước khi áp dụng migration trên máy hiện tại. File database và bản sao lưu bị ignore.

   ```powershell
   Set-Location -LiteralPath 'D:\Python_DuAnLapKeHoachHocTap'
   & .\.venv\Scripts\python.exe manage.py migrate
   & .\.venv\Scripts\python.exe manage.py check
   & .\.venv\Scripts\python.exe manage.py test accounts studies planner --noinput
   & .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
   ```

   Mong đợi: migration mới là OK hoặc không còn migration cần áp dụng; check không có lỗi; **60 tests / OK** (37 cũ + 23 mới). Không cần cài thêm thư viện. Nếu server cũ đang chạy, dừng và chạy lại để nạp module planner.

   Các kiểm thử tự động dùng database trong bộ nhớ. Kiểm tra trình duyệt dùng database tạm cùng cookie riêng trên cổng 8001, không thêm lịch mẫu vào tài khoản/database của bạn. Server kiểm tra tạm được dừng trước khi bàn giao.

2. **URL và dữ liệu mẫu tự nhập**

   Đăng nhập, chọn **Lịch tuần** trên menu:

   | Trang | URL |
   |---|---|
   | Lịch tuần | http://127.0.0.1:8000/planner/ |
   | Danh sách lịch bận | http://127.0.0.1:8000/planner/busy/ |
   | Thêm lịch bận | http://127.0.0.1:8000/planner/busy/add/ |
   | Giờ học | http://127.0.0.1:8000/planner/preferences/ |

   Chọn một tuần tương lai, ký hiệu ngày thứ Hai là D. Trong Giờ học, chọn thứ Hai/Tư/Sáu, khung 18:00–22:00, tối đa 120 phút/ngày, buổi mong muốn 50 phút, nghỉ 10 phút.

   Tạo lịch **Lớp Python** vào D, 19:00–20:00, lặp hằng tuần tới D+14 ngày. Thêm **Ca qua đêm** từ thứ Ba 22:00 đến thứ Tư 02:00, một lần. Từ phần Học tập, tạo công việc có deadline thứ Tư 21:00 cùng tuần. Dùng A/B ở hai cửa sổ để kiểm tra quyền dữ liệu.

3. **Checklist lịch bận**

   | ID | Thao tác | Kết quả mong đợi | Kết quả của bạn |
   |---|---|---|---|
   | M04-TC01 | Chưa đăng nhập, mở lịch tuần, giờ học hoặc URL lịch bận | Chuyển tới đăng nhập; không xem được dữ liệu | Chưa kiểm thử |
   | M04-TC02 | Thêm lịch bận một lần rồi mở tuần tương ứng | Hiển thị đúng ngày và giờ Việt Nam; tuần khác không lặp lại | Chưa kiểm thử |
   | M04-TC03 | Tạo Lớp Python theo mẫu, xem D, D+7 và D+14 | Đúng thứ Hai 19:00–20:00 ở cả ba tuần; không xuất hiện trước D hoặc ở D+21 | Chưa kiểm thử |
   | M04-TC04 | Tạo lịch lặp không có ngày dừng, xem một tuần xa hơn | Lịch vẫn hiện đúng thứ/giờ; không cần lưu hàng loạt bản ghi lặp | Chưa kiểm thử |
   | M04-TC05 | Tạo Ca qua đêm theo mẫu | Thứ Ba hiện 22:00–24:00, thứ Tư hiện 00:00–02:00 | Chưa kiểm thử |
   | M04-TC06 | Tạo ca Chủ nhật 22:00 → thứ Hai 02:00, xem tuần bắt đầu thứ Hai | Phần 00:00–02:00 vẫn hiện dù ca bắt đầu ở tuần trước | Chưa kiểm thử |
   | M04-TC07 | Nhập kết thúc bằng/trước bắt đầu; lịch lặp dài từ 7 ngày; ngày dừng trước lần đầu | Form báo lỗi, không tạo lịch sai và không lỗi 500 | Chưa kiểm thử |
   | M04-TC08 | Sửa tên/giờ lịch lặp, sau đó bỏ Lặp hằng tuần rồi lưu | Thay đổi áp dụng cho cả chuỗi; bỏ lặp chuyển thành một lần và xóa ngày dừng chuỗi đã lưu | Chưa kiểm thử |
   | M04-TC09 | Mở trang Xóa rồi Hủy; sau đó xóa một lịch thử | Mở trang không xóa ngay; xác nhận xóa gỡ lịch/chuỗi, không xóa công việc hoặc tài liệu | Chưa kiểm thử |
   | M04-TC10 | Ở A mở URL sửa/xóa lịch lấy từ tài khoản B | Trả 404; dữ liệu B giữ nguyên | Chưa kiểm thử |

   Một lịch lặp dùng đúng thứ của lần đầu; bận nhiều thứ thì nhập các lịch riêng. Với ca qua đêm, ngày dừng xét ngày bắt đầu mỗi lần, nên phần kết thúc có thể sang ngày hôm sau. Sửa/xóa tác động toàn chuỗi, chưa hỗ trợ ngoại lệ riêng từng lần.

4. **Checklist giờ học và tính khoảng trống**

   | ID | Thao tác | Kết quả mong đợi | Kết quả của bạn |
   |---|---|---|---|
   | M04-TC11 | Tài khoản chưa lưu Giờ học, mở/xem lại lịch và tùy chọn | Dùng mặc định 08:00–22:00, tất cả ngày, 240 phút/ngày, buổi 50, nghỉ 10; chỉ xem không tự ghi tùy chọn | Chưa kiểm thử |
   | M04-TC12 | Lưu tùy chọn theo dữ liệu mẫu; tải lại | Giữ đúng thứ Hai/Tư/Sáu, giờ và số phút; ngày không chọn không có khoảng trống | Chưa kiểm thử |
   | M04-TC13 | Mở Khoảng trống ở thứ Hai D có Lớp Python 19:00–20:00 | Có 18:00–19:00 (60 phút), 20:00–22:00 (120 phút); quỹ bố trí tối đa vẫn là 120 phút/ngày | Chưa kiểm thử |
   | M04-TC14 | Thêm lịch bận chồng 19:30–20:30 ở D | Khoảng bận gộp thành 19:00–20:30; còn 18:00–19:00 và 20:30–22:00, tổng 150 phút, không trừ hai lần | Chưa kiểm thử |
   | M04-TC15 | Tạo hai lịch tiếp nhau 18:00–19:00 và 19:00–20:00 | Không có khoảng trống giả ở 19:00; phần trống tiếp theo từ 20:00 | Chưa kiểm thử |
   | M04-TC16 | Bỏ chọn tất cả ngày rồi lưu | Lưu được; không có khoảng trống, lịch bận và deadline vẫn hiển thị | Chưa kiểm thử |
   | M04-TC17 | Nhập khung kết thúc ≤ bắt đầu, giới hạn/buổi bằng 0, phút nghỉ âm hoặc số phút >1440 | Form từ chối và hiển thị lỗi; cấu hình cũ không bị thay | Chưa kiểm thử |
   | M04-TC18 | Nhập độ dài buổi lớn hơn giới hạn ngày hoặc dài hơn toàn khung học | Báo lỗi ở độ dài buổi | Chưa kiểm thử |
   | M04-TC19 | Xem tuần đã qua và ngày hiện tại | Ngày đã qua không có khoảng trống tương lai; hôm nay không đưa ra giờ trước hiện tại | Chưa kiểm thử |
   | M04-TC20 | A/B lưu tùy chọn khác nhau; đổi cửa sổ và tải lại | Mỗi người giữ tùy chọn riêng; không đổi được tùy chọn B bằng query/owner giả | Chưa kiểm thử |

   Khung học hiện dùng chung cho các ngày đã chọn và nằm trong cùng ngày; ca qua đêm được hỗ trợ ở Lịch bận. Quỹ phút là giới hạn trên theo khoảng trống và mức tối đa mỗi ngày. Độ dài buổi/thời gian nghỉ được lưu để dùng ở mốc tự xếp lịch; chưa có buổi tự học nên không khấu trừ nghỉ giữa các buổi trong quỹ này.

5. **Checklist lịch tuần và hồi quy**

   | ID | Thao tác | Kết quả mong đợi | Kết quả của bạn |
   |---|---|---|---|
   | M04-TC21 | Chọn một ngày giữa tuần, bấm Xem tuần; dùng Tuần trước/Tuần sau/Tuần này | Luôn hiện thứ Hai–Chủ nhật, ngày và liên kết điều hướng đúng | Chưa kiểm thử |
   | M04-TC22 | Xem công việc có deadline thứ Tư 21:00; đánh dấu hoàn thành rồi xem lại | Mốc hạn hiện đúng 21:00, đổi nhãn hoàn thành; không bị tính là khoảng bận | Chưa kiểm thử |
   | M04-TC23 | A/B có lịch bận và deadline tên khác nhau | Lịch tuần, danh sách lịch bận chỉ hiện dữ liệu của người đang đăng nhập | Chưa kiểm thử |
   | M04-TC24 | Mở `/planner/?week=bad-date` hoặc ngày không hợp lệ | Có lỗi ở ô chọn ngày, không lỗi 500 hoặc lộ dữ liệu | Chưa kiểm thử |
   | M04-TC25 | Xem lịch và Giờ học ở 375/320 px; dùng Tab, mở Khoảng trống | Không tràn ngang; lịch chuyển thành các ngày xếp một cột; các ô/nút và mục mở rộng dùng được | Chưa kiểm thử |
   | M04-TC26 | Khởi động lại server và xem lại; kiểm tra tài khoản/môn/công việc/tài liệu | Lịch và tùy chọn còn nguyên; chức năng các mốc cũ vẫn dùng được | Chưa kiểm thử |

   Native date/time picker có thể hiển thị định dạng theo ngôn ngữ trình duyệt. Nội dung lịch dùng ngày/tháng và giờ Việt Nam. Chọn tuần tương lai để kiểm tra khoảng trống đầy đủ, vì các giờ đã qua được bỏ khỏi kết quả.

6. **Kết quả xác minh của agent**

   - `manage.py check`: PASS; `manage.py test accounts studies planner --noinput`: **60/60 PASS**.
   - 23 kiểm thử mới bao phủ lịch một lần/lặp, trước lần đầu, ngày dừng tính bao gồm, ca qua đêm qua ranh giới tuần, lịch nhiều ngày, trừ hợp khoảng bận, ngày được học, giới hạn ngày và loại thời gian đã qua.
   - Đã kiểm tra ranh giới deadline/tuần, công việc hoàn thành, ngày chọn sai, mặc định không ghi dữ liệu qua GET, CRUD, owner giả, quyền A/B, CSRF và constraint database.
   - Migration `planner.0001_initial` đã áp dụng; `makemigrations --check --dry-run` và `migrate --check`: PASS.
   - Trình duyệt với database/cookie riêng: lưu tùy chọn → tạo lịch lặp → ca qua đêm → xem deadline/khoảng trống → chuyển tuần và chọn ngày thành công.
   - Đã kiểm tra lịch ở 375 px và biểu mẫu ở 320 px không tràn ngang; điều hướng bàn phím tới nội dung chính hoạt động. Các dữ liệu mẫu không được thêm vào database của bạn.

7. **Commit/push sau khi bạn kiểm thử đạt**

   ```powershell
   git status --short
   git diff --check
   git check-ignore .env .venv/Scripts/python.exe db.sqlite3 db.sqlite3-before-m04
   git add planner config/settings.py config/urls.py templates/base.html templates/planner static/css/planner.css README.md HD_Test.md docs/KE_HOACH_PHAT_TRIEN.md docs/THIET_KE_BAN_DAU.md
   git diff --cached --stat
   git diff --cached --check
   git commit -m "feat: add busy schedules study preferences and weekly calendar"
   git push origin main
   ```

   Giữ migration trong commit; không đưa database/bản sao lưu/`.env` lên GitHub. Nhánh khi bắt đầu mốc là `main`; nếu bạn đổi nhánh thì thay tên khi push. Agent không stage/commit/push thay bạn.

   Gửi ID test và kết quả thực tế nếu có lỗi. Sau khi bạn xác nhận mốc 04 đạt và đã push, mốc 05 mới triển khai thuật toán tự xếp lịch.

---

**Mốc 05 — Tự sinh kế hoạch tuần, xem trước và áp dụng**

Trạng thái: người dùng đã cho phép chuyển sang mốc 06. Giữ checklist và kết quả mốc 05 làm lịch sử.

Phạm vi: thuật toán Python xếp deadline gần trước, cùng hạn thì ưu tiên cao trước; chia buổi, chừa nghỉ, tôn trọng ngày/khung học, quỹ ngày và lịch bận. Có bản xem trước, báo cáo phút chưa bố trí theo công việc, áp dụng lên lịch và danh sách 10 kế hoạch gần nhất. Phần chỉnh/khóa/hủy buổi, tự xếp lại và theo dõi học thực tế thuộc mốc tiếp theo.

1. **Khởi động và kiểm tra kỹ thuật**

   Nếu server cũ đang chạy, dừng bằng Ctrl+C trong terminal của server rồi chạy lại:

   ```powershell
   Set-Location -LiteralPath 'D:\Python_DuAnLapKeHoachHocTap'
   & .\.venv\Scripts\python.exe manage.py migrate
   & .\.venv\Scripts\python.exe manage.py check
   & .\.venv\Scripts\python.exe manage.py test accounts studies planner --noinput
   & .\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
   & .\.venv\Scripts\python.exe manage.py migrate --check
   & .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
   ```

   Mong đợi: **90/90 tests PASS**, không có migration thiếu, không có lỗi system check. Không thêm thư viện mới. Agent đã dùng SQLite backup tạo `db.sqlite3-before-m05` trước khi áp dụng `planner.0002_studyplan_studysession` trên máy này; không ghi đè bản sao lưu cũ. Các kiểm thử tự động dùng database riêng. Không xóa database đang dùng để chạy lại test.

   Đường dẫn chính:

   - Tạo/xem các kế hoạch gần đây: `http://127.0.0.1:8000/planner/plans/new/`.
   - Chi tiết kế hoạch: `/planner/plans/<id>/`.
   - Áp dụng: POST `/planner/plans/<id>/apply/`, dùng nút có CSRF trên giao diện.
   - Lịch tuần: `/planner/?week=YYYY-MM-DD`; tuần luôn được chuẩn hóa về thứ Hai.

2. **Dữ liệu mẫu để đối chiếu chính xác**

   Đăng ký tài khoản thử A riêng để không có lịch/công việc cũ ảnh hưởng. Dùng tài khoản B riêng cho ca phân quyền. Không dùng dữ liệu học thật cho ca xóa hoặc thay đổi deadline.

   Gọi **D** là thứ Hai của một tuần tương lai. Ví dụ tại ngày viết hướng dẫn: D = 16/11/2026; nếu đã qua, chọn thứ Hai mới. Giờ nhập theo Việt Nam.

   - Giờ học: thứ Hai, thứ Ba, thứ Tư; 18:00–22:00; tối đa 120 phút/ngày; buổi mong muốn 50 phút; nghỉ 10 phút.
   - Lịch bận: **Lớp Python**, thứ Hai D 19:00–20:00, lặp hằng tuần.
   - Các công việc đều Chưa bắt đầu, chưa có buổi học đã áp dụng:

   | Tên | Ước tính/còn lại | Deadline | Ưu tiên | Chia buổi |
   |---|---|---|---|---|
   | Bài tập Python | 120 phút | D 22:00 | Cao | Có |
   | Ôn thi cuối kỳ | 300 phút | D+2 ngày 22:00 | Trung bình | Có |
   | Bài thực hành liên tục | 180 phút | D+2 ngày 22:00 | Thấp | Không |

   Ở Tạo kế hoạch, chọn một ngày trong tuần D rồi bấm **Tạo bản xem trước**. Kết quả dự kiến **9 buổi, 360 phút, 240 phút chưa bố trí**:

   | Ngày | Công việc | Các buổi đề xuất | Tổng |
   |---|---|---|---|
   | Thứ Hai D | Bài tập Python | 18:00–18:50; 20:00–20:50; 21:00–21:20 | 120 phút |
   | Thứ Ba D+1 | Ôn thi cuối kỳ | 18:00–18:50; 19:00–19:50; 20:00–20:20 | 120 phút |
   | Thứ Tư D+2 | Ôn thi cuối kỳ | 18:00–18:50; 19:00–19:50; 20:00–20:20 | 120 phút |

   Báo cáo: Bài tập Python đủ 120 phút; Ôn thi còn thiếu 60 phút; Bài thực hành liên tục thiếu 180 phút vì không có quỹ ngày đủ cho một buổi liên tục. Nghỉ không tính vào phút học. Hai buổi có thể cách nhau bằng đúng số phút nghỉ yêu cầu.

3. **Checklist luồng chính — chạy theo thứ tự trên bộ mẫu**

   | ID | Thao tác | Kết quả mong đợi | Kết quả của bạn |
   |---|---|---|---|
   | M05-TC01 | Chưa đăng nhập, mở Tạo kế hoạch hoặc URL chi tiết | Chuyển sang Đăng nhập; không lộ kế hoạch | Chưa kiểm thử |
   | M05-TC02 | Đăng nhập A, mở Tạo kế hoạch rồi tải lại trước khi bấm tạo | Không tự tạo bản xem trước hoặc ghi tùy chọn | Chưa kiểm thử |
   | M05-TC03 | Chọn thứ Tư D+2, bấm Tạo bản xem trước | Chuẩn hóa về thứ Hai D; đúng 9 buổi/360 phút/thiếu 240 như mẫu | Chưa kiểm thử |
   | M05-TC04 | Đọc danh sách và báo cáo từng việc | Không đè Lớp Python; không vượt deadline, 120 phút/ngày; buổi cuối 20 phút; báo đúng thiếu 60 và 180 | Chưa kiểm thử |
   | M05-TC05 | Từ bản xem trước bấm Xem lịch tuần, chưa áp dụng | Chỉ có lịch bận/deadline, chưa có buổi tự học; tối đa vẫn 120 phút/ngày | Chưa kiểm thử |
   | M05-TC06 | Quay lại bản xem trước và bấm Áp dụng vào lịch tuần | Chuyển về đúng tuần D, thông báo thành công, 9 buổi hiện màu xanh; quỹ bố trí thêm bằng 0 ở ba ngày | Chưa kiểm thử |
   | M05-TC07 | Mở khoảng trống thứ Hai sau áp dụng | Có 21:30–22:00; dù còn trống 30 phút nhưng quỹ ngày đã hết nên không bố trí thêm | Chưa kiểm thử |
   | M05-TC08 | Mở công việc sau áp dụng; xem lại bản đã áp dụng | Còn lại vẫn 120/300/180, chưa tự đánh dấu xong; bản đã áp dụng không còn nút áp dụng | Chưa kiểm thử |
   | M05-TC09 | Tạo bản xem trước mới cùng tuần D, không sửa dữ liệu | 0 buổi mới; báo đã có lịch tương lai 120/240/0; phần thiếu vẫn 0/60/180, không nhân đôi buổi | Chưa kiểm thử |
   | M05-TC10 | Xem 10 kế hoạch gần nhất, mở các bản vừa tạo | Bản mới nhất đứng trước, đúng nhãn xem trước/đã áp dụng; tài khoản B không thấy bản A | Chưa kiểm thử |

4. **Checklist thay đổi đầu vào và áp dụng**

   | ID | Thao tác | Kết quả mong đợi | Kết quả của bạn |
   |---|---|---|---|
   | M05-TC11 | Sau TC09 tăng tối đa ngày lên 180, giữ nghỉ 10; tạo bản mới tuần D | Thêm 60 phút cho Ôn thi: thứ Hai 21:30–22:00 và thứ Ba 20:30–21:00; Bài tập Python không được xếp lại | Chưa kiểm thử |
   | M05-TC12 | Chưa áp dụng bản TC11, đổi nghỉ từ 10 thành 15; trở về bản đó và bấm Áp dụng | Hiện lỗi yêu cầu tạo bản mới, không thêm hai buổi cũ vào lịch, bản vẫn là xem trước | Chưa kiểm thử |
   | M05-TC13 | Tạo bản mới; sửa deadline/thời lượng công việc hoặc thêm/sửa lịch bận; thử áp dụng bản vừa tạo | Từ chối bản cũ, giữ nguyên lịch đã áp dụng trước đó; không áp dụng một phần | Chưa kiểm thử |
   | M05-TC14 | Với dữ liệu có thể xếp thêm buổi, tạo hai bản cùng đầu vào; áp dụng bản thứ nhất rồi thử bản thứ hai | Bản thứ hai bị từ chối; lịch không chứa hai bộ buổi giống nhau | Chưa kiểm thử |
   | M05-TC15 | B mở URL chi tiết của A hoặc gửi POST vào URL áp dụng của A | 404; kế hoạch của A không đổi. Có test tự động cho POST giả owner và CSRF | Chưa kiểm thử |
   | M05-TC16 | Nhập ngày không hợp lệ hoặc tuần đã qua vào form; mở trực tiếp URL áp dụng bằng GET | Form báo lỗi ngày/tuần; GET áp dụng trả 405, không tạo buổi | Chưa kiểm thử |

   Gửi lặp lại POST cho cùng bản đã áp dụng chỉ thông báo đã áp dụng, không tạo thêm bản ghi; đã có test tự động. Với tuần hiện tại, nếu giờ đề xuất đã bắt đầu trôi qua trước khi áp dụng, phải tạo bản mới. Ở tuần tương lai, chờ vài phút không tự làm bản mất hiệu lực nếu kết quả xếp vẫn giữ nguyên.

5. **Checklist ràng buộc — mỗi ca dùng bộ dữ liệu thử độc lập**

   Các ca sau nên dùng tài khoản thử riêng hoặc tuần/công việc chưa có buổi áp dụng; các buổi cũ luôn giữ chỗ. Không cần xóa dữ liệu thật để đạt kết quả.

   | ID | Thao tác | Kết quả mong đợi | Kết quả của bạn |
   |---|---|---|---|
   | M05-TC17 | Chỉ có việc liên tục 90 phút, khung 18:00–22:00, quỹ 120, buổi mong muốn 50 | Một buổi 18:00–19:30; không tự chia thành 50+40 | Chưa kiểm thử |
   | M05-TC18 | Việc liên tục 90 phút nhưng lịch bận chỉ chừa các đoạn rời 60 phút | Không xếp; báo không có khoảng liên tục đủ dài. Đổi Cho phép chia thì xếp theo các đoạn và nghỉ | Chưa kiểm thử |
   | M05-TC19 | Hai việc cùng deadline tranh quỹ ngày 60 phút, ưu tiên khác nhau | Việc ưu tiên cao được xếp trước; việc còn lại được báo phần thiếu | Chưa kiểm thử |
   | M05-TC20 | Việc 120 phút nhưng deadline lúc 18:30, khung bắt đầu 18:00 | Chỉ xếp 18:00–18:30, thiếu 90 phút; không đặt sau hạn | Chưa kiểm thử |
   | M05-TC21 | Bỏ chọn toàn bộ ngày, hoặc tạo tài khoản chưa có việc; tạo xem trước | Không lỗi; 0 buổi, không có nút áp dụng; có báo thiếu hoặc lời nhắc thêm công việc | Chưa kiểm thử |
   | M05-TC22 | Có việc đã hoàn thành và việc quá hạn | Việc hoàn thành không tham gia phân bổ; việc quá hạn được báo, không có buổi trong quá khứ | Chưa kiểm thử |
   | M05-TC23 | Chọn tuần hiện tại với giờ học còn lại; thêm ca qua đêm/lịch lặp | Không xếp trước hiện tại hoặc đè ca; giây lẻ được làm tròn lên phút kế tiếp | Chưa kiểm thử |
   | M05-TC24 | Việc có deadline sau hai tuần, đã áp dụng một phần ở tuần sau; tạo bản ở tuần trước | Trừ phần phút tương lai đã có lịch ở tuần sau, không phân bổ đủ lượng công việc hai lần | Chưa kiểm thử |
   | M05-TC25 | Việc lớn, deadline sau tuần được chọn, quỹ tuần không đủ | Báo phần thiếu trong tuần này và khả năng cần thêm tuần sau; không tự kết luận việc đã quá hạn | Chưa kiểm thử |
   | M05-TC26 | Chỉ trên việc thử: mở trang Xóa rồi Hủy; sau đó xác nhận xóa việc có buổi học | Trang nêu rõ sẽ xóa cả buổi; Hủy giữ dữ liệu; xác nhận gỡ buổi khỏi lịch nhưng giữ tài liệu với liên kết việc rỗng | Chưa kiểm thử |
   | M05-TC27 | Xem form tạo kế hoạch, danh sách buổi/báo cáo ở 375/320 px và dùng Tab | Không tràn ngang; nội dung/nút đọc được, thao tác bàn phím dùng được | Chưa kiểm thử |
   | M05-TC28 | Khởi động lại server, xem lại kế hoạch và thử chức năng mốc 02–04 | Bản áp dụng còn nguyên, chỉ hiện dữ liệu người đang đăng nhập; tài khoản/môn/tài liệu/lịch bận vẫn dùng được | Chưa kiểm thử |

6. **Quy tắc và giới hạn cần hiểu khi đánh giá**

   - Thuật toán tham lam, chưa chứng minh tối ưu toàn cục. Ưu tiên cao chỉ quyết định khi deadline bằng nhau; deadline gần luôn được xét trước.
   - Buổi chia nhỏ có thể ngắn hơn độ dài mong muốn, tối thiểu một phút. Không đặt buổi liên tục vượt quỹ ngày.
   - Nghỉ áp dụng giữa các buổi tự học; lịch bận không mặc định cần thêm một khoảng nghỉ. Nghỉ được chừa quanh buổi đã áp dụng, kể cả qua ngày/tuần.
   - Các buổi đã qua không tự chứng minh đã học xong. Hãy cập nhật thời lượng còn lại theo thực tế. Buổi đang diễn ra chỉ được tính phần nguyên phút chưa qua vào thời gian đã có lịch tương lai. Buổi đã qua trong ngày vẫn tiêu quỹ học của ngày đó.
   - Thêm bản mới là bổ sung, giữ mọi buổi đã áp dụng. Chưa có sửa/khóa/hủy/xếp lại buổi ở mốc 05. Sửa deadline/lịch bận/khung giờ sau áp dụng chưa tự dời buổi; đánh dấu xong việc cũng chưa tự gỡ các đặt chỗ cũ. Đã ghi giới hạn trên trang chi tiết để người dùng rà soát.
   - Báo cáo là số liệu lúc tạo; tên/deadline ở danh sách buổi theo công việc hiện tại. Thay đổi đầu vào liên quan yêu cầu tạo bản mới khi áp dụng. Các bản chưa áp dụng không giữ chỗ.
   - Công việc không chia buổi nhưng đã có một phần lịch tương lai được báo cần rà soát, không tự thêm các mảnh mới.
   - PostgreSQL, bản online, AI, Pomodoro, nhắc việc và đồng bộ Calendar vẫn thuộc các mốc sau theo kế hoạch.

7. **Kết quả xác minh của agent**

   - 30 kiểm thử mới cho thuật toán, deadline, ưu tiên, chia/không chia, lịch lặp/chồng/qua đêm, quỹ ngày, nghỉ qua ngày/tuần, trừ phút đã có lịch và làm tròn thời điểm hiện tại; cùng kiểm thử quyền, CSRF, preview/apply, bản cũ, gửi lặp, xóa việc và ràng buộc database.
   - Tổng `manage.py test accounts studies planner --noinput`: **90/90 PASS**. System check, kiểm tra migration và diff whitespace: PASS.
   - Migration `planner.0002_studyplan_studysession` áp dụng thành công; bản sao lưu local `db.sqlite3-before-m05` được Git bỏ qua.
   - Trình duyệt với database/cookie riêng: đăng nhập → tạo mẫu 9 buổi/360 phút/thiếu 240 → lịch chưa có buổi trước áp dụng → áp dụng thành công → tạo lại không nhân đôi → mở thêm quỹ để xếp bổ sung → sửa nghỉ → từ chối bản cũ.
   - Lịch tuần ở 375 px và chi tiết kế hoạch ở 320 px không tràn ngang; đã quan sát ảnh giao diện desktop và mobile. Server QA riêng đã dừng, dữ liệu mẫu không ghi vào `db.sqlite3` của bạn.

8. **Commit/push sau khi bạn kiểm thử đạt**

   ```powershell
   git status --short
   git diff --check
   git check-ignore .env .venv/Scripts/python.exe db.sqlite3 db.sqlite3-before-m05
   git add planner/forms.py planner/models.py planner/views.py planner/urls.py planner/services/availability.py planner/services/scheduling.py planner/test_scheduling.py planner/migrations/0002_studyplan_studysession.py studies/views.py templates/planner/base.html templates/planner/week.html templates/planner/plan_form.html templates/planner/plan_detail.html static/css/planner.css README.md HD_Test.md docs/KE_HOACH_PHAT_TRIEN.md docs/THIET_KE_BAN_DAU.md
   git diff --cached --stat
   git diff --cached --check
   git commit -m "feat: generate preview and apply weekly study plans"
   git push origin main
   ```

   Giữ file migration trong commit. Không đưa `.env`, `.venv`, database hoặc bản sao lưu lên GitHub. Nhánh khi bắt đầu mốc là `main`; thay tên khi push nếu bạn đã đổi nhánh. Agent không stage/commit/push thay bạn.

   Nếu gặp lỗi, gửi ID test, bước thao tác và kết quả thực tế. Chờ bạn kiểm thử và xác nhận trước khi làm mốc 06.

---

**Mốc 06 — Chỉnh/khóa buổi, tiến độ, xếp lại và cảnh báo**

Trạng thái: người dùng đã cho phép chuyển sang mốc 07. Giữ checklist và kết quả mốc 06 làm lịch sử.

Phạm vi đã làm: chỉnh giờ/độ dài buổi tương lai; khóa/mở khóa; ghi nhận Đã học hoặc Hủy/bỏ qua; cập nhật tiến độ công việc; xem trước và áp dụng xếp lại đúng các buổi được phép; cảnh báo deadline, xung đột và buổi chưa ghi nhận. Nghiệp vụ xử lý bằng Python/Django, không thêm thư viện.

1. **Khởi động và kiểm tra kỹ thuật**

   Dừng server cũ bằng Ctrl+C trong terminal của server rồi chạy:

   ```powershell
   Set-Location -LiteralPath 'D:\Python_DuAnLapKeHoachHocTap'
   & .\.venv\Scripts\python.exe manage.py migrate
   & .\.venv\Scripts\python.exe manage.py check
   & .\.venv\Scripts\python.exe manage.py test accounts studies planner --noinput
   & .\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
   & .\.venv\Scripts\python.exe manage.py migrate --check
   & .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
   ```

   Mong đợi: **121/121 tests PASS**, không lỗi system check, không có migration thiếu. Migration mới là `planner.0003_studyplan_mode_studyplan_replacement_ids_and_more`. Agent đã tạo `db.sqlite3-before-m06` bằng SQLite backup trước khi migrate trên máy này; không ghi đè bản sao lưu cũ hoặc xóa dữ liệu mốc trước.

   Mở [Tạo kế hoạch](http://127.0.0.1:8000/planner/plans/new/) hoặc [Cảnh báo](http://127.0.0.1:8000/planner/alerts/). Từ buổi học trên lịch, mở kế hoạch để thấy các thao tác mới. Các bản xem trước cũ có thể cần tạo lại sau migration nếu kiểm tra đầu vào báo đã thay đổi; các bản đã áp dụng vẫn giữ nguyên dữ liệu với trạng thái mặc định Chưa ghi nhận.

   | Trang/thao tác | URL | Ghi chú |
   |---|---|---|
   | Chỉnh buổi | `/planner/sessions/<id>/edit/` | GET xem, POST lưu |
   | Ghi nhận/hủy | `/planner/sessions/<id>/record/` | GET xem, POST lưu |
   | Khóa/mở khóa | POST `/planner/sessions/<id>/lock/` | Dùng nút trên chi tiết kế hoạch; GET trả 405 |
   | Tiến độ công việc | `/studies/tasks/<id>/progress/` | Trạng thái và thời lượng còn lại |
   | Cảnh báo | `/planner/alerts/` | Chỉ đọc, tính lại theo dữ liệu hiện tại |

2. **Dữ liệu mẫu cho luồng xếp lại**

   Đăng ký tài khoản thử A riêng để không bị các buổi/công việc cũ ảnh hưởng. Dùng B cho kiểm tra phân quyền. Gọi **D** là thứ Hai của một tuần tương lai, ví dụ 16/11/2026 tại lúc viết hướng dẫn; thay bằng tuần mới nếu ngày này đã qua.

   - Giờ học: thứ Hai/Ba/Tư, 18:00–22:00, tối đa **180 phút/ngày**, buổi **50 phút**, nghỉ **10 phút**.
   - Một công việc **Python mốc 06**, ước tính/còn lại **180 phút**, deadline D+2 ngày 22:00, Chưa bắt đầu, cho chia buổi.
   - Ban đầu chưa có lịch bận hoặc công việc khác. Chọn tuần D, chế độ **Bổ sung**, tạo và áp dụng: thứ Hai có 18:00–18:50, 19:00–19:50, 20:00–20:50, 21:00–21:30.
   - Khóa buổi 18:00. Chỉnh buổi 19:00 sang **thứ Ba D+1 18:00–18:50**, giữ độ dài; buổi này có nhãn Đã chỉnh tay.
   - Thêm lịch bận **Ca làm mới**, thứ Hai D **20:00–21:00**.

   Chọn **Xếp lại buổi tự động chưa bắt đầu trong tuần**. Kết quả mong đợi:

   | Nội dung | Kết quả |
   |---|---|
   | Buổi được giữ | Thứ Hai 18:00–18:50 đã khóa; thứ Ba 18:00–18:50 đã chỉnh tay |
   | Buổi cũ sẽ hủy khi áp dụng | Thứ Hai 20:00–20:50 và 21:00–21:30 |
   | Buổi mới đề xuất | Thứ Hai 19:00–19:50 và 21:00–21:30 |
   | Báo cáo Python | Còn 180; đã có lịch được giữ 100; bố trí mới 80; thiếu 0 phút |

   Một buổi mới có thể trùng giờ buổi cũ bị thay, nhưng bản xem trước ghi rõ hai bộ; áp dụng phải hủy bộ cũ trước khi kích hoạt bộ mới trong cùng transaction. Các buổi khóa/chỉnh tay không được nhân bản sang bản mới.

3. **Checklist chỉnh/khóa và xếp lại — chạy theo bộ mẫu**

   | ID | Thao tác | Kết quả mong đợi | Kết quả của bạn |
   |---|---|---|---|
   | M06-TC01 | Tạo và áp dụng bộ mẫu ở trên | Có đúng bốn buổi ban đầu, còn lại vẫn 180 phút | Chưa kiểm thử |
   | M06-TC02 | Khóa 18:00; tải lại; mở khóa rồi khóa lại | Nhãn/nút đúng trạng thái; khóa không đổi giờ hay thời lượng | Chưa kiểm thử |
   | M06-TC03 | Khi 18:00 đang khóa, thử chỉnh giờ hoặc hủy buổi | Có lỗi yêu cầu mở khóa; buổi giữ nguyên | Chưa kiểm thử |
   | M06-TC04 | Chỉnh buổi 19:00 sang thứ Ba 18:00–18:50 | Lưu thành công, nhãn Đã chỉnh tay, chuyển đúng ngày trên lịch | Chưa kiểm thử |
   | M06-TC05 | Thêm Ca làm mới 20:00–21:00, xem Cảnh báo | Nếu D trong 7 ngày tới: báo buổi 20:00 trùng lịch bận | Chưa kiểm thử |
   | M06-TC06 | Tạo bản Xếp lại tuần D | Hiện rõ Sẽ hủy 2 buổi cũ; đúng hai buổi mới và báo cáo như bảng mẫu | Chưa kiểm thử |
   | M06-TC07 | Trước khi áp dụng, mở lại lịch/chi tiết kế hoạch cũ | Buổi cũ chưa bị hủy; bản xem trước chưa giữ chỗ | Chưa kiểm thử |
   | M06-TC08 | Áp dụng bản xếp lại | Hai buổi tự động cũ chuyển Đã hủy / bỏ qua; buổi khóa/chỉnh tay giữ đúng ID/giờ; buổi mới lên lịch, không nhân đôi | Chưa kiểm thử |
   | M06-TC09 | Xem kế hoạch cũ và lịch; xem lại Cảnh báo | Kế hoạch cũ vẫn có dấu vết hai buổi hủy; lịch không hiện/khấu trừ buổi hủy; hết cảnh báo trùng ca làm | Chưa kiểm thử |
   | M06-TC10 | Tạo bản Bổ sung cùng tuần, không đổi dữ liệu | Không xếp lại 180 phút; đã có đủ lịch tương lai, không có buổi mới cho Python | Chưa kiểm thử |
   | M06-TC11 | Tạo một bản Xếp lại; trước áp dụng đổi khóa, chỉnh giờ hoặc tiến độ | Áp dụng bị từ chối vì dữ liệu thay đổi; buổi cũ chưa bị hủy; tạo bản mới để tiếp tục | Chưa kiểm thử |

4. **Checklist ràng buộc chỉnh giờ — các ca độc lập, chưa lưu thay đổi nếu form báo lỗi**

   Dùng một buổi planned tương lai, không khóa. Giữ các lịch mẫu để kiểm tra nghỉ/xung đột; có thể tạo tài khoản thử khác khi cần bộ dữ liệu đơn giản.

   | ID | Thao tác | Kết quả mong đợi | Kết quả của bạn |
   |---|---|---|---|
   | M06-TC12 | Nhập kết thúc bằng/trước bắt đầu, sang ngày sau hoặc ra ngoài tuần của kế hoạch | Báo lỗi; giờ cũ và cờ chỉnh tay không đổi | Chưa kiểm thử |
   | M06-TC13 | Chỉnh sang ngày không được học, ngoài 18:00–22:00, vượt deadline hoặc lịch bận | Từ chối, không lưu một phần | Chưa kiểm thử |
   | M06-TC14 | Chỉnh đè buổi khác hoặc chỉ cách 5 phút khi nghỉ 10; sau đó thử cách đúng 10 phút | Đè/thiếu nghỉ bị từ chối; đúng 10 phút được chấp nhận nếu mọi giới hạn khác hợp lệ | Chưa kiểm thử |
   | M06-TC15 | Tăng độ dài khiến tổng học trong ngày vượt giới hạn hoặc tổng phút đã xếp vượt còn lại của việc | Báo rõ giới hạn bị vượt; không đổi buổi | Chưa kiểm thử |
   | M06-TC16 | Với việc không chia buổi, chỉnh chỉ giữ một phần thời lượng còn lại | Từ chối; cần đủ toàn bộ thời lượng trong một buổi, đúng quỹ và khung học | Chưa kiểm thử |
   | M06-TC17 | Thử chỉnh buổi đã bắt đầu/đã học/đã hủy hoặc dời vào quá khứ | Không cho chỉnh; sửa tiến độ công việc dùng trang riêng | Chưa kiểm thử |

5. **Checklist tiến độ và hủy buổi**

   | ID | Thao tác | Kết quả mong đợi | Kết quả của bạn |
   |---|---|---|---|
   | M06-TC18 | Trên Công việc, chọn Cập nhật tiến độ; nhập Đang thực hiện, còn 100 phút | Chỉ đổi trạng thái/phút còn lại, không đổi deadline/môn/giờ buổi | Chưa kiểm thử |
   | M06-TC19 | Với mẫu đang giữ 100 phút khóa/chỉnh tay, sau TC18 tạo Xếp lại | Chỉ cần hủy các buổi tự động còn lại, có thể 0 buổi mới; nút Áp dụng vẫn có và thao tác hủy hợp lệ | Chưa kiểm thử |
   | M06-TC20 | Nhập còn lại 0 nhưng trạng thái chưa hoàn thành; thử số âm. Sau đó chọn Hoàn thành | Dữ liệu không nhất quán/âm bị từ chối; chọn Hoàn thành đưa còn lại về 0 | Chưa kiểm thử |
   | M06-TC21 | Ở buổi tương lai, chọn Ghi nhận Đã học | Báo chưa thể ghi nhận buổi tương lai, không đổi tiến độ | Chưa kiểm thử |
   | M06-TC22 | Với buổi đã bắt đầu chưa ghi nhận: Đã học, nhập còn lại 70 phút | Buổi sang Đã học, việc sang Đang thực hiện còn đúng 70; không tự trừ thêm độ dài buổi | Chưa kiểm thử |
   | M06-TC23 | Ghi nhận một buổi khác đã bắt đầu, nhập còn lại 0; mở lại buổi | Việc Hoàn thành/còn 0; buổi Đã học không còn form ghi nhận; không ghi nhận lần hai | Chưa kiểm thử |
   | M06-TC24 | Hủy/bỏ qua buổi không khóa, giữ nguyên số phút còn lại | Buổi giữ dấu vết, biến khỏi lịch và giải phóng quỹ ngày; việc không giảm thời lượng | Chưa kiểm thử |
   | M06-TC25 | Chọn hủy nhưng đồng thời đổi số phút còn lại | Từ chối, yêu cầu giữ nguyên phút hoặc cập nhật riêng ở trang công việc | Chưa kiểm thử |

   Với TC22–23, có thể dùng buổi đã bắt đầu từ các mốc trước. Nếu chưa có, dùng tài khoản thử khác, chọn ngày hiện tại/khung giờ còn lại trong ngày, tạo việc và áp dụng rồi chờ tới giờ bắt đầu; hệ thống không cho khai buổi tương lai là đã học. Các ca thời điểm này cũng được kiểm thử tự động bằng đồng hồ cố định, không phải chờ trong test suite.

6. **Checklist cảnh báo, quyền và hồi quy**

   | ID | Thao tác | Kết quả mong đợi | Kết quả của bạn |
   |---|---|---|---|
   | M06-TC26 | Tạo việc chưa hoàn thành có deadline hôm qua và việc hạn trong 7 ngày nhưng chưa đủ lịch | Trang Cảnh báo nêu Quá hạn/Chưa đủ lịch và đúng số phút thiếu; việc đã hoàn thành không vào danh sách deadline | Chưa kiểm thử |
   | M06-TC27 | Đổi khung/ngày, giới hạn ngày hoặc deadline làm buổi sắp tới vi phạm; giảm còn lại xuống dưới phút đã xếp | Báo lý do sai khung/quỹ/hạn hoặc vượt phút còn lại. Buổi khóa/chỉnh tay cần xử lý trực tiếp | Chưa kiểm thử |
   | M06-TC28 | Có buổi đã kết thúc chưa ghi nhận; sau đó ghi nhận/bỏ qua | Hiện trong danh sách chờ, tổng số đúng; xử lý xong biến khỏi danh sách chờ; tối đa hiện 20 buổi gần nhất | Chưa kiểm thử |
   | M06-TC29 | B mở URL chỉnh/ghi nhận/POST khóa của A hoặc trang tiến độ việc A; đăng xuất rồi mở các trang mới | B nhận 404, không lộ/sửa dữ liệu A; chưa đăng nhập chuyển Đăng nhập. POST thiếu CSRF bị từ chối trong test tự động | Chưa kiểm thử |
   | M06-TC30 | Mở URL thao tác buổi thuộc bản chưa áp dụng; mở URL khóa bằng GET | Buổi nháp trả 404; GET khóa trả 405; chỉ xem trang không ghi dữ liệu | Chưa kiểm thử |
   | M06-TC31 | Tạo buổi khóa/chỉnh tay ở tuần khác; xếp lại tuần D; kiểm tra buổi đã học/đã bắt đầu | Không thay các buổi ngoài tuần, đã khóa/chỉnh tay/đã bắt đầu/đã học | Chưa kiểm thử |
   | M06-TC32 | Xem cảnh báo/chỉnh giờ ở 375/320 px, dùng Tab; khởi động lại server; thử mốc 02–05 | Không tràn ngang; nhãn/form/nút dùng được; trạng thái và lịch còn nguyên, các chức năng cũ vẫn hoạt động | Chưa kiểm thử |

7. **Quy tắc và giới hạn**

   - Chưa có kéo thả, tạo buổi thủ công từ đầu, hoặc đổi tuần của một buổi. Chỉnh buổi hiện có bằng form, lưu thành buổi đã chỉnh tay.
   - Khóa bảo vệ buổi khỏi xếp lại; mở khóa không biến buổi chỉnh tay thành tự động. Muốn thuật toán phân bổ lại phần đó thì hủy buổi chỉnh tay trước, rồi tạo bản Xếp lại/Bổ sung.
   - Xếp lại do người dùng chủ động yêu cầu, không tự chạy sau mỗi lần sửa dữ liệu. Ràng buộc được bảo đảm cho các buổi mới; buổi giữ nguyên nhưng vi phạm được cảnh báo trong phạm vi 7 ngày để xử lý trực tiếp. Các tuần xa hơn vẫn xem được trên lịch.
   - Hủy và ghi nhận là trạng thái cuối của buổi, không có nút hoàn tác. Hủy vẫn giữ bản ghi; có thể sinh buổi mới để bố trí lại. Nếu nhập sai số phút còn lại, sửa ở Cập nhật tiến độ công việc; chưa sửa lại trạng thái buổi.
   - Đã học giữ thời gian đặt trên lịch và tiêu quỹ ngày; không còn được tính vào phút sẽ học trong tương lai. Nếu ghi nhận trước giờ kết thúc, lịch vẫn giữ đến giờ kết thúc cũ. Chưa có nhật ký phút học thực tế hoặc tự trừ thời lượng.
   - Cảnh báo xét mọi việc quá hạn, việc đến hạn/buổi sắp diễn ra trong 7 ngày; danh sách chờ hiện tối đa 20 buổi gần nhất kèm tổng số. “Chưa đủ lịch” không có nghĩa đã chứng minh không thể hoàn thành.
   - Task hoàn thành không tự xóa buổi khóa/chỉnh tay; cảnh báo để người dùng hủy trực tiếp. Xếp lại có thể hủy các buổi tự động chưa bắt đầu của việc đã xong mà không tạo buổi mới.
   - Báo cáo kế hoạch vẫn là số liệu tại lúc tạo; số buổi/phút còn hiệu lực có thể thay đổi sau chỉnh/ghi nhận/xếp lại. Xóa việc vẫn xóa các buổi thuộc việc như mốc trước, tài liệu được giữ.
   - Pomodoro, nhật ký học/thống kê, email/tác vụ nền, AI, đồng bộ và bản online là các mốc sau.

8. **Kết quả xác minh của agent**

   - **31 test mới**, tổng **121/121 PASS**. Bao phủ bảo toàn buổi khóa/chỉnh tay/đã bắt đầu/đã học/ngoài tuần; xem trước không đổi lịch; thay thế nguyên tử; bản cũ do đổi khóa/thời gian/tiến độ; áp dụng 0 buổi mới; gửi lặp; chỉnh giờ sai ràng buộc; ghi nhận/hủy và bảo vệ quyền/CSRF.
   - Các test cảnh báo kiểm tra quá hạn, hạn gần, phút chưa có lịch, trùng bận/lặp qua đêm/buổi khác, nghỉ, khung học, quỹ, deadline, vượt thời lượng còn lại, công việc hoàn thành, phạm vi 7 ngày và 20 buổi chờ.
   - `manage.py check`, kiểm tra migration và `git diff --check`: PASS. Migration 0003 đã áp dụng, bản sao lưu được Git bỏ qua.
   - Trình duyệt với database/cookie riêng: ghi nhận buổi cũ từ 90 còn 40 phút → xác nhận việc Đang thực hiện → mở/khóa → chỉnh giờ → xem trước xếp lại hai buổi → áp dụng → buổi khóa/chỉnh tay giữ nguyên, hết xung đột ca làm. Cảnh báo quá hạn vẫn đúng.
   - Đã quan sát giao diện desktop; Cảnh báo 375 px và form Chỉnh giờ 320 px không tràn ngang. Server QA riêng đã dừng, dữ liệu mẫu không ghi vào database của bạn.

9. **Commit/push sau khi bạn kiểm thử đạt**

   ```powershell
   git status --short
   git diff --check
   git check-ignore .env .venv/Scripts/python.exe db.sqlite3 db.sqlite3-before-m06
   git add planner studies/forms.py studies/urls.py studies/views.py templates/planner templates/studies/form.html templates/studies/task_list.html static/css/planner.css README.md HD_Test.md docs/KE_HOACH_PHAT_TRIEN.md docs/THIET_KE_BAN_DAU.md
   git diff --cached --stat
   git diff --cached --check
   git commit -m "feat: edit lock track and replan study sessions with alerts"
   git push origin main
   ```

   Nhánh khi bắt đầu mốc là `main`; thay tên nếu bạn đổi nhánh. Giữ migration trong commit, không đưa `.env`, `.venv`, SQLite hoặc bản sao lưu lên GitHub. Agent không stage/commit/push thay bạn.

   Gửi ID test và kết quả thực tế nếu có lỗi. Sau khi bạn kiểm thử và xác nhận, mốc 07 mới làm Pomodoro, nhật ký và thống kê.

---

**Mốc 07 — Pomodoro, nhật ký học và thống kê**

Trạng thái: người dùng đã cho phép chuyển sang mốc 08. Giữ checklist và kết quả mốc 07 làm lịch sử.

Phạm vi: Pomodoro 25 phút học/5 phút nghỉ; tạm dừng, tiếp tục, kết thúc sớm và hủy; lưu nhật ký phút học một lần; nhật ký nhập tay có sửa/xóa/lọc ngày; thống kê bằng Python theo ngày, môn và nguồn. JavaScript chỉ vẽ/đồng bộ đồng hồ, không quyết định số phút được lưu.

1. **Khởi động và kiểm tra kỹ thuật**

   Dừng server cũ bằng Ctrl+C rồi chạy:

   ```powershell
   Set-Location -LiteralPath 'D:\Python_DuAnLapKeHoachHocTap'
   & .\.venv\Scripts\python.exe manage.py migrate
   & .\.venv\Scripts\python.exe manage.py check
   & .\.venv\Scripts\python.exe manage.py test accounts studies planner focus --noinput
   & .\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
   & .\.venv\Scripts\python.exe manage.py migrate --check
   & .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
   ```

   Mong đợi: **150/150 tests PASS**; system check và kiểm tra migration không có lỗi. Không thêm thư viện vào `requirements.txt`. Migration mới `focus.0001_initial` đã áp dụng trên máy hiện tại sau khi tạo SQLite backup `db.sqlite3-before-m07`, không ghi đè bản sao lưu cũ.

   - [Pomodoro](http://127.0.0.1:8000/focus/): bắt đầu và mở 10 phiên gần nhất.
   - Chi tiết phiên: `/focus/sessions/<id>/`; đọc trạng thái JSON: GET `/focus/sessions/<id>/state/`.
   - Thao tác phiên: POST `/focus/sessions/<id>/pause/`, `resume/`, `finish/`, `cancel/`, `break/` qua nút có CSRF; GET các URL thao tác trả 405.
   - [Nhật ký](http://127.0.0.1:8000/focus/logs/): thêm tại `logs/add/`, sửa/xóa tại `logs/<id>/edit/` và `logs/<id>/delete/`.
   - [Thống kê](http://127.0.0.1:8000/focus/statistics/): mặc định 7 ngày gần nhất, tính cả hôm nay.

2. **Dữ liệu mẫu và số liệu đối chiếu**

   Dùng tài khoản thử A mới để không có nhật ký cũ; B cho ca phân quyền. Gọi **H** là ngày hôm nay theo giờ Việt Nam. Tạo hai môn và hai công việc chưa hoàn thành:

   | Môn | Công việc | Ước tính/còn lại | Deadline |
   |---|---|---|---|
   | Lập trình Python, HK1 | Ôn vòng lặp và hàm | 120 phút | H+3 ngày |
   | Toán rời rạc, HK1 | Bài tập đồ thị | 90 phút | H+4 ngày |

   Nhập hai nhật ký tay: Python **30 phút ngày H**, Toán **45 phút ngày H−1**. Chọn khoảng H−6 đến H để đối chiếu:

   | Trạng thái dữ liệu | Tổng | Bản ghi/ngày có học | Theo nguồn | Theo môn |
   |---|---|---|---|---|
   | Hai nhật ký mẫu | 75 phút | 2 / 2 | Tay 75, Pomodoro 0 | Python 30, Toán 45 |
   | Thêm đúng một Pomodoro Python được lưu P phút, P≥1 | 75+P | 3 / 2 | Tay 75, Pomodoro P | Python 30+P, Toán 45 |
   | Thêm nhật ký Python 15 phút hôm nay, rồi sửa thành 20 | 95+P | 4 / 2 | Tay 95, Pomodoro P | Python 50+P, Toán 45 |

   Trung bình = tổng phút / **toàn bộ 7 ngày** trong khoảng, gồm cả ngày không học, làm tròn 1 chữ số. Ví dụ P=2 thì tổng cuối **97**, 4 bản ghi/2 ngày, trung bình **13,9**, ngày H có 52 phút, H−1 có 45 phút. Các ngày còn lại bằng 0.

   Để test nhanh, chạy Pomodoro ít nhất 60 giây học thực sự rồi kết thúc sớm; P là phút tròn được lưu. Các ca thử nhiều phiên, hết đủ 25 phút hoặc hủy nên dùng bộ dữ liệu/tài khoản thử riêng để không làm lệch bảng mẫu trên. Test tự động dùng đồng hồ cố định, không phải chờ 25 phút.

3. **Checklist Pomodoro**

   | ID | Thao tác | Kết quả mong đợi | Kết quả của bạn |
   |---|---|---|---|
   | M07-TC01 | Mở Tập trung hoặc Học Pomodoro từ danh sách công việc | Form chỉ chọn việc của tài khoản đang đăng nhập, chưa hoàn thành; liên kết từ công việc chọn sẵn đúng việc | Chưa kiểm thử |
   | M07-TC02 | Chọn việc và bấm Bắt đầu học 25 phút | Có phiên Học tập/Đang chạy, đồng hồ khoảng 25:00 rồi giảm; đúng tên việc/môn | Chưa kiểm thử |
   | M07-TC03 | Đang chạy, tải lại trang hoặc rời trang rồi quay lại | Khôi phục cùng phiên, không trở về 25:00 hoặc tạo phiên mới; số phút được xác nhận bằng giờ server | Chưa kiểm thử |
   | M07-TC04 | Bấm Tạm dừng, đợi khoảng 10 giây rồi tải lại | Giữ nguyên số giây còn lại, trạng thái Tạm dừng; thời gian chờ không cộng vào học | Chưa kiểm thử |
   | M07-TC05 | Bấm Tiếp tục, đợi vài giây | Đồng hồ chạy từ phần đã giữ, không reset; bấm/gửi lặp không đặt lại mốc tính giờ | Chưa kiểm thử |
   | M07-TC06 | Khi đang chạy hoặc tạm dừng, mở trang Pomodoro ở tab khác | Hiện Tiếp tục phiên hiện tại, không tạo phiên thứ hai; mỗi người chỉ có một phiên học/nghỉ hoạt động | Chưa kiểm thử |
   | M07-TC07 | Có ≥60 giây học thực sự, nhập ghi chú và bấm Lưu và kết thúc | Có đúng một nhật ký Pomodoro P phút tròn; không tính nghỉ/tạm dừng; thời lượng công việc vẫn 120 phút | Chưa kiểm thử |
   | M07-TC08 | Sau khi lưu, tải lại, mở lại hoặc gửi lại thao tác kết thúc | Không tạo nhật ký lần hai, không cộng thêm thời gian; không còn nút lưu phiên đã kết thúc | Chưa kiểm thử |
   | M07-TC09 | Ở bộ thử riêng, kết thúc phiên chưa đủ 60 giây | Phiên kết thúc, không tạo nhật ký 0 phút | Chưa kiểm thử |
   | M07-TC10 | Ở bộ thử riêng, chọn Hủy phiên, không lưu sau khi đã chạy | Trạng thái Đã hủy, không tạo nhật ký dù đã chạy một phần; không thể lưu lại phiên hủy | Chưa kiểm thử |
   | M07-TC11 | Sau phiên học kết thúc, bấm Nghỉ 5 phút; tạm dừng/tiếp tục hoặc Kết thúc nghỉ | Đồng hồ nghỉ khoảng 05:00; mọi phút nghỉ không tạo nhật ký; bấm Nghỉ lại từ cùng phiên học mở đúng phiên nghỉ cũ | Chưa kiểm thử |
   | M07-TC12 | Để phiên học đủ 25 phút hoặc quay lại sau khi đã hết giờ | Đồng hồ về 00:00, có lời nhắc xác nhận; không tự ghi nhật ký. Bấm lưu chỉ ghi tối đa 25 phút, không tính thời gian quá giờ | Chưa kiểm thử |

   Hai tab đồng bộ khi quay lại trang và khoảng mỗi 15 giây. Nếu thao tác từ tab khác đổi trạng thái, trang thông báo tải lại để lấy các thao tác mới, không xóa ghi chú đang nhập bằng cách tự tải lại. Trạng thái kết thúc/hủy không được tiếp tục. Hết giờ vẫn giữ phiên hoạt động cho đến khi bạn xác nhận hoặc hủy.

4. **Checklist nhật ký**

   | ID | Thao tác | Kết quả mong đợi | Kết quả của bạn |
   |---|---|---|---|
   | M07-TC13 | Thêm hai nhật ký tay theo mẫu | Hiện 30 phút hôm nay, 45 phút hôm qua, đúng việc/môn/nguồn Nhập tay | Chưa kiểm thử |
   | M07-TC14 | Thử 0, số âm, >1440 phút, ngày tương lai hoặc ghi chú >1000 ký tự | Form báo lỗi, không thêm bản ghi, không lỗi 500 | Chưa kiểm thử |
   | M07-TC15 | Gửi lặp cùng form tạo nhật ký (ví dụ trình duyệt gửi lại sau Back) | Cùng mã biểu mẫu không tạo bản ghi thứ hai. Muốn nhập hoạt động mới, mở mới trang Thêm nhật ký | Chưa kiểm thử |
   | M07-TC16 | Thêm nhật ký Python 15 phút; sửa thành 20, đổi ghi chú/ngày nếu cần | Giữ một bản ghi được sửa, thống kê cập nhật, không thay tiến độ hoặc lịch | Chưa kiểm thử |
   | M07-TC17 | Sửa nhật ký Pomodoro | Chỉ có ghi chú; không sửa ngày, phút, nguồn hoặc công việc của bản ghi đo từ đồng hồ | Chưa kiểm thử |
   | M07-TC18 | Mở Xóa nhật ký rồi Hủy, giữ lại; sau đó xóa bản thử khi đã chắc chắn | Mở GET không xóa; xác nhận POST mới xóa và giảm thống kê; không đổi thời lượng công việc/lịch | Chưa kiểm thử |
   | M07-TC19 | Xóa một nhật ký Pomodoro thử, mở lại phiên và gửi lại kết thúc | Nhật ký đã xóa không được tự tạo lại; thống kê giữ mức sau xóa. Thao tác xóa không hoàn tác trong ứng dụng | Chưa kiểm thử |
   | M07-TC20 | Chỉ trên dữ liệu thử: đổi tên hoặc xóa công việc/môn đã có nhật ký | Nhật ký/phiên giữ tên và nhãn môn cũ, phút lịch sử không mất; xóa việc làm liên kết việc rỗng, vẫn đọc/sửa ghi chú nhật ký được | Chưa kiểm thử |
   | M07-TC21 | Xóa công việc khi Pomodoro còn chạy rồi kết thúc phiên | Phiên vẫn kết thúc và ghi phút học với tên cũ, không lỗi vì thiếu công việc; không có liên kết cập nhật tiến độ việc đã xóa | Chưa kiểm thử |
   | M07-TC22 | Có >20 nhật ký, chọn khoảng ngày rồi chuyển trang | Mỗi trang tối đa 20 bản; Trang trước/sau giữ nguyên bộ lọc, không trùng tham số ngày qua mỗi lần chuyển | Chưa kiểm thử |

5. **Checklist thống kê**

   | ID | Thao tác | Kết quả mong đợi | Kết quả của bạn |
   |---|---|---|---|
   | M07-TC23 | Trên bộ mẫu, mở Thống kê trước và sau khi lưu Pomodoro P phút | Đúng công thức 75 rồi 75+P; số bản ghi, ngày học, nhóm môn và nguồn khớp bảng mẫu | Chưa kiểm thử |
   | M07-TC24 | Sau khi nhật ký thêm 15 được sửa thành 20 | Tổng 95+P, chỉ 4 bản ghi, 2 ngày; Python 50+P, Toán 45; nghỉ/hủy không được cộng | Chưa kiểm thử |
   | M07-TC25 | Chọn riêng hôm nay rồi riêng hôm qua | Chỉ cộng bản ghi thuộc ngày tương ứng, biên đầu/cuối đều được tính; trung bình chia đúng số ngày chọn | Chưa kiểm thử |
   | M07-TC26 | Chọn khoảng không có nhật ký hoặc tài khoản chưa có dữ liệu | Tổng/bản ghi/ngày học/trung bình bằng 0, biểu đồ có ngày 0 phút, không lỗi chia cho 0 | Chưa kiểm thử |
   | M07-TC27 | Ngày sai, kết thúc trước bắt đầu, kết thúc tương lai hoặc khoảng >366 ngày | Hiện lỗi bộ lọc, không lỗi 500; không tính nhầm dữ liệu ngoài phạm vi | Chưa kiểm thử |
   | M07-TC28 | Chạy phiên qua nửa đêm hoặc đối chiếu test đồng hồ cố định | Toàn bộ phút được gán ngày bắt đầu phiên theo giờ Việt Nam; không tự tách thành hai nhật ký | Chưa kiểm thử |

6. **Checklist quyền và hồi quy**

   | ID | Thao tác | Kết quả mong đợi | Kết quả của bạn |
   |---|---|---|---|
   | M07-TC29 | Chưa đăng nhập mở Pomodoro, phiên, nhật ký, thống kê hoặc URL thao tác | Chuyển Đăng nhập; không lộ dữ liệu | Chưa kiểm thử |
   | M07-TC30 | B mở URL phiên/API trạng thái/sửa/xóa nhật ký của A; thử POST thao tác phiên A | 404, không đọc/sửa được dữ liệu A. Bộ chọn việc không nhận việc B gửi giả từ A | Chưa kiểm thử |
   | M07-TC31 | Gửi owner/giây chạy/nguồn/ngày giả vào thao tác timer hoặc trường chỉ đọc của nhật ký Pomodoro | Máy chủ bỏ qua các trường không cho sửa; phút học/owner/nguồn giữ đúng; đã có test tự động cho dữ liệu giả và CSRF | Chưa kiểm thử |
   | M07-TC32 | Chỉ xem/tải lại trang hoặc API sau khi timer đã hết | Không tự tạo/kết thúc/xóa phiên hoặc ghi nhật ký bằng GET; GET pause/resume/finish/cancel/break trả 405 | Chưa kiểm thử |
   | M07-TC33 | Xem Pomodoro 320 px, nhật ký/thống kê 375 px; dùng Tab và tạm dừng | Không tràn ngang; đồng hồ/nút/form đọc được, không đọc số đếm liên tục qua aria-live; thao tác bàn phím dùng được | Chưa kiểm thử |
   | M07-TC34 | Khởi động lại server; xem lại nhật ký/phiên tạm dừng, thử tài khoản/học tập/lịch mốc trước | Phiên và số liệu giữ nguyên; các tính năng mốc 02–06 vẫn hoạt động | Chưa kiểm thử |

7. **Quy tắc và giới hạn**

   - 25 phút học/5 phút nghỉ cố định. Chưa có tùy chỉnh độ dài, nghỉ dài sau nhiều vòng, tự chạy chu kỳ tiếp theo, chuông hoặc thông báo trình duyệt/email. Hết giờ có lời nhắc trên trang, cần bấm xác nhận.
   - Đồng hồ lưu ở máy chủ. Đóng tab không hủy, hết giờ không tự ghi log; quay lại mở phiên hiện tại. JavaScript chỉ hiển thị ước lượng đếm ngược, số phút lưu luôn tính lại từ trạng thái server và giới hạn phiên.
   - Tính phần nguyên phút học, bỏ giây lẻ; mỗi lần pause chốt giây tròn. Không cộng pause, break hoặc thời gian quá 25 phút. Hủy khác Lưu và kết thúc: hủy bỏ toàn bộ phút của phiên, không ghi log.
   - Pomodoro và nhật ký không tự giảm Task.remaining_minutes, không tự đánh dấu StudySession đã học. Dùng Cập nhật tiến độ/Ghi nhận buổi ở mốc 06 để ghi phần việc còn lại, tránh trừ tiến độ hai lần.
   - Nhật ký là thời gian được ghi nhận, không chứng minh mức độ tập trung hoặc đã hoàn thành việc. Không nhập tay lại cùng hoạt động Pomodoro đã lưu. Mã biểu mẫu chỉ ngăn gửi trùng cùng yêu cầu, không đoán hai bản ghi nhập riêng có phải cùng hoạt động.
   - Nhật ký tay chấp nhận 1–1440 phút/bản, có thể gắn việc đã hoàn thành để ghi lịch sử. Thời gian học thực tế không bắt buộc theo khung/quỹ dự kiến trên lịch. Muốn sửa log tay sau khi việc đã xóa có thể giữ liên kết rỗng; tên/môn lịch sử được giữ.
   - Xóa nhật ký không hoàn tác, không tự hồi sinh khi finish lại. Pomodoro cho sửa ghi chú, không sửa số phút/ngày đo được. Thống kê chỉ cộng nhật ký còn lưu, không cộng FocusSession riêng.
   - Ngày Pomodoro là ngày bắt đầu phiên ở Asia/Ho_Chi_Minh; phiên qua ngày hoặc tạm dừng nhiều ngày vẫn ghi vào ngày bắt đầu. Nhật ký tay theo ngày bạn chọn. Môn nhóm theo nhãn lúc bắt đầu phiên hoặc nhập/sửa nhật ký tay; đổi tên/học kỳ rồi ghi thêm có thể thành nhóm khác.
   - Nhật ký và thống kê mặc định 7 ngày, chọn được 1–366 ngày; trung bình bao gồm ngày không học. Giao diện ngày gốc có thể theo định dạng trình duyệt, nội dung báo cáo dùng ngày/tháng.
   - SQLite có thể báo đang bận khi thao tác đồng thời; trang thao tác yêu cầu tải lại/thử lại, không báo lưu thành công giả. Constraint database vẫn chặn nhiều phiên hoạt động và nhật ký trùng theo phiên/yêu cầu.
   - Email/tác vụ nền, AI, đồng bộ Calendar, PostgreSQL/bản online vẫn là các mốc sau theo kế hoạch.

8. **Kết quả xác minh của agent**

   - **29 test mới**, tổng `manage.py test accounts studies planner focus --noinput`: **150/150 PASS**.
   - Bao phủ vòng đời timer, pause/resume/lặp yêu cầu, giới hạn 25 phút, dưới một phút, hủy, nghỉ không tính, GET không ghi, lưu log một lần kể cả sau xóa, quyền A/B, CSRF, trường giả, validation, CRUD, phân trang/ngày và tổng thống kê theo nguồn/môn/ngày.
   - Test constraint kiểm tra một phiên hoạt động/owner, trạng thái hợp lệ, giây không vượt thời lượng và log không có 0 phút. Kiểm tra giữ lịch sử khi xóa việc, thời lượng công việc không tự giảm và thông báo SQLite bận.
   - `manage.py check`, `makemigrations --check --dry-run`, `migrate --check`, kiểm tra tính toàn vẹn SQLite và `git diff --check`: PASS. Migration `focus.0001_initial` đã áp dụng; bản sao lưu được Git bỏ qua.
   - Trình duyệt với database/cookie riêng: mở timer mẫu → pause/tải lại giữ 22:16 → resume → lưu 2 phút → nghỉ/kết thúc nghỉ không thêm log → thống kê 77 phút → thêm log 15/sửa 20 → tổng 97, 4 bản ghi/2 ngày, nguồn tay 95/Pomodoro 2, môn Python 52/Toán 45.
   - Đã bắt đầu phiên mới từ form, kiểm tra đồng hồ 320 px rồi hủy; thống kê ở 375 px không tràn ngang. Đã quan sát ảnh desktop. Server QA riêng đã dừng và dọn database tạm; không thêm dữ liệu mẫu vào `db.sqlite3` của bạn.

9. **Commit/push sau khi bạn kiểm thử đạt**

   ```powershell
   git status --short
   git diff --check
   git check-ignore .env .venv/Scripts/python.exe db.sqlite3 db.sqlite3-before-m07
   git add focus config/settings.py config/urls.py studies/views.py templates/base.html templates/studies/task_list.html templates/focus static/css/focus.css static/js/focus_timer.js README.md HD_Test.md docs/KE_HOACH_PHAT_TRIEN.md docs/THIET_KE_BAN_DAU.md
   git diff --cached --stat
   git diff --cached --check
   git commit -m "feat: add persistent pomodoro study logs and statistics"
   git push origin main
   ```

   Nhánh lúc bắt đầu mốc là `main`; thay tên nếu bạn đã đổi nhánh. Giữ migration trong commit; không đưa `.env`, `.venv`, SQLite hoặc bản sao lưu lên GitHub. Agent không stage/commit/push thay bạn.

   Nếu có lỗi, gửi ID test và kết quả thực tế. Chờ bạn kiểm thử và xác nhận trước khi triển khai mốc 08 (thông báo và email nhắc bằng tác vụ nền).

---

**Mốc 08 — Thông báo, email nhắc và worker nền**

Trạng thái: chờ bạn kiểm thử và commit/push GitHub. Agent dừng ở mốc 08.

Phạm vi: nhắc deadline và buổi học sắp bắt đầu, hộp thông báo đọc/chưa đọc, lịch sử email, tùy chọn mỗi người; worker Python/hàng đợi database, chống tạo trùng, kiểm tra dữ liệu sống, thử lại có giới hạn và xử lý email chưa chắc kết quả. Không yêu cầu cài thêm thư viện/broker ở mốc local này.

1. **Khởi động và kiểm tra kỹ thuật**

   Dừng server cũ bằng Ctrl+C. Terminal thứ nhất:

   ```powershell
   Set-Location -LiteralPath 'D:\Python_DuAnLapKeHoachHocTap'
   & .\.venv\Scripts\python.exe manage.py migrate
   & .\.venv\Scripts\python.exe manage.py check
   & .\.venv\Scripts\python.exe manage.py test accounts studies planner focus notifications --noinput
   & .\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
   & .\.venv\Scripts\python.exe manage.py migrate --check
   & .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
   ```

   Mong đợi **181/181 tests PASS**, không lỗi system check hoặc migration thiếu. Migration mới: `notifications.0001_initial`. Trên máy này agent đã tạo SQLite backup `db.sqlite3-before-m08` trước migrate, không ghi đè bản sao lưu cũ. Không xóa database để kiểm thử lại.

   Kiểm thử local giữ email backend mặc định `django.core.mail.backends.console.EmailBackend`; nếu bạn đã tự đặt `EMAIL_BACKEND` khác trong `.env`, chuyển về console trước các ca thử mẫu. Chỉ thêm/sửa các biến cần thiết, không chép đè `.env` hiện tại từ file mẫu. Chế độ email hiển thị ngay trên trang Tùy chọn/Lịch sử email.

   Terminal thứ hai, cùng thư mục dự án:

   ```powershell
   Set-Location -LiteralPath 'D:\Python_DuAnLapKeHoachHocTap'
   # Chạy một lượt để đối chiếu số lượng, chưa cần bật vòng lặp.
   & .\.venv\Scripts\python.exe manage.py process_reminders
   # Khi cần chạy liên tục, dùng lệnh dưới; Ctrl+C để dừng.
   & .\.venv\Scripts\python.exe manage.py process_reminders --watch
   ```

   `--watch` kiểm tra mỗi 60 giây; có thể dùng `--watch --interval 5` để thử nhanh, giá trị hợp lệ 1–3600 giây. Không cần Redis/Celery. Đây là worker nội bộ của web, chạy tách khỏi server; mở web không tự bật worker. Trên bản online cần tiến trình worker riêng hoặc bộ lập lịch gọi lệnh một lượt.

   - [Thông báo](http://127.0.0.1:8000/notifications/): chỉ các nhắc trong web đã xử lý thành công.
   - [Lịch sử email](http://127.0.0.1:8000/notifications/email/): chờ/đang xử lý/đã bàn giao/lỗi/bỏ qua/chưa xác nhận.
   - [Tùy chọn nhắc](http://127.0.0.1:8000/notifications/preferences/): bật kênh và chọn số phút nhắc trước.

2. **Dữ liệu mẫu — tạo đúng thứ tự để đối chiếu**

   Dùng tài khoản thử A mới, có email đúng định dạng khi đăng ký. Dùng B cho ca phân quyền. Để worker tắt trong lúc tạo dữ liệu. Không dùng email hoặc tài liệu thật trong ca thử local.

   1. Tạo công việc **Ôn cấu trúc dữ liệu**, 30 phút, cho chia buổi, deadline sau 3 ngày. Đây là công việc duy nhất lúc tạo kế hoạch.
   2. Trong Giờ học, chọn ngày hiện tại; khung học bắt đầu khoảng **10–14 phút nữa**, kết thúc đủ cho buổi 30 phút trong cùng ngày; tối đa ngày 60, buổi 30, nghỉ 5. Nếu sắp nửa đêm, thực hiện lúc còn đủ khung trong ngày hoặc chọn một thời điểm phù hợp khác.
   3. Tạo và áp dụng kế hoạch cho tuần chứa ngày đó. Kiểm tra có **một buổi 30 phút** bắt đầu sau 10–14 phút. Không ghi nhận hoặc hủy buổi này.
   4. Sau khi đã áp dụng buổi trên, mới tạo công việc **Nộp bài Python**, còn 45 phút, deadline khoảng **40 phút nữa**; chưa cần xếp lịch công việc này.
   5. Tại Tùy chọn nhắc: bật Trong web và Email, deadline **1 giờ**, buổi **15 phút**. Dùng chế độ email console.

   Chạy worker một lượt khi buổi vẫn còn trong tương lai và cách hiện tại không quá 15 phút. Mong đợi:

   | Nội dung | Kết quả |
   |---|---|
   | Thông báo trong web | 2 bản: một deadline, một buổi học; ban đầu đều chưa đọc |
   | Email console | 2 thư trong terminal worker, đúng email của A, nội dung đúng đối tượng/giờ/phút còn lại |
   | Lịch sử email | 2 bản Đã bàn giao email; mỗi bản 1 lần thử |
   | Kết quả lệnh lần đầu | Tạo 4 nhắc; xử lý thành công 4 nhắc |
   | Chạy lại cùng dữ liệu/thời điểm | Tạo 0; xử lý 0; không thêm thông báo hoặc email |

   Email có liên kết mở việc/kế hoạch và đường dẫn tới tùy chọn thay/tắt email. Tiêu đề MIME trong terminal có thể được mã hóa UTF-8; phần thân vẫn đọc được. Không có thư tới inbox thật trong chế độ console. Nếu còn công việc/buổi khác cũng đến ngưỡng nhắc, tổng sẽ lớn hơn bảng mẫu; dùng tài khoản mới hoặc kiểm tra theo đúng tên mẫu.

3. **Checklist tùy chọn và hộp thông báo**

   | ID | Thao tác | Kết quả mong đợi | Kết quả của bạn |
   |---|---|---|---|
   | M08-TC01 | Tài khoản chưa lưu tùy chọn, chỉ mở/tải lại trang | Mặc định web bật, email tắt, deadline 24 giờ, buổi 15 phút; GET không tạo bản ghi tùy chọn | Chưa kiểm thử |
   | M08-TC02 | Lưu tùy chọn mẫu rồi tải lại | Giữ đúng hai kênh/1 giờ/15 phút và email của tài khoản A | Chưa kiểm thử |
   | M08-TC03 | Chưa chạy worker, mở web rồi chờ/tải lại | GET không tự tạo hoặc gửi nhắc; các trang học tập vẫn dùng được | Chưa kiểm thử |
   | M08-TC04 | Chạy worker một lượt theo dữ liệu mẫu | Đúng 4 nhắc xử lý: 2 trong web + 2 email console | Chưa kiểm thử |
   | M08-TC05 | Chạy lại vài lượt hoặc bật watch | Cùng đối tượng/thời điểm/kênh không được nhân bản; không gửi lại bản đã xử lý | Chưa kiểm thử |
   | M08-TC06 | Xem hộp thông báo rồi tải lại, chưa bấm đã đọc | Vẫn 2 chưa đọc; chỉ xem không tự đánh dấu | Chưa kiểm thử |
   | M08-TC07 | Đánh dấu một bản đã đọc; chọn Chưa đọc và lọc | Số chưa đọc còn 1, chỉ còn bản chưa đọc trong bộ lọc | Chưa kiểm thử |
   | M08-TC08 | Bấm Đánh dấu tất cả đã đọc, lọc Chưa đọc | Số chưa đọc bằng 0, danh sách lọc trống; Tất cả vẫn giữ lịch sử | Chưa kiểm thử |
   | M08-TC09 | Mở nội dung liên quan từ nhắc deadline/buổi | Tới đúng công việc hoặc kế hoạch, vẫn qua kiểm tra quyền sở hữu | Chưa kiểm thử |
   | M08-TC10 | Chọn thời gian nhắc không hợp lệ bằng request giả hoặc bật email trên tài khoản có email rỗng/sai | Form từ chối, cấu hình trước đó giữ nguyên; email hiện có lấy từ thông tin tài khoản | Chưa kiểm thử |

4. **Checklist hàng đợi và dữ liệu thay đổi**

   Dùng dữ liệu thử độc lập cho các ca dưới, dừng watch trước khi thay đổi để quan sát dễ hơn. Các trường hợp dữ liệu đổi giữa lúc đã xếp hàng và lúc gửi được kiểm thử tự động bằng đồng hồ cố định, không cần chờ hoặc gửi SMTP thật.

   | ID | Thao tác | Kết quả mong đợi | Kết quả của bạn |
   |---|---|---|---|
   | M08-TC11 | Tắt một kênh trước khi worker phát nhắc | Kênh tắt không phát nhắc mới; bản chờ ở kênh đó bị bỏ qua; lịch sử đã phát giữ nguyên | Chưa kiểm thử |
   | M08-TC12 | Web đã nhắc, sau đó mới bật email khi đối tượng vẫn đủ điều kiện | Chỉ thêm nhắc email một lần, không nhân đôi thông báo web | Chưa kiểm thử |
   | M08-TC13 | Đổi mức nhắc sớm sau khi một sự kiện đã xử lý | Không gửi lại cùng sự kiện chỉ vì đổi lead; nếu bản còn chờ và lead mới chưa tới thì hoãn đến ngưỡng mới | Chưa kiểm thử |
   | M08-TC14 | Đổi deadline sang thời điểm mới còn trong ngưỡng nhắc | Nhắc cũ chưa phát bị bỏ qua; thời điểm mới có một nhắc mới mỗi kênh; lịch sử đã phát không bị xóa | Chưa kiểm thử |
   | M08-TC15 | Chỉnh giờ, hủy hoặc ghi nhận buổi trước khi nhắc được phát | Không gửi nhắc cho giờ cũ/buổi đã hủy/đã ghi nhận; giờ mới chỉ nhắc khi đến ngưỡng và còn trong tương lai | Chưa kiểm thử |
   | M08-TC16 | Hoàn thành/xóa việc hoặc xóa buổi trước khi worker phát nhắc | Không gửi nhắc lỗi thời; lịch sử được giữ với liên kết rỗng nếu đối tượng đã xóa | Chưa kiểm thử |
   | M08-TC17 | Khóa tài khoản A trong Admin trước khi worker phát nhắc | Không tạo/phát nhắc cho tài khoản khóa; mở khóa chỉ nhắc đối tượng vẫn còn hiệu lực | Chưa kiểm thử |
   | M08-TC18 | Worker dừng qua ngưỡng nhắc rồi mở lại trước khi đến hạn/bắt đầu | Gửi bù một lần nếu thời điểm đích vẫn ở tương lai; không phát nhắc cho deadline đã qua hoặc buổi đã bắt đầu | Chưa kiểm thử |
   | M08-TC19 | Có buổi thuộc bản xem trước chưa áp dụng, buổi done/cancelled hoặc việc done | Không tạo nhắc cho các đối tượng này | Chưa kiểm thử |

5. **Checklist email và vận hành**

   | ID | Thao tác | Kết quả mong đợi | Kết quả của bạn |
   |---|---|---|---|
   | M08-TC20 | Xem Lịch sử email sau lượt mẫu console | Hai bản Đã bàn giao email, một lần thử/bản; có dòng chỉ rõ email thử ở terminal, không kết luận inbox thật đã nhận | Chưa kiểm thử |
   | M08-TC21 | Mô phỏng SMTP từ chối/cấu hình sai trong test tự động | Trạng thái Gửi lỗi, thử tối đa 3 lần và giãn ít nhất 1 phút; quá số lượt không tự gửi tiếp | Chưa kiểm thử |
   | M08-TC22 | Mô phỏng mất kết nối sau khi bắt đầu gửi | Chưa xác nhận kết quả; không tự retry; lịch sử yêu cầu kiểm tra hộp thư trước gửi lại | Chưa kiểm thử |
   | M08-TC23 | Trên bản Gửi lỗi/Chưa xác nhận, bấm Đã kiểm tra hộp thư, yêu cầu gửi lại | Chỉ xếp hàng một lượt mới, chưa gửi trong request; worker kiểm tra lại dữ liệu/kênh và tối đa 3 lần cho lượt này | Chưa kiểm thử |
   | M08-TC24 | Mô phỏng worker gián đoạn khi đang claim, chạy lại sau 5 phút | Nhắc web có thể đưa về chờ; email sang Chưa xác nhận, không tự gửi lại có nguy cơ trùng; worker cũ không ghi đè claim đã thu hồi | Chưa kiểm thử |
   | M08-TC25 | Chạy watch, để có sự kiện đến ngưỡng hoặc thay dữ liệu; Ctrl+C | Các lượt chạy theo interval, dữ liệu hàng đợi tồn tại sau restart; Ctrl+C dừng gọn | Chưa kiểm thử |
   | M08-TC26 | Dùng `--interval 0` hoặc mô phỏng SQLite tạm khóa | Interval sai bị từ chối; watch báo database bận rồi tiếp tục lượt sau; lệnh một lượt trả thất bại để người vận hành chạy lại | Chưa kiểm thử |

   Có thể chạy riêng các ca lỗi email/claim mà không cần tài khoản SMTP:

   ```powershell
   & .\.venv\Scripts\python.exe manage.py test notifications.tests.ReminderTests.test_rejected_email_retries_three_times_one_minute_apart notifications.tests.ReminderTests.test_disconnect_is_uncertain_and_not_automatically_retried notifications.tests.ReminderTests.test_live_claim_cannot_be_claimed_twice_and_stale_claim_recovery notifications.tests.ReminderTests.test_manual_retry_queues_only_failed_or_uncertain_without_sending_in_request --noinput
   ```

   Các test dùng backend trong bộ nhớ và giả lập phản hồi, không gửi thư thật. Không cần cố tình nhập sai mật khẩu SMTP để tái hiện lỗi.

6. **Checklist quyền, giao diện và hồi quy**

   | ID | Thao tác | Kết quả mong đợi | Kết quả của bạn |
   |---|---|---|---|
   | M08-TC27 | Chưa đăng nhập mở các trang/thao tác mới | Chuyển Đăng nhập, không lộ lịch sử | Chưa kiểm thử |
   | M08-TC28 | B mở lịch sử của mình, gửi POST đánh dấu/gửi lại với ID của A; giả owner khi lưu tùy chọn | Không thấy/sửa dữ liệu A; ID người khác trả 404; tùy chọn vẫn chỉ lưu cho người đăng nhập | Chưa kiểm thử |
   | M08-TC29 | GET URL đánh dấu/gửi lại, hoặc POST thiếu CSRF | GET thao tác trả 405; POST thiếu CSRF bị từ chối; không tự gửi mail hoặc đánh dấu bằng GET | Chưa kiểm thử |
   | M08-TC30 | Có >20 thông báo hoặc email, chuyển trang; nhập bộ lọc lạ | Phân trang tối đa 20; giữ bộ lọc chưa đọc; bộ lọc sai có lỗi và không lộ dữ liệu | Chưa kiểm thử |
   | M08-TC31 | Xem hộp thông báo 375 px, tùy chọn 320 px; dùng Tab | Không tràn ngang, nút/chọn/checkbox và nhãn dùng được | Chưa kiểm thử |
   | M08-TC32 | Khởi động lại server/worker, thử tài khoản, lịch, Pomodoro và nhật ký | Nhắc/đã đọc/tùy chọn còn nguyên, không phát lại bản đã xử lý; mốc 02–07 vẫn hoạt động | Chưa kiểm thử |

7. **SMTP thật — cấu hình khi bạn sẵn sàng thử gửi**

   Trong `.env` đang được Git bỏ qua, chỉnh các biến theo nhà cung cấp của bạn, không ghi thông tin đăng nhập vào source hoặc tài liệu:

   ```dotenv
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.ten-nha-cung-cap-cua-ban
   EMAIL_PORT=587
   EMAIL_USE_TLS=true
   EMAIL_USE_SSL=false
   EMAIL_HOST_USER=tai-khoan-gui-cua-ban
   EMAIL_HOST_PASSWORD=mat-khau-ung-dung-cua-ban
   DEFAULT_FROM_EMAIL=Nhịp Học <dia-chi-gui-duoc-nha-cung-cap-cho-phep>
   SITE_URL=http://127.0.0.1:8000
   ```

   Đây là giá trị minh họa, cần thay bằng cấu hình hợp lệ; một số nhà cung cấp yêu cầu mật khẩu ứng dụng/quyền gửi riêng. Nếu dùng SSL cổng 465 thì TLS=false, SSL=true; không bật đồng thời. Khởi động lại cả web và worker sau đổi môi trường. Khi deploy, SITE_URL phải là URL thật của web. Tham khảo [Django 5.2 email](https://docs.djangoproject.com/en/5.2/topics/email/) cho các thiết lập gửi.

   Chỉ bật email cho tài khoản nhận mà bạn muốn thử, tạo một sự kiện mới để kiểm tra, kiểm tra Inbox/Spam và trạng thái tại nhà cung cấp. Chế độ console/locmem đã được kiểm thử trong mốc này; SMTP qua nhà cung cấp thật chưa được xác minh vì chưa có cấu hình của bạn. Sau thử, có thể tắt email trong Tùy chọn nhắc hoặc chuyển lại console.

8. **Quy tắc và giới hạn**

   - Nhắc deadline/buổi học trong web/email, chưa có push notification, chuông thiết bị hoặc email báo hết Pomodoro. Cảnh báo trực tiếp ở planner vẫn là tính năng riêng, không tự đồng nghĩa đã gửi nhắc.
   - Worker phải chạy độc lập; mặc định kiểm tra mỗi 60 giây, nên nhắc có độ trễ theo interval và thời gian xử lý. Không bảo đảm đúng từng giây hoặc gửi bù khi đối tượng đã quá hạn/bắt đầu.
   - Mỗi loại đối tượng/ID/thời điểm/kênh có một bản nhắc. Đổi thời điểm đích tạo phiên bản mới; lịch sử đã gửi vẫn được giữ. Đổi lead không gửi lại cùng sự kiện. Bản bỏ qua có thể hoạt động lại khi đối tượng/kênh hợp lệ và còn lượt.
   - Nhắc kiểm tra trạng thái ngay trước phát; thay đổi xảy ra trong khi SMTP đang gửi không thể thu hồi một thư đã bàn giao. SMTP chấp nhận cũng không bảo đảm đã vào inbox. Khi kết quả không xác định, kiểm tra hộp thư trước gửi lại vì có thể nhận trùng.
   - Gửi lại thủ công reset một lượt tối đa 3 lần; gửi lặp nút không reset bản đang chờ/đang xử lý/đã gửi. Lịch sử hiển thị số lần trong lượt hiện tại, chưa có nhật ký từng lần thử riêng.
   - Recipient luôn lấy từ email tài khoản hiện tại; email phải đúng định dạng. Mốc này chưa thêm xác minh email hay thay email tự phục vụ; tài khoản quản trị thiếu email có thể cập nhật trong Admin.
   - Lịch sử và thời điểm dùng giờ Việt Nam; lưu địa chỉ nhận/chế độ tại lần thử, nên đổi backend sang SMTP không biến thư console cũ thành thư đã gửi thật. Lỗi hiển thị được chuẩn hóa để không đưa nội dung exception SMTP/thông tin xác thực vào web. Giao diện lịch sử không cho sửa recipient hoặc nội dung gửi bằng POST giả.
   - Giữ `.env`, SQLite/bản sao lưu ngoài Git. Tự khởi động worker khi đăng nhập Windows hoặc vận hành trên host online chưa được cấu hình tự động ở mốc local này; các lệnh đã sẵn để chạy thủ công/bộ lập lịch.

9. **Kết quả xác minh của agent**

   - **31 test mới**, tổng `manage.py test accounts studies planner focus notifications --noinput`: **181/181 PASS**.
   - Bao phủ ngưỡng giờ, kênh, đã hoàn thành/nháp/hủy/xóa, sửa thời điểm/lead, tài khoản khóa, dữ liệu sống lúc phát, khóa trùng database, claim, thử lại, mất kết nối, gián đoạn worker, đọc/chưa đọc, quyền A/B, owner giả, CSRF và worker watch/database bận.
   - `manage.py check`, kiểm tra migration, SQLite integrity và diff whitespace: PASS. Migration `notifications.0001_initial` đã áp dụng, bản sao lưu `db.sqlite3-before-m08` được Git bỏ qua.
   - Worker với database riêng và console backend: lượt đầu tạo/xử lý 4 nhắc (2 web + 2 email), lượt thứ hai 0/0. Không gửi thư ra ngoài.
   - Trình duyệt: thấy hai thông báo → đánh dấu một còn 1 → lọc Chưa đọc → tất cả đã đọc còn 0 → lịch sử email rõ chế độ console/đã bàn giao → đổi/lưu kênh và lead thành công. Hộp thông báo 375 px và tùy chọn 320 px không tràn ngang.
   - Server/fixture QA riêng đã dừng và dọn; không thêm dữ liệu mẫu vào `db.sqlite3` của bạn. SMTP thật chưa được kiểm tra.

10. **Commit/push sau khi bạn kiểm thử đạt**

   ```powershell
   git status --short
   git diff --check
   git check-ignore .env .venv/Scripts/python.exe db.sqlite3 db.sqlite3-before-m08
   git add notifications config/settings.py config/urls.py .env.example templates/base.html templates/planner/alerts.html templates/notifications static/css/notifications.css README.md HD_Test.md docs/KE_HOACH_PHAT_TRIEN.md docs/THIET_KE_BAN_DAU.md
   git diff --cached --stat
   git diff --cached --check
   git commit -m "feat: add queued study reminders inbox and email delivery"
   git push origin main
   ```

   Nhánh lúc bắt đầu là `main`; thay tên nếu bạn đã đổi nhánh. Giữ migration và `.env.example` trong commit, không đưa `.env` thật hoặc database lên GitHub. Agent không stage/commit/push thay bạn.

   Nếu có lỗi, gửi ID test và kết quả thực tế. Chờ bạn kiểm thử và xác nhận trước khi chuyển mốc 09 — đồng bộ một chiều sang Google Calendar.

---

**Mốc 09 — Đồng bộ một chiều sang Google Calendar**

Trạng thái: người dùng đã cho phép chuyển từ mốc 08. Đã triển khai mốc 09; dừng tại đây để bạn kiểm thử và commit/push trước mốc 10.

Phạm vi: kết nối Google bằng OAuth có state/PKCE, mã hóa token, tạo lịch riêng Nhịp Học, xem trước thay đổi theo tuần, xác nhận vào hàng đợi và worker Python tạo/cập nhật/gỡ sự kiện. Có lịch sử kết quả và ngắt kết nối. Đồng bộ là một chiều từ web sang Google; cần xác nhận lại sau khi sửa dữ liệu.

1. **Cập nhật môi trường và database**

   Trong PowerShell tại thư mục dự án:

   ```powershell
   Set-Location -LiteralPath 'D:\Python_DuAnLapKeHoachHocTap'
   & .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   & .\.venv\Scripts\python.exe manage.py migrate
   & .\.venv\Scripts\python.exe manage.py check
   & .\.venv\Scripts\python.exe manage.py test --noinput
   & .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
   ```

   Khởi động lại server cũ nếu đang chạy. Migration mới là `integrations.0001_initial`. Agent đã tạo bản sao SQLite `db.sqlite3-before-m09` trước khi migrate trên máy hiện tại; các tài khoản, công việc, buổi học và nhật ký cũ được giữ nguyên. Không ghi đè `.env` bằng `.env.example`.

   Có thể kiểm tra phần chưa cấu hình và chạy toàn bộ test ngay, chưa cần tài khoản Google. Các test dùng database riêng và giả lập API, không gọi Google thật. Các thư viện mới được chốt phiên bản trong `requirements.txt`.

2. **Cấu hình OAuth thật bằng tài khoản của bạn**

   Đây là bước bắt buộc để kiểm tra kết nối Google thật. Agent chưa tạo OAuth Client, chưa cấp quyền và chưa ghi vào Google Calendar thật của bạn.

   - Mở [Google Cloud Console](https://console.cloud.google.com/), chọn hoặc tạo project dành cho ứng dụng.
   - Bật **Google Calendar API** trong thư viện API của project.
   - Trong Google Auth Platform/OAuth consent screen, cấu hình tên ứng dụng, email liên hệ và đối tượng sử dụng. Nếu đang ở chế độ Testing, thêm tài khoản Google dùng để thử vào danh sách test users.
   - Khai báo các scope ứng dụng cần: `openid`, `https://www.googleapis.com/auth/userinfo.email`, `https://www.googleapis.com/auth/calendar.app.created`. Scope Calendar này giới hạn vào các lịch phụ do ứng dụng tạo; ứng dụng không cần quyền đọc toàn bộ lịch cá nhân.
   - Tạo OAuth Client loại **Web application**. Thêm **Authorized redirect URI** chính xác: `http://127.0.0.1:8000/integrations/google/callback/`. Không thêm/bớt dấu `/`, không thay `127.0.0.1` bằng `localhost` trong lúc thử. Khi triển khai sẽ khai báo callback HTTPS tương ứng với tên miền thật.
   - Lưu Client ID và Client secret vào `.env` đang bị Git bỏ qua. Không tải tệp credentials vào thư mục được Git theo dõi, không gửi secret trong ảnh chụp hoặc báo lỗi.

   Tạo khóa mã hóa một lần trên máy bạn:

   ```powershell
   & .\.venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

   Thêm các dòng sau vào `.env`, thay nội dung trong dấu `<...>` bằng giá trị thật:

   ```dotenv
   GOOGLE_CLIENT_ID=<Client ID của Web application>
   GOOGLE_CLIENT_SECRET=<Client secret của Web application>
   GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/integrations/google/callback/
   GOOGLE_TOKEN_ENCRYPTION_KEY=<khóa Fernet vừa tạo>
   ```

   Không giữ dấu `<...>` trong giá trị thật. Giữ khóa mã hóa ổn định cùng database; đổi hoặc mất khóa thì token đã lưu không đọc được và cần kết nối lại. Sao lưu khóa riêng với bản sao database, không đưa khóa lên GitHub. Dừng rồi mở lại server và worker sau khi đổi `.env`.

   Tài liệu đối chiếu: [OAuth cho ứng dụng web](https://developers.google.com/identity/protocols/oauth2/web-server), [scope Calendar API](https://developers.google.com/workspace/calendar/api/auth), [tạo lịch phụ](https://developers.google.com/workspace/calendar/api/v3/reference/calendars/insert) và [tạo sự kiện với ID do ứng dụng đặt](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert). Các yêu cầu xuất bản/xác minh Google phụ thuộc cấu hình project; sẽ cần kiểm tra lại khi triển khai online.

3. **Chạy worker đồng bộ**

   Mở terminal riêng tại thư mục dự án:

   ```powershell
   & .\.venv\Scripts\python.exe manage.py process_calendar_sync --watch
   ```

   Mặc định kiểm tra mỗi 60 giây, Ctrl+C để dừng. Có thể dùng `--watch --interval 5` để kiểm thử nhanh; interval nhận 1–3600 giây. Muốn kiểm tra một lượt:

   ```powershell
   & .\.venv\Scripts\python.exe manage.py process_calendar_sync
   ```

   Khi chưa có yêu cầu, kết quả là `Google Calendar: processed 0 sync job(s).` Khi xử lý một yêu cầu là `processed 1 sync job(s).` Số này là số yêu cầu đã xử lý, gồm cả yêu cầu bị dừng/lỗi; xem trạng thái chi tiết trong web để biết có thành công không. Thông báo terminal dùng tiếng Anh để tương thích mã hóa Windows; giao diện vẫn tiếng Việt.

   Worker này độc lập với `process_reminders` của mốc 08. Không cần Redis/Celery; cần giữ worker hoạt động để xử lý yêu cầu, kể cả khi đóng trình duyệt. Nếu worker bị ngắt giữa chừng, chạy lại và đợi hơn 5 phút để thu hồi claim treo. Nếu bị ngắt lúc tạo lịch Google, cần kiểm tra lịch đích theo TC09-15.

4. **Dữ liệu và luồng kiểm thử chính**

   Đăng nhập tài khoản A. Chuẩn bị một kế hoạch đã **Áp dụng** có ít nhất hai buổi học của A trong cùng tuần (có thể tạo việc thử với tên `M09 — thử đồng bộ`, deadline tương lai rồi tạo/áp dụng kế hoạch). Ghi lại tuần, tên việc và giờ bắt đầu/kết thúc. Chuẩn bị tài khoản B riêng để kiểm tra quyền dữ liệu.

   Mở [Đồng bộ Google Calendar](http://127.0.0.1:8000/integrations/google/) qua liên kết **Đồng bộ** trên thanh điều hướng. Thực hiện các test dưới đây và ghi `Đạt/Không đạt`, kèm lỗi thực tế. Chỉ dùng dữ liệu/lịch thử khi kiểm tra các thao tác hủy/xóa.

   | ID | Thao tác | Kết quả cần đạt |
   |---|---|---|
   | TC09-01 | Chưa thêm biến Google, mở Đồng bộ; thử phần Học tập/Lịch tuần | Thông báo chưa cấu hình OAuth, các phần còn lại hoạt động, không xuất hiện trang lỗi |
   | TC09-02 | Sau cấu hình và restart, bấm Kết nối Google; tự đăng nhập và cấp các quyền đã nêu | Trở về web, hiện Đã kết nối và đúng email Google; chưa có sự kiện mới chỉ vì vừa kết nối |
   | TC09-03 | Bắt đầu kết nối rồi chọn từ chối/hủy trên Google | Web báo chưa được cấp quyền, dữ liệu học tập giữ nguyên; có thể bắt đầu kết nối lại |
   | TC09-04 | Chọn một ngày bất kỳ trong tuần đã áp dụng và bấm Xem trước | Chuẩn hóa về thứ Hai; liệt kê đúng tên/giờ buổi của A theo giờ Việt Nam; mới xem trước chưa ghi lên Google |
   | TC09-05 | Chọn tuần trống hoặc chỉ có bản kế hoạch nháp | Có trạng thái chưa có thay đổi, không có nút xác nhận trống và không tạo lịch Google |
   | TC09-06 | Xem trước → Xác nhận khi worker chưa chạy | Hiện yêu cầu Đang chờ worker. Tải lại không tự tạo yêu cầu khác |
   | TC09-07 | Chạy worker một lượt rồi Tải lại kết quả; mở Google Calendar | Trạng thái Đồng bộ thành công, có lịch riêng Nhịp Học và các buổi đúng tiêu đề/ngày/giờ; các lịch cá nhân khác giữ nguyên |
   | TC09-08 | Xem trước và xác nhận lại cùng tuần, chạy worker | Không tạo thêm lịch riêng hoặc bản sự kiện trùng; cập nhật các sự kiện đã có |
   | TC09-09 | Sửa tên việc hoặc giờ một buổi hợp lệ trong web; xem trước/xác nhận/chạy worker | Sự kiện cũ đổi tên/giờ tương ứng, giữ cùng một sự kiện |
   | TC09-10 | Sửa tiêu đề/giờ của một sự kiện Nhịp Học trực tiếp trên Google; đồng bộ lại tuần đó | Web giữ nguyên; sự kiện Google được ghi lại theo dữ liệu web. Thay đổi trên Google không nhập về |
   | TC09-11 | Hủy một buổi thử trong web rồi đồng bộ lại đúng tuần cũ | Bản xem trước có một mục gỡ; worker gỡ đúng sự kiện; buổi khác và tuần khác giữ nguyên |
   | TC09-12 | Xóa công việc thử đã từng đồng bộ, rồi đồng bộ lại đúng tuần cũ | Vẫn thấy các mục gỡ nhờ ánh xạ còn giữ; các sự kiện tương ứng được gỡ khỏi Google |
   | TC09-13 | Sau khi mở bản xem trước, sửa dữ liệu trong tab khác rồi xác nhận bản cũ; hoặc đợi quá 10 phút | Yêu cầu xem trước lại, không xếp hàng bản dữ liệu cũ. Sửa dữ liệu khi job đang chờ cũng làm worker dừng với trạng thái Cần xem trước lại |
   | TC09-14 | Tạm ngắt mạng khi worker đồng bộ, khôi phục mạng rồi xem trước/xác nhận lại | Lỗi có thông báo rõ; phần đã gửi có thể còn trên Google; chạy lại hoàn tất bằng ánh xạ cũ, không chủ động tạo bản trùng |
   | TC09-15 | Nếu gặp Chưa xác nhận tạo lịch hoặc Không tìm thấy lịch đích | Kiểm tra Google trước. Chỉ khi muốn dùng lịch mới, đánh dấu xác nhận và bấm Cho phép tạo lịch mới; lần đồng bộ sau tạo lịch đích mới. Lịch/sự kiện cũ trên Google được giữ lại, cần tự xử lý nếu đã tồn tại |
   | TC09-16 | Ngắt kết nối khi còn một yêu cầu đang chờ, rồi chạy worker | Web chuyển Chưa kết nối, token local bị xóa, yêu cầu cũ mất hiệu lực; lịch/sự kiện Google đã có được giữ. Nếu chưa xác nhận thu hồi quyền, web hướng dẫn gỡ quyền trong tài khoản Google |
   | TC09-17 | Kết nối lại cùng Google; sau đó nếu muốn đổi Google thì ngắt kết nối trước | Cùng Google giữ lịch đích/ánh xạ. Đổi sang Google khác sau ngắt kết nối dùng lịch đích mới, giữ lịch cũ ở tài khoản cũ |
   | TC09-18 | B đăng nhập, xem Đồng bộ và thử mở URL kết quả của A | B không thấy kết nối/lịch sử của A; URL kết quả của A trả 404. Đăng xuất rồi mở Đồng bộ chuyển về đăng nhập |
   | TC09-19 | Mở giao diện trên điện thoại hoặc viewport 375 px; thử xem trước và đọc kết quả | Nội dung/nút xuống dòng, ngày giờ đọc được, không tràn ngang; thông báo trạng thái rõ |

   Với TC09-14/15, không cố làm mất mạng khi đang dùng dữ liệu quan trọng. Các nhánh mất phản hồi/claim treo được kiểm tra bằng API giả lập trong bộ test; có thể đánh dấu kiểm tra thật là chưa thực hiện nếu không chủ động tạo lỗi ngoài dịch vụ.

5. **Các quy tắc cần nhớ khi đối chiếu**

   - Chỉ đồng bộ buổi học của kế hoạch đã áp dụng, gồm buổi Đã học, khóa hoặc đã chỉnh tay. Buổi hủy không được đẩy; bản nháp, lịch bận, mốc deadline, tài liệu và nhật ký Pomodoro không được đẩy.
   - Web là nguồn chính. Sửa dữ liệu chưa tự đồng bộ; phải chọn đúng tuần, xem trước và xác nhận lại. Xóa việc/buổi vẫn cần đồng bộ tuần cũ để gỡ sự kiện Google. Danh sách gần đây hiển thị tối đa 10 yêu cầu của tài khoản đang đăng nhập.
   - Sự kiện dùng giờ Việt Nam, chế độ riêng tư và tắt nhắc mặc định của Google để tránh trùng nhắc việc trong ứng dụng. Ứng dụng không gửi lời mời người tham dự.
   - Chỉ quản lý sự kiện có ánh xạ và dấu nhận diện ứng dụng/ID nguồn khớp; nếu dấu bị đổi/mất thì dừng và báo lỗi thay vì sửa/gỡ nhầm. Sự kiện tự thêm trong lịch Google được giữ nguyên.
   - Mỗi kết nối chỉ có một yêu cầu đang chờ/chạy. Gửi lặp khi chưa xong đưa về yêu cầu hiện tại. Dữ liệu đổi giữa đợt làm dừng phần còn lại; cần xem trước và gửi lại.
   - Gặp lỗi không tự lặp vô hạn. Yêu cầu đã lỗi cần người dùng xem kết quả, xem trước và xác nhận lại. ID sự kiện được lưu trước khi gửi giúp xử lý lại khi mất phản hồi; không cam kết tuyệt đối mọi tình huống phía Google đều trả kết quả xác định.
   - Request đã tới Google trước lúc ngắt kết nối có thể vẫn hoàn tất. Token local bị xóa và worker cũ không được ghi lại token/kết quả vào phiên kết nối mới. Thu hồi quyền qua Google thất bại do mạng thì cần gỡ quyền thủ công trong tài khoản Google.
   - Không đổi khóa mã hóa hoặc xóa database để “sửa” lỗi đồng bộ: mất ánh xạ có thể để lại lịch/sự kiện cũ trên Google. Trước khi tạo lại lịch đích, kiểm tra và xử lý lịch cũ theo thông báo của ứng dụng.

6. **Chẩn đoán lỗi cấu hình**

   | Dấu hiệu | Cách kiểm tra |
   |---|---|
   | Chưa cấu hình Google OAuth | Client ID, secret và khóa Fernet phải có trong `.env`; khóa phải là kết quả generate_key; restart server/worker |
   | `redirect_uri_mismatch` trên Google | OAuth Client phải là Web application; URI Google Cloud và GOOGLE_REDIRECT_URI giống hệt, kể cả cổng và `/`; mở web bằng cùng host |
   | Không được phép truy cập app ở chế độ Testing | Thêm đúng Google email vào test users của project; tài khoản Workspace có thể bị chính sách tổ chức giới hạn |
   | Quyền Google hết hạn/bị từ chối | Bấm Cấp lại quyền Google, cấp đủ scope; kiểm tra Calendar API đã bật. Không gửi token cho người hỗ trợ |
   | Không đọc được thông tin cấp quyền | Khóa mã hóa đã thay hoặc token không hợp lệ; khôi phục khóa đúng hoặc cấp lại quyền |
   | Chờ worker mãi | Chạy đúng môi trường/project/database, xem terminal; tải lại kết quả. Claim treo cần hơn 5 phút để được xử lý lại |
   | Chưa xác nhận tạo lịch | Kiểm tra lịch Nhịp Học trong Google, tránh tạo lại mù; xem TC09-15 |

7. **Kết quả xác minh của agent**

   - Bộ kiểm thử mới kiểm tra OAuth/state/PKCE, mã hóa token và quyền thực cấp, chống truy cập chéo/CSRF, bản xem trước có chữ ký, dữ liệu đổi/hết hạn, trùng hàng đợi, tạo/cập nhật/gỡ, chạy lại sau mất phản hồi, 409, sự kiện đã xóa, bảo vệ dấu nhận diện, lịch đích không xác định, claim treo và ngắt kết nối.
   - Trình duyệt với database tạm và API giả lập: xem trước 2 cập nhật + 1 gỡ → xác nhận → thấy Đang chờ worker → tải lại thành công 2 cập nhật + 1 gỡ. Kiểm tra tuần trống và ngắt kết nối thành công. Viewport 375 px không tràn ngang.
   - Không tạo dữ liệu QA vào database thật, không gọi API Google thật. Đã dừng server/worker QA và dọn fixture tạm.
   - **38 test mới; tổng 219/219 PASS** với `manage.py test --noinput`. Lỗi mã hóa terminal Windows đã được tái hiện bằng test cp1252 và sửa trong worker Calendar. Ngắt kết nối cũng vô hiệu hóa phiên OAuth còn chờ trong trình duyệt.
   - `manage.py check`, `makemigrations --check --dry-run`, `pip check`, kiểm tra whitespace và SQLite integrity: PASS. Dữ liệu tài khoản/công việc/buổi học/nhật ký/nhắc việc khớp bản sao trước migration; bảng kết nối và job thật đều có 0 bản ghi. Lệnh worker thật chạy một lượt, xử lý 0 yêu cầu và không gọi Google.

8. **Commit/push sau khi bạn kiểm thử đạt**

   ```powershell
   git status --short
   git diff --check
   git check-ignore .env .venv/Scripts/python.exe db.sqlite3 db.sqlite3-before-m09
   git add integrations config/settings.py config/urls.py requirements.txt .env.example templates/base.html templates/integrations static/css/integrations.css README.md HD_Test.md docs/KE_HOACH_PHAT_TRIEN.md docs/THIET_KE_BAN_DAU.md
   git diff --cached --stat
   git diff --cached --check
   git commit -m "feat: add reviewed one-way Google Calendar sync"
   git push origin main
   ```

   Nhánh lúc bắt đầu là `main`; thay nếu bạn đã đổi nhánh. Giữ migration và `.env.example` trong commit, giữ `.env`, OAuth credentials, khóa mã hóa và database/bản sao lưu ngoài Git. Agent không stage/commit/push thay bạn.

   Dừng ở mốc 09. Nếu có lỗi, gửi ID test và thông báo thực tế đã che thông tin xác thực. Chỉ chuyển sang mốc 10 — AI hỗ trợ — sau khi bạn kiểm thử và xác nhận.

---

**Mốc 10 — AI hỗ trợ từ dữ liệu học tập thực tế**

Trạng thái: người dùng đã cho phép chuyển từ mốc 09. Đã triển khai mốc 10 và dừng để bạn kiểm thử, commit/push trước khi hoàn thiện/triển khai online.

Phạm vi: trang AI hỗ trợ, tổng hợp nhật ký 14 ngày/việc chưa xong/phương án bổ sung tuần hiện tại/cảnh báo bằng Python; xem trước dữ liệu, chủ động đồng ý gọi OpenAI, bốn nhóm nhận xét có căn cứ và lịch sử riêng. AI không tự sửa lịch hoặc tiến độ. Không cần API key để xem phần phân tích Python.

1. **Cập nhật và chạy**

   ```powershell
   Set-Location -LiteralPath 'D:\Python_DuAnLapKeHoachHocTap'
   & .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   & .\.venv\Scripts\python.exe manage.py migrate
   & .\.venv\Scripts\python.exe manage.py check
   & .\.venv\Scripts\python.exe manage.py test --noinput
   & .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
   ```

   Migration mới: `insights.0001_initial`. Agent đã sao lưu SQLite thành `db.sqlite3-before-m10` trước khi migrate. Không có thư viện mới ở mốc này; dùng Requests đã có. Nếu server cũ đang chạy, khởi động lại để nhận app/settings mới. Không chép đè `.env` hiện tại.

   Đăng nhập rồi mở [AI hỗ trợ](http://127.0.0.1:8000/insights/) từ thanh điều hướng. Phần AI gọi trực tiếp khi bấm yêu cầu, không cần worker riêng; các worker nhắc việc/Calendar vẫn độc lập.

2. **Bật OpenAI thật nếu muốn kiểm thử kết nối**

   Máy hiện tại chưa có `OPENAI_API_KEY`; agent chỉ kiểm thử bằng API giả lập. Để gọi thật, bạn cần tài khoản API có key, quyền dùng model và hạn mức sử dụng phù hợp. Phí API tách khỏi ứng dụng Django.

   Trong `.env` đang bị Git bỏ qua, thêm:

   ```dotenv
   OPENAI_API_KEY=<API key thật, chỉ lưu trên máy chủ>
   OPENAI_MODEL=gpt-5.6-terra
   ```

   Không giữ dấu `<...>` trong giá trị thật. Không dán key vào ô nhập trên web, ảnh chụp hoặc báo lỗi. Dừng và mở lại server sau khi cập nhật. Model này đã được đối chiếu trong [OpenAI Docs](https://developers.openai.com/api/docs/models/gpt-5.6-terra); quyền sử dụng thực tế phụ thuộc tài khoản API. Nếu đổi model, cần model hỗ trợ Responses API, JSON schema strict và reasoning low như request hiện tại.

   Ứng dụng gửi tới `https://api.openai.com/v1/responses`, dùng [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs), đặt `store=false` theo [Responses API](https://developers.openai.com/api/reference/resources/responses/methods/create). `store=false` không đồng nghĩa nhà cung cấp không lưu bất kỳ log nào; việc xử lý/lưu giữ phía dịch vụ còn theo chính sách của OpenAI. Giới hạn ứng dụng là 5 yêu cầu/user/ngày, không thay thế giới hạn chi tiêu của tài khoản API.

3. **Chuẩn bị dữ liệu có thể đối chiếu**

   Dùng tài khoản A với ít nhất hai công việc có hạn và thời lượng còn lại; một việc gần hạn chưa được xếp lịch và một việc khác có buổi đã áp dụng. Có thể thêm việc thử quá hạn để thấy cảnh báo rõ hơn. Tạo vài nhật ký trong 14 ngày gồm hôm nay: chẳng hạn hôm nay 25 phút, hôm qua 50 phút, 8 ngày trước 30 phút. Tổng mong đợi cho ba bản ghi này là 105 phút, 3/14 ngày có ghi nhận, trung bình 7,5 phút/ngày.

   Nếu đã có nhật ký khác trong khoảng này, tính thêm vào tổng. Không dùng số phút buổi trên lịch thay cho nhật ký: đặt lịch và học thực tế là hai dữ liệu riêng. Chuẩn bị tài khoản B không có dữ liệu để đối chiếu quyền và trạng thái trống.

4. **Checklist kiểm thử**

   Ghi `Đạt/Không đạt`, kèm thông báo thực tế theo ID. Các test gọi AI thật cần cấu hình ở phần 2 và bạn tự xem dữ liệu rồi đồng ý gửi.

   | ID | Thao tác | Kết quả cần đạt |
   |---|---|---|
   | TC10-01 | Chưa cấu hình key, mở AI hỗ trợ | Có số liệu, nhận xét ghi rõ Phân tích Python/Không gọi AI và hướng dẫn cấu hình; Học tập/Lịch tuần/Pomodoro vẫn dùng được |
   | TC10-02 | Đối chiếu nhật ký trong 14 ngày gồm hôm nay | Tổng phút, số bản ghi, ngày có ghi nhận và trung bình theo cả 14 ngày khớp; ngày không ghi nhận tính 0 |
   | TC10-03 | Thêm bản ghi 15 ngày trước, rồi bản ghi trong 14 ngày | Bản ngoài khoảng không cộng; bản trong khoảng được cộng. Phiên nghỉ/hủy không tự tăng số phút |
   | TC10-04 | Đối chiếu việc gần hạn và phương án trong Lịch tuần | Đúng số phút còn lại/đã dành tương lai/đề xuất thêm/chưa xếp; mở AI hỗ trợ không tạo bản kế hoạch mới |
   | TC10-05 | Xem việc quá hạn, thiếu lịch hoặc buổi trùng lịch bận | Giải thích khớp trang Cảnh báo; thiếu lịch không bị khẳng định là không thể xếp; buổi chưa ghi nhận không bị coi là đã học |
   | TC10-06 | Mở Xem chính xác dữ liệu sẽ gửi đến OpenAI | Có H/L/V/C/M, số phút, ngày giờ, tùy chọn và lý do do Python tính. Không có tên việc/môn/học kỳ, username/email, ghi chú, tài liệu, tên lịch bận hoặc token/key |
   | TC10-07 | Khi đã có key, không tích đồng ý rồi bấm Yêu cầu AI phân tích | Trình duyệt yêu cầu tích checkbox; request thiếu consent bị backend từ chối, không gọi API |
   | TC10-08 | Xem dữ liệu, tích đồng ý rồi gửi | Nhận bốn nhóm: Tóm tắt, Thói quen học, Gợi ý phân bổ, Giải thích cảnh báo; mỗi nhận xét có mã căn cứ và nhãn local để đối chiếu |
   | TC10-09 | Đối chiếu trước/sau yêu cầu AI | Lịch/buổi/khóa buổi, thời lượng công việc và nhật ký giữ nguyên. Muốn đổi lịch phải vào Xem trước kế hoạch rồi kiểm tra/áp dụng riêng |
   | TC10-10 | Tải lại trang kết quả hoặc gửi lại cùng biểu mẫu | Đọc báo cáo đã có, không gọi AI lần nữa và không thêm báo cáo trùng |
   | TC10-11 | Tạo yêu cầu khác trong vòng 60 giây, hoặc khi một yêu cầu khác đang chạy | Báo cần chờ; không phát sinh lời gọi mới. Sau đủ 60 giây và không có yêu cầu chạy mới được tạo tiếp |
   | TC10-12 | Mở trang xem trước, sửa số liệu/giờ học/tên việc ở tab khác, rồi xác nhận bản cũ; hoặc đợi quá 10 phút | Yêu cầu xem lại bản dữ liệu mới; bản cũ không được gửi |
   | TC10-13 | Mở báo cáo thành công, sau đó sửa nhật ký/việc/tùy chọn liên quan rồi tải lại báo cáo | Báo dữ liệu đã thay đổi; nội dung và nhãn trong báo cáo cũ giữ theo thời điểm tạo; có đường về dữ liệu hiện tại |
   | TC10-14 | Dùng key không hợp lệ hoặc tài khoản chưa có hạn mức, rồi gửi | Lỗi được giải thích, không lộ key/raw provider response; vẫn quay lại được phần Python. Lỗi sau khi tạo yêu cầu được tính vào giới hạn |
   | TC10-15 | Lỗi mạng hoặc request bị gián đoạn | Không tự gọi lại API. Có lịch sử lỗi/đang xử lý; nếu treo quá 5 phút, yêu cầu mới đánh dấu bản cũ bị gián đoạn. Kiểm tra mức sử dụng API trước khi thử lại vì nhà cung cấp có thể đã xử lý |
   | TC10-16 | Đăng nhập B và thử mở URL kết quả của A | B không thấy số liệu/tên việc/lịch sử của A; URL kết quả A trả 404. Chưa đăng nhập thì được chuyển tới đăng nhập |
   | TC10-17 | B chưa có nhật ký/công việc, mở AI hỗ trợ | Thấy 0 và lời nhắc chưa đủ dữ liệu; không tự suy ra không học, không bịa công việc/cảnh báo |
   | TC10-18 | Thử giao diện ở 375 px | Thẻ số liệu, checkbox, nút, nội dung/căn cứ xuống dòng và không tràn ngang; JSON xem trước có khu vực đọc riêng |

   Các nhánh phản hồi không đúng schema/căn cứ lạ, từ chối, dở dang, giới hạn 5 lần/ngày và kết quả về muộn được kiểm tra bằng test giả lập. Không cần cố gọi API thật nhiều lần chỉ để tạo lỗi hoặc chạm giới hạn; có thể chạy:

   ```powershell
   & .\.venv\Scripts\python.exe manage.py test insights --noinput
   ```

5. **Phạm vi dữ liệu và giới hạn**

   - Nhật ký gồm hôm nay và 13 ngày trước theo giờ Việt Nam. So sánh hai nhóm 7 ngày liền nhau; không suy ra giờ học hiệu quả hoặc mức hiểu bài vì dữ liệu này chưa được thu thập.
   - Việc chưa hoàn thành lấy tối đa 20 việc gần hạn nhất, cùng hạn ưu tiên cao. Cảnh báo lấy tối đa 20 mục, từ việc quá hạn/thiếu lịch rồi đến xung đột buổi trong phạm vi 7 ngày của planner. Tổng số và số được đưa vào có trong payload; phần Python tóm tắt tối đa 5 việc và 5 cảnh báo, có thêm nhắc buổi chưa ghi nhận khi cần.
   - Phân bổ dựa trên thuật toán Bổ sung của tuần hiện tại, giữ mọi buổi đã áp dụng; chưa phải phương án Xếp lại và chưa được lưu/áp dụng. Quỹ L02 là giới hạn khả dụng trước khi thêm các đề xuất; không cộng lần nữa vào số phút đã đề xuất.
   - Phút trong buổi đặt lịch và phút thực học trong nhật ký không tự thay thế nhau. Đã học đủ phút chưa chứng minh đã hoàn thành công việc. Thiếu nhật ký không chứng minh người dùng không học.
   - AI chỉ thấy payload dùng mã, không thấy bảng mã/nhãn local. Các nhận xét dẫn H/L/V/C; tên local được gắn trong web để người dùng đối chiếu. Kiểm tra schema/căn cứ không bảo đảm mọi nhận xét hoặc con số AI diễn giải đều đúng.
   - Mỗi nhóm AI tối đa 5 mục, text tối đa 1200 ký tự, mỗi mục 1–5 mã căn cứ hợp lệ. Kết quả không hợp lệ/từ chối/dở dang không được hiển thị như một phân tích thành công. Không render HTML do AI trả về và không có tool cho AI thao tác ứng dụng.
   - Tối đa 5 yêu cầu/ngày/user, giãn ít nhất 60 giây. Thiếu key, thiếu đồng ý hoặc bản xem trước không hợp lệ không tạo yêu cầu. Lỗi xảy ra sau khi tạo báo cáo vẫn tính giới hạn. Yêu cầu lỗi không tự retry.
   - Gọi API trực tiếp ngoài transaction, timeout kết nối 5 giây/đọc 40 giây; thời gian thực tế còn phụ thuộc kết nối/nhà cung cấp. Nếu web bị đóng trong khi xử lý, kiểm tra lịch sử trước khi tạo yêu cầu mới. Bản treo được đánh dấu khi bắt đầu yêu cầu khác sau hơn 5 phút; GET không tự chạy lại.
   - Lịch sử giữ dữ liệu/nhãn lúc yêu cầu và hiển thị 10 bản gần nhất của chủ sở hữu. Thời gian trôi qua không tự tạo phân tích mới. Dữ liệu học tập thay đổi cần xem lại hiện trạng trước khi dựa vào báo cáo cũ.

6. **Kết quả xác minh của agent**

   - **26 test mới; tổng 245/245 PASS**. Bao phủ khoảng ngày/múi giờ, tổng/so sánh, quyền A/B, payload không có văn bản riêng, nháp/hủy/đã học, quỹ lịch và cảnh báo thực tế, giới hạn payload, consent/CSRF, chữ ký/hết hạn/dữ liệu đổi, idempotency, cooldown/hạn ngày, request treo/kết quả muộn, schema/căn cứ, HTML escape và lỗi API.
   - Trình duyệt với database tạm: tổng 230 phút/5 ngày → mở JSON đã dùng mã → đồng ý → nhận đủ nhóm báo cáo và căn cứ. Lần tiếp theo giả lập 429 hiển thị lỗi hạn mức; tài khoản trống chỉ thấy số liệu 0 và hướng dẫn. Trang chính/kết quả ở viewport 375 px không tràn ngang.
   - Chỉ dùng API giả lập, không gửi dữ liệu ra OpenAI thật và không phát sinh phí API. Server QA đã dừng; fixture riêng được dọn, không đưa dữ liệu mẫu vào SQLite thật.
   - Đã áp dụng migration sau sao lưu `db.sqlite3-before-m10`. `manage.py check`, kiểm tra migration thiếu, `pip check`, whitespace và SQLite integrity: PASS. Dữ liệu người dùng/nghiệp vụ cũ giữ nguyên; Django chỉ bổ sung content type và 4 quyền mặc định cho model mới. Bảng AI thật có 0 báo cáo. Kiểm thử kết nối/model thật vẫn cần bạn thực hiện theo phần 2.

7. **Commit/push sau khi bạn kiểm thử đạt**

   ```powershell
   git status --short
   git diff --check
   git check-ignore .env .venv/Scripts/python.exe db.sqlite3 db.sqlite3-before-m10
   git add insights config/settings.py config/urls.py .env.example templates/base.html templates/insights static/css/insights.css README.md HD_Test.md docs/KE_HOACH_PHAT_TRIEN.md docs/THIET_KE_BAN_DAU.md
   git diff --cached --stat
   git diff --cached --check
   git commit -m "feat: add grounded study insights and opt-in AI reports"
   git push origin main
   ```

   Nhánh lúc bắt đầu là `main`; thay nếu bạn đã đổi nhánh. Giữ migration và `.env.example`, không commit `.env` thật, key, database hoặc bản sao lưu. Agent không stage/commit/push thay bạn.

   Dừng ở mốc 10. Nếu lỗi, gửi ID test và thông báo đã che thông tin xác thực. Chỉ chuyển sang phần hoàn thiện/triển khai online sau khi bạn kiểm thử và xác nhận.
