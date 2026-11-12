# Luồng làm việc — từ clip thô tới video hoàn chỉnh, cho mọi thể loại

Lệnh chạy từ `skill/short-video-editing/` (hoặc `~/.claude/skills/short-video-editing/` sau khi cài).
Claude chạy các bước này khi bạn nhờ; tài liệu này để bạn hiểu và kiểm lại.

**Trước khi bắt đầu, trên mọi máy:** `./setup.sh --check` (Windows: bash của Git Bash). Thiếu gì thì
`./setup.sh`; sau mỗi `git pull` chạy lại `./setup.sh` để bản skill đã cài khớp với repo.

**Python:** `python3` nghĩa là Python 3 bất kỳ. Trên Windows dùng `python` hoặc
`~/.local/share/short-video-kit/venv/Scripts/python.exe` (lệnh `python3` có thể là bản giả của Microsoft Store).

## Ý tưởng chính: playbook theo thể loại

Mọi thứ phụ thuộc **loại video** nằm trong một *playbook* (`playbooks/<id>.json` cho máy đọc +
`playbooks/<id>.md` cho người/Claude đọc): độ dài, hook, độ dài cảnh, cắt theo giọng hay theo nhạc, cấu trúc
các nhịp, chuyển cảnh, chuyển động camera, kiểu phụ đề, bảng màu, "look" màu, hiệu ứng âm thanh, đồ hoạ nên
dùng/tránh, danh sách tuân thủ. Kế hoạch dựng ghi `**Playbook:** <id>` ở đầu; mọi script đọc luật từ đó.

| Playbook | Dùng cho | Cắt theo |
|---|---|---|
| `product-demo` (`:unboxing`, `:listicle`) | review/demo sản phẩm TikTok Shop, trước/sau | giọng |
| `real-estate` (`:voiceover`) | tour căn hộ, nhà phố, villa, homestay, đất | nhạc |
| `food-fnb` (`:review`) | món ăn, quán, đồ uống | nhạc |
| `talking-head` (`:testimonial`, `:agency`) | chuyên gia, chia sẻ, câu chuyện, cảm nhận khách; `:agency` = video giới thiệu dịch vụ cắt từ các take của người dẫn | giọng trên camera (jump cut) |
| `tutorial` | hướng dẫn, công thức, từng bước | giọng |
| `fashion-beauty` | thử đồ, lookbook, makeup, skincare | nhạc |
| `montage-recap` | du lịch, sự kiện, khai trương, hậu trường | nhạc |
| `promo-sale` | khuyến mãi, ra mắt, thông báo | nhạc |

Thư mục làm việc để **ngoài repo**:

```
<thư-mục-làm-việc>/
├── v1/  script.txt  captions.srt  words.json  edit-plan.md      (mỗi video một thư mục; giữ mọi edit-plan.md)
├── analysis.json  clips.png  library.json
└── render/                                                       (một dự án Remotion cho cả lô)
    ├── public/clips   proxy đã hiệu chỉnh + corrections.json
    ├── public/audio   giọng đã làm sạch, nhạc đã cân mức
    └── public/images  logo, mặt bằng, packshot (nếu có)
```

## Các bước

### 1. Phân tích nguồn và ý định → chọn playbook
```bash
python3 scripts/inspect_footage.py /duong/dan/clips --measure --json analysis.json   # sáng, ám màu, nhiễu, rung, camera di chuyển, có người nói, HDR, fps
python3 scripts/contact_sheet.py /duong/dan/clips --out clips.png                     # MỞ RA XEM
python3 scripts/playbook.py suggest --intent "lời yêu cầu của bạn" --analysis analysis.json
python3 scripts/playbook.py show real-estate
```
Nếu yêu cầu và footage khớp nhau, Claude nói chọn playbook nào và vì sao (một dòng) rồi làm tiếp. Nếu lệch
nhau hoặc thiếu dữ kiện (giá, diện tích, địa chỉ, ngày khuyến mãi, có giọng hay chỉ nhạc), Claude hỏi **tối
đa 3 câu**, mỗi câu kèm phương án mặc định. Lô nhiều video: tính ngân sách footage trước
(`references/footage-ingest.md` §1b, `references/policy.md` §4.1).

