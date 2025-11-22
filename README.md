# AI Audio Content Processor for Shadowing Practice

Một công cụ tự động xử lý nội dung audio/video từ YouTube để tạo tài liệu luyện shadowing. Sử dụng AI (Claude/GPT-4) để phân tích, phân đoạn và phân loại nội dung.

## Tính năng

- ✅ **Tự động tải audio từ YouTube**: Tải và chuyển đổi sang MP3 chất lượng cao
- ✅ **Chuyển đổi giọng nói thành văn bản**: Sử dụng OpenAI Whisper với timestamps chi tiết
- ✅ **Phân đoạn thông minh**: AI tự động chia transcript thành các cụm từ ngắn (5-15 từ) phù hợp cho shadowing
- ✅ **Phân tích metadata**: Tự động xác định độ khó, giọng điệu, tốc độ nói và phân loại nội dung
- ✅ **Phân tích âm thanh**: Đo tốc độ nói, tempo và các metrics khác
- ✅ **Xuất JSON**: Lưu toàn bộ dữ liệu dưới dạng JSON để tích hợp dễ dàng

## Cài đặt

### Yêu cầu
- Python 3.8+
- FFmpeg (để xử lý audio)
- API keys: Anthropic Claude và/hoặc OpenAI

### Bước 1: Clone repository
```bash
git clone <repository-url>
cd AI
```

### Bước 2: Cài đặt FFmpeg
**Windows:**
- Tải FFmpeg từ [ffmpeg.org](https://ffmpeg.org/download.html)
- Giải nén và thêm vào PATH

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

### Bước 3: Cài đặt Python packages
```bash
pip install -r requirements.txt
```

### Bước 4: Cấu hình API keys
Tạo file `.env` từ template:
```bash
copy .env.example .env
```

Chỉnh sửa `.env` và thêm API keys:
```
ANTHROPIC_API_KEY=your_claude_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

## Sử dụng

### Chạy chương trình
```bash
python model.py
```

Nhập URL YouTube khi được yêu cầu:
```
Enter YouTube URL: https://www.youtube.com/watch?v=...
```

### Kết quả

Chương trình sẽ tạo ra:
1. File MP3 audio trong thư mục `output/`
2. File JSON chứa:
   - Transcript đầy đủ với timestamps
   - Các segments đã được phân đoạn
   - Metadata (độ khó, giọng điệu, tags, etc.)
   - Audio metrics (tempo, thời lượng)

### Ví dụ output JSON
```json
{
  "source_url": "https://youtube.com/...",
  "title": "Video Title",
  "transcript": "Full transcript text...",
  "segments": [
    {"segment": "Hello everyone", "word_count": 2},
    {"segment": "Welcome to this lesson", "word_count": 4}
  ],
  "metadata": {
    "difficulty": "Intermediate",
    "accentType": "American",
    "speechRate": "Normal",
    "vocabulary_level": "B1",
    "suggestedTags": ["education", "english"]
  },
  "audio_metrics": {
    "tempo": 120.5,
    "duration_minutes": 5.2
  }
}
```

## Cấu trúc dự án

```
AI/
├── model.py              # Main processing script
├── requirements.txt      # Python dependencies
├── .env                  # API keys (không commit)
├── .env.example          # Template cho .env
├── README.md             # Documentation này
└── output/               # Thư mục chứa kết quả
    ├── *.mp3            # Audio files
    └── *_shadowing.json # Processed data
```

## Tùy chỉnh

### Thay đổi Whisper model
Trong `model.py`, bạn có thể chọn model khác:
- `tiny`: Nhanh nhất, độ chính xác thấp
- `base`: Cân bằng (mặc định)
- `small`: Chính xác hơn
- `medium`: Rất chính xác
- `large`: Chính xác nhất, chậm nhất

```python
result = await processor.create_from_youtube(url, whisper_model="small")
```

### Chọn AI provider
Mặc định sử dụng Claude. Để dùng OpenAI:
```python
segments = processor.ai_segment_transcript(transcript, use_claude=False)
metadata = processor.ai_analyze_metadata(transcript, metrics, use_claude=False)
```

## Xử lý lỗi

### Import errors khi chạy
Đảm bảo đã cài đặt tất cả dependencies:
```bash
pip install -r requirements.txt
```

### FFmpeg not found
Kiểm tra FFmpeg đã được cài và có trong PATH:
```bash
ffmpeg -version
```

### API errors
- Kiểm tra API keys trong file `.env`
- Đảm bảo có đủ credits trong tài khoản API

### Out of memory
Với video dài, giảm kích thước Whisper model xuống `tiny` hoặc `base`

## Lưu ý

- API calls tốn phí, hãy kiểm tra giá của Claude/OpenAI
- Whisper model `large` yêu cầu GPU hoặc RAM cao
- Tôn trọng bản quyền khi tải nội dung từ YouTube

## License

MIT License - Xem file LICENSE để biết thêm chi tiết

## Đóng góp

Mọi đóng góp đều được chào đón! Tạo issue hoặc pull request.

## Liên hệ

Nếu có câu hỏi hoặc gặp vấn đề, hãy tạo issue trên GitHub.
