# Cấu trúc repo, công cụ và kỹ thuật

Tài liệu này trả lời ba câu hỏi: **mỗi thư mục và file làm gì**, **repo dùng công cụ nào**, và **dùng kỹ thuật
nào để video khớp tiếng, mượt và không lặp footage**. Cách làm việc từng bước nằm ở
[`WORKFLOW.md`](WORKFLOW.md); lý do chọn công cụ và các bẫy đã gặp nằm ở [`DECISIONS.md`](DECISIONS.md).

## 1. Repo này làm gì

Bộ công cụ dựng video ngắn dọc (TikTok, TikTok Shop, Reels, Shorts; 10–90 giây) **cho nhiều thể loại**: review
sản phẩm, bất động sản, ẩm thực, nói trước camera, hướng dẫn, thời trang/làm đẹp, montage sự kiện/du lịch, khuyến
mãi. Mọi thứ phụ thuộc thể loại nằm trong **playbook**; phần dùng chung (vùng an toàn, căn phụ đề, render, chính
sách bản quyền) nằm ở `references/` và `scripts/`. Một video được mô tả **một lần** bằng *kế hoạch dựng* (Markdown
hai bảng, ghi `**Playbook:**` ở đầu), qua các cổng kiểm tra và được render bởi **một** composition Remotion.

```
clip thô ─► inspect_footage --measure + contact_sheet ─┐
yêu cầu người dùng ─────────────────────────────────────┴─► playbook.py suggest/show ─► playbook
clip thô ─► prepare_footage (HDR, khung, khử nhiễu, chống rung, cân trắng, phơi sáng, grade) ─► proxy
giọng ─► trim_voice (cắt câu / jump cut) ─► process_audio voice ─► align_captions ─► captions.srt + words.json
nhạc  ─► process_audio music ─► suggest_cuts --music (beat)          giọng ─► suggest_cuts (chỗ lặng)
            ─► playbook.py skeleton ─► plan_scenes ─► edit-plan.md (Scenes + Overlays)
            ─► pacing_checker + footage_overlap_checker (cổng kiểm tra theo playbook)
            ─► plan_to_project ─► project.json + báo cáo bắt nhịp ─► Remotion ─► process_audio master ─► contact_sheet
```

## 2. Cây thư mục

```
short-video-kit/
├── CLAUDE.md                 Chỉ dẫn cho Claude khi mở repo (Claude tự đọc đầu tiên)
├── README.md                 Giới thiệu, cài đặt, cách dùng (tiếng Anh, chuẩn repo quốc tế)
├── setup.sh · selftest.sh    Cài đặt và kiểm tra máy
├── requirements.txt          Thư viện Python (faster-whisper, numpy, onnxruntime)
├── requirements-ocr.txt      Thư viện OCR tùy chọn (rapidocr, opencv), cài bằng setup.sh --ocr
├── .env.example              Mẫu file khóa ElevenLabs (không chứa khóa)
├── .gitignore · .gitattributes
├── docs/                     Tài liệu cho người đọc
├── samples/                  Dữ liệu mẫu cho selftest
└── skill/short-video-editing/   ← chính là "skill" mà Claude nạp
    ├── SKILL.md              Quy tắc chung + quy trình 9 bước (phân tích → playbook → dựng → master → báo cáo)
    ├── playbooks/            Mỗi thể loại một JSON (luật máy đọc) + một MD (tay nghề); README = chọn và thêm thể loại
    ├── references/           Tri thức dùng chung theo chủ đề (Claude đọc khi cần)
    ├── scripts/              Công cụ dòng lệnh Python
    ├── assets/               Mẫu kế hoạch + template Remotion
    └── evals/                Bộ ca kiểm tra chất lượng skill
```

## 3. Gốc repo

| File | Chức năng |
|---|---|
| `CLAUDE.md` | Chỉ dẫn cho Claude: kiểm tra máy đầu phiên, các bước cài đặt, quy trình khi người dùng nhờ dựng video, việc phải hỏi người dùng (tải về, gói ElevenLabs, giấy phép Remotion), các bài học đã trả giá. |
| `README.md` | Tổng quan, yêu cầu hệ thống, cài đặt (có Windows), cách dùng, giấy phép bên thứ ba, hạn chế đã biết. |
| `setup.sh` | Cài mọi thứ vào `$HOME`: venv Python, thư viện, mô hình Whisper (~460 MB), khóa ElevenLabs (nếu có `.env.local`), chép skill vào `~/.claude/skills`. Chạy lại an toàn. Tùy chọn: `--check` (chỉ báo cáo), `--set-key` (nhập khóa ẩn), `--no-model`, `--person-model` (tải thêm model tách người 168 MB cho quy trình agency; hỏi người dùng trước), `--ocr` (RapidOCR + OpenCV ~85 MB cho analyze_reference.py; hỏi trước), `--all` (mọi thứ tùy chọn tải được không cần gõ: OCR, model tách người, ffmpeg tĩnh), `--no-skill`, `--download-ffmpeg` (Linux), `--package` (đóng gói `.skill` cho app desktop). |
| `selftest.sh` | 13 nhóm kiểm tra không tốn credit: công cụ; soi clip; playbook (mọi playbook/biến thể hợp lệ, khung của nó qua luật nhịp của chính nó, mọi thành phần/grade/theme/kiểu phụ đề đều được ít nhất một playbook dùng) và luật nhịp theo playbook; căn phụ đề; khóa ElevenLabs; biên dịch kế hoạch (review sản phẩm + tour BĐS có speed ramp và đồ hoạ thông tin); trùng footage (tính cả cảnh tua nhanh); cắt theo chỗ lặng và theo beat; cắt giọng và jump cut; bảng khung hình; dựng khung dự án; hiệu ứng âm thanh; làm sạch giọng + master; đo và hiệu chỉnh footage. `--render [DIR]` thêm nhóm 14: typecheck template và render ảnh tĩnh (cả đồ hoạ thông tin). |
| `requirements.txt` | `faster-whisper==1.2.1`, `numpy`, `onnxruntime`. |
| `requirements-ocr.txt` | `rapidocr` và `opencv-python-headless` (ghim phiên bản). Tùy chọn. `selftest.sh` nhóm 1 kiểm mọi gói bên thứ ba mà scripts import đều có trong một file `requirements*.txt`. |
| `.env.example` | Chỉ có dòng `ELEVENLABS_API_KEY=`. Khóa thật nằm ở `.env.local` (bị `.gitignore` chặn) hoặc `~/.config/short-video-kit/env`. |
| `.gitignore` | Chặn khóa (`.env*`), media (`*.mp4`, `*.mp3`), `models/`, `bin/`, `dist/`, `node_modules/`, `out/`, `renders/`. |
| `.gitattributes` | Ép LF cho file văn bản, để Git for Windows không biến `.sh` thành CRLF làm bash lỗi. |

