# Luồng làm việc — từ clip thô tới video hoàn chỉnh

Lệnh chạy từ `skill/short-video-editing/` (hoặc `~/.claude/skills/short-video-editing/` sau khi cài).
Claude chạy các bước này khi bạn nhờ; tài liệu này để bạn hiểu và kiểm lại.

**Trước khi bắt đầu, trên mọi máy:** `./setup.sh --check` (Windows: chạy bash của Git Bash). Thiếu gì thì
`./setup.sh`; sau mỗi lần `git pull` chạy lại `./setup.sh` để bản skill đã cài khớp với repo.

**Python:** trong tài liệu `python3` nghĩa là Python 3 bất kỳ. Trên Windows dùng `python` hoặc
`~/.local/share/short-video-kit/venv/Scripts/python.exe` (lệnh `python3` có thể là bản giả của Microsoft Store).

**Gói giao việc điển hình:** PDF kịch bản (KB4, KB7…) + thư mục clip thô + thư mục giọng mẫu + độ dài 30–40 s.
Làm theo đúng thứ tự dưới đây; file làm việc để **ngoài repo**:

```
<thư-mục-làm-việc>/
├── kb7/  script.txt  voice.mp3  captions.srt  words.json  edit-plan.md
├── kb4/  ...                                   (mỗi video một thư mục)
└── render/                                     (một dự án Remotion cho cả lô: public/clips = proxy)
```

```
clip thô ─► [1 soi + chia ngân sách footage] ─► [2 hook] ─► [3 bảng Scenes] ─► [4 bảng Overlays]
                                                                  │                 │
voice ─► [5 phụ đề + thời gian từng từ] ─────────────────────────────┴─────────┐       │
                                                                             ▼       ▼
                                   [6 pacing_checker + footage_overlap_checker] ─► [7 plan_to_project]
                                                                                       │ sync report
                                                                       [8 still → render Remotion] ◄┘
```

## Các bước

### 1. Soi clip, chia ngân sách footage
```bash
python3 scripts/inspect_footage.py /duong/dan/clips --log
python3 scripts/contact_sheet.py /duong/dan/clips --out clips.png    # mỗi clip một hàng khung hình: mở ảnh ra xem
```
Lập shot log theo **loại khoảnh khắc** (TRƯỚC, SAU, ĐỔ CHAI, CẦM SẢN PHẨM, VÒ, VẤN ĐỀ). Một lô footage phải
nuôi **nhiều video nhất có thể**: chia khoảng nguồn cho từng video, không dùng lại đoạn nào
(`references/footage-ingest.md` §1b).

### 2. Chọn hook (0–3 giây)
Có biến đổi nhìn thấy được → dùng (TRƯỚC → SAU trong 3 giây đầu); có social proof thật → dùng; nêu được vấn đề
cụ thể → pain point; còn lại → giới thiệu sản phẩm. `references/hook-library.md`.

### 3. Bảng Scenes
Dùng `assets/edit-plan-template.md`. Cảnh **3–4 giây** (ngoài hook), cắt **ở khoảng lặng của giọng**, không
cắt giữa từ. Mỗi cảnh có cột **Transition** (`fade`, `slide up`, `wipe right +leak`, `zoomThrough +flash`…) và
**Camera** (`push 1.0>1.08`, `pull`, `pan left 6%`, `hold`, hoặc để trống cho `--auto-camera`).

### 4. Bảng Overlays (chữ và đồ hoạ)
Mỗi dòng một thành phần: `title` (5 kiểu: outline, stack, gradient, glass, marker), `callout`, `highlight`,
`step`, `checklist`, `price`, `cart`, `sticker`, `progress`, `magnifier`, `thumbs`, `compare`, `ranking`, `lowerThird`,
cùng `punch` (phóng theo từ khoá) và `sfx`. Thời điểm có thể neo theo từ: `@"chai hồng"`.
Quy tắc: không đè lên mặt, tránh thanh nút bên phải, không quá 2 thành phần thông tin cùng lúc, đổi kiểu tiêu
đề giữa các nhịp, chữ trên màn hình nói điều **khác** lời đọc. `references/layout-and-motion-graphics.md`,
`references/typography.md`.

### 5. Giọng đọc + phụ đề
```bash
python3 scripts/make_voiceover.py --quota                              # gói + credit còn lại
python3 scripts/make_voiceover.py script.txt --voice <id> --dry-run    # tính phí, không tiêu
python3 scripts/make_voiceover.py script.txt --voice <id> --out audio/
python3 scripts/align_captions.py voice.mp3 --script script.txt --out captions.srt --words-out words.json
```
Soát claim theo `references/platform-specs.md` §7 **trước khi** tạo giọng.

