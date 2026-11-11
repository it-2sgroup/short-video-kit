# Prompt chuẩn: dựng video ngắn bằng bộ skill `short-video-editing` (mọi thể loại)

Prompt này **không gắn với một thể loại hay một luồng cố định**. Mọi thứ phụ thuộc loại video (độ dài, nhịp,
cắt theo giọng hay theo nhạc, cấu trúc, màu, chữ, âm thanh, đồ hoạ, tuân thủ) nằm trong **playbook** của kit
(`product-demo`, `real-estate`, `food-fnb`, `talking-head`, `tutorial`, `fashion-beauty`, `montage-recap`,
`promo-sale` và các biến thể `:unboxing :listicle :voiceover :review :testimonial`). Prompt chỉ nói **ý
định, ràng buộc, danh mục kỹ thuật và tiêu chuẩn nghiệm thu**; số cụ thể do Claude lấy từ playbook
(`playbook.py show <id>`), không do prompt ghi cứng.

Cách dùng: copy khối **PROMPT** (mục 1–6), điền các ô `[...]`, xoá dòng không cần. Bỏ trống ô nào thì Claude
dùng mặc định của playbook hoặc hỏi lại (tối đa 3 câu, mỗi câu kèm phương án mặc định). Mục 7 là bản rút
gọn và ví dụ cho vài thể loại. Mở **chat mới** sau khi cài hoặc cập nhật skill (`./setup.sh`) để skill nạp.

---

## PROMPT

Dùng skill `short-video-editing`. Làm việc bằng tiếng Việt. Dựng cho tôi **[số] video** dọc 9:16,
**[độ dài mong muốn, hoặc "theo playbook"]**, đăng **[TikTok / TikTok Shop / Reels / Shorts]**
(**[organic / chạy quảng cáo]**). Mức hoàn thiện: **[bản demo gửi khách hàng / bản đăng thật]**, cả hình,
màu, ánh sáng, nhịp, chữ và âm thanh phải chỉn chu.

### 1. Brief (điền những gì đã biết)

- **Chủ đề / đối tượng:** `[sản phẩm, căn nhà, quán, món, người nói, sự kiện…]`, tên đúng như trên bao bì,
  thực đơn, giấy tờ: `[..]`.
- **Thể loại:** `[điền tên playbook nếu đã biết, hoặc "để Claude đề xuất"]`. Nếu để trống: chạy
  `playbook.py suggest` với footage và lời nhờ này, nói chọn cái nào và vì sao; nếu lời nhờ và footage lệch nhau
  thì hỏi, không ép footage vào một thể loại nó không gánh được.
- **Mục tiêu / CTA:** `[bán qua giỏ hàng · đặt lịch xem · ghé quán · kéo follow · lưu bài · nhận diện…]`.
- **Footage thô:** `[thư mục]` (máy quay/điện thoại, có thể 4K, HEVC, 10-bit, HDR, 60 fps).
- **Giọng:** `[đã có file: đường dẫn · cần tạo giọng (ElevenLabs) · người nói trước camera · chỉ nhạc]`.
- **Nhạc:** `[đã có file có giấy phép · nhờ Claude tìm (hỏi tôi trước khi tải) · không nhạc]`.
- **Video mẫu phong cách:** `[đường dẫn hoặc "không có"]`: nếu có, phân tích nó trước (nhịp, chuyển cảnh,
  camera, màu, chữ, nhạc, cảnh mở và cảnh kết, và nó đã dùng đoạn nào của footage).
- **Dữ kiện phải hiện trên màn hình** (chỉ lấy từ tôi hoặc giấy tờ, không bịa, không làm tròn): giá, diện
  tích (thông thủy hay tim tường), địa chỉ, giờ mở cửa, hạn khuyến mãi, mã giảm giá, tên người nói và chức
  danh… `[..]`. Không có thì không hiện.
- **Yêu cầu phong cách riêng của khách** (ưu tiên hơn mặc định của playbook, ghi lại trong plan):
  `[ví dụ: giữ cảnh mở xoay nghiêng · cảnh dài 3–4 s chuyển cảnh mềm · không chữ trong khung · bỏ âm
  thanh chuyển cảnh · tông chữ theo màu video · logo cuối video]`.