### 1b. Khách đưa video mẫu ("làm giống cái này")
```bash
python3 scripts/analyze_reference.py mau.mp4 --out ref/ --dense 0-3,15-20   # đo: số cảnh, chuyển cảnh, cú nháy, màu, độ ồn + ảnh tổng hợp
```
Mở `ref/report.md`, `scenes.png`, mọi `dense_*.png` (cứ 2 khung hình một lần trong đoạn: cú nháy trên khung 0, 2, 4, đống chữ đang
ghép lại) và `spectrum_*.png` (tiếng click là vạch đứng, whoosh là dải chéo), rồi **nhìn**. Số đo cho thời điểm chính xác tới khung
hình; ảnh cho biết đó là kỹ thuật gì. Liệt kê từng kỹ thuật thấy được, tìm nó trong `references/capcut-techniques.md` và
`references/layout-and-motion-graphics.md`; kỹ thuật bộ công cụ chưa có thì **nghiên cứu và thêm thành thành phần** (kèm dòng tài
liệu và selftest), không làm nhái. Người dẫn nói trước ống kính giới thiệu dịch vụ → `references/agency-pitch-recipe.md` (10 bước).
Logo và sản phẩm khách đưa lên thẻ thuộc về khách: xin file vector và sự đồng ý. Không dùng nhạc, footage của video mẫu.

### 2. Chuẩn bị footage (hiệu chỉnh + màu)
```bash
python3 scripts/new_remotion_project.py ~/renders/lo1 --playbook real-estate --proxies /duong/dan/clips   # --install lần đầu (hỏi trước: ~300 MB)
python3 scripts/contact_sheet.py ~/renders/lo1/public/clips --out proxies.png
```
`prepare_footage.py` (được `--proxies` gọi) tự: chuyển HDR iPhone về SDR, cắt khung 9:16, khử nhiễu khi cảnh tối
và nhiễu, chống rung khi rung, cân bằng trắng (đo trên điểm ảnh trung tính), chỉnh phơi sáng, áp "look" màu của
playbook (gộp vào một LUT 3D). Video trước/sau (`correction: shared`) dùng **cùng một** hiệu chỉnh cho mọi clip.
Căn thẳng đường chân trời: `--fix "IMG_0402:rotate=-1.2"`. Cần slow-motion 0,5x: thêm `--slowmo` (giữ 60 fps).
Xem `corrections.json` để biết đã làm gì với clip nào.

### 3. Âm thanh
**Giọng có sẵn:**
```bash
python3 scripts/trim_voice.py voice.mp3 --silences                                   # quá dài so với playbook: liệt kê chỗ lặng
python3 scripts/trim_voice.py voice.mp3 --keep 0-3.8,8.3-16.1 --out voice_ngan.mp3   # bỏ trọn câu, ghi rõ câu nào
python3 scripts/process_audio.py voice voice_ngan.mp3 --out ~/renders/lo1/public/audio/v1.wav   # khử ồn (nếu cần), EQ, de-ess, nén, −16 LUFS
python3 scripts/align_captions.py ~/renders/lo1/public/audio/v1.wav --out draft.srt # bản chép nháp → sửa tay → script.txt
python3 scripts/align_captions.py ~/renders/lo1/public/audio/v1.wav --script script.txt --out captions.srt --words-out words.json
```
**Người nói trước camera (talking head):**
```bash
python3 scripts/trim_voice.py noi.mp4 --jumpcut --out noi_cat.wav --scenes-out cuts.json   # bỏ mọi khoảng lặng > 0,35 s; mỗi đoạn giữ lại là một cảnh
python3 scripts/process_audio.py voice noi_cat.wav --out ~/renders/lo1/public/audio/v1.wav
```
**Giọng tạo bằng ElevenLabs:** soát claim trước, rồi `make_voiceover.py --quota` → `--dry-run` → tạo giọng →
`process_audio.py voice … --no-clean`.
**Nhạc** (có giấy phép thương mại cho nền tảng): `process_audio.py music nhac.mp3 --out ~/renders/lo1/public/audio/music.wav`.

