# Luồng nghiệm thu và trình bày dự án

Bản hiện tại đã triển khai chức năng đến mốc 10 và chuẩn bị cấu hình/demo ở mốc 11. Theo lựa chọn người dùng, **chưa triển khai online**; không coi bản local là đã đạt yêu cầu URL online trong đề. Xem `HD_Test.md` để kiểm thử từng mốc và `docs/TRIEN_KHAI.md` cho phần vận hành.

## Chuẩn bị dữ liệu demo

Đăng ký một tài khoản riêng, ví dụ `demo`, bằng giao diện. Tài khoản phải active, không phải staff/admin và chưa có dữ liệu học tập/tùy chọn/kết nối. Mật khẩu do bạn nhập; lệnh không tạo hoặc đổi mật khẩu.

```powershell
& .\.venv\Scripts\python.exe manage.py seed_demo --username demo
```

Lệnh thêm dữ liệu mang nhãn `[Demo]` trong một transaction:

| Nội dung | Số lượng / giá trị |
|---|---|
| Môn | 2 |
| Công việc | 5, có việc quá hạn và việc đã hoàn thành |
| Tài liệu liên kết | 2 |
| Lịch bận | 1, lặp hằng tuần |
| Kế hoạch đã áp dụng | 1 |
| Buổi | 3: hai buổi chưa ghi nhận (một khóa), một buổi hủy |
| Nhật ký | 5 bản trong 14 ngày, tổng 175 phút |
| Email nhắc | Tắt |
| Google/OpenAI | Không kết nối, không gọi API |

Lệnh in tuần có buổi học để bạn chọn đúng tuần; buổi tương lai đầu tiên là ngày mai. Chạy lại thấy `Demo already exists; no changes made.` Tài khoản đã có dữ liệu khác bị từ chối và dữ liệu giữ nguyên. Muốn trình diễn lại từ đầu, tạo tài khoản demo mới; lệnh không có chức năng xóa/reset dữ liệu.

## Trạng thái hoàn thiện cuối

Ngày 15/11/2026: mã các chức năng của kế hoạch đã có, bổ sung Tổng quan và hướng dẫn ngay trong web. Bản hiện tại qua 272 test SQLite, hành trình HTTP trên Waitress + hai worker, và kiểm tra Tổng quan ở máy tính/375px. Chưa có khóa SMTP/Google/OpenAI nên không đánh dấu dịch vụ thật đã đạt. Public website nằm ngoài yêu cầu hiện tại; yêu cầu URL online của đề vẫn phải làm trước khi nộp nếu thầy yêu cầu. Workflow Compose mới cần xác minh sau push. [Báo cáo kỹ thuật](BAO_CAO_DU_AN.md) có bảng đối chiếu từng yêu cầu và phần giải thích để bảo vệ.

## Kịch bản trình bày

1. **Bài toán và dữ liệu:** đăng nhập vào Tổng quan, xem số liệu, buổi sắp tới và việc quá hạn. Mở môn/công việc, giải thích deadline, ưu tiên, ước tính và số phút còn lại. Chỉ ra việc đã hoàn thành không còn cần xếp lịch.
2. **Khung thời gian và lập kế hoạch:** mở lịch bận/giờ học/lịch tuần. Chọn tuần có demo, thấy buổi khóa và lịch lên lớp. Tạo phương án Bổ sung, chỉ xem trước để giải thích các buổi đã giữ, nghỉ giữa buổi và phần chưa xếp.
3. **Điều chỉnh:** nếu muốn thay đổi lịch demo, kiểm tra phương án rồi áp dụng. Giải thích buổi khóa/chỉnh tay được giữ khi Xếp lại; thay đổi đầu vào không âm thầm thay lịch.
4. **Tiến độ và thời gian thực học:** mở Pomodoro, nhật ký và thống kê. Nhật ký demo ban đầu là 175 phút trong 5 ngày; không tự đồng nghĩa hoàn thành công việc.
5. **Cảnh báo và nhắc:** mở việc quá hạn/thiếu lịch. Worker nhắc chạy riêng; tùy chọn web/email tách biệt. Nếu trình diễn email console, nói rõ đó là bản xem nội dung, không phải SMTP thật.
6. **Đồng bộ:** giới thiệu xem trước và xác nhận theo tuần. Chỉ cấp quyền/kết nối Google khi đã cấu hình và muốn thử thật; không trình bày API giả lập như đã ghi được vào Google thật.
7. **AI:** mở số liệu Python, xem payload dùng mã và căn cứ. Nếu có API key, tự xem dữ liệu/đồng ý gửi. AI diễn giải; thao tác thay lịch vẫn qua planner kiểm tra và bạn áp dụng.
8. **Quyền và kỹ thuật:** đăng nhập tài khoản khác để chứng minh dữ liệu riêng; nêu bộ test và cách chạy. Trình bày Docker/PostgreSQL là cấu hình đã chuẩn bị, chỉ xác nhận đã chạy thật khi có kết quả tương ứng.

## Những điểm cần nói đúng

- Backend, kiểm tra quyền, thời gian, thuật toán, tổng hợp thống kê, worker và tích hợp API được viết bằng Python. Django Templates dựng giao diện; JavaScript hỗ trợ đồng hồ.
- Thuật toán tham lam xét deadline/ưu tiên, ràng buộc lịch/quỹ ngày/chia buổi/nghỉ; chưa chứng minh tối ưu toàn cục. Phần chưa xếp được hiển thị rõ.
- AI không có quyền tự sửa lịch/tiến độ. Kiểm tra mã căn cứ không bảo đảm diễn giải luôn đúng.
- OAuth, SMTP và AI thật cần thông tin cấu hình cùng kiểm thử dịch vụ tương ứng. Ngày 15/11/2026 đã xác minh 260 test trên PostgreSQL 17.12 portable và SQLite. CI của commit `cfcb3b5` cũng thành công trên SQLite/Windows và PostgreSQL/Linux, gồm Docker build và Compose config; chưa chạy toàn bộ ứng dụng qua Compose hoặc URL online.
- Không để key, token, `.env`, database hoặc bản sao lưu trong commit/ảnh trình bày.

## Điều kiện nghiệm thu online còn lại

- Có URL HTTPS thật, DEBUG tắt, static đầy đủ và health hoạt động.
- Dữ liệu nằm ở PostgreSQL bền qua restart/deploy; migration, backup và hai worker được vận hành.
- Kiểm thử tài khoản/quyền và toàn bộ luồng trên URL đó; Google callback/SITE_URL/email đúng môi trường khi bật.
- Hoàn thành checklist đã chọn trong HD_Test.md và ghi lại phần chưa kiểm tra, không thay bằng lời khẳng định đã đạt.
