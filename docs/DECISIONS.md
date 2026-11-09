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

## Renderer thứ hai: HyperFrames (11/2026)

**Vì sao.** Remotion tính phí theo ghế từ 4 nhân viên trở lên và một tác tử viết code Remotion cũng chiếm ghế. HyperFrames
(HeyGen, Apache-2.0, "không phí mỗi lần render hay ngưỡng thương mại" theo README) dựng video từ HTML + animation tua được,
render bằng Chrome headless + ffmpeg. Chọn cách **giữ nguyên mọi thứ trước bước render** (phân tích, proxy, giọng, phụ đề,
kế hoạch, bộ kiểm) và chỉ thay renderer: `project_to_hyperframes.py` đọc cùng `project.json`.

**Thiết kế.** Hợp đồng của HyperFrames là timeline GSAP tạm dừng; bộ vẽ `kit.js` thì là **hàm thuần của khung hình**
(`render(frame)`) đúng như component Remotion, nên công thức (easing, spring, camera, chuyển cảnh căn giữa) được port nguyên
và chuyển động không phụ thuộc cách HyperFrames tua. GSAP chỉ đẩy đầu phát qua một setter, vì `seek()` mặc định chặn callback.
Cảnh có `speed`/`ramp` được nướng bằng ffmpeg (HyperFrames chỉ phát tốc độ không đổi); âm thanh trộn sẵn một file
(`audio/mix.wav`) để không phụ thuộc tự động hoá âm lượng của HyperFrames.

**Đã kiểm thực tế** (Windows, Node 26, HyperFrames 0.9.26, Chrome hệ thống): `check` 0 lỗi (23 cảnh báo `line_unread` do phụ đề
theo giọng nhanh); video cafe 3 dài 28,5 s render ~55 s, 855 khung; độ ồn −16,3 LUFS và thời lượng giống bản Remotion; 6 khung
chuyển cảnh/phụ đề và 7 khung đồ họa so cạnh nhau giống hệt mắt thường; tốc độ 2x, 0,5x và ramp ra đúng số khung của cảnh.

**Chưa kiểm / hạn chế.** Chưa nghe âm thanh bản HyperFrames; chưa render đồ họa `pin`, `label`, `chart`, `specs`, `stat`,
`progress`, `lowerThird`, `image` song song với Remotion (đã nhìn ảnh HyperFrames, ảnh Remotion cùng khung không render
được trong lần chạy đó); không vẽ `magnifier`, `thumbs`, `compare`, `ranking`; `crossZoom` là mờ-phóng chứ không phải shader
WebGL; trên Windows HyperFrames dùng chụp màn hình (không phải đường BeginFrame chỉ có trên Linux) nên không đảm bảo giống
từng bit với bản render Linux; GSAP tải từ jsDelivr nên lần render đầu cần mạng.

**So sánh khung hình với Remotion** (cùng video cafe 3, 855 khung): SSIM 0,987, PSNR 36,3 dB; 852/855 khung trên 0,95. Lần đo
đầu chỉ 0,946 vì `perceptual-scale` của Remotion nội suy zoom theo **diện tích** (`√(a² + t(b² − a²))`) chứ không phải hàm mũ
như bản port đầu: đã sửa. Một clip đếm khung cho thấy hai renderer đọc đúng cùng khung nguồn. Thời gian render (cùng máy,
mỗi bên một lượt): HyperFrames 56 s (một lượt trước đó 122 s), Remotion 100 s.

**Hiệu ứng kiểu CapCut** (`+shake`, `+glitch`, `+rgb`, `+pulse`, `--look`) chỉ có ở HyperFrames; `plan_to_project.py` lưu
`scenes[].fx` và cảnh báo rằng Remotion bỏ qua. Bản đầu dùng `drop-shadow` để tách màu: sai (bóng của khung kín chỉ hiện ở
mép), nên đổi sang bộ lọc SVG tách kênh thật. Bẫy làm tròn: `round()` của Python làm tròn nửa về số chẵn còn
`Math.round` của JS làm tròn lên, đủ lệch một khung ở chuyển cảnh 9 khung: script dùng hàm làm tròn lên.

Tham khảo: `github.com/heygen-com/hyperframes`, `hyperframes.heygen.com` (html-schema, data-attributes, frame-adapters,
gsap-animation, shader-transitions, cli, rendering, faq), `heygen.com/research/html-to-video`. Danh mục kỹ thuật CapCut tổng
hợp từ mô tả công khai của ứng dụng (chợ ứng dụng, trang tính năng): tên và gói trả phí thay đổi.

## Keyframe camera (11/2026)

**Vì sao.** CapCut dựng chuyển động bằng keyframe (đặt giá trị tại mốc, đổi tiếp ở mốc khác, easing cho từng đoạn); bộ công cụ
chỉ có một cú push/pull/pan cho mỗi cảnh. Thêm `Camera: keys TIME=ZOOM[@X,Y][ roll DEG][ ease] ; …`: 2-4 khung hình có tên, mỗi đoạn
một easing, tiêu điểm là **điểm của cảnh quay** đặt vào giữa khung (khác `focus` là điểm gốc của phép scale). Hai renderer cùng đọc
`scenes[].camera.keys` (`ts` = giây kể từ điểm cắt; phân số của cảnh được đổi sang giây ở `plan_to_project.py`).

**Quyết định thiết kế.** Zoom nội suy theo **diện tích** như `perceptual-scale` của Remotion; tâm và roll nội suy tuyến tính; mép khung
không bao giờ lộ (tịnh tiến bị kẹp theo phần scale dư, trừ phần roll cần); 8 easing có tên thay vì tay cầm bezier tự do, vì đủ cho
quảng cáo ngắn và kiểm được; `back` (lố 8 %) chỉ dùng một lần mỗi video. Nguồn: trang keyframe và hướng dẫn PC của CapCut (các
công thức: Ken Burns = hai keyframe scale cách nhau vài giây, punch-in = hai keyframe sát nhau), nguyên tắc easing/anticipation/
overshoot trong thiết kế chuyển động (dùng tiết chế).

**Áp dụng cho 3 video cafe.** 27 cảnh có hành động (rót, thả túi, giơ sản phẩm, uống, mở đầu bàn ăn, kết thúc lùi lại) được gán keyframe;
tọa độ đọc từ ảnh chụp từng cảnh và **kiểm lại ở cuối chuyển động** (chủ thể phải nằm trong khung): vài điểm phải sửa (người ngồi
thấp hơn dự đoán, đầu bị cắt ở cảnh kết). Clip AI gốc 720×1280 nên zoom bị chặn ở ~1,38: bản đầu zoom 1,6-1,7 sẽ mờ; cảnh báo của
`plan_to_project.py` giờ nói rõ giới hạn là điểm ảnh của clip chứ không phải của proxy.

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
