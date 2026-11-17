# Render miễn phí cho buổi báo cáo

Cấu hình ngày 17/11/2026, dành cho bản trình diễn tạm thời. `render.yaml` tạo đúng hai tài nguyên: một Web Service Free và một PostgreSQL Free tại Singapore. Web và hai worker chạy chung trong một container, không tạo dịch vụ Background Worker có phí. Không nhập database SQLite hoặc thông tin đăng nhập local lên hosting.

## Giới hạn cần biết

- Web ngủ sau 15 phút không có truy cập; mở lại có thể mất khoảng một phút. Khi web ngủ, cả worker nhắc việc và worker Calendar cũng ngừng. Mở ứng dụng trước buổi báo cáo và kiểm tra lại thao tác cần trình diễn.
- PostgreSQL Free hết hạn 30 ngày sau khi tạo. Không dùng bản này để lưu dữ liệu cần giữ lâu dài. Redeploy web không xóa database PostgreSQL còn hiệu lực.
- Free không đồng nghĩa với AI/email/Google đã được cấu hình. Chưa có API key thì chỉ dùng phân tích Python; email mặc định xuất vào log. Không mô tả chúng là dịch vụ thật đã nghiệm thu.
- Không chọn Upgrade hoặc nhập phương thức thanh toán cho bản demo. Kiểm tra cả web lẫn database đều là **Free** trước khi tạo. Render có hạn mức giờ chạy, băng thông và build; tài khoản không có phương thức thanh toán sẽ bị tạm dừng khi hết hạn mức tương ứng.

Nguồn: [Render Free](https://render.com/docs/free), [Blueprint](https://render.com/docs/blueprint-spec), [Docker](https://render.com/docs/docker).

## Tạo bản deploy

1. Commit/push bản mã chứa `render.yaml`, `config/render.py` và `deploy/demo.py` lên một nhánh GitHub. Chọn đúng nhánh này, không dùng nhánh `main` cũ chưa có cấu hình.
2. Đăng nhập Render, dùng **New → Blueprint**, chọn repository `NgDuyDuc84/Python_DuAnLapKeHoachHocTap`, chọn nhánh vừa push và đường dẫn `render.yaml`. Nếu đang ở trang chọn loại dịch vụ ban đầu, bấm Skip để vào dashboard rồi mở New → Blueprint.
3. Kiểm tra bản xem trước chỉ có `nhip-hoc-demo` (Web / Free) và `nhip-hoc-demo-db` (PostgreSQL / Free), không có tài nguyên trả phí. Xác nhận tạo Blueprint.
4. Chờ database sẵn sàng và web build/start thành công. URL `https://...onrender.com` thật do Render cấp nằm ở trang Web Service; không tự đoán URL từ tên service.
5. Blueprint tắt auto-deploy để không phát sinh build khi chỉ push mã. Khi cập nhật, dùng Manual Deploy → Deploy latest commit của đúng nhánh.

Nếu chưa kết nối GitHub với Render, người dùng tự cấp quyền cho **đúng repository này** trong bước kết nối. Không cần cấp quyền cho toàn bộ repository.

## Những gì cấu hình tự làm

- Dockerfile đóng gói static qua WhiteNoise. Lệnh chạy trên Render là `python -m deploy.demo`.
- `config.render` lấy hostname chính xác từ `RENDER_EXTERNAL_HOSTNAME`, suy ra `SITE_URL` HTTPS và chỉ cho phép hostname đó. Khi thêm domain riêng, đặt rõ `DJANGO_ALLOWED_HOSTS` và `SITE_URL` tương ứng.
- Render sinh `RENDER_SECRET_KEY` 256 bit. Settings dùng SHA-256 để đổi sang chuỗi secret 64 ký tự đáp ứng kiểm tra Django; không ghi secret vào repository. Đổi secret sẽ làm các phiên đăng nhập cũ mất hiệu lực.
- `DATABASE_URL` lấy trực tiếp từ PostgreSQL trong Blueprint, không nhập mật khẩu bằng tay. `ipAllowList: []` chặn truy cập database từ Internet; web truy cập bằng mạng nội bộ Render.
- Trước khi mở cổng, launcher chạy kiểm tra production và migration. Sau đó khởi động Waitress, worker nhắc và worker Calendar. Một tiến trình thoát bất thường sẽ dừng cả nhóm với mã lỗi để hosting khởi động lại; khi nhận lệnh dừng, các tiến trình con được thu dọn.
- `/health/` kiểm tra database mà không chuyển hướng HTTP probe; các trang thông thường vẫn yêu cầu HTTPS và dùng secure cookies. `TRUSTED_PROXY=*` chỉ dành cho container phía sau proxy được Render quản lý, không dùng nếu mở thẳng cổng Waitress ra Internet.

## Nghiệm thu URL thật

Sau khi Render báo Live:

1. Mở `/health/`: trả `{"status":"ok"}`; trang chủ có CSS, font và JavaScript.
2. Đăng ký tài khoản demo mới qua web; kiểm tra đăng nhập, đăng xuất và lưu dữ liệu. Không đưa mật khẩu tài khoản demo vào Git hoặc ảnh báo cáo.
3. Thêm môn, công việc, lịch bận và giờ học; tạo bản xem trước, áp dụng lịch, chỉnh/khóa một buổi. Kiểm tra tài khoản khác không đọc/sửa được dữ liệu này.
4. Thử Pomodoro, nhật ký và thống kê. Tạo việc sắp đến hạn, bật nhắc trong web, chờ worker tạo thông báo; log phải có cả worker reminders và Calendar hoạt động.
5. Kiểm tra giao diện desktop/mobile; ghi lại URL, thời điểm và kết quả thực sự quan sát. Có thể giữ screenshot trang web và trạng thái Live làm bằng chứng báo cáo.

Không chạy `deploy.smoke --allow-test-data` lên bản online: công cụ đó chỉ chấp nhận loopback và dành cho database QA riêng. Không chạy bộ `manage.py test` trên database hosting.

Muốn bật Google sau này, đặt `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_TOKEN_ENCRYPTION_KEY` và callback HTTPS đúng URL web trong Environment; giữ khóa mã hóa ổn định giữa các deploy. AI dùng `OPENAI_API_KEY` cùng model khả dụng. Các khóa chỉ đặt ở hosting, không commit.
