# Quyết định, bẫy đã gặp, và nguồn

Mỗi mục ghi **điều gì đúng**, **vì sao biết**, và **chỗ nào còn chưa chắc**.

## Giấy phép — hai chỗ tốn tiền / có thể vi phạm

| Công cụ | Điều khoản | Nguồn |
|---|---|---|
| **Remotion** | Free cho cá nhân hoặc tổ chức vì lợi nhuận **tối đa 3 nhân viên**. Trên mức đó cần Company License **$25/tháng/người "who writes Remotion code themselves or using agentic coding tools"** → Claude viết code vẫn tính 1 ghế | `LICENSE.md` của repo remotion-dev/remotion; remotion.dev/docs/license/faq |
| **ElevenLabs** | Gói Free **"cannot be used for any commercial purpose"**; âm thanh tạo ngoài gói trả phí "(before or after) cannot be used commercially"; Free phải ghi nguồn | elevenlabs.io/docs/help-center/legal/can-i-publish-the-content-i-generate-on-the-platform |
| ffmpeg bản tĩnh | GPL. Dùng nội bộ, không phân phối lại | johnvansickle.com/ffmpeg |
| Whisper / faster-whisper | MIT | — |

Telemetry Remotion: render CLI phía máy chỉ gửi dữ liệu **khi đặt license key**; render phía trình duyệt luôn gửi
(IP, tên miền). Ghi lại để biết, **không phải** gợi ý né giấy phép — công ty đang đủ điều kiện Free.

## Bẫy kỹ thuật đã gặp

**1. `eleven_multilingual_v2` KHÔNG hỗ trợ tiếng Việt.** Tên "multilingual" gây hiểu nhầm; model chỉ có 29 ngôn
ngữ, không có `vi`. Có `vi`: `eleven_v4`, `eleven_v4_turbo`, `eleven_v3`, `eleven_turbo_v2_5`,
`eleven_flash_v2_5`. Cách biết: `GET /v1/models`, xem `languages`. Bản đầu của tài liệu này đã viết sai — sửa sau
khi hỏi API. Mặc định hiện tại: `eleven_turbo_v2_5` (đã thử: chấp nhận cài đặt, chạy được trên gói Free).

**2. Gói Free chỉ gọi được giọng `premade` qua API.** Giọng thư viện/professional (kể cả giọng Việt Ethan
trong tài khoản) trả HTTP 402 `paid_plan_required`.

**3. Whisper nghe sai tiếng Việt.** "túi xách" → "tui sách", "kiểu dáng" → "kiểu gián". Vô hình trong bản ghi,
chói mắt khi burn lên video. Cách xử lý: lấy **thời gian** từ Whisper, lấy **chữ** từ kịch bản gốc (ta đã biết
chính xác vì chính ta gửi cho TTS), ghép bằng so chuỗi bỏ dấu. Kiểm chứng: 171/171 từ khớp.

**4. faster-whisper 1.2.1 vỡ với PyAV mới** (`open() got an unexpected keyword argument 'metadata_errors'`).
Không ghim phiên bản; giải mã bằng ffmpeg ra mảng numpy rồi đưa thẳng cho Whisper.

**5. Nhãn cảm xúc `[excited]` chỉ model dòng v3 hiểu.** Model khác đọc to chữ "excited". `make_voiceover.py`
tự bỏ nhãn cho model không hỗ trợ; `align_captions.py` luôn bỏ nhãn khỏi chữ phụ đề.

**6. venv Python không mang sang máy khác được** (gắn cứng đường dẫn và phiên bản). Vì vậy `setup.sh` dựng
lại thay vì copy. Venv của Python là symlink tới Python hệ thống nên so `resolve()` không phân biệt được hai
cái — lỗi này đã bắt được nhờ chạy `selftest.sh` trên "máy mới" giả lập.

**7. Kho cache Hugging Face mới dùng `blobs/` chung**, nên `du` trên thư mục model báo 2,6MB trong khi model thật
462MB (symlink). Khi đóng gói phải `cp -L`.

## Số liệu ngách (16.242 video SAIZA tẩy mốc, 02/06/2025 → 03/11/2026)

Tái hiện bằng `docs/niche-data-queries.sql`. Đo được:
- Top 20% video theo view chiếm **95,1% GMV**; 80% còn lại trung bình **171 view**, nhưng GMV/1.000 view của họ
  còn *nhỉnh hơn* → nút thắt là **reach**, không phải lời chào hàng.
- CTR và tỉ lệ ra đơn đạt đỉnh ở **35–44 giây**; dưới 25s tệ nhất. Giữ nguyên khi chỉ xét KOC đã chứng minh.
  KOC giỏi chỉ làm video dưới 25s đúng ~1% số lần.
- **9 KOC tạo 59,3% GMV** trong ~2.900 người.

**Dữ liệu KHÔNG có:** retention / tỉ lệ xem hết, loại hook, nhịp cắt, âm thanh. Mọi nhận định về hook và nhịp
cắt trong skill là **thực hành nghề**, không phải số đo — skill gắn nhãn `[DATA]` / `[HYPOTHESIS]` để phân biệt.

Quy tắc "cảnh ≤ 4 giây" và "hook ≤ 3 giây" đến từ thực hành short-form phổ biến, **không** rút ra từ dữ liệu này.

## Kịch bản hiện hành của campaign đang chứa claim vi phạm

Doc Lark *"TQA 6 - REVIEW - GIỌNG ADAM"* (21 kịch bản). Các câu cần viết lại — đối chiếu chính sách TikTok Shop
trong `references/platform-specs.md`:

| Câu | Vấn đề |
|---|---|
| "Không hiệu quả anh gửi tiền lại liền" · "Hổng sạch hổng lấy tiền" | Cam kết hoàn tiền / đảm bảo kết quả |
| "diệt khuẩn", "diệt nấm mốc" | Sản phẩm tẩy rửa không được tuyên bố diệt/ức chế vi khuẩn, **nấm**, virus |
| "tẩy sạch mọi vết bẩn" · "sạch tinh như mới" | "Giải quyết mọi vấn đề" / phục hồi tức thì |
| "ngay lập tức" | Hiệu quả tức thì |
| "tốt nhất thị trường" | Cấp so sánh tuyệt đối không có bằng chứng |

Câu hoàn tiền nằm trên **một trong những video doanh thu cao nhất** của campaign. Chạy được ≠ hợp lệ.
Đồng thời, TikTok Shop yêu cầu **kịch bản gốc cho từng video** — phát nguyên một kịch bản cho nhiều KOC là rủi ro.

## Công cụ đã khảo sát

| Công cụ | Kết luận |
|---|---|
| **Kinocut** (github.com/KyaniteLabs/kinocut) — MCP server bọc ffmpeg, 205 tool, Apache-2.0 | Có thật (243 sao). **Chưa cài, chưa thử.** Ứng viên nếu muốn lớp kiểm tra giữa Claude và ffmpeg |
| auto-editor | Tự cắt đoạn im lặng. Hợp bước làm sạch footage thô. Chưa dùng |
| MoviePy, editly, OpenTimelineIO | MoviePy chậm; editly bỏ bê từ 05/2025; OTIO chỉ khi cần xuất sang Premiere/DaVinci |

⚠️ Một kết quả tìm kiếm quảng cáo repo `kyanitelabs/mcp-video` "87 tool" — repo đó **không tồn tại** (API GitHub
trả 404; tên thật là KyaniteLabs/kinocut). Thư mục MCP bên thứ ba ghi số sao mâu thuẫn nhau. **Luôn kiểm tra repo
qua API GitHub trước khi tin.**
