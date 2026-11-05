---
name: skill-short-video-editing
description: "Skill dựng video ngắn TikTok Shop đã build xong, có file .skill cài được; chứa số liệu thật từ 16.242 video SAIZA"
metadata: 
  node_type: memory
  type: project
  originSessionId: 1956b66b-81a6-461a-932f-81e9c4f71b76
---

Skill `short-video-editing` (tiếng Anh) đã build + kiểm thử xong 04/11/2026, đóng gói tại
`~/Documents/sismo-project/skills/short-video-editing.skill` (15 file). Nguồn ở
`~/Documents/sismo-project/skills/short-video-editing/`.

**Stack đã chốt 05/11/2026: ffmpeg (cắt/ghép) + Remotion (đồ hoạ) + ElevenLabs (giọng)
+ Whisper (canh giờ chữ).** Bỏ HyperFrames khỏi skill. Remotion free vì công ty 2 người
(ngưỡng là 3 nhân viên; trên ngưỡng là $25/ghế/tháng, và dùng AI viết code vẫn tính 1 ghế).

4 script chạy được: `inspect_footage.py` (ffprobe soi clip thô), `make_voiceover.py`
(ElevenLabs, 1 file/câu, key ở `.env.local` sẵn có), `align_captions.py`, `pacing_checker.py`.

**Bẫy đã gặp và đã xử lý:**
- faster-whisper 1.2.1 vỡ với PyAV mới (`metadata_errors` bị bỏ) → giải mã bằng ffmpeg ra
  numpy, bỏ hẳn PyAV.
- **Whisper nghe sai tiếng Việt**: "túi xách"→"tui sách", "kiểu dáng"→"kiểu gián". Nên
  `align_captions.py` lấy *thời gian* từ Whisper nhưng *chữ* từ kịch bản gốc, khớp bằng cách
  bỏ dấu + so chuỗi. Đã kiểm chứng: 171/171 từ khớp, SRT không chồng lấn.
- Bảng cảnh có cột Source/In (timecode nguồn) tách khỏi Start/End (vị trí timeline).

**Bộ kit chuyển máy: `~/Documents/sismo-project/short-video-kit/` + `short-video-kit.tar.gz`** — gồm skill,
`setup.sh`/`selftest.sh`, ffmpeg + model Whisper đi kèm (chạy offline), `.env.local` (key thật), docs,
SQL tái hiện số liệu. Đã kiểm thử trên "máy mới" giả lập (HOME giả + PATH cắt): setup + 5 nhóm selftest đều qua.
Chưa dựng thử dự án Remotion nào; skill chưa được đánh giá lại sau khi đổi stack.

**ElevenLabs (phát hiện 05/11/2026) — đừng lặp lại:**
- `eleven_multilingual_v2` KHÔNG có tiếng Việt (29 ngôn ngữ, không có `vi`) dù tên "multilingual". Có `vi`:
  eleven_v4, v4_turbo, v3, turbo_v2_5, flash_v2_5. Hỏi `GET /v1/models` thay vì đoán.
- Tài khoản đang gói **free**, còn ~1/10.000 credit, **reset 12/11/2026**. Free **không dùng thương mại**
  (trang trợ giúp chính thức), và âm thanh tạo ngoài gói trả phí không thương mại hoá được kể cả sau khi nâng cấp.
- Free chỉ gọi được giọng `premade`; giọng Việt Ethan (EcENCamMHdzIoMysqdsv) trả HTTP 402.
- Nhãn `[excited]`… chỉ v3 hiểu; model khác đọc to. Kịch bản Adam trong Lark có nhãn kiểu `[ persuasive]`.
- Mình đã tiêu ~17 credit để thử model (số dư lúc đó chỉ ~18).
- `make_voiceover.py` có `--quota` và `--dry-run`; tự từ chối trước khi tiêu nếu thiếu credit.

**Số liệu thật rút từ 16.242 video SAIZA tẩy mốc** (Supabase SISMO-KHACH HANG, bảng `videos`,
product_id 1731438356080002524) — đây là phần giá trị nhất, nằm trong
`references/niche-winning-patterns.md`:
- Top 20% video theo view chiếm **95,1% GMV**; nhóm dưới trung bình 171 view. GMV/1k view của
  nhóm dưới còn *nhỉnh hơn* → **nút thắt là reach, không phải lời chào hàng**.
- CTR và tỉ lệ ra đơn đạt đỉnh ở **35–44 giây** (3,37% / 26,6%); dưới 25s tệ nhất mọi mặt.
  Kiểm soát theo KOC vẫn giữ đỉnh 35–44s; KOC giỏi chỉ quay dưới 25s đúng 1% số lần.
- **9 KOC tạo 59,3% GMV** / ~2.900 người. Đăng 642 video (nhiều nhất) chỉ được 1,71% GMV.

**Cảnh báo quan trọng:** kịch bản hiện hành của campaign (doc Lark "TQA 6 - REVIEW - GIỌNG ADAM")
chứa nhiều claim vi phạm chính sách TikTok Shop — "không hiệu quả gửi tiền lại", "hổng sạch hổng
lấy tiền", "diệt khuẩn", "sạch mọi vết bẩn", "ngay lập tức". Câu hoàn tiền nằm trên một trong
những video doanh thu cao nhất. Chạy được ≠ hợp lệ. Bảng viết lại ở `references/platform-specs.md` §7.

Kết quả kiểm thử: **15/15 tiêu chí có skill vs 8/15 không skill**. Điểm khác biệt lớn nhất không
phải nội dung (bản không skill viết khá tốt, còn dẫn luật quảng cáo VN) mà là **kế hoạch dựng
máy kiểm tra được** — `scripts/pacing_checker.py` parse được bảng cảnh, bản không skill viết
timestamp trong văn xuôi nên không ai verify được, và có cảnh dài 5,5–6s vi phạm trần 4 giây.

Liên quan: [[nhat-ky-pipeline-video-koc-file]], [[supabase-sismo-khachhang-cam-bay]],
[[sismo-vs-saiza-phan-biet]]
