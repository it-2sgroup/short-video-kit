# Cấu trúc repo, công cụ và kỹ thuật

Tài liệu này trả lời ba câu hỏi: **mỗi thư mục và file làm gì**, **repo dùng công cụ nào**, và **dùng kỹ thuật
nào để video khớp tiếng, mượt và không lặp footage**. Cách làm việc từng bước nằm ở
[`WORKFLOW.md`](WORKFLOW.md); lý do chọn công cụ và các bẫy đã gặp nằm ở [`DECISIONS.md`](DECISIONS.md).

## 1. Repo này làm gì

Bộ công cụ dựng video ngắn dọc (TikTok Shop, 30–40 giây) từ clip thô + kịch bản + giọng đọc. Một video được mô
tả **một lần** bằng *kế hoạch dựng* (file Markdown có hai bảng), rồi đi qua các bước kiểm tra tự động và được
render bởi **một** composition Remotion. Muốn đổi video thì đổi kế hoạch, không viết lại code.

```
clip thô ──► inspect_footage + contact_sheet ──► shot log ─┐
                                                           ▼
kịch bản ──► giọng (có sẵn / ElevenLabs) ──► trim_voice ──► align_captions ──► captions.srt + words.json
                                                           │
                          edit-plan.md (bảng Scenes + bảng Overlays) ◄─ viết theo mẫu + references
                                      │
                 pacing_checker + footage_overlap_checker (cổng kiểm tra)
                                      ▼
                  plan_to_project ──► project.json + báo cáo bắt nhịp
                                      ▼
            Remotion (template trong skill) ──► video .mp4 ──► contact_sheet (nhìn lại bằng mắt)
```

## 2. Cây thư mục

```
short-video-kit/
├── CLAUDE.md                 Chỉ dẫn cho Claude khi mở repo (Claude tự đọc đầu tiên)
├── README.md                 Giới thiệu, cài đặt, cách dùng (tiếng Anh, chuẩn repo quốc tế)
├── setup.sh · selftest.sh    Cài đặt và kiểm tra máy
├── requirements.txt          Thư viện Python (faster-whisper, numpy)
├── .env.example              Mẫu file khóa ElevenLabs (không chứa khóa)
├── .gitignore · .gitattributes
├── docs/                     Tài liệu cho người đọc
├── samples/                  Dữ liệu mẫu cho selftest
└── skill/short-video-editing/   ← chính là "skill" mà Claude nạp
    ├── SKILL.md              Quy tắc cứng + quy trình 9 bước
    ├── references/           Tri thức theo chủ đề (Claude đọc khi cần)
    ├── scripts/              Công cụ dòng lệnh Python
    ├── assets/               Mẫu kế hoạch + template Remotion
    └── evals/                Bộ ca kiểm tra chất lượng skill
```

## 3. Gốc repo

| File | Chức năng |
|---|---|
| `CLAUDE.md` | Chỉ dẫn cho Claude: kiểm tra máy đầu phiên, các bước cài đặt, quy trình khi người dùng nhờ dựng video, việc phải hỏi người dùng (tải về, gói ElevenLabs, giấy phép Remotion), các bài học đã trả giá. |
| `README.md` | Tổng quan, yêu cầu hệ thống, cài đặt (có Windows), cách dùng, giấy phép bên thứ ba, hạn chế đã biết. |
| `setup.sh` | Cài mọi thứ vào `$HOME`: venv Python, thư viện, mô hình Whisper (~460 MB), khóa ElevenLabs (nếu có `.env.local`), chép skill vào `~/.claude/skills`. Chạy lại an toàn. Tùy chọn: `--check` (chỉ báo cáo), `--set-key` (nhập khóa ẩn), `--no-model`, `--no-skill`, `--download-ffmpeg` (Linux), `--package` (đóng gói `.skill` cho app desktop). |
| `selftest.sh` | 11 nhóm kiểm tra không tốn credit (công cụ, soi clip, luật nhịp, căn phụ đề, khóa ElevenLabs, biên dịch kế hoạch, trùng footage, cắt giọng, bảng khung hình, dựng khung dự án, hiệu ứng âm thanh). `--render [DIR]` thêm nhóm 12: typecheck template và render một ảnh tĩnh. |
| `requirements.txt` | `faster-whisper==1.2.1` và `numpy`. |
| `.env.example` | Chỉ có dòng `ELEVENLABS_API_KEY=`. Khóa thật nằm ở `.env.local` (bị `.gitignore` chặn) hoặc `~/.config/short-video-kit/env`. |
| `.gitignore` | Chặn khóa (`.env*`), media (`*.mp4`, `*.mp3`), `models/`, `bin/`, `dist/`, `node_modules/`, `out/`, `renders/`. |
| `.gitattributes` | Ép LF cho file văn bản, để Git for Windows không biến `.sh` thành CRLF làm bash lỗi. |

