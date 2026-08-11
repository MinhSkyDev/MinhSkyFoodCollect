import os
import sys
from pathlib import Path

# Đảm bảo Windows console hiển thị chuẩn ký tự tiếng Việt UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from backend.config import Config
from backend.repository import JSONFileRepository
from backend.ai_service import GeminiAIService
from backend.service import FoodRecapService


def main():
    print("=" * 70)
    print("[MUNCH RECAP] XỬ LÝ 16 LINK QUÁN ĂN TRÍCH XUẤT TỪ ẢNH")
    print("=" * 70)

    repo = JSONFileRepository()
    ai_service = GeminiAIService()
    service = FoodRecapService(repository=repo, ai_service=ai_service)

    sample_file = BASE_DIR / "data" / "sample_links.txt"
    if not sample_file.exists():
        print(f"[Error]: Không tìm thấy file {sample_file}!")
        return

    print(f"[*] Đang đọc danh sách link từ file: {sample_file}")
    results = service.process_file_input(str(sample_file))

    print(f"\n[THÀNH CÔNG] Đã phân tích & lưu thành công {len(results)} quán ăn!")
    print("-" * 70)

    for idx, place in enumerate(results, 1):
        name = place.get("name", "N/A")
        cat = place.get("category", "N/A")
        addr = place.get("address", "N/A")
        dishes = place.get("recommended_dishes", [])
        dishes_str = ", ".join(dishes) if isinstance(dishes, list) else str(dishes)
        price = place.get("price_range", "N/A")
        
        print(f"{idx:02d}. [{cat}] {name}")
        print(f"    - Địa chỉ: {addr}")
        print(f"    - Món gợi ý: {dishes_str}")
        print(f"    - Khoảng giá: {price}")
        print(f"    - Link Maps: {place.get('original_url')}")
        print("-" * 70)

    # Export ra Excel
    export_file = BASE_DIR / "data" / "danh_sach_quan_an_tu_anh.xlsx"
    service.export_to_excel(str(export_file))
    print(f"[*] Đã xuất bảng tổng hợp quán ăn ra file Excel: {export_file}")


if __name__ == "__main__":
    main()
