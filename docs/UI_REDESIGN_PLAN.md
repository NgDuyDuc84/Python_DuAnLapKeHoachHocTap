# Nhịp Học — Kế hoạch tổ chức lại UI

Ngày lập: **16/11/2026**. Cập nhật sau dùng thử Pha 1: các quyết định điều hướng dưới đây ghi đè bản ban đầu. Dựa trên `DANH_SACH_TINH_NANG_VA_TRANG_UI.md` và ảnh chụp trang Lịch tuần.

**Phạm vi:** tổ chức lại điều hướng, cách gom trang và các thành phần dùng chung của toàn bộ ứng dụng. **Không đổi** nội dung trang Lịch tuần (`/planner/`) vì trang này đã được chỉnh xong; mọi thứ còn lại được sắp xếp xoay quanh nó.

---

## 1. Vấn đề hiện tại

1. **Mỗi app một thanh tab riêng.** Có 5 khung `base.html` khác nhau (`studies`, `planner`, `focus`, `notifications`, `insights`). Đi từ trang này sang trang khác thì menu đổi hình dạng.
2. **Một dữ liệu, hai nơi quản lý.** Môn học, Công việc, Tài liệu vừa nằm trong thanh bên của Lịch, vừa có 3 trang `/studies/...` riêng.
3. **Cài đặt rải rác.** Giờ học (planner), Tùy chọn nhắc (notifications), Tài khoản (menu avatar), Google (mục "Đồng bộ" trên thanh trên).
4. **Thanh điều hướng không theo mức độ dùng.** "Đồng bộ" (thiết lập một lần) ngang hàng với "Lịch"; Thống kê, Nhật ký, Thông báo không có chỗ rõ ràng.
5. **Luồng nhiều bước bị cắt thành trang rời.** Tạo kế hoạch → Chi tiết → Áp dụng; Cảnh báo; Ghi nhận buổi học.
6. **Form còn kiểu mặc định của Django.** Ô ngày hiện `mm/dd/yyyy`, dropdown hiện `---------`.
7. **Trùng lặp template.** Có 4 trang xác nhận xóa riêng (`studies/confirm_delete.html`, `planner/confirm_delete.html`, `focus/log_delete.html`, và các biến thể).

---

## 2. Cấu trúc điều hướng mới

```
Thanh trên: Tổng quan │ Lịch tuần  Tạo kế hoạch  Cảnh báo  Lịch bận  Giờ học │ Môn & Việc  Tập trung  Thống kê    🔔  👤

Tổng quan      /
Lịch tuần     /planner/            ← GIỮ NGUYÊN thân Lịch tuần; gồm Chỉnh giờ / Ghi nhận buổi học
Tạo kế hoạch  /planner/plans/new/   ← gồm chi tiết và áp dụng kế hoạch
Cảnh báo      /planner/alerts/
Lịch bận      /planner/busy/        ← gồm thêm / sửa / xóa
Giờ học       /planner/preferences/
Môn & Việc     tab: Công việc | Môn học | Tài liệu
Tập trung      /focus/  →  phiên đang chạy
Thống kê       tab: Biểu đồ | Nhật ký | AI hỗ trợ
🔔 Thông báo   tab: Thông báo | Email đã gửi
👤 Menu        Tài khoản, Cài đặt, Quản trị (nếu là staff), Đăng xuất
Cài đặt        3 tab dạng pill: Tài khoản | Nhắc việc | Kết nối Google (không có sidebar)
```

Thanh trên có đúng 9 liên kết, chia 3 nhóm: Tổng quan / 5 mục xếp lịch / 3 mục quản lý; ngăn nhóm bằng vạch dọc 1px, cao khoảng 20px. Không còn mục "Lịch học tập" gộp hay thanh tab con trên các trang planner. Từ 1280px trở lên hiển thị một hàng, nav co giãn và căn giữa trong khoảng trống giữa logo và chuông/avatar; dưới 1280px dùng nút Menu mở cùng danh sách theo ba nhóm có tiêu đề nhỏ. Logo, chuông và avatar luôn hiện. Menu đóng khi chọn liên kết, bấm ngoài hoặc Esc; hỗ trợ bàn phím. Chừa khoảng trống trong vùng co giãn cho chip Pomodoro ở Pha 4, chưa triển khai chip.

---

## 3. Bảng ánh xạ: trang cũ → vị trí mới

