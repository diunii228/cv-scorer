from paddleocr import PaddleOCR

class OCRModel:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = PaddleOCR(
                lang="en",
                use_angle_cls=True
            )
        return cls._instance
