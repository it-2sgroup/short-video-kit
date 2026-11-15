# Nhật ký các việc đã làm cho khách (CASE LOG)

File này là **lịch sử**, không phải hướng dẫn. Skill và bộ công cụ **không được đọc nó để biết cách làm**: mọi bài học dùng lại
được đã được chuyển thành kỹ thuật trong `skill/short-video-editing/` (tài liệu chung, không tên khách, không tên file
footage) và `docs/DECISIONS.md` (quyết định và bẫy kỹ thuật). Ở đây mới được ghi tên khách, số liệu chiến dịch, tên file thật.

Quy tắc ghi: mỗi việc một mục, có **ngày, việc gì, kết quả đo, chưa kiểm cái gì**; bài học dùng lại thì viết sang
`DECISIONS.md` rồi để một dòng trỏ về đây. **Repo phải để private** (số liệu GMV, tên khách).

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

## Video giới thiệu dịch vụ dựng lại từ video mẫu (11/2026)

Việc: video quảng cáo agency (SISMO) từ 28 take của một người dẫn + file giọng 62,6 s, theo video mẫu của khách (63,7 s, 60 fps, 31 cảnh). Quy trình
đầy đủ và các lệnh: `references/agency-pitch-recipe.md`. Tại sao làm như vậy, và cái gì đã thử rồi bỏ:

- **File giọng là âm thanh gốc của các take, đã ghép** (tương quan 0,98–1,0). Nên mỗi cảnh người dẫn dùng chính hình của take với `In = start + lag`
  (`match_voice_takes.py`) và môi khớp từng mẫu âm thanh; `check_lipsync.py` kiểm lại trên bản cuối (21 cảnh lệch ≤ 5 ms). Đoạn không take nào chứa
  (phần danh mục) lấy hình phụ từ đoạn lặng đầu/cuối của take khác (`find_cutaways.py`), không bao giờ dùng take khác của cùng câu.
- **Cú nháy silhouette mở đầu**: đo trên mẫu, người dẫn tô trắng trên khung 0, 2, 4 (30 fps) rồi mới tới video. Làm bằng model tách người `u2net_human_seg`
  (Apache-2.0, 168 MB, để ngoài repo, hỏi trước khi tải) → PNG alpha; cùng model cho vị trí đầu (`--faces`) để làm sáng da. Chọn model này vì chạy CPU bằng
  onnxruntime (đã có cùng faster-whisper), không cần GPU, không cần tài khoản.
- **Chữ**: 14 hiệu ứng trong một engine (`Fx.tsx`) thay vì mỗi hiệu ứng một component; mỗi hiệu ứng dùng một hai lần trong video. Vòng elip quanh chữ "stamp"
  cắt ngang mặt người dẫn → thay bằng khung hai vạch sát chữ; neon nhấp nháy làm mất chữ → mẫu nhấp nháy dịu hơn.
- **Âm thanh**: một tiếng whoosh và một tiếng pop làm video đơn điệu, nên ngân hàng có 58 bản ghi CC0 (Kenney, OpenGameArt) + 17 âm tự tổng hợp, xoay vòng theo
  sự kiện (không lặp liền nhau), mỗi hiệu ứng chữ có tiếng riêng, `sfx.rules` của biến thể cho 5 tiếng/3 s. Không ai nghe thử: chọn theo tên, mô tả gói và số đo.
  **Đã thử và bỏ**: tự nhận diện tiếng hiệu ứng trong bản mix (nhảy năng lượng trên 1 kHz). Thử trên bản mix có 68 tiếng đã biết vị trí: tìm được 5 tiếng, và
  đo phân biệt giữa thời điểm có tiếng và thời điểm ngẫu nhiên chỉ AUC 0,53–0,58 (gần như tung đồng xu) vì giọng nói che mất. `analyze_reference.py` thay bằng
  ảnh phổ (`spectrum_*.png`) để người xem; số tiếng, tỷ lệ cắt có tiếng KHÔNG được báo.
- **Nhạc**: tài khoản doanh nghiệp TikTok chỉ được dùng Commercial Music Library (render không với tới được) → `make_music.py` viết nền tự tạo theo điểm cắt, và giao
  thêm bản không nhạc. Mức nhạc `--music-levels=-6,-6` (phải có `=`): bản đầu render ra không nhạc vì argparse từ chối `-8,-8` mà không ai đọc dòng "wrote".