## 4. `docs/` — tài liệu cho người đọc

| File | Nội dung |
|---|---|
| `WORKFLOW.md` | Luồng từ clip thô tới video hoàn chỉnh, từng lệnh, thư mục làm việc chuẩn (tiếng Việt). |
| `DECISIONS.md` | Giấy phép (Remotion, ElevenLabs), bẫy kỹ thuật đã gặp, số liệu ngách, lý do chọn kiến trúc, các công cụ đã khảo sát, claim vi phạm trong kịch bản hiện hành. |
| `CAU-TRUC.md` | Chính file này. |
| `niche-data-queries.sql` | Các truy vấn tái hiện mọi số liệu trong `niche-winning-patterns.md` (bảng `videos`; không cộng `video_metrics_daily` vì lặp chu kỳ 7 ngày). |

## 5. `samples/` — dữ liệu mẫu

| File | Dùng ở |
|---|---|
| `example-edit-plan.md` | Kế hoạch mẫu 11 cảnh + 9 lớp đồ họa; selftest dùng để thử `pacing_checker`, `plan_to_project`, `footage_overlap_checker`. |
| `line_00.mp3` + `line_00.txt` | Một câu giọng đọc và đúng lời của nó; selftest dùng để thử `align_captions` (kiểm tra giữ chính tả "túi xách"). |

## 6. `skill/short-video-editing/` — skill

### 6.1 `SKILL.md`

Điểm vào mà Claude nạp. Gồm 8 **quy tắc cứng** (hook trong 3 giây; cảnh 3–4 giây; có mốc thời gian; 25–45 giây; soát
claim; một lô footage nuôi nhiều video không dùng lại đoạn nào; đồ họa tôn trọng khung hình; cảnh quay của mình hoặc
có giấy phép, không xáo trộn một nguồn thành nhiều video), quy trình 9 bước, bảng
chỉ mục `references/` và phần "trung thực về bằng chứng" (đâu là số liệu đo, đâu là quy ước nghề).

### 6.2 `references/` — tri thức theo chủ đề

