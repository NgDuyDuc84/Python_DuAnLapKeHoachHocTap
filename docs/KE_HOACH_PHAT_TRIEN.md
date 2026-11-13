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

**Mốc 05 hiện tại:** thuật toán tham lam bằng Python tự sinh kế hoạch tuần, chia buổi, chừa nghỉ, tôn trọng deadline và quỹ ngày; báo phút chưa bố trí theo công việc. Xem trước rồi áp dụng với kiểm tra dữ liệu/thời gian đã thay đổi. Giữ buổi đã áp dụng, khấu trừ phút tương lai đã có lịch ở các tuần và hiển thị buổi học trên lịch tuần. Đang chờ người dùng kiểm thử và push GitHub.

**Mốc 06 dự kiến:** sửa/khóa buổi, cập nhật tiến độ, xếp lại phần được phép và cảnh báo deadline. Mốc 05 chưa tự điều chỉnh các buổi đã áp dụng khi đầu vào thay đổi; tạo kế hoạch bổ sung không thay thế kế hoạch cũ.

PostgreSQL và bản online giữ thành hạng mục triển khai riêng, được thực hiện sau các mốc chức năng ưu tiên theo yêu cầu người dùng; URL online vẫn là điều kiện bắt buộc trước nghiệm thu. Các module mới chỉ tạo khi đến mốc cần dùng.
