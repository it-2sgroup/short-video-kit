# Legacy — HyperFrames + edge-tts

Đây là các dự án làm **trước khi đổi stack** sang Remotion + ElevenLabs. Giữ lại làm tham chiếu,
không phải phần của luồng hiện tại.

| Thư mục | Là gì |
|---|---|
| `aff-video/` | Video aff túi xách 53s dọc 1080x1920, dựng bằng HyperFrames. `generate_index.py` sinh `index.html` từ `captions.json` — mẫu hay để tham khảo cách ánh xạ phụ đề thành các lớp theo thời gian |
| `aff-video-45s/` | Script tạo giọng bằng edge-tts (`gen_tts.py`) và ghép audio (`build_audio.py`) |
| `demo-video/` | Bản thử đầu tiên, 8s |

**Đã bỏ:** video render (~21MB/bản), `node_modules`, thư mục `.hyperframes/`, file audio.
Dựng lại video thì dùng `npx hyperframes render` trong thư mục dự án (cần Node 22 + ffmpeg).

**Cảnh báo về `gen_tts.py`:** edge-tts gọi một endpoint không chính thức của Microsoft Edge.
Điều khoản dùng thương mại của nó **chưa được kiểm tra** — chỉ nên dùng làm bản nháp/nghe thử.