| Hiện tại | Chuyển thành | Cách xử lý |
| --- | --- | --- |
| Tổng quan `/` | **Tổng quan** | Dựng lại bố cục (mục 4.1) |
| 3 trang danh sách môn/việc/tài liệu | **Môn & Việc** (3 tab) | Gộp thành 1 trang; URL cũ redirect |
| Thêm/Sửa môn, việc, tài liệu | Drawer/dialog trong trang Môn & Việc | Dùng lại `form_fields.html` |
| Cập nhật tiến độ | Hành động nhanh ở menu `⋯` của dòng công việc | Bỏ trang riêng |
| Các trang xác nhận xóa (studies, planner, focus log) | 1 dialog xác nhận dùng chung | Giữ mô tả ảnh hưởng theo từng loại |
| Lịch tuần `/planner/` | **Lịch tuần** trên header | Chỉ đổi header, giữ nguyên thân trang |
| Tạo kế hoạch + Chi tiết/Áp dụng kế hoạch | **Tạo kế hoạch** trên header; luồng 3 bước ở Pha 3 (mục 4.3) | Giữ URL/view; không còn thanh tab con |
| Chỉnh giờ / Ghi nhận buổi học | Active **Lịch tuần** trên header; thẻ nhỏ ở Pha 4 | Giữ URL/view; không còn thanh tab con |
| Cảnh báo `/planner/alerts/` | **Cảnh báo** trên header; Tổng quan có thể dẫn tới trang này | Giữ trang và URL, bỏ tab con; phần giải thích đầu trang gập trong details; link "Cài đặt nhắc việc" dẫn tới tùy chọn nhắc |
| Giờ học + Danh sách/Thêm/Sửa/Xóa lịch bận | **Giờ học** / **Lịch bận** trên header | Giữ URL/view; active đúng mục tương ứng, không có tab con; nút "+ Thêm lịch bận" trên Lịch giữ nguyên |
| Pomodoro (bắt đầu, phiên) | **Tập trung** | Giữ; thêm chip "đang học" ở thanh trên |
| Nhật ký (xem/thêm/sửa/xóa) | Thống kê → Nhật ký | Chỉ đổi thanh tab |
| Thống kê | Thống kê → Biểu đồ | Chỉ đổi thanh tab |
| AI hỗ trợ + Chi tiết báo cáo | Thống kê → AI hỗ trợ | Chỉ đổi thanh tab |
| Hộp thông báo + Lịch sử email | Thông báo (2 tab) | Chuông chỉ hiện 5 mục gần nhất |
| Tùy chọn nhắc | Cài đặt → Nhắc việc | Từ hộp thông báo có link bánh răng |
| Google Calendar + chi tiết yêu cầu đồng bộ | Cài đặt → Kết nối Google | Nút đồng bộ tuần xuất hiện ở cuối luồng kế hoạch |
| Tài khoản + Đổi mật khẩu + trang "thành công" | Cài đặt → Tài khoản | Gộp vào layout Cài đặt; bỏ trang "thành công", dùng thông báo (toast) |
| Trang giới thiệu, Đăng ký, Đăng nhập | Layout riêng, không có thanh menu | |
| Django Admin, lỗi 403/404/500 | Giữ nguyên | Thêm nút "Về Tổng quan" cho 404/500 |

---

## 4. Thiết kế các khu chính

### 4.1. Tổng quan

Quyết định cập nhật: Tổng quan lấy hành động cần làm làm trọng tâm, theo bố cục mẫu gồm thẻ nổi bật, dải số liệu mỏng, hai thẻ nội dung và lịch tuần thu gọn. Bỏ nút "Mở lịch học của bạn" và khối "Bước tiếp theo của bạn". Không thêm biểu đồ nhỏ hay khối xung đột riêng.

- **Đầu trang:** "Chào <tên> · <Thứ>, dd/mm"; dùng tên gọi hoặc tên tài khoản khi chưa có tên. Một câu tóm tắt số buổi hôm nay và số việc chưa hoàn thành đến hạn trong 7 ngày, lấy từ dữ liệu thật. Khi trống: "Hôm nay chưa có buổi học nào."
- **Nên làm bây giờ:** đúng một hành động chính, tối đa một hành động phụ. Một hàm thuần nhận dữ liệu đã truy vấn và chọn trường hợp đầu tiên khớp theo thứ tự:
  1. Có phiên Pomodoro đang dở → "Tiếp tục phiên: <việc>" / **Tiếp tục**. Dùng cùng nguồn `active_session` của Tập trung, gồm cả phiên tạm dừng và phiên nghỉ chưa kết thúc.
  2. Có buổi học đã áp dụng đang diễn ra → **Bắt đầu tập trung** / Ghi nhận.
  3. Có buổi đã qua chưa ghi nhận → **Ghi nhận buổi này**. Vẫn tìm được buổi thuộc tuần trước.
  4. Có việc quá hạn → **Cập nhật tiến độ** / Xếp lịch.
  5. Có việc đến hạn trong 7 ngày chưa đủ lịch → **Xếp lịch** / Học ngay. Tính số phút thiếu bằng cùng hàm với trang Cảnh báo, chỉ tính lịch đã áp dụng và không bị hủy.
  6. Có buổi tiếp theo hôm nay → "Buổi tiếp theo: <việc> lúc HH:mm" / **Xem lịch**.
  7. Chưa hoàn thành khởi đầu → checklist bên dưới.
  8. Còn lại → "Bạn đã sẵn sàng" / **Bắt đầu tập trung**.
