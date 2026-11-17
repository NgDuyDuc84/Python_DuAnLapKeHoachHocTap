# Báo cáo đưa điều hướng planner lên header

## Thay đổi

Header của người đã đăng nhập có một danh sách duy nhất gồm đúng 9 liên kết, dùng reverse name hiện có:

1. Tổng quan.
2. Lịch tuần, Tạo kế hoạch, Cảnh báo, Lịch bận, Giờ học.
3. Môn & Việc, Tập trung, Thống kê.

Trên desktop, hai vạch viền 1px cao 20px ngăn ba nhóm. Nav là phần tử flex co giãn, căn giữa trong khoảng còn lại giữa logo và chuông/avatar. Từng liên kết không xuống dòng. Không thêm chip Pomodoro; vùng nav co giãn vẫn còn khoảng trống để bố trí chip cạnh chuông sau này.

Trên màn hình nhỏ, dùng chính danh sách đó trong `<details>` có nút biểu tượng + Menu và ba tiêu đề nhóm nhỏ. Không nhân đôi DOM hay liên kết active giữa desktop/mobile. Dùng lại `header.js` để đồng bộ `aria-expanded`, đóng khi chọn liên kết/bấm ngoài/Esc; Esc trả focus về summary. Enter và Tab dùng hành vi bàn phím gốc của details/liên kết. Khi JS không chạy, details mở mặc định và vẫn có thể thao tác bằng summary. Mở chuông/avatar trên desktop không đóng nav.

Đã bỏ duy nhất dòng include tab con trong `planner/base.html`; giữ các block, page header và nội dung khác. Component `section_tabs.html` không cần sửa: các khu Cài đặt, Môn & Việc, Thống kê, Thông báo vẫn dùng như cũ. Avatar và ba tab Cài đặt giữ nguyên.

## File tạo/sửa

| Nhóm | File | Nội dung |
| --- | --- | --- |
| Header | `templates/base.html` | Một nav, ba nhóm, nút Menu bằng details |
| Bảng active | `core/templatetags/navigation.py` | Năm mục planner độc lập, ánh xạ theo tên URL, bỏ dữ liệu tab planner cũ |
| Responsive | `static/css/navigation.css` | Flex, vạch ngăn, nowrap, active gạch chân 2px, menu nhỏ |
| Tương tác | `static/js/header.js` | Tái sử dụng cơ chế đóng menu, đồng bộ trạng thái và breakpoint |
| Bỏ tab con | `templates/planner/base.html` | Xóa một dòng include tab, giữ nguyên block |
| Kiểm thử | `core/test_navigation.py`, `core/test_ui_cleanup.py` | Đủ chín URL, active từng trang, không còn tab planner, người chưa đăng nhập |
| Đặc tả | `docs/UI_REDESIGN_PLAN.md` | Cập nhật mục 2, 3, 8.2; sửa dòng tóm tắt Pha 1 ở mục 6 để không còn chỉ dẫn năm mục cũ |
| Báo cáo | **Tạo** `docs/BAO_CAO_HEADER_DIEU_HUONG.md` | Kết quả và giới hạn |

Không xóa file nào. Các thay đổi chưa commit đã có trong workspace trước lượt này được giữ nguyên, không gộp vào commit điều hướng; riêng `templates/base.html` chỉ stage phần header của lượt này.

## Bảng active

| Mục header | Các tên URL |
| --- | --- |
| Lịch tuần | `planner:week`, `session_move`, `session_record`, `session_lock` |
| Tạo kế hoạch | `planner:plan_generate`, `plan_detail`, `plan_apply` |
| Cảnh báo | `planner:alerts` |
| Lịch bận | `planner:busy_list`, `busy_create`, `busy_update`, `busy_delete` |
| Giờ học | `planner:preferences` |

Các tên viết ngắn trong bảng đều thuộc namespace `planner`. URL khác giữ bảng active cũ, URL không thuộc bảng không active mục nào. Cả trường hợp chỉ nhận POST (`plan_apply`, `session_lock`) được kiểm tra bằng resolve/render header, không thay đổi hoặc gọi endpoint đó để phục vụ điều hướng.

## Khác biệt giữa kế hoạch và mã

