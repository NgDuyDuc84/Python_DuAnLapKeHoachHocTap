**Thiết kế ban đầu — Nhịp Học**

Tài liệu thiết kế, chưa phải danh sách model đã được triển khai. Tên Nhịp Học là tên hiển thị tạm thời. Đã triển khai bộ khung ở mốc 01 và luồng tài khoản ở mốc 02; các model học tập vẫn là thiết kế dự kiến.

1. **Phân chia trách nhiệm**

   Python xử lý tài khoản, kiểm tra quyền, lưu dữ liệu, thời gian/lịch lặp, thuật toán lập kế hoạch, thống kê, cảnh báo, thông báo và gọi API. Django Templates dựng trang từ dữ liệu máy chủ. JavaScript chỉ cần cho các tương tác như kéo thả lịch và đồng hồ Pomodoro.

   Trong từng module: `models.py` biểu diễn dữ liệu; `forms.py` kiểm tra biểu mẫu; `views.py` nhận request; nghiệp vụ phức tạp đặt ở `services/`. Không chuyển thuật toán xếp lịch sang trình duyệt.

2. **Cấu trúc dự kiến**

   | Module | Vai trò | Trạng thái hiện tại |
   |---|---|---|
   | config | Settings, URL, WSGI/ASGI | Đã tạo cho local |
   | core | Trang chủ và giao diện chung | Đã tạo |
   | accounts | Luồng tài khoản, quyền và hồ sơ | Đã có đăng ký, đăng nhập/đăng xuất, đổi mật khẩu và thông tin tài khoản riêng |
   | studies | Môn, công việc, tài liệu | Chưa triển khai |
   | planner | Lịch bận, tùy chọn, kế hoạch, thuật toán | Chưa triển khai |
   | focus | Pomodoro, nhật ký học | Chưa triển khai |
   | notifications | Nhắc việc và email | Chưa triển khai |
   | insights | Thống kê, AI | Chưa triển khai |
   | integrations | Kết nối lịch bên ngoài | Chưa triển khai |

3. **Dữ liệu nghiệp vụ dự kiến**

   | Đối tượng | Nội dung và quan hệ |
   |---|---|
   | User | Dùng User mặc định Django; username, email, mật khẩu băm, trạng thái, quyền staff/superuser |
   | StudyPreference | Thuộc user; khung giờ học theo ngày, múi giờ, phút tối đa/ngày, độ dài buổi, phút nghỉ |
   | Subject | Thuộc user; tên môn, màu, học kỳ, trạng thái lưu trữ |
   | Task | Thuộc user, có thể gắn môn; deadline, ưu tiên, phút ước tính/còn lại, cho phép chia nhỏ, trạng thái |
   | BusyEvent | Thuộc user; lịch một lần hoặc mẫu lặp hằng tuần, giờ bắt đầu/kết thúc, khoảng ngày hiệu lực |
   | StudyPlan | Thuộc user; tuần, trạng thái nháp/áp dụng |
   | StudySession | Thuộc công việc; thời gian, trạng thái, nguồn thủ công/tự động, cờ khóa và kế hoạch nếu có |
   | StudyLog | Nhật ký thực tế; công việc, phút học, ghi chú, buổi học nếu có |
   | FocusSession | Phiên Pomodoro; user, công việc, trạng thái và các mốc học/nghỉ/tạm dừng |
   | Material | Thuộc user; tên, URL, mô tả, môn/công việc liên quan |
   | Reminder | Đối tượng, kênh, thời điểm, phiên bản và trạng thái gửi |
   | CalendarConnection | User, lịch đích, thông tin cấp quyền được bảo vệ và trạng thái |
   | CalendarEventMapping | Buổi học, ID sự kiện bên ngoài và trạng thái đồng bộ |

   Mỗi quan hệ dữ liệu phải cùng chủ sở hữu. Một công việc có thể có nhiều buổi học. Thời gian đã học và trạng thái hoàn thành công việc được lưu riêng; hết thời gian không tự động chứng minh đã làm xong việc.

   Ở mốc 02, tài khoản mới được tạo qua `UserCreationForm` mở rộng với email bắt buộc. Đăng nhập bằng username; email phục vụ thông tin hồ sơ, chưa có xác minh hoặc khôi phục mật khẩu qua email. Username là định danh duy nhất; không áp dụng ràng buộc email duy nhất ở mốc này.

   Trang thông tin lấy user trực tiếp từ phiên đăng nhập, không nhận ID người khác để xem. Đăng xuất dùng POST có CSRF. `is_staff` cho phép vào khu vực Admin; quyền xem/sửa người dùng được Django kiểm tra riêng. Tài khoản tạo bằng `createsuperuser` có đầy đủ quyền quản trị. Form đăng ký không cho người dùng tự đặt `is_staff`, `is_superuser` hoặc nhóm quyền.