- **Checklist khởi đầu:** Thêm môn học → Thêm công việc → Tạo kế hoạch tuần; từng bước có trạng thái hoàn thành và nút đến URL sẵn có. Bước tạo kế hoạch hoàn thành khi đã có kế hoạch, kể cả bản nháp. Giữ checklist tới khi cả ba bước xong, nhưng các hành động 1–6 luôn được ưu tiên. Khi checklist hiện, thay toàn bộ các khối nội dung bên dưới bằng checklist.
- **Dải số liệu:** ba mục bấm được: "Hôm nay X/Y buổi đã ghi nhận" → Lịch; "7 ngày qua: N phút" → Thống kê; "Quá hạn: M" → danh sách việc quá hạn. Buổi học chỉ tính lịch đã áp dụng, không bị hủy. Chỉ tô nổi số quá hạn khi lớn hơn 0. Không hiện số thông báo chưa đọc vì đã có chuông. Ẩn dải khi hiện checklist.
- **Hai thẻ nội dung:**
  - "Hôm nay & sắp tới": tối đa 6 buổi, nhóm Hôm nay / Ngày mai / Thứ N dd/mm. Mỗi dòng có giờ 24 giờ, màu môn, tên việc và Bắt đầu hoặc Ghi nhận; buổi đã ghi nhận hiện trạng thái. Khi hôm nay trống có nút "Xếp lịch tuần này"; không có câu mô tả "Tối đa 6 buổi...".
  - "Việc cần chú ý": tối đa 6 việc chưa hoàn thành có hạn trong 7 ngày hoặc đã quá hạn, theo thứ tự deadline/ưu tiên hiện có; tên, môn, deadline tương đối, chip ưu tiên, "Chưa có lịch" khi thiếu lịch, "Còn X phút cần học", Học ngay và Tiến độ. "Xem tất cả" dẫn tới `/planner/alerts/`. Không thêm câu mô tả dài.
- **Tuần này:** 7 ô T2–CN, đánh dấu hôm nay, ngày có buổi đã áp dụng và ngày có deadline. Dùng lại các tập dữ liệu đã tải; mỗi ô chỉ liên kết tới `/planner/?week=YYYY-MM-DD`. Không sửa trang Lịch.
- **Hành động tập trung:** Học ngay/Bắt đầu của một công việc gửi POST tới endpoint hiện có `focus:home`, kèm CSRF, công việc và `request_key` từ `FocusStartForm`. Không tạo logic phiên mới. Các ngày đầy đủ dùng dd/mm/yyyy, giờ dùng HH:mm, theo múi giờ hiện có.
- **Kiểm chứng:** test đủ 8 nhánh và thứ tự ưu tiên; view 200 cho người mới, việc chưa đủ lịch, phiên đang chạy; test quyền sở hữu, CSRF/chống gửi lặp và số phút thiếu khớp Cảnh báo. Đo toàn bộ GET trước/sau trên cùng dữ liệu: 14 → 12 truy vấn; thêm dải Tuần này không phát sinh truy vấn riêng.

### 4.2. Môn & Việc

- Một nút chính duy nhất "+ Thêm …", đổi theo tab đang mở.
- Thanh lọc gọn một hàng: tìm kiếm, môn, trạng thái, công tắc "quá hạn"; các bộ lọc còn lại gập vào "Bộ lọc khác".
- Mỗi dòng công việc: chấm màu môn, tên, deadline, phút còn lại, trạng thái; hành động trong menu `⋯` (Sửa, Cập nhật tiến độ, Xóa).
- Thanh bên của Lịch giữ nguyên hành vi; chỉ dùng chung component/form với trang này và có thể thêm link "Mở trang đầy đủ".

### 4.3. Luồng xếp kế hoạch (3 bước, có stepper)

1. **Chọn tuần và chế độ.** Bổ sung / Xếp lại có mô tả ngắn ngay dưới lựa chọn. Bố cục hiện tại là form bên trái và thẻ "Cách hệ thống xếp lịch" bên phải (ba ý ngắn + details cho chi tiết); gợi ý tuần nằm ngay dưới ô ngày. "10 kế hoạch gần nhất" rộng đủ khung ở bên dưới, không gập toàn bộ lịch sử vào accordion.
2. **Xem trước.** Thanh tóm tắt trên cùng (đã xếp X/Y phút, thiếu Z, n cảnh báo), rồi bảng các buổi. Lý do và phần thiếu gập lại. Thanh dưới cố định: [Hủy] [Áp dụng vào lịch].
3. **Áp dụng.** Quay về Lịch kèm thông báo; nếu đã kết nối Google thì có nút "Đồng bộ lên Google Calendar".

### 4.4. Cài đặt

Không có sidebar trái. Dùng component tab dạng pill như Môn & Việc / Thống kê, gồm đúng 3 mục:

