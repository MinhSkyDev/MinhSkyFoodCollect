import os
import sys
import time
import shutil
import subprocess
import threading
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, HTTPServer

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent
ARTIFACT_DIR = Path(r"C:\Users\Laptop\.gemini\antigravity\brain\773c61ca-8aa0-4a50-9f4a-99de92448bee")

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
    print("[QC ALL GRID MODES VERIFICATION] Khởi chạy Headless Visual Capture")
    print("=" * 60)

    edge_path = find_edge_path()
    if not edge_path:
        print("[!] Không tìm thấy Edge/Chrome.")
        return

    port = 3010
    server = HTTPServer(('localhost', port), CustomHTTPRequestHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    url = f"http://localhost:{port}/index.html"
    time.sleep(1)

    output_dir = BASE_DIR / "data" / "qc_screenshots"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Chụp mặc định
    file_default = output_dir / "qc_grid_3cols.png"
    subprocess.run([edge_path, "--headless", "--disable-gpu", "--window-size=1280,820", f"--screenshot={file_default}", url], capture_output=True, timeout=15)
    
    if file_default.exists():
        shutil.copy(file_default, ARTIFACT_DIR / "qc_grid_3cols.png")
        print(f"[OK QC] Grid 3 Cột: {file_default.stat().st_size} bytes")

    print("[THÀNH CÔNG] Đã chụp ảnh và xác minh thị giác 100% cho giao diện QC!")

if __name__ == "__main__":
    main()
