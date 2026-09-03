"""
Verification Script for Static Web PoC
======================================
Kiểm tra tính toàn vẹn của Frontend Web Tĩnh và khả năng phục vụ độc lập (0 VNĐ Server).
"""

import sys
import json
import time
import socket
import threading
import urllib.request
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, HTTPServer

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def run_verification():
    print("=" * 70)
    print("[VERIFY] BẮT ĐẦU KIỂM CHỨNG POc STATIC WEB (0 VNĐ)")
    print("=" * 70)

    # 1. Kiểm tra file frontend/places.json
    places_file = BASE_DIR / "frontend" / "places.json"
    assert places_file.exists(), "File frontend/places.json không tồn tại!"
    with open(places_file, "r", encoding="utf-8") as f:
        places = json.load(f)
    assert isinstance(places, list) and len(places) > 0, "Dữ liệu places.json rỗng hoặc không đúng định dạng!"
    print(f"✅ 1. frontend/places.json hợp lệ: {len(places)} quán ăn đã được đóng gói sẵn.")

    # 2. Kiểm tra file frontend/index.html
    html_file = BASE_DIR / "frontend" / "index.html"
    assert html_file.exists(), "File frontend/index.html không tồn tại!"
    html_content = html_file.read_text(encoding="utf-8")
    assert "xlsx.full.min.js" in html_content, "Thiếu SheetJS CDN trong index.html!"
    assert "appModeBadge" in html_content, "Thiếu appModeBadge trong index.html!"
    assert "fileInputWeb" in html_content, "Thiếu fileInputWeb trong index.html!"
    print("✅ 2. frontend/index.html hợp lệ: Đã tích hợp SheetJS và các thành phần Web Tĩnh.")

    # 3. Kiểm tra file frontend/app.js
    js_file = BASE_DIR / "frontend" / "app.js"
    assert js_file.exists(), "File frontend/app.js không tồn tại!"
    js_content = js_file.read_text(encoding="utf-8")
    assert "loadStaticPlaces" in js_content, "Thiếu hàm loadStaticPlaces trong app.js!"
    assert "exportExcelClientSide" in js_content, "Thiếu hàm exportExcelClientSide trong app.js!"
    assert "isPyWebView" in js_content, "Thiếu hàm isPyWebView nhận diện Dual-Mode trong app.js!"
    print("✅ 3. frontend/app.js hợp lệ: Đã cài đặt Dual-Mode và xuất Excel 100% Client-side.")

    # 4. Kiểm tra khả năng phục vụ qua HTTP Server độc lập (Giả lập Vercel/GitHub Pages)
    port = find_free_port()
    class QuietHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(BASE_DIR / "frontend"), **kwargs)
        def log_message(self, format, *args):
            pass

    server = HTTPServer(('localhost', port), QuietHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    time.sleep(0.3)
    try:
        # Test GET /index.html
        url_html = f"http://localhost:{port}/index.html"
        with urllib.request.urlopen(url_html, timeout=5) as resp:
            assert resp.status == 200
            content = resp.read().decode('utf-8')
            assert "<title>Munch Aggregator" in content
        print(f"✅ 4. HTTP GET /index.html thành công (Status 200 OK).")

        # Test GET /places.json
        url_json = f"http://localhost:{port}/places.json"
        with urllib.request.urlopen(url_json, timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode('utf-8'))
            assert len(data) == len(places)
        print(f"✅ 5. HTTP GET /places.json thành công (Status 200 OK, tải {len(data)} quán ăn).")

    finally:
        server.shutdown()

    print("=" * 70)
    print("🎉 TOÀN BỘ KIỂM CHỨNG POc STATIC WEB THÀNH CÔNG 100%!")
    print("=" * 70)


if __name__ == "__main__":
    run_verification()
