# Báo cáo bố cục và phong cách Sổ tay xanh

## Phạm vi và quyết định

Áp dụng hai yêu cầu theo thứ tự: chuẩn hóa bố cục trước, sau đó áp phong cách mà không thêm luồng/khối dữ liệu mới. Ảnh Tổng quan đính kèm được dùng làm tham chiếu hình thức; không sao chép dữ liệu mẫu. Không nhận được các file ảnh riêng `ban_do_bo_cuc.png`/`bang_phong_cach.png` được nhắc trong văn bản; các quy tắc chi tiết và token đã đủ để thực hiện.

- Chọn `--page-w: 1120px` vì đây là chiều rộng CSS thật của đa số trang, thay vì số 1260px ước tính. Khung tính cả padding: nội dung B/C rộng 1056px trên desktop; D rộng 696px trong khung 760px; auth rộng 416px trong khung 480px. Gutter 32/24/16px theo breakpoint; khoảng 768–1023px dùng 24px vì yêu cầu chỉ ấn định rõ phần dưới 768px và từ 1024px.
- Một `main.page`; kiểu trang theo tên URL tập trung trong `navigation_state`, kích thước trong `layout.css`. `main_class` vẫn tương thích với Lịch tuần. Form thêm/sửa môn, việc, tài liệu và cập nhật tiến độ chưa được gán kiểu riêng trong yêu cầu: dùng khung chuẩn, đủ chiều rộng, trường hai cột theo quy tắc form không có nội dung phụ.
- Dùng page header chung, tab tùy chọn bên dưới; tiêu đề/thẻ/tab thẳng mép. Các trang C dùng form/thông tin trái và nội dung phụ thật ở phải; chú thích giữ nguyên nội dung và các ID liên kết aria. Tạo kế hoạch có ba ý ngắn + details chi tiết ở thẻ phụ, lịch sử rộng đủ khung bên dưới. Không thực hiện stepper/drawer hay gộp URL.
- Các hàng số liệu/thẻ Tổng quan và lưới môn stretch, empty state căn giữa; aside của `.split` giữ chiều cao theo nội dung để sticky hoạt động. Dưới 1024px aside xuống dưới, bỏ sticky. Lịch sử kế hoạch/nhật ký/email/đồng bộ có hàng đầy khung, chuyển thành thẻ trên màn nhỏ.
- Giữ chỗ scrollbar trên trang chuẩn để trang ngắn/dài không lệch mép. Lịch tuần được loại khỏi quy tắc này, giữ nguyên khung rộng cũ.

## Bảng trước/sau từng trang

Đo trực tiếp trong trình duyệt ở **1920 / 1440 / 1366 CSS px**, cao 1000px, cùng dữ liệu QA trên bản sao SQLite. Trong hai cột mép, các cặp `trái/phải` lần lượt ứng với ba độ rộng này. Đây là mép vùng nội dung bên trong khung, không phải mép ngoài `main`. Mỗi dòng là một trang/template thực tế, tên URL là reverse name hiện có.

Trước sửa: padding ngang `main`/shell là 0; `.container` tự chừa 24px mỗi bên khi hẹp, 18px dưới 640px, margin-inline auto. Tổng quan thêm max-width 980px ở bên trong; form-card max-width 760px nằm trái; auth-shell max-width 560px căn giữa. Các thẻ nhỏ trong lưới môn/tài liệu/thống kê là cột lưới có chủ đích. Google có thêm `.sync-shell` max-width 1040px, khiến phần nội dung không hết khung. Cột “Khung/thẻ” ghi chiều rộng thực ở 1920px, dấu — khi không có loại thẻ được đo. Sai lệch 7,6px giữa trang dài/ngắn trước sửa đến từ scrollbar.