## 4. `docs/` — tài liệu cho người đọc

| File | Nội dung |
|---|---|
| `WORKFLOW.md` | Luồng từ clip thô tới video hoàn chỉnh, từng lệnh, thư mục làm việc chuẩn (tiếng Việt). |
| `PROMPT-VIDEO.md` | Prompt mẫu tổng quát (mọi thể loại): brief, quy tắc bất biến, quy trình, danh mục kỹ thuật, tiêu chuẩn nghiệm thu, bàn giao. |
| `PROMPT-LO-VIDEO.md` | Khung viết yêu cầu cho một lô video đăng thật (nhiều nguồn, tăng tốc giọng, bàn giao vào thư mục đồng bộ), kèm các chỗ prompt hay mơ hồ. |
| `DECISIONS.md` | Chỉ phần **kỹ thuật**: giấy phép (Remotion, ElevenLabs), bẫy kỹ thuật đã gặp, lý do chọn kiến trúc, renderer thứ hai, keyframe camera, các công cụ đã khảo sát. Việc đã làm cho từng khách nằm ở `CASE-LOG.md`. |
| `CASE-LOG.md` | **Lịch sử**, không phải hướng dẫn: số liệu ngách, các việc đã làm cho khách (tên khách, tên file, kết quả đo, điều chưa kiểm), phân tích prompt của một lô. Bài học dùng lại đã được chuyển thành kỹ thuật trong skill. Chứa tên khách và số liệu chiến dịch nên repo phải private. |
| `CAU-TRUC.md` | Chính file này. |
| `niche-data-queries.sql` | Các truy vấn tái hiện số liệu trong `niche-winning-patterns.md` (bảng `videos`; không cộng `video_metrics_daily` vì lặp chu kỳ 7 ngày). Dữ liệu của một chiến dịch thật: chỉ ở `docs/`, không đưa vào skill. |

## 5. `samples/` — dữ liệu mẫu

| File | Dùng ở |
|---|---|
| `example-edit-plan.md` | Kế hoạch mẫu `product-demo` 11 cảnh + 11 lớp đồ họa; selftest dùng để thử `pacing_checker`, `plan_to_project`, `footage_overlap_checker`. |
| `example-real-estate-plan.md` | Kế hoạch mẫu `real-estate` (cắt theo nhạc, speed ramp, 0,5x, `specs`/`pin`/`label`/`stat`/`chart`/`image`/`price`); selftest dùng để thử luật theo playbook và biên dịch các tính năng mới. |
| `line_00.mp3` + `line_00.txt` | Một câu giọng đọc và đúng lời của nó; selftest dùng để thử `align_captions` (kiểm tra giữ chính tả "túi xách"). |

## 6. `skill/short-video-editing/` — skill

### 6.1 `SKILL.md`

Điểm vào mà Claude nạp. Gồm 9 **quy tắc chung** cho mọi video (phân tích trước khi lập kế hoạch; hook trong 3 giây;
nhịp đúng playbook; có mốc thời gian; soát claim; footage của mình/có giấy phép, không dùng lại, không xáo trộn; đồ
họa tôn trọng khung hình; không làm giả trước/sau; nói rõ điều chưa kiểm), các quyết định thuộc về con người, quy
trình 9 bước, bảng chỉ mục tài liệu và phần "trung thực về bằng chứng".

### 6.2 `playbooks/` — luật theo thể loại

| File | Nội dung |
|---|---|
| `README.md` | Bảng 8 playbook; cách chọn (bảng "footage cho thấy gì + người dùng muốn gì → playbook"; tối đa 3 câu hỏi); ý nghĩa từng khóa JSON và script nào đọc nó; cách thêm thể loại hoặc "house style" của khách (biến thể). |
| `<id>.json` | Luật máy đọc: thời lượng, hook, độ dài cảnh, `drive` (giọng/nhạc), cấu trúc nhịp, chuyển cảnh, camera, kiểu phụ đề, theme, grade, kiểu hiệu chỉnh (`shared`/`per-clip`), nhịp nhạc (bpm), đồ hoạ nên dùng/tránh, ghi đè hiệu ứng âm thanh, checklist tuân thủ, tài liệu cần đọc, biến thể. |
| `<id>.md` | Tay nghề của thể loại: khi nào dùng, câu hỏi cần làm rõ, cấu trúc, cảnh quay cần có, dựng, âm thanh, màu, đồ hoạ, hook, tuân thủ (luật VN), lệnh chạy. |

Tám playbook: `product-demo` (+`unboxing`, `listicle`), `real-estate` (+`voiceover`), `food-fnb` (+`review`),
`talking-head` (+`testimonial`), `tutorial`, `fashion-beauty`, `montage-recap`, `promo-sale`.

### 6.3 `references/` — tri thức dùng chung

