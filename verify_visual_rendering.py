import os
import sys
import time
import subprocess
import threading
import socket
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, HTTPServer

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR / "frontend"), **kwargs)

    def log_message(self, format, *args):
        pass

def find_edge_path():
    possible_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return None

def main():
    print("=" * 60)
    print("[QC VISUAL VERIFICATION] Khởi chạy Headless Rendering Capture")
    print("=" * 60)

    edge_path = find_edge_path()
    if not edge_path:
        print("[!] Không tìm thấy Edge/Chrome để chụp ảnh giao diện.")
        return

    # Khởi chạy HTTP Server trên port 3009
    port = 3009
    server = HTTPServer(('localhost', port), CustomHTTPRequestHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    url = f"http://localhost:{port}/index.html"
    print(f"[*] Local Server: {url}")
    time.sleep(1)

    artifacts_dir = BASE_DIR / "data" / "qc_screenshots"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    screenshot_file = artifacts_dir / "qc_visual_verify.png"

    # Chụp ảnh Headless Browser
    cmd = [
        edge_path,
        "--headless",
        "--disable-gpu",
        "--window-size=1280,820",
        f"--screenshot={screenshot_file}",
        url
    ]

    print(f"[*] Đang thực thi chụp ảnh màn hình giao diện thực tế: {' '.join(cmd[:4])}...")
    proc = subprocess.run(cmd, capture_output=True, timeout=15)
    
    if screenshot_file.exists():
        print(f"[THÀNH CÔNG QC] Ảnh chụp giao diện thực tế đã tạo: {screenshot_file} ({screenshot_file.stat().st_size} bytes)")
    else:
        print(f"[!] Chụp ảnh không thành công: {proc.stderr.decode('utf-8', errors='ignore')}")

if __name__ == "__main__":
    main()
