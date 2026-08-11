import unittest
import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock
import pandas as pd
from backend.repository import JSONFileRepository
from backend.service import FoodRecapService


class TestFoodRecapService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = Path(self.temp_dir.name) / "places.json"
        self.repo = JSONFileRepository(file_path=self.test_file)

        def mock_analyze(url):
            unique_suffix = str(uuid.uuid4())[:8]
            return {
                "id": str(uuid.uuid4()),
                "name": "Quán Test " + unique_suffix,
                "address": f"{unique_suffix} Đường Test, Hà Nội",
                "category": "Phở",
                "recommended_dishes": ["Phở bò", "Quẩy"],
                "price_range": "30,000đ - 50,000đ",
                "vibe": "Máy lạnh",
                "summary": "Quán phở ngon chuẩn vị",
                "rating_ai": 4.8,
                "highlights": ["Must Try!"],
                "original_url": url,
                "expanded_url": url
            }

        self.mock_ai = MagicMock()
        self.mock_ai.analyze_food_link.side_effect = mock_analyze
        self.service = FoodRecapService(repository=self.repo, ai_service=self.mock_ai)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_process_text_input(self):
        text = """
        Danh sách quán ăn:
        https://maps.app.goo.gl/sample123
        https://www.google.com/maps/place/Pho+Thin
        """
        results = self.service.process_text_input(text)
        self.assertEqual(len(results), 2)

        stats = self.service.get_stats()
        self.assertEqual(stats["total_places"], 2)
        self.assertEqual(stats["total_categories"], 1)

    def test_process_excel_file(self):
        # Tạo file Excel mẫu
        excel_path = Path(self.temp_dir.name) / "test_input.xlsx"
        df = pd.DataFrame({
            "Tên Quán": ["Phở", "Bún đậu"],
            "Link Google Maps": [
                "https://maps.app.goo.gl/sampleExcel1",
                "https://maps.app.goo.gl/sampleExcel2"
            ]
        })
        df.to_excel(excel_path, index=False)

        results = self.service.process_file_input(str(excel_path))
        self.assertEqual(len(results), 2)

        # Test Xuất Excel
        output_excel = Path(self.temp_dir.name) / "exported.xlsx"
        exported_path = self.service.export_to_excel(str(output_excel))
        self.assertTrue(Path(exported_path).exists())


if __name__ == "__main__":
    unittest.main()
