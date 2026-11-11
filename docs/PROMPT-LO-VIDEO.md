# Cấu trúc prompt cho một **lô video đăng thật** (nhiều video, nhiều nguồn, có giọng, có bàn giao)

File này dành cho kiểu việc như: "gộp footage mới và footage cũ, làm N video không trùng nhau, tăng tốc giọng, đẩy kết quả
vào thư mục đồng bộ Drive, đăng lên kênh TikTok thật". Quy tắc chung, quy trình từng bước và danh mục kỹ thuật nằm ở
[`PROMPT-VIDEO.md`](PROMPT-VIDEO.md); file này chỉ thêm **khung viết yêu cầu cho lô sản xuất** và chỉ ra chỗ prompt hay
bị mơ hồ. Không ghi cứng thể loại: độ dài, nhịp, màu, chữ, nhạc lấy từ playbook của kit.

---

## 0. Sáu nguyên tắc viết prompt cho việc này

1. **Nói mục tiêu và ràng buộc, không nói cách làm.** "Mỗi video 40–45 s, giọng nghe rõ" tốt hơn "tăng 1.7x". Hệ số
   tăng tốc là cách; độ dài và độ rõ là đích. Ghi hệ số như **mức trần**, để Claude giảm khi giọng méo.
2. **Mỗi con số có đơn vị, phạm vi và cách đo.** "40% footage mới" phải nói: tính theo giây hiển thị trong từng video hay
   cả lô, sai số bao nhiêu. "1.07 đến 1.18" phải nói là 1 phút 07 giây hay 1,07 giây.
3. **Đường dẫn đầy đủ, ngày tháng đã soát.** Nguồn "11-10-2026" mà đích "11-09-2026" là hai ngày khác nhau: chọn nhầm là ghi vào
   sai thư mục. Claude sẽ hỏi lại thay vì đoán.
4. **Thay "tuyệt đối không lỗi" bằng tiêu chí đo được** (mục E). Công cụ kiểm được thì ghi tên công cụ; chỗ chỉ người nghe mới
   biết thì ghi "Claude phải nói rõ chưa nghe".
5. **Chia cổng dừng thay vì "hỏi hết trước" hoặc "làm hết không hỏi".** Việc an toàn thì tự làm; chỉ dừng ở các điều kiện đã liệt
   kê (mục F). Làm **một video mẫu** đạt chuẩn rồi mới nhân ra cả lô.
6. **Cho biết nguồn nào là gì** (quay thật, AI tạo, của khách, mua giấy phép). Nó quyết định nhãn AI, giấy phép giọng và
   quy tắc trùng lặp.

---

## 1. Khung prompt (copy, điền `[...]`, xoá dòng không cần)

```
Dùng skill `short-video-editing`. Làm việc bằng tiếng Việt. Hôm nay là [ngày]. Quy tắc chung và quy trình theo
docs/PROMPT-VIDEO.md (mục 2–6); phần dưới là yêu cầu riêng cho lô này.

## A. Mục tiêu và mức rủi ro
- Dựng [N] video dọc 9:16 để đăng [kênh/nền tảng], [organic / chạy quảng cáo]. Đây là bản [đăng thật / demo].
- Thành công nghĩa là: [N] file đạt mục E, nằm đúng thư mục đích, không video nào trùng cảnh với video khác.

## B. Đầu vào (đường dẫn đầy đủ, nói rõ nguồn gốc từng thứ)
- Footage MỚI: `[đường dẫn]` — [quay thật / AI tạo bằng công cụ ... / của ai, giấy phép gì].
- Footage CŨ: `[đường dẫn]` — [như trên].
- Giọng: `[đường dẫn]` — [số file; mỗi file dài bao nhiêu; giọng người thật hay AI (ElevenLabs, gói nào)]; ghép với video thế nào:
  [mỗi file một video / một file dùng cho nhiều video / để Claude đề xuất].
- Nhạc: [không / file có giấy phép / nhờ tìm, hỏi tôi trước khi tải].
- Kịch bản chữ nếu có: `[đường dẫn]`. Dữ kiện phải hiện trên màn hình: `[giá, tên sản phẩm, hạn ưu đãi... hoặc "không có"]`.
- Video mẫu phong cách: `[đường dẫn / không]`.

## C. Số lượng và ràng buộc về nội dung
- [N] video, mỗi video [min]–[max] giây (ngoài khoảng của playbook thì báo cho tôi, đừng tự nới).
- Tỷ lệ footage: khoảng [40]% mới / [60]% cũ, tính theo **[giây hiển thị trong mỗi video / cả lô]**, sai số ±[5] điểm %.
  Cảnh nào cũng ghi nguồn là mới hay cũ trong plan.
- Không đoạn nguồn nào được dùng hai lần trong cả lô (`footage_overlap_checker.py` trên mọi plan). Ngoại lệ dùng chung:
  [không có / cảnh mở ..., cảnh kết ...].
- Thể loại: [tên playbook / để Claude đề xuất và nói lý do].
- Yêu cầu phong cách riêng: [cảnh dài-ngắn, chuyển cảnh, màu chữ, có/không tiếng chuyển cảnh, logo cuối...].

## D. Xử lý giọng
- Mục tiêu độ dài sau xử lý: [40–45] s mỗi video. Hệ số tăng tốc: **tối đa [1.7]×**, giữ cao độ (ffmpeg `atempo`), chọn hệ số
  nhỏ nhất đạt mục tiêu độ dài.
- Sau khi tăng tốc vẫn phải: nghe rõ từng chữ tiếng Việt, không méo, không rè đầu/cuối/khoảng nghỉ. Nếu cần quá [1.7]× mới đạt
  độ dài thì **dừng và báo** (phương án: bỏ trọn câu nào, hay chấp nhận dài hơn) — không tự bóp giọng thêm.
- Thứ tự: cắt (nếu cần) → tăng tốc → `process_audio.py voice` → phiên âm, sửa tay → `align_captions.py`, để phụ đề khớp đúng
  bản đã tăng tốc.

## E. Tiêu chí nghiệm thu (mỗi video, ghi PASS/FAIL vào bảng báo cáo)
- Kỹ thuật: 1080×1920, h264 + AAC, +faststart; thời lượng trong khoảng C; `pacing_checker.py` PASS; lệch tỷ lệ mới/cũ trong sai số.
- Hình: không cảnh tối chìm, cháy sáng, ngả màu, rung; màu liền mạch; chữ đọc được trên mọi nền (xem contact sheet từng video).
- Âm: −14 ± 1 LUFS, đỉnh ≤ −1 dBTP; giọng không rè hay tiếng lạ ở đầu, cuối, khoảng nghỉ; nhạc không át lời.
- Nội dung: không claim bị cấm (nêu quy tắc nếu sửa); dữ kiện chữ khớp tài liệu tôi đưa; nhãn AI/nội dung thương mại nằm trong checklist đăng.
- Không video nào lỗi thì mới giao; video lỗi thì sửa tới khi đạt hoặc báo rõ vì sao không đạt, không âm thầm giao.

## F. Cách làm và chỗ phải dừng
1. Kiểm tra máy (`doctor.py`) và **kiểm kê đầu vào**: mở được thư mục, file đã tải thật về máy (không phải bản giữ chỗ của Drive),
   đủ dung lượng đĩa; đo footage, xem contact sheet; đo từng file giọng.
2. **Ngân sách footage** (tính trước khi dựng): giây dùng được mới/cũ so với [N] × [độ dài] × tỷ lệ; nêu số.
3. Làm **video 1 hoàn chỉnh** (plan → render → master → kiểm theo E), đưa tôi bản nén xem **nếu** [tôi muốn duyệt mẫu / không cần
   chờ tôi, cứ làm tiếp]. Sau đó dựng các video còn lại với cùng quy trình; render lần lượt, mỗi lần một việc ffmpeg nặng.
4. Kiểm trùng lặp trên **tất cả** plan, kiểm từng video theo E, rồi mới bàn giao (mục G).
- DỪNG và hỏi tôi khi: footage không đủ cho [N] video theo tỷ lệ và quy tắc không trùng (báo số, đừng xáo trộn để cho đủ); thư mục
  nguồn/đích không thấy hoặc ngày không khớp; giọng AI chưa rõ gói ElevenLabs (bản miễn phí không dùng thương mại); cần tải
  gói/model/nhạc; giọng quá dài/quá ngắn sau tăng tốc; footage bên thứ ba; thể loại lệch với footage.
- Không commit, không push, không xoá hay sửa file gốc. File làm việc nằm ngoài repo: `[thư mục làm việc]`.

## G. Bàn giao
- Đích: `[đường dẫn thư mục đích, ví dụ G:\...\Video Final\<ngày>]`. Tên file: `[Thương hiệu]_[ngày]_V01 … V[N].mp4`.
- **Sao chép** (không di chuyển) bản master vào đích; sau đó kiểm từng file: có đủ [N] file, kích thước bằng bản gốc, `ffprobe` đọc
  được, thời lượng khớp. Không ghi đè file cùng tên đã có sẵn trong đích: gặp thì dừng và hỏi.
- Việc đồng bộ lên Drive là của ứng dụng Drive, Claude chỉ xác nhận file đã nằm đúng chỗ (có thể kiểm thêm bằng trình kết nối
  Drive nếu bật); không viết "đã lên Drive" nếu chưa kiểm.
- Báo cáo bằng tiếng Việt: bảng [video × nguồn mới/cũ × độ dài × hệ số tăng tốc × LUFS × PASS/FAIL], cảnh nào dùng clip nào, cờ
  claim, checklist đăng, và **điều chưa kiểm chứng** (chưa nghe hết, chưa xem trên điện thoại thật, chưa kiểm Drive...).
```

---

## 2. Prompt gốc của bạn, viết lại theo khung (điền nốt các ô còn thiếu rồi dùng)

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

## 3. Chỗ prompt gốc dễ làm Claude đoán sai (và cách sửa)

| Câu gốc | Vấn đề | Sửa |
|---|---|---|
| "dài từ 1.07s cho tới 1.18s" | Là 1:07–1:18 (67–78 s) hay 1,07 s? Nếu 67–78 s, chia 1.7 ra **39,4–45,9 s**: vừa đủ, gần như không dư để bỏ câu. | Ghi "1 phút 07 giây". Kiểm số học trước: độ dài giọng ÷ hệ số phải nằm trong 40–45 s. |
| "tăng lên khoảng 1.7x" | 1.7× là cách, không phải đích. Kit ghi giọng thương mại quá ~1.15× đã nghe vội (`voiceover-and-captions.md`); 1.7× trên giọng Việt dễ mất thanh điệu và nuốt âm. Kit **chưa có script tăng tốc** (chỉ có `make_voiceover.py --speed` khi tạo giọng), Claude sẽ dùng `ffmpeg atempo` trong thư mục làm việc. | Đặt đích = độ dài và độ rõ, 1.7× là trần; có phương án khi vượt trần. |
| "40% video thô hôm nay và 60% cũ" | Tính theo giây hiển thị, theo số clip hay theo dung lượng? Mỗi video hay cả lô? Không có sai số. Còn `CLAUDE.md` ghi tỷ lệ "mới" bị chặn bởi số học khi không được dùng lại: 8 × ~42 s = ~336 s footage dùng được, 40% là ~134 s mới và ~202 s cũ. | Nêu cách đo và sai số; Claude tính ngân sách và báo trước khi dựng. |
| "ko trùng nhau" | Trùng cảnh, trùng đoạn nguồn, hay chỉ khác thứ tự? TikTok Shop gọi việc xáo thứ tự là nội dung lặp (`Chính sách.md`). | "Không đoạn nguồn nào dùng hai lần trong cả lô", kiểm bằng `footage_overlap_checker.py`. Hết cảnh thì dừng và báo. |
| "11-10-2026" nguồn, "11-09-2026" đích | Hai ngày khác nhau, trong khi hôm nay là 11-11. Một trong hai có thể đánh nhầm. | Ghi đường dẫn đầy đủ hoặc để Claude liệt kê thư mục rồi bạn xác nhận. |
| "đẩy vào ổ G … tự đồng bộ" | Ổ G có thể chưa gắn; file Drive đôi khi chỉ là bản giữ chỗ chưa tải; ghi đè nhầm file đang có. | Mục G và F.1: kiểm tồn tại, sao chép, không ghi đè, kiểm sau khi chép. |
| "ai voice audio" | Giọng AI: gói nào? Gói miễn phí của ElevenLabs không dùng thương mại; đăng kênh thật là dùng thương mại. Footage AI cũng cần nhãn "nội dung do AI tạo". | Ghi nguồn gốc từng thứ ở mục B; Claude đưa vào checklist đăng. |
| "Áp dụng mọi kỹ thuật … tuyệt đối không được lỗi" | Không kiểm được, và "mọi kỹ thuật" có thể dùng thừa (kit nói dùng theo playbook, không dùng hết). | Thay bằng tiêu chí đo được (mục E) và quy trình mẫu-rồi-nhân. |
| "Bắt đầu làm đi!!!" kèm "nghiên cứu kĩ trước" | Hai yêu cầu kéo ngược nhau: vừa phải kiểm kê, vừa muốn làm ngay. | Mục F: kiểm kê và ngân sách là bước 1–2 (không cần chờ), chỉ dừng ở điều kiện đã liệt kê. |

## 4. Gợi ý nhỏ khi dùng

- Hai lô liên tiếp của cùng khách: đặt phần B, C (yêu cầu riêng) và E thành một file `brief.md` trong thư mục làm việc rồi chỉ
  viết "làm lô mới theo brief.md, khác: …". Claude đọc được file, không cần dán lại cả prompt.
- Nếu muốn xem mẫu trước, đổi ở F.3 thành "dừng sau video 1 và gửi bản nén".
- Bài học của lô Kiiro ghi trong `CLAUDE.md`, nên không cần nhắc lại trong prompt: phân bổ theo vòng tròn giữa các video, mỗi video
  để dành một clip kết, tên file không có dấu chấm, giọng có sẵn phải kiểm tiếng rè ở 2 giây đầu.
