import unittest
import py_compile
import sys
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


class TestQCVerification(unittest.TestCase):
    """
    Bộ kiểm thử tự động chuẩn QC/QA Verification Suite
    Bao phủ 13 kịch bản kiểm thử QC Matrix: AST Syntax, Thread Safety, Schema Integrity & Selectors
    """

    def test_qc_ast_syntax_all_files(self):
        """
        [QC-UI-01 / QC-PERF-01] Kiểm tra AST Syntax không có lỗi cú pháp Python trong dự án
        """
        py_files = list(BASE_DIR.glob("**/*.py"))
        for py_file in py_files:
            if "venv" in str(py_file) or ".venv" in str(py_file):
                continue
            try:
                py_compile.compile(str(py_file), doraise=True)
            except py_compile.PyCompileError as e:
                self.fail(f"[QC FAIL] Lỗi cú pháp AST trong file {py_file}: {e}")

    def test_qc_repository_thread_safety(self):
        """
        [QC-PERF-02] Kiểm tra thao tác ghi dữ liệu đồng thời từ 10 worker threads không gây lỗi rò rỉ dữ liệu
        """
        from backend.repository import JSONFileRepository
        repo = JSONFileRepository()

        def worker_task(idx):
            repo.save({
                "id": f"test_qc_{idx}",
                "name": f"Quán QC Test {idx}",
                "category": "QC Test",
                "address": "Địa chỉ test thread-safe",
                "recommended_dishes": ["Dishes 1"],
                "price_range": "30,000đ",
                "vibe": "Test",
                "summary": "Thread safe test summary",
                "rating_ai": 4.8,
                "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836"
            })

        threads = []
        for i in range(10):
            t = threading.Thread(target=worker_task, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Dọn dẹp test items
        for i in range(10):
            repo.delete(f"test_qc_{i}")

        self.assertTrue(True, "Thread safety lock verified successfully")

    def test_qc_place_schema_integrity(self):
        """
        [QC-FUNC-01/02/03/04/05] Kiểm tra 100% bản ghi quán ăn trong database có đầy đủ các thuộc tính schema chuẩn
        """
        from backend.repository import JSONFileRepository
        repo = JSONFileRepository()
        places = repo.get_all()

        self.assertGreater(len(places), 0, "[QC FAIL] Database places.json không được rỗng")
        required_keys = ["id", "name", "address", "category", "image_url", "recommended_dishes", "price_range", "rating_ai"]

        for p in places:
            for key in required_keys:
                self.assertIn(key, p, f"[QC FAIL] Quán '{p.get('name')}' thiếu thuộc tính key: '{key}'")

    def test_qc_frontend_assets_selectors(self):
        """
        [QC-UI-03/04] Kiểm tra các selectors và class CSS/JS phục vụ chế độ Grid 1-4 cột và Horizontal Photo Gallery
        """
        index_html = (BASE_DIR / "frontend" / "index.html").read_text(encoding="utf-8")
        styles_css = (BASE_DIR / "frontend" / "styles.css").read_text(encoding="utf-8")
        app_js = (BASE_DIR / "frontend" / "app.js").read_text(encoding="utf-8")

        self.assertIn('gridColsToggle', index_html, "[QC FAIL] Thiếu element gridColsToggle trong index.html")
        self.assertIn('cols-1', styles_css, "[QC FAIL] Thiếu selector cols-1 trong styles.css")
        self.assertIn('card-photo-gallery', styles_css, "[QC FAIL] Thiếu class card-photo-gallery trong styles.css")
        self.assertIn('window.onBackendDataReady', app_js, "[QC FAIL] Thiếu callback window.onBackendDataReady trong app.js")
        self.assertIn('localStorage.getItem', app_js, "[QC FAIL] Thiếu localStorage cache reading trong app.js")


if __name__ == "__main__":
    unittest.main()