- **Lô nhiều video:** `[số video; cảnh nào được dùng chung giữa các video (ví dụ cảnh mở và cảnh kết); video
  cũ đã làm]`.

### 2. Quy tắc bất biến (vi phạm là hỏng, cái nào có công cụ thì công cụ kiểm)

1. **Phân tích trước khi lập kế hoạch:** xem contact sheet bằng mắt và đo footage (`inspect_footage.py
   --measure`); biết mục tiêu của tôi; chọn playbook từ cả hai.
2. **Hook xong trong 3 giây đầu**, khung hình đầu không trống. Hình, chữ và âm thanh mỗi kênh làm một việc khác
   nhau (`references/hook-library.md`).
3. **Nhịp theo playbook** (độ dài cảnh, tổng thời lượng, số nhịp hook): `pacing_checker.py` phải PASS. Nếu tôi
   xin độ dài ngoài khoảng của playbook thì nói khoảng đó và lý do, rồi để tôi quyết.
4. **Mọi plan có timestamp từng cảnh** theo `assets/edit-plan-template.md`, ghi `**Playbook:**`.
5. **Soát claim** (chữ trên màn hình, lời thoại, caption) theo checklist của playbook và
   `references/claims-and-compliance.md`. Claim nằm sẵn trong giọng tôi đưa thì **gắn cờ, không giữ lặng
   lẽ**; chữ trên màn hình không nhắc lại claim đó.
6. **Footage của tôi hoặc có giấy phép thương mại. Không dùng video của người khác. Không dùng lại một đoạn nguồn
   hai lần trong cả lô**, không xáo trộn một nguồn thành nhiều video (`footage_overlap_checker.py` trên **mọi**
   plan, kể cả plan dựng lại từ video mẫu). Hết cảnh thì dừng, báo số liệu, đề xuất quay thêm.
   Đọc `references/Chính sách.md` trước khi lập lô.
7. **Đồ hoạ tôn trọng khung hình:** không che mặt, không đè vùng giao diện nền tảng, tiêu đề dải trên
   (y ≈ 236–420), phụ đề một phần ba dưới (y ≈ 1340, ≤ 2 dòng), phần giữa dành cho footage, tối đa hai thành
   phần thông tin cùng lúc. Quảng cáo Reels dùng `--platform reels-ad`; không có mũi tên giỏ hàng trên Reels.
8. **Không dựng giả một phép chứng minh:** không giấu điểm cắt giữa TRƯỚC và SAU, cùng hiệu chỉnh màu cho cả hai,
   nén thời gian thì ghi trên màn hình. Quảng cáo trả phí không có so sánh trước/sau.
9. **Nói rõ điều chưa kiểm chứng.** Công cụ không nghe được: không viết "đã nghe" nếu chưa ai nghe.
10. **Những việc phải hỏi tôi, không tự quyết:** mọi lần tải (gói npm, model, **nhạc**, stock, binary: nêu tên,
    nguồn, giấy phép, dung lượng), gói ElevenLabs (bản miễn phí không dùng thương mại), giấy phép Remotion
    (miễn phí tới 3 nhân viên) so với HyperFrames, footage của bên thứ ba, số video khi footage không đủ, cắt giọng
    có sẵn hoặc bỏ claim (nói rõ câu nào), thể loại khi lời nhờ và footage lệch nhau, có chạy quảng cáo hay không.
11. **Chưa commit và chưa push** gì cho tới khi tôi nói. File làm việc nằm **ngoài repo**
    (`<work>/<video>/{script.txt,edit-plan.md,captions.srt,words.json}`, `analysis.json`, một `render/` cho cả lô).

### 3. Quy trình (đúng thứ tự; đưa kết quả thật, thất bại không gọi là thành công)

Chạy script trong `~/.claude/skills/short-video-editing/scripts`. Windows: `python -X utf8`, đường dẫn có dấu
cách đặt trong ngoặc kép, chạy một việc ffmpeg nặng một lúc.

