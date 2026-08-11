import os
from pathlib import Path
from dotenv import load_dotenv

# Tải cấu hình từ .env
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    PLACES_API_KEY = os.getenv("PLACES_API_KEY", GEMINI_API_KEY).strip()
    PORT = int(os.getenv("PORT", 3000))
    HOST = os.getenv("HOST", "localhost")
    DATA_DIR = BASE_DIR / "data"
    DATA_FILE = DATA_DIR / "places.json"

# Tự động tạo thư mục data nếu chưa tồn tại
Config.DATA_DIR.mkdir(parents=True, exist_ok=True)
