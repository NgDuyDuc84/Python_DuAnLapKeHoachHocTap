# Cấu hình chạy và triển khai Nhịp Học

Mốc 11 chỉ chuẩn bị cấu hình theo lựa chọn của người dùng: **chưa triển khai online, chưa tạo dịch vụ có phí**. Chưa có URL nghiệm thu. Bổ sung ngày 15/11/2026: đã chạy 260 test trên SQLite và 260 test trên PostgreSQL 17.12 portable, cùng migration/static/deploy checks và hai worker trên database PostgreSQL tạm. Không cài dịch vụ Windows hoặc đổi SQLite mặc định. Đã xác minh [Actions của commit cfcb3b5](https://github.com/NgDuyDuc84/Python_DuAnLapKeHoachHocTap/actions/runs/43715304135): job SQLite/Windows và PostgreSQL/Linux, Docker build, Compose config đều thành công. Chưa chạy toàn bộ ứng dụng bằng `docker compose up` hoặc kiểm thử URL online.

**Lượt hoàn thiện cuối và điều chỉnh lịch:** 286 test hiện tại qua trên SQLite; hành trình HTTP qua Waitress với database QA riêng và hai worker cũng qua, gồm nhận nhắc trong web. Workflow mới đã thêm chạy Compose và hành trình này trên CI nhưng chưa được xác minh trên GitHub cho mã mới. Máy hiện tại không có Docker; không khẳng định đã chạy Compose. Không cần khóa dịch vụ để thử phần lõi.

## Ba chế độ

| Chế độ | Settings | Database | Máy chủ |
|---|---|---|---|
| Phát triển tại máy | `config.settings` | SQLite mặc định hoặc PostgreSQL khi có DATABASE_URL | `manage.py runserver` |
| Docker kiểm thử tại máy | `config.settings`, DEBUG=false | PostgreSQL 17 riêng trong volume | Waitress + hai worker |
| Production sau này | `config.production` | Bắt buộc PostgreSQL | Waitress sau reverse proxy HTTPS + hai worker |

`config.assets` chỉ dùng đóng gói static có mã băm/nén, không yêu cầu secret production hoặc kết nối database. Không dùng module này để thay cấu hình production.

## Chạy tại Windows

Giữ `.env` hiện tại và SQLite. Từ thư mục dự án:

```powershell
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe manage.py migrate
& .\.venv\Scripts\python.exe manage.py collectstatic --noinput --settings=config.assets
& .\.venv\Scripts\python.exe manage.py test --noinput
& .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Muốn kiểm tra Waitress tại máy thay cho runserver, mở terminal riêng:

```powershell
$env:DJANGO_SETTINGS_MODULE = 'config.settings'
$env:HOST = '127.0.0.1'
$env:PORT = '8001'
& .\.venv\Scripts\python.exe -m deploy.serve
```

Các biến trên chỉ áp dụng cho terminal này. Đóng terminal sau khi thử hoặc gỡ các biến khi quay về quy trình mặc định. Dùng `config.production` chỉ khi đã có PostgreSQL và lớp HTTPS tương ứng.

Worker vẫn chạy riêng, mỗi worker một terminal:

```powershell
& .\.venv\Scripts\python.exe -X utf8 manage.py process_reminders --watch
```

```powershell
& .\.venv\Scripts\python.exe -X utf8 manage.py process_calendar_sync --watch
```

`-X utf8` giúp terminal Windows in thông báo tiếng Việt. Không cần đổi cấu hình mã hóa của Windows. Ctrl+C để dừng tiến trình.

## PostgreSQL qua Docker Compose tại máy

Phần này dành cho máy đã cài Docker Engine/Desktop và Docker Compose. Không tự cài hoặc mở dịch vụ Docker ở mốc 11.

```powershell
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose logs --tail 50 web reminders calendar migrate
```

Compose tạo database `nhiphoc` riêng; chạy migration một lượt sau khi database sẵn sàng, sau đó mới khởi động web và hai worker. Web chỉ mở tại `127.0.0.1:8000`, PostgreSQL không mở cổng ra máy ngoài. Nếu cổng 8000 đang có runserver, dừng runserver trước.

Đây là môi trường kiểm thử HTTP tại máy với mật khẩu minh họa, không dùng để công khai trên Internet. File `.env` thật không được đưa vào image; Compose dùng cấu hình local cố định, email console và không gắn khóa Google/OpenAI. Database mới ban đầu rỗng, không tự nhập SQLite hiện tại.

Tạo tài khoản demo qua web rồi thêm dữ liệu:

```powershell
docker compose exec web python manage.py seed_demo --username demo
```

Chạy test PostgreSQL riêng trong container:

```powershell
docker compose exec web python manage.py test --noinput
```

Dừng bằng `docker compose down`; volume PostgreSQL vẫn giữ dữ liệu. Không dùng tùy chọn xóa volume nếu muốn giữ dữ liệu. Lần cập nhật mã/migration, chạy lại `docker compose up --build -d` và kiểm tra trạng thái dịch vụ migrate trước khi thao tác.

## Kiểm thử hành trình HTTP tại máy

`deploy.smoke` là chương trình Python kiểm tra web đang chạy. Chỉ nhận HTTP loopback (`127.0.0.1`, `localhost`, `::1`); không truy cập URL online. Mặc định chỉ đọc health, trang chủ và CSS:

```powershell
& .\.venv\Scripts\python.exe -m deploy.smoke --base-url http://127.0.0.1:8000
```

Chế độ đầy đủ **tạo hai tài khoản dùng một lần và dữ liệu thử**, không tự xóa chúng. Chỉ dùng với database QA riêng hoặc Compose riêng, không chạy trên database cá nhân đang dùng. Email của hai tài khoản là `@example.test`, email nhắc mặc định tắt; không gọi Google/OpenAI hoặc mở liên kết tài liệu.

Với Docker đã cài, dùng project thử riêng (cổng 8000 phải trống):

```powershell
docker compose -p nhiphoc-test up --build -d
& .\.venv\Scripts\python.exe -m deploy.smoke --allow-test-data --expect-reminders
docker compose -p nhiphoc-test ps
docker compose -p nhiphoc-test logs --tail 50 reminders calendar
docker compose -p nhiphoc-test down
```

Project này dùng volume riêng với Compose mặc định. Lệnh dừng trên giữ volume để xem lại dữ liệu. Không chạy cùng lúc hai project cùng bind cổng 8000. Nếu không dùng Docker, trỏ `--base-url` vào Waitress/runserver có **database thử riêng**, chạy worker nhắc trong cùng môi trường; xem cấu hình Django test trong HD_Test.md. Không cần sửa `.env` cá nhân để chạy test tự động bằng `manage.py test`.

Công cụ đã bổ sung kiểm tra thêm môn/sửa việc trong thanh bên và lịch Sáng/Chiều/Tối. Các bước mong đợi đều in `PASS`: health/static → đăng ký/đăng nhập/Tổng quan → môn/việc/tài liệu/lịch bận/giờ học → xem trước/áp dụng/khóa buổi → Pomodoro/nhật ký/thống kê → trang hỗ trợ/quyền tài khoản thứ hai → nhận nhắc. Công cụ chờ web/database sẵn sàng tối đa 60 giây; `--expect-reminders` chờ thông báo tối đa 90 giây và cần worker đang chạy. Bỏ cờ này nếu chỉ thử web; không coi đó là đã xác minh worker.

CI PostgreSQL/Linux sẽ khởi động Compose trong project `ci-smoke`, chạy công cụ đầy đủ, kiểm tra `db/web/reminders/calendar` còn hoạt động và dọn volume thử của runner khi kết thúc. Bước dọn này chỉ áp dụng dữ liệu CI dùng một lần. CI Windows vẫn kiểm tra SQLite. Cần kiểm tra Actions của commit chứa thay đổi mới sau khi push; kết quả `cfcb3b5` ở trên chỉ xác nhận workflow cũ.

## Production được chuẩn bị ra sao

### Lưu ý khi kiểm thử worker

Test nghiệp vụ dùng Django `TestCase` được bao bởi transaction. Không để `close_old_connections()` của worker đóng kết nối do transaction này quản lý; các test gọi command trong trường hợp đó chỉ giả lập bước dọn kết nối. Hai test `core.test_workers.WorkerConnectionTests` dùng `TransactionTestCase`, thực thi việc đóng/mở lại kết nối thật và xác minh dữ liệu/kết quả còn đúng trên PostgreSQL. Mã worker khi chạy độc lập vẫn giữ nguyên.

Để chạy lại phần hồi quy trong môi trường kiểm thử đã có DATABASE_URL đến PostgreSQL (hoặc qua `docker compose exec web`):

```powershell
python manage.py test notifications integrations core.test_workers --noinput
python manage.py test --noinput
```

Dùng database thử riêng với tài khoản có quyền tạo database test, không trỏ vào database production. Django tạo/xóa database test; không cần đưa mật khẩu hoặc URL database vào log gửi hỗ trợ. Tham khảo [TestCase và TransactionTestCase](https://docs.djangoproject.com/en/5.2/topics/testing/tools/#transactiontestcase).

### Thành phần cấu hình

Các thành phần đã có:

- `Dockerfile`: Python 3.14, cài dependency đã chốt, đóng gói static; chạy bằng user không phải root. Build không đưa secret/database local vào image.
- `deploy/production.env.example`: tên biến và giá trị minh họa để chuẩn bị môi trường riêng. Bản thật nên lưu thành `.env.production` ngoài Git.
- `config.production`: tắt DEBUG, yêu cầu secret đủ dài, hosts cụ thể, SITE_URL là HTTPS origin và PostgreSQL; bật secure cookies, chuyển HTTPS, HSTS và static manifest.
- `deploy.serve`: WSGI bằng Waitress, 4 luồng; HOST/PORT cấu hình qua môi trường. Không dùng runserver để phục vụ production.
- `/health/`: kiểm tra SELECT 1; trả 200 khi database dùng được, 503 khi lỗi, không trả URL/password/lỗi database. Response không cache.
- `.github/workflows/tests.yml`: SQLite trên Windows, PostgreSQL 17 trên Linux; kiểm tra migration, static, `check --deploy`, toàn bộ test và build/validate Docker.

Production cần ít nhất các biến sau được thay bằng giá trị thật, không giữ giá trị minh họa:

File `.env.production` không tự được nạp. Cần truyền biến vào process qua phần Environment của hosting hoặc `docker run --env-file .env.production` khi thử image; không copy file secret vào image. Cổng ứng dụng production chỉ mở cho lớp proxy riêng, không công khai trực tiếp.

```dotenv
DJANGO_SETTINGS_MODULE=config.production
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<secret ngẫu nhiên riêng, ít nhất 50 ký tự>
DJANGO_ALLOWED_HOSTS=<tên miền ứng dụng, không có scheme/path>
SITE_URL=https://<tên miền ứng dụng>
DATABASE_URL=<URL PostgreSQL do nhà cung cấp cấp>
TRUSTED_PROXY=<IP reverse proxy thực sự kết nối vào Waitress>
```

Tạo secret trên máy của bạn:

```powershell
& .\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

PostgreSQL mặc định yêu cầu SSL trong production. URL có thể quy định `sslmode`; chỉ dùng `sslmode=disable` cho mạng local/nội bộ được kiểm soát như Compose/CI, không áp dụng cho kết nối qua Internet.

Lớp HTTPS phải do hosting/reverse proxy cung cấp. Waitress không tự cấp chứng chỉ TLS. Proxy phải ghi lại `X-Forwarded-Proto` theo kết nối thực, và cổng ứng dụng phải ở mạng riêng. Đặt TRUSTED_PROXY đúng IP upstream; chỉ dùng `*` nếu cổng ứng dụng không truy cập trực tiếp từ Internet và mọi upstream đều đáng tin cậy. Waitress xóa header proxy không được tin cậy và đặt scheme; Django không tự tin header do client gửi. Cấu hình sai proxy có thể gây vòng chuyển hướng HTTPS.

Thứ tự vận hành sau khi có hosting, khi người dùng yêu cầu triển khai:

1. Tạo PostgreSQL và môi trường riêng; nhập secret/hosts/SITE_URL/proxy đúng. Không tự sao chép dữ liệu SQLite hoặc khóa local lên host.
2. Build image, cấu hình tiến trình migration một lượt: `python manage.py migrate --noinput`.
3. Kiểm tra cấu hình: `python manage.py check --deploy --fail-level WARNING`. Static đã được đóng gói trong image.
4. Khởi động web bằng `python -m deploy.serve`; mở riêng hai worker bằng các lệnh `process_reminders --watch` và `process_calendar_sync --watch`. Cả ba dùng cùng PostgreSQL, SITE_URL và khóa Google ổn định khi bật đồng bộ.
5. Kiểm tra health, CSS, đăng ký/đăng nhập/đăng xuất, lưu dữ liệu và checklist nghiệm thu trên URL HTTPS thật. Cấu hình cơ chế restart và backup PostgreSQL của nền tảng.
6. Nếu bật SMTP, thay email backend và nhập SMTP thật theo mốc 08. Nếu bật Google, đổi callback sang URL HTTPS thật và khai báo lại trong Google Cloud theo mốc 09. Nếu bật AI, nhập API key phía server và thử theo mốc 10.

Email console, OAuth chưa cấu hình và AI chưa có key không phải bằng chứng các dịch vụ thật đã được kiểm thử. URL online và PostgreSQL thật vẫn là phần cần xác minh sau này.

Nguồn kỹ thuật: [Django deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/), [WhiteNoise](https://whitenoise.readthedocs.io/en/stable/django.html), [Waitress](https://docs.pylonsproject.org/projects/waitress/en/stable/runner.html).
