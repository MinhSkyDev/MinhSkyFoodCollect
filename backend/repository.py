from abc import ABC, abstractmethod
import json
import uuid
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from backend.config import Config


class IFoodRepository(ABC):
    """
    Interface cho Repository quản lý dữ liệu quán ăn.
    Sử dụng Dependency Injection để dễ dàng chuyển đổi nguồn lưu trữ (JSON, SQLite, MongoDB...)
    mà không làm thay đổi các tầng logic phía trên.
    """
    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_by_id(self, place_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def save(self, place_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def save_batch(self, places_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete(self, place_id: str) -> bool:
        pass

    @abstractmethod
    def clear_all(self) -> bool:
        pass


class JSONFileRepository(IFoodRepository):
    """
    Cài đặt cụ thể của IFoodRepository lưu trữ dữ liệu vào file JSON local.
    Thread-safe với threading.Lock().
    """
    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = file_path or Config.DATA_FILE
        self._lock = threading.Lock()
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def _read_data(self) -> List[Dict[str, Any]]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _write_data(self, data: List[Dict[str, Any]]) -> bool:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[Error writing JSON repo]: {e}")
            return False

    def get_all(self) -> List[Dict[str, Any]]:
        data = self._read_data()
        # Sắp xếp mới nhất lên đầu
        return sorted(data, key=lambda x: x.get("created_at", ""), reverse=True)

    def get_by_id(self, place_id: str) -> Optional[Dict[str, Any]]:
        data = self._read_data()
        for item in data:
            if item.get("id") == place_id:
                return item
        return None

    def save(self, place_data: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            data = self._read_data()
            
            # Tạo copy độc lập để tránh biến đổi object dùng chung
            item_to_save = dict(place_data)

            # Nếu chưa có ID thì cấp ID mới
            if "id" not in item_to_save or not item_to_save["id"]:
                item_to_save["id"] = str(uuid.uuid4())
                
            if "created_at" not in item_to_save:
                item_to_save["created_at"] = datetime.now().isoformat()
                
            # Kiểm tra trùng lặp qua URL nếu có
            existing_index = -1
            url = item_to_save.get("original_url") or item_to_save.get("url")
            if url:
                for idx, item in enumerate(data):
                    if item.get("original_url") == url or item.get("url") == url:
                        existing_index = idx
                        break

            if existing_index >= 0:
                # Cập nhật thông tin quán cũ
                data[existing_index].update(item_to_save)
                saved_item = data[existing_index]
            else:
                data.append(item_to_save)
                saved_item = item_to_save

            self._write_data(data)
            return saved_item

    def save_batch(self, places_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        saved_items = []
        for place in places_list:
            saved_item = self.save(place)
            saved_items.append(saved_item)
        return saved_items

    def delete(self, place_id: str) -> bool:
        data = self._read_data()
        new_data = [item for item in data if item.get("id") != place_id]
        if len(new_data) < len(data):
            return self._write_data(new_data)
        return False

    def clear_all(self) -> bool:
        return self._write_data([])
