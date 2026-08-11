import unittest
import tempfile
import os
from pathlib import Path
from backend.repository import JSONFileRepository


class TestRepository(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = Path(self.temp_dir.name) / "test_places.json"
        self.repo = JSONFileRepository(file_path=self.test_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_repository_crud(self):
        # 1. Ban đầu trống
        self.assertEqual(len(self.repo.get_all()), 0)

        # 2. Thêm quán mới
        sample_place = {
            "name": "Phở Thìn Bờ Hồ",
            "category": "Phở",
            "address": "61 Đinh Tiên Hoàng, Hoàn Kiếm, Hà Nội",
            "original_url": "https://maps.app.goo.gl/sample123"
        }
        saved = self.repo.save(sample_place)
        self.assertIsNotNone(saved.get("id"))
        self.assertEqual(saved["name"], "Phở Thìn Bờ Hồ")

        # 3. Lấy lại tất cả
        places = self.repo.get_all()
        self.assertEqual(len(places), 1)
        self.assertEqual(places[0]["name"], "Phở Thìn Bờ Hồ")

        # 4. Xóa quán
        deleted = self.repo.delete(saved["id"])
        self.assertTrue(deleted)
        self.assertEqual(len(self.repo.get_all()), 0)


if __name__ == "__main__":
    unittest.main()