### 4. Cắt cảnh và lập kế hoạch
```bash
python3 scripts/suggest_cuts.py words.json --playbook product-demo --json > cuts.json                        # cắt theo chỗ lặng của giọng
python3 scripts/suggest_cuts.py --music ~/renders/lo1/public/audio/music.wav --end 40 --playbook real-estate --json > cuts.json   # cắt theo beat
python3 scripts/playbook.py skeleton real-estate --cuts cuts.json --title "Villa Thảo Điền" > v1/edit-plan.md
python3 scripts/plan_scenes.py --library library.json --plan v1/edit-plan.md --kinds "VIEW,ROOM,EXTERIOR,..." --used v0/edit-plan.md
```
Bộ khung điền sẵn Type, Transition, Speed, gợi ý từng nhịp và danh sách tuân thủ. Hoàn thiện bảng **Scenes**
(Source/In, Camera hoặc để trống cho `--auto-camera`, Speed: `2x` cho đoạn chờ, `ramp 1>2>1` qua cửa,
`0.5x` cho cảnh "money shot" 60 fps) và bảng **Overlays** (chữ và đồ hoạ: `title`, `specs`, `pin`, `label`,
`stat`, `chart`, `price`, `step`, `checklist`, `thumbs`, `compare`, `image`, `cart`…; neo theo từ bằng
`@"cụm từ"`). Chữ trên màn hình nói điều **khác** lời đọc; mọi con số lấy từ người dùng/giấy tờ.

### 5. Kiểm kế hoạch
```bash
python3 scripts/pacing_checker.py v1/edit-plan.md                          # luật của playbook ghi trong plan
python3 scripts/footage_overlap_checker.py v1/edit-plan.md v0/edit-plan.md --clips /duong/dan/clips
```

### 6. Biên dịch và render
```bash
python3 scripts/plan_to_project.py v1/edit-plan.md --out ~/renders/lo1/v1.json --voice audio/v1.wav --music audio/music.wav \
    --captions captions.srt --words words.json --auto-camera --analysis analysis.json --auto-sfx [--platform reels-ad]
cd ~/renders/lo1
node stills.mjs v1.json out/s --cuts                                  # một lần bundle: ảnh sau mỗi điểm cắt và giữa mỗi cảnh (hoặc --every 0.5 --from 0 --to 8, hoặc liệt kê giây)
python3 scripts/montage.py "out/s_*.jpg" --cols 6 --out out/sheet.jpg  # NHÌN từng chuyển cảnh, hiệu ứng chữ, thẻ trên một ảnh
npx remotion render src/index.ts Short out/v1.mp4 --props=v1.json --codec=h264 --crf=18 --concurrency=5
```
`--concurrency=5`: 8 luồng báo "No frame found at position" với proxy cao 2880. Đọc dòng "wrote …" sau mỗi lần biên dịch: tham số
bị argparse từ chối (`--music-levels -6,-6` phải viết `=`) có thể để lại project cũ và video render ra không có nhạc.
Đọc **sync report**: cắt giữa từ, chữ hiện/tắt sát điểm cắt, đồ hoạ lấn vùng giao diện (TikTok, quảng cáo Reels),
thành phần playbook không nên dùng, slow-motion sẽ giật, thiếu file trong `public/`.

