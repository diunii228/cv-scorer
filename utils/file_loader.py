# utils/file_loader.py
import os
import cv2
import numpy as np
import platform
from pdf2image import convert_from_path
from core.logger import logger


def convert_pil_to_opencv(pil_image):
    """
    Chuyển ảnh PIL (từ pdf2image) sang định dạng OpenCV (numpy array)
    để PaddleOCR có thể đọc được.
    """
    # PIL (RGB) -> OpenCV (BGR)
    open_cv_image = np.array(pil_image)
    if len(open_cv_image.shape) == 3:
        open_cv_image = open_cv_image[:, :, ::-1].copy()
    return open_cv_image


def load_file_as_images(file_path):
    """
    Input:  Đường dẫn file (PDF hoặc ảnh)
    Output: List ảnh dạng numpy array để đưa vào OCR
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return []

    file_ext = os.path.splitext(file_path)[1].lower()
    images = []

    try:
        # =========================
        # TRƯỜNG HỢP 1: FILE PDF
        # =========================
        if file_ext == ".pdf":
            poppler_path = None

            # Windows cần chỉ rõ poppler_path
            if platform.system() == "Windows":
                poppler_path = r"C:\poppler\Library\bin"

            logger.info(f"Loading PDF file: {file_path}")

            pil_images = convert_from_path(
                file_path,
                dpi=200,
                poppler_path=poppler_path
            )

            if not pil_images:
                logger.error("PDF loaded but no pages were extracted (empty PDF or Poppler error)")
                return []

            for idx, pil_img in enumerate(pil_images):
                img_cv = convert_pil_to_opencv(pil_img)
                images.append(img_cv)

        # =========================
        # TRƯỜNG HỢP 2: FILE ẢNH
        # =========================
        elif file_ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
            logger.info(f"Loading image file: {file_path}")

            img_cv = cv2.imread(file_path)
            if img_cv is None:
                logger.error("OpenCV cannot read image file")
                return []

            images.append(img_cv)

        # =========================
        # TRƯỜNG HỢP KHÁC
        # =========================
        else:
            logger.error(f"Unsupported file format: {file_ext}")
            return []

    except Exception as e:
        logger.error(f"Error loading file {file_path}: {e}")
        return []

    return images