**Giọng có sẵn (không tạo mới):**
```bash
python3 scripts/trim_voice.py voice.mp3 --silences                       # nếu > 45 s: liệt kê chỗ lặng + điểm cắt
python3 scripts/trim_voice.py voice.mp3 --keep 0-3.8,8.3-16.1 --out voice_short.mp3   # bỏ trọn câu, ghi rõ câu nào
python3 scripts/align_captions.py voice_short.mp3 --out draft.srt         # bản chép nháp (Whisper nghe sai tiếng Việt)
# sửa tay cho khớp lời đọc thật → script.txt, rồi:
python3 scripts/align_captions.py voice_short.mp3 --script script.txt --out captions.srt --words-out words.json
```
Đọc giọng để tìm câu có claim không được lặp lại trên màn hình ("sạch tinh", "tiết kiệm tiền trăm tiền triệu"…) và
báo người dùng; không tự ý sửa lời đã thu.

### 6. Kiểm kế hoạch
```bash
python3 scripts/pacing_checker.py edit-plan.md
python3 scripts/footage_overlap_checker.py kb7/edit-plan.md kb4/edit-plan.md kb9/edit-plan.md --clips /duong/dan/clips
```

### 7. Biên dịch kế hoạch
```bash
python3 scripts/plan_to_project.py edit-plan.md --out du-an-render/kb7.json \
    --voice audio/kb7.mp3 --captions captions.srt --words words.json --auto-camera \
    --punch-keywords "saiza,chai xanh" --auto-sfx
```
`--auto-sfx` thêm hiệu ứng âm thanh theo bảng `assets/sfx/sfx-map.json`: chuyển cảnh trượt/quét có tiếng vút, cảnh
BEFORE → AFTER có tiếng chụp ảnh, mũi tên giỏ hàng có tiếng click, bước đánh số có tiếng bấm; chuyển cảnh mờ dần
và khoảnh khắc lộ kết quả để im (xem `references/sound-design.md`). Chỉ dùng âm thanh CC0 hoặc tự tạo. Sau khi
render phải **nghe thật** trước khi giao.
Đọc **sync report**: điểm cắt rơi giữa từ, chữ hiện/tắt sát điểm cắt, đồ hoạ lấn thanh nút, hai thành phần
chồng cùng vùng, phụ đề nhấp nháy.

### 8. Render
```bash
python3 scripts/new_remotion_project.py ~/renders/saiza --install --proxies "/duong/dan/clips"   # một lần
cp voice.mp3 ~/renders/saiza/public/audio/kb7.mp3     # giọng nằm trong public/ để Remotion thấy
cd ~/renders/saiza
npx remotion still src/index.ts Short out/kiemtra.png --frame=45 --props=kb7.json
npx remotion render src/index.ts Short out/kb7.mp4 --props=kb7.json --codec=h264 --crf=18
```
`npm run studio` mở bộ mẫu `project.example.json` để xem mọi kiểu chữ và đồ hoạ khi chưa có footage.

### 9. Kiểm cuối
```bash
python3 scripts/contact_sheet.py out/kb7.mp4 --project du-an-render/kb7.json --out out/sheet.png
ffprobe -v error -show_entries format=duration -of csv=p=0 out/kb7.mp4        # khớp với kế hoạch
ffmpeg -i out/kb7.mp4 -c:v libx264 -crf 24 -c:a aac -b:a 128k -movflags +faststart out/kb7_nen.mp4   # bản < 30 MB để gửi điện thoại
```
Mở bảng khung hình (giữa mỗi cảnh + mỗi điểm cắt) và **nhìn thật**: chữ chìm trên vải trắng, vòng khoanh lệch,
chữ đè lên mặt hay vật. Nghe trọn video. Nhạc phải từ Commercial Music Library của TikTok; khi đăng bật
**"Disclose commercial content"**. Báo cáo cho người dùng: những gì **chưa** kiểm (ví dụ chưa nghe trọn video).

## Quy tắc cứng (trong SKILL.md, máy kiểm)

1. Hook xong trong 3 giây đầu (hình + chữ + tiếng, mỗi kênh một việc).
2. Cảnh 3–4 giây: không quá 4, ngoài hook không dưới 2,5.
3. Mọi kế hoạch có timestamp từng cảnh.
4. Tổng 25–45 giây, lý tưởng 30–40.
5. Soát claim thương mại trước khi giao.
6. Một lô footage nuôi nhiều video; không đoạn nào dùng hai lần.
7. Đồ hoạ tôn trọng khung hình: không đè mặt, không vào vùng giao diện TikTok, phụ đề có dải riêng.