0. **Máy sẵn sàng chưa:** `doctor.py` (thiếu gì thì hỏi trước khi cài). Sau `git pull` chạy lại `./setup.sh`.
1. **Phân tích và chọn playbook:** `contact_sheet.py` (mở xem), `inspect_footage.py --measure --json
   analysis.json`, `playbook.py suggest/show`, đọc `playbooks/<id>.md`. Nói lựa chọn trong một dòng.
2. **Chọn cảnh:** lập bảng cảnh theo loại (xem "Shots the footage needs" của playbook). Xem khung hình
   đầu, giữa, cuối của **từng** đoạn trước khi đưa vào plan. Loại cảnh tối đen, rung, vật cản che khung, mặt
   người nhìn thẳng ống kính khi chưa được phép, hai cảnh gần giống nhau. Lô nhiều video: tính ngân sách footage
   trước (`footage-ingest.md` §1b), dùng `plan_scenes.py` với `--used` và `--reserve`.
3. **Chuẩn bị hình:** `new_remotion_project.py RENDER --playbook <id> --proxies CLIPS` (hoặc `prepare_footage.py`
   với `--analysis`): tone-map HDR, đưa về 9:16, khử nhiễu khi tối hoặc nhiễu, chống rung khi rung, cân trắng
   từ điểm ảnh trung tính, chỉnh phơi sáng, grade của playbook gộp một LUT; `--fix "CLIP:rotate=-1.5"`,
   `--slowmo` khi cần chậm 0,5x. Đọc `corrections.json` và xem contact sheet proxy: cảnh tối phải được nâng sáng,
   hình không ngả màu lạ; nếu không clip nào được chỉnh dù thấy tối thì nghi phép đo và kiểm tra bằng mắt.
4. **Âm thanh:**
   - *Giọng có sẵn:* `process_audio.py measure`, `trim_voice.py --silences`/`--keep` nếu dài quá khoảng của
     playbook (bỏ trọn câu, báo câu nào), `process_audio.py voice`. **Nghe số đo 2 giây đầu và các khoảng nghỉ:**
     nếu còn rè, lách tách hay tiếng hít (bước chuẩn hoá có thể khuếch đại chúng), chặn phần không có lời bằng
     ngưỡng năng lượng với cổng mềm 25–30 ms, lấy mốc bắt đầu nói theo âm thanh thật chứ không theo Whisper, giữ file gốc.
   - *Người nói trước camera:* `trim_voice.py --jumpcut --scenes-out`, rồi `process_audio.py voice`.
   - *Tạo giọng:* soát claim, `make_voiceover.py --quota`, `--dry-run`, tạo (`eleven_turbo_v2_5` cho tiếng
     Việt), `process_audio.py voice --no-clean`.
   - *Phụ đề:* `align_captions.py` không `--script` lấy bản nháp, **sửa tay** cho đúng lời nói, chạy lại với
     `--script --words-out`. Whisper cho thời gian, kịch bản cho chữ.
   - *Nhạc:* chỉ nhạc CC0, tự làm hoặc có giấy phép cho nền tảng và loại tài khoản (kho nhạc thương mại nằm trong
     app TikTok/Meta, render không lấy được; đọc giấy phép từng bài, ghi nguồn vào `SOURCES.md`). Hỏi tôi trước khi
     tải. `process_audio.py music`; khoảng bpm và tâm trạng lấy từ playbook.
5. **Cắt:** theo `drive` của playbook: giọng (`suggest_cuts.py words.json`, cắt ở chỗ nghỉ, không cắt giữa chữ),
   nhạc (`suggest_cuts.py --music --beats-out`, cắt trên nhịp, ưu tiên đầu ô nhịp), hoặc cả hai (cắt theo giọng, nhấc
   lên nhịp trong 4 khung hình). Với nhạc có phần êm rồi lên cao: dò thời điểm "drop" bằng năng lượng, chọn đoạn
   nhạc sao cho drop trùng một điểm cắt có chủ đích (cảnh hero hoặc đổi nhịp). Fade vào ngắn, fade ra 2–3 s.
   Không cắt ngang cảnh chứng minh trước/sau.
6. **Plan:** `playbook.py skeleton <id> --cuts cuts.json --title "…"` rồi điền Source/In, Transition, Camera,
   Speed, Overlays (`plan_scenes.py` hỗ trợ). `pacing_checker.py` PASS; `footage_overlap_checker.py` với tất cả plan.
   Một ngoại lệ chia sẻ (cảnh mở, cảnh kết) chỉ áp dụng khi tôi đã ghi ở mục 1; vẫn lấy đoạn khác nhau và báo.
7. **Biên dịch:** `plan_to_project.py … --voice --music --captions --words --auto-camera --analysis` (thêm
   `--auto-sfx` **chỉ khi** playbook/khách muốn tiếng chuyển cảnh; thêm `--caption-style`, `--punch-keywords`,
   `--platform reels-ad` khi cần). Đọc **sync report** và sửa mọi cảnh báo (cắt trong chữ, chữ sát điểm cắt, vùng giao
   diện, chồng đồ hoạ, thành phần playbook tránh, slow-motion giật, thiếu file). Đặt mức nhạc trong `project.json`
   theo có giọng hay không (mục 4 bên dưới).
8. **Render:** `npx remotion still` vài khung chính (hook, đổi nhịp, mọi tiêu đề, thẻ kết) và **nhìn** trước khi
   render đủ (`--codec=h264 --crf=18`). Chọn Remotion hay HyperFrames cho từng video và nói lý do
   (`hyperframes-flow.md` §1: HyperFrames không vẽ `magnifier`, `thumbs`, `compare`, `ranking`; có `+shake +glitch
   +rgb +pulse`, `--look`). Hỏi trước lần `npx hyperframes` đầu tiên.
9. **Master:** `process_audio.py master … --phone` (−14 LUFS, đỉnh ≤ −1 dBTP, AAC, `+faststart`; bản nén cho điện thoại
   dưới ~30 MB). Đo mức từng đoạn: mở đầu, drop, khoảng nghỉ, cuối.
10. **Kiểm cuối:** `contact_sheet.py … --project …` và xem từng cảnh; `ffprobe` thời lượng khớp plan; đối chiếu
    mục 5 bên dưới.

### 4. Danh mục kỹ thuật (chọn theo thể loại và footage; không dùng hết, không dùng thừa)

| Nhóm | Kỹ thuật có sẵn trong kit (nguồn) | Dùng khi |
|---|---|---|
| **Hook** | 3 kênh khác việc; ưu tiên chứng minh xã hội, tiết lộ sản phẩm/địa điểm, biến đổi nhìn thấy; tránh quyền uy mở đầu và mệnh lệnh trần (`hook-library.md`) | luôn luôn |
| **Chọn cảnh** | contact sheet theo từng clip, shot log theo loại (BEFORE/AFTER/POUR/HERO/…), ngân sách footage cho lô | luôn luôn |
| **Hình** | tone-map HDR, cân trắng điểm trung tính, phơi sáng gamma, khử nhiễu có điều kiện, chống rung vid.stab, sửa méo ống kính và căn thẳng, grade `natural / bright-interior / warm-food / soft-skin / vivid`, `correction: shared` cho trước/sau (`image-processing.md`) | luôn qua `prepare_footage`; xem lại bằng mắt |
| **Nhịp và cắt** | cắt theo giọng, theo nhạc, theo cả hai; jump cut người nói; cắt theo động tác, match cut; J/L-cut; re-hook giữa video; ramp tốc độ `2x`, `ramp 1>2.5>1`, `0.5x` (cần 60 fps) (`cutting-and-pacing.md`, `sync-and-timing.md`) | theo `drive` và cấu trúc của playbook |
| **Camera ảo** | push, pull, pan, roll, hold, `focus`, `keys` (nhiều khung với easing), punch-in theo từ khoá, thang cỡ cảnh rộng–vừa–cận; footage đã chuyển động thì giữ tĩnh (`camera-moves.md`) | mỗi cảnh một chuyển động nhìn thấy được (≥ 12% zoom hoặc 8% pan), nhắm vào hành động |
| **Chuyển cảnh** | `fade slide wipe zoomThrough blurDissolve whip pushCut iris flip crossZoom cut`, nhấn `+flash +leak`, tối đa 3–4 loại, tối đa 2 nhấn (`transitions.md`); HyperFrames thêm `+shake +glitch +rgb +pulse` | họ chuyển cảnh theo playbook; cắt thẳng đúng nhịp ở điểm drop |
| **Đồ hoạ** | `title callout highlight step checklist price cart sticker progress magnifier thumbs compare ranking lowerThird specs pin label stat chart image punch` (`layout-and-motion-graphics.md`) | theo danh sách `use/avoid` của playbook; mỗi đồ hoạ một ý, neo theo từ bằng `@"cụm từ"` |
| **Chữ** | theme `cool / warm / luxe`; 5 kiểu tiêu đề `outline stack gradient glass marker`; phụ đề `karaoke / pop / plain / none`; 3–4 kiểu mỗi video, không lặp liền nhau, một từ nhấn; chữ trên nền sáng/trắng dùng `outline` hoặc `marker` (`typography.md`, `captions-and-text.md`) | màu chữ phải hợp tông footage: theme do playbook chọn, đổi bằng `new_remotion_project.py --theme cool|warm|luxe` khi khách yêu cầu (lặp lại `--theme` sau mỗi `--update`) |
| **Âm thanh** | chuỗi giọng (lọc ồn có dấu vết, EQ, de-ess, nén, −16 LUFS), nhạc −14 LUFS, nhạc tự hạ khi có lời (`volumeDb`, `duckDb`), nhạc 0 dB khi không có giọng, im lặng nửa giây trước reveal/drop, tiếng thật của chủ thể giữ nguyên, master −14 LUFS (`audio-and-music.md`, `audio-processing.md`) | luôn qua `process_audio.py` |
| **Hiệu ứng âm thanh** | `--auto-sfx` từ `sfx-map.json` + ghi đè của playbook, chỉ CC0 hoặc tự làm, không đặt ngang reveal; chuyển cảnh mềm không có tiếng (`sound-design.md`) | chỉ khi playbook và khách muốn; mặc định bám playbook |
| **Trước / sau** | thẻ `compare`, cùng khung và cùng hiệu chỉnh, ghi nén thời gian (`before-after.md`) | chỉ khi có kết quả nhìn thấy; không dùng khi chạy quảng cáo |
| **Kiểu CapCut** | tìm kỹ thuật trong `capcut-techniques.md` trước khi tự nghĩ; mỗi nhấn dùng 1–2 lần | khi khách nói "làm kiểu CapCut" |
| **Nền tảng** | khuôn TikTok/Reels, vùng an toàn, tín hiệu xếp hạng, nhạc theo nền tảng, checklist đăng (`platforms.md` §6) | luôn luôn, khi báo cáo |
| **Tuân thủ** | luật theo thể loại: bất động sản, thực phẩm, mỹ phẩm, tài chính, khuyến mãi; quảng cáo; gắn nhãn AI và nội dung thương mại (`claims-and-compliance.md`) | luôn luôn |

### 5. Tiêu chuẩn nghiệm thu (tự kiểm trước khi gửi tôi)

- **Hình:** chủ thể rõ trong mọi cảnh; không cảnh tối chìm, cháy sáng, ngả màu, rung, vật cản che; màu liền mạch giữa các
  cảnh; chữ đọc được trên mọi nền; không đồ hoạ lấn mặt, vùng giao diện hay chữ trên biển hiệu.
- **Nhịp:** hook thấy trong 1–3 giây đầu; mỗi cảnh có thay đổi nhìn thấy; không đoạn nào trùng cảnh đã dùng; điểm cắt không
  nằm giữa chữ; điểm cắt mạnh trùng nhịp hoặc drop; cảnh kết có CTA hoặc thông tin liên hệ đúng.
- **Âm thanh:** giọng rõ, không rè hay tiếng lạ ở đầu, cuối, khoảng nghỉ; nhạc nghe rõ ở đoạn mở và không át lời; mức tổng
  −14 ± 1 LUFS, đỉnh ≤ −1 dBTP; không tiếng chuyển cảnh nếu tôi đã loại.
- **Nội dung:** không claim bị cấm; dữ kiện trên màn hình khớp tài liệu; người xuất hiện trong hình đã được ghi chú về sự đồng ý;
  nhạc và giọng đúng giấy phép; nhãn thương mại/AI được nhắc trong checklist đăng.

### 6. Bàn giao và báo cáo

- Gửi **bản nén ≤ 30 MB** vào chat, kèm đường dẫn bản chuẩn.
- Báo cáo ngắn bằng tiếng Việt: playbook và lý do; thời lượng, số cảnh, hook; hiệu chỉnh hình đã áp (từ `corrections.json`);
  nhịp cắt theo giọng hay nhạc và điểm drop; mức âm đã đo; sync report còn báo gì; claim đã sửa hoặc gắn cờ (nêu quy tắc);
  cảnh dùng chung theo ngoại lệ; checklist đăng; và **điều chưa kiểm chứng** (chưa nghe thử, người trong hình chưa đồng ý,
  quy định nhạc của tài khoản doanh nghiệp, kết quả đo là heuristic).
- Giữ mọi `edit-plan.md` (là sổ cảnh) và ghi trạng thái từng video để lần sau tiếp tục được.
- Nếu phát hiện lỗi trong kit (ví dụ một phép đo sai với định dạng footage này), nói rõ, đề xuất bản sửa, **không** tự commit.

---

## 7. Bản rút gọn và ví dụ

**Bản rút gọn (đủ dùng khi footage và yêu cầu rõ):**

> Dùng skill `short-video-editing`. Dựng [N] video [độ dài] từ footage `[thư mục]`, giọng `[file / không]`, nhạc `[file / tìm (hỏi
> tôi trước khi tải)]`, đăng `[nền tảng]` `[organic/ads]`. Mục tiêu: `[CTA]`. Thể loại: `[tên playbook / để bạn đề xuất]`.
> Yêu cầu riêng: `[..]`. Không trùng cảnh giữa các video `[trừ: ..]`. Làm đủ quy trình trong `docs/PROMPT-VIDEO.md` (mục 2–6),
> gửi bản nén vào chat và nêu điều chưa kiểm chứng.

**Ví dụ A: nhà hàng (`food-fnb`, có giọng và nhạc)**

> … 1 video 30 giây cho quán Kiiro Sushi (Đà Nẵng) từ `…\29_10 Kiiro`, giọng `…\Kiiro kb12.m4a`, nhạc Nhật có giấy phép (hỏi tôi
> trước khi tải). Video mẫu `Video-filnal(1_3).mp4`: phân tích cách edit của nó. Không trùng cảnh với video 1/3; chỉ cảnh mở quay
> lia vào quán và cảnh kết mặt tiền được dùng chung. Giữ pha quay xoay nghiêng ở cảnh đầu, bỏ âm thanh chuyển cảnh, chữ theo tông ấm.

**Ví dụ B: căn hộ (`real-estate`, chỉ nhạc, cần số liệu)**

> … 1 video 40 giây tour căn 2PN `[tên dự án]`, footage gimbal `[thư mục]`, chỉ nhạc. Dữ kiện: giá `[..]`, diện tích `[.. m², thông thủy]`,
> hướng `[..]`, địa chỉ `[..]`, pháp lý `[..]`. Không có dữ kiện nào khác thì không hiện. Hỏi tôi nếu dự án chưa đủ điều kiện kinh doanh.

**Ví dụ C: review sản phẩm bán qua giỏ hàng (`product-demo`, có trước/sau)**

> … 3 video 35 giây cho `[sản phẩm]` (giá `[..]`, link thẻ sản phẩm `[..]`), footage `[thư mục]`, giọng `[file]`. Đăng TikTok Shop, **không**
> chạy quảng cáo (nên được dùng thẻ trước/sau, có ghi nén thời gian). Không đoạn nào dùng hai lần giữa ba video; hết cảnh thì dừng và báo.
> Claim trong giọng có sẵn: gắn cờ, đừng giữ lặng lẽ.

**Ví dụ D: người nói trước camera (`talking-head`)**

> … video 45 giây từ `[video người nói]`: bỏ khoảng lặng (jump cut), phụ đề `pop`, B-roll ở `[thư mục]` cho từng ý, tên và chức danh người
> nói `[..]` (đúng thực tế). Lời khuyên liên quan sức khoẻ hoặc tài chính: kiểm theo mục tuân thủ trước khi dựng.
