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
Nhịp "3–4 giây một cảnh, chuyển cảnh mượt" là **yêu cầu của khách** (11/2026) — tìm trên web không có nguồn đo nào.

## Kiến trúc dựng (11/2026)

**Một bảng kế hoạch → `project.json` → một composition Remotion.** Không có nội dung video nào nằm trong
code: đổi video là đổi kế hoạch. Lý do:
- Kênh Mike Like Design (TikTok) chỉ ra rằng sửa video bằng cách gõ prompt cho từng thay đổi vừa lâu vừa tốn
  token; một bộ skill/workflow cố định + dữ liệu là cách làm nhanh và rẻ.
- `browser-use/video-use` (MIT) làm tương tự: tác tử làm việc trên transcript cấp từ chứ không trên khung hình.
- `remotion-dev/skills` (quy tắc chính thức của Remotion cho tác tử AI): mọi chuyển động theo
  `useCurrentFrame()`, transform trên lớp bọc, `perceptual-scale` khi phóng.

Các thành phần đã chọn và nguồn tham khảo:

| Phần | Lựa chọn | Nguồn |
|---|---|---|
| Chuyển cảnh | `@remotion/transitions` (fade, slide, wipe, iris, pushCut, flip, crossZoom) + 3 cái tự viết (zoomThrough, blurDissolve, whip); căn giữa điểm cắt để không lệch giọng | Tài liệu Remotion; HyperFrames (Apache-2.0) cho thông số whip/blur |
| Chữ | Be Vietnam Pro + Playfair Display Italic (chữ nhấn) + Anton (số); 5 kiểu tiêu đề; không khung viền | Siêu dữ liệu Google Fonts (đã kiểm subset `vietnamese`); ảnh mẫu của kênh Mike Like Design |
| Bố cục | Dải trên đầu / mặt bỏ trống / dải ngực / dải phụ đề; tránh thanh nút bên phải | Đo của bên thứ ba (TikTok không công bố); Remotion safe-zone overlay |
| Góc máy | push/pull/pan/hold + punch-in theo từ khoá, phóng perceptual, không reset ở điểm cắt | StudioBinder, iart-ai/tiktok-video-skills (MIT), tài liệu Remotion |
| Bắt nhịp | Neo đồ hoạ vào từ (`@"từ"`), cắt ở khoảng lặng, báo cáo đồng bộ tự động | Hướng dẫn phụ đề tiếng Việt của Netflix (17 ký tự/giây), video-use |

`iart-ai` = bộ skill MIT `iart-ai/tiktok-video-skills` và `ecommerce-video-skills` (Remotion). Đã đọc, lấy
thông số; không chép nguyên văn vì có vài con số không có nguồn ("87% quyết định trong 3 giây").

**Đã kiểm thực tế trên máy Windows của dự án:** render shader (`crossZoom`, light leak) với GL `angle`; render
đủ 33,7 giây với 12 cảnh, 17 lớp đồ hoạ, phụ đề karaoke; audio và hình dài bằng nhau.

**Chưa kiểm:** chưa nghe/xem trọn video cuối trên điện thoại thật; vùng an toàn chưa đối chiếu bằng bài đăng
thử; chưa render từ proxy 2160×3840 (punch-in > 1,15× sẽ mờ trên proxy 1080p).

## Mở rộng đa thể loại (11/2026)

**Vì sao playbook.** Bộ công cụ ban đầu chỉ cho review sản phẩm tẩy rửa: hằng số nhịp (2,5–4 s, 25–45 s), cấu trúc
HOOK→PROBLEM→…→REVEAL, loại shot STAIN/POUR/SOAK, camera và chuyển cảnh đều nằm cứng trong script. Giờ mọi thứ phụ thuộc
thể loại là dữ liệu trong `playbooks/<id>.json`, có 8 thể loại và 7 biến thể. Luật của khách Phương (cảnh 3–4 s, chuyển
cảnh mềm, không chữ trong khung) là house style của `product-demo`, không áp cho ẩm thực hay montage (ở đó cảnh 1–2 s theo
beat là chuẩn nghề) — nếu cùng khách làm thể loại khác thì nói rõ với khách.