| File | Khi nào đọc |
|---|---|
| `policy.md` | **Trước khi lập kế hoạch một lô video hoặc dùng cảnh không phải của mình:** nội dung không gốc, lặp, vi phạm bản quyền; footage hiện có làm được bao nhiêu video; kết luận về crawl Douyin; cách đi hợp lệ để có số lượng lớn. |
| `claims-and-compliance.md` | Viết lời/chữ có tính quảng cáo: quy tắc chung (Luật Quảng cáo 75/2025, từ "nhất", so sánh đối thủ, khớp giá), theo ngành (gia dụng + bảng câu thay thế, BĐS — Luật KDBĐS 2023 & NĐ 339/2026, thực phẩm/TPBVSK, mỹ phẩm, tài chính, khuyến mãi), luật trước/sau. |
| `platforms.md` | TikTok vs Reels vs Shorts: định dạng, vùng an toàn (đo thực tế TikTok + vùng quảng cáo Reels của Meta), tín hiệu xếp hạng do nền tảng công bố, nhạc theo nền tảng, đặc thù TikTok Shop, checklist đăng. |
| `hook-library.md` | Cấu trúc hook 3 kênh, xếp hạng kiểu hook, hook theo từng playbook. |
| `cutting-and-pacing.md` | Nhịp theo playbook, các kiểu cắt (J/L, match, jump, smash…), cắt theo giọng hay theo beat, tua nhanh/slow-motion/speed ramp, re-hook, chỗ không được cắt. |
| `transitions.md` | Danh mục 11 chuyển cảnh, họ chuyển cảnh theo playbook, toán học căn giữa điểm cắt, shader trên Windows. |
| `camera-moves.md` | Push/pull/pan/roll/hold, footage đã tự di chuyển thì giữ yên, thang cỡ cảnh, chuyển động theo loại shot của từng playbook. |
| `image-processing.md` | HDR, cân bằng trắng (điểm ảnh trung tính), phơi sáng, các grade, chống rung, khử nhiễu, sửa méo ống kính, căn thẳng; ngưỡng đo được, bẫy ffmpeg, tốc độ. |
| `agency-pitch-recipe.md` | Quy trình đầy đủ từng bước cho video giới thiệu dịch vụ của người dẫn: khớp giọng–take, cảnh phụ, cú nháy silhouette, ánh sáng da, plan, âm thanh, render, bàn giao, các bẫy đã gặp. |
| `typography.md` | Font có tiếng Việt, quy tắc không khung viền, 5 kiểu tiêu đề, chữ "to" cho quảng cáo agency (`phrase`, `pill`, `arc`, `script`, `tag`), 4 theme màu (cool, warm, luxe, crimson). |
| `layout-and-motion-graphics.md` | Vùng an toàn, bố cục theo thể loại, danh mục 20 thành phần đồ họa và khóa nội dung, quy ước chuyển động. |
| `captions-and-text.md` | Kiểu phụ đề (karaoke, pop, plain, none) và bằng chứng đọc hiểu, nhóm phụ đề, vị trí, chữ làm việc khác lời đọc, SRT. |
| `sync-and-timing.md` | Đồng hồ chung (giọng hoặc nhạc), cắt ở chỗ lặng, neo đồ họa theo từ, hạ nhạc khi có lời, kiểm khớp. |
| `footage-ingest.md` | Soi và đo clip, shot log, thư viện shot, chia ngân sách footage cho nhiều video. |
| `voiceover-and-captions.md` | ElevenLabs (mô hình, thẻ cảm xúc, chi phí), căn phụ đề, **giọng có sẵn**. |
| `audio-and-music.md` | Bản quyền nhạc, chọn nhạc theo thể loại, cắt theo nhạc, các mức âm lượng, âm thanh hiện trường, J/L-cut. |
| `audio-processing.md` | Khử ồn, chuỗi xử lý giọng, mục tiêu loudness, các bẫy ffmpeg đã đo. |
| `sound-design.md` | Hiệu ứng âm thanh: nguồn hợp lệ, bộ âm thanh, tiếng nào cho sự kiện nào (có ghi đè theo playbook), mức và thời điểm. |
| `before-after.md` | Làm kết quả trước/sau rõ và trung thực: kỹ thuật, thẻ `compare`, chọn cặp khung hình, cảnh báo quảng cáo. |
| `niche-winning-patterns.md` | Số liệu thật trên 16.242 video sản phẩm gia dụng (cho `product-demo`). *Số liệu nội bộ, repo phải để private.* |
| `remotion-output.md` | Giấy phép Remotion, pipeline render, bố cục template, ranh giới ffmpeg ↔ Remotion. |
| `hyperframes-flow.md` | Luồng render bằng **HyperFrames** (Apache-2.0): chọn renderer nào, các bước, cú pháp `+shake/+glitch/+rgb/+pulse` và `--look`, `check` báo gì, đối chiếu với Remotion (số đo), bẫy, cách mở rộng. |
| `capcut-techniques.md` | Danh mục kỹ thuật CapCut (cắt, tốc độ, camera, chuyển cảnh, hiệu ứng, mặt nạ, màu, chữ, âm thanh, AI) ánh xạ sang bộ công cụ: có ở đâu, bằng lệnh nào, hoặc vì sao chưa; công thức review kiểu CapCut. |
| `adding-techniques.md` | **Cách bộ công cụ lớn lên**: một vòng duy nhất để thêm một kỹ thuật mới (tìm trước, nghiên cứu có nguồn và giấy phép, cài ở đúng chỗ theo loại, thẻ, tài liệu, test), các loại kỹ thuật và file cài của từng loại. |
| `technique-backlog.md` | Những kỹ thuật **đã nghiên cứu nhưng chưa làm** (nạp shader GL Transitions, match cut, mặt nạ/ink reveal, rack focus, parallax 2.5D, OCR…), kèm cách dựng, bẫy, giấy phép; xóa dòng khi đã làm. |
| `subject-effects.md` | Hiệu ứng theo mặt nạ người (cột `Subject`): nháy silhouette, viền, quầng sáng, đèn rọi, giữ màu, chữ nằm sau người; cách làm mặt nạ (`person_matte.py --frames/--range`), khi nào dùng, bẫy. |
| `reference-analysis.md` | Cách đọc báo cáo của `analyze_reference.py`: từng khóa đo (họ chuyển cảnh, đường camera, tốc độ, dấu vân tay màu, bằng chứng, `--compare`), ngưỡng, điều gì đã đo và điều gì Claude phải tự đọc từ ảnh. |
| `editor.md` | Trình sửa video trên trình duyệt (`editor.py`): khởi động, các vùng màn hình, phím tắt, lưu ở đâu, giới hạn. |

### 6.4 `scripts/` — công cụ dòng lệnh

Chạy từ thư mục skill. `align_captions.py` và `suggest_cuts.py --music` cần venv (chúng tự khởi chạy lại trong venv của
bộ công cụ); phần còn lại chỉ cần Python 3 và ffmpeg (bản đủ bộ lọc: `doctor.py` kiểm tra).