| Reverse name | Kiểu sau | Khung/thẻ trước (px) | Mép trước: 1920 · 1440 · 1366 | Mép sau: 1920 · 1440 · 1366 |
| --- | --- | --- | --- | --- |
| `core:home` | B | 980 / 980 | 462.4/1442.4 · 222.4/1202.4 · 185.6/1165.6 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `planner:week` | A | 1720 / — | 100/1820 · 24/1416 · 24/1342.4 | 100/1820 · 24/1416 · 24/1342.4 |
| `planner:plan_generate` | C | 1120 / 760 | 400/1520 · 160/1280 · 123.2/1243.2 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `planner:plan_detail` | B | 1120 / — | 392.4/1512.4 · 152.4/1272.4 · 115.6/1235.6 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `planner:alerts` | B | 1120 / — | 400/1520 · 160/1280 · 123.2/1243.2 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `planner:busy_list` | B | 1120 / 1120 | 400/1520 · 160/1280 · 123.2/1243.2 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `planner:busy_create` | D | 1120 / 760 | 400/1520 · 160/1280 · 123.2/1243.2 | 604.4/1300.4 · 364.4/1060.4 · 327.6/1023.6 |
| `planner:busy_update` | D | 1120 / 760 | 400/1520 · 160/1280 · 123.2/1243.2 | 604.4/1300.4 · 364.4/1060.4 · 327.6/1023.6 |
| `planner:busy_delete` | D | 1120 / 760 | 400/1520 · 160/1280 · 123.2/1243.2 | 604.4/1300.4 · 364.4/1060.4 · 327.6/1023.6 |
| `planner:preferences` | C | 1120 / 760 | 392.4/1512.4 · 152.4/1272.4 · 115.6/1235.6 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `planner:session_move` | D | 1120 / 760 | 400/1520 · 160/1280 · 123.2/1243.2 | 604.4/1300.4 · 364.4/1060.4 · 327.6/1023.6 |
| `planner:session_record` | D | 1120 / 760 | 400/1520 · 160/1280 · 123.2/1243.2 | 604.4/1300.4 · 364.4/1060.4 · 327.6/1023.6 |
| `studies:task_list` | B | 1120 / 1120 | 400/1520 · 160/1280 · 123.2/1243.2 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `studies:subject_list` | B | 1120 / 550 | 400/1520 · 160/1280 · 123.2/1243.2 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `studies:material_list` | B | 1120 / 550 | 400/1520 · 160/1280 · 123.2/1243.2 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `studies:task_create` | B | 1120 / 760 | 392.4/1512.4 · 152.4/1272.4 · 115.6/1235.6 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `studies:task_update` | B | 1120 / 760 | 392.4/1512.4 · 152.4/1272.4 · 115.6/1235.6 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `studies:task_progress` | B | 1120 / 760 | 400/1520 · 160/1280 · 123.2/1243.2 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `studies:task_delete` | D | 1120 / 760 | 400/1520 · 160/1280 · 123.2/1243.2 | 604.4/1300.4 · 364.4/1060.4 · 327.6/1023.6 |
| `studies:subject_create` | B | 1120 / 760 | 400/1520 · 160/1280 · 123.2/1243.2 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `studies:subject_update` | B | 1120 / 760 | 400/1520 · 160/1280 · 123.2/1243.2 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `studies:subject_delete` | D | 1120 / 760 | 400/1520 · 160/1280 · 123.2/1243.2 | 604.4/1300.4 · 364.4/1060.4 · 327.6/1023.6 |
| `studies:material_create` | B | 1120 / 760 | 392.4/1512.4 · 152.4/1272.4 · 115.6/1235.6 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `studies:material_update` | B | 1120 / 760 | 392.4/1512.4 · 152.4/1272.4 · 115.6/1235.6 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `studies:material_delete` | D | 1120 / 760 | 400/1520 · 160/1280 · 123.2/1243.2 | 604.4/1300.4 · 364.4/1060.4 · 327.6/1023.6 |
| `focus:home` | C | 1120 / 760 | 400/1520 · 160/1280 · 123.2/1243.2 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `focus:session` | B | 1120 / 1120 | 400/1520 · 160/1280 · 123.2/1243.2 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `focus:statistics` | B | 1120 / 362.66 | 392.4/1512.4 · 152.4/1272.4 · 115.6/1235.6 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `focus:logs` | B | 1120 / 1120 | 400/1520 · 160/1280 · 123.2/1243.2 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `focus:log_create` | D | 1120 / 760 | 400/1520 · 160/1280 · 123.2/1243.2 | 604.4/1300.4 · 364.4/1060.4 · 327.6/1023.6 |
| `focus:log_update` | D | 1120 / 760 | 400/1520 · 160/1280 · 123.2/1243.2 | 604.4/1300.4 · 364.4/1060.4 · 327.6/1023.6 |
| `focus:log_delete` | D | 1120 / 760 | 400/1520 · 160/1280 · 123.2/1243.2 | 604.4/1300.4 · 364.4/1060.4 · 327.6/1023.6 |
| `insights:home` | B | 1120 / 268 | 392.4/1512.4 · 152.4/1272.4 · 115.6/1235.6 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `insights:report` | B | 1120 / 1120 | 392.4/1512.4 · 152.4/1272.4 · 115.6/1235.6 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `notifications:inbox` | B | 1120 / — | 400/1520 · 160/1280 · 123.2/1243.2 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `notifications:email_history` | B | 1120 / — | 400/1520 · 160/1280 · 123.2/1243.2 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `notifications:preferences` | C | 1120 / 760 | 400/1520 · 160/1280 · 123.2/1243.2 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `accounts:profile` | C | 1120 / 760 | 400/1520 · 160/1280 · 123.2/1243.2 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `accounts:password_change` | C | 1120 / 760 | 400/1520 · 160/1280 · 123.2/1243.2 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `integrations:google` | C | 1120 / 508 | 400/1520 · 160/1280 · 123.2/1243.2 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `integrations:job` | B | 1120 / 1040 | 400/1520 · 160/1280 · 123.2/1243.2 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |

| Trang công khai | Kiểu sau | Khung/thẻ trước (px) | Mép trước: 1920 · 1440 · 1366 | Mép sau: 1920 · 1440 · 1366 |
| --- | --- | --- | --- | --- |
| Giới thiệu `/` (chưa đăng nhập) | B | 1120 / — | 400/1520 · 160/1280 · 123.2/1243.2 | 424.4/1480.4 · 184.4/1240.4 · 147.6/1203.6 |
| `accounts:login` | Auth | 560 / 560 | 680/1240 · 440/1000 · 403.2/963.2 | 744.4/1160.4 · 504.4/920.4 · 467.6/883.6 |
| `accounts:register` | Auth | 560 / 560 | 672.4/1232.4 · 432.4/992.4 · 395.6/955.6 | 744.4/1160.4 · 504.4/920.4 · 467.6/883.6 |

Sau sửa, **29 trang B/C có sai lệch mép trái và phải bằng 0px** tại mỗi độ rộng đo, đạt giới hạn 1px. Trang lỗi 403/404/500 được gán D và dùng page header chung; các URL chỉ nhận POST/JSON, `/health/`, Admin và URL đổi mật khẩu thành công chỉ redirect không tạo thêm trang để đo.

### Template tương ứng

- Tổng quan: `core/dashboard.html`; Lịch: `planner/week.html`; Tạo kế hoạch/chi tiết: `planner/plan_form.html`, `planner/plan_detail.html`; Cảnh báo: `planner/alerts.html`; Lịch bận: `planner/busyevent_list.html`, `planner/form.html`, `planner/confirm_delete.html`; Giờ học cũng dùng `planner/form.html`; Chỉnh/Ghi nhận dùng `planner/session_form.html`.
- Môn & Việc: `studies/task_list.html`, `subject_list.html`, `material_list.html`, các form dùng `studies/form.html`, xác nhận xóa dùng `studies/confirm_delete.html`.
- Tập trung: `focus/start.html`, `session.html`, `statistics.html`, `log_list.html`, `log_form.html`, `log_delete.html`; AI: `insights/home.html`, `report.html`.
- Thông báo: `notifications/inbox.html`, `email_history.html`, `preferences.html`; tài khoản: `accounts/profile.html`, `password_change.html`; Google: `integrations/google.html`, `job.html`; auth: `accounts/login.html`, `register.html` qua `form_page.html`; giới thiệu: `core/home.html`.

## Phong cách và font

`tokens.css` chứa duy nhất các khai báo `:root` (kể cả breakpoint), toàn bộ bảng màu/bo góc/bóng/font/gutter. `app.css` dùng token cho nền và chữ cơ bản; `theme.css` áp thành phần dùng chung. Đã chuyển 94 màu hex cũ sang token, sửa các ánh xạ theo vai trò: pine cho buổi học, sky cho lịch bận, amber cho deadline/thiếu lịch, coral cho lỗi/quá hạn.

