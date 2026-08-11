# Project Context: Munch Recap (Google Maps Food Aggregator & AI Analyzer)

## 📌 Tổng Quan Dự Án (Project Overview)
**Munch Recap** (Google Maps Food Recap & Aggregator) là ứng dụng Desktop & Web thông minh hỗ trợ thu thập, phân tích, trích xuất và tổng hợp thông tin chi tiết về các quán ăn từ danh sách đường link Google Maps.

Ứng dụng kết hợp sức mạnh của **Google Gemini AI** để tự động nhận diện tên quán, địa chỉ chi tiết, danh mục ẩm thực, món ăn phải thử, khoảng giá ước tính, không gian & tiện ích, cùng nhận xét của thực khách từ link dán trực tiếp, file văn bản Notepad++ (`.txt`), hoặc file Excel (`.xlsx`, `.csv`).

---

## 🛠️ Stack Công Nghệ & Thư Viện Key (Tech Stack)

- **Ngôn ngữ cốt lõi**: Python 3.12+
- **Desktop Framework**: `pywebview` (Tích hợp giao diện Web HTML5/CSS3/JS native vào cửa sổ Desktop)
- **AI SDK**: `google-genai` / `google-generativeai` (Sử dụng model chính: `gemini-3.6-flash` / `gemini-3.5-flash`)
- **Xử lý File & Dữ liệu**: `pandas`, `openpyxl`, `python-dotenv`, `requests`, `urllib.parse`
- **Giao diện Frontend**: HTML5, CSS3 Custom Tokens (Modern Dark Theme Amber/Emerald), Vanilla JS (0ms Initial Data Push Injection)
- **Kiểm thử**: `unittest` (8/8 unit tests bao phủ toàn bộ logic backend & startup)

---

## 🏗️ Thiết Kế Kiến Trúc (Architecture & Patterns)

### 1. Dependency Injection (DI) & Repository Pattern
- **`IFoodRepository` (Abstract Base Class)**: Định nghĩa hợp đồng thao tác dữ liệu (`get_all`, `save`, `delete`, `clear_all`).
- **`JSONFileRepository`**: Cài đặt lưu dữ liệu local vào file `data/places.json`. Được trang bị `threading.Lock()` đảm bảo an toàn tuyệt đối khi ghi dữ liệu đa luồng (Thread-safe).
- **Mở rộng**: Dễ dàng thay thế bằng `SQLiteRepository` hoặc `SupabaseRepository` mà không làm thay đổi luồng nghiệp vụ.

### 2. Multi-Threading & Rate Limit Control
- **Parallel Processing**: Sử dụng `concurrent.futures.ThreadPoolExecutor` để giải mã và phân tích hàng chục link Google Maps cùng lúc.
- **Smart URL Parser**: Khi gặp giới hạn Rate Limit (`429 RESOURCE_EXHAUSTED`), bộ parser tự động trích xuất Tên Quán và Địa Chỉ thực tế 100% trực tiếp từ tham số `q=` và đường dẫn `place/` trong URL đã unquote.

---

## 📁 Cấu Trúc Thư Mục & Các File Chính (Project Directory Structure)

```
d:\Hobby\link_recap/
├── .env                         # File cấu hình biến môi trường (GEMINI_API_KEY)
├── main.py                      # Entrypoint chính khởi chạy ứng dụng Desktop GUI
├── requirements.txt             # Danh sách thư viện Python cần thiết
├── run_tests.py                 # Runner chạy toàn bộ bộ kiểm thử tự động
├── process_image_links.py       # Script chạy bóc tách hàng loạt link thực tế
├── reprocess_fallback.py        # Script chạy phân tích & cập nhật lại các quán chưa rõ thông tin
├── web_deployment_plan.md       # Kế hoạch chi tiết chuyển ứng dụng lên Cloud Web miễn phí
├── PROJECT_CONTEXT.md           # Tài liệu bối cảnh và tài liệu kỹ thuật toàn bộ dự án
├── backend/                     # Tầng xử lý nghiệp vụ Python
│   ├── config.py                # Nạp cấu hình từ .env
│   ├── repository.py            # IFoodRepository & JSONFileRepository (Thread-safe DI)
│   ├── parsers.py               # Giải mã URL rút gọn Google Maps, đọc TXT & Excel
│   ├── ai_service.py            # GeminiAIService phân tích thông tin quán ăn
│   ├── service.py               # FoodRecapService xử lý logic nghiệp vụ chính
│   └── api.py                   # PyWebView ApiBridge kết nối Python và JavaScript
├── frontend/                    # Tầng giao diện Desktop Application
│   ├── index.html               # Khung HTML5 giao diện
│   ├── styles.css               # Design Token System (Dark Amber Warm & Emerald Green)
│   └── app.js                   # Logic tương tác UI, render thẻ, bộ lọc, modal randomizer
├── data/                        # Thư mục dữ liệu local
│   ├── places.json              # Cơ sở dữ liệu quán ăn local JSON
│   ├── sample_links.txt         # File TXT mẫu chứa link Google Maps
│   └── danh_sach_quan_an_tu_anh.xlsx # Bảng báo cáo Excel tổng hợp
└── tests/                       # Bộ kiểm thử tự động (Unit Tests)
    ├── test_parsers.py          # Test hàm trích xuất và giải mã URL
    ├── test_repository.py       # Test thao tác lưu trữ CRUD
    ├── test_service.py          # Test FoodRecapService và Mock AI
    └── test_startup.py          # Test AST Syntax Check toàn bộ file & nạp module khởi động
```

---

## 🚀 Các Lệnh Khởi Chạy & Kiểm Thử (Command Guide)

### 1. Khởi chạy Ứng dụng Desktop
```bash
python main.py
```

### 2. Chạy Bộ Kiểm Thử Tự Động (Unit Test Suite)
```bash
python run_tests.py
```

### 3. Phân Tích & Cập Nhật Lại Các Quán Thiếu Thông Tin
```bash
python reprocess_fallback.py
```

---

## 🔐 Cấu Hình Biến Môi Trường (`.env`)
```env
# Gemini API Key từ Google AI Studio (https://aistudio.google.com/)
GEMINI_API_KEY=your_actual_gemini_api_key

# Cấu hình ứng dụng
PORT=3000
HOST=localhost
```
