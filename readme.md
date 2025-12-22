# AI Powered CV Scoring System 

Hệ thống đánh giá và chấm điểm CV tự động sử dụng:
- **OCR:** PaddleOCR & PDF2Image để đọc CV (PDF/Ảnh).
- **Matching:** Thuật toán so khớp từ khóa và ngữ cảnh (Context-aware) để xác định Level (Junior/Senior).
- **LLM:** Sử dụng Local LLM (Qwen2.5-7B) để viết nhận xét chi tiết như chuyên gia tuyển dụng.
- **UI:** Giao diện Streamlit trực quan.

## Tính năng
1. **Phân tích CV:** Trích xuất thông tin cá nhân, kỹ năng, kinh nghiệm, bằng cấp.
2. **Chấm điểm:** So sánh CV với JD (Job Description) theo trọng số:
   - Kỹ năng (50%)
   - Kinh nghiệm (30%)
   - Học vấn (10%)
   - Ngoại ngữ (10%)
3. **AI Feedback:** Nhận xét điểm mạnh/yếu và đề xuất phỏng vấn.
4. **Lịch sử:** Lưu trữ kết quả đánh giá.

## Cài đặt

1. **Yêu cầu hệ thống:**
   - Python 3.10+
   - Poppler (để xử lý PDF)
   - RAM >= 8GB (để chạy Local LLM)

2. **Cài đặt thư viện:**
   ```bash
   pip install -r requirements.txt

## Cấu trúc dự án
app.py: Main application.
services/: Logic xử lý (Parser, Scorer, History).
models/: Quản lý AI Models (OCR, LLM, Embedding).
ui/: Thành phần giao diện.
core/: Cấu hình hệ thống.