| File | Khi nào đọc |
|---|---|
| `niche-winning-patterns.md` | Đầu tiên với hàng gia dụng/tẩy rửa: số liệu thật trên 16.242 video (thời lượng, CTR, tập trung vào top creator). *Chứa số liệu nội bộ, repo phải để private.* |
| `Chính sách.md` | **Đọc trước khi lập kế hoạch một lô video hoặc dùng cảnh không phải của mình:** TikTok, TikTok Shop và Douyin coi gì là nội dung không gốc, lặp, vi phạm bản quyền; nguồn hiện có làm được bao nhiêu video; kết luận về việc crawl Douyin; cách đi hợp lệ để có số lượng lớn. |
| `platform-specs.md` | Viết kịch bản/claim; bảng "câu cấm → câu thay thế"; luật before/after; vùng an toàn. |
| `hook-library.md` | Chọn hoặc viết 3 giây đầu; xếp hạng kiểu hook; ví dụ tiếng Việt. |
| `before-after.md` | Cách dựng TRƯỚC/SAU cho tẩy vết bẩn: kỹ thuật editor trên thế giới dùng, thẻ `compare`, chọn cặp khung hình, cảnh báo chính sách quảng cáo của TikTok. |
| `pacing-and-transitions.md` | Nhịp, cấu trúc video, re-hook, xử lý footage không khớp luật. |
| `transitions.md` | Danh mục 11 chuyển cảnh, toán học căn giữa điểm cắt, chuyển cảnh shader trên Windows, công thức "chưa mượt". |
| `camera-moves.md` | Push/pull/pan/hold, phóng theo từ khóa, cách tránh "khựng". |
| `typography.md` | Font có tiếng Việt, quy tắc không khung viền, 5 kiểu tiêu đề, kiểu nào đọc được trên vải trắng. |
| `layout-and-motion-graphics.md` | Vùng an toàn 1080×1920, bố cục theo loại nội dung, danh mục thành phần đồ họa và khóa nội dung. |
| `sync-and-timing.md` | Cắt ở chỗ lặng, neo đồ họa theo từ, nhạc nền hạ tiếng khi có lời, cách kiểm tra khớp. |
| `captions-and-text.md` | Nhóm phụ đề, vị trí, SRT. |
| `footage-ingest.md` | Soi clip, shot log, chia ngân sách footage cho nhiều video, xuất danh sách cắt ffmpeg. |
| `voiceover-and-captions.md` | ElevenLabs (mô hình, thẻ cảm xúc, chi phí), căn phụ đề, **giọng có sẵn**. |
| `audio-and-music.md` | Trộn âm, bản quyền nhạc, tiếng hiện trường. |
| `sound-design.md` | Hiệu ứng âm thanh (SFX): nguồn nào dùng được về bản quyền, bộ âm thanh của kit, tiếng nào cho sự kiện nào, mức âm lượng, thời điểm đặt, cách kiểm tra. |
| `remotion-output.md` | Giấy phép Remotion, pipeline render, bố cục template, quy tắc để render đúng. |

### 6.3 `scripts/` — công cụ dòng lệnh

Chạy từ thư mục skill. Chỉ `align_captions.py` cần venv (nó tự khởi chạy lại trong venv của bộ công cụ); phần còn
lại chỉ cần Python 3 và ffmpeg.

| Script | Việc làm | Vào → Ra |
|---|---|---|
| `inspect_footage.py` | Đọc thuộc tính thật của clip (thời lượng, độ phân giải, xoay, fps, có tiếng không), cảnh báo clip ngang, thiếu tiếng, lệch định dạng; `--log` in bảng shot log trống. | thư mục clip → báo cáo |
| `contact_sheet.py` | Ảnh tổng hợp khung hình: một hàng cho mỗi clip thô; hoặc giữa mỗi cảnh + mỗi điểm cắt của video đã render. | clip/video → `.png` |
| `trim_voice.py` | `--silences` liệt kê chỗ lặng và điểm cắt; `--keep a-b,c-d` nối các đoạn giữ lại. | giọng → giọng ngắn hơn |
| `make_sfx.py` | Tự tạo 6 tiếng hiệu ứng (pop, tick, ding, thud, swoosh, riser) bằng ffmpeg: không tải gì, không vướng bản quyền; đỉnh −3 dB như các file CC0. | thư mục → `.wav` |
| `make_voiceover.py` | Tạo giọng bằng ElevenLabs, mỗi dòng một file; `--quota`, `--dry-run` (không tiêu credit), từ chối chạy nếu không đủ credit. | `script.txt` → `.mp3` + `voice_manifest.json` |
| `align_captions.py` | Whisper cho **thời gian**, kịch bản cho **chữ**; gộp nhóm phụ đề quá ngắn; `--words-out` ghi thời gian từng từ. | giọng + script → `captions.srt`, `words.json` |
| `suggest_cuts.py` | Gợi ý điểm cắt cảnh từ `words.json`: cắt đúng chỗ lặng của giọng, không cắt giữa từ, cảnh 2,5–4 s, nhịp hook ngắn (quy hoạch động); `--prefer` ưu tiên chỗ đổi shot. | `words.json` → bảng/`cuts.json` |
| `plan_scenes.py` | Điền cột Source/In của bảng Scenes từ **thư viện shot** sao cho không đoạn nào dùng hai lần (trong và giữa các video), chọn Transition và Camera theo loại shot; thoát 1 khi footage hết. | `library.json` + `cuts.json` → bảng Scenes |
| `pacing_checker.py` | Cổng kiểm tra luật nhịp (hook, cảnh ≤ 4 s và ≥ 2,5 s ngoài hook, liền mạch, tổng thời lượng). Thoát 1 nếu vi phạm. | `edit-plan.md` → báo cáo |
| `footage_overlap_checker.py` | Biến mỗi cảnh thành khoảng nguồn `[In, In+độ dài]` và báo trùng/sát nhau trong và giữa các plan; `--clips` liệt kê đoạn còn trống. | các `edit-plan.md` → báo cáo |
| `plan_to_project.py` | Biên dịch kế hoạch thành `project.json`; tự gán camera (`--auto-camera`), phóng theo từ khóa (`--punch-keywords`); in **báo cáo bắt nhịp**; `--auto-sfx` thêm hiệu ứng âm thanh theo `sfx-map.json`; báo thiếu file (clip, giọng, nhạc, SFX) trong `public/`. | `edit-plan.md` + SRT + words → `project.json` |
| `new_remotion_project.py` | Tạo dự án render từ template; `--proxies` làm bản proxy ffmpeg; `--install` chạy npm; `--update` chép lại template vào dự án cũ; luôn đặt bộ SFX vào `public/sfx/`. | → thư mục dự án |

