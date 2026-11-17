# Font cục bộ

Lora (variable 400–700) và Inter (variable 100–900), kiểu đứng, lấy nguyên file WOFF2 do Google Fonts phân phối; không sửa nội dung font. Mỗi họ gồm ba subset `latin`, `latin-ext`, `vietnamese`. Các `@font-face` trong `fonts.css` giữ `unicode-range` và `font-display: swap`, chỉ dùng URL tương đối trong thư mục này. Hai subset Latin được preload trong `base.html`; subset tiếng Việt/mở rộng tải theo ký tự sử dụng.

Nguồn gốc và giấy phép:

- [Lora trong kho Google Fonts](https://github.com/google/fonts/tree/main/ofl/lora), giấy phép `Lora-OFL.txt` (giữ Reserved Font Name).
- [Inter trong kho Google Fonts](https://github.com/google/fonts/tree/main/ofl/inter), giấy phép `Inter-OFL.txt`.
- `sources.json` ghi URL tải gốc, kích thước và SHA-256 của từng file. Các URL nguồn chỉ phục vụ truy xuất nguồn gốc; ứng dụng không gọi CDN.

Tổng sáu file WOFF2: 210.444 byte. Giữ đủ cả ba subset để hỗ trợ tiếng Việt và Latin mở rộng.
