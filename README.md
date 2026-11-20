# Nhịp Học

Web lập kế hoạch học tập cá nhân bằng Django/Python, giao diện tiếng Việt và giờ Việt Nam. Dữ liệu được tách riêng theo tài khoản.

## Tính năng hiện có

- Đăng ký, đăng nhập, đổi mật khẩu và quản lý tài khoản.
- Quản lý môn học, công việc, deadline, mức ưu tiên, tiến độ và tài liệu liên kết hoặc tệp tải lên (tối đa 10 MB/tệp). Chủ sở hữu có thể tải xuống, thay hoặc gỡ tệp. Tệp nhỏ được lưu cùng database để giữ qua redeploy Render; dung lượng tệp tính vào dung lượng database.
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

Mỗi lệnh chạy ở một terminal; Ctrl+C để dừng. Email mặc định chỉ xuất ra terminal. Gửi email thật cần các biến `EMAIL_*` (SMTP) hoặc Gmail API qua HTTPS như bên dưới; Google Calendar cần `GOOGLE_*` và callback đúng địa chỉ web; AI cần `GROQ_API_KEY` và `GROQ_MODEL` khả dụng trong hạn mức miễn phí của Groq. Xem tên biến trong `.env.example`. Khi chưa cấu hình dịch vụ ngoài, chức năng học tập và phân tích Python vẫn hoạt động. Khóa và mật khẩu chỉ lưu trong môi trường, không đưa lên Git.

## Cấu hình Groq, Calendar và Gmail trên Render

Thực hiện trong Environment của web service. Giữ nguyên các biến secret/database do Render cấp. Giữ Groq ở Free Plan, không nâng cấp Developer nếu chỉ muốn dùng miễn phí. Tài khoản trường có thể cần quản trị viên cho phép tạo Google Cloud project hoặc cấp quyền OAuth.

Gom các khóa và tùy chọn tích hợp thực tế vào một file riêng `.env.render` (đã được Git bỏ qua), dùng file này khi nhập biến môi trường lên Render. `.env.example` là mẫu chạy tại máy; `deploy/production.env.example` là mẫu production tự quản lý. Hai file mẫu không chứa khóa thật.

1. **Groq:** tạo API key trong [Groq Console](https://console.groq.com/keys). Đặt `GROQ_API_KEY` và `GROQ_MODEL=openai/gpt-oss-20b`. Model này hỗ trợ JSON schema nghiêm ngặt và có hạn mức Free Plan; kiểm tra hạn mức thực tế của tài khoản trước demo. Trang AI chỉ gửi dữ liệu đã xem trước sau khi người dùng đồng ý. Tên model có tiền tố `openai/` nhưng yêu cầu được gửi đến Groq, không dùng API key hay thanh toán OpenAI.
2. **Google Cloud:** bật Google Calendar API và Gmail API trong dự án sở hữu OAuth client. Trong Google Auth Platform, khai báo ứng dụng; với ứng dụng External đang Testing, thêm email demo vào Test users. Tạo OAuth client loại **Web application**, thêm redirect URI `https://<ten-web>.onrender.com/integrations/google/callback/` và `https://developers.google.com/oauthplayground`. Lưu client ID/secret vào `GOOGLE_CLIENT_ID` và `GOOGLE_CLIENT_SECRET`.
3. **Calendar:** đặt `SITE_URL=https://<ten-web>.onrender.com` và `GOOGLE_REDIRECT_URI` đúng callback đã đăng ký. Tạo khóa một lần bằng `cryptography.fernet.Fernet.generate_key()`, lưu vào `GOOGLE_TOKEN_ENCRYPTION_KEY`; giữ nguyên khóa này qua các lần deploy để đọc được token đã lưu. Đăng nhập Nhịp Học → menu tài khoản → Kết nối Google → cấp quyền Calendar. Ứng dụng chỉ yêu cầu quyền với lịch do chính ứng dụng tạo, cùng thông tin tài khoản cơ bản.
4. **Gmail trên Render Free:** các cổng SMTP 25/465/587 bị chặn, nên đặt `EMAIL_BACKEND=notifications.gmail_backend.EmailBackend`. Trong [OAuth Playground](https://developers.google.com/oauthplayground/), mở Settings → bật **Use your own OAuth credentials**, nhập cùng client ID/secret; chọn Access type **Offline**, prompt **Consent Screen**. Chỉ cấp scope `https://www.googleapis.com/auth/gmail.send`, đăng nhập tài khoản gửi, rồi Exchange authorization code for tokens. Lưu **refresh token** vào `GMAIL_REFRESH_TOKEN`; không dùng access token ngắn hạn. Đặt `DEFAULT_FROM_EMAIL=Nhịp Học <email-tai-khoan-gui>`. Không cần mật khẩu Gmail hay App Password. Token email này dành cho máy chủ gửi nhắc; độc lập với kết nối Calendar của từng người dùng. Với ứng dụng External ở chế độ Testing, refresh token cho các scope này thường hết hạn sau 7 ngày; tài khoản trường còn có thể chịu chính sách riêng.
5. **Triển khai và kiểm tra:** Manual Deploy đúng commit. Tại `/insights/`, xem trước và gửi một yêu cầu AI; tại `/integrations/google/`, kết nối rồi xem trước/xác nhận đồng bộ một tuần; đăng ký tài khoản Nhịp Học với email thật, bật email nhắc và tạo việc chưa hoàn thành đến hạn trong khoảng nhắc để kiểm tra hộp thư/lịch sử. Launcher `deploy.demo` chạy cả hai worker khi web đang thức. Render Free có thể ngủ nên không bảo đảm gửi nhắc khi không có truy cập.

Tất cả API key, OAuth secret, refresh token và khóa mã hóa phải nằm trong Render Environment hoặc file `.env.*` được Git bỏ qua. Không đưa vào mã nguồn, ảnh báo cáo hoặc log. Kiểm tra trạng thái Google Cloud trước khi chia sẻ bản demo cho tài khoản ngoài danh sách thử nghiệm.

Tài liệu: [Groq Free Plan](https://console.groq.com/docs/rate-limits), [Groq Structured Outputs](https://console.groq.com/docs/structured-outputs), [Google Calendar OAuth](https://developers.google.com/workspace/calendar/api/auth), [Gmail gửi qua API](https://developers.google.com/workspace/gmail/api/guides/sending), [OAuth refresh token](https://developers.google.com/identity/protocols/oauth2#expiration), [giới hạn Render Free](https://render.com/docs/free).

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