- Kế hoạch cũ gom planner vào “Lịch học tập” và năm tab con. Quyết định mới ghi đè: năm mục trực tiếp trên header, bỏ hoàn toàn tab planner. Đã cập nhật tài liệu để các pha sau không dựng lại tab cũ.
- Header thực tế dùng grid và có quy tắc responsive cũ trong `app.css`, không căn giữa bằng absolute. Thay bố cục bằng flex qua stylesheet `navigation.css` tải sau, đủ specificity để ghi đè cả breakpoint cũ; không sửa `app.css` đang có thay đổi ngoài phạm vi.
- `planner/week.html` đã override block `planner_heading` rỗng. Giữ nguyên cấu trúc này; việc xóa include tab ở base không ảnh hưởng thân Lịch tuần.
- Component tab chung còn phục vụ bốn khu khác; chỉ bỏ nơi gọi trong planner và cấu hình tab planner, không sửa component hay các tab đó.

## Ngưỡng responsive và rà thủ công

Chọn **1280px** theo quyết định mới; tại chính ngưỡng này chín mục vẫn còn đủ khoảng trống, không cần giảm cỡ chữ thêm hay chuyển menu sớm. Dùng CSS `(width < 1280px)` và JS `(min-width: 1280px)` để tránh khe hở ở chiều rộng CSS lẻ khi hệ điều hành scale màn hình.

| Độ rộng | Kết quả trực tiếp trong trình duyệt |
| --- | --- |
| 1920px | Chín mục cùng tọa độ y=22px, một hàng; hai vạch ngăn; logo và chuông/avatar tách biệt; không tràn ngang |
| 1366px | Một hàng đầy đủ, Tạo kế hoạch active đúng, không còn tab con; không tràn hay đè logo/nút phải |
| 1280px | Vẫn một hàng; nav luôn mở; mở avatar không làm mất nav |
| 1279px | Ẩn dãy mục, hiện Menu; mở có đủ chín mục/ba nhóm, active đúng; không tràn ngang |
| 390px và 320px | Logo, Menu, chuông và avatar cùng hiện; bảng menu nằm trong viewport, có cuộn khi cần |

Đã kiểm tra Enter mở menu, Esc đóng và trả focus, bấm vùng ngoài đóng, chọn Cảnh báo dẫn tới đúng trang và đóng menu, trang mới active Cảnh báo. Không cần bấm qua Lịch tuần để tới Tạo kế hoạch/Cảnh báo.

## Badge Cảnh báo

**Không triển khai badge.** `build_alerts` dùng công việc tới hạn, các buổi đã áp dụng, tùy chọn giờ học và lịch bận để tính thiếu phút/xung đột/buổi chưa ghi nhận; không có số đếm sẵn dùng chung trên mọi request. Không thể lấy cùng số chính xác bằng tối đa một truy vấn nhẹ. Không gọi service này trong header hoặc thay bằng một số đếm khác. Điều hướng mới không thêm truy vấn DB.

## Kiểm tra

- `.venv\Scripts\python.exe manage.py check`: đạt, không có vấn đề.
- `.venv\Scripts\python.exe manage.py test --noinput`: **328 test đạt** trên workspace.
- Bản nội dung được stage, tách khỏi các thay đổi có sẵn: `check` đạt, **312 test đạt**. Chênh lệch 16 test thuộc các thay đổi có sẵn ngoài commit này.
- Nhóm test điều hướng/header sau khi hoàn tất: **23 test đạt**. Test đủ mọi trang GET planner, gồm danh sách/thêm/sửa/xóa lịch bận và chỉnh giờ/ghi nhận; mỗi header có đúng một mục active; không có marker `class="section-tabs"`, nhãn “Quản lý lịch” hay template tab chung trong response planner.
- Các tên trang đã đăng nhập ở nhiều app đều được render header để xác nhận đủ chín liên kết đúng thứ tự/URL. Test người chưa đăng nhập và layout công khai xác nhận không xuất hiện nav/Menu này. Test Cài đặt/Thông báo/Thống kê và quyền sở hữu/CSRF cũ vẫn đạt.
- Dùng Django Client và loader tạm để render Lịch tuần với base trước/sau trên cùng bản sao dữ liệu: **HTML bên trong `<main>` giống hệt nhau**, chỉ chuẩn hóa token CSRF ngẫu nhiên. So sánh hash với đầu lượt để xác nhận các template Lịch bị cấm, views, URL, model, migration và service nghiệp vụ không đổi.

Không có hạng mục nào khác cần quyết định. Dừng ở phần điều hướng header; các pha khác giữ nguyên phạm vi.