| Script | Việc làm | Vào → Ra |
|---|---|---|
| `doctor.py` | **Chạy đầu tiên trên máy mới.** Kiểm tra mọi thứ skill cần: Python, venv (faster-whisper, numpy), ffmpeg và từng bộ lọc/encoder mà script gọi (vidstab, zscale, haldclut, afftdn…), mô hình Whisper, Node, khoá ElevenLabs (không in giá trị), dung lượng ổ đĩa; nói rõ thiếu gì và cách cài theo hệ điều hành. Không đổi gì; `--json`, `--only NHÓM`. Chỉ dùng thư viện chuẩn. | máy → báo cáo, mã thoát 0/1 |
| `playbook.py` | Nạp playbook (kể cả biến thể `id:variant`); `list`, `show`, `suggest` (xếp hạng playbook theo lời yêu cầu + số đo footage), `skeleton` (khung kế hoạch đúng luật thể loại, từ `cuts.json` nếu có), `check` (kiểm mọi playbook; selftest chạy). Các script khác import nó. | yêu cầu/plan → playbook |
| `technique.py` | **Danh mục kỹ thuật**: `list`, `kinds`, `show`, `search` (tìm theo tên, bí danh của CapCut/Premiere/After Effects, thẻ), `scaffold KIND ID` (in các file phải sửa để thêm một kỹ thuật), `check` (so thẻ trong `assets/techniques.json` với code, tài liệu và selftest, hai chiều). | từ khóa → thẻ; code ↔ thẻ |
| `editor.py` | Trình sửa video chạy cục bộ (chỉ thư viện chuẩn của Python, nghe `127.0.0.1`): mở `project.json`, kéo thả cảnh/chữ/phụ đề trên timeline, sửa thuộc tính, lưu có ảnh chụp lịch sử, render lại. Giao diện ở `assets/editor/`. | project.json → project.json |
| `ref_measure.py` | Các phép đo cho `analyze_reference.py` (không cần thư viện mới): họ chuyển cảnh, đường camera từ vid.stab, tốc độ và khung đứng, dấu vân tay màu. | clip → số đo |
| `inspect_footage.py` | Đọc thuộc tính thật của clip (thời lượng, độ phân giải, xoay, fps, tiếng, HDR), cảnh báo clip ngang, thiếu tiếng, lệch định dạng; `--log` in shot log trống; `--measure` đo độ sáng, ám màu (trên điểm ảnh trung tính), nhiễu, rung/di chuyển camera (vid.stab), có người nói, rồi đề xuất hiệu chỉnh; `--json FILE` ghi `analysis.json`. | thư mục clip → báo cáo / `analysis.json` |
| `prepare_footage.py` | Làm proxy: chuyển HDR, khung 9:16, khử nhiễu, chống rung 2 lượt, sửa méo/căn thẳng (`--fix`), 30 hoặc 60 fps (`--slowmo`), cân trắng + phơi sáng + grade của playbook gộp vào một LUT 3D, làm nét nhẹ; `correction: shared` cho cùng một hiệu chỉnh mọi clip; ghi `corrections.json`. | clip thô → `public/clips/*.mp4` |
| `process_audio.py` | `voice`: đo nền nhiễu/mức giọng, khử ồn bằng mẫu nhiễu khi cần, EQ, de-ess, nén theo mức giọng, expander, −16 LUFS; `music`: cân về −14 LUFS; `master`: cả video về −14 LUFS, đỉnh ≤ −1 dBTP, AAC, `--phone` bản nhẹ; `measure`. | âm thanh/video → bản đã xử lý |
| `contact_sheet.py` | Ảnh tổng hợp khung hình: một hàng cho mỗi clip thô; hoặc giữa mỗi cảnh + mỗi điểm cắt của video đã render. | clip/video → `.png` |
| `trim_voice.py` | `--silences` liệt kê chỗ lặng và điểm cắt; `--keep a-b,c-d` nối các đoạn giữ lại; `--jumpcut` (talking head) bỏ mọi khoảng lặng dài, gộp/tách đoạn theo độ dài cảnh của playbook, ghi giọng đã nối + `--scenes-out` (mỗi cảnh có thời điểm nguồn). | giọng/video → giọng ngắn hơn, cảnh |
| `_venv.py` | Không phải lệnh: hàm `ensure_venv()` mà các script cần numpy/onnxruntime gọi đầu file để tự chạy lại trong venv của bộ công cụ (`$SVK_PYTHON` hoặc venv do `setup.sh` tạo) khi Python hệ thống thiếu thư viện — như `align_captions.py` đã làm với faster-whisper. | — |
| `analyze_reference.py` | Đo một video MẪU của khách trước khi dựng lại: tách cảnh theo thay đổi khung hình (số cảnh, cảnh ngắn nhất, cảnh/phút), các đoạn chuyển động liên tục 4+ khung (= chuyển cảnh, độ dài theo khung hình), cú nháy một khung, màu viền/giữa của từng cảnh, độ ồn (LUFS, đỉnh), ảnh `scenes.png`, ảnh dày `dense_*.png` (cứ n khung một lần) và ảnh phổ `spectrum_*.png`. Không tự nhận diện tiếng hiệu ứng (đã thử, không đáng tin: `docs/DECISIONS.md`). | video mẫu → `ref/report.md` + `.json` + ảnh |
| `montage.py` | Ghép bất kỳ ảnh nào thành một ảnh có nhãn (thời điểm lấy từ tên file, hoặc `--labels`): ảnh `stills.mjs` render ra, khung mẫu đặt cạnh khung của mình. | ảnh → một ảnh |
| `mix_report.py` | Số đo cho video đã xong: kích thước, fps, dải màu (cờ lỗi nếu full-range), thời lượng so với project, LUFS/đỉnh, độ ồn từng 10 s, mức giọng và mức trong chỗ nghỉ, nhạc có thật trong file (`--nomusic`), số tiếng hiệu ứng. Chỉ đo, không nghe. | mp4/wav → báo cáo, mã thoát 1 nếu có lỗi |
| `agency_plan.py` | Viết bản nháp `edit-plan.md` cho video giới thiệu dịch vụ (`talking-head:agency`) từ words.json + matches.json (match_voice_takes) + cutaways.json: cảnh người dẫn cắt theo khoảng nghỉ (In = start + lag), cảnh thẻ với cảnh phụ chưa dùng, chuyển cảnh, camera, cột Face/Flash, khối chữ cho từng mệnh đề (hiệu ứng luân phiên), logo ở tên thương hiệu, dải phụ đề. Là bản nháp để chỉnh tay. | json → `edit-plan.md` |
| `finish_video.py` | Từ bản render Remotion ra file giao: chuyển dải màu full → limited (BT.709), master âm thanh −14 LUFS, bản không nhạc (`--audio-nomusic`), bản phone, cover, bản xem thử 720p. | mp4 render → thư mục final |
| `check_lipsync.py` | Kiểm trên video CUỐI: với mỗi cảnh người dẫn, so âm thanh gốc của take tại `In` với âm thanh bản cuối; lệch quá 1 khung hình là lỗi timeline. | project.json + mp4 + clip gốc → bảng |
| `person_matte.py` | Cắt người khỏi nền bằng model tách người ONNX (u2net_human_seg, ~168 MB, để NGOÀI repo): xuất PNG silhouette trắng cho cú nháy mở đầu; `--faces` đo vị trí đầu (x, y, r) cho ánh sáng làm đẹp da. | clip + thời điểm → PNG / JSON |
| `find_cutaways.py` | Liệt kê đoạn im lặng của các take (khoảng nghỉ trước/sau lời) làm cảnh phụ: xếp hạng theo độ dài, có người trong khung (`--person`), loại đoạn đã dùng (`--avoid`). | thư mục clip → bảng, JSON |
| `match_voice_takes.py` | Khi giọng được cắt ra từ chính âm thanh các take (người dẫn, phỏng vấn): tương quan chéo giọng với từng clip, in `thời gian clip = thời gian giọng + lag` cho từng đoạn khớp và các đoạn giọng không take nào có (chỗ để chèn cảnh phụ). Cảnh bắt đầu ở giây T của giọng dùng `In = T + lag` nên khẩu hình khớp từng mẫu âm. | giọng + thư mục clip → bảng, `--out` JSON |
| `make_music.py` | Tự tổng hợp nhạc nền không vướng bản quyền (numpy + ffmpeg): các đoạn nhạc bắt đầu đúng chỗ cắt của video (lưới nhịp khởi động lại ở mỗi đoạn), cường độ 0..1 chọn lớp (pad, bass, kick + hat, chord, clap + arpeggio), `--hits` đặt cú đập + riser. Mức cuối do `process_audio.py music` lo. | `--sections --hits` → `.wav` |
| `make_sfx.py` | Tự tạo 6 tiếng hiệu ứng (pop, tick, ding, thud, swoosh, riser) bằng ffmpeg: không tải gì, không vướng bản quyền; đỉnh −3 dB như các file CC0. | thư mục → `.wav` |
| `make_voiceover.py` | Tạo giọng bằng ElevenLabs, mỗi dòng một file; `--quota`, `--dry-run` (không tiêu credit), từ chối chạy nếu không đủ credit. | `script.txt` → `.mp3` + `voice_manifest.json` |
| `align_captions.py` | Whisper cho **thời gian**, kịch bản cho **chữ**; gộp nhóm phụ đề quá ngắn; `--words-out` ghi thời gian từng từ. | giọng + script → `captions.srt`, `words.json` |
| `suggest_cuts.py` | Gợi ý điểm cắt: theo chỗ lặng của `words.json`, hoặc theo beat của nhạc (`--music`: spectral flux + tempogram + bám phách quy hoạch động, ưu tiên đầu ô nhịp; `--beats-out`; cần numpy nên tự chạy trong venv), hoặc cả hai (cắt theo giọng rồi kéo về beat gần trong 4 khung); độ dài cảnh/hook lấy từ playbook (quy hoạch động). | `words.json`/nhạc → bảng/`cuts.json` |
| `plan_scenes.py` | Điền Source/In từ **thư viện shot** sao cho không đoạn nào dùng hai lần (tính cả cảnh tua nhanh), giữ Type/Speed/Transition của khung (`--plan`), chọn Camera theo `move` của span → `camera.byKind` của playbook → cỡ cảnh; thoát 1 khi footage hết. | `library.json` + khung/`cuts.json` → bảng Scenes |
| `pacing_checker.py` | Cổng kiểm tra luật nhịp **của playbook** ghi trong plan (hook, độ dài cảnh, liền mạch, tổng thời lượng). Thoát 1 nếu vi phạm. | `edit-plan.md` → báo cáo |
| `footage_overlap_checker.py` | Biến mỗi cảnh thành khoảng nguồn `[In, In + độ dài × tốc độ]` và báo trùng/sát nhau trong và giữa các plan; `--clips` liệt kê đoạn còn trống. | các `edit-plan.md` → báo cáo |
| `plan_to_project.py` | Biên dịch kế hoạch thành `project.json` (cả Speed/ramp); kiểu phụ đề, camera tự động (`--auto-camera`, giữ yên clip đang di chuyển theo `--analysis`), ghi đè SFX lấy từ playbook; `--platform reels-ad`; in **báo cáo bắt nhịp** (cắt giữa từ, chữ sát điểm cắt, vùng giao diện, thành phần playbook tránh, slow-motion sẽ giật, thiếu file). | `edit-plan.md` + SRT + words → `project.json` |
| `project_to_hyperframes.py` | **Renderer thứ hai**: biến cùng `project.json` thành dự án HyperFrames (Apache-2.0, không tính ghế): dàn cảnh giống `timeline.ts`, **nướng** cảnh có `speed`/`ramp` thành clip riêng bằng ffmpeg, trộn giọng + nhạc tự hạ + SFX thành `audio/mix.wav` (cùng mức và độ hạ như `audio.tsx`), nối cứng proxy (không chép), ghi `index.html`, `kit.js`, `kit.css`, `package.json` (ghim `hyperframes@0.9.26`); `--look vignette=,grain=`; `--check`, `--render FILE --quality`; báo thành phần chưa vẽ (magnifier, thumbs, compare, ranking) và cảnh mà clip nguồn hết trước. | `project.json` → thư mục HyperFrames |
| `new_remotion_project.py` | Tạo dự án render từ template; `--playbook` đặt theme (và grade cho proxy); `--proxies` gọi `prepare_footage.py`; `--slowmo`; `--install` chạy npm; `--theme cool|warm|luxe|crimson`; `--update` chép lại template (lặp lại `--playbook`/`--theme`); luôn đặt bộ SFX vào `public/sfx/`. | → thư mục dự án |

