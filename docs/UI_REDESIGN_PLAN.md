# Nhịp Học — Kế hoạch tổ chức lại UI

Ngày lập: **16/11/2026**. Dựa trên `DANH_SACH_TINH_NANG_VA_TRANG_UI.md` và ảnh chụp trang Lịch tuần.

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
Lịch học tập   /planner/            ← GIỮ NGUYÊN
Môn & Việc     tab: Công việc | Môn học | Tài liệu
Tập trung      /focus/  →  phiên đang chạy
Thống kê       tab: Biểu đồ | Nhật ký | AI hỗ trợ
🔔 Thông báo   tab: Thông báo | Email đã gửi
👤 Menu        Tài khoản, Cài đặt, Quản trị (nếu là staff), Đăng xuất
Cài đặt        4 nhóm: Tài khoản | Thời gian (Giờ học, Lịch bận) | Nhắc việc | Kết nối Google
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
| Tạo kế hoạch + Chi tiết kế hoạch | Luồng 3 bước (mục 4.3) | Giữ URL |
| Chỉnh giờ / Ghi nhận buổi học | Thẻ nhỏ có "← Quay lại lịch" | Giữ URL, chỉ đổi cách trình bày |
| Cảnh báo `/planner/alerts/` | Khối "Cần xử lý" trên Tổng quan + link xem đầy đủ | Giữ trang |
| Giờ học + Danh sách/Thêm/Sửa lịch bận | Cài đặt → Thời gian | Nút "+ Thêm lịch bận" trên Lịch giữ nguyên |
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

Gom 7 khối hiện tại thành 4 vùng:

- **Hàng đầu:** lời chào và một nút chính "Bắt đầu tập trung".
- **Cột trái:**
  - "Hôm nay": các buổi học trong ngày, bấm để ghi nhận.
  - "Cần xử lý": việc quá hạn, buổi chưa ghi nhận, xung đột; tối đa 5 dòng kèm "Xem tất cả" (→ `/planner/alerts/`).
- **Cột phải:** phiên Pomodoro đang dở (nếu có), phút học 7 ngày (số + biểu đồ nhỏ), deadline sắp tới.
- **Khi chưa có dữ liệu:** 3 bước gợi ý — Thêm môn → Thêm việc → Xếp lịch.

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

Menu dọc bên trái, 4 nhóm:

- **Tài khoản:** thông tin tài khoản + đổi mật khẩu.
- **Thời gian:** Giờ học; Lịch bận.
- **Nhắc việc:** tùy chọn kênh web/email và độ nhắc sớm.
- **Kết nối Google:** trạng thái, kết nối/ngắt, lịch sử đồng bộ.

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
| Lịch học tập | `/planner/`, `/planner/plans/*`, `/planner/sessions/*`, `/planner/alerts/` |
| Môn & Việc | `/studies/*` |
| Tập trung | `/focus/` và `/focus/sessions/*` |
| Thống kê | `/focus/statistics/`, `/focus/logs/*`, `/insights/*` |
| Thông báo (chuông) | `/notifications/`, `/notifications/email/` |
| Cài đặt (avatar) | `/accounts/profile/`, `/accounts/password-change/*`, `/planner/preferences/`, `/planner/busy/*`, `/notifications/preferences/`, `/integrations/google/*` |

`components/section_tabs.html` nhận danh sách tab và tab hiện tại; dùng cho Thống kê, Thông báo và Môn & Việc. Layout Cài đặt (`components/settings_layout.html`) có menu dọc 4 nhóm như mục 4.4; các trang Cài đặt kế thừa layout này nhưng **giữ URL và view hiện có**.

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
- Ngày giờ: `<input type="datetime-local">` hiển thị theo ngôn ngữ trình duyệt/hệ điều hành, thuộc tính `lang` không đảm bảo kết quả. Muốn cố định dd/mm/yyyy và 24h thì tách thành ô Ngày + ô Giờ, hoặc dùng bộ chọn ngày cục bộ có locale `vi`. Chọn cách ít xâm lấn nhất, giữ nguyên parsing/validation phía server và múi giờ `Asia/Ho_Chi_Minh`, và cập nhật test form nếu cần.
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
