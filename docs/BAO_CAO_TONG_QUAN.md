# Báo cáo thiết kế lại Tổng quan

## Kết quả

Trang `/` dùng lời chào, số liệu thật, một thẻ hành động ưu tiên, dải ba số liệu, hai thẻ Hôm nay & sắp tới / Việc cần chú ý và bảy ô Tuần này. Bố cục, màu nhấn và khoảng cách dựa theo ảnh mẫu; nội dung và nút lấy từ dữ liệu thật. Bỏ nút Mở lịch học của bạn và toàn bộ khối Bước tiếp theo của bạn. Không triển khai các phần khác của Pha 2.

Hàm thuần `select_dashboard_action` chọn đúng thứ tự: phiên đang dở → buổi đang diễn ra → buổi chưa ghi nhận → việc quá hạn → việc thiếu lịch trước hạn → buổi tiếp theo hôm nay → checklist → sẵn sàng. Các nút tập trung theo công việc dùng `FocusStartForm` và POST `focus:home` hiện có, kèm CSRF và khóa chống gửi lặp. Không sửa endpoint hoặc logic tạo phiên.

## File thay đổi

| Mục đích | File |
| --- | --- |
| Tổng hợp dữ liệu, chọn hành động, nhóm buổi học, chỉ báo tuần | `core/dashboard.py` |
| Tái sử dụng phép tính số phút thiếu của Cảnh báo | `planner/services/alerts.py` |
| Giao diện và responsive | `templates/core/dashboard.html`, `static/css/dashboard.css` |
| Nút GET / form POST dùng chung trên Tổng quan | **Tạo** `templates/components/dashboard_button.html` |
| Hàm thuần: tám nhánh và thứ tự ưu tiên | **Tạo** `core/test_dashboard_actions.py` |
| View, quyền sở hữu, checklist, tuần, CSRF, gửi lặp, số truy vấn | **Tạo** `core/test_dashboard_layout.py` |
| Điều chỉnh kỳ vọng của test cũ theo giao diện mới | `core/test_dashboard.py`, `core/tests.py` |
| Đặc tả và báo cáo | `docs/UI_REDESIGN_PLAN.md` mục 4.1, **tạo** `docs/BAO_CAO_TONG_QUAN.md` |

Không xóa file nào trong lượt này. Repo có thay đổi chưa commit trước khi bắt đầu; các thay đổi đó được giữ nguyên. Hai file giao diện Tổng quan được thay nội dung theo yêu cầu thiết kế lại. Thay đổi sẵn có ở test trang giới thiệu và việc xóa CSS của trang hướng dẫn không được đưa vào commit này; các quy tắc CSS hướng dẫn cũ được giữ trong commit để không kéo theo phần xóa trang đó.

## Điểm kế hoạch khác mã và quyết định xử lý

- Mục 4.1 cũ chia bốn vùng, có cột Pomodoro, biểu đồ phút học nhỏ và khối xung đột. Prompt mới ghi đè: dùng thẻ hành động, dải số liệu, hai thẻ và dải tuần. Đã cập nhật lại toàn bộ mục 4.1.
- Tổng quan cũ chỉ tải tối đa sáu việc và sáu buổi sắp tới; chưa đủ để chọn buổi đang diễn ra, buổi chưa ghi nhận thuộc tuần trước hoặc đếm dấu mốc cả tuần. Tổng quan nay tải các buổi liên quan trong tuần/đến bảy ngày tới, cùng một truy vấn lấy buổi chưa ghi nhận gần nhất không giới hạn tuần; không tải toàn bộ lịch sử.
- Cảnh báo đã có phép tính phút thiếu nhưng nằm trong `build_alerts`, cùng xử lý xung đột có nhiều dữ liệu và có thể khởi tạo tùy chọn giờ học. Đã tách nguyên phép tính sang `build_task_alerts`, để cả hai nơi dùng chung. Không thay đổi công thức, giới hạn hạn chót, cách làm tròn phút hay phần xử lý xung đột. Có test đối chiếu kết quả.
- `active_session` hiện có coi cả RUNNING và PAUSED, cả phiên học và nghỉ chưa kết thúc, là phiên đang dở. Tổng quan tiếp tục dùng cùng nguồn này để không gợi ý tạo phiên mới khi endpoint sẽ từ chối vì đã có phiên.
- Điều kiện onboarding trong yêu cầu 3.g nói chưa có môn/công việc; yêu cầu 7 nói checklist biến mất khi đủ ba bước. Áp dụng đủ ba bước: có môn, có công việc và có một kế hoạch; bản nháp cũng tính là đã tạo kế hoạch. Các nhánh hành động a–f vẫn thắng checklist, như thứ tự được yêu cầu. Cách hiểu này đã được ghi vào mục 4.1 và test.
- Badge “Chưa có lịch” áp dụng khi còn thiếu phút theo Cảnh báo, gồm cả trường hợp đã có một phần lịch. Không tự tạo tiêu chí thiếu lịch khác.
- Số thông báo chưa đọc chỉ lấy ở chuông hiện có; bỏ truy vấn đếm trùng từ Tổng quan.

