**Kế hoạch phát triển — ứng dụng lập kế hoạch học tập cá nhân**

Định hướng đã thống nhất: Django/Python xử lý nghiệp vụ, PostgreSQL cho bản online, giao diện Django Templates và JavaScript tối thiểu cho lịch/Pomodoro. Các giai đoạn không gắn với lịch trình hay số thành viên.

1. Chốt quy tắc nghiệp vụ, dữ liệu và màn hình.
2. Dựng bộ khung Django, giao diện chung và môi trường triển khai.
3. Làm tài khoản, quyền người dùng/quản trị và bảo vệ dữ liệu theo chủ sở hữu.
4. Làm môn học, công việc/deadline/ưu tiên/thời lượng và tài liệu dạng liên kết.
5. Làm lịch bận, tùy chọn học và lịch tuần.
6. Viết thuật toán xếp lịch Python: tìm khoảng trống, chia buổi, phân bổ, kiểm tra và báo phần chưa xếp được.
7. Làm chỉnh sửa, khóa buổi, theo dõi tiến độ, xếp lại lịch và cảnh báo deadline.
8. Làm Pomodoro, nhật ký học và thống kê bằng Python.
9. Làm thông báo và email nhắc bằng tác vụ nền.
10. Tích hợp đồng bộ một chiều từ ứng dụng sang Google Calendar; phạm vi này được ghi rõ vì đề chưa quy định chiều đồng bộ.
11. Tích hợp AI nhận xét thói quen, gợi ý phân bổ, tóm tắt việc và giải thích cảnh báo từ dữ liệu thực.
12. Hoàn thiện UI/UX, kiểm thử toàn bộ trên URL thật, dữ liệu demo và tài liệu bảo vệ.

Phần lõi phải hoạt động độc lập với AI. Thuật toán không được xếp trùng lịch bận, vượt giới hạn học hoặc đặt buổi sau deadline. Nếu chưa xếp đủ phải công khai phần còn thiếu; thuật toán tham lam chưa chứng minh lịch tối ưu toàn cục.

Các chức năng quản lý tài khoản, lịch, tài liệu, Pomodoro, nhắc việc, đồng bộ và AI đều phải hoàn thành trước nghiệm thu. Bản khung local chưa phải sản phẩm hoàn chỉnh theo đề.

**Quy trình từng mốc**

- Mỗi mốc có phạm vi, kiểm tra kỹ thuật và checklist trong `HD_Test.md`.
- Dừng sau mốc để người dùng kiểm thử, commit và push GitHub.
- Chỉ làm mốc tiếp theo sau khi người dùng xác nhận; nếu có lỗi thì sửa tại mốc hiện tại.
- Giữ kết quả và checklist các mốc trước trong `HD_Test.md` khi thêm mốc mới.

**Mốc 01:** đã hoàn thành tài liệu thiết kế và phần khởi tạo local của nền Django; trang chủ, template chung, static CSS, cấu hình `.env` và SQLite. Người dùng đã cho phép chuyển sang mốc 02.

**Mốc 02:** đã hoàn thành tài khoản và phân quyền. Người dùng đã cho phép chuyển sang mốc 03.

**Mốc 03:** đã hoàn thành quản lý môn học, công việc và tài liệu theo lựa chọn của người dùng. Người dùng đã cho phép chuyển sang mốc 04.

**Mốc 04:** đã hoàn thành lịch bận một lần/lặp hằng tuần, ca qua đêm, tùy chọn học và lịch tuần. Người dùng đã cho phép chuyển sang mốc 05.

**Mốc 05:** đã hoàn thành tự sinh kế hoạch tuần, chia buổi, chừa nghỉ, báo phần chưa bố trí, xem trước và áp dụng. Người dùng đã cho phép chuyển sang mốc 06.

**Mốc 06:** đã hoàn thành chỉnh/khóa buổi, ghi nhận, cập nhật tiến độ, xem trước/xếp lại và cảnh báo. Người dùng đã cho phép chuyển sang mốc 07.

**Mốc 07:** đã hoàn thành Pomodoro 25/5, nhật ký nhập tay/từ đồng hồ, lọc/sửa/xóa và thống kê bằng Python. Người dùng đã cho phép chuyển sang mốc 08.

**Mốc 08:** đã hoàn thành thông báo trong web và email nhắc deadline/buổi đã áp dụng, tùy chọn theo user, hộp đã đọc/chưa đọc và lịch sử email. Worker Python dùng hàng đợi database, kiểm tra hiệu lực trước gửi, chống tạo trùng, thử lại có giới hạn và xử lý kết quả email không chắc chắn. Email local dùng console, có cấu hình SMTP qua môi trường. Người dùng đã cho phép chuyển sang mốc 09.

**Mốc 09:** đã triển khai OAuth có state/PKCE, token mã hóa, kết nối/ngắt kết nối, lịch Google riêng, xem trước theo tuần và hàng đợi đồng bộ bằng worker Python. Tạo/cập nhật/gỡ sự kiện theo buổi đã áp dụng, lưu ánh xạ và kiểm tra dữ liệu sống trước mỗi thao tác. Đã kiểm thử tự động và trình duyệt với API giả lập; cấu hình OAuth Client và kiểm thử Google thật theo `HD_Test.md`. Người dùng đã cho phép chuyển sang mốc 10.

**Mốc 10:** đã triển khai trang AI hỗ trợ, tổng hợp nhật ký 14 ngày/việc/phương án bổ sung/cảnh báo bằng Python, nhận xét không cần API và yêu cầu AI có bước xem trước/đồng ý. Dùng OpenAI Responses API với JSON schema, kiểm tra căn cứ, dữ liệu dùng mã thay tên, lịch sử theo owner, báo thay đổi dữ liệu và giới hạn số lần gọi. AI không tự đổi lịch/tiến độ. Đã kiểm thử API giả lập; API thật cần OPENAI_API_KEY theo `HD_Test.md`. Người dùng đã cho phép chuyển sang mốc 11.

**Mốc 11 hiện tại:** theo lựa chọn của người dùng, chỉ hoàn thiện tại máy và chuẩn bị cấu hình, chưa triển khai online. Đã thêm cấu hình PostgreSQL/production, static manifest, Waitress, Docker/Compose, CI, health endpoint, giao diện lỗi và đường bắt đầu phù hợp trạng thái đăng nhập. Có lệnh demo dành cho tài khoản riêng còn trống và tài liệu chạy/nghiệm thu. Đã kiểm thử SQLite/Waitress và cấu hình; Docker/PostgreSQL chưa chạy vì chưa có trên máy, CI chưa được kích hoạt trong phiên. Đang chờ người dùng kiểm thử và push GitHub.

**Phần online còn lại:** khi người dùng yêu cầu triển khai, chọn hosting, chạy PostgreSQL thật và CI, vận hành hai worker, cấu hình HTTPS/SMTP/OAuth/API theo môi trường và kiểm thử trên URL thật. Đây vẫn là điều kiện bắt buộc theo đề, chưa được coi là hoàn thành ở mốc 11.

PostgreSQL và bản online giữ thành hạng mục triển khai riêng, được thực hiện sau các mốc chức năng ưu tiên theo yêu cầu người dùng; URL online vẫn là điều kiện bắt buộc trước nghiệm thu. Các module mới chỉ tạo khi đến mốc cần dùng.
