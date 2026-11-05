# Luồng làm việc — từ clip thô tới video hoàn chỉnh

Tất cả lệnh chạy từ thư mục `skill/short-video-editing/` (hoặc `~/.claude/skills/short-video-editing/` sau
khi cài). Claude chạy các bước này tự động khi bạn nhờ; phần này để bạn hiểu và kiểm tra lại.

```
clip thô ─► [1 soi] ─► [2 shot log] ─► [3 hook] ─► [4 timeline] ─► [5 kịch bản] ─► [6 giọng]
                                                       │                              │
                                                  pacing_checker                 align_captions
                                                                                      │
                                       [8 trộn tiếng + xuất] ◄─ [7 cắt + dựng đồ hoạ] ◄┘
                                          ffmpeg                  ffmpeg  ─►  Remotion
```

## Phân công công cụ

| Việc | Công cụ | Vì sao |
|---|---|---|
| Soi, cắt, ghép, tăng tốc, trộn tiếng | **ffmpeg** | Một lệnh, gần như tức thì. Làm trong Remotion thì chậm và vụng |
| Chữ, tiêu đề, bộ đếm, lớp phủ, chuyển cảnh | **Remotion** | Điều khiển bằng số khung hình → render lặp lại chính xác |
| Giọng đọc | **ElevenLabs** | Chọn bởi người dùng |
| Canh giờ cho chữ | **Whisper** (cục bộ) | Lấy *thời điểm* từ Whisper, *chữ* từ kịch bản |

## Các bước

### 1. Soi clip thô
```bash
python3 scripts/inspect_footage.py /duong/dan/clips --log
```
Báo thời lượng, độ phân giải, hướng, fps, có tiếng không, và **cảnh báo**: clip ngang (cần crop hoặc nền mờ),
clip câm, định dạng lệch nhau, footage ít (dưới ~45s cho một video 30–40s). In kèm bảng shot log trống.

### 2. Lập shot log
Xem clip, ghi **khoảnh khắc dùng được** (một dòng một khoảnh khắc, không phải một dòng một file). In/Out ở đây là
timecode **trong file nguồn**. Chi tiết và ví dụ: `references/footage-ingest.md`.

### 3. Chọn hook (0–3 giây)
Thứ tự ưu tiên: có biến đổi nhìn thấy được → dùng nó; có social proof thật → dùng; nêu được vấn đề cụ thể →
pain point; còn lại → product reveal. Tránh hook "chuyên gia" và hook ra lệnh. `references/hook-library.md`.

### 4. Dựng timeline
Dùng `assets/edit-plan-template.md`. Bảng cảnh có **Start/End** (vị trí trên timeline) và **Source/In** (timecode
trong file nguồn) — hai con số khác nhau, nhầm là lỗi hay gặp nhất.
```bash
python3 scripts/pacing_checker.py edit-plan.md
```
Phải PASS mới giao. Kiểm: hook xong trước 3,0s · không cảnh nào quá 4,0s · không hở/chồng · tổng 25–45s.

### 5. Viết kịch bản
Ngân sách 150–170 từ cho 35 giây. **Soát từng câu theo bảng viết lại ở `references/platform-specs.md` §7 trước khi
tổng hợp giọng** — sửa lời cấm sau khi đã có giọng là trả tiền hai lần.
Một dòng một câu, lưu `script.txt`. Nhãn `[excited]`… được phép viết sẵn (xem bước 6).

### 6. Giọng đọc + phụ đề
```bash
python3 scripts/make_voiceover.py --quota                              # gói + credit còn lại
python3 scripts/make_voiceover.py --list-voices                        # chọn voice_id
python3 scripts/make_voiceover.py script.txt --voice <id> --dry-run    # tính phí, không tiêu
python3 scripts/make_voiceover.py script.txt --voice <id> --out audio/
python3 scripts/align_captions.py audio/voice_full.mp3 --script script.txt --out captions.srt
```
Chi tiết model, nhãn cảm xúc, chi phí: `references/voiceover-and-captions.md`. **Luôn truyền `--script`** cho
`align_captions.py`.

### 7. Cắt và dựng
Từ shot log: ffmpeg cắt từng đoạn (re-encode để cắt đúng khung hình), ghép, rồi Remotion dựng chữ/đồ hoạ lên
trên. Lệnh mẫu: `references/footage-ingest.md` §4 và `references/remotion-output.md`.

### 8. Trộn tiếng và kiểm cuối
Giọng ở mức đầy đủ, nhạc nền thấp hơn giọng 15–25 dB, tắt nhạc ngay trước và trong lúc lộ kết quả.
**Nhạc phải lấy từ Commercial Music Library của TikTok** (tài khoản doanh nghiệp). Khi đăng: **bật "Disclose
commercial content"** — dựng không cứu được hai thứ này.

## Quy tắc cứng (nằm trong SKILL.md, được `pacing_checker.py` kiểm bằng máy)

1. Hook xong trong 3 giây đầu — hình + chữ + tiếng, mỗi kênh một việc khác nhau.
2. Không cảnh nào quá 4 giây. Cảnh hook nên 1–2 giây.
3. Mọi kế hoạch có timestamp từng cảnh.
4. Tổng 25–45s, lý tưởng 30–40s.
5. Soát claim thương mại trước khi giao.