### 6.4 `assets/`

| Đường dẫn | Chức năng |
|---|---|
| `edit-plan-template.md` | Mẫu kế hoạch dựng: bảng **Scenes** (Start, End, Source, In, Type, Transition, Camera, Shot, Audio), bảng **Overlays** (Start, End, Component, Zone, Tone, Content), danh sách soát tuân thủ. |
| `shot-library.example.json` | Mẫu thư viện shot cho `plan_scenes.py`: mỗi đoạn một loại shot (`kind`), điểm hành động (`focus`), cỡ cảnh (`size`). |
| `sfx/` | Bộ hiệu ứng âm thanh: 5 file ghi âm CC0 (`whoosh`, `whip`, `switch`, `mouse-click`, `shutter-modern`), `SOURCES.md` (tác giả, nguồn, giấy phép từng file), `sfx-map.json` (tiếng nào cho sự kiện nào, mức dB, độ dẫn trước). |
| `remotion-template/` | Dự án Remotion điều khiển bằng dữ liệu (mục 7). |

### 6.5 `evals/` — bộ ca kiểm tra skill

Ba ca: `full-edit-plan-from-brief` (lập plan đầy đủ từ brief), `pushes-back-on-too-short` (từ chối làm video 15 giây,
giải thích lý do), `rejects-banned-claims` (bắt claim cấm và đề xuất câu thay). Mỗi ca có `prompt.md`, `case.yaml` và
thư mục `graders/` (tiêu chí chấm từng điểm). *Đã cập nhật theo luật hiện hành nhưng chưa chạy lại.*

## 7. `assets/remotion-template/` — template render

Một composition duy nhất, `Short`, đọc `project.json` qua `--props`. **Không có chữ nội dung video trong code.**

