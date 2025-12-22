import os

class Settings:
    # Model Repos
    LLM_REPO_ID = "bartowski/Qwen2.5-7B-Instruct-GGUF"
    LLM_FILENAME = "Qwen2.5-7B-Instruct-Q4_K_M.gguf"
    EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-base"
    TOP_K_CANDIDATES = 5
    SUPPORTED_CV_FORMATS = [".pdf", ".docx"]
    # Thresholds
    SKILL_MATCH_THRESHOLD = 0.85
    EDUCATION_THRESHOLD = 0.65
    USE_OCR_FALLBACK = True        # nếu pdfplumber không trích được text thì dùng OCR
    OCR_LANG = "eng"               # ngôn ngữ cho Tesseract, ví dụ "eng" hoặc "vie"
    OCR_DPI = 300                  # DPI khi convert pdf->image
    OCR_MAX_PAGES = 50             # giới hạn số trang để tránh xử lý vô hạn
    TESSERACT_CMD = None 
    # Paths
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MODEL_CACHE_DIR = os.path.join(ROOT_DIR, "data", "models_cache")

settings = Settings()