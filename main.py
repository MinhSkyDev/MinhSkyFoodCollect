import os
import sys
import json
import threading
import socket
import webbrowser
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, HTTPServer
import webview

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from backend.config import Config
from backend.repository import JSONFileRepository
from backend.ai_service import GeminiAIService
from backend.service import FoodRecapService
from backend.api import ApiBridge


class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    """
    Custom HTTP Request Handler để phục vụ file từ thư mục frontend/
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR / "frontend"), **kwargs)

    def log_message(self, format, *args):
        # Nén bớt log HTTP thừa
        pass


def find_free_port(start_port=3000):
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    return start_port


def start_local_server(port):
    server = HTTPServer(('localhost', port), CustomHTTPRequestHandler)
    server.serve_forever()


def main():
    print("=" * 60)
    print("[MUNCH RECAP] Khởi chạy Google Maps Food Recap App")
    print("=" * 60)

    # 1. Khởi tạo Repository với Dependency Injection
    repository = JSONFileRepository()
    print(f"[*] Data Storage: JSON Repository ({Config.DATA_FILE})")

    # 2. Khởi tạo Gemini AI Service
    ai_service = GeminiAIService()
    if Config.GEMINI_API_KEY:
        print(f"[*] Gemini AI Service: Activated (API Key loaded)")
    else:
        print(f"[!] Gemini AI Service: Warning - GEMINI_API_KEY chưa được cấu hình!")

    # 3. Khởi tạo Core Business Service
    service = FoodRecapService(repository=repository, ai_service=ai_service)

    # 4. Khởi tạo API Bridge
    api_bridge = ApiBridge(service=service)

    # 5. Khởi chạy Local HTTP Server trên Thread ngầm
    port = find_free_port(Config.PORT)
    server_thread = threading.Thread(target=start_local_server, args=(port,), daemon=True)
    server_thread.start()
    
    app_url = f"http://localhost:{port}/index.html"
    print(f"[*] Local Web Server: Running at {app_url}")

    # 6. Thử mở cửa sổ Desktop GUI bằng PyWebView
    try:
        window = webview.create_window(
            title="Munch Aggregator - Google Maps Food Recap (AI Powered)",
            url=app_url,
            js_api=api_bridge,
            width=1280,
            height=820,
            resizable=True,
            min_size=(900, 600)
        )
        api_bridge.set_window(window)

        def on_loaded():
            try:
                places = service.repository.get_all()
                places_json = json.dumps(places, ensure_ascii=False)
                window.evaluate_js(f"if (typeof window.onInitialDataLoaded === 'function') window.onInitialDataLoaded({places_json});")
            except Exception as e:
                print(f"[Error pushing initial data]: {e}")

        window.events.loaded += on_loaded
        print("[*] Đang hiển thị cửa sổ giao diện ứng dụng...")
        webview.start(debug=False)

    except Exception as e:
        print(f"[Notice PyWebView GUI]: Không thể mở cửa sổ Desktop GUI native ({e}).")
        print(f"[*] Đang tự động mở ứng dụng trên Trình Duyệt Web mặc định: {app_url}")
        webbrowser.open(app_url)
        # Giữ process chạy server
        try:
            server_thread.join()
        except KeyboardInterrupt:
            print("\n[!] Đã dừng ứng dụng.")


if __name__ == "__main__":
    main()
