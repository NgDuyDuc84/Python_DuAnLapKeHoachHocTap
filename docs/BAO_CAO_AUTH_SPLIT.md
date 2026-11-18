# Đăng nhập và đăng ký chung bố cục chia đôi

Ngày kiểm tra: 18/11/2026.

Hai trang dùng `accounts/auth_split.html`, nhận `auth_mode` là `login` hoặc `register`. DOM luôn đặt phần giới thiệu trước form; CSS đổi vị trí trên desktop. Form rộng 480px, khoảng cách hai cột 96px. Dưới 1000px dùng một cột; ở 390px không tràn ngang. Header chỉ có thương hiệu, footer là © Nhịp Học. Giữ nội dung trợ giúp của form hiện có nên trang đăng ký cuộn dọc ở màn hình thấp.

## Trang chủ

Chọn cách (a): khách vào `/` nhận cùng giao diện đăng nhập với `AuthenticationForm`; form POST về URL `accounts:login` hiện có. Không thêm bước chuyển hướng hoặc sửa xử lý POST. Người đã đăng nhập vẫn nhận Tổng quan và Cache-Control như trước. Giữ nguyên URL, validation, CSRF, next, redirect đăng nhập/đăng ký và phân quyền.

## File

Tạo:
- `templates/accounts/auth_split.html`: khung chung, nội dung, form và footer.
- `static/css/auth.css`: bố cục, responsive và View Transitions; dùng token hiện có.
- `accounts/test_auth_layout.py`: kiểm tra chế độ, trường/autocomplete, heading, liên kết, CSRF và lỗi.
- `docs/BAO_CAO_AUTH_SPLIT.md`: báo cáo này.

Sửa:
- `templates/accounts/login.html`, `templates/accounts/register.html`: gọi khung chung theo chế độ.
- `templates/base.html`: thêm block meta description, thuộc tính body, footer và scripts; mặc định giao diện sau đăng nhập giữ nguyên.
- `core/views.py`: cung cấp form đăng nhập cho trang chủ công khai.
- `accounts/forms.py`: thêm autofocus cho tên đăng nhập khi đăng ký, không thay validation.
- `static/css/app.css`: bỏ CSS giới thiệu cũ và auth-intro không còn dùng; giữ auth-card/auth-shell vì các trang tài khoản và trang lỗi còn tham chiếu.
- `core/test_dashboard.py`, `core/test_page_layout.py`, `core/tests.py`: cập nhật kỳ vọng trang chủ và bố cục công khai.

Xóa:
- `templates/core/home.html`: phần giới thiệu cũ đã được thay thế.
- `templates/accounts/form_page.html`: khung đăng nhập/đăng ký cũ không còn được template nào tham chiếu.

## Kiểm tra

- `manage.py check`: đạt, không có vấn đề.
- `manage.py test --noinput`: **343/343 đạt**, bao gồm đăng nhập đúng/sai, đăng ký hợp lệ/không hợp lệ, redirect/next, CSRF, Tổng quan sau đăng nhập và mỗi trang công khai đúng một h1.
- `git diff --check`: đạt.
- Rà trực quan hai chế độ trong trình duyệt tích hợp tại 1920×1080, 1440×900, 1366×768 và 390×844. Desktop xác nhận form 480px và gap 96px; mobile giới thiệu trước form và không cuộn ngang.
- View Transitions: đã thêm navigation auto, hai tên auth-info/auth-form, 350ms ease-in-out và tắt hiệu ứng theo prefers-reduced-motion. Trình duyệt tích hợp nhận diện quy tắc CSS và hai transition-name; liên kết chuyển qua lại hoạt động. Chưa xác minh hoạt ảnh thực tế trên Chrome/Edge riêng, chưa mô phỏng reduced motion hoặc trình duyệt không hỗ trợ.
- Không nhận được hai ảnh dang_nhap.png/dang_ky.png, nên đối chiếu theo yêu cầu chữ đính kèm.

Không sửa model, migration, nghiệp vụ, Django Admin, health hoặc giao diện sau đăng nhập. Chưa commit, push hoặc redeploy thay đổi này.