### 6.5 `assets/`

| Đường dẫn | Chức năng |
|---|---|
| `edit-plan-template.md` | Mẫu kế hoạch dựng: đầu trang (Playbook, Platform, Drive, Look…), bảng **Scenes** (Start, End, Source, In, Type, Transition, Camera, Speed, Shot, Audio), bảng **Overlays** (Start, End, Component, Zone, Tone, Content), checklist tuân thủ. |
| `grades.json` | 15 "look" màu: 5 của các playbook (natural, bright-interior, warm-food, soft-skin, vivid) và 9 thư viện (teal-orange, cinematic-fade, moody, pastel, vintage-film, mono, bleach-bypass, golden-hour, cold-blue); chuỗi lọc ffmpeg chỉ gồm bộ lọc màu nướng được vào LUT 3D + `wbStrength`; `--grade-strength 0..1` pha look với ảnh đã chỉnh. |
| `techniques.json` | **Danh mục kỹ thuật**: một thẻ cho mỗi kỹ thuật (chuyển cảnh, hiệu ứng chữ, hiệu ứng theo mặt nạ, grade, camera, tốc độ, look, font, đồ họa, theme…): id, loại, nó trông thế nào, cú pháp trong kế hoạch, renderer, tài liệu, test, nguồn và giấy phép. `technique.py check` giữ nó khớp với code. |
| `editor/` | `index.html`, `editor.css`, `editor.js`: giao diện của `scripts/editor.py` (JavaScript thuần, không CDN, không thư viện). |
| `shot-library.example.json` | Mẫu thư viện shot cho `plan_scenes.py`: `kind`, `focus`, `size`, `move` tùy chọn. |
| `sfx/` | Bộ hiệu ứng âm thanh: 5 file ghi âm CC0 (`whoosh`, `whip`, `switch`, `mouse-click`, `shutter-modern`), `SOURCES.md` (tác giả, nguồn, giấy phép từng file), `sfx-map.json` (tiếng nào cho sự kiện nào, mức dB, độ dẫn trước). |
| `remotion-template/` | Dự án Remotion điều khiển bằng dữ liệu (mục 7). |
| `hyperframes-template/` | Bộ vẽ cho renderer HyperFrames (mục 7b): `kit.js`, `kit.css`. |