- **Tài khoản:** thông tin tài khoản + đổi mật khẩu.
- **Nhắc việc:** tùy chọn kênh web/email và độ nhắc sớm.
- **Kết nối Google:** trạng thái, kết nối/ngắt, lịch sử đồng bộ và chi tiết yêu cầu.

Giờ học và mọi trang Lịch bận thuộc **Lịch học tập**, không nằm trong Cài đặt. Link Cài đặt ở avatar dẫn tới Tài khoản. Đổi mật khẩu active tab Tài khoản; chi tiết yêu cầu đồng bộ active tab Kết nối Google. Tiêu đề, mô tả và tối đa một nút chính nằm trong page header chung, đặt ngoài thẻ nội dung. Trang Tài khoản không có nút "Vào không gian học tập"; chỉ staff thấy dòng Vai trò.

Thông báo kỹ thuật về Google/email/dịch vụ nền chỉ dành cho staff hoặc DEBUG. Người dùng thường thấy lời giải thích thân thiện. Nút kết nối Google bị vô hiệu khi chưa cấu hình; checkbox email bị vô hiệu khi backend hiện tại chỉ dùng kiểm thử, kèm chú thích và giữ nguyên giá trị tùy chọn đã có.

### 4.5. Thống kê, Thông báo, Tập trung

- **Thống kê:** 3 tab Biểu đồ | Nhật ký | AI hỗ trợ; bộ lọc khoảng ngày dùng chung (`focus/range_filter.html`) cho Biểu đồ và Nhật ký.
- **Thông báo:** 2 tab Thông báo | Email đã gửi.
- **Tập trung:** giữ trang bắt đầu và trang phiên; thêm chip "Đang tập trung" trên thanh trên khi có phiên chạy.

---

## 5. Thành phần dùng chung

- **Một `base.html`** + component tab (`components/section_tabs.html`) thay cho 5 khung hiện tại.
- **Page header chuẩn:** tiêu đề bên trái, mô tả một dòng, tối đa 1 nút chính (xanh đậm) bên phải, vùng tab tùy chọn; dùng `components/page_header.html`.
- **Một dialog xác nhận xóa** dùng chung.
- **Form chuẩn:** theo các kiểu trang ở mục 5.1; form không có nội dung phụ dùng đủ khung với trường hai cột từ 1024px, nút Lưu (chính) + Hủy.
- **Toast** và **empty state** dùng chung.
- **Quy ước màu** nhất quán với chú thích của Lịch: lịch bận xanh dương, buổi học xanh đậm, deadline cam; môn học dùng màu riêng của môn.

### 5.1. Bố cục (quyết định cập nhật)

Giá trị đo từ mã thật: `.container` của đa số trang có chiều rộng tối đa **1120px**, không phải con số 1260px ước tính. Chọn `--page-w: 1120px`; `--narrow-w: 760px`; `--auth-w: 480px`; `--section-gap: 24px`; padding thẻ 24px. Các giá trị khung tính cả padding do `box-sizing: border-box`. `--gutter` là 32px từ 1280px, 24px trong khoảng 768–1279px (gồm 1024–1279px), 16px dưới 768px.

`base.html` có đúng một `main.page`, block `page_class` mặc định lấy từ bảng tên URL trong `navigation_state`. Không đặt độ rộng trang rải rác theo app. `layout.css` quyết định khung, bỏ giới hạn thẻ con gây trống nửa trang; `main_class` cũ vẫn tương thích với Lịch tuần.

| Kiểu | Trang | Quy tắc |
| --- | --- | --- |
| A — Rộng | Chỉ Lịch tuần | Giữ `.container.calendar-container` hiện có: tối đa 1720px, lề 24px khi co lại, 18px dưới 640px; không đổi HTML/JS/lưới/kích thước/spacing của Lịch |
| B — Tiêu chuẩn | Tổng quan; ba danh sách Môn & Việc; Biểu đồ/Nhật ký/AI và báo cáo; Cảnh báo; danh sách Lịch bận; Thông báo/Email; chi tiết kế hoạch; chi tiết đồng bộ; trang phiên Tập trung | `max-width: var(--page-w)`, căn giữa, padding ngang theo gutter; tiêu đề/tab/nội dung cùng mép |
| C — Form + phụ | Tạo kế hoạch, bắt đầu Tập trung, Giờ học, Nhắc việc, Tài khoản, Kết nối Google, Đổi mật khẩu có quy tắc | Cùng khung B; `.split` = `minmax(0,7fr) minmax(0,5fr)`, gap 24px; aside sticky cách đỉnh bằng chiều cao header 64px + 16px; dưới 1024px thành một cột, aside xuống dưới và bỏ sticky |
| D — Hẹp | Thêm/sửa/xóa Lịch bận; thêm/sửa/xóa Nhật ký; các xác nhận xóa; Ghi nhận/Chỉnh giờ buổi học; trang lỗi | `.page--narrow`, cả tiêu đề và thẻ nằm trong khung 760px căn giữa |
| Đăng nhập | Đăng nhập/Đăng ký | `.page--auth`, khung 480px, giữ layout công khai |

