import os
from typing import List, Dict, Any, Optional
import pandas as pd
from backend.repository import IFoodRepository, JSONFileRepository
from backend.ai_service import GeminiAIService
from backend.parsers import extract_urls_from_text, parse_file_any


class FoodRecapService:
    """
    Service quản lý logic chính của ứng dụng Tổng hợp Quán ăn.
    Sử dụng Dependency Injection cho Repository và AI Service.
    """
    def __init__(
        self,
        repository: Optional[IFoodRepository] = None,
        ai_service: Optional[GeminiAIService] = None
    ):
        # Dependency Injection: Nhận repository từ ngoài vào (mặc định dùng JSONFileRepository)
        self.repository = repository or JSONFileRepository()
        self.ai_service = ai_service or GeminiAIService()

    def get_all_places(self) -> List[Dict[str, Any]]:
        return self.repository.get_all()

    def process_links(self, urls: List[str], max_workers: int = 4) -> List[Dict[str, Any]]:
        """
        Xử lý danh sách các link Google Maps SONG SONG có kiểm soát Rate Limit:
        Đảm bảo không vượt quá giới hạn 15 request/phút của Gemini API Free Tier.
        """
        import time
        cleaned_urls = [u.strip() for u in urls if u.strip()]
        if not cleaned_urls:
            return []

        results = []
        
        def _process_single(url: str):
            time.sleep(0.3) # Giảm tải xung đột API key
            analyzed_data = self.ai_service.analyze_food_link(url)
            return self.repository.save(analyzed_data)

        # Sử dụng ThreadPoolExecutor 4 workers
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=min(max_workers, len(cleaned_urls))) as executor:
            future_to_url = {executor.submit(_process_single, url): url for url in cleaned_urls}
            for future in as_completed(future_to_url):
                try:
                    data = future.result()
                    results.append(data)
                except Exception as e:
                    print(f"[Error processing single link parallel]: {e}")

        return results

    def process_text_input(self, raw_text: str) -> List[Dict[str, Any]]:
        """
        Trích xuất link từ đoạn văn bản thô (dán trực tiếp nhiều link/Notepad++) và xử lý.
        """
        urls = extract_urls_from_text(raw_text)
        return self.process_links(urls)

    def process_file_input(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Đọc file .txt hoặc Excel .xlsx/.csv, lấy link và xử lý.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Không tìm thấy file: {file_path}")
            
        urls = parse_file_any(file_path)
        return self.process_links(urls)

    def delete_place(self, place_id: str) -> bool:
        return self.repository.delete(place_id)

    def clear_all(self) -> bool:
        return self.repository.clear_all()

    def get_stats(self) -> Dict[str, Any]:
        """
        Tính toán dữ liệu thống kê cho Dashboard UI.
        """
        places = self.repository.get_all()
        total_places = len(places)

        # Đếm loại hình danh mục
        category_counts: Dict[str, int] = {}
        for p in places:
            cat = p.get("category", "Khác")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Món ăn được đề xuất nhiều nhất
        all_dishes: List[str] = []
        for p in places:
            dishes = p.get("recommended_dishes", [])
            if isinstance(dishes, list):
                all_dishes.extend(dishes)

        return {
            "total_places": total_places,
            "total_categories": len(category_counts),
            "category_breakdown": category_counts,
            "popular_dishes": list(set(all_dishes))[:10]
        }

    def reanalyze_place(self, place_id: str) -> Optional[Dict[str, Any]]:
        """
        Phân tích lại 1 quán ăn cụ thể theo place_id.
        """
        place = self.repository.get_by_id(place_id)
        if not place:
            return None

        url = place.get("original_url") or place.get("expanded_url")
        if not url:
            return None

        analyzed = self.ai_service.analyze_food_link(url)
        analyzed["id"] = place_id  # Giữ nguyên ID
        return self.repository.save(analyzed)

    def reanalyze_all_fallbacks(self) -> List[Dict[str, Any]]:
        """
        Tự động quét và phân tích lại tất cả các quán chưa có tên/địa chỉ rõ ràng.
        """
        places = self.repository.get_all()
        fallback_ids = [
            p["id"] for p in places 
            if p.get("name") == "Quán ăn từ Google Maps" or "Đang cập nhật" in p.get("address", "")
        ]

        results = []
        for pid in fallback_ids:
            updated = self.reanalyze_place(pid)
            if updated:
                results.append(updated)

        return results

    def export_to_excel(self, output_path: str) -> str:
        """
        Xuất danh sách quán ăn hiện có ra file Excel định dạng đẹp mắt.
        """
        places = self.repository.get_all()
        if not places:
            raise ValueError("Chưa có dữ liệu quán ăn để xuất Excel!")

        export_data = []
        for p in places:
            dishes = p.get("recommended_dishes", [])
            dishes_str = ", ".join(dishes) if isinstance(dishes, list) else str(dishes)
            
            highlights = p.get("highlights", [])
            highlights_str = ", ".join(highlights) if isinstance(highlights, list) else str(highlights)

            export_data.append({
                "Tên Quán": p.get("name", ""),
                "Loại Hình": p.get("category", ""),
                "Địa Chỉ": p.get("address", ""),
                "Món Phải Thử": dishes_str,
                "Khoảng Giá": p.get("price_range", ""),
                "Tiện Ích & Không Gian": p.get("vibe", ""),
                "Điểm AI": p.get("rating_ai", 4.0),
                "Nhãn Nổi Bật": highlights_str,
                "Tóm Tắt Nhận Xét": p.get("summary", ""),
                "Link Google Maps": p.get("original_url") or p.get("expanded_url", "")
            })

        df = pd.DataFrame(export_data)
        df.to_excel(output_path, index=False, engine='openpyxl')
        return output_path