Đã tự host **sáu WOFF2 variable gốc** của [Lora](https://github.com/google/fonts/tree/main/ofl/lora) và [Inter](https://github.com/google/fonts/tree/main/ofl/inter), đủ Latin, Latin mở rộng và tiếng Việt, tổng 210.444 byte. Giữ giấy phép OFL, Reserved Font Name và nội dung file gốc; `sources.json` có URL/checksum. `fonts.css` dùng URL tương đối, unicode-range và font-display swap. Hai font Latin được preload; helper nhỏ bỏ query cache chỉ có trong development để URL preload khớp CSS, vẫn giữ tên hashed khi dùng Manifest storage. Không có dependency font/framework mới lúc chạy, không dùng CDN.

Tiêu đề/tên thẻ/số lớn dùng Lora, giao diện dùng Inter, số giờ/bảng tabular-nums. Nền giấy gradient nhẹ, nav/tab pill, thẻ bo 22px, nút chính xanh thông, cảnh báo hổ phách; focus ring rõ và reduced-motion tắt chuyển động. Các cặp chữ/nền chính có test tương phản ≥4.5:1. Không đổi màu môn đã lưu. Input/select/textarea bắt đầu cao 48px (textarea kéo được), chỉ option `---------` được đổi nhãn bằng JS dùng chung, giữ nguyên value/tập lựa chọn.

### Giá trị cũ còn giữ có chủ đích

- `static/vendor/flatpickr/flatpickr.min.css`: giữ nguyên toàn bộ CSS vendored, gồm màu xám ngày/tháng/mũi tên/trạng thái gốc; theme chỉ đè nền, chữ chung, font, bo góc/bóng và màu ngày được chọn. Không sửa vendor để tránh rủi ro picker.
- Màu môn là dữ liệu `Subject.color`, được render qua `--subject-color` ở `studies/subject_list.html`, `core/dashboard.html` và màu có sẵn của người dùng; không chuyển thành màu cố định. Fallback hex cũ trên Tổng quan đã chuyển sang `var(--muted)`.
- Inline style biểu đồ trong `focus/statistics.html` chỉ là chiều rộng phần trăm từ dữ liệu, được giữ nguyên. Không còn hex màu cũ trong CSS ứng dụng ngoài `tokens.css`.
- Một số khai báo padding/font-size/độ rộng cũ trong stylesheet từng app được giữ để không tác động Lịch; khung mới được quyết định tập trung bằng selector `.page:not(.calendar-container)` trong `layout.css`. Kích thước lưới/spacing của Lịch giữ nguyên tuyệt đối.
- Repo chưa có dialog dùng chung đang hoạt động; không thêm luồng/dialog mới trong lượt đổi bố cục/phong cách này.

## Lịch tuần

Không sửa `planner/week.html`, `planner/study_sidebar.html`, `planner/calendar_item.html`, `studies/form_fields.html`, JS lịch/ngày giờ, view hoặc service. Các khai báo bố cục của `planner.css` được giữ; chỉ đổi màu, bo góc và bóng sang token. Thân Lịch giữ Segoe UI để tránh thay đổi ngắt dòng, không áp input 48px, page padding hay form-grid mới vào Lịch.

Đã so sánh trực tiếp trước/sau tại ba độ rộng: khung, commandbar, calendar-main, bảng và từng ô lịch có cùng chiều rộng/chiều cao, không có khác biệt hình học. Lề Lịch và lề header bằng nhau: 1920px → 100/1820; 1440px → 24/1416; 1366px → 24/1342.4. Phần nhìn thấy đổi: nền giấy ấm, bề mặt/viền be, lịch bận xanh trời nhạt/chữ sky-ink, buổi học xanh thông nhạt, deadline hổ phách, bo góc/bóng theo token. Header đổi Lora/Inter và active pill; số cột, độ cao ô, khoảng cách và công cụ Lịch không đổi. Ở màn nhỏ vẫn giữ lưới tối thiểu 800px và cuộn trong vùng lịch, không thu nhỏ/sắp lại lưới.

## Kiểm tra và giới hạn

- `manage.py check`: đạt, không có vấn đề.
- `manage.py test --noinput`: **335 test đạt**. Nhóm bố cục/điều hướng/Tổng quan: 34 test đạt; nhóm sau chỉnh nhỏ: 16 test đạt.
- Test mới cho đủ 41 trang đăng nhập và ba trang công khai: đúng một main.page, kiểu khung đúng, page header chung, split đúng trang, auth không có nav riêng tư; kiểm tra trường hợp đổi mật khẩu không có quy tắc, POST sai vẫn giữ khung/CSRF/giá trị, help text/ID và nguồn mô tả chế độ xếp lịch; font checksum/định dạng, unicode-range/swap và tương phản token.
- Đo 41 trang ở 1920/1440/1366 trước và sau, thêm ba trang công khai; các mép B/C sau sửa bằng nhau. Đo thêm 41 trang ở 960/390: B/C/D không tràn ngang; cả bảy split thành một cột, aside static. Kiểm tra header tại 1280px vẫn đủ chín liên kết một hàng, không đè chuông/avatar; dưới ngưỡng giữ Menu cũ.
- Rà trực tiếp các khu Tổng quan, Môn & Việc, Tập trung, Thống kê, Tài khoản/Cài đặt, Tạo kế hoạch, Cảnh báo, Lịch bận, Giờ học và Đăng nhập. Có ảnh kiểm chứng ở các thời điểm chính trong phiên kiểm tra; dữ liệu mẫu chỉ nằm trong bản sao QA.
- Hash bảo vệ xác nhận model/migration/view/URL/form và service nghiệp vụ không đổi; giữ endpoint POST, chủ sở hữu, CSRF và múi giờ Asia/Ho_Chi_Minh. Không thêm framework hoặc thay thuật toán.

Không có trang bắt buộc nào phải hoãn. Giới hạn đã nêu: một ảnh tham chiếu được cung cấp; font của thân Lịch được giữ để bảo toàn hình học; một phần màu của Flatpickr còn thuộc CSS vendor. Không tự thực hiện các pha chức năng tiếp theo.

## File đã thay đổi

### CSS bố cục/token/theme và stylesheet ứng dụng

- `static/css/app.css`
- `static/css/dashboard.css`
- `static/css/focus.css`
- `static/css/insights.css`
- `static/css/integrations.css`
- `static/css/layout.css` (tạo)
- `static/css/navigation.css`
- `static/css/notifications.css`
- `static/css/planner.css`
- `static/css/studies.css`
- `static/css/theme.css` (tạo)
- `static/css/tokens.css` (tạo)

### Font tự host và nguồn/giấy phép

- `static/fonts/Inter-OFL.txt` (tạo)
- `static/fonts/Lora-OFL.txt` (tạo)
- `static/fonts/README.md` (tạo)
- `static/fonts/fonts.css` (tạo)
- `static/fonts/inter-latin-ext.woff2` (tạo)
- `static/fonts/inter-latin.woff2` (tạo)
- `static/fonts/inter-vietnamese.woff2` (tạo)
- `static/fonts/lora-latin-ext.woff2` (tạo)
- `static/fonts/lora-latin.woff2` (tạo)
- `static/fonts/lora-vietnamese.woff2` (tạo)
- `static/fonts/sources.json` (tạo)

### Template

- `templates/403.html`
- `templates/404.html`
- `templates/500.html`
- `templates/accounts/form_fields.html`
- `templates/accounts/password_change.html`
- `templates/accounts/profile.html`
- `templates/base.html`
- `templates/components/page_header.html`
- `templates/components/settings_layout.html`
- `templates/core/dashboard.html`
- `templates/focus/base.html`
- `templates/focus/log_list.html`
- `templates/focus/start.html`
- `templates/insights/base.html`
- `templates/insights/home.html`
- `templates/insights/report.html`
- `templates/integrations/google.html`
- `templates/notifications/base.html`
- `templates/notifications/email_history.html`
- `templates/notifications/preferences.html`
- `templates/planner/form.html`
- `templates/planner/plan_form.html`
- `templates/studies/base.html`
- `templates/studies/form.html`
- `templates/studies/subject_list.html`

### Mã trình bày/JS nhãn

- `core/templatetags/navigation.py`
- `static/js/form_labels.js` (tạo)

### Test

- `core/test_page_layout.py` (tạo)
- `core/test_ui_cleanup.py`

### Tài liệu

- `docs/BAO_CAO_SO_TAY_XANH.md` (tạo)
- `docs/UI_REDESIGN_PLAN.md`