### 6.6 `evals/` — bộ ca kiểm tra skill

Năm ca: `full-edit-plan-from-brief` (lập plan review sản phẩm đầy đủ, ghi đúng playbook), `pushes-back-on-too-short`
(phản biện video 15 giây bằng số liệu), `rejects-banned-claims` (bắt claim cấm, đề xuất câu thay), `routes-real-estate-tour`
(nhận ra tour BĐS, dùng playbook `real-estate`, cắt theo nhạc, giữ đúng dữ kiện), `asks-when-ambiguous` (footage hợp hai thể
loại: hỏi tối đa 3 câu có mặc định hoặc chọn và nói lý do). Mỗi ca có `prompt.md`, `case.yaml`, `graders/`. Hai ca mới đã
chạy tay một lần bằng agent mới (đạt; kết quả trong `DECISIONS.md`); chưa có harness tự động.

## 7. `assets/remotion-template/` — template render

Một composition duy nhất, `Short`, đọc `project.json` qua `--props`. **Không có chữ nội dung video trong code.**

| Đường dẫn | Chức năng |
|---|---|
| `stills.mjs` | Render nhiều ảnh tĩnh của một project từ MỘT lần bundle (`--cuts`, `--every S --from A --to B`, hoặc liệt kê giây): để nhìn từng chuyển cảnh và hiệu ứng trước khi render đầy đủ; ghép bằng `montage.py`. |
| `package.json` · `tsconfig.json` · `remotion.config.ts` | Phụ thuộc ghim đúng phiên bản; cấu hình TypeScript; bộ GL mặc định `swangle` (phần mềm, chạy mọi máy; `SVK_GL=angle` cho máy có GPU) để chuyển cảnh shader và light leak chạy. |
| `project.example.json` | Thư viện mẫu không cần footage: đủ kiểu chữ và đồ họa (cả `pin`, `label`, `chart`, `specs`, `stat`); mở bằng `npm run studio`. |
| `src/index.ts` · `src/Root.tsx` | Đăng ký composition; độ dài lấy từ `duration` và `fps` trong dữ liệu (`calculateMetadata`). |
| `src/project.ts` | **Hợp đồng dữ liệu**: kiểu `Project` (cả `layout`), `Scene` (cả `speed`, `ramp`), `Overlay`, `CaptionStyle`, `Word`, `Camera`… |
| `src/theme.ts` | **Mọi token thiết kế**: font, **bốn bảng màu** (`cool`: trắng, xanh da trời; `warm`: trắng ngà, vàng, đỏ, nâu cho ẩm thực/ánh vàng; `luxe`: trắng ấm, vàng champagne, than chì cho BĐS/thời trang; `crimson`: trắng, đỏ thương hiệu, vàng, đỏ đô cho quảng cáo agency; một dòng `THEME` do playbook quyết định), font điều kiện (Barlow Condensed) và chữ viết tay (Pacifico), kích thước thẻ video + lưới (`card`, `grid`), màu chữ tiêu đề, vùng bố cục, dải phụ đề theo layout (feed / reels-ad), điểm giỏ hàng (112, 1677; đo từ ảnh chụp TikTok thật), kích thước đồ họa thông tin, đường cong chuyển động, giới hạn camera, thẻ so sánh. Đổi diện mạo ở đây. |
| `src/engine/timeline.ts` | Dàn cảnh với chuyển cảnh **căn giữa điểm cắt**; tính lại khung nguồn cho `speed` và `ramp` (khung nguồn tại điểm cắt luôn là `In`). |
| `src/engine/transitions.tsx` | Bảng chuyển cảnh (31 tên): có sẵn của Remotion (cả nhóm shader `filmBurn`, `zoomBlur`, `crosswarp`…), `zoomThrough`, `blurDissolve`, `whip` khớp tốc độ (mờ theo chiều chuyển động), và 5 cái viết bằng CSS (`blinds`, `diamond`, `doors`, `glitchSlice`, `spinZoom`). |
| `src/engine/Subject.tsx` | Hiệu ứng theo mặt nạ người (`Scene.subject`): fill/nháy silhouette, outline, glow, dim, colorpop, behind (chữ giữa nền và bản cắt của người); vẽ trong khung camera nên bám theo mọi cú đẩy. |
| `src/fonts.ts` | Thư viện 31 font Google (OFL, có subset tiếng Việt) theo tâm trạng, chọn bằng `font=<id>` trên từng lớp chữ; chỉ tải font mà dự án dùng. |
| `src/engine/camera.ts` | Camera ảo: push, pull, pan, hold, phóng theo từ khóa; và **keyframe** (`keys`): danh sách khung hình (zoom, điểm giữa, roll) với easing cho từng đoạn (`inOut soft out in snap back linear hold`), zoom nội suy theo diện tích, mép khung không bao giờ lộ; thêm `shake` (rung tay: nhiễu mượt trên x, y, roll, mỗi trục một seed). |
| `src/engine/audio.tsx` | Giọng, nhạc nền tự hạ khi có lời, hiệu ứng âm; nằm ngoài chuỗi chuyển cảnh nên không bị xê dịch. |
| `src/engine/Short.tsx` | Composition: nối cảnh, camera, tốc độ (ramp đọc lại khung nguồn từng khung trong `<Freeze>`), lớp đồ họa, phụ đề, âm thanh, lớp `look` (vignette, grain). |
| `src/components/registry.tsx` | Tên thành phần dùng trong `project.json`; tên lạ sẽ báo lỗi. |
| `src/components/anim.ts` | Hàm hoạt họa dùng chung (vào/ra, spring, vừa khung). |
| `src/components/text/` | `Title.tsx` (5 kiểu: outline, stack, gradient, glass, marker), `Captions.tsx` (karaoke / pop / plain; dải phụ đề `captionBands`, có `hide`), `primitives.tsx` (chữ viền, chữ gradient, chữ trồi qua mặt nạ), `Phrase.tsx` (`phrase`, `pill`, `arc`, `script`, `tag`, `burst`), `Fx.tsx` (14 hiệu ứng chữ: scatter, slam, stamp, glitch, drop, elastic, wave, flip, maskwipe, split, shine, neon, typewriter, rise). |
| `src/components/graphics/Grid.tsx` | Nền lưới đỏ chuyển động như vải bay trong gió (hàm thuần của khung hình) cho các cảnh thẻ. |
| `src/components/graphics/Brand.tsx`, `Glyph.tsx` | `logo` (mờ chuyển động rồi nét, `tint`, `hold`), `counter` ("5 → 10"), `icon`, `circled`, `rawfinal` (RAW | FINAL cùng một take) và bộ biểu tượng SVG. |
| `src/components/graphics/` | 20 thành phần: `Callout`, `Lists` (checklist, step), `Price` (đếm số, có thập phân), `Pointers` (mũi tên giỏ hàng TikTok Shop, vòng khoanh, sticker), `Media` (kính lúp, dải 3 hình `thumbs`, thẻ TRƯỚC/SAU `compare`, ảnh `image`), `Ranking`, `Bars` (thanh tiến trình, thẻ tên), `Info` (**`specs`** hàng thông số có icon, **`pin`** ghim bản đồ, **`label`** nhãn phòng/món/món đồ, **`stat`** số đếm lên, **`chart`** biểu đồ thanh). |

