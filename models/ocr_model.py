from paddleocr import PaddleOCR
import inspect

class OCRModel:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            # Lấy danh sách tham số PaddleOCR hỗ trợ
            sig = inspect.signature(PaddleOCR)
            kwargs = {
                "lang": "en",
                "use_textline_orientation": True
            }

            # Chỉ thêm show_log nếu version hỗ trợ
            if "show_log" in sig.parameters:
                kwargs["show_log"] = False

            cls._instance = PaddleOCR(**kwargs)

        return cls._instance
