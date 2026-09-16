# AI Translate
AI Translate là ứng dụng dịch nhanh trên máy tính, được xây dựng bằng Python và PyQt6. Ứng dụng cho phép người dùng bôi đen văn bản ở bất kỳ đâu, nhấn phím tắt `Ctrl + Q` để dịch sang tiếng Việt và hiển thị kết quả trong một cửa sổ popup nhỏ.

Ngoài chức năng dịch, ứng dụng còn hỗ trợ lưu từ vựng vào sổ tay cá nhân, xem lại lịch sử từ đã lưu, tìm kiếm từ vựng và quản lý danh sách học tập.

## Chức năng chính

* Dịch nhanh văn bản được bôi đen bằng phím tắt `Ctrl + Q`.
* Hiển thị bản dịch trong popup nổi trên màn hình.
* Hỗ trợ dịch từ, cụm từ và câu tiếng Anh sang tiếng Việt.
* Với từ/cụm từ ngắn, ứng dụng hiển thị thêm nghĩa, phiên âm và ví dụ.
* Lưu từ vựng yêu thích vào sổ tay.
* Xem, tìm kiếm và xóa từ vựng đã lưu.
* Chạy ngầm dưới khay hệ thống.
* Có thể mở lại popup hoặc thoát ứng dụng từ icon khay hệ thống.

## Công nghệ sử dụng

* Python
* PyQt6
* SQLite
* OpenRouter API
* PyAutoGUI
* Pyperclip
* Keyboard
* Requests
* Python-dotenv

## Cấu trúc thư mục

```text
AI_Translate/
│
├── .github/workflows/      # Cấu hình GitHub Actions nếu có
├── assets/                 # Thư mục chứa tài nguyên của ứng dụng
├── history.py              # Giao diện và xử lý sổ tay từ vựng
├── main.py                 # File khởi chạy chính của ứng dụng
├── translation.py          # Xử lý gọi API dịch thuật
├── ui.py                   # Giao diện popup hiển thị bản dịch
├── utils.py                # Hàm tiện ích và xử lý cơ sở dữ liệu
├── requirements.txt        # Danh sách thư viện cần cài đặt
└── .gitignore
```

## Yêu cầu hệ thống

Trước khi chạy dự án, cần cài đặt:

* Python 3.10 trở lên
* pip
* Git
* Kết nối Internet để gọi API dịch thuật

## Cài đặt dự án

### Bước 1: Clone repository

```bash
git clone https://github.com/nvluong-05/AI_Translate.git
```

Di chuyển vào thư mục dự án:

```bash
cd AI_Translate
```

### Bước 2: Tạo môi trường ảo

```bash
python -m venv venv
```

Kích hoạt môi trường ảo trên Windows:

```bash
venv\Scripts\activate
```

Nếu dùng macOS hoặc Linux:

```bash
source venv/bin/activate
```

### Bước 3: Cài đặt thư viện

```bash
pip install -r requirements.txt
```

### Bước 4: Tạo file `.env`

Tạo file `.env` trong thư mục gốc của dự án và thêm API key:

```env
OPENROUTER_API_KEY=your_api_key_here
```

Trong đó `your_api_key_here` là API key lấy từ OpenRouter.

## Chạy ứng dụng

Sau khi cài đặt xong, chạy lệnh:

```bash
python main.py
```

Khi ứng dụng chạy thành công, chương trình sẽ chạy ngầm dưới khay hệ thống.

## Cách sử dụng

1. Bôi đen một đoạn văn bản cần dịch.
2. Nhấn tổ hợp phím `Ctrl + Q`.
3. Ứng dụng sẽ tự động copy văn bản đã chọn.
4. Gửi văn bản đến API dịch thuật.
5. Hiển thị kết quả dịch trong popup.
6. Nhấn biểu tượng ngôi sao để lưu từ/cụm từ vào sổ tay.
7. Mở sổ tay từ vựng để xem lại các từ đã lưu.

## Mô tả hoạt động

Khi người dùng nhấn `Ctrl + Q`, ứng dụng sẽ lấy vị trí chuột hiện tại, sao chép nội dung đang được bôi đen vào clipboard, sau đó gửi nội dung này đến bộ xử lý dịch thuật. Kết quả trả về sẽ được hiển thị trong popup gần vị trí con trỏ chuột.

Nếu nội dung là từ hoặc cụm từ ngắn, hệ thống sẽ yêu cầu API trả về bản dịch theo định dạng gồm nghĩa, phiên âm và ví dụ. Nếu nội dung là câu dài, hệ thống chỉ trả về bản dịch ngắn gọn, sát nghĩa.

Các từ vựng được lưu sẽ được ghi vào cơ sở dữ liệu SQLite để người dùng có thể xem lại sau.

## Một số file quan trọng

### `main.py`

Là file khởi chạy chính của chương trình. File này có nhiệm vụ:

* Khởi tạo ứng dụng PyQt6.
* Lắng nghe phím tắt `Ctrl + Q`.
* Gọi chức năng dịch.
* Hiển thị popup.
* Quản lý icon khay hệ thống.
* Kết nối chức năng lưu từ vựng.

### `translation.py`

Chứa lớp xử lý dịch thuật. File này gửi request đến OpenRouter API và nhận kết quả dịch từ mô hình AI.

### `ui.py`

Xây dựng giao diện popup hiển thị bản dịch. Popup có các thành phần như:

* Nội dung bản dịch.
* Phiên âm.
* Ví dụ.
* Văn bản gốc.
* Nút lưu từ vựng.
* Nút mở sổ tay từ vựng.
* Nút đóng popup.

### `history.py`

Quản lý giao diện sổ tay từ vựng. Người dùng có thể:

* Xem danh sách từ đã lưu.
* Tìm kiếm từ hoặc nghĩa.
* Lọc theo tag.
* Xóa từ khỏi sổ tay.

### `utils.py`

Chứa các hàm tiện ích, đặc biệt là xử lý cơ sở dữ liệu SQLite để lưu và truy xuất từ vựng.

## Lưu ý khi sử dụng

* Ứng dụng cần quyền đọc bàn phím để nhận phím tắt `Ctrl + Q`.
* Một số hệ điều hành có thể yêu cầu chạy terminal bằng quyền Administrator.
* Cần có API key hợp lệ để chức năng dịch hoạt động.
* Nếu không bôi đen văn bản, ứng dụng sẽ không hiển thị popup dịch.
* Ứng dụng cần kết nối Internet để gửi yêu cầu dịch thuật.

## Hướng phát triển

Trong tương lai, dự án có thể được mở rộng thêm các chức năng:

* Hỗ trợ nhiều ngôn ngữ đầu vào và đầu ra.
* Cho phép người dùng tự chọn phím tắt.
* Thêm chức năng xuất sổ tay từ vựng ra file Excel hoặc PDF.
* Đồng bộ dữ liệu từ vựng lên cloud.
* Thêm chế độ ôn tập từ vựng.
* Cải thiện giao diện người dùng.
* Đóng gói thành file `.exe` để dễ cài đặt trên Windows.

## Tác giả

Dự án được phát triển nhằm hỗ trợ việc dịch nhanh và học từ vựng tiếng Anh hiệu quả hơn trong quá trình học tập và làm việc.

## License

Dự án hiện chưa công bố giấy phép sử dụng. Người dùng cần liên hệ tác giả nếu muốn sử dụng hoặc phát triển lại cho mục đích khác.
