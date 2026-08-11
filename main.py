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
    # 1. Đường dẫn file HTML giao diện trực tiếp trên ổ đĩa (0ms load)
    index_path = str(BASE_DIR / "frontend" / "index.html")

    # 2. Khởi tạo đối tượng API Bridge nhẹ nhất có thể trong < 1ms
    repository = JSONFileRepository()
    ai_service = GeminiAIService()
    service = FoodRecapService(repository=repository, ai_service=ai_service)
    api_bridge = ApiBridge(service=service)

    # 3. MỞ CỬA SỔ ỨNG DỤNG TỨC THÌ (0ms) KHÔNG CHỜ SOCKET HAY HTTP SERVER
    try:
        window = webview.create_window(
            title="Munch Aggregator - Google Maps Food Recap (AI Powered)",
            url=index_path,
            js_api=api_bridge,
            width=1280,
            height=820,
            resizable=True,
            min_size=(900, 600)
        )
        api_bridge.set_window(window)

        # 4. Khởi chạy Server HTTP & Đồng bộ dữ liệu ngầm KHI CỬA SỔ ĐÃ MỞ (Background Task)
        def async_bg_init():
            print("=" * 60)
            print("[MUNCH RECAP] Cửa sổ giao diện Desktop đã mở TỨC THÌ (0ms)!")
            print("=" * 60)
            print(f"[*] Data Storage: JSON Repository ({Config.DATA_FILE})")

            # Khởi chạy HTTP Server ngầm
            try:
                port = find_free_port(Config.PORT)
                server_thread = threading.Thread(target=start_local_server, args=(port,), daemon=True)
                server_thread.start()
                print(f"[*] Local Web Server: Running at http://localhost:{port}/index.html")
            except Exception as e:
                print(f"[Notice HTTP Server]: {e}")

            # Đẩy dữ liệu mới nhất ngầm cho UI
            try:
                places = repository.get_all()
                places_json = json.dumps(places, ensure_ascii=False)
                window.evaluate_js(f"if (typeof window.onBackendDataReady === 'function') window.onBackendDataReady({places_json});")
            except Exception as e:
                print(f"[Async Push Error]: {e}")

        # Đăng ký sự kiện nạp ngầm khi UI xuất hiện
        window.events.shown += lambda: threading.Thread(target=async_bg_init, daemon=True).start()
        
        print("[*] Đang hiển thị cửa sổ giao diện ứng dụng TỨC THÌ...")
        webview.start(debug=False)

    except Exception as e:
        print(f"[Notice PyWebView GUI]: Không thể mở cửa sổ Desktop GUI native ({e}).")
        port = find_free_port(Config.PORT)
        server_thread = threading.Thread(target=start_local_server, args=(port,), daemon=True)
        server_thread.start()
        app_url = f"http://localhost:{port}/index.html"
        print(f"[*] Đang tự động mở ứng dụng trên Trình Duyệt Web mặc định: {app_url}")
        webbrowser.open(app_url)
        try:
            server_thread.join()
        except KeyboardInterrupt:
            print("\n[!] Đã dừng ứng dụng.")


if __name__ == "__main__":
    main()
