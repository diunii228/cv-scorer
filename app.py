import streamlit as st
import os
import tempfile
import traceback

# Import Core & Services
from services.cv_parser_service import CVParserService
from services.jd_parser_service import parse_jd_input
from services.scoring_service import ScoringService
from services.history_service import HistoryService
from models.llm_model import LocalLLM

# Import LLM Service
try:
    from services.llm_service import generate_feedback_local
except ImportError:
    generate_feedback_local = None

# Import UI
from ui.ui_components import (
    render_sidebar, 
    render_jd_form, 
    render_upload_section, 
    render_results, 
    render_history_table
)

# Page Config
st.set_page_config(page_title="AI CV Scorer", page_icon="📄", layout="wide")

# --- Initialize Services (Cached) ---
@st.cache_resource
def get_services():
    return {
        "parser": CVParserService(),
        "scorer": ScoringService(),
        "history": HistoryService(),
        "llm": LocalLLM.get_instance() 
    }

services = get_services()

# --- Main App Logic ---
def main():
    st.title("📄 AI Powered CV Scoring System")
    render_sidebar()

    # Tabs
    tab1, tab2 = st.tabs(["🚀 Đánh giá CV", "📜 Lịch sử"])

    with tab1:
        # 1. Input JD
        jd_raw = render_jd_form()
        
        # 2. Upload CV
        uploaded_file = render_upload_section()

        # 3. Process Button
        if st.button("🔍 Phân tích & Chấm điểm", type="primary"):
            if not uploaded_file:
                st.error("Vui lòng upload file CV!")
            else:
                with st.spinner("Đang xử lý OCR và Phân tích..."):
                    # Tạo file tạm để xử lý
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name

                    try:
                        # ---------------------------------------------------------
                        # A. OCR & Basic Extraction (Giống logic extract_text_from_cv)
                        # ---------------------------------------------------------
                        cv_text, err = services["parser"].parse_cv_document(tmp_path)
                        
                        if err:
                            st.error(f"Lỗi đọc file: {err}")
                        else:
                            # Trích xuất thông tin cơ bản (Info)
                            # parser.extract_info tương đương với các hàm find_full_name, extract_emails...
                            info = services["parser"].extract_info(cv_text)
                            
                            # ---------------------------------------------------------
                            # B. Parse JD & Matching (Logic Loop từ snippet của bạn)
                            # ---------------------------------------------------------
                            jd_parsed = parse_jd_input(jd_raw)
                            
                            skill_results = {}
                            formatted_skills = {} # Dictionary chứa skill đã format đẹp (Senior/Junior)

                            # Loop qua các category kỹ thuật
                            for cat in ['programming_languages', 'frameworks', 'databases']:
                                # Lấy skill yêu cầu từ JD
                                req_skills = jd_parsed.get(cat, {})
                                
                                # Thực hiện Matching (tương đương hybrid_skill_matching_with_level)
                                matched_dict = services["scorer"].match_skills(cv_text, req_skills)
                                skill_results[cat] = matched_dict

                                # --- LOGIC FORMATTING TỪ SNIPPET CỦA BẠN ---
                                # Chuyển đổi level số (1,2,3) thành chữ (Junior, Mid, Senior)
                                lst_display = []
                                for s, l in matched_dict.items():
                                    if l >= 3: lvl_str = "Senior"
                                    elif l == 2: lvl_str = "Mid"
                                    else: lvl_str = "Junior"
                                    
                                    lst_display.append(f"{s} ({lvl_str})")
                                formatted_skills[cat] = lst_display
                                # -------------------------------------------

                            # ---------------------------------------------------------
                            # C. Scoring (Tương đương calculate_advanced_score)
                            # ---------------------------------------------------------
                            # Gom dữ liệu lại thành cv_data_full
                            # Lưu ý: info['languages_detected'] đã có sẵn từ parser
                            cv_data_full = {
                                **info,
                                "skills_extracted": skill_results,  # Dict dùng để tính điểm (số)
                                "skills_display": formatted_skills, # Dict dùng để hiển thị/AI (chữ)
                                "lang_extracted": info.get('languages_detected', [])
                            }
                            
                            score, breakdown = services["scorer"].calculate_score(cv_data_full, jd_parsed)
                            
                            # ---------------------------------------------------------
                            # D. AI Feedback (Tương đương generate_feedback_local)
                            # ---------------------------------------------------------
                            ai_feedback = ""
                            if services["llm"] and generate_feedback_local:
                                ai_feedback = generate_feedback_local(
                                    cv_data=cv_data_full, # Truyền data đã có skills_display
                                    jd_parsed=jd_parsed, 
                                    match_score=score, 
                                    llm_model=services["llm"]
                                )
                            elif not services["llm"]:
                                ai_feedback = "⚠️ Local LLM chưa được tải hoặc gặp lỗi. Không thể tạo nhận xét chi tiết."
                            
                            # ---------------------------------------------------------
                            # E. Save History & Render UI
                            # ---------------------------------------------------------
                            services["history"].save_record(cv_data_full, score, jd_parsed['job_title'])
                            render_results(cv_data_full, score, breakdown, ai_feedback)

                    except Exception as e:
                        st.error("Đã xảy ra lỗi hệ thống!")
                        st.code(traceback.format_exc()) 
                    finally:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)

    with tab2:
        history_data = services["history"].load_history()
        render_history_table(history_data)
        if st.button("Xóa lịch sử"):
            services["history"].clear_history()
            st.rerun()

if __name__ == "__main__":
    main()