## 7b. `assets/hyperframes-template/` — bộ vẽ cho HyperFrames

Không phải dự án hoàn chỉnh: `project_to_hyperframes.py` chép hai file này vào dự án và sinh `index.html` quanh chúng.
Cùng hợp đồng `project.json` với mục 7; hợp đồng HyperFrames: một timeline GSAP tạm dừng đăng ký ở `window.__timelines["main"]`.

| Đường dẫn | Chức năng |
|---|---|
| `kit.js` | Toàn bộ bộ vẽ: `render(frame)` là **hàm thuần của khung hình** (đặt style mọi phần tử từ dữ liệu), GSAP chỉ đẩy đầu phát qua một setter nên mọi lần tua đều đúng. Gồm token theme (cool/warm/luxe, sao từ `theme.ts`), easing và spring giống Remotion, dàn cảnh + chuyển cảnh căn giữa, camera ảo (push/pull/pan/hold/roll, punch), 11 chuyển cảnh, accent flash/light leak, **hiệu ứng trên điểm cắt** (`shake`, `pulse`, `rgb` tách kênh bằng bộ lọc SVG, `glitch`), **look** (vignette, hạt phim), phụ đề karaoke/pop/plain, 5 kiểu tiêu đề và 17 thành phần đồ họa (`FACTORY`). Chưa vẽ: `magnifier`, `thumbs`, `compare`, `ranking`. |
| `kit.css` | Nền và lớp xếp chồng (`z-index`), phông Be Vietnam Pro / Playfair Display / Anton (HyperFrames nhúng Google Fonts lúc render). |

Hướng dẫn dùng, so sánh với Remotion, số đo thực và các bẫy: `references/hyperframes-flow.md`. Danh mục kỹ thuật CapCut
và chỗ chúng nằm trong bộ công cụ: `references/capcut-techniques.md`.

## 8. Nằm ngoài repo (do `setup.sh` và quá trình làm việc tạo ra)

| Vị trí | Nội dung |
|---|---|
| `~/.local/share/short-video-kit/venv` | Môi trường Python (đổi bằng `SVK_PYTHON`). |
| `~/.cache/short-video-kit/models` | Mô hình Whisper `small` (đổi bằng `WHISPER_MODEL_DIR`). |
| `~/.config/short-video-kit/env` | Khóa ElevenLabs, quyền 600. |
| `~/.claude/skills/short-video-editing` | Bản skill đã cài (chạy lại `setup.sh` sau mỗi `git pull`). |
| `<thư-mục-làm-việc>/<video>/` | `script.txt`, `captions.srt`, `words.json`, `edit-plan.md` của từng video. |
| `<thư-mục-làm-việc>/analysis.json` | Số đo footage (`inspect_footage.py --measure`). |
| `<thư-mục-làm-việc>/render/` | Một dự án Remotion cho cả lô (`public/clips` = proxy đã hiệu chỉnh + `corrections.json`, `public/audio` = giọng/nhạc đã xử lý, `public/images`). |

## 9. Công cụ đang dùng

