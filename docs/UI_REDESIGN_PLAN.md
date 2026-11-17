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
Thanh trên:  Tổng quan | Lịch học tập | Môn & Việc | Tập trung | Thống kê      🔔  👤
                         (giữ nguyên)

Tổng quan      /
Lịch học tập   /planner/            ← GIỮ NGUYÊN thân Lịch tuần
              Các trang khác: Lịch tuần | Tạo kế hoạch | Cảnh báo | Lịch bận | Giờ học
Môn & Việc     tab: Công việc | Môn học | Tài liệu
Tập trung      /focus/  →  phiên đang chạy
Thống kê       tab: Biểu đồ | Nhật ký | AI hỗ trợ
🔔 Thông báo   tab: Thông báo | Email đã gửi
👤 Menu        Tài khoản, Cài đặt, Quản trị (nếu là staff), Đăng xuất
Cài đặt        3 tab dạng pill: Tài khoản | Nhắc việc | Kết nối Google (không có sidebar)
```

Thanh trên giữ 5 mục nhưng mỗi mục có nghĩa rõ ràng; mọi thứ còn lại nằm trong tab hoặc menu avatar.

---

## 3. Bảng ánh xạ: trang cũ → vị trí mới

| Hiện tại | Chuyển thành | Cách xử lý |
| --- | --- | --- |
| Tổng quan `/` | **Tổng quan** | Dựng lại bố cục (mục 4.1) |
| 3 trang danh sách môn/việc/tài liệu | **Môn & Việc** (3 tab) | Gộp thành 1 trang; URL cũ redirect |
| Thêm/Sửa môn, việc, tài liệu | Drawer/dialog trong trang Môn & Việc | Dùng lại `form_fields.html` |
| Cập nhật tiến độ | Hành động nhanh ở menu `⋯` của dòng công việc | Bỏ trang riêng |
| Các trang xác nhận xóa (studies, planner, focus log) | 1 dialog xác nhận dùng chung | Giữ mô tả ảnh hưởng theo từng loại |
| Tạo kế hoạch + Chi tiết kế hoạch | Lịch học tập → Tạo kế hoạch; luồng 3 bước ở Pha 3 (mục 4.3) | Giữ URL và thanh 5 tab của khu Lịch |
| Chỉnh giờ / Ghi nhận buổi học | Lịch học tập → tab Lịch tuần; thẻ nhỏ ở Pha 4 | Giữ URL và thanh 5 tab của khu Lịch, chỉ đổi cách trình bày |
| Cảnh báo `/planner/alerts/` | Lịch học tập → Cảnh báo; Tổng quan có thể dẫn tới trang này | Giữ trang và URL; phần giải thích đầu trang gập trong details; link "Cài đặt nhắc việc" dẫn tới tùy chọn nhắc |
| Giờ học + Danh sách/Thêm/Sửa/Xóa lịch bận | Lịch học tập → Giờ học / Lịch bận | Giữ URL/view; dùng chung 5 tab của khu Lịch, mục Lịch học tập trên thanh trên luôn active; nút "+ Thêm lịch bận" trên Lịch giữ nguyên |
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

1. **Chọn tuần và chế độ.** Bổ sung / Xếp lại là 2 thẻ lựa chọn có mô tả ngắn. "10 kế hoạch gần đây" gập vào accordion.
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
- **Page header chuẩn:** tiêu đề bên trái, tối đa 1 nút chính (xanh đậm) bên phải.
- **Một dialog xác nhận xóa** dùng chung.
- **Form chuẩn:** 1 cột, nhóm trường rõ ràng, nút Lưu (chính) + Hủy.
- **Toast** và **empty state** dùng chung.
- **Quy ước màu** nhất quán với chú thích của Lịch: lịch bận xanh dương, buổi học xanh đậm, deadline cam; môn học dùng màu riêng của môn.

---

## 6. Thứ tự thực hiện (mỗi pha đều chạy được độc lập)

| Pha | Nội dung |
| --- | --- |
| **1. Nền & điều hướng** | `base.html` mới, thanh trên 5 mục + chuông + menu avatar, trạng thái active; `section_tabs` thay các base riêng (Thống kê, Thông báo); layout Cài đặt (chỉ chuyển link/tab, chưa đổi logic); layout riêng cho đăng ký/đăng nhập |
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

`templates/base.html` hiển thị: Tổng quan | Lịch học tập | Môn & Việc | Tập trung | Thống kê, chuông thông báo, menu avatar. Mục active xác định theo **tên URL**, không theo app:

| Mục | URL thuộc về mục này |
| --- | --- |
| Tổng quan | `/` |
| Lịch học tập | `/planner/`, `/planner/plans/*`, `/planner/sessions/*`, `/planner/alerts/`, `/planner/busy/*`, `/planner/preferences/` |
| Môn & Việc | `/studies/*` |
| Tập trung | `/focus/` và `/focus/sessions/*` |
| Thống kê | `/focus/statistics/`, `/focus/logs/*`, `/insights/*` |
| Thông báo (chuông) | `/notifications/`, `/notifications/email/` |
| Cài đặt (avatar) | `/accounts/profile/`, `/accounts/password-change/*`, `/notifications/preferences/`, `/integrations/google/*` |

`components/section_tabs.html` nhận danh sách tab và tab hiện tại; dùng cho Lịch học tập, Cài đặt, Thống kê, Thông báo và Môn & Việc. Layout Cài đặt (`components/settings_layout.html`) chỉ có 3 tab Tài khoản | Nhắc việc | Kết nối Google, không có sidebar như mục 4.4; các trang Cài đặt kế thừa layout này nhưng **giữ URL và view hiện có**.

Mọi trang Lịch học tập **trừ Lịch tuần** dùng cùng thứ tự tab: **Lịch tuần | Tạo kế hoạch | Cảnh báo | Lịch bận | Giờ học**. Tạo/chi tiết kế hoạch active Tạo kế hoạch; chỉnh giờ/ghi nhận buổi học active Lịch tuần; cảnh báo active Cảnh báo; danh sách/thêm/sửa/xóa lịch bận active Lịch bận; giờ học active Giờ học. Không thêm badge cảnh báo nếu phải tính thêm dữ liệu tốn kém; chỉ dùng cùng nguồn với trang Cảnh báo khi không phát sinh truy vấn đáng kể.

**Dọn hiển thị sau Pha 1:** bỏ eyebrow trên mọi trang trừ các template Lịch tuần được bảo vệ; dùng page header chung có tiêu đề, một dòng mô tả, tối đa một nút chính bên phải. Môn & Việc giữ các URL hiện tại, thứ tự Công việc | Môn học | Tài liệu, mặc định Công việc; học kỳ dạng số hiển thị có nhãn. Tập trung dùng nhãn rỗng “Chọn công việc…” và mô tả 1–2 câu. Tạo kế hoạch đặt form trước, mô tả chế độ ngay dưới lựa chọn và cập nhật khi đổi; phần giải thích cũ gập trong “Cách hệ thống xếp lịch”. Link “Điều chỉnh giờ học” giữ `planner:preferences`. Những thay đổi này không triển khai gộp studies/drawer/redirect/stepper của Pha 2–3.

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

Giữ `/planner/plans/new/`, `/planner/plans/<id>/`, `/planner/plans/<id>/apply/`. Thêm stepper 3 bước, thanh hành động cố định ở đáy ở bước xem trước, accordion cho lịch sử và phần "lý do/phần thiếu". Không đổi thuật toán hay dữ liệu báo cáo.

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
