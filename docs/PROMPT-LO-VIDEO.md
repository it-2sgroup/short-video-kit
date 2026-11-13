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

## 2. Gợi ý nhỏ khi dùng

- Hai lô liên tiếp của cùng khách: đặt phần B, C (yêu cầu riêng) và E thành một file `brief.md` trong thư mục làm việc rồi chỉ
  viết "làm lô mới theo brief.md, khác: …". Claude đọc được file, không cần dán lại cả prompt.
- Nếu muốn xem mẫu trước, đổi ở F.3 thành "dừng sau video 1 và gửi bản nén".
- Bài học phân bổ footage cho cả lô đã ghi trong `CLAUDE.md`, nên không cần nhắc lại trong prompt: phân bổ theo vòng tròn giữa các video, mỗi video
  để dành một clip kết, tên file không có dấu chấm, giọng có sẵn phải kiểm tiếng rè ở 2 giây đầu.