| Đường dẫn | Chức năng |
|---|---|
| `package.json` · `tsconfig.json` · `remotion.config.ts` | Phụ thuộc ghim đúng phiên bản; cấu hình TypeScript; bộ GL `angle` để chuyển cảnh shader và light leak chạy trên Windows. |
| `project.example.json` | Thư viện mẫu không cần footage: đủ kiểu chữ và đồ họa; mở bằng `npm run studio`. |
| `src/index.ts` · `src/Root.tsx` | Đăng ký composition; độ dài lấy từ `duration` và `fps` trong dữ liệu (`calculateMetadata`). |
| `src/project.ts` | **Hợp đồng dữ liệu**: kiểu `Project`, `Scene`, `Overlay`, `Caption`, `Word`, `Camera`… |
| `src/theme.ts` | **Mọi token thiết kế**: font, bảng màu, vùng bố cục, điểm giỏ hàng (112, 1677; đo từ ảnh chụp màn hình TikTok thật), đường cong chuyển động, giới hạn camera, thông số thẻ so sánh. Đổi diện mạo ở đây. |
| `src/engine/timeline.ts` | Dàn cảnh với chuyển cảnh **căn giữa điểm cắt**, để giọng không bị lệch. |
| `src/engine/transitions.tsx` | Bảng chuyển cảnh: có sẵn của Remotion + `zoomThrough`, `blurDissolve`, `whip`. |
| `src/engine/camera.ts` | Camera ảo: push, pull, pan, hold, phóng theo từ khóa. |
| `src/engine/audio.tsx` | Giọng, nhạc nền tự hạ khi có lời, hiệu ứng âm; nằm ngoài chuỗi chuyển cảnh nên không bị xê dịch. |
| `src/engine/Short.tsx` | Composition: nối cảnh, camera, lớp đồ họa, phụ đề, âm thanh. |
| `src/components/registry.tsx` | Tên thành phần dùng trong `project.json`; tên lạ sẽ báo lỗi. |
| `src/components/anim.ts` | Hàm hoạt họa dùng chung (vào/ra, spring, vừa khung). |
| `src/components/text/` | `Title.tsx` (5 kiểu: outline, stack, gradient, glass, marker), `Captions.tsx` (karaoke/plain), `primitives.tsx` (chữ viền, chữ gradient, chữ trồi qua mặt nạ). |
| `src/components/graphics/` | 13 thành phần: `Callout`, `Lists` (checklist, step), `Price`, `Pointers` (mũi tên cong chỉ đúng ô giỏ hàng của TikTok Shop, vòng khoanh, sticker), `Media` (kính lúp, **dải 3 hình nhỏ ở đầu `thumbs`**, **thẻ so sánh TRƯỚC/SAU `compare`**), `Ranking`, `Bars` (thanh tiến trình, thẻ tên). |

## 8. Nằm ngoài repo (do `setup.sh` và quá trình làm việc tạo ra)

| Vị trí | Nội dung |
|---|---|
| `~/.local/share/short-video-kit/venv` | Môi trường Python (đổi bằng `SVK_PYTHON`). |
| `~/.cache/short-video-kit/models` | Mô hình Whisper `small` (đổi bằng `WHISPER_MODEL_DIR`). |
| `~/.config/short-video-kit/env` | Khóa ElevenLabs, quyền 600. |
| `~/.claude/skills/short-video-editing` | Bản skill đã cài (chạy lại `setup.sh` sau mỗi `git pull`). |
| `<thư-mục-làm-việc>/<video>/` | `script.txt`, `voice.mp3`, `captions.srt`, `words.json`, `edit-plan.md` của từng video. |
| `<thư-mục-làm-việc>/render/` | Một dự án Remotion cho cả lô (`public/clips` = proxy, `public/audio` = giọng). |

## 9. Công cụ đang dùng

| Công cụ | Phiên bản | Vai trò |
|---|---|---|
| Claude Code (skill + `CLAUDE.md`) | hiện hành | Điều phối: đọc chỉ dẫn, lập kế hoạch, chạy công cụ, báo cáo. |
| Python | 3.10+ (thử trên 3.12 Windows, 3.14 Linux) | Mọi script. |
| faster-whisper (CTranslate2) | 1.2.1, mô hình `small` | Lấy **thời gian** từng từ của giọng. |
| numpy | — | Xử lý mẫu âm cho Whisper. |
| ffmpeg / ffprobe | bản gần đây | Đọc thuộc tính clip, proxy, `silencedetect`, `atrim`/`concat`, ảnh tổng hợp, nén bản gửi điện thoại. |
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