Các form thêm/sửa môn, việc, tài liệu và cập nhật tiến độ không có nội dung phụ thật: dùng đủ khung B, trường hai cột từ 1024px; textarea chiếm hai cột. Đổi mật khẩu không có quy tắc sẵn có cũng dùng đủ khung thay vì `.split`. Trang giới thiệu dùng khung B.

- Tạo kế hoạch: form trước; thẻ phụ có ba ý + details phần giải thích cũ; kế hoạch gần đây đủ khung ở dưới. Quyết định này ghi đè việc gập toàn bộ giải thích trong details toàn chiều rộng.
- Tập trung: form hoặc phiên đang dở ở cột chính; 10 phiên gần nhất ở cột phụ.
- Giờ học: gom chính các help text hiện có vào thẻ Lưu ý, giữ ID cho `aria-describedby`. Nhắc việc: đưa các ghi chú hiện có sang Lưu ý. Tài khoản: thông tin ở trái, thẻ Mật khẩu/Đổi mật khẩu ở phải. Google: Tài khoản Google / Đồng bộ một chiều; Yêu cầu gần đây đủ khung phía dưới.
- Page header chung có khoảng trên 40px và cách nội dung 24px; dưới 768px khoảng trên 28px. Trừ Lịch tuần và trang auth, mọi trang dùng component này; tab tùy chọn được render ngay sau tiêu đề/mô tả.
- Thẻ cạnh nhau stretch, flex dọc; empty state căn giữa. Hai thẻ Tổng quan cao bằng nhau, dải số liệu ba cột bằng nhau. Môn học: ba cột từ 1100px, hai cột từ 720px, một cột nhỏ hơn.
- Lịch sử kế hoạch, Nhật ký, Email và đồng bộ dùng đủ khung, hàng/cột nhất quán và chuyển thành thẻ trên màn nhỏ. Không bỏ dữ liệu hay hành động hiện có.
- Giữ chỗ thanh cuộn dọc để các trang chuẩn không lệch mép khi nội dung dài/ngắn. Lịch tuần có ngoại lệ để khung rộng và vị trí của nó giữ nguyên.

### 5.2. Phong cách — Sổ tay xanh

`static/css/tokens.css` là nơi duy nhất khai báo `:root` và biến dùng chung, nạp trước mọi CSS khác. `theme.css` áp phong cách lên thành phần dùng chung, không thay đổi thứ tự khối, URL hay hành vi. Phong cách áp sau bố cục 5.1; ảnh mẫu là tham chiếu hình thức, không thêm dữ liệu hoặc nội dung giả.

| Nhóm token | Giá trị |
| --- | --- |
| Nền/viền | bg `#F7F3E8`, bg-sunk `#EFE9D8`, surface `#FFFDF9`, line `#E9E2D0`, line-strong `#D9D0B8` |
| Chữ | ink `#14312B`, text `#38443E`, muted `#5F6A63` |
| Xanh thông | pine `#1D6B56`, pine-hover `#17594A`, pine-soft `#DDEFE5`, pine-softer `#EEF7F1` |
| Hổ phách | amber `#E59E2B`, amber-soft `#FFF1D3`, amber-line `#F2D9A4`, amber-ink `#8A5410` |
| San hô | coral `#E1584B`, coral-soft `#FCE5E1`, coral-ink `#9C2F26` |
| Xanh trời | sky `#4A86C9`, sky-soft `#E4EEFA`, sky-ink `#24507F` |
| Môn học s1–s8 | `#EF6A5B #F2B134 #86C240 #26B39B #4DA3E0 #6B79E6 #A56BE0 #E96AA6`; giữ nguyên màu đã lưu của người dùng |
| Bo góc | r-sm 10px, r-md 14px, r-lg 22px |
| Bóng | sh-sm `0 1px 2px rgba(60,48,20,.05)`; sh-md `0 1px 2px rgba(60,48,20,.04), 0 12px 28px -18px rgba(60,48,20,.28)`; sh-lg `0 2px 4px rgba(60,48,20,.04), 0 24px 48px -28px rgba(60,48,20,.38)` |
| Focus | ring `0 0 0 3px rgba(29,107,86,.28)`, kèm outline có thể thấy |
| Chữ | display `'Lora', Georgia, 'Times New Roman', serif`; UI `'Inter', system-ui, 'Segoe UI', Roboto, sans-serif` |

