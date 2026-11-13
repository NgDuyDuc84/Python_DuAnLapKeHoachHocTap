**Thiết kế ban đầu — Nhịp Học**

Tài liệu gồm thiết kế đã triển khai và các phần dự kiến. Tên Nhịp Học là tên hiển thị tạm thời. Đã hoàn thành các mốc 01–06 (nền Django, tài khoản, học tập, lịch và xếp lịch), cùng Pomodoro/nhật ký/thống kê ở mốc 07.

1. **Phân chia trách nhiệm**

   Python xử lý tài khoản, kiểm tra quyền, lưu dữ liệu, thời gian/lịch lặp, thuật toán lập kế hoạch, thống kê, cảnh báo, thông báo và gọi API. Django Templates dựng trang từ dữ liệu máy chủ. JavaScript chỉ cần cho các tương tác như kéo thả lịch và đồng hồ Pomodoro.

   Trong từng module: `models.py` biểu diễn dữ liệu; `forms.py` kiểm tra biểu mẫu; `views.py` nhận request; nghiệp vụ phức tạp đặt ở `services/`. Không chuyển thuật toán xếp lịch sang trình duyệt.

2. **Cấu trúc dự kiến**

   | Module | Vai trò | Trạng thái hiện tại |
   |---|---|---|
   | config | Settings, URL, WSGI/ASGI | Đã tạo cho local |
   | core | Trang chủ và giao diện chung | Đã tạo |
   | accounts | Luồng tài khoản, quyền và hồ sơ | Đã có đăng ký, đăng nhập/đăng xuất, đổi mật khẩu và thông tin tài khoản riêng |
   | studies | Môn, công việc, tài liệu | Đã có model, migration, CRUD, tìm kiếm/lọc và quyền sở hữu |
   | planner | Lịch bận, tùy chọn, kế hoạch, thuật toán | Đã có lịch bận, tùy chọn, lịch tuần, thuật toán sinh bản xem trước và áp dụng |
   | focus | Pomodoro, nhật ký và thống kê thời gian học | Đã có đồng hồ bền qua tải lại, thao tác trạng thái, nhật ký và thống kê bằng Python |
   | notifications | Nhắc việc và email | Chưa triển khai |
   | insights | Phân tích thói quen, AI | Chưa triển khai; thống kê thời gian cơ bản hiện đặt ở focus |
   | integrations | Kết nối lịch bên ngoài | Chưa triển khai |