1. **Dựng bằng dữ liệu.** Kế hoạch (Markdown) → `project.json` → một composition. Đổi video = đổi bảng, nên Claude
   không phải viết lại code mỗi lần và kết quả lặp lại được.
2. **Chữ lấy từ kịch bản, thời gian lấy từ Whisper.** Whisper nghe sai tiếng Việt ("túi xách" → "tui sách"). Chuỗi từ
   của Whisper được so khớp với chuỗi từ của kịch bản (bỏ dấu, hạ chữ thường) rồi giữ chính tả của kịch bản.
3. **Cắt ở chỗ lặng của giọng.** `silencedetect` (−35 dB) tìm khoảng lặng; không bao giờ cắt giữa từ. Với giọng có
   sẵn: chép nháp → sửa tay cho khớp lời thật → căn lại.
4. **Chuyển cảnh căn giữa điểm cắt.** Chuyển cảnh chồng hai cảnh nên tổng ngắn đi; template đặt
   `begin = cut − T/2`, `finish = cutTiếp + T/2`, đọc nguồn sớm `T/2`, nhờ vậy điểm cắt trùng đúng chỗ giọng đã định.
5. **Camera ảo liên tục.** Phóng/kéo/lia bằng thang tỉ lệ cảm nhận được (`perceptual-scale`), không reset ở điểm cắt;
   phóng theo từ khóa bằng spring ngắn.
6. **Đồ họa neo theo từ.** `@"chai hồng"` đưa đồ họa vào trước từ đó 3 khung hình; thời gian giữ =
   `max(0,83 s; 0,3 s + số ký tự ÷ 15)`; tắt trước điểm cắt tiếp theo ít nhất 3 khung hình.
7. **Vùng an toàn và mật độ.** Khung 1080×1920 có vùng cấm (đầu, cuối, thanh nút bên phải); phụ đề có dải riêng; tối đa
   hai thành phần thông tin cùng lúc; không chữ trong khung viền trên cảnh demo (yêu cầu của khách).
8. **Chia ngân sách footage.** Mỗi cảnh thành khoảng nguồn `[In, In+độ dài]`; kiểm tra giao nhau trong và giữa các plan
   với biên 0,5 giây (chuyển cảnh mượn ~0,2 giây mỗi bên); liệt kê đoạn còn trống để lập video kế tiếp.
9. **Proxy.** Footage iPhone là 4K HEVC có siêu dữ liệu xoay; dựng từ bản proxy H.264 1080×1920 30 fps để nhanh và đúng
   chiều.
10. **Báo cáo bắt nhịp.** Tự bắt: điểm cắt rơi giữa từ, chữ hiện/tắt sát điểm cắt, đồ họa lấn vùng giao diện TikTok, hai
    thành phần chồng cùng vùng, nhóm phụ đề nhấp nháy, thiếu file trong `public/`.
11. **Kiểm bằng mắt.** `contact_sheet.py` cho ảnh giữa mỗi cảnh + mỗi điểm cắt; đây là nơi lộ lỗi như chữ trắng chìm
    trên áo trắng hay vòng khoanh lệch.
12. **Kiểm tra máy mới.** `setup.sh --check`, `selftest.sh` (11 nhóm), thử sạch trên bản clone mới với `HOME` trống,
    và một Claude không có ngữ cảnh đọc thử repo để tìm chỗ thiếu.
13. **Hiệu ứng âm thanh theo bảng.** Mỗi tiếng có mức dB và "độ dẫn" (`lead`) đo từ đỉnh của file để đỉnh rơi đúng
    điểm cắt; chuyển cảnh trượt/quét có tiếng vút, chuyển cảnh mờ và khoảnh khắc lộ kết quả để im; tối đa 2 tiếng
    trong 3 giây và cách nhau ≥ 0,2 giây. Chỉ dùng âm thanh CC0 hoặc tự tạo bằng ffmpeg (`make_sfx.py`).
14. **Giữ repo sạch.** Không file thừa, không code chết, không nội dung video trong template; khóa, media, mô hình và
    thư mục làm việc luôn nằm ngoài git.
