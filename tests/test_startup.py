import unittest
import py_compile
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


class TestStartup(unittest.TestCase):
    def test_all_python_files_syntax(self):
        """
        Kiểm tra cú pháp AST (Syntax Check) của tất cả các file Python trong dự án
        Đảm bảo không có bất kỳ lỗi SyntaxError nào khi khởi động.
        """
        py_files = list(BASE_DIR.glob("**/*.py"))
        for py_file in py_files:
            if "venv" in str(py_file) or ".venv" in str(py_file):
                continue
            try:
                py_compile.compile(str(py_file), doraise=True)
            except py_compile.PyCompileError as e:
                self.fail(f"Lỗi cú pháp trong file {py_file}: {e}")

    def test_startup_imports(self):
        """
        Kiểm tra khả năng nạp các module khởi động chính (main.py, api.py, service.py...)
        """
        from backend.config import Config
        from backend.repository import JSONFileRepository
        from backend.ai_service import GeminiAIService
        from backend.service import FoodRecapService
        from backend.api import ApiBridge

        # Đảm bảo có thể khởi tạo instance mà không có lỗi
        repo = JSONFileRepository()
        ai = GeminiAIService()
        service = FoodRecapService(repository=repo, ai_service=ai)
        api = ApiBridge(service=service)

        self.assertIsNotNone(api)
        self.assertIsNotNone(api.get_places())

    def test_frontend_files_exist(self):
        """
        Kiểm tra sự tồn tại và tính hợp lệ của các file giao diện Frontend
        """
        index_html = BASE_DIR / "frontend" / "index.html"
        styles_css = BASE_DIR / "frontend" / "styles.css"
        app_js = BASE_DIR / "frontend" / "app.js"

        self.assertTrue(index_html.exists(), "Thiếu file frontend/index.html")
        self.assertTrue(styles_css.exists(), "Thiếu file frontend/styles.css")
        self.assertTrue(app_js.exists(), "Thiếu file frontend/app.js")


if __name__ == "__main__":
    unittest.main()