### 6b. (Tuỳ chọn) Render bằng HyperFrames thay cho Remotion
Cùng `project.json`, renderer thứ hai (Apache-2.0, không tính ghế như Remotion). Chọn theo từng video và nói lý do:
HyperFrames hợp khi studio vượt giới hạn 3 nhân viên của Remotion, hoặc muốn hiệu ứng kiểu CapCut (`+shake`, `+glitch`,
`+rgb`, `+pulse` ở ô Transition; `--look vignette,grain`). **Không** vẽ `magnifier`, `thumbs`, `compare`, `ranking`: video
cần thẻ trước/sau thì dùng Remotion.
```bash
python3 scripts/new_remotion_project.py ~/renders/lo1 --playbook <id> --proxies /duong/dan/clips     # KHÔNG --install: chỉ lấy proxy + SFX
python3 scripts/plan_to_project.py … --out ~/renders/lo1/v1.json …                                    # như bước 6
python3 scripts/project_to_hyperframes.py ~/renders/lo1/v1.json --out ~/hf/v1 --playbook <id> [--look vignette=0.3,grain=0.05]
cd ~/hf/v1
npx hyperframes@0.9.26 check                       # hỏi người dùng trước lần npx đầu (tải gói); cần Node 22+, Chrome
npx hyperframes@0.9.26 snapshot --at 0.5,4,9,28    # NHÌN ảnh tổng hợp
npx hyperframes@0.9.26 render --quality high --output final.mp4
```
`check` phải 0 lỗi; cảnh báo `line_unread` trên phụ đề theo giọng nhanh là bình thường. Đo thực: video 28,5 s render ~55 s,
độ ồn −16,3 LUFS và thời lượng trùng Remotion, hình giống nhau khi đặt cạnh. Tiếp tục bước 7 với `final.mp4`.
Chi tiết, bẫy, mở rộng: `references/hyperframes-flow.md`; danh mục kỹ thuật CapCut: `references/capcut-techniques.md`.

### 7. Master âm thanh và xuất
```bash
python3 scripts/process_audio.py master out/v1.mp4 --out out/v1_final.mp4 --phone    # −14 LUFS, đỉnh ≤ −1 dBTP + bản nhẹ gửi điện thoại
python3 scripts/finish_video.py out/v1.mp4 --name TEN_v1 --out-dir out/final --audio-nomusic nomusic.wav --cover-at 3 --preview720   # quy trình agency
```
Remotion xuất dải màu full (`yuvj420p`): `finish_video.py` đổi về limited BT.709. Tài khoản doanh nghiệp TikTok không thể "nướng" nhạc có bản quyền
vào video: giao thêm một bản **không nhạc** để người dùng gắn nhạc từ Commercial Music Library khi đăng (`make_music.py` viết nền nhạc tự tạo).
Một bản master sạch dùng cho mọi nền tảng; **không** tải video từ TikTok về đăng lại lên Reels (dính watermark).

### 8. Kiểm cuối và báo cáo
```bash
python3 scripts/contact_sheet.py out/v1_final.mp4 --project ~/renders/lo1/v1.json --out out/sheet.png
python3 scripts/mix_report.py out/v1_final.mp4 --project ~/renders/lo1/v1.json --words words.json [--nomusic out/v1_nomusic.mp4]   # đo: dải màu, thời lượng, LUFS, đỉnh, nhạc có thật sự trong file
python3 scripts/check_lipsync.py ~/renders/lo1/v1.json out/v1_final.mp4 --clips /duong/dan/clip-goc   # giọng cắt từ các take: mọi cảnh lệch ≤ 1 khung hình
```
**Nhìn thật**: chủ thể không bị che, chữ đọc được (chữ trắng trên vải trắng), không lấn vùng giao diện, trước/sau
trung thực. Nghe trọn video. Báo cáo: playbook và lý do, thời lượng, số cảnh, hook, hiệu chỉnh đã áp cho footage,
sync report còn báo gì, claim đã sửa/đã gắn cờ, checklist đăng (`references/platforms.md` §6), những gì **chưa**
kiểm (ví dụ chưa nghe trọn video).

## Quy tắc chung (SKILL.md)

1. Phân tích footage + ý định trước khi lập kế hoạch; nói rõ chọn playbook nào và vì sao.
2. Hook xong trong 3 giây đầu; khung đầu không trống.
3. Nhịp đúng playbook (độ dài cảnh, tổng thời lượng) — `pacing_checker.py` kiểm.
4. Mọi kế hoạch có timestamp từng cảnh.
5. Soát claim theo playbook và `references/claims-and-compliance.md` trước khi đọc/viết.
6. Footage của mình hoặc có giấy phép; không dùng lại đoạn nào trong một lô; không xáo trộn một nguồn thành nhiều video.
7. Đồ hoạ tôn trọng khung hình và vùng an toàn của nền tảng.
8. Không giấu điểm cắt giữa trước/sau; cùng màu cho trước/sau; ghi rõ tua nhanh.
9. Nói rõ những gì chưa kiểm.
