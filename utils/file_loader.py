# utils/file_loader.py
import os
import cv2
import numpy as np
from pdf2image import convert_from_path

def convert_pil_to_opencv(pil_image):
    """
    Chuyển ảnh PIL (từ pdf2image) sang định dạng OpenCV (numpy array)
    để PaddleOCR có thể đọc được.
    """
    # Convert RGB to BGR
    open_cv_image = np.array(pil_image) 
    open_cv_image = open_cv_image[:, :, ::-1].copy() 
    return open_cv_image

def load_file_as_images(file_path):
    """
    Input: Đường dẫn file (PDF hoặc Ảnh)
    Output: List các ảnh (numpy array) để đưa vào OCR
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_ext = os.path.splitext(file_path)[1].lower()
    images = []

    try:
        # TRƯỜNG HỢP 1: PDF (Cần cài đặt poppler)
        if file_ext == '.pdf':
            # Chuyển mỗi trang PDF thành 1 ảnh
            # dpi=200 là đủ nét cho OCR, dpi=300 thì chính xác hơn nhưng chậm hơn
            pil_images = convert_from_path(file_path, dpi=200)
            
            for pil_img in pil_images:
                img_cv = convert_pil_to_opencv(pil_img)
                images.append(img_cv)
                
        # TRƯỜNG HỢP 2: Ảnh thường
        elif file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
            img_cv = cv2.imread(file_path)
            if img_cv is not None:
                images.append(img_cv)
            else:
                raise ValueError("Không thể đọc file ảnh.")
        
        else:
            raise ValueError(f"Định dạng file không hỗ trợ: {file_ext}")

    except Exception as e:
        print(f"Error loading file {file_path}: {e}")
        return []

    return images