| Công cụ | Phiên bản | Vai trò |
|---|---|---|
| Claude Code (skill + `CLAUDE.md`) | hiện hành | Điều phối: đọc chỉ dẫn, lập kế hoạch, chạy công cụ, báo cáo. |
| Python | 3.10+ (thử trên 3.12 Windows, 3.14 Linux) | Mọi script. |
| faster-whisper (CTranslate2) | 1.2.1, mô hình `small` | Lấy **thời gian** từng từ của giọng. |
| numpy | — | Xử lý mẫu âm cho Whisper; phát hiện beat (`suggest_cuts.py --music` tự chạy lại trong venv). |
| ffmpeg / ffprobe | 6+ (thử 7.0 static, có libvidstab) | Đo footage (`signalstats`, `vidstabdetect`, `psnr`), hiệu chỉnh và grade (`zscale/tonemap`, `hqdn3d`, `vidstabtransform`, `lenscorrection`, `rotate`, `haldclut`), âm thanh (`afftdn`, `deesser`, `acompressor`, `agate`, `alimiter`, `loudnorm` để đo), `silencedetect`, `atrim`/`concat`, ảnh tổng hợp, giải mã nhạc để tìm beat. |
| ElevenLabs API | `eleven_turbo_v2_5` | Tạo giọng khi không có giọng sẵn (gói free không dùng thương mại). |
| Node.js | 20.19+ | Chạy Remotion. |
| Remotion | 4.0.540 (`@remotion/cli`, `transitions`, `light-leaks`, `paths`, `google-fonts`) | Render video từ dữ liệu; chuyển cảnh, hiệu ứng, camera. Miễn phí cho cá nhân hoặc công ty ≤ 3 người. |
| React / TypeScript | 19.3.1 / 5.9.3 | Viết thành phần đồ họa; typecheck bằng `tsc --noEmit`. |
| Google Fonts | Be Vietnam Pro, Playfair Display Italic, Anton | Font đã kiểm tra có bộ ký tự tiếng Việt (OFL). |
| bash (Git Bash trên Windows) | — | `setup.sh`, `selftest.sh`. |
| git + GitHub CLI | — | Mã nguồn (repo private), đăng nhập `gh auth login --web`. |
| winget / brew / apt | — | Cài Python, Node, ffmpeg theo hệ điều hành. |
| Supabase (chỉ phía dữ liệu) | — | Nguồn số liệu ngách; chỉ còn lại file SQL tái hiện. |

## 10. Kỹ thuật chính

1. **Playbook theo thể loại.** Luật phụ thuộc thể loại là dữ liệu (`playbooks/<id>.json`) mà mọi script đọc; thêm thể
   loại = thêm một JSON + một MD, `playbook.py check` bảo đảm nó hợp lệ, khung của nó tự qua luật của nó, và không thành
   phần/grade/theme nào "nằm chơi" không playbook nào dùng.
2. **Phân tích trước, chọn sau.** Đo footage (`--measure`) + lời yêu cầu → `playbook.py suggest` gợi ý; Claude xem
   contact sheet để xác nhận, hỏi tối đa 3 câu khi mơ hồ.
3. **Dựng bằng dữ liệu.** Kế hoạch (Markdown) → `project.json` → một composition. Đổi video = đổi bảng.
4. **Hiệu chỉnh hình đo được.** Cân trắng trên điểm ảnh trung tính (không phải mọi điểm ảnh: chậu xanh lá từng làm sai),
   phơi sáng bằng gamma, khử nhiễu chỉ khi tối và nhiễu, chống rung khi rung > 4 px/khung, HDR về SDR; cân trắng +
   phơi sáng + grade gộp vào một LUT 3D (nhanh gấp ~2,5 lần, sai khác không thấy được); trước/sau dùng chung hiệu chỉnh.
5. **Âm thanh đo được.** Nền nhiễu = phân vị 5% của cửa sổ 100 ms; khử ồn bằng mẫu nhiễu chỉ khi giọng cách nhiễu < 35 dB;
   nén theo mức giọng; expander trả lại khoảng lặng; −16 LUFS cho giọng, −14 LUFS / −1 dBTP cho bản master.
6. **Chữ lấy từ kịch bản, thời gian lấy từ Whisper.** Whisper nghe sai tiếng Việt; chuỗi từ được so khớp rồi giữ chính tả
   của kịch bản.
7. **Cắt theo giọng hoặc theo nhạc.** Chỗ lặng (`silencedetect`, khoảng trống giữa từ) hoặc beat (spectral flux, tempo
   có trọng số + bằng chứng nửa phách, bám phách quy hoạch động, đầu ô nhịp từ dải trầm; 88–95% phách trùng onset trên nhạc thật); quy hoạch động chọn điểm cắt cho mọi cảnh trong độ dài của playbook.
   Talking head: jump cut tự động, mỗi đoạn giữ lại là một cảnh có thời điểm nguồn nên hình–tiếng luôn khớp.
8. **Tốc độ và speed ramp.** Cột Speed (`2x`, `0.5x`, `ramp 1>2.5>1`); khung nguồn tại điểm cắt luôn là `In`; ramp tính
   lại khung nguồn từng khung (đã kiểm: lệch ≤ 3 khung trên clip có đồng hồ); kiểm trùng footage tính cả tốc độ;
   cảnh báo slow-motion giật khi proxy không đủ fps.
9. **Chuyển cảnh căn giữa điểm cắt.** `begin = cut − T/2`, `finish = cutTiếp + T/2`, nên điểm cắt trùng đúng chỗ đã định.
10. **Camera ảo liên tục**, thang tỉ lệ cảm nhận được, không reset ở điểm cắt; clip đã tự di chuyển thì giữ yên.
11. **Đồ họa neo theo từ** (`@"cụm từ"`), giữ đủ thời gian đọc, tắt trước điểm cắt ≥ 3 khung.
12. **Vùng an toàn theo nền tảng.** TikTok (đo thực tế) cho feed; vùng quảng cáo Reels của Meta (`--platform reels-ad`);
    phụ đề có dải riêng; tối đa hai thành phần thông tin cùng lúc.
13. **Chia ngân sách footage.** Khoảng nguồn `[In, In + độ dài × tốc độ]`, biên 0,5 giây, liệt kê đoạn còn trống.
14. **Báo cáo bắt nhịp** và **kiểm bằng mắt** (`contact_sheet.py`): nơi lộ lỗi như chữ trắng chìm trên áo trắng.
15. **Hiệu ứng âm thanh theo bảng**, có ghi đè theo playbook; chỉ CC0 hoặc tự tạo.
16. **Giữ repo sạch.** Không file thừa, không code chết, không nội dung video trong template; khóa, media, mô hình và thư
    mục làm việc nằm ngoài git; `playbook.py check` chặn kỹ thuật "viết ra mà không dùng".
