# Kế Hoạch Triển Khai Web (Web Deployment & Architecture Plan)

Tài liệu này đóng gói toàn bộ lộ trình kỹ thuật và thiết kế kiến trúc để đưa ứng dụng **Google Maps Food Recap & Aggregator** từ dạng **Desktop App** lên nền tảng **Web Application hoàn toàn miễn phí**.

---

## 🎯 Mục Tiêu Triển Khai Web
- Truy cập ứng dụng qua URL trên mọi thiết bị (Máy tính, Máy tính bảng, Điện thoại di động iOS/Android).
- Tự động hóa quá trình deploy (CI/CD) thông qua GitHub Repository.
- Sử dụng các nền tảng **Cloud Miễn Phí 100%** cho cả Web Server, Frontend và Database.

---

## 📊 Phân Tích & Lựa Chọn Nền Tảng Cloud Miễn Phí

| Nền Tảng | Thành Phần | Tính Năng Miễn Phí | Đánh Giá & Đề Xuất |
|---|---|---|---|
| **Render.com** | Fullstack Web Service (FastAPI / Flask) | 512MB RAM, HTTPS miễn phí, Tự động deploy từ GitHub | ⭐ **Đề xuất làm Backend API Server** |
| **Vercel** | Frontend (HTML5 / React) | Bandwidth 100GB/tháng, CDN toàn cầu tốc độ cực nhanh | ⭐ **Đề xuất làm Frontend Web Hosting** |
| **Supabase** | Cloud Database (PostgreSQL) | 500MB Data, Realtime Subscription, REST API | ⭐ **Đề xuất làm Cloud Database** |
| **Hugging Face Spaces** | Python App Hosting | 16GB RAM CPU Instance, Chạy 24/7 không bị sleep | 💡 **Phương án dự phòng chạy 24/7** |

---

## 🏗️ Kiến Trúc Chuyển Đổi (Migration Architecture)

### 1. Mô hình Hiện tại (Desktop Local)
```
[HTML5 / CSS3 / JS UI] <---> [PyWebView Bridge] <---> [FoodRecapService] <---> [JSONFileRepository (places.json)]
```

### 2. Mô hình Web Cloud (Target Web Architecture)
```
[Client Browser (Mobile/PC)] <--- HTTP / REST API ---> [FastAPI Web Server (Render/Vercel)]
                                                             |
                                                             +---> [Gemini AI Service]
                                                             +---> [SupabaseRepository (PostgreSQL Cloud)]
```

---

## 🛠️ Lộ Trình Triển Khai 4 Bước (Execution Roadmap)

### Bước 1: Khởi Tạo Cloud Database (Supabase PostgreSQL)
- Đăng ký tài khoản miễn phí tại [supabase.com](https://supabase.com/).
- Tạo bảng `places` với schema:
  - `id` (UUID, Primary Key)
  - `name` (TEXT)
  - `category` (TEXT)
  - `address` (TEXT)
  - `recommended_dishes` (JSONB / ARRAY)
  - `price_range` (TEXT)
  - `vibe` (TEXT)
  - `summary` (TEXT)
  - `rating_ai` (FLOAT)
  - `highlights` (JSONB / ARRAY)
  - `original_url` (TEXT)
  - `expanded_url` (TEXT)
  - `created_at` (TIMESTAMP)

### Bước 2: Viết Lớp `SupabaseRepository` (Dependency Injection)
Tận dụng kiến trúc DI đã có, tạo thêm file `backend/supabase_repository.py`:
```python
from backend.repository import IFoodRepository
from supabase import create_client

class SupabaseRepository(IFoodRepository):
    def __init__(self, url: str, key: str):
        self.client = create_client(url, key)
    
    def get_all(self):
        res = self.client.table("places").select("*").order("created_at", desc=True).execute()
        return res.data
        
    def save(self, place_data):
        res = self.client.table("places").upsert(place_data).execute()
        return res.data[0]
```

### Bước 3: Chuyển Đổi Backend Sang FastAPI Web Routes
Tạo file `server.py` thay thế cho `main.py` Desktop:
- `GET /api/places`: Lấy danh sách quán ăn.
- `POST /api/process-text`: Phân tích danh sách link dán trực tiếp.
- `POST /api/process-file`: Đọc file Excel / TXT upload.
- `POST /api/reanalyze-fallbacks`: Phân tích lại các quán bị thiếu thông tin.
- `GET /api/export-excel`: Tải file Excel tổng hợp.

### Bước 4: Deploy Lên Render.com / Vercel
- Đưa dự án lên GitHub Repository.
- Kết nối Render.com với GitHub, thiết lập:
  - **Build Command**: `pip install -r requirements.txt`
  - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`
  - **Environment Variables**: Thêm `GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`.

---

## 🧪 Kế Hoạch Kiểm Thử Sau Khi Deploy Web
1. Truy cập URL ứng dụng trên trình duyệt điện thoại iPhone / Android.
2. Dán thử 3 - 5 link Google Maps từ điện thoại và kiểm tra tốc độ phân tích AI.
3. Kiểm tra tính đồng bộ dữ liệu giữa máy tính và điện thoại qua Supabase Cloud DB.
