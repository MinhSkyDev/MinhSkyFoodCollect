import os
import webview
from typing import List, Dict, Any
from backend.service import FoodRecapService


class ApiBridge:
    """
    Lớp API làm cầu nối giao tiếp giữa Python backend và giao diện HTML/CSS/JS (pywebview).
    Tất cả phương thức ở đây có thể gọi trực tiếp từ JavaScript thông qua: window.pywebview.api.method_name(...)
    """
    def __init__(self, service: FoodRecapService):
        self.service = service
        self._window = None  # Dùng private attribute (_window) để PyWebView JS reflection bỏ qua không quét COM object native

    def set_window(self, window):
        self._window = window

    def get_places(self) -> List[Dict[str, Any]]:
        return self.service.repository.get_all()

    def process_text(self, raw_text: str) -> Dict[str, Any]:
        try:
            results = self.service.process_text_input(raw_text)
            return {
                "success": True,
                "count": len(results),
                "places": self.service.repository.get_all()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def process_file(self, file_path: str) -> Dict[str, Any]:
        try:
            results = self.service.process_file_input(file_path)
            return {
                "success": True,
                "count": len(results),
                "places": self.service.repository.get_all()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_place(self, place_id: str) -> Dict[str, Any]:
        try:
            success = self.service.delete_place(place_id)
            return {
                "success": success,
                "places": self.service.repository.get_all()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def clear_all(self) -> Dict[str, Any]:
        try:
            self.service.clear_all()
            return {"success": True, "places": []}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def reanalyze_place(self, place_id: str) -> Dict[str, Any]:
        try:
            updated = self.service.reanalyze_place(place_id)
            return {
                "success": bool(updated),
                "place": updated,
                "places": self.service.repository.get_all()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def reanalyze_fallbacks(self) -> Dict[str, Any]:
        try:
            results = self.service.reanalyze_all_fallbacks()
            return {
                "success": True,
                "count": len(results),
                "places": self.service.repository.get_all()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_stats(self) -> Dict[str, Any]:
        try:
            return self.service.get_stats()
        except Exception as e:
            return {"error": str(e)}

    def open_file_dialog(self) -> Dict[str, Any]:
        """
        Mở hộp thoại chọn file native (Excel, TXT, CSV) của hệ điều hành.
        """
        if not self._window:
            return {"success": False, "error": "Chưa khởi tạo cửa sổ ứng dụng"}

        file_types = (
            'Tất cả file hỗ trợ (*.txt;*.xlsx;*.xls;*.csv)',
            'File Notepad++ TXT (*.txt)',
            'File Excel (*.xlsx;*.xls)',
            'File CSV (*.csv)'
        )
        
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=file_types
        )
        
        if result and len(result) > 0:
            file_path = result[0]
            return self.process_file(file_path)
        
        return {"success": False, "cancelled": True}

    def export_excel_dialog(self) -> Dict[str, Any]:
        """
        Mở hộp thoại Save File để xuất danh sách ra file Excel.
        """
        if not self._window:
            return {"success": False, "error": "Chưa khởi tạo cửa sổ ứng dụng"}

        file_types = ('File Excel (*.xlsx)',)
        result = self._window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename='food_recap_export.xlsx',
            file_types=file_types
        )

        if result:
            output_path = result if isinstance(result, str) else result[0]
            try:
                exported_file = self.service.export_to_excel(output_path)
                return {"success": True, "file_path": exported_file}
            except Exception as e:
                return {"success": False, "error": str(e)}

        return {"success": False, "cancelled": True}