- Font WOFF2 variable tự host trong `static/fonts/`, đủ Latin/Latin mở rộng/tiếng Việt, `font-display: swap`; preload hai subset Latin chính. Giữ file font gốc và giấy phép OFL; không gọi CDN lúc chạy. Xem nguồn/checksum ở `static/fonts/sources.json`.
- h1/h2/h3, tên thẻ và số lớn dùng Lora; phần còn lại dùng Inter. Giờ/số bảng dùng tabular-nums. Riêng thân Lịch tuần giữ Segoe UI để không đổi ngắt dòng/kích thước đã kiểm chứng.
- Nền gradient nhẹ `#F9F5EB → #F5F0E2`; header nền `rgba(255,253,248,.9)`, logo gradient xanh. Nav là pill padding 8px 13px, active pine-soft/pine-hover đậm 650, **bỏ gạch chân cũ**, giữ vạch ngăn nhóm. Tab nội dung bo 12px, active pine-soft.
- Nút chính pine/chữ trắng, bo 14px, bóng nhẹ/viền sáng trong; phụ surface/line-strong/pine; nguy hiểm coral-soft/coral-ink; có cỡ nhỏ, trạng thái disabled và focus rõ.
- Thẻ surface/line/r-lg/sh-md. Thẻ hành động Tổng quan a–e gradient `#FFF3D9 → #FFF9EC → #FFFDF9`, viền amber-line/sh-lg; f/h dùng pine-softer.
- Chip có cặp nền soft/chữ ink: thiếu lịch amber, đủ lịch pine, quá hạn coral, lịch bận sky. Màu môn vẫn là dữ liệu người dùng, không đổi model/mặc định đã lưu.
- Ô nhập/select/textarea cao ban đầu 48px, bo 12px, viền 1.5px line-strong; textarea có thể kéo cao hơn; checkbox/radio giữ cỡ phù hợp. Label 14px đậm, chú thích 13px. JS nhãn form dùng chung đổi riêng option `---------` thành nhãn Chọn… bằng tiếng Việt, không đổi value/tập lựa chọn và không chạy trong Lịch tuần.
- Message/dialog/bảng dùng token tương ứng; success pine-soft, warning amber-soft, error coral-soft. Chữ thường tối thiểu 4.5:1; không dùng amber làm chữ trên nền sáng. Transition màu/bóng/transform 150ms; thẻ bấm hover nâng 1px, nút nhấn xuống 1px; tắt animation/transform theo reduced-motion.
- Lịch tuần chỉ nhận đổi màu/bo góc/bóng qua token; giữ các template, JS và khai báo bố cục cũ. Không áp quy tắc input 48px, page padding hay grid mới vào thân Lịch.

---

## 6. Thứ tự thực hiện (mỗi pha đều chạy được độc lập)

| Pha | Nội dung |
| --- | --- |
| **1. Nền & điều hướng** | `base.html` mới, thanh trên 9 mục theo ba nhóm + chuông + menu avatar, menu thu gọn dưới 1280px, trạng thái active theo mục 8.2; bỏ tab planner; `section_tabs` thay các base riêng (Thống kê, Thông báo); layout Cài đặt (chỉ chuyển link/tab, chưa đổi logic); layout riêng cho đăng ký/đăng nhập |
| **2. Môn & Việc** | Gộp 3 trang thành tab, drawer/dialog thêm-sửa, dialog xóa dùng chung, form chuẩn (ngày giờ, nhãn rỗng), redirect URL cũ |
| **3. Tổng quan & luồng kế hoạch** | Dựng lại Tổng quan (4.1); stepper + thanh hành động dính cho tạo kế hoạch / chi tiết kế hoạch |
| **4. Hoàn thiện** | Thẻ nhỏ cho Chỉnh giờ / Ghi nhận buổi, chip Pomodoro, empty state, toast |

---

## 7. Giữ nguyên

- Toàn bộ model, migration, logic nghiệp vụ, thuật toán xếp lịch, nhắc việc, tích hợp Google/AI.
- Trang Lịch tuần: `planner/week.html`, `planner/study_sidebar.html`, `planner/calendar_item.html` và view tương ứng. Chỉ thanh điều hướng trên cùng thay đổi; thân trang phải hiển thị như cũ.
- Django Admin, trang lỗi, `/health/`, các endpoint POST ở mục 4 của file danh sách tính năng.

### Tùy chọn trên trang Lịch (chỉ làm nếu chủ dự án đồng ý)

- Nút "Môn học", "Tài liệu" trên thanh công cụ trùng với tab trong thanh bên → bỏ hoặc gộp thành một nút.
- Hai nút đóng chồng nhau: "Đóng bảng học tập" và "Đóng" trong form.
- Ô ngày hiện kiểu `mm/dd/yyyy`.
- Nút "Xếp lịch tuần này" dẫn thẳng vào luồng 3 bước (4.3).

---

## 8. Đặc tả kỹ thuật cho người triển khai

### 8.1. Nguyên tắc bất biến

