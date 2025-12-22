import cv2
import re
import numpy as np
from sentence_transformers import util

# --- Import Models ---
from models.ocr_model import OCRModel
from models.embedding_model import EmbeddingModel

# --- Import Utils ---
from utils.image_processing import preprocess_column, split_cv_columns
from utils.text_cleaner import clean_ocr_errors_smart, clean_text
from utils.file_loader import load_file_as_images
from core.constants import EDUCATION_LEVELS, LANGUAGES, FRAMEWORKS, DATABASES
from core.logger import logger

class CVParserService:
    def __init__(self):
        self.ocr = OCRModel.get_instance()
        self.embedder = EmbeddingModel.get_instance()

    # =========================================================================
    # 1. OCR ENGINE
    # =========================================================================

    def _ocr_image_data(self, image_data):
        try:
            result = self.ocr.ocr(image_data, cls=True)
            if not result or not result[0]: return ""
            lines = [line[1][0] for line in result[0] if line[1][1] > 0.5]
            return "\n".join(lines)
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""

    def parse_cv_document(self, file_path):
        """
        Hàm chính: Xử lý cả PDF và Ảnh bằng PaddleOCR
        """
        # 1. Load file thành list ảnh (PDF 3 trang -> 3 ảnh)
        images = load_file_as_images(file_path)
        
        if not images:
            return "", "Không thể load file hoặc file rỗng."

        full_text = ""
        
        # 2. Xử lý từng trang một
        for i, img in enumerate(images):
            print(f"Processing page {i+1}/{len(images)}...")
            page_text = self._process_single_page_numpy(img)
            full_text += page_text + "\n"
            
        clean_raw = clean_ocr_errors_smart(clean_text(full_text))
        return clean_raw, None
    def _process_single_page_numpy(self, image_numpy):
        """Xử lý chia cột (Layout Analysis)"""
        if len(image_numpy.shape) == 3:
            gray = cv2.cvtColor(image_numpy, cv2.COLOR_BGR2GRAY)
        else:
            gray = image_numpy

        height, width = gray.shape
        left_check_area = gray[:, :int(width * 0.40)]
        right_check_area = gray[:, int(width * 0.60):]
        
        mean_left = np.mean(left_check_area)
        mean_right = np.mean(right_check_area)
        
        DIFFERENCE_THRESHOLD = 80
        is_dark_left = (abs(mean_left - mean_right) > DIFFERENCE_THRESHOLD) and (mean_left < mean_right)
        is_dark_right = (abs(mean_left - mean_right) > DIFFERENCE_THRESHOLD) and (mean_right < mean_left)

        if is_dark_left:
            split = int(width * 0.42)
            left_txt = self._ocr_image_data(preprocess_column(gray[:, :split], True))
            right_txt = self._ocr_image_data(preprocess_column(gray[:, split:], False))
            return left_txt + "\n\n" + right_txt
        elif is_dark_right:
            split = int(width * 0.58)
            left_txt = self._ocr_image_data(preprocess_column(gray[:, :split], False))
            right_txt = self._ocr_image_data(preprocess_column(gray[:, split:], True))
            return left_txt + "\n\n" + right_txt
        else:
            processed = preprocess_column(gray, np.mean(gray) < 100)
            return self._ocr_image_data(processed)

    # =========================================================================
    # 2. INFO EXTRACTION
    # =========================================================================

    def extract_info(self, text):
        return {
            "full_name": self._find_full_name(text),
            "email": self._extract_emails(text),
            "phone_number": self._find_phone_number(text),
            "years_experience": self._find_years_experience(text),
            "education_level": self._extract_education_level(text),
            # Passive Scan: Tìm tất cả skill có thể để hiển thị Info
            "skills_detected": self._extract_all_skills_passive(text), 
            "languages_detected": self._extract_foreign_languages(text)
        }

    def _find_full_name(self, text):
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        for line in lines[:15]:
            if (line.istitle() or line.isupper()) and 2 <= len(line.split()) <= 6:
                if '@' not in line and not re.search(r'\d', line):
                    ignore = ["resume", "cv", "curriculum", "vitae", "profile", "contact", "developer", "engineer"]
                    if not any(w in line.lower() for w in ignore):
                        return line.title()
        return "Unknown Candidate"

    def _extract_emails(self, text):
        if not text: return []
        _EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', re.IGNORECASE)
        return list(set(_EMAIL_RE.findall(text)))

    def _find_phone_number(self, text):
        patterns = [
            r'\b((\+84|0)[3|5|7|8|9]([\s\.-]?\d{2,4}){2,3})\b',
            r'\b(\(?[1-9]\d{2}\)?[\s\.-]?\d{3}[\s\.-]?\d{4})\b',
            r'\b([1-9]\d{2}[\s\.-]\d{4})\b'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                phone_str = match.group(0)
                if phone_str.startswith('+'):
                    cleaned_phone = '+' + re.sub(r'\D', '', phone_str[1:])
                else:
                    cleaned_phone = re.sub(r'\D', '', phone_str)

                return cleaned_phone

        return None

    def _find_years_experience(self, text):
        pattern = re.compile(r'(\d{1,2})\+?\s*(year|nam|yrs)s?\s*(experience|kinh nghiem)?', re.IGNORECASE)
        match = pattern.search(text)
        return int(match.group(1)) if match else 0

    def _extract_education_level(self, text, threshold=0.60):
        lines = [s.strip() for s in text.split('\n') if 4 < len(s.strip()) < 80]
        if not lines: return None
        
        emb_edu = self.embedder.encode(EDUCATION_LEVELS, convert_to_tensor=True)
        emb_lines = self.embedder.encode(lines, convert_to_tensor=True)
        cos_scores = util.cos_sim(emb_lines, emb_edu)
        max_score = cos_scores.max()
        
        if max_score > threshold:
            idx = (cos_scores == max_score).nonzero(as_tuple=True)[1][0]
            return EDUCATION_LEVELS[idx.item()]
        return None

    def _extract_foreign_languages(self, text):
        text_clean = text.replace('\n', '  ')
        results = []
        target_languages = ['English', 'Vietnamese', 'Japanese', 'Korean', 'Chinese', 'French']
        for lang in target_languages:
            lang_esc = re.escape(lang)
            # Regex tìm ngôn ngữ + level/chứng chỉ gần đó
            pattern = r'\b' + lang_esc + r'.{0,35}?\b(IELTS\s*[\d\.]+|TOEIC\s*\d+|N[1-5]|HSK\s*\d|Native|Fluent|Intermediate|Basic|Advanced)\b'
            
            match = re.search(pattern, text_clean, re.IGNORECASE)
            if match:
                results.append(f"{lang} ({match.group(1).title()})")
            elif re.search(r'\b' + lang_esc + r'\b', text_clean, re.IGNORECASE):
                # Nếu chỉ thấy tên ngôn ngữ (VD: English) mà ko có level, có thể bỏ qua hoặc thêm vào
                pass 
        return results

    def _extract_all_skills_passive(self, text):
        """Quét toàn bộ skill có trong database để hiển thị thông tin chung"""
        found_skills = {}
        text_lower = text.lower()

        def scan_list(category, items):
            found = []
            for item in items:
                item_esc = re.escape(item.lower())
                pattern = r'(?:^|\s|[,\.\-\/])' + item_esc + r'(?:$|\s|[,\.\-\/])'
                if re.search(pattern, text_lower):
                    found.append(item)
            if found:
                found_skills[category] = found

        scan_list('Languages', LANGUAGES)
        scan_list('Frameworks', FRAMEWORKS)
        scan_list('Databases', DATABASES)
        
        return found_skills