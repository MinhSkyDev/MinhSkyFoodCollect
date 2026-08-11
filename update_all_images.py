import os
import sys
from pathlib import Path

# Cấu hình UTF-8 cho Windows Console Stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from backend.repository import JSONFileRepository
from backend.parsers import get_food_image_by_category
from backend.service import FoodRecapService

def update_all_places_images():
    print("=" * 60)
    print("[MUNCH RECAP] Cập nhật hình ảnh & thông tin mở rộng cho 29 quán ăn")
    print("=" * 60)

    repository = JSONFileRepository()
    service = FoodRecapService(repository=repository)
    
    places = repository.get_all()
    print(f"[*] Tổng số quán trong database: {len(places)}")

    updated_count = 0
    for place in places:
        category = place.get("category", "Ẩm thực")
        name = place.get("name", "")
        
        # Gán image_url chuẩn theo danh mục và tên quán
        img_url = get_food_image_by_category(category, name)
        place["image_url"] = img_url
        
        # Đảm bảo có rating_ai
        if "rating_ai" not in place:
            place["rating_ai"] = 4.5

        repository.save(place)
        updated_count += 1
        print(f"  [OK] {name} -> Image: {img_url[:60]}...")

    # Xuất lại file Excel
    excel_path = service.export_to_excel(str(BASE_DIR / "data" / "danh_sach_quan_an_tu_anh.xlsx"))
    print("=" * 60)
    print(f"[THÀNH CÔNG] Đã cập nhật xong {updated_count} quán ăn với ảnh chất lượng cao!")
    print(f"[*] File Excel đã xuất lại: {excel_path}")
    print("=" * 60)

if __name__ == "__main__":
    update_all_places_images()