- Không thêm model, không tạo migration, không đổi logic nghiệp vụ.
- Giữ nguyên **tên URL (reverse name)** hiện có. Trang bị gộp thì URL cũ **redirect khi GET**; nếu việc bỏ xử lý POST ở URL cũ làm vỡ test hoặc tích hợp hiện có, giữ POST ở URL cũ với hành vi như cũ.
- Giữ phân quyền theo chủ sở hữu và CSRF.
- Không thêm framework front-end; dùng stack hiện có. Nếu bắt buộc cần thư viện nhỏ, đặt file cục bộ (không tải CDN) và nêu lý do.
- Toàn bộ chữ hiển thị bằng tiếng Việt.
- Tái sử dụng truy vấn/service sẵn có; không nhân đôi logic (ví dụ khối "Cần xử lý" dùng cùng nguồn dữ liệu với `/planner/alerts/`).

### 8.2. Điều hướng và trạng thái active

`templates/base.html` hiển thị đúng 9 liên kết theo sơ đồ mục 2, chuông thông báo và menu avatar. Dùng reverse name hiện có, không gõ cứng URL. Mục active xác định theo **tên URL**, không theo app; dùng pill pine-soft/pine-hover đậm 650 và `aria-current="page"` theo phong cách mục 5.2, thay gạch chân cũ. Mỗi trang chỉ có một danh sách nav dùng chung cho desktop/menu, không nhân đôi liên kết. URL không thuộc bảng không active mục nào:

| Mục | URL thuộc về mục này |
| --- | --- |
| Tổng quan | `/` |
| Lịch tuần (`planner:week`) | `/planner/` và `/planner/sessions/*` (`session_move`, `session_record`, `session_lock`) |
| Tạo kế hoạch (`planner:plan_generate`) | `/planner/plans/*` (`plan_generate`, `plan_detail`, `plan_apply`) |
| Cảnh báo (`planner:alerts`) | `/planner/alerts/` |
| Lịch bận (`planner:busy_list`) | `/planner/busy/*` (`busy_list`, `busy_create`, `busy_update`, `busy_delete`) |
| Giờ học (`planner:preferences`) | `/planner/preferences/` |
| Môn & Việc | `/studies/*` |
| Tập trung | `/focus/` và `/focus/sessions/*` |
| Thống kê | `/focus/statistics/`, `/focus/logs/*`, `/insights/*` |
| Thông báo (chuông) | `/notifications/`, `/notifications/email/` |
| Cài đặt (avatar) | `/accounts/profile/`, `/accounts/password-change/*`, `/notifications/preferences/`, `/integrations/google/*` |

`components/section_tabs.html` nhận danh sách tab và tab hiện tại; dùng cho Cài đặt, Thống kê, Thông báo và Môn & Việc; **không dùng trên planner**. Layout Cài đặt (`components/settings_layout.html`) chỉ có 3 tab Tài khoản | Nhắc việc | Kết nối Google, không có sidebar như mục 4.4; các trang Cài đặt kế thừa layout này nhưng **giữ URL và view hiện có**.

Mọi trang planner đều bỏ thanh tab con, chỉ giữ tiêu đề/nội dung hiện có; Lịch tuần giữ nguyên block và thân trang. Bảng active trên ghi đè quyết định cũ về mục "Lịch học tập" và năm tab con. Header dùng flex, không căn giữa bằng position:absolute; từng liên kết nowrap. Chuyển sang Menu ở **1280px**: 1280px trở lên một hàng, dưới ngưỡng ẩn dãy và mở bảng danh sách có nhãn nhóm. Dùng details và JS header hiện có để đóng khi bấm ngoài, Esc hoặc chọn mục; đồng bộ `aria-expanded`. Trên desktop menu điều hướng luôn mở, mở chuông/avatar không làm mất nav.

Badge Cảnh báo chỉ được thêm nếu số đếm đúng nguồn của `build_alerts`, chỉ hiện khi > 0, tốn tối đa một truy vấn nhẹ/request hoặc dùng dữ liệu sẵn có. **Bản hiện tại bỏ badge:** nguồn Cảnh báo gồm thiếu phút trước hạn, xung đột và buổi chưa ghi nhận; tính đầy đủ đòi hỏi nhiều tập dữ liệu và xử lý, không thể có cùng số chính xác trong giới hạn này. Không thay bằng số việc quá hạn hoặc số thông báo chưa đọc. Không gọi `build_alerts` từ header.

**Dọn hiển thị sau Pha 1:** bỏ eyebrow trên mọi trang trừ các template Lịch tuần được bảo vệ; dùng page header chung có tiêu đề, một dòng mô tả, tối đa một nút chính bên phải. Môn & Việc giữ các URL hiện tại, thứ tự Công việc | Môn học | Tài liệu, mặc định Công việc; học kỳ dạng số hiển thị có nhãn. Tập trung dùng nhãn rỗng “Chọn công việc…” và mô tả 1–2 câu. Tạo kế hoạch dùng `.split` theo mục 5.1: form trái, mô tả chế độ ngay dưới lựa chọn và cập nhật khi đổi; thẻ giải thích bên phải có ba ý ngắn và details cho phần chi tiết. Link “Điều chỉnh giờ học” giữ `planner:preferences`. Những thay đổi này không triển khai gộp studies/drawer/redirect/stepper của Pha 2–3.

