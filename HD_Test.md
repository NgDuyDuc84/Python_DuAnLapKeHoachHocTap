**Hướng dẫn kiểm thử theo từng mốc**

Sau mỗi mốc, người dùng kiểm thử, ghi nhận kết quả rồi commit/push GitHub. Chỉ chuyển mốc khi người dùng xác nhận. Khi có mốc mới, bổ sung vào tài liệu và giữ lịch sử các mốc cũ.

Mốc cần kiểm thử hiện tại: **mốc 03 — môn học, công việc và tài liệu**, ở phần cuối tài liệu.

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

Trạng thái: chờ người dùng kiểm thử và push GitHub. Người dùng đã chọn ưu tiên chức năng học tập ở mốc này; PostgreSQL/triển khai online giữ cho mốc sau.

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
