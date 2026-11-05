# short-video-kit

Bộ công cụ dựng video ngắn TikTok Shop (30–40s) cùng Claude: nhận brief hoặc **video thô**, ra kế hoạch
dựng có timestamp, giọng đọc, phụ đề khớp từng chữ, và kiểm tra tự động các quy tắc nhịp cắt.

## ⚠️ Đọc 3 điều này trước

**1. Key ElevenLabs KHÔNG nằm trong git** (`.gitignore` chặn `.env*`). Trên máy mới chạy `./setup.sh --set-key`
và gõ key (ẩn, không hiện ra màn hình). **Không bao giờ** dán key vào khung chat với Claude. Không có key cũ trong
tay thì tạo key mới ở elevenlabs.io → Developers → API Keys. Repo này phải để **private**: `docs/` có số GMV thật
và tên KOC.

**2. ElevenLabs gói Free không dùng thương mại được — và hiện đã hết credit.**
Chính trang trợ giúp của ElevenLabs ghi: *"The free plan does not include a commercial license and cannot be
used for any commercial purpose"*, và âm thanh tạo ngoài gói trả phí **không thể dùng thương mại kể cả sau
khi nâng cấp**. Tài khoản này đang là `free`, **còn 1/10.000 credit, reset 12/11/2026**.
→ Giọng đọc cho video bán hàng/khách hàng phải tạo **trong lúc đang có gói trả phí**.
Chạy `python3 skill/short-video-editing/scripts/make_voiceover.py --quota` để xem tình trạng hiện tại.

**3. Remotion miễn phí chỉ cho cá nhân hoặc công ty tối đa 3 nhân viên.** Trên mức đó: $25/ghế/tháng, và để
Claude viết code Remotion **vẫn tính là một ghế**. Công ty hiện 2 người nên đủ điều kiện — kiểm tra lại khi
team lớn lên.

## Cài trên máy mới (qua git)

```bash
# 1. Lấy mã nguồn. Repo private nên máy mới phải đăng nhập GitHub trước (một trong hai cách):
gh auth login && gh repo clone <chủ-sở-hữu>/short-video-kit        # cách 1: GitHub CLI
git clone git@github.com:<chủ-sở-hữu>/short-video-kit.git           # cách 2: SSH key đã thêm vào GitHub
cd short-video-kit

# 2. Để Claude tự cài — mở Claude Code TRONG thư mục này rồi nói "cài đặt":
claude "Đọc CLAUDE.md và cài đặt bộ kit này"
```

Claude Code **tự đọc `CLAUDE.md`** khi mở thư mục, trong đó ghi sẵn từng bước: chạy `setup.sh`, xử lý ffmpeg, nhắc bạn
nhập key bằng `--set-key`, chạy `selftest.sh`. Muốn tự cài bằng tay:

```bash
./setup.sh --download-ffmpeg    # bỏ cờ này nếu máy đã có ffmpeg (apt/brew install ffmpeg)
./setup.sh --set-key            # gõ key ElevenLabs (ẩn)
./selftest.sh                   # 5 nhóm kiểm tra, không tốn credit
```

`setup.sh` chạy lại nhiều lần được. Nó tải ~460MB model Whisper (Hugging Face) và, nếu bạn thêm
`--download-ffmpeg`, ~40MB ffmpeg tĩnh (johnvansickle.com, có kiểm checksum). Mọi thứ cài vào `$HOME`,
không vào thư mục repo.

**Bản git KHÔNG chứa** `bin/`, `models/`, `.env.local` — quá nặng (GitHub chặn file >100MB) hoặc bí mật.
Máy không có mạng thì dùng file nén `short-video-kit.tar.gz` (có sẵn ffmpeg + model, nhưng **chứa key thật** —
xem cảnh báo trong file đó).

Yêu cầu máy: Python 3.10+, Node 18+ (chỉ khi render Remotion), `xz` nếu dùng `--download-ffmpeg`.

## Dùng với Claude

Skill tự kích hoạt khi bạn nhờ làm video ngắn. Ví dụ câu lệnh:

> *Đây là 5 clip thô trong `~/clips/saiza`. Dựng video TikTok Shop 35 giây cho bộ tẩy mốc SAIZA, KOC memamnuoicon.*

