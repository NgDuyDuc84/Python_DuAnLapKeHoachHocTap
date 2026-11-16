# Nhịp Học — Nhập ngày/giờ dùng chung

Ngày kiểm tra: 16/11/2026. Nhánh: `ui-redesign`.

## Phương án

Dùng **Flatpickr 4.6.13**, lưu JS, CSS, locale và giấy phép MIT trong `static/vendor/flatpickr/`. Không có request tới CDN khi chạy ứng dụng. Gói lấy từ npm registry chính thức, xác minh SHA-512; các file vendor được giữ nguyên và đối chiếu lại với gói tải về. JS + CSS + locale khoảng 67 KiB chưa nén truyền tải.

Chỉ có một controller của ứng dụng: `static/js/datetime_inputs.js`. Layout chung nạp asset một lần; controller tìm mọi input date/time/datetime-local trong trang, kể cả input do partial dùng chung render ra. Không phải sửa widget Python hay từng template form.

- Ngày hiển thị `dd/mm/yyyy`; giờ `HH:mm` 24 giờ; ngày kèm giờ `dd/mm/yyyy HH:mm`.
- Dùng `altInput`: ô hiển thị không có tên gửi lên server; input gốc giữ nguyên name và giá trị ISO `YYYY-MM-DD`, `HH:mm` hoặc `YYYY-MM-DDTHH:mm`. [Ví dụ chính thức](https://flatpickr.js.org/examples/#human-friendly-dates), [các tùy chọn](https://flatpickr.js.org/options/).
- Locale tiếng Việt của upstream được đặt tên `vn.js` / `l10ns.vn`; controller alias sang `vi` và dịch nhãn trợ năng Năm/Tháng/Giờ/Phút. Buộc dùng picker này trên mobile để tránh quay về định dạng native khi JS hoạt động.
- Cho phép chọn bằng lịch và nhập trực tiếp. Kiểm tra chặt định dạng, ngày không tồn tại và giờ vượt phạm vi; không tự cuộn `31/02` thành ngày tháng 3. Nội dung nhập sai được giữ để sửa, với thông báo tiếng Việt.
- Không chuyển giá trị sang UTC trong JS. Chuỗi gửi lên vẫn là giờ địa phương theo hợp đồng form hiện tại; Django tiếp tục xử lý `Asia/Ho_Chi_Minh` như cũ.
- Nhãn label, aria-describedby và aria-invalid được chuyển/giữ cho ô hiển thị. Required, quyền sở hữu và CSRF không đổi.

Chọn thư viện vì đưa được vào repo và hỗ trợ tách hiển thị/giá trị gửi; không cần phương án tách Ngày/Giờ riêng cho mỗi trang hoặc thêm parsing định dạng Việt vào server.

## Danh sách toàn bộ chỗ được áp dụng

Các định nghĩa widget nằm ở `studies/forms.py`, `planner/forms.py`, `focus/forms.py`; nội dung các file này **không đổi** trong lượt sửa.

| Trang / vị trí | Form và trường | Hiển thị | Giá trị gửi giữ nguyên |
| --- | --- | --- | --- |
| Thống kê `/focus/statistics/` | LogRangeForm.start, end | dd/mm/yyyy | YYYY-MM-DD |
| Nhật ký `/focus/logs/` | LogRangeForm.start, end | dd/mm/yyyy | YYYY-MM-DD |
| Thêm/sửa nhật ký nhập tay | StudyLogForm.studied_on | dd/mm/yyyy | YYYY-MM-DD |
| Tạo kế hoạch `/planner/plans/new/` | PlanWeekForm kế thừa WeekForm.week | dd/mm/yyyy | YYYY-MM-DD |
| Chọn tuần ngay trên Lịch `/planner/` | WeekForm.week | dd/mm/yyyy | YYYY-MM-DD |
| Chọn tuần xem trước Google Calendar, khi đã kết nối | WeekForm.week | dd/mm/yyyy | YYYY-MM-DD |
| Giờ học `/planner/preferences/` | StudyPreferenceForm.study_start, study_end | HH:mm, 24 giờ | HH:mm |
| Thêm/sửa Lịch bận | BusyEventForm.starts_at, ends_at | dd/mm/yyyy HH:mm | YYYY-MM-DDTHH:mm |
| Thêm/sửa Lịch bận | BusyEventForm.repeat_until | dd/mm/yyyy | YYYY-MM-DD |
| Chỉnh giờ buổi học | SessionMoveForm.starts_at, ends_at | dd/mm/yyyy HH:mm | YYYY-MM-DDTHH:mm |
| Thêm/sửa Công việc riêng | TaskForm.deadline qua studies/form_fields.html | dd/mm/yyyy HH:mm | YYYY-MM-DDTHH:mm |
| Thêm/sửa Công việc trong thanh bên Lịch | TaskForm.deadline qua cùng studies/form_fields.html | dd/mm/yyyy HH:mm | YYYY-MM-DDTHH:mm |

Form Môn học và Tài liệu cũng dùng `studies/form_fields.html` nhưng không có trường ngày/giờ; không bị thay đổi. Nhật ký Pomodoro chỉ sửa ghi chú qua LogNotesForm nên không có ô ngày cần đổi. Không áp dụng vào Django Admin vì Admin dùng layout riêng, ngoài UI nghiệp vụ này.

## Fallback

- HTML ban đầu vẫn là input date/time/datetime-local nguyên bản. Nếu JS không chạy hoặc thiếu thư viện/locale, chúng vẫn hiển thị và gửi ISO như trước.
- Nếu picker lỗi giữa lúc khởi tạo, controller hủy phần thay thế và khôi phục type, class, readonly, label và giá trị gốc. Thiếu CSS cũng trở về input gốc.
- Lỗi runtime phát ra từ file picker/controller sẽ khôi phục các input đã nâng cấp. Không xử lý lỗi JS không liên quan của các tính năng khác.
- Đã thử trên trình duyệt với file thư viện trả 404 và với lỗi mô phỏng sau khi picker đã tạo ô thay thế: cả hai đều khôi phục input gốc, giữ ngày đã chọn và gửi lại bộ lọc ISO thành công.

## Kiểm thử và kiểm tra thanh bên Lịch

- `.venv\Scripts\python.exe manage.py check`: không có vấn đề.
- `.venv\Scripts\python.exe manage.py test --noinput`: **313 test qua**.
- Snapshot riêng của commit cũng qua `check` và **297 test**. Số lượng khác vì các test chưa commit đã có từ trước của chủ dự án được giữ ngoài snapshot; không gộp các thay đổi Lịch tuần của chủ dự án vào commit này.
- `node --check static/js/datetime_inputs.js`: qua.
- 4 test mới trong `core/test_datetime_inputs.py`: deadline ISO và múi giờ Việt Nam; khoảng ISO Thống kê không lẫn ngày/tháng, lọc đúng dữ liệu chủ sở hữu; TaskForm dùng chung vẫn nhận ISO và giữ CSRF; input gốc và asset cục bộ trên các form. Luồng POST trực tiếp của thanh bên còn được phủ bởi các test workspace hiện có và lượt rà trình duyệt bên dưới.
- Trình duyệt: ô Từ ngày `10/11/2026` khớp ngày đầu biểu đồ `10/11/2026`. Đổi sang `11/11/2026`, bấm Xem kết quả: URL nhận `start=2026-11-11&end=2026-11-16` và kết quả lọc đúng.
- Trình duyệt: nhập `31/02/2026` bị chặn bằng thông báo tiếng Việt, không điều hướng/lưu thành ngày khác; chuỗi nhập sai được giữ lại.
- Trình duyệt: Tạo kế hoạch hiển thị `16/11/2026`; Giờ học hiển thị `08:00` và `22:00`.
- **Đã thêm công việc từ thanh bên Lịch** bằng cách nhập deadline `19/11/2026 08:15`, ước tính 45 phút; bấm Lưu công việc nhận thông báo thành công và dòng việc hiển thị `Hạn 19/11 · 08:15`.
- Đối chiếu trực tiếp SQLite kiểm thử: deadline lưu `2026-11-19 01:15:00` UTC, tương ứng `2026-11-19 08:15:00+07:00`; thời lượng còn lại 45 phút, đúng tài khoản kiểm thử. Công việc kiểm thử không có trong SQLite gốc.
- Rà trình duyệt dùng bản sao SQLite và tài khoản tổng hợp, không tạo dữ liệu thử trong dữ liệu gốc.
- Đối chiếu checksum **53 file được bảo vệ** với trạng thái đầu lượt: mọi form Python, model, migration, view, URL, service, settings, ba template Lịch và `studies/form_fields.html` đều giữ nguyên.

## File tạo/sửa

Sửa:

- `templates/base.html`: nạp CSS và ba script cục bộ, đúng thứ tự và defer.
- `docs/UI_REDESIGN_PLAN.md`: ghi nhận chuẩn ngày/giờ dùng chung tại mục 8.5.

Tạo:

- `static/js/datetime_inputs.js`: controller duy nhất cho ứng dụng.
- `static/vendor/flatpickr/flatpickr.min.js`, `flatpickr.min.css`, `vn.js`.
- `static/vendor/flatpickr/LICENSE.md`, `README.md`: giấy phép, phiên bản và nguồn gói.
- `core/test_datetime_inputs.py`: kiểm thử ISO, múi giờ, Thống kê, thanh bên và CSRF.
- `docs/UI_DATETIME_REPORT.md`: báo cáo này.

Không xóa file. Không sửa trực tiếp `planner/week.html`, `planner/study_sidebar.html`, `planner/calendar_item.html`; cũng không cần sửa partial form dùng chung, vì controller nhận diện input do partial render ra.

## Rủi ro / giới hạn còn lại

- Khi fallback về input gốc, cách hiển thị lại phụ thuộc ngôn ngữ trình duyệt; đây là đường dự phòng để form vẫn hoạt động khi JS không khả dụng.
- Chưa nghiệm thu trên điện thoại thật hoặc các thiết bị dùng múi giờ khác Việt Nam. Server và chuỗi ISO không thay đổi múi giờ.
- Không có quyết định bắt buộc còn chờ; dừng tại phạm vi nhập ngày/giờ dùng chung.
