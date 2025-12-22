from paddleocr import PaddleOCR

class OCRModel:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            print("⏳ Loading PaddleOCR...")
            cls._instance = PaddleOCR(lang='en', use_textline_orientation=True, show_log=False)
        return cls._instance