> *Kiểm tra kịch bản này có câu nào vi phạm chính sách TikTok Shop không, rồi sửa lại.*

> *Có voice-over rồi (`audio/voice_full.mp3`) và kịch bản (`script.txt`) — làm phụ đề SRT.*

Claude sẽ soi clip → lập shot log → chọn hook → dựng timeline (kiểm bằng `pacing_checker`) → viết VO →
giọng đọc → phụ đề → xuất kế hoạch + SRT + lệnh ffmpeg. Chi tiết từng bước: `docs/WORKFLOW.md`.

Nếu Claude desktop app không thấy skill: mở `skill/short-video-editing.skill` rồi bấm **Save skill**.

## Trong thư mục có gì

| Đường dẫn | Nội dung |
|---|---|
| `skill/short-video-editing/` | Skill (nguồn). `SKILL.md` + 9 tài liệu tham chiếu + 4 script + mẫu kế hoạch |
| `skill/short-video-editing.skill` | Gói cài sẵn của chính skill đó |
| `docs/WORKFLOW.md` | Luồng làm việc từng bước, kèm lệnh |
| `docs/DECISIONS.md` | Vì sao chọn từng công cụ, các bẫy đã gặp, nguồn |
| `docs/niche-data-queries.sql` | Câu SQL tái hiện mọi số liệu trong skill (16.242 video SAIZA) |
| `docs/eval-results/` | Kết quả kiểm thử skill (xem mục "Chưa làm" bên dưới) |
| `docs/memory-notes.md` | Ghi chú Claude lưu về dự án này |
| `CLAUDE.md` | Hướng dẫn cho Claude tự cài đặt trên máy mới |
| `setup.sh` · `selftest.sh` | Cài đặt và kiểm tra |
| `samples/` | Dữ liệu mẫu cho `selftest.sh` |
| `legacy-hyperframes/` | Dự án cũ (HyperFrames + edge-tts), chỉ để tham khảo. Bản trên git bỏ `aff-video/` |

## Chưa làm / chưa kiểm chứng

Nói rõ để máy mới không tưởng nhầm là đã xong:

- **Chưa dựng thử dự án Remotion nào.** Skill có tài liệu `remotion-output.md` nhưng chưa có dự án Remotion
  chạy được. Hai video đã render đều làm bằng HyperFrames (cũ). Bước đầu tiên nên làm trên máy mới.
- **Chưa kiểm thử lại skill sau khi đổi stack.** 15/15 vs 8/15 trong `docs/eval-results/` là điểm của phiên bản
  *trước* khi thêm bước soi clip, ElevenLabs, Whisper và Remotion.
- **Chưa thử `eleven_v3` / `eleven_v4`** (hết credit giữa chừng). Chỉ `eleven_turbo_v2_5` được xác nhận chạy.
  Nhãn cảm xúc `[excited]`… chỉ có tác dụng với dòng v3, nên kịch bản Adam có nhãn chưa nghe thử đúng ý đồ.
- **Chưa đánh giá độ tự nhiên của giọng tiếng Việt.** Giọng `premade` là giọng tiếng Anh nói tiếng Việt; Whisper
  nghe ra được nhưng chất lượng phát âm phải nghe bằng tai. Giọng Việt chuyên nghiệp trong tài khoản (Ethan,
  `EcENCamMHdzIoMysqdsv`) cần gói trả phí mới gọi qua API được.

## Sự cố thường gặp

| Triệu chứng | Cách xử lý |
|---|---|
| `faster-whisper is not installed` | Chạy `./setup.sh` |
| `HTTP 402 … library voices` | Gói Free chỉ dùng được giọng `premade`. `make_voiceover.py --list-voices` |
| `Not enough credits` | `--quota` xem ngày reset. Script từ chối **trước** khi tiêu, không mất gì |
| `ffmpeg/ffprobe not found` | `./setup.sh --download-ffmpeg` (Linux), hoặc `apt install ffmpeg` / `brew install ffmpeg` |
| Phụ đề sai chính tả | Phải truyền `--script`. Không có nó, chữ lấy từ Whisper, vốn nghe sai tiếng Việt |