**Lưu ý với Lịch tuần:** nếu `planner/week.html` đang kế thừa `planner/base.html`, phải giữ cấu trúc block tương thích để thân trang Lịch không đổi. Kiểm tra trang `/planner/` hiển thị như cũ (chỉ khác thanh trên).

### 8.3. Môn & Việc

- URL đề xuất: `/studies/` với `?tab=tasks|subjects|materials` (mặc định `tasks`), kèm `q`, các bộ lọc, `page`, `action=new|edit|delete|progress`, `id`. Cơ chế query-param, server-render, giống thanh bên Lịch.
- Redirect (GET): `/studies/subjects/` → `?tab=subjects`; `/studies/tasks/` → `?tab=tasks`; `/studies/materials/` → `?tab=materials`; `.../add/` → `&action=new`; `.../<id>/edit/` → `&action=edit&id=<id>`; `.../<id>/delete/` → `&action=delete&id=<id>`; `/studies/tasks/<id>/progress/` → `?tab=tasks&action=progress&id=<id>`.
- Drawer/dialog chỉ là lớp trình bày của form server-render; dùng lại `studies/form_fields.html` và validation sẵn có, không viết lại.
- Chỉ trích xuất partial dùng chung với thanh bên Lịch khi việc đó **không** làm đổi giao diện hay hành vi của thanh bên. Nếu không chắc, để nguyên thanh bên.

### 8.4. Dialog xác nhận xóa

Tạo `components/confirm_delete.html`. Các template xác nhận xóa hiện có trở thành wrapper mỏng (hoặc được thay thế), vẫn giữ nguyên mô tả ảnh hưởng của từng loại dữ liệu (ví dụ xóa môn: giữ công việc/tài liệu, bỏ liên kết môn).

### 8.5. Form

- Trường chọn môn: `empty_label` tiếng Việt (ví dụ "Chọn môn học" hoặc "Không gắn môn") thay cho `---------`.
- Ngày giờ: đã thống nhất bằng Flatpickr 4.6.13 cục bộ và một controller `static/js/datetime_inputs.js` trong layout chung. Locale tiếng Việt `vi` (alias từ `vn` của upstream), hiển thị `dd/mm/yyyy`, `HH:mm` hoặc `dd/mm/yyyy HH:mm`; giữ giá trị gửi lên là ISO như cũ. Không tạo widget riêng ở từng trang hoặc đổi parsing/validation Django. Khi JS/thư viện khởi tạo lỗi, trở về input date/time/datetime-local gốc; không dựa vào thuộc tính lang để ép định dạng native. Giữ múi giờ server `Asia/Ho_Chi_Minh` và các test nhận ISO.
- Bố cục form 1 cột, nhóm trường, nút Lưu (chính) + Hủy.

### 8.6. Luồng kế hoạch

Giữ `/planner/plans/new/`, `/planner/plans/<id>/`, `/planner/plans/<id>/apply/`. Stepper và thanh hành động cố định ở đáy bước xem trước vẫn là phần việc sau. Lịch sử giữ rộng đủ khung bên dưới form theo quyết định bố cục 5.1; chỉ phần giải thích chi tiết/lý do có thể gập. Không đổi thuật toán hay dữ liệu báo cáo.

### 8.7. Chip Pomodoro

Context processor chỉ chạy khi đã đăng nhập, dùng tối đa 1 truy vấn để tìm phiên đang hoạt động của người dùng. Phiên bản đầu hiển thị chip tĩnh "Đang tập trung" dẫn tới trang phiên; đếm ngược là tùy chọn (dùng endpoint `/focus/sessions/<id>/state/` sẵn có).

### 8.8. Thông báo

Giữ chuông và danh sách 5 thông báo gần nhất. `/notifications/` và `/notifications/email/` dùng chung thanh tab. Trang Tùy chọn nhắc dùng layout Cài đặt, có link bánh răng từ hộp thông báo. Trang đổi mật khẩu thành công: chuyển về trang Tài khoản kèm thông báo thành công.

### 8.9. Kiểm thử và nghiệm thu

- `python manage.py check` và `python manage.py test` đều qua.
- Mỗi URL cũ bị gộp: GET trả redirect đúng; test mới cho các redirect.
- Mỗi URL thuộc bảng 8.2 hiển thị đúng mục active (kiểm tra các trường hợp chính).
- Người dùng chưa đăng nhập vẫn bị chuyển hướng như cũ; dữ liệu vẫn giới hạn theo chủ sở hữu.
- Danh sách kiểm tra thủ công cuối mỗi pha: mở từng trang trong thanh trên và trong menu avatar; thêm/sửa/xóa một môn, một việc, một tài liệu; tạo và áp dụng một kế hoạch; chạy một phiên Pomodoro; `/planner/` hiển thị như cũ.
