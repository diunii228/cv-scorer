# services/llm_service.py

def generate_feedback_local(cv_data, jd_parsed, match_score, llm_model):
    """
    Hàm nhận dữ liệu CV + JD và yêu cầu AI viết nhận xét.
    """
    if not llm_model:
        return "⚠️ AI chưa sẵn sàng (Model chưa tải xong hoặc lỗi)."

    # 1. Chuẩn bị danh sách kỹ năng để đưa vào prompt
    skills_text = "Không tìm thấy"
    if cv_data.get('skills_extracted'):
        # Chuyển dict skills thành chuỗi dễ đọc
        # Ví dụ: Python: Senior, Java: Junior
        lines = []
        for cat, items in cv_data['skills_extracted'].items():
            if items:
                skills_in_cat = ", ".join([f"{k} ({v})" for k, v in items.items()])
                lines.append(f"- {cat}: {skills_in_cat}")
        if lines:
            skills_text = "\n".join(lines)

    # 2. Xây dựng Prompt (Kịch bản cho AI)
    system_prompt = (
        "Bạn là một chuyên gia tuyển dụng HR (Recruiter) chuyên nghiệp và sắc sảo. "
        "Nhiệm vụ của bạn là đánh giá mức độ phù hợp của ứng viên với công việc."
    )
    
    user_prompt = f"""
    Hãy viết nhận xét đánh giá ngắn gọn (khoảng 150 từ) bằng Tiếng Việt cho hồ sơ sau:

    === THÔNG TIN CÔNG VIỆC (JD) ===
    - Vị trí: {jd_parsed.get('job_title', 'N/A')}
    - Yêu cầu kinh nghiệm: {jd_parsed.get('required_experience_years')} năm
    - Yêu cầu kỹ năng: {', '.join(list(jd_parsed.get('programming_languages', {}).keys()))}

    === THÔNG TIN ỨNG VIÊN ===
    - Tên: {cv_data.get('full_name', 'Ứng viên')}
    - Số năm kinh nghiệm: {cv_data.get('years_experience')} năm
    - Bằng cấp: {cv_data.get('education_level')}
    - Kỹ năng thực tế tìm thấy trong CV:
    {skills_text}
    
    === ĐIỂM SỐ HỆ THỐNG ===
    - Tổng điểm phù hợp: {match_score}/100

    === YÊU CẦU ĐẦU RA ===
    Hãy đưa ra nhận xét theo cấu trúc Markdown:
    1. **Đánh giá chung**: Nhận xét sơ bộ về mức độ phù hợp.
    2. **Điểm mạnh**: Nêu 2-3 điểm nổi bật khớp với JD.
    3. **Điểm yếu/Rủi ro**: Nêu những kỹ năng còn thiếu hoặc kinh nghiệm chưa đủ.
    4. **Kết luận**: Có nên mời phỏng vấn không? (Yes/No/Consider).
    """

    # 3. Gửi cho Model xử lý
    try:
        response = llm_model.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=600,  # Độ dài tối đa câu trả lời
            temperature=0.7  # Độ sáng tạo (0.7 là cân bằng)
        )
        return response['choices'][0]['message']['content']
        
    except Exception as e:
        print(f"❌ Lỗi khi sinh văn bản AI: {e}")
        return "Xin lỗi, đã xảy ra lỗi khi tạo nhận xét từ AI."