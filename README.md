# Python_DuAnLapKeHoachHocTap

Ứng dụng lập kế hoạch học tập cá nhân có AI gợi ý lịch, định hướng Django với Python xử lý nghiệp vụ chính.

- [Kế hoạch phát triển](docs/KE_HOACH_PHAT_TRIEN.md)
- [Thiết kế ban đầu](docs/THIET_KE_BAN_DAU.md)
- [Hướng dẫn kiểm thử từng bước](HD_Test.md)

Hiện tại: **mốc 10 — AI hỗ trợ từ dữ liệu học tập thực tế**, đang chờ người dùng kiểm thử và push GitHub. Tên hiển thị tạm thời của ứng dụng là **Nhịp Học**.

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

Mốc này dùng SQLite; PostgreSQL và cấu hình triển khai online được thực hiện ở mốc sau. Đã có tài khoản, quản lý học tập, lịch bận, tùy chọn thời gian học, lịch tuần và thuật toán Python tự xếp buổi học.

Các trang chính:

- [Đăng ký](http://127.0.0.1:8000/accounts/register/): tên đăng nhập duy nhất, email và mật khẩu.
- [Đăng nhập](http://127.0.0.1:8000/accounts/login/): dùng tên đăng nhập.
- [Tài khoản của bạn](http://127.0.0.1:8000/accounts/profile/): yêu cầu đăng nhập, có liên kết đổi mật khẩu.
- [Môn học](http://127.0.0.1:8000/studies/subjects/): thêm/sửa/xóa, màu, học kỳ và lưu trữ.
- [Công việc](http://127.0.0.1:8000/studies/tasks/): deadline, ưu tiên, thời lượng, trạng thái và lọc quá hạn.
- [Tài liệu](http://127.0.0.1:8000/studies/materials/): liên kết HTTP/HTTPS theo môn hoặc công việc.
- [Lịch tuần](http://127.0.0.1:8000/planner/): lịch bận, buổi học đã áp dụng, deadline và khoảng trống từ hiện tại.
- [Tạo kế hoạch](http://127.0.0.1:8000/planner/plans/new/): chọn tuần và chế độ Bổ sung/Xếp lại, xem trước rồi áp dụng vào lịch.
- [Cảnh báo](http://127.0.0.1:8000/planner/alerts/): việc quá hạn, thiếu lịch trước hạn, buổi xung đột và buổi đã kết thúc chưa ghi nhận.
- [Lịch bận](http://127.0.0.1:8000/planner/busy/): một lần/lặp hằng tuần, hỗ trợ qua đêm.
- [Giờ học](http://127.0.0.1:8000/planner/preferences/): ngày được học, khung giờ chung, giới hạn phút/ngày, độ dài buổi và nghỉ.
- [Tập trung](http://127.0.0.1:8000/focus/): Pomodoro 25 phút học/5 phút nghỉ, tạm dừng/tiếp tục, lưu sớm hoặc hủy.
- [Nhật ký](http://127.0.0.1:8000/focus/logs/): phút học từ Pomodoro và nhập tay, lọc ngày, sửa/xóa.
- [Thống kê](http://127.0.0.1:8000/focus/statistics/): tổng phút, ngày có học, trung bình và phân bổ theo ngày/môn/nguồn, xử lý bằng Python.
- [Thông báo](http://127.0.0.1:8000/notifications/): nhắc deadline/buổi học, đọc/chưa đọc và lịch sử email.
- [Tùy chọn nhắc](http://127.0.0.1:8000/notifications/preferences/): bật riêng từng kênh, chọn thời gian nhắc trước hạn/buổi.
- [Đồng bộ](http://127.0.0.1:8000/integrations/google/): kết nối Google, xem trước theo tuần, xác nhận và xem kết quả đồng bộ.
- [AI hỗ trợ](http://127.0.0.1:8000/insights/): số liệu 14 ngày, nhận xét Python, xem trước dữ liệu gửi AI và lịch sử phân tích riêng.
- [Quản trị](http://127.0.0.1:8000/admin/): tài khoản quản trị có quyền phù hợp.

Tạo quản trị viên bằng `& .\.venv\Scripts\python.exe manage.py createsuperuser`, nhập thông tin trực tiếp trong terminal. Đăng xuất qua nút trên giao diện dùng POST, không mở URL đăng xuất bằng GET.

Chạy kiểm thử tự động:

```powershell
& .\.venv\Scripts\python.exe manage.py test --noinput
```

Các kiểm thử dùng database riêng trong bộ nhớ, không sửa tài khoản đang lưu ở `db.sqlite3`. Xem checklist đầy đủ và cách kiểm tra khóa/mở tài khoản trong `HD_Test.md`.

Mốc 03 có migration mới: chạy `manage.py migrate` trước khi mở phần Học tập. Mỗi người chỉ xem/sửa/xóa dữ liệu mình sở hữu. Xóa môn/công việc gỡ liên kết nhưng giữ lại tài liệu; lưu trữ môn giữ nguyên các liên kết. Công việc mới có thời lượng còn lại bằng ước tính; chọn Hoàn thành đưa thời lượng còn lại về 0.

Mốc 04 thêm migration `planner/0001_initial.py`; tiếp tục chạy `manage.py migrate` khi cập nhật. Lịch tuần dựng bằng Python/Django Templates, tuần bắt đầu thứ Hai và dùng giờ Việt Nam. Lịch bận chồng nhau được gộp khi tính khoảng trống; deadline chỉ là mốc hạn, không chiếm một khoảng thời gian.

Mốc 05 thêm migration `planner/0002_studyplan_studysession.py`. Thuật toán tham lam xếp deadline gần trước, cùng hạn thì ưu tiên cao trước; tôn trọng lịch bận, khung học, phút/ngày, chia buổi và nghỉ. Bản xem trước chưa chiếm lịch; áp dụng kiểm tra lại dữ liệu/thời gian trong transaction. Giữ các buổi đã áp dụng và trừ phút tương lai đã dành cho công việc ở mọi tuần để tránh xếp lại. Xếp lịch không tự giảm thời lượng còn lại. Xóa công việc cũng xóa các buổi học của công việc, vẫn giữ liên kết tài liệu.

Mốc 06 thêm migration `planner/0003_studyplan_mode_studyplan_replacement_ids_and_more.py`; chạy `manage.py migrate` và khởi động lại server. Từ chi tiết kế hoạch đã áp dụng, có thể chỉnh giờ/độ dài buổi tương lai, khóa/mở khóa, ghi nhận Đã học hoặc Hủy/bỏ qua. Chỉnh tay phải đúng khung học, deadline, quỹ ngày, không trùng và đủ nghỉ; không vượt thời lượng công việc còn lại. Nhập số phút thực tế còn cần khi ghi nhận; nhập 0 đánh dấu việc hoàn thành. Có form Cập nhật tiến độ riêng trên danh sách công việc.

Chế độ Xếp lại chỉ thay buổi tự động chưa bắt đầu trong tuần được chọn, giữ buổi khóa, đã chỉnh tay, đang học, đã học và các tuần khác. Xem trước chỉ đọc các đặt chỗ cũ; khi áp dụng mới hủy buổi cũ và thêm buổi mới trong cùng transaction. Buổi bị hủy giữ dấu vết, không còn chiếm lịch/quỹ ngày. Bổ sung vẫn giữ mọi buổi đã áp dụng.

Thay đổi đầu vào chưa tự chạy xếp lại; cần chọn Xếp lại và kiểm tra bản xem trước. Buổi khóa hoặc chỉnh tay có xung đột cần xử lý trực tiếp. Cảnh báo trong ứng dụng xét mọi việc quá hạn, việc đến hạn/buổi sắp diễn ra trong 7 ngày và tối đa 20 buổi chưa ghi nhận gần nhất. Chưa gửi email. Thuật toán chưa bảo đảm tối ưu toàn cục.

Mốc 07 thêm app `focus` và migration `focus/0001_initial.py`. Mỗi tài khoản chỉ có một phiên học/nghỉ đang chạy hoặc tạm dừng. Thời gian tính ở Python, JavaScript chỉ hiển thị/đồng bộ đồng hồ. Tải lại hoặc đóng trang không làm mất phiên. Hết giờ vẫn cần bấm Lưu và kết thúc; phút học bị giới hạn tối đa 25, nghỉ/tạm dừng không cộng. Kết thúc sớm chỉ ghi phút tròn, dưới một phút không tạo nhật ký. Hủy không ghi nhật ký; gửi lặp thao tác kết thúc không ghi hai lần.

Nhật ký không tự giảm thời lượng công việc hoặc đánh dấu buổi trên lịch đã học; tiếp tục dùng Cập nhật tiến độ/Ghi nhận buổi của mốc 06. Nhật ký nhập tay được sửa ngày/phút/việc/ghi chú; nhật ký Pomodoro chỉ sửa ghi chú. Xóa nhật ký giảm thống kê và không được tự tạo lại khi kết thúc lại cùng phiên. Xóa công việc giữ nhật ký/Pomodoro với tên việc và môn đã chụp lúc ghi nhận.

Nhật ký/thống kê mặc định xem 7 ngày gần nhất, hỗ trợ khoảng 1–366 ngày đã qua. Pomodoro quy toàn bộ phút vào ngày bắt đầu phiên theo giờ Việt Nam, không chia ở nửa đêm. Môn nhóm theo nhãn trong nhật ký; đổi nhãn có thể tách nhóm lịch sử. Chưa có tự lặp chu kỳ, nghỉ dài, chuông/Pomodoro push hoặc tự xác nhận đã học.

Mốc 08 thêm app `notifications` và migration `notifications/0001_initial.py`. Mặc định nhận thông báo trong web, email tắt; nhắc deadline trước 24 giờ, buổi học trước 15 phút. Chọn được deadline 1/3/24 giờ và buổi học 5/15/30 phút. Email lấy từ tài khoản, phải bật chủ động. Web chỉ xem/lưu tùy chọn/đánh dấu đã đọc hoặc yêu cầu gửi lại; tạo/gửi nhắc chạy trong worker Python riêng dùng hàng đợi database.

Sau khi migrate và mở web, mở terminal thứ hai tại thư mục dự án:

```powershell
& .\.venv\Scripts\python.exe manage.py process_reminders --watch
```

Worker kiểm tra mỗi 60 giây, Ctrl+C để dừng. Muốn kiểm thử một lượt: `manage.py process_reminders` không có `--watch`. Không cần Redis/Celery ở mốc local này; có thể gọi lệnh một lượt bằng bộ lập lịch khi triển khai. Worker phải hoạt động để tạo/gửi nhắc, kể cả khi trình duyệt đã đóng.

Email mặc định dùng console backend, nội dung xuất hiện trong terminal worker. SMTP thật cấu hình bằng các biến `EMAIL_*`, `DEFAULT_FROM_EMAIL`, `SITE_URL` trong `.env` theo `.env.example`; chưa thử gửi qua nhà cung cấp thật trong mốc này. Không ghi đè `.env` đang dùng hoặc đưa thông tin đăng nhập SMTP lên GitHub.

Mỗi đối tượng/thời điểm/kênh có một bản nhắc; đổi độ nhắc sớm không gửi lại bản đã xử lý. Đổi deadline/giờ buổi tạo nhắc cho thời điểm mới. Trước gửi kiểm tra lại tài khoản, kênh nhận, công việc, buổi và thời điểm; bỏ nhắc cũ/đã quá giờ. Email bị từ chối được tự thử tối đa 3 lần, cách ít nhất 1 phút; mất kết nối/kẹt khi gửi chuyển Chưa xác nhận và cần người dùng kiểm tra hộp thư trước khi yêu cầu gửi lại. Hệ thống SMTP không bảo đảm thư đã vào inbox hoặc tuyệt đối không trùng khi kết quả gửi không xác định. Xem checklist và cấu hình kiểm thử mốc 08 ở cuối `HD_Test.md`.

Mốc 09 thêm app `integrations` và migration `integrations/0001_initial.py`. Cài lại `requirements.txt`, chạy `manage.py migrate` và khởi động lại server. Các biến `GOOGLE_*` trong `.env.example` là tùy chọn; thiếu cấu hình thì trang Đồng bộ hướng dẫn cấu hình, các phần học tập vẫn hoạt động. Xem phần mốc 09 trong `HD_Test.md` để tạo OAuth Client loại Web application, khai báo callback và tạo khóa Fernet. Không chép đè `.env`, không đưa client secret, khóa mã hóa hoặc database lên GitHub.

Sau khi kết nối, chọn tuần → xem trước → xác nhận; mở terminal riêng chạy:

```powershell
& .\.venv\Scripts\python.exe manage.py process_calendar_sync --watch
```

Worker kiểm tra hàng đợi mỗi 60 giây, Ctrl+C để dừng; bỏ `--watch` để xử lý một lượt. Chỉ xử lý tuần đã được xác nhận, không tự đồng bộ mỗi khi sửa lịch. Không cần Redis/Celery ở mốc local. Worker nhắc việc và worker Calendar là hai tiến trình độc lập.

Ứng dụng xin quyền `calendar.app.created` để tạo lịch Google riêng **Nhịp Học**, cùng quyền định danh/email để hiển thị tài khoản kết nối. Chỉ đẩy buổi học của kế hoạch đã áp dụng, gồm buổi đã học; không nhập lịch Google về web. Mỗi lần đồng bộ ghi lại giờ/nội dung theo web, gỡ sự kiện của buổi hủy/xóa, không sửa sự kiện thiếu dấu nhận diện của ứng dụng. Token được mã hóa trước khi lưu. Ngắt kết nối xóa token trong web và cố thu hồi quyền Google, giữ lịch/sự kiện đã có.

Nếu mất phản hồi khi tạo lịch, hệ thống yêu cầu kiểm tra Google rồi xác nhận trước khi tạo lịch đích mới. Ánh xạ sự kiện được lưu trước khi gửi để có thể chạy lại sau mất mạng. Kiểm thử tự động và trình duyệt ở mốc này dùng API giả lập; OAuth và Calendar thật cần bạn cấu hình và kiểm thử theo `HD_Test.md`.

Mốc 10 thêm app `insights` và migration `insights/0001_initial.py`. Chạy `manage.py migrate` và khởi động lại server. Trang AI hỗ trợ luôn hiển thị số liệu/nhận xét do Python tính: nhật ký 14 ngày gồm hôm nay, so sánh hai nhóm 7 ngày, việc chưa hoàn thành, phương án bổ sung tuần hiện tại và cảnh báo thực tế. Không có API key thì phần này vẫn dùng được và được ghi rõ là phân tích Python.

Muốn dùng AI thật, thêm `OPENAI_API_KEY` vào `.env`; `OPENAI_MODEL` mặc định `gpt-5.6-terra`. API key chỉ dùng ở máy chủ, không nhập vào web hoặc commit lên GitHub. Sau khi restart server, mở AI hỗ trợ → xem dữ liệu gửi → chủ động đồng ý → Yêu cầu AI phân tích. Dùng OpenAI Responses API với Structured Outputs, `store=false`, giới hạn đầu ra và timeout; không cần cài thêm SDK hoặc chạy worker cho phần AI ở mốc này. Hạn mức sử dụng và phí API thuộc tài khoản OpenAI riêng.

Dữ liệu gửi dùng mã việc/môn, số phút, deadline, tùy chọn học và cảnh báo; không gửi tên, email, ghi chú, tài liệu hoặc token Google. Mỗi nhận xét phải dẫn mã căn cứ hợp lệ, được kiểm tra trước khi hiển thị; điều này không bảo đảm diễn giải của AI luôn đúng. Kết quả chỉ để tham khảo, không tự sửa lịch/tiến độ. Lịch sử giữ bản dữ liệu và kết quả theo chủ sở hữu, phát hiện khi dữ liệu đã đổi. Tối đa 5 yêu cầu/ngày/user, cách nhau ít nhất 60 giây; không tự gọi lại khi lỗi. Chi tiết cấu hình, kiểm thử và giới hạn ở phần mốc 10 cuối `HD_Test.md`. Kiểm thử agent dùng API giả lập; chưa gửi dữ liệu hoặc tạo phí trên OpenAI thật.
