# services/jd_parser_service.py
import re
from typing import Dict, List, Any
from core.constants import SKILL_LEVEL_MAPPING

def _parse_skill_list_to_dict(skill_list: List[str]) -> Dict[str, int]:
    """
    Chuyển list ["Skill A (Level)", "Skill B"] thành {"Skill A": 3, "Skill B": 1}
    """
    result = {}
    if not skill_list:
        return result

    for item in skill_list:
        if not isinstance(item, str): continue
        
        # 1. Tách tên kỹ năng (Loại bỏ phần trong ngoặc)
        # VD: "Python (Senior)" -> "Python"
        skill_name = re.sub(r'\s*\(.*?\)', '', item).strip()
        
        if not skill_name:
            continue

        # 2. Tìm Level trong ngoặc đơn
        # Mặc định là 1 (Junior/Basic) nếu không ghi gì
        level_score = 1 
        match = re.search(r'\((.*?)\)', item)
        
        if match:
            level_text = match.group(1).lower()
            # Map text sang số dựa trên constants.py
            for key, score in SKILL_LEVEL_MAPPING.items():
                if key.lower() in level_text:
                    level_score = score
                    break
        
        result[skill_name] = level_score
            
    return result

def parse_jd_input(jd_raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Chuẩn hóa dữ liệu JD đầu vào.
    Input: Dictionary thô từ API/Frontend
    Output: Dictionary đã được parse level cho các trường kỹ năng
    """
    parsed_jd = jd_raw_data.copy()
    
    # Các trường cần parse level
    tech_categories = ['programming_languages', 'frameworks', 'databases']
    
    for category in tech_categories:
        raw_list = jd_raw_data.get(category, [])
        if raw_list:
            parsed_jd[category] = _parse_skill_list_to_dict(raw_list)
        else:
            parsed_jd[category] = {}

    # Chuẩn hóa field education_level (nếu cần)
    if 'education_level' in parsed_jd:
        parsed_jd['education_level'] = parsed_jd['education_level'].strip().title()

    return parsed_jd