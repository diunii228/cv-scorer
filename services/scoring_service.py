import difflib
import re
from core.constants import SKILL_LEVEL_MAPPING, EDUCATION_RANKING
from utils.text_cleaner import clean_text

class ScoringService:

    # 1. Thêm 'self' vào tham số đầu tiên
    def get_education_rank(self, edu_text):
        if not edu_text: return 0
        # Map text sang số (Bachelor -> 2)
        for key, rank in EDUCATION_RANKING.items():
            if key.lower() in edu_text.lower():
                return rank
        return 0
    def _detect_level_from_context(self, skill_name, cv_text, window=60):
        """
        Hàm nội bộ: Quét ngữ cảnh xung quanh skill để đoán level.
        - window: Số ký tự quét trước và sau từ khóa.
        """
        skill_lower = skill_name.lower()
        cv_lower = cv_text.lower()
        
        # Tìm tất cả vị trí xuất hiện của skill trong CV
        # Dùng re.escape để xử lý skill có ký tự đặc biệt như C++, C#
        matches = [m.start() for m in re.finditer(re.escape(skill_lower), cv_lower)]
        
        if not matches:
            return 0 # Không tìm thấy
            
        max_detected_level = 1 # Mặc định là 1 (Cơ bản) nếu tìm thấy mà ko có keyword

        for idx in matches:
            # Cắt chuỗi xung quanh từ khóa (Context Window)
            start = max(0, idx - window)
            end = min(len(cv_lower), idx + len(skill_lower) + window)
            context_snippet = cv_lower[start:end]
            
            # Quét các từ khóa Level trong đoạn text này
            for keyword, level_val in SKILL_LEVEL_MAPPING.items():
                # Dùng regex bound \b để tránh bắt nhầm (vd: "good" trong "goods")
                if re.search(r'\b' + re.escape(keyword) + r'\b', context_snippet):
                    if level_val > max_detected_level:
                        max_detected_level = level_val
        
        return max_detected_level
    
    # 2. match_skills giữ nguyên (đã đúng self)
    def match_skills(self, cv_text, jd_req_dict):
        """
        Dựa vào skill JD yêu cầu, tìm trong CV và trả về Level.
        Input: 
            - cv_text: Nội dung CV
            - jd_req_dict: {'Python': 3, 'Java': 1} (Skill và Level yêu cầu từ JD)
        Output:
            - matched_results: {'Python': 3, 'Java': 2} (Skill tìm thấy và Level thực tế của ứng viên)
        """
        if not jd_req_dict: return {}
        
        cv_clean = clean_text(cv_text)
        matched_results = {}
        
        # Chỉ quét những skill mà JD yêu cầu
        for skill_name in jd_req_dict.keys():
            # 1. Kiểm tra sự tồn tại (Dùng regex biên để phân biệt Java vs JavaScript)
            skill_esc = re.escape(skill_name.lower())
            # Pattern: \bSkill\b hoặc ký tự đặc biệt (cho C++, C#)
            pattern = r'(?:^|\s|[,\.\-\/])' + skill_esc + r'(?:$|\s|[,\.\-\/])'
            
            if re.search(pattern, cv_clean.lower()):
                # 2. Nếu tìm thấy -> Detect Level từ ngữ cảnh
                detected_level = self._detect_level_from_context(skill_name, cv_clean)
                matched_results[skill_name] = detected_level
                
        return matched_results

    # 3. Thêm 'self' vào tham số đầu tiên
    def calculate_score(self, cv_data, jd_requirements_parsed):
        score = 0
        breakdown = {}

        # --- Tech skills ---
        total_skill_points_max = 0
        total_skill_points_candidate = 0

        tech_cats = ['programming_languages', 'frameworks', 'databases']

        for cat in tech_cats:
            req_dict = jd_requirements_parsed.get(cat, {})
            # Lưu ý: Cần đảm bảo cv_data['skills_extracted'] có cấu trúc dict lồng nhau
            # Ví dụ: {'programming_languages': {'Python': 1}, 'databases': {'SQL': 1}}
            found_dict = cv_data.get('skills_extracted', {}).get(cat, {})

            for skill_name, req_level in req_dict.items():
                total_skill_points_max += req_level

                if skill_name in found_dict:
                    found_level = found_dict[skill_name]
                    if found_level >= req_level:
                        total_skill_points_candidate += req_level
                    else:
                        total_skill_points_candidate += (found_level / req_level) * req_level

        if total_skill_points_max > 0:
            tech_score = (total_skill_points_candidate / total_skill_points_max) * 50
        else:
            tech_score = 50

        score += tech_score
        breakdown['Skills'] = f"{tech_score:.1f}/50"
        
        # --- Education ---
        req_edu_str = jd_requirements_parsed.get('education_level', 'None')
        found_edu_str = cv_data.get('education_level')

        # 4. SỬA LỖI GỌI HÀM: Phải dùng self.get_education_rank
        req_rank = self.get_education_rank(req_edu_str)
        found_rank = self.get_education_rank(found_edu_str)

        edu_score = 0
        if req_rank == 0:
            edu_score = 10
        else:
            if found_rank >= req_rank:
                edu_score = 10
            elif found_rank > 0:
                edu_score = (found_rank / req_rank) * 10
            else:
                edu_score = 0

        score += edu_score
        breakdown['Education'] = f"{edu_score:.1f}/10 (Require: {req_edu_str} vs Have: {found_edu_str})"

        # --- Experience ---
        req_exp = jd_requirements_parsed.get('required_experience_years', 0) or 0
        cand_exp = cv_data.get('years_experience', 0) or 0

        if req_exp == 0: exp_score = 30
        else:
            exp_score = min((cand_exp / req_exp) * 30, 30) # Max 30

        score += exp_score
        breakdown['Experience'] = f"{exp_score:.1f}/30 ({cand_exp}/{req_exp} năm)"

        # --- Foreign language ---
        req_langs = jd_requirements_parsed.get('foreign_languages', [])
        found_langs = cv_data.get('lang_extracted', {}) # Dict

        if not req_langs: lang_score = 10
        else:
            match_count = 0
            for req in req_langs:
                if req in found_langs: match_count += 1

            lang_score = (match_count / len(req_langs)) * 10

        score += lang_score
        breakdown['Foreign Languge'] = f"{lang_score:.1f}/10"

        return round(score, 1), breakdown