3. **Dữ liệu nghiệp vụ dự kiến**

   | Đối tượng | Nội dung và quan hệ |
   |---|---|
   | User | Dùng User mặc định Django; username, email, mật khẩu băm, trạng thái, quyền staff/superuser |
   | StudyPreference | Một bản ghi/user; ngày được học, một khung giờ chung, phút tối đa/ngày, độ dài buổi, phút nghỉ |
   | Subject | Thuộc user; tên môn, màu, học kỳ, trạng thái lưu trữ |
   | Task | Thuộc user, có thể gắn môn; deadline, ưu tiên, phút ước tính/còn lại, cho phép chia nhỏ, trạng thái |
   | BusyEvent | Thuộc user; thời điểm bắt đầu/kết thúc của lần đầu, cờ lặp hằng tuần, ngày dừng lặp tùy chọn |
   | StudyPlan | Đã có: owner, thứ Hai đầu tuần, ngày tạo/áp dụng, dấu vân tay đầu vào và báo cáo phân bổ |
   | StudySession | Đã có: owner, công việc, kế hoạch, bắt đầu/kết thúc, trạng thái planned/done/cancelled, is_locked và is_manual |
   | StudyLog | Đã có: owner, công việc tùy chọn, tên việc/nhãn môn lịch sử, ngày học, phút, ghi chú, nguồn manual/pomodoro, liên kết một-một tới FocusSession nếu có |
   | FocusSession | Đã có: owner, việc tùy chọn, tên/nhãn môn lịch sử, phase work/break, trạng thái, thời lượng/giây tích lũy và mốc bắt đầu/tiếp tục/kết thúc; liên kết một-một tới phiên học trước cho giờ nghỉ |
   | Material | Thuộc user; tên, URL, mô tả, môn/công việc liên quan |
   | Reminder | Đối tượng, kênh, thời điểm, phiên bản và trạng thái gửi |
   | CalendarConnection | User, lịch đích, thông tin cấp quyền được bảo vệ và trạng thái |
   | CalendarEventMapping | Buổi học, ID sự kiện bên ngoài và trạng thái đồng bộ |

   Mỗi quan hệ dữ liệu phải cùng chủ sở hữu. Một công việc có thể có nhiều buổi học. Thời gian đã học và trạng thái hoàn thành công việc được lưu riêng; hết thời gian không tự động chứng minh đã làm xong việc.

   Ở mốc 02, tài khoản mới được tạo qua `UserCreationForm` mở rộng với email bắt buộc. Đăng nhập bằng username; email phục vụ thông tin hồ sơ, chưa có xác minh hoặc khôi phục mật khẩu qua email. Username là định danh duy nhất; không áp dụng ràng buộc email duy nhất ở mốc này.

   Trang thông tin lấy user trực tiếp từ phiên đăng nhập, không nhận ID người khác để xem. Đăng xuất dùng POST có CSRF. `is_staff` cho phép vào khu vực Admin; quyền xem/sửa người dùng được Django kiểm tra riêng. Tài khoản tạo bằng `createsuperuser` có đầy đủ quyền quản trị. Form đăng ký không cho người dùng tự đặt `is_staff`, `is_superuser` hoặc nhóm quyền.

   Mốc 03 đã triển khai `Subject`, `Task`, `Material`; các đối tượng học tập khác trong bảng vẫn là dự kiến. Mọi danh sách, trang sửa/xóa và lựa chọn liên kết đều giới hạn theo user đang đăng nhập. Không nhận owner từ POST. Model validation kiểm tra quyền sở hữu liên kết; form chỉ cho chọn môn/công việc của mình.

   Thời lượng ước tính phải lớn hơn 0. Công việc mới lấy thời lượng còn lại bằng ước tính; chọn Hoàn thành đưa còn lại về 0. Công việc chưa hoàn thành phải còn thời lượng dương, có thể lớn hơn ước tính nếu phát sinh thêm. Database có constraint cho thời lượng, mức ưu tiên và trạng thái/thời lượng còn lại. Cho phép ghi công việc đã quá hạn; bộ lọc Quá hạn loại công việc đã hoàn thành.

   Lưu trữ môn chỉ ẩn khỏi danh sách Đang học, không gỡ các liên kết. Xóa môn đặt liên kết môn của công việc/tài liệu về rỗng; xóa công việc gỡ liên kết công việc của tài liệu. Không xóa dây chuyền các dữ liệu đó. Xóa tài liệu chỉ xóa liên kết trong ứng dụng, không tác động tệp ở website gốc.

   Tài liệu ở mốc này là URL HTTP/HTTPS; có thể độc lập hoặc gắn các môn/công việc mình sở hữu. Không yêu cầu môn gắn trực tiếp trên tài liệu phải giống môn của công việc được gắn, để hỗ trợ tài liệu dùng chung. Không tải tệp lên hoặc đọc nội dung đường dẫn từ máy chủ.

   Mốc 04 thêm `StudyPreference` và `BusyEvent`. `StudyPreference.study_days` là danh sách số nguyên 0–6 (thứ Hai–Chủ nhật) trong JSONField, được kiểm tra không trùng hoặc ngoài phạm vi. Cho phép bỏ chọn toàn bộ ngày. Một khung giờ trong cùng ngày áp dụng cho các ngày đã chọn; múi giờ dùng cấu hình chung `Asia/Ho_Chi_Minh`. Độ dài buổi phải nằm trong khung giờ và không vượt giới hạn phút/ngày. Đọc tùy chọn mặc định không tạo bản ghi; chỉ ghi khi người dùng lưu.

   Lịch lặp giữ thứ và giờ địa phương của lần đầu, không sinh trước ngày bắt đầu. Ngày dừng tính theo ngày bắt đầu mỗi lần, bao gồm ngày dừng; một ca qua đêm có thể kết thúc sau ngày đó. Mỗi lần lặp ngắn hơn 7 ngày. Một lịch chỉ lặp ở một thứ; bận nhiều thứ thì nhập các lịch riêng. Sửa/xóa lịch lặp tác động cả chuỗi; chưa có ngoại lệ cho từng lần.

   `planner/services/availability.py` xử lý mở rộng lịch lặp và trừ hợp các khoảng bận theo quy ước [bắt đầu, kết thúc). Ca qua đêm/nhiều ngày được cắt theo từng ngày để hiển thị. Khoảng trống nằm trong ngày/giờ được học và từ hiện tại trở đi, làm tròn lên phút kế tiếp nếu đang có giây lẻ. Quỹ ngày là giá trị nhỏ hơn giữa tổng phút trống và giới hạn phút/ngày. Đây là giới hạn trên, chưa bảo đảm xếp được số buổi mong muốn hoặc đã chừa thời gian nghỉ giữa các buổi.

   Lịch tuần hiển thị các mốc deadline của user trong tuần (kể cả việc hoàn thành), nhưng không coi deadline là khoảng bận. Các ngày đã qua không có khoảng trống tương lai. Các buổi tự học, trạng thái thực hiện và thuật toán phân bổ chưa triển khai ở mốc 04.

   Mốc 05 thêm `StudyPlan`, `StudySession` và `planner/services/scheduling.py`. Tạo bản xem trước qua POST; các GET chỉ đọc. Thuật toán xét công việc chưa hoàn thành theo deadline, ưu tiên giảm dần khi cùng hạn, rồi ID để giữ tính xác định. Chỉ xếp trong tuần được chọn, từ hiện tại làm tròn lên phút, trước hoặc bằng deadline. Buổi chia nhỏ có thể ngắn hơn độ dài mong muốn; công việc không chia buổi cần toàn phần còn thiếu liên tục và không vượt quỹ ngày.

   Các buổi của kế hoạch đã áp dụng chặn thời gian, chừa khoảng nghỉ ở cả hai phía (kể cả qua ngày/tuần) và tiêu quỹ ngày bằng phút học, không tính phút nghỉ vào phút học. Phút của buổi tương lai dành cho công việc ở mọi tuần được trừ khỏi nhu cầu, phần đã qua không tự tính đã học xong. Buổi đang diễn ra chỉ được tính phần nguyên phút từ hiện tại làm tròn lên. Công việc không chia nhưng đã có một phần lịch sẽ được yêu cầu rà soát thay vì thêm mảnh mới. Kế hoạch bổ sung giữ mọi buổi đã áp dụng.

   Báo cáo lưu ảnh chụp tên/deadline/thời lượng và các phút đã có lịch, bố trí mới, chưa bố trí khi tạo. Danh sách buổi hiển thị thông tin công việc hiện tại. Áp dụng qua POST có CSRF và kiểm tra owner; transaction so khớp dấu vân tay đầu vào và kết quả tính lại theo thời gian hiện tại. Từ chối phương án cũ, không áp dụng một phần. Gửi lại cùng bản đã áp dụng không tạo thêm buổi. Lịch tuần chỉ lấy buổi thuộc kế hoạch đã áp dụng. Không giảm `Task.remaining_minutes` khi xếp lịch.

   Xóa công việc xóa các buổi thuộc công việc, giữ báo cáo kế hoạch và tài liệu; giao diện xác nhận nêu rõ tác động. Mốc 05 chưa có chỉnh/khóa/hủy từng buổi hoặc tự xếp lại khi sửa lịch bận/giờ học/deadline sau áp dụng. Các buổi cũ tiếp tục giữ chỗ dù công việc được đánh dấu xong, chờ cơ chế cập nhật/xếp lại ở mốc 06. Đây là các đặt chỗ dự kiến, chưa phải nhật ký học thực tế.

   Mốc 06 thêm `StudyPlan.mode` (add/replace), `replacement_ids` và trạng thái/cờ của buổi. Chế độ add giữ mọi buổi; replace chọn đúng buổi planned, tự động, không khóa, bắt đầu sau hiện tại và thuộc tuần được chọn. Phút của các buổi được thay không tính vào nhu cầu đã có lịch/quỹ bị chiếm trong phương án mới, nhưng vẫn đưa vào dấu vân tay để phát hiện thay đổi sau xem trước. Áp dụng so khớp cả danh sách buổi cần thay rồi chuyển chúng sang cancelled trong cùng transaction với việc kích hoạt buổi mới. Cho phép áp dụng bản chỉ hủy buổi cũ khi việc đã xong; không cần tạo buổi rỗng giả. Lịch tuần bỏ cancelled; chi tiết kế hoạch giữ chúng để xem lại.

   `planner/services/sessions.py` xử lý chỉnh giờ, khóa/mở khóa và ghi nhận theo owner trong transaction. Chỉ chỉnh buổi planned chưa bắt đầu, không khóa, sang giờ tròn phút trong cùng tuần. Kiểm tra model và lịch bận/lặp, khung học, nghỉ, quỹ ngày, tổng phút đã dành cho công việc và quy tắc không chia buổi. Chỉnh thành công đặt is_manual=True; mở khóa không gỡ cờ chỉnh tay. Muốn thay một buổi chỉnh tay bằng tự động thì hủy buổi rồi tạo/xếp lại. Khóa có nghĩa giữ khi tự xếp lại; phải mở khóa trước khi chỉnh/hủy. Vẫn có thể ghi nhận Đã học cho buổi khóa đã bắt đầu.

   Ghi nhận Đã học được phép từ thời điểm bắt đầu, không tự trừ độ dài buổi. Người dùng nhập số phút công việc thực tế còn cần: 0 đưa Task sang done, số dương đưa sang in_progress. Hủy/bỏ qua không đổi tiến độ, giữ bản ghi và giải phóng lịch/quỹ. Buổi đã ghi nhận hoặc hủy không ghi nhận lại; sửa ước lượng còn lại qua trang tiến độ công việc. Buổi done vẫn giữ thời gian trên lịch và tiêu quỹ ngày, nhưng không còn được tính là phút tương lai sẽ học cho công việc. Nếu kết thúc sớm, đặt chỗ vẫn giữ đến giờ kết thúc cũ; chưa có đo thời gian thực tế.

   `planner/services/alerts.py` dựng cảnh báo từ dữ liệu hiện tại: mọi công việc quá hạn, công việc đến hạn trong 7 ngày thiếu phút tương lai, buổi planned sắp diễn ra trong 7 ngày trùng lịch bận/buổi khác, thiếu nghỉ, sai khung/ngày, quá quỹ/ngày, vượt deadline hoặc vượt thời lượng còn lại. Hiện tối đa 20 buổi đã kết thúc chưa ghi nhận gần nhất, kèm tổng số; các buổi cũ hơn vẫn xem được từ lịch và kế hoạch. Chưa gửi email và chưa kết luận thiếu lịch là không thể xếp đủ. Các buổi giữ nguyên nhưng đã sai ràng buộc được cảnh báo để người dùng xử lý trực tiếp; xếp lại không tự thay buổi khóa/chỉnh tay/đã bắt đầu/đã học.

   Mốc 07 tạo app `focus`. `FocusSession` có unique constraint có điều kiện: tối đa một phiên running/paused mỗi owner, kể cả giờ nghỉ. Server tính giây tích lũy và phần từ resumed_at tới hiện tại, chặn số âm và giới hạn duration_seconds (1500 học/300 nghỉ). Pause lưu giây đã chạy rồi bỏ resumed_at; resume giữ phần tích lũy và đặt lại mốc chạy. GET và API đọc trạng thái không ghi database, không tự kết thúc khi hết giờ. JavaScript dùng thời gian tương đối để vẽ đồng hồ, đồng bộ bằng GET mỗi 15 giây/khi quay lại trang. Hết giờ hiển thị lời nhắc xác nhận, chưa gửi thông báo ngoài trang.

   Start có UUID theo biểu mẫu; lặp cùng yêu cầu trả lại phiên cũ. Các thao tác trạng thái dùng POST/CSRF, lọc owner và transaction. Finish tạo một StudyLog duy nhất cho phiên work có ít nhất 60 giây, phút là phần nguyên của giây đã học/60; không cộng pause hoặc break. Finish lặp lại không ghi thêm, kể cả log cũ đã bị xóa. Cancel không tạo log. Mỗi phiên work finished có tối đa một phiên nghỉ liên kết; bấm bắt đầu nghỉ lại mở đúng phiên đó, không tạo chuỗi nghỉ trùng. Trạng thái và constraint được kiểm thử trong database; lỗi SQLite bận khi thao tác đồng thời được thông báo để tải lại/thử lại.

   StudyLog nhập tay có ngày không vượt hiện tại, 1–1440 phút/bản và ghi chú tối đa 1000 ký tự; UUID theo biểu mẫu tránh ghi lặp cùng lần gửi. Nhật ký nhập tay được sửa ngày/phút/việc/ghi chú; nhật ký Pomodoro chỉ sửa ghi chú để giữ số đo đồng hồ. Có trang xác nhận xóa qua POST: xóa làm giảm thống kê, không tự đổi tiến độ hoặc lịch. Foreign key Task dùng SET_NULL cho FocusSession/StudyLog; tên việc và nhãn môn được chụp khi bắt đầu Pomodoro hoặc nhập/sửa nhật ký tay để giữ lịch sử sau đổi/xóa dữ liệu gốc. Nhãn môn không chứa trạng thái lưu trữ.

   Thời gian nhật ký độc lập với ước lượng công việc: không tự giảm Task.remaining_minutes hoặc tự ghi nhận StudySession. Người dùng cập nhật tiến độ và trạng thái buổi bằng mốc 06. Pomodoro gắn công việc, chưa gắn trực tiếp từng buổi lịch. Thống kê chỉ tổng hợp các StudyLog còn lưu, không cộng FocusSession riêng để tránh tính hai lần. Mặc định 7 ngày, chọn được 1–366 ngày; dữ liệu theo ngày có cả ngày 0 phút, theo nhãn môn và nguồn; trung bình chia cho toàn bộ số ngày đã chọn. Pomodoro gán toàn bộ phút vào ngày bắt đầu phiên ở Asia/Ho_Chi_Minh, chưa chia phiên qua nửa đêm. Đổi nhãn môn rồi ghi thêm có thể tạo nhóm lịch sử khác.

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
