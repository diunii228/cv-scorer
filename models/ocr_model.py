from paddleocr import PaddleOCR
import paddle
import logging

# ==============================================================================
# WINDOWS HOTFIX (Bản vá lỗi dành riêng cho Windows)
# ==============================================================================
try:
    from paddle.base.libpaddle import AnalysisConfig
    if not hasattr(AnalysisConfig, 'set_optimization_level'):
        AnalysisConfig.set_optimization_level = lambda self, x: None
except (ImportError, AttributeError, Exception) as e:
    logging.warning(f"Không thể áp dụng bản vá Windows cho Paddle: {e}")
# ==============================================================================

class OCRModel:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            # lang="en": Nhận diện tiếng Anh (và hỗ trợ tiếng Việt không dấu tốt)
            # use_angle_cls=True: Tự động xoay ảnh nếu ảnh CV bị nghiêng
            cls._instance = PaddleOCR(
                lang="en", 
                use_angle_cls=True,
                show_log=False  # Tắt log rác để terminal gọn hơn
            )
        return cls._instance