**Nguyên tắc "kỹ thuật phải được dùng".** `playbook.py check` (selftest chạy) báo lỗi nếu một thành phần đồ họa, grade,
theme hay kiểu phụ đề không được playbook nào dùng; mỗi khóa trong JSON đều có script đọc (bảng ở `playbooks/README.md`);
khung kế hoạch do chính playbook sinh ra phải qua luật nhịp của chính nó ở cả hai đầu khoảng thời lượng lý tưởng.

**Bẫy đã gặp khi làm (đã đo, đã sửa):**

| Bẫy | Hậu quả | Cách xử lý trong code |
|---|---|---|
| Cân trắng "gray world" trên mọi điểm ảnh | Chậu nhựa xanh lá trong clip thật đọc thành ám xanh +0,10 | Chỉ đo điểm ảnh gần trung tính; < 5% khung là trung tính thì không đoán |
| Đo nhiễu bằng PSNR so với bản khử nhiễu | Bê tông có vân (ban ngày, sạch) đọc 43,6 dB như "nhiễu" | Khử nhiễu chỉ khi < 40 dB, hoặc < 44 dB và cảnh tối |
| `hqdn3d` ở khung đầu tiên | Gần như không lọc → PSNR khung đầu 55 dB so với 41 dB các khung sau | Bỏ khung đầu khi đo |
| Bộ lọc RGB ngay sau `vidstabtransform` | ffmpeg 7.0 segfault (exit −11) | Chèn `scale=iw:ih` |
| Chuỗi màu từng bộ lọc trên 4K60 | 113 s cho 6 s footage | Gộp cân trắng + phơi sáng + grade vào LUT 3D (Hald 64³): 45 s, sai khác 46 dB PSNR |
| `grayworld` của ffmpeg | Chậm 23× thời gian thực, xuất float | Không dùng |
| Hai job ffmpeg 4K chạy song song | Máy 14 GB hết RAM, tiến trình bị giết | Tài liệu: một job nặng một lúc trên máy nhỏ |
| Nền nhiễu = phân vị 10% | Giọng TTS ít khoảng lặng: rơi vào mép từ (−47 dB) → "khử ồn" file sạch, nền lên −31 dB | Phân vị 5% (các khoảng lặng thật, −90 dB) |
| Nén ngưỡng cố định −24 dB | Giọng to bị nén 10 dB, bước cân mức kéo nhiễu lên theo | Ngưỡng = mức giọng − 8 dB, thêm expander nhẹ |
| `afftdn`, `alimiter`, `loudnorm` | Trễ 25 ms; tự tăng gain; giới hạn mẫu chứ không phải true peak; linear âm thầm chuyển dynamic | Xem `references/audio-processing.md` |
| Phụ đề hiện từng chữ | Nghiên cứu ASSETS 2019/2021: người xem đọc trước, câu 6–12 từ dễ hơn từng từ | Kiểu `pop` hiện cả cụm ≤ 5 từ, tô từ đang nói |
| Animate `playbackRate` trong Remotion | Không hoạt động (docs Remotion) | Ramp đọc lại khung nguồn từng khung trong `<Freeze>`; đã kiểm trên clip có đồng hồ |

**Nghiên cứu (07/11/2026):** ba hướng song song — kỹ thuật dựng theo 12 thể loại (có luật VN: Luật Quảng cáo 75/2025
hiệu lực 01/01/2026, Luật KDBĐS 2023, NĐ 339/2026 thay NĐ 16/2022, cấm "trị" trong mỹ phẩm, cảnh báo TPBVSK), xử lý âm thanh
+ thông số nền tảng (TikTok/Instagram không công bố chuẩn LUFS; vùng an toàn quảng cáo Reels của Meta 14% trên / 35% dưới /
6% hai bên; tín hiệu xếp hạng Mosseri 01/2025), xử lý hình (tự đo trên ffmpeg 7.0, clip tổng hợp và một clip iPhone thật
4K60). Năm con số hay được trích dẫn không tìm thấy nguồn gốc: liệt kê ở `references/platforms.md` §3 để đừng lặp lại.

**Kiểm thêm sau khi người dùng giao "tự quyết, làm tốt nhất" (07/11/2026):**