4. **Quy tắc lịch**

   - Múi giờ mặc định: `Asia/Ho_Chi_Minh`; timestamp có múi giờ và được lưu nhất quán qua Django.
   - Khoảng thời gian tính từ đầu đến trước cuối: hai buổi 08:00–09:00 và 09:00–10:00 không chồng nhau.
   - Chỉ xếp trong tương lai, thuộc khung được học, không chồng lịch bận/buổi khác và không vượt deadline.
   - Tôn trọng giới hạn ngày, khoảng nghỉ và công việc phải làm liên tục.
   - Xếp lại giữ buổi đã hoàn thành, buổi thủ công và buổi khóa; thay phần tự động còn lại.
   - Tạo phương án nháp, xem trước rồi áp dụng; kiểm tra lại xung đột trước khi lưu.
   - Cảnh báo dựa trên dữ liệu chương trình tính; AI giải thích và gợi ý, không tự bỏ qua ràng buộc.

5. **Các màn hình và luồng chính**

   | Màn hình | Chức năng dự kiến |
   |---|---|
   | Trang chủ | Giới thiệu ngắn và cách sử dụng; đã có ở mốc 01 |
   | Tài khoản | Đăng ký, đăng nhập/đăng xuất, đổi mật khẩu |
   | Tổng quan | Hôm nay, deadline gần, cảnh báo, thao tác chính |
   | Môn học/công việc | Nhập, sửa, lọc và quản lý tiến độ |
   | Lịch tuần | Lịch bận, buổi học, tạo và chỉnh phương án |
   | Tài liệu | Liên kết theo môn hoặc công việc |
   | Tập trung | Pomodoro gắn công việc |
   | Thống kê/AI | Nhật ký, chỉ số thực tế và đề xuất |
   | Cài đặt | Khung giờ học, nhắc việc và kết nối lịch |
   | Quản trị | Quản lý người dùng, khóa/mở tài khoản |

   Luồng nghiệm thu: đăng ký → nhập môn và công việc → nhập lịch bận → tạo kế hoạch → áp dụng/chỉnh sửa → học và ghi nhận tiến độ → xem cảnh báo/thống kê/AI → nhận nhắc → kiểm tra lịch đồng bộ.

6. **Tình huống cần kiểm tra ở các mốc sau**

   | Tình huống | Kết quả mong muốn |
   |---|---|
   | Công việc 180 phút, có ba khoảng 60 phút | Có thể phân bổ ba buổi nếu cho chia nhỏ |
   | Cần 180 phút, chỉ còn 120 phút trước hạn | Nêu rõ 60 phút chưa xếp được |
   | Việc phải liên tục 90 phút, chỉ có khoảng rời 60 phút | Không tự chia nhỏ |
   | Hai việc cùng hạn tranh một khoảng trống | Xét chung nguồn thời gian, không hứa đủ cho cả hai |
   | Thêm ca làm sau khi áp dụng kế hoạch | Phát hiện ảnh hưởng và cho xếp lại phần được phép |
   | A gửi request sửa công việc của B | Bị từ chối, dữ liệu của B giữ nguyên |
   | Học hết thời gian dự kiến nhưng chưa xong | Cho cập nhật thời lượng còn lại, không tự đánh dấu xong |
   | Dịch vụ AI không phản hồi | Quản lý dữ liệu và thuật toán xếp lịch vẫn dùng được |
