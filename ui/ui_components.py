import streamlit as st
import pandas as pd
import plotly.express as px

def render_sidebar():
    """Hiển thị Sidebar cấu hình"""
    with st.sidebar:
        st.header("⚙️ Configuration")
        st.info("Hệ thống đánh giá CV tự động sử dụng AI Local.")
        
        st.divider()
        st.subheader("Model Status")
        st.success("✅ OCR Engine: Ready")
        st.success("✅ Embedding: Ready")
        # Giả lập check status
        st.warning("⚠️ Local LLM: Loading..." if 'llm_loaded' not in st.session_state else "✅ Local LLM: Ready")

def render_jd_form():
    """Hiển thị form nhập Job Description"""
    st.subheader("1. Định nghĩa Job Description (JD)")
    
    col1, col2 = st.columns(2)
    with col1:
        job_title = st.text_input("Vị trí tuyển dụng", value="Python Backend Developer")
        exp_years = st.number_input("Số năm kinh nghiệm yêu cầu", min_value=0, value=2)
    
    with col2:
        edu_level = st.selectbox("Bằng cấp tối thiểu", 
                                ["Bachelor", "Engineer", "Master", "Phd", "Associate", "None"], 
                                index=0)
    
    st.markdown("**Yêu cầu kỹ năng (Nhập tên kỹ năng và level trong ngoặc)**")
    st.caption("Ví dụ: Python (Senior), Docker (Basic)")
    
    tech_skills = st.text_area("Programming Languages & Frameworks", 
                              value="Python (Intermediate), FastAPI (Basic), SQL (Good)")
    
    languages = st.multiselect("Ngoại ngữ yêu cầu", 
                              ["English", "Japanese", "Korean", "Chinese", "French", "Dutch", "German", "Arab"], 
                              default=["English"])
    
    return {
        "job_title": job_title,
        "required_experience_years": exp_years,
        "education_level": edu_level,
        "programming_languages": [x.strip() for x in tech_skills.split(',') if x.strip()],
        "foreign_languages": languages
    }

def render_upload_section():
    """Khu vực upload file"""
    st.subheader("2. Upload CV Ứng viên")
    uploaded_file = st.file_uploader("Chọn file CV (PDF, PNG, JPG)", type=["pdf", "png", "jpg", "jpeg"])
    return uploaded_file

def render_results(cv_data, score, breakdown, ai_feedback):
    """Hiển thị kết quả phân tích"""
    st.divider()
    st.header("📊 Kết quả Đánh giá")
    
    # 1. Score Metrics
    # Đảm bảo breakdown.get() gọi đúng key tiếng Anh đã sửa ở ScoringService
    col1, col2, col3, col4,col5 = st.columns(5)
    col1.metric("Tổng điểm Match", f"{score}/100", delta_color="normal")
    col2.metric("Kỹ năng", breakdown.get("Skills", "0/50"))
    col3.metric("Kinh nghiệm", breakdown.get("Experience", "0/30"))
    col4.metric("Học vấn", breakdown.get("Education", "0/10"))
    col5.metric("Ngoại ngữ", breakdown.get("Foreign Language", "0/10"))
    # 2. AI Feedback
    st.subheader("🤖 Nhận xét từ AI")
    if ai_feedback:
        st.markdown(ai_feedback)
    else:
        st.warning("Chưa có nhận xét từ AI.")

    # 3. Extracted Info Detail
    with st.expander("ℹ️ Xem chi tiết thông tin trích xuất"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Họ tên:** {cv_data.get('full_name')}")
            # Xử lý hiển thị Email (List -> String)
            emails = cv_data.get('email', [])
            email_str = ", ".join(emails) if isinstance(emails, list) else emails
            st.markdown(f"**Email:** {email_str}")
            
            st.markdown(f"**SĐT:** {cv_data.get('phone_number')}")
            st.markdown(f"**Kinh nghiệm:** {cv_data.get('years_experience')} năm")
            
        with c2:
            st.markdown(f"**Bằng cấp:** {cv_data.get('education_level')}")
            
            # --- [LOGIC MỚI] GỘP SKILLS ---
            st.markdown("**Kỹ năng tìm thấy:**")
            
            all_skills_list = []
            
            # Ưu tiên lấy từ 'skills_display' (đã có format Senior/Junior)
            if 'skills_display' in cv_data and cv_data['skills_display']:
                source_dict = cv_data['skills_display']
                for category, skills in source_dict.items():
                    if isinstance(skills, list):
                        all_skills_list.extend(skills)
            
            # Nếu không có display, fallback về 'skills_detected' (raw scan)
            elif 'skills_detected' in cv_data and cv_data['skills_detected']:
                source_dict = cv_data['skills_detected']
                for category, skills in source_dict.items():
                    if isinstance(skills, list):
                        all_skills_list.extend(skills)

            # Hiển thị dạng Tags hoặc Text
            if all_skills_list:
                # Cách 1: Hiển thị dạng Text ngăn cách dấu phẩy
                st.info(", ".join(all_skills_list))
                
                # Cách 2 (Optional): Hiển thị dạng Tags đẹp hơn
                # st.markdown(" ".join([f"`{s}`" for s in all_skills_list]))
            else:
                st.text("Không tìm thấy kỹ năng cụ thể.")

            # Hiển thị Ngoại ngữ
            langs = cv_data.get('languages_detected', [])
            if langs:
                st.markdown(f"**Ngoại ngữ:** {', '.join(langs)}")

def render_history_table(history_data):
    """Hiển thị bảng lịch sử"""
    st.subheader("📜 Lịch sử đánh giá")
    if not history_data:
        st.info("Chưa có dữ liệu lịch sử.")
        return

    df = pd.DataFrame(history_data)
    # Chọn các cột cần hiển thị
    display_cols = ["timestamp", "candidate_name", "job_title", "total_score", "experience_years"]
    
    # Đổi tên cột cho đẹp
    df = df[display_cols].rename(columns={
        "timestamp": "Thời gian",
        "candidate_name": "Ứng viên",
        "job_title": "Vị trí",
        "total_score": "Điểm",
        "experience_years": "Kinh nghiệm (năm)"
    })
    
    st.dataframe(df, use_container_width=True)