| Hạng mục | Cách kiểm | Kết quả |
|---|---|---|
| HDR | Bản HLG/BT.2020 10-bit chuyển từ clip iPhone thật | Công thức `hable` phổ biến làm tối 30% (luma 90 so với 128) → đổi sang `mobius`: 125 / bão hòa 11,6 so với 11,6 của bản gốc |
| Cảnh đêm | Clip thật làm tối + nhiễu cảm biến | Đo ra "exposure, denoise"; proxy nâng bóng tối, giảm hạt rõ |
| Nhận diện giọng trên camera | Cùng hình, một bản tiếng môi trường, một bản có giọng | no / yes đúng |
| Rung/di chuyển | Clip thật quay tripod | 0,0 / 0,0 — đúng là máy đứng yên |
| Beat trên nhạc thật | 3 bản CC0 OpenGameArt, đối chiếu khoảng cách onset | Bộ dò Python thuần sai 2/3 bài, bản "tương phản" sai 2/3; bản numpy (spectral flux + tempogram + DP) đúng 97 và 104 bpm, 88–95% phách trùng onset; bài nhịp ghép ra 73 bpm (110 cũng hợp lý) |
| Âm thanh đầu ra | Render 9 s có giọng + nhạc thật + SFX, master, đo | −14,0 LUFS, đỉnh −1,4 dBTP; lời ~−11,7 LUFS, nhạc trong khoảng lặng ~−20,1 LUFS (thấp hơn ~8 LU) |
| Eval `routes-real-estate-tour` | Agent mới, chỉ có skill đã cài, chấm theo 5 grader | Đạt 5/5: playbook `real-estate`, lộ trình tham quan, cắt theo nhạc, hook ban công 1,5 s, dữ kiện đúng nguyên văn, không bịa pháp lý, checker PASS, nêu tuân thủ. Lộ lỗi: `suggest` nghiêng về `:voiceover` vì chữ "môi giới" → biến thể giờ cộng từ khoá của bản gốc, bỏ từ khoá bị phủ định ("không có giọng đọc") |
| Eval `asks-when-ambiguous` | Như trên, 2 grader | Đạt 2/2: nhận ra hai hướng (talking-head / food-fnb:review), hỏi đúng 3 câu có mặc định. Lộ lỗi: "giày" khớp nhầm "50 giây" khi bỏ dấu → so khớp có dấu, theo ranh giới từ; thêm từ khoá "đứng nói" cho talking-head; báo "Close call" giữa hai thể loại |
| Cài đặt máy này | `setup.sh` (dùng mô hình Whisper có sẵn trong cache Hugging Face, không tải lại) | `selftest.sh` qua toàn bộ, `--render` qua |

**Vẫn chưa kiểm:** footage thật quay cầm tay, ban đêm, góc rộng 0,5×, HDR quay thật; nhạc có tempo thay đổi; tai người
chưa nghe đầu ra nào (bản `mix_final_phone.mp4` đã gửi để nghe thử).

## Kịch bản hiện hành của campaign đang chứa claim vi phạm

Doc Lark *"TQA 6 - REVIEW - GIỌNG ADAM"* (21 kịch bản). Các câu cần viết lại — đối chiếu chính sách TikTok Shop
trong `references/claims-and-compliance.md` §2:

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
| browser-use/video-use (MIT) | Biên tập theo transcript, cắt ở khoảng lặng ≥ 400 ms. Đã lấy quy tắc; bước phiên âm của nó cần ElevenLabs Scribe (trả phí) |
| heygen-com/hyperframes (Apache-2.0) | HTML + GSAP, không phải React. Lấy quy tắc chuyển động/phụ đề, không lấy code. Dự án HyperFrames cũ đã xoá khỏi repo |
| remotion-dev/skills | Quy tắc chính thức cho tác tử; không thấy giấy phép nên chỉ tham chiếu, không chép |
| MoviePy, editly, OpenTimelineIO | MoviePy chậm; editly bỏ bê từ 05/2025; OTIO chỉ khi cần xuất sang Premiere/DaVinci |

⚠️ Một kết quả tìm kiếm quảng cáo repo `kyanitelabs/mcp-video` "87 tool" — repo đó **không tồn tại** (API GitHub
trả 404; tên thật là KyaniteLabs/kinocut). Thư mục MCP bên thứ ba ghi số sao mâu thuẫn nhau. **Luôn kiểm tra repo
qua API GitHub trước khi tin.**