- **Dải màu**: Remotion xuất full-range `yuvj420p`; điện thoại hiện bạc hoặc cháy → `finish_video.py` đổi về limited BT.709, master −14 LUFS / ≤ −1 dBTP.
- **Render**: 8 luồng báo "No frame found at position" với proxy cao 2880 → `--concurrency=5`.
- **Logo** được tách nền từ khung hình mẫu (alpha = (R−G+55)/260, ffmpeg `geq`, phóng 4× Lanczos): là giải pháp cuối cùng, hỏi khách file vector.
- **Chưa kiểm**: không ai nghe âm thanh/nhạc hay xem trọn video; câu 8 của kịch bản đoán từ bản Whisper kém; số liệu trong giọng (hơn 300 thương hiệu, 10–50 video/tháng,
  5–10 ngày, ưu đãi chỉ trong tháng này) là lời khách cần bằng chứng; tên khách hàng trên thẻ cần sự đồng ý.
- **Công cụ thêm vì việc này** (đều có trong `docs/CAU-TRUC.md`): `analyze_reference.py`, `montage.py`, `stills.mjs` (template), `mix_report.py`, `match_voice_takes.py`,
  `find_cutaways.py`, `person_matte.py`, `agency_plan.py`, `make_music.py`, `finish_video.py`, `check_lipsync.py`; `align_captions.py --prompt`; `doctor.py` kiểm
  onnxruntime, model tách người và các filter ffmpeg mới; `./setup.sh --person-model`; `project_to_hyperframes.py` báo mọi tính năng chỉ Remotion có.

## Kỹ thuật "thả vật thể" học từ một video TikTok công khai (15/11/2026)

Việc: người dùng gửi https://vt.tiktok.com/ZSpqrEJLQ/ (video 14,6 s, 576x1024, "Trên đường về nhà", kênh vantien96666, tag #editcapcut) và nhờ nghiên cứu kỹ thuật "đặt vật thể". Chỉ xem trong trình duyệt, **không tải, không lấy hình ảnh** của họ vào kit.

Đo được (khung 1/30 s quanh giây 6,1): vật thể (cổng) vào từ mép trên ở 6,10, rơi 3-4 khung, **cắt cứng** sang cảnh mới ở 6,20 kèm chớp nổ vàng-cam ở chân cổng (4 khung), rồi khói xám 2 khung, hết ở 6,33. Cùng kiểu ở 0,6 (xe cẩu), 2,5 (nhà xây dở), 12,2 (tòa tháp), 12,6 (nhà thờ rơi chồng lên sau tòa tháp); thêm chuyển cảnh trượt dọc (2,9 / 4,0 / 11,4 s) và xoay nghiêng (9,0-9,6 s). Âm thanh: nhạc liên tục có nhịp ~0,4-0,6 s, nhịp to hơn 6-8 dB ngay sau lần chạm đất ở 6,2 và sau cú cắt ở 8,1 (đo mức, chưa nghe).

Chưa kiểm: người làm dùng công cụ nào để tách vật thể (tìm kiếm tiếng Việt và tiếng Anh không ra tên kỹ thuật hay hướng dẫn); chưa nghe âm thanh; chưa có ai xin phép dùng video đó làm mẫu (kit chỉ lấy kỹ thuật).

Xây vào kit: overlay `objectDrop` và `impact` (`Drop.tsx`), `scripts/object_cutout.py` (`--poly` không cần model; `--model` chỉ chạy với model người dùng đưa, mới thử với `u2net_human_seg` trên cảnh có người, **chưa thử với `isnet-*`**), cách làm ở `references/layout-and-motion-graphics.md` ("The object drop"). Giấy phép trọng số tách nền kiểm ngày 15/11/2026 qua trang GitHub: SAM 2 Apache-2.0 (code và checkpoint); rembg MIT nhưng mỗi model có giấy phép riêng; `isnet-general-use` trang DIS không nêu; RMBG-2.0 cần thỏa thuận trả phí; BiRefNet code MIT, trọng số không nêu. Chưa render video đầy đủ bằng kỹ thuật này; mới xem ảnh tĩnh từng khung rơi và nổ trên cảnh thử.

Bản demo SISMO lần 1 (4 cú rơi, mỗi cảnh 2,4 s, người dẫn đứng yên, chớp nổ tròn to) bị chấm 4/10: so với video gốc, 4 sự kiện trong 12,4 s thay vì ~22 trong 14,6 s, chuyển động trung vị 1,7 thay vì 9,7, chớp nổ là một vầng sáng tròn che cả thân người. Đo video gốc từng khung (bộ đo: chênh lệch độ sáng giữa hai khung liên tiếp ở 72x128, đếm điểm ảnh vàng): mỗi cú rơi gồm rơi 3-4 khung, cắt cứng, nhòe ngang cả khung 2 khung, chùm tia vàng-trắng mảnh dẹt trên mặt đất (rộng ~29% khung, cao ~10%), bụi nâu loãng dần. Viết lại `impact` theo cách xếp lớp của người làm hậu kỳ (pop phơi sáng, lõi nhỏ, tia lửa có vệt, hạt lửa rơi theo trọng lực, bụi nhiễu có cạnh sần, bóng tiếp đất, vòng sóng rất mờ), thêm hit `+jolt` (nhòe ngang và rung giảm dần lúc cắt). Bản 2: 12 cảnh 0,8-1,6 s, 11 cú rơi, đo lại 11 sự kiện trong 11,6 s, chuyển động trung vị 3,8. Vẫn chưa bằng bản gốc về chuyển động (camera tĩnh, đẩy giả) và vẫn có hai người dẫn trong 4 khung lúc rơi vì cảnh cũ cũng có cô ấy. Chưa nghe âm thanh.

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

## Lô 8 video đăng thật: prompt gốc của khách và chỗ dễ mơ hồ (11/2026)

Phân tích prompt thật của một lô (nguồn: `docs/PROMPT-LO-VIDEO.md` trước khi tách). Khung dùng lại được vẫn ở `PROMPT-LO-VIDEO.md`.

### Prompt viết lại theo khung

```
Dùng skill `short-video-editing`. Làm việc bằng tiếng Việt. Hôm nay là 11-11-2026. Quy tắc chung và quy trình theo
docs/PROMPT-VIDEO.md (mục 2–6).

## A. Mục tiêu và mức rủi ro
- Dựng 8 video dọc 9:16 cho kênh TikTok [tên kênh], [organic / chạy quảng cáo]. Đây là bản ĐĂNG THẬT.
- Thành công: 8 file đạt tiêu chí mục E, nằm đúng thư mục đích, không video nào trùng cảnh với video khác.

## B. Đầu vào
- Footage MỚI (tạo hôm nay, gồm cả video mới và giọng AI): thư mục Drive "video ngày [11-10-2026 — xác nhận ngày]" tại
  `[đường dẫn đã tải về máy]`; footage mới là [AI tạo bằng công cụ nào / quay thật].
- Footage CŨ: thư mục "Video AI cà phê" tại `[đường dẫn]`; [AI tạo / quay thật].
- Giọng AI: trong thư mục "[...]", [số] file, mỗi file 1 phút 07 giây – 1 phút 18 giây; tạo bằng [ElevenLabs gói ... / công cụ
  khác]. Ghép: [mỗi video một giọng / giọng dùng lại cho nhiều video].
- Nhạc: [không dùng / nhờ tìm, hỏi trước khi tải]. Kịch bản chữ: [có/không]. Dữ kiện trên màn hình: [giá, tên sản phẩm, ...].

## C. Số lượng và ràng buộc
- 8 video, mỗi video 40–45 giây.
- Tỷ lệ footage: khoảng 40% mới / 60% cũ tính theo giây hiển thị trong MỖI video, sai số ±5 điểm %.
- Không đoạn nguồn nào dùng hai lần trong cả 8 video (không ngoại lệ).
- Thể loại: để Claude đề xuất (sản phẩm là [tên]); nói lý do.
- Yêu cầu riêng: [giữ nguyên các quy ước của khách nếu có: cảnh 3–4 s, chuyển cảnh mềm, không chữ trong khung].

## D. Xử lý giọng
- Giọng đọc chậm: tăng tốc để mỗi video 40–45 s, tối đa 1.7×, giữ cao độ; nghe rõ từng chữ, không méo.
  Cần hơn 1.7× mới đủ → dừng và báo. Phiên âm và phụ đề làm sau khi tăng tốc.

## E. Nghiệm thu: như khung, mục E.

## F. Cách làm: như khung, mục F (làm video 1 trước, rồi nhân ra 7 video còn lại, không cần chờ tôi duyệt mẫu).

## G. Bàn giao
- Đích: `G:\[...]\Video Final\[11-09-2026 hay 11-11-2026 — xác nhận]`. Tên file `[Kênh]_[ngày]_V01 … V08.mp4`. Sao chép, không di chuyển,
  kiểm đủ 8 file, không ghi đè. Việc đồng bộ Drive là của ứng dụng Drive.
```

