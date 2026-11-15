**Thiết kế ban đầu — Nhịp Học**

Tài liệu gồm thiết kế đã triển khai và các phần dự kiến. Tên Nhịp Học là tên hiển thị tạm thời. Đã triển khai chức năng đến mốc 10 và chuẩn bị giao diện/demo/cấu hình production ở mốc 11. Theo lựa chọn người dùng, chưa triển khai online. Kết nối Google và OpenAI thật cần cấu hình và kiểm thử theo HD_Test.md.

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
   | notifications | Nhắc việc và email | Đã có tùy chọn, hàng đợi, worker, hộp thông báo và lịch sử email |
   | insights | Phân tích thói quen, AI | Đã có tổng hợp Python, xem trước/đồng ý gửi AI, Structured Outputs và lịch sử riêng |
   | integrations | Kết nối lịch bên ngoài | Đã có OAuth, token mã hóa, xem trước và worker đồng bộ một chiều sang Google Calendar |

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
   | ReminderPreference | Đã có: một bản/user, bật web/email, chọn số phút trước deadline/buổi |
   | Reminder | Đã có: owner, việc/buổi, kênh, khóa sự kiện/thời điểm, lịch nhắc, nội dung lịch sử, trạng thái, lần thử, mốc thử lại/claim/gửi/đọc |
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

   Mốc 08 tạo app notifications. Mỗi lượt worker tìm công việc chưa xong và buổi planned đã áp dụng, thời điểm còn ở tương lai nhưng đã tới ngưỡng nhắc của user. Tùy chọn mặc định web bật/email tắt, deadline 1440 phút, buổi 15 phút; GET mặc định không tự tạo preference. Không gửi bù đối tượng đã quá hạn/bắt đầu. Hàng đợi dùng unique(owner, channel, dedup_key), với khóa băm từ loại đối tượng, ID và thời điểm đích; nhắc web/email độc lập, đổi lead không tạo lại sự kiện đã xử lý, đổi thời điểm đích tạo phiên bản mới.

   Worker `process_reminders` mặc định một lượt, `--watch` lặp mỗi 60 giây, `--interval` cho phép 1–3600 giây. Đây là tiến trình Python nền riêng với web, không tạo/gửi trong GET hoặc request lưu form. Bản local dùng database và management command để chạy trực tiếp trên Windows; không thêm broker/dependency. Chế độ watch tiếp tục sau lỗi database tạm khóa; lỗi một lượt trả thất bại để người vận hành chạy lại. Worker kiểm tra dữ liệu sống trước mỗi lần phát nhắc: tài khoản active, kênh bật, owner khớp, công việc chưa xong, buổi chưa ghi nhận/hủy và thời điểm không đổi/chưa qua. Nếu lead mới chưa đến, hoãn next_attempt_at. Bản bỏ qua có thể được kích hoạt lại khi đối tượng/kênh hợp lệ và còn lượt; bản đã gửi không tự gửi lại.

   Mỗi bản được claim bằng UPDATE có điều kiện và token riêng trước gửi, không giữ transaction qua SMTP. Web chuyển sent/delivered_at, chỉ các bản web sent mới xuất hiện ở hộp thông báo. Đánh dấu đọc/tất cả đã đọc bằng POST theo owner. Email tăng attempts, SMTP trả chấp nhận mới ghi sent; không cam kết vào inbox. Bị từ chối rõ ràng hoặc cấu hình/địa chỉ sai thì failed và tối đa 3 lần, giãn ít nhất một phút. Mất kết nối không xác nhận chuyển uncertain, không tự retry. Claim email treo quá 5 phút cũng uncertain; claim web có thể đưa lại pending. Token ngăn worker muộn ghi đè kết quả đã thu hồi. Người dùng kiểm tra hộp thư rồi POST yêu cầu gửi lại failed/uncertain, reset một lượt tối đa 3 lần, vẫn kiểm tra hiệu lực trước gửi. Email SMTP không hỗ trợ cam kết tuyệt đối gửi đúng một lần khi kết nối bị gián đoạn.

   Nội dung email chỉ gồm tên việc, thời điểm, phút còn lại và liên kết nội bộ với SITE_URL cấu hình, kèm đường dẫn thay/tắt nhắc. Email nhận lấy từ tài khoản hiện tại, không lấy recipient/owner từ POST. Lịch sử lưu cả địa chỉ nhận và chế độ thử nghiệm/máy chủ tại lần thử để không nhầm thư console cũ sau khi đổi sang SMTP. Mặc định console backend để kiểm thử local; SMTP và thông tin xác thực qua môi trường. Lỗi lưu vào lịch sử dùng thông báo cố định, không chép exception SMTP có thể chứa thông tin riêng. Foreign key việc/buổi dùng SET_NULL giữ lịch sử; bản chưa phát được bỏ qua sau xóa. Cảnh báo trực tiếp ở planner vẫn độc lập với lịch sử nhắc này. Chưa có push notification/chuông hoặc email báo hết Pomodoro.

   Mốc 09 triển khai `CalendarConnection` (một kết nối hiện tại/user, định danh Google, email, token mã hóa Fernet, phiên kết nối và trạng thái lịch đích), `CalendarEventMapping` (ID buổi nguồn, FK SET_NULL, tuần và ID sự kiện Google), `CalendarSyncJob` (tuần, fingerprint, phiên kết nối, claim và kết quả). Giữ ID nguồn/ánh xạ sau khi xóa buổi hoặc công việc để lần đồng bộ tuần cũ có thể gỡ sự kiện trên Google. Không đưa token vào Django Admin hoặc giao diện.

   OAuth dùng google-auth-oauthlib với state một lần, thời hạn 10 phút, PKCE, redirect URI cố định trong môi trường và offline access. Dùng endpoint userinfo đã xác thực để lấy Google sub/email và kiểm tra scope thực sự được cấp. Chỉ xin `calendar.app.created`, openid và userinfo.email; không xin quyền đọc các lịch cá nhân khác. Token được mã hóa bằng `GOOGLE_TOKEN_ENCRYPTION_KEY` riêng, khóa đặt ngoài Git. Callback lỗi hiển thị thông báo cố định. Ngắt kết nối xóa token, đổi phiên, vô hiệu hóa yêu cầu đang chờ/chạy và cố thu hồi token phía Google. Lịch và sự kiện từ các lần trước được giữ lại. Kết nối lại cùng Google sub giữ lịch đích; đổi Google sub sau ngắt kết nối xóa ánh xạ cũ và dùng lịch đích mới.

   GET xem trước chỉ đọc dữ liệu; chữ ký có owner/kết nối/phiên/tuần/fingerprint, hiệu lực 10 phút. POST xác nhận kiểm tra lại rồi tạo job; mỗi kết nối chỉ có một job pending/running bằng unique constraint. Worker `process_calendar_sync` xử lý một lượt hoặc `--watch --interval 60`; dùng claim có điều kiện, heartbeat và token riêng, thu hồi claim treo quá 5 phút. Không giữ transaction qua HTTP. Kiểm tra tài khoản active, phiên kết nối và fingerprint trước từng thao tác; thay đổi giữa đợt thì dừng và yêu cầu xem trước lại. Mốc local không thêm Redis/Celery.

   Lần đầu có dữ liệu tạo lịch riêng Nhịp Học theo múi giờ Việt Nam. Đồng bộ tất cả buổi chưa hủy của kế hoạch đã áp dụng trong tuần đã chọn, gồm buổi đã học, với tiêu đề/môn/giờ/liên kết web và sự kiện private, tắt nhắc mặc định của Google. Những phần này được ghi lại theo dữ liệu trong web mỗi lần đồng bộ. Không đẩy lịch bận/deadline, không nhập dữ liệu Google về. Buổi khóa/chỉnh tay vẫn được đồng bộ như các buổi khác. Chỉ sự kiện có ánh xạ và dấu nhận diện ứng dụng/ID nguồn đúng mới được sửa/gỡ; sự kiện Google khác được giữ nguyên.

   ID sự kiện UUID dạng base32hex hợp lệ được lưu trước insert. Nếu mất phản hồi, lần chạy lại tìm đúng ID để cập nhật; 409 kiểm tra dấu nhận diện trước khi sửa. Nếu sự kiện đã bị xóa, lưu ID mới trước khi tạo lại. Hủy/xóa nguồn để lại ánh xạ cho đến khi xác nhận gỡ hoặc sự kiện đã vắng mặt. Tạo lịch không có ID do client đặt: phản hồi không xác định hoặc claim treo lúc tạo chuyển sang trạng thái cần kiểm tra; không tự tạo lịch khác. Người dùng kiểm tra Google rồi POST xác nhận tạo lịch đích mới, bỏ ánh xạ cũ nhưng giữ nguyên lịch/sự kiện cũ trên Google.

   Đồng bộ chỉ chạy sau xác nhận, không tự theo mọi chỉnh sửa. Khi lỗi, phần đã ghi lên Google có thể còn đó; cần xem trước và chạy lại để hoàn tất. Request đang ở phía Google lúc ngắt kết nối không thể thu hồi. Mã kiểm thử sử dụng API giả lập; kiểm thử thật phụ thuộc OAuth Client/test user và sự đồng ý cấp quyền của người dùng.

   Mốc 10 thêm `InsightReport`: owner, UUID yêu cầu, thời điểm tạo/kết thúc, model, fingerprint, snapshot dữ liệu/nhãn local, trạng thái, kết quả và mã lỗi an toàn. Unique(owner, request_key) chống gửi lại cùng biểu mẫu; unique owner khi running ngăn nhiều lời gọi đồng thời. Không đăng ký model này vào Django Admin. Mỗi người chỉ xem bản dữ liệu/báo cáo của mình; các thao tác tạo dùng POST và CSRF.

   Snapshot dùng cùng thời điểm tham chiếu: nhật ký 14 ngày gồm hôm nay theo giờ Việt Nam, so sánh 7 ngày trước/7 ngày gần nhất, tổng phút/ngày có ghi nhận/nguồn/môn; tối đa 20 việc chưa xong gần hạn; tùy chọn/quỹ tuần hiện tại; kết quả bổ sung từ calculate_schedule và tối đa 20 cảnh báo build_alerts. Có tổng số và số được đưa vào để công khai phần giới hạn. Phân bổ theo môn giữ tối đa 10 nhãn nhật ký và báo số nhãn còn lại. Không tính nghỉ hoặc phiên hủy; buổi đã qua chưa ghi nhận không tự thành phút học. Không có dữ liệu giờ học hiệu quả hoặc mức hiểu bài.

   Payload OpenAI chỉ gồm mã H/L/V/C/M, số liệu/ngày giờ/tùy chọn và các lý do do Python sinh. Tên việc, tên môn/học kỳ, tài khoản/email, ghi chú, tài liệu, tên lịch bận, khóa API và token Google không nằm trong payload. Bảng mã/nhãn giữ trong snapshot local để hiển thị căn cứ. GET tổng hợp chỉ đọc, không tạo kế hoạch nháp hoặc gọi API. Người dùng mở JSON sẽ gửi, xác nhận bằng checkbox rồi POST bản xem trước có chữ ký (owner, thời điểm, fingerprint, UUID), hiệu lực 10 phút; dữ liệu thay đổi thì yêu cầu xem lại.

   Yêu cầu AI chạy trực tiếp ngoài transaction qua Requests đã có trong dự án, endpoint OpenAI cố định, không theo redirect, timeout kết nối 5 giây/đọc 40 giây, không tự retry. Model mặc định gpt-5.6-terra; Responses API dùng store=false, reasoning low, tối đa 4000 token đầu ra và JSON schema strict, không gắn tool. Bốn nhóm kết quả: tóm tắt, thói quen, phân bổ, cảnh báo. Backend kiểm tra shape, số mục/độ dài, căn cứ phải tồn tại; từ chối kết quả bị từ chối/dở dang/sai cấu trúc/căn cứ lạ và không chép lỗi provider ra web. AI vẫn có thể diễn giải sai dù qua kiểm tra cấu trúc. Không có việc/cảnh báo đầu vào thì không chấp nhận AI tự thêm phần tương ứng.

   Tối đa 5 yêu cầu/user/ngày giờ Việt Nam, giãn ít nhất 60 giây, tính cả lỗi sau khi đã tạo báo cáo. Trùng UUID trả báo cáo hiện tại; đang running chặn yêu cầu khác. Yêu cầu running treo hơn 5 phút được đánh dấu interrupted khi người dùng bắt đầu yêu cầu mới; phản hồi đến muộn không ghi đè trạng thái đó. Không giữ khóa database trong lúc gọi HTTP. Lịch sử hiển thị 10 bản gần nhất, giữ nguyên dữ liệu/nhãn lúc tạo và so fingerprint khi đọc để báo dữ liệu đã đổi. Thiếu key hoặc lỗi API vẫn có phân tích Python được ghi rõ nguồn. Gợi ý chỉ để tham khảo; đổi lịch phải qua kiểm tra/xem trước/áp dụng ở planner, không tự ghi nhật ký/đổi tiến độ. Kiểm thử agent dùng API giả lập; chưa gọi OpenAI thật.

   Mốc 11 giữ `config.settings` cho local SQLite/PostgreSQL tùy DATABASE_URL; URL nếu có phải là PostgreSQL. `config.assets` kế thừa settings chung để build static có mã băm/nén; `config.production` kế thừa assets, bắt buộc secret riêng, hosts cụ thể, SITE_URL HTTPS và PostgreSQL, bật secure cookies/HTTPS/HSTS. WhiteNoise đứng ngay sau SecurityMiddleware. Không tin trực tiếp header proxy trong Django; Waitress chỉ xử lý X-Forwarded-Proto từ TRUSTED_PROXY đã cấu hình và xóa header không đáng tin.

   Máy chủ `deploy.serve` dùng Waitress, HOST/PORT từ môi trường, 4 luồng. Docker build static trước và chạy dưới user không phải root; không sao chép .env/database local vào image. Compose chỉ là môi trường PostgreSQL HTTP tại máy, có migration một lượt trước web/hai worker, web bind loopback và database dùng volume riêng. Production cần reverse proxy HTTPS, cổng ứng dụng private và tiến trình migration riêng, không tự migrate trong mỗi worker. Workflow CI chuẩn bị SQLite/Windows và PostgreSQL/Linux cùng kiểm tra build Docker; chưa chạy CI trong phiên.

   `/health/` kiểm tra SELECT 1, trả 200/503 với trạng thái tối thiểu và không cache. Trang chủ đưa người chưa đăng nhập sang đăng ký, người đã đăng nhập vào lịch; trang lỗi 403/404/500 có thông báo và đường quay về. Lệnh `seed_demo --username` chỉ dùng tài khoản active không phải staff/admin, kiểm tra tài khoản còn trống, tạo dữ liệu một transaction và không đổi mật khẩu/gọi dịch vụ ngoài. Chạy lại khi có môn marker demo thì không ghi thêm. Không có schema mới hoặc tự nhập SQLite sang PostgreSQL. Chi tiết cấu hình/kịch bản ở docs/TRIEN_KHAI.md và docs/NGHIEM_THU.md.

   Bổ sung kiểm tra CI ngày 15/11/2026: PostgreSQL làm lộ việc test command worker đóng kết nối của transaction do TestCase quản lý; SQLite in-memory bỏ qua close nên trước đó không thấy lỗi. Các test nghiệp vụ command chỉ giả lập dọn kết nối trong wrapper TestCase; hai test TransactionTestCase riêng buộc kết nối hết hạn rồi chạy cleanup thật và kiểm tra kết quả. Không sửa cơ chế cleanup của worker độc lập. Toàn bộ 260 test đã qua trên SQLite và PostgreSQL 17.12 portable tại máy; Docker/GitHub Actions và URL online chưa được xác nhận. PostgreSQL thử nghiệm chỉ dùng loopback và database riêng.

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