## Truy vấn và kiểm tra

Đo toàn bộ GET `/` sau khi đăng nhập, bằng `CaptureQueriesContext`, cùng dữ liệu và mốc 17/11/2026 09:00 tại Asia/Ho_Chi_Minh. Dữ liệu rà giao diện nằm trong bản sao SQLite, không ghi vào cơ sở dữ liệu gốc.

| Trạng thái | Trước | Sau |
| --- | ---: | ---: |
| Người dùng mới | 14 | 12 |
| Có việc chưa đủ lịch | 14 | 12 |
| Có phiên đang chạy | 14 | 12 |

Sau sửa có 8 truy vấn dữ liệu Tổng quan và 4 truy vấn xác thực/chuông hiện có. Dải Tuần này dùng lại danh sách đã tải, không thêm truy vấn. Test `assertNumQueries(12)` giữ mức này cho cả ba trạng thái.

- `.venv\Scripts\python.exe manage.py check`: đạt, không có vấn đề.
- `.venv\Scripts\python.exe manage.py test --noinput`: **326 test đạt** trên workspace.
- Kiểm tra riêng bản nội dung được stage, không mang theo thay đổi chưa commit có sẵn: `check` đạt và **310 test đạt**. Chênh lệch 16 test là các test đã có sẵn ngoài commit này.
- Test mới bao phủ tám nhánh bằng dữ liệu thuần không dùng DB, điều kiện cùng đúng, ranh giới giờ bắt đầu/kết thúc, hạn bảy ngày, checklist, quyền sở hữu, chỉ lịch đã áp dụng/không hủy, buổi chưa ghi nhận từ tuần trước và deadline của việc hoàn thành trong dấu mốc tuần.
- Test POST thực thi endpoint Pomodoro hiện có: công việc đúng, thiếu CSRF trả 403, có CSRF tạo phiên, gửi lặp cùng khóa không tạo phiên thứ hai. GET Tổng quan vẫn chỉ đọc dữ liệu.
- Rà trực tiếp trên trình duyệt: người dùng trống thấy đúng checklist thay toàn bộ khối chính; người có việc thiếu lịch thấy thẻ nổi bật, chỉ một nút chính/một nút phụ, dải số liệu và các thẻ; người có phiên đang chạy thấy Tiếp tục và số buổi hôm nay đúng. Giờ hiển thị 24 giờ; ngày đầy đủ dùng dd/mm/yyyy, lời chào/nhóm ngày dùng dd/mm theo yêu cầu.
- So sánh hash với đầu lượt: `planner/week.html`, `planner/study_sidebar.html`, `planner/calendar_item.html`, mọi views, URL, model và migration không bị sửa. Không thay Django Admin, `/health/`, quyền sở hữu, CSRF, endpoint POST hay thuật toán xếp lịch.

## Tồn đọng và giới hạn

Không có mục nào bị bỏ hoặc hoãn; dải tuần đã làm mà không thêm truy vấn. Không có quyết định nào đang chờ phê duyệt. Các truy vấn chỉ được đo bằng dữ liệu kiểm tra SQLite và khóa bằng test, chưa phải benchmark tải sản xuất. Thẻ buổi học và công việc vẫn giới hạn sáu dòng như Tổng quan cũ, có liên kết mở trang đầy đủ.