---

### Chỗ prompt gốc dễ làm Claude đoán sai (và cách sửa)

| Câu gốc | Vấn đề | Sửa |
|---|---|---|
| "dài từ 1.07s cho tới 1.18s" | Là 1:07–1:18 (67–78 s) hay 1,07 s? Nếu 67–78 s, chia 1.7 ra **39,4–45,9 s**: vừa đủ, gần như không dư để bỏ câu. | Ghi "1 phút 07 giây". Kiểm số học trước: độ dài giọng ÷ hệ số phải nằm trong 40–45 s. |
| "tăng lên khoảng 1.7x" | 1.7× là cách, không phải đích. Kit ghi giọng thương mại quá ~1.15× đã nghe vội (`voiceover-and-captions.md`); 1.7× trên giọng Việt dễ mất thanh điệu và nuốt âm. Kit **chưa có script tăng tốc** (chỉ có `make_voiceover.py --speed` khi tạo giọng), Claude sẽ dùng `ffmpeg atempo` trong thư mục làm việc. | Đặt đích = độ dài và độ rõ, 1.7× là trần; có phương án khi vượt trần. |
| "40% video thô hôm nay và 60% cũ" | Tính theo giây hiển thị, theo số clip hay theo dung lượng? Mỗi video hay cả lô? Không có sai số. Còn `CLAUDE.md` ghi tỷ lệ "mới" bị chặn bởi số học khi không được dùng lại: 8 × ~42 s = ~336 s footage dùng được, 40% là ~134 s mới và ~202 s cũ. | Nêu cách đo và sai số; Claude tính ngân sách và báo trước khi dựng. |
| "ko trùng nhau" | Trùng cảnh, trùng đoạn nguồn, hay chỉ khác thứ tự? TikTok Shop gọi việc xáo thứ tự là nội dung lặp (`policy.md`). | "Không đoạn nguồn nào dùng hai lần trong cả lô", kiểm bằng `footage_overlap_checker.py`. Hết cảnh thì dừng và báo. |
| "11-10-2026" nguồn, "11-09-2026" đích | Hai ngày khác nhau, trong khi hôm nay là 11-11. Một trong hai có thể đánh nhầm. | Ghi đường dẫn đầy đủ hoặc để Claude liệt kê thư mục rồi bạn xác nhận. |
| "đẩy vào ổ G … tự đồng bộ" | Ổ G có thể chưa gắn; file Drive đôi khi chỉ là bản giữ chỗ chưa tải; ghi đè nhầm file đang có. | Mục G và F.1: kiểm tồn tại, sao chép, không ghi đè, kiểm sau khi chép. |
| "ai voice audio" | Giọng AI: gói nào? Gói miễn phí của ElevenLabs không dùng thương mại; đăng kênh thật là dùng thương mại. Footage AI cũng cần nhãn "nội dung do AI tạo". | Ghi nguồn gốc từng thứ ở mục B; Claude đưa vào checklist đăng. |
| "Áp dụng mọi kỹ thuật … tuyệt đối không được lỗi" | Không kiểm được, và "mọi kỹ thuật" có thể dùng thừa (kit nói dùng theo playbook, không dùng hết). | Thay bằng tiêu chí đo được (mục E) và quy trình mẫu-rồi-nhân. |
| "Bắt đầu làm đi!!!" kèm "nghiên cứu kĩ trước" | Hai yêu cầu kéo ngược nhau: vừa phải kiểm kê, vừa muốn làm ngay. | Mục F: kiểm kê và ngân sách là bước 1–2 (không cần chờ), chỉ dừng ở điều kiện đã liệt kê. |
