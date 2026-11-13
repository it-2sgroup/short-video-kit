# Chính sách — video bị đánh vi phạm khi dùng lại, trùng lặp hoặc lấy cảnh của video khác

Tài liệu này trả lời một câu hỏi: **làm video bán hàng TikTok Shop từ một nguồn quay có sẵn, với số
lượng lớn (hàng trăm video), thì cách nào bị đánh vi phạm và cách nào an toàn?** Nó cũng trả lời việc có
được lấy cảnh từ video của người khác (ví dụ Douyin) để ghép vào hay không.

**Claude phải đọc file này trước khi** lập kế hoạch cho một lô video, trước khi dùng bất kỳ cảnh quay
nào không phải do người dùng quay hoặc không có giấy phép, và trước khi đề xuất "đảo cảnh / đổi nhạc để
ra thêm video".

Kiểm tra ngày 2026-11-06. Đây là tổng hợp chính sách để làm việc, **không phải tư vấn pháp lý**.
Nhãn độ tin cậy: **[P]** trang chính sách chính thức đã đọc; **[S]** nguồn thứ cấp (blog, báo, hãng luật);
**[C]** quy ước của bộ công cụ này; **[?]** chưa kiểm chứng.

---

## 1. Tám quy tắc cho Claude

1. **Không dùng cảnh quay của bên thứ ba** (Douyin, TikTok, Kuaishou, YouTube, Facebook, shop đối thủ,
   video của creator khác) khi chưa có **giấy phép thương mại bằng văn bản** của chủ sở hữu. Hỏi người
   dùng; không tự tải, không tự cắt.
2. **Không chạy, không sửa, không dựng lại** quy trình kiểu "crawl video Douyin" (tải Douyin không
   watermark → cắt → lồng tiếng → đăng lại) cho video bán hàng. Mục 4.3 giải thích vì sao.
3. **Một đoạn nguồn không dùng ở hai video trong cùng một lô** (mặc định `r = 1`, mục 5). Muốn nhiều
   video hơn số cảnh quay cho phép thì **nói số liệu và đề xuất quay thêm**, không xáo trộn cảnh.
4. **Hai video khác nhau phải khác nhau thật**: kịch bản, giọng, hook, cấu trúc, cảnh. TikTok Shop gọi
   đích danh "đăng lại cùng video chỉ đổi thứ tự clip" và "dùng cùng một kịch bản bán hàng chung cho
   nhiều sản phẩm" là nội dung lặp (mục 2.2). Đổi nhạc, giọng, nền **không** cứu được.
5. **Cảnh quay phải là của đúng sản phẩm đang quảng cáo.** Không ghép kết quả của sản phẩm khác để làm
   "kết quả" (mục 2.5). Cảnh dựng sẵn hoặc tua nhanh phải gắn nhãn trên màn hình.
6. **Hỏi thị trường và giới hạn đăng.** Mỗi thị trường có giới hạn riêng (mục 2.6); thị trường Việt Nam
   chưa kiểm chứng được. Không lên lịch đăng hàng trăm video dồn vào một tài khoản, và không đăng cùng
   nội dung lên nhiều tài khoản.
7. **Before/after trong quảng cáo trả phí** bị chính sách quảng cáo cấm (`before-after.md`). Hỏi người
   dùng có định chạy quảng cáo / Spark Ads không.
8. **Báo cáo trung thực**: nêu rủi ro bằng số liệu, nêu điều chưa kiểm chứng (mục 7), không nói "an toàn"
   khi nguồn chỉ là blog.

---

## 2. Các nhóm vi phạm

### 2.1 Nội dung không gốc / tái sử dụng

| Quy định | Nguồn |
|---|---|
| "Content is also ineligible for the FYF if it includes unoriginal or reused material without anything new." Nội dung tái sử dụng mà không có gì mới thì **không đủ điều kiện lên For You**. | [P] Community Guidelines, *Integrity & Authenticity* |
| "You should only post content you created or have the right to share." Chỉ đăng thứ mình tạo ra hoặc có quyền chia sẻ. | [P] cùng trang |
| TikTok Shop: nội dung bị coi là không gốc nếu "the user has not added new or creative edits to any imported or uploaded media". Watermark hoặc logo hiện trên video "is a sign of unoriginal content". | [P] TikTok Shop Academy, *Content Policy* (US, 2026-10-26) |
| Hình phạt (TikTok Shop): xóa nội dung, hạn chế tính năng, điểm vi phạm, hạn chế tài khoản; áp dụng cho "all Creators and the content they promote". | [P] cùng trang |

Hệ quả: video ghép từ cảnh của người khác **không có phần sáng tạo mới thật sự** là loại bị xử lý nhẹ nhất
(mất phân phối) tới nặng (gỡ video, điểm vi phạm). Dùng cảnh Douyin còn rơi vào mục 2.4.

### 2.2 Nội dung lặp (repetitive / near-duplicate) — kể cả nội dung của chính mình

TikTok Shop định nghĩa nội dung lặp là nội dung "published continuously and in bulk, where the
structure, visuals, narration, or materials are highly similar". Hai ví dụ nêu thẳng trong chính sách:

- "Re-posting the same video at high volume with only order of clips changed." (**đăng lại cùng video hàng
  loạt, chỉ đổi thứ tự clip**)
- "Using the same generic sales script for a range of different products." (**cùng một kịch bản chung cho
  nhiều sản phẩm**)

Chính sách nói thay đổi nhỏ về nhạc, lời đọc, nền **không** làm hết lặp. [P] *Content Policy*, US.

Bản Malaysia của bài *Content Posting Limit* liệt kê thêm: số lượng lớn video "hampir sama dengan variasi
kreatif yang minimum" (gần giống nhau, ít biến thể sáng tạo) và "menyiarkan video yang serupa pada beberapa
akaun" (đăng video tương tự trên nhiều tài khoản). [P] seller-my.tiktok.com (bản Malay, 2026-10-16).

**Đây là điểm trúng đích với kế hoạch "một nguồn → hàng trăm video":** xáo cảnh từ một nguồn quay chính là
"đổi thứ tự clip".

Ngưỡng định lượng ("giống bao nhiêu phần trăm thì bị đánh") **không được công bố** [?]. Blog nói TikTok
dùng nhận dạng nội dung (fingerprint) để bắt trùng; đó là suy đoán của blog, không có trong chính sách [S].

### 2.3 Spam, hành vi giả mạo, nhiều tài khoản, công cụ tự động

- "You can have multiple accounts … but not to deceive others or break the rules." Được có nhiều tài khoản,
  không được dùng để lách luật. [P] *Integrity & Authenticity*
- "We strictly prohibit automation tools, scripts, or other tricks designed to bypass our systems." [P] cùng trang
- Liệt kê vi phạm của creator TikTok Shop có mục "Using multiple accounts to avoid enforcement". [P]
  *Creator Enforcement Policy* (US, 2026-10-09)
- Hình phạt cho hành vi giả mạo: hạn chế tài khoản, "limiting your ability to post new content, appear in
  top search results, or in the FYF". [P] *Integrity & Authenticity*

Hệ quả: chia một lô video giống nhau ra nhiều tài khoản để "né" giới hạn là hướng bị xử lý.

### 2.4 Bản quyền / sở hữu trí tuệ

**TikTok.** [P] *Copyright Policy* (2025-03-27):
- "We do not allow any content that infringes copyright."
- "The use of copyrighted content of others without proper authorization or legally valid reason may lead
  to a violation of TikTok's policies." (có nhắc *fair use* của Mỹ và *fair dealing* của EU như lý do hợp
  pháp, nhưng không đảm bảo)
- Có quyền "ban the account of a user who repeatedly commits copyright infringement" và "immediately ban
  any account in cases of severe copyright violations".
- Có kháng nghị trong app; chủ bản quyền có thể phản đối kháng nghị.
- Không tìm thấy số lượng "gậy bản quyền" cụ thể [?].

**Douyin (nguồn video Trung Quốc).** [P] Thỏa thuận người dùng Douyin (cập nhật 2026-02-13, hiệu lực 2026-02-20):
- Quyền sở hữu trí tuệ của video thuộc người đăng hoặc chủ bản quyền gốc (điều 10.2).
- Người dùng chỉ được cấp quyền dùng Douyin **"cá nhân, … không thương mại"** và **không được** "改编、复制、传播、爬虫" —
  chỉnh sửa, sao chép, phát tán, crawl (điều 2.4).
- Cấm công cụ tự động thu thập nội dung (điều 5.1).
- Khi chưa có **giấy phép bằng văn bản** của Douyin, cấm: chỉnh sửa rồi hiển thị ở nền tảng khác (5.3-2), tải
  bằng scrape / mô phỏng tải (5.3-4), che hoặc sửa logo Douyin (5.3-5), và **"将抖音中的信息或内容用于任何形式的销售和商业使用"
  — dùng nội dung cho bất kỳ hình thức bán hàng hoặc thương mại** (5.3-7).
- Luật áp dụng là luật Trung Quốc, tòa Hải Điện (Bắc Kinh) có thẩm quyền (điều 16). Điều 14.6: Douyin không
  bảo đảm hợp pháp ở ngoài nơi phát hành chính thức; người dùng tự chịu trách nhiệm theo luật nơi mình ở.

Điều 10.5 cho phép người dùng khác "转发、复制、下载" **theo tính năng nền tảng** — đó là xem, chia sẻ, tải cá
nhân; không phải giấy phép thương mại.

**Luật.**
- Trung Quốc: tòa Internet Bắc Kinh (2018, Douyin kiện Huopai) công nhận video ngắn, kể cả 15 giây, là tác
  phẩm được luật bản quyền bảo vệ. [S] technode, caixin, ipkitten. Có vụ hình sự ở Gia Hưng về kẻ lấy hàng loạt
  clip phim, sửa và né bộ lọc để đăng lại kiếm lời. [S]
- Việt Nam: Luật Sở hữu trí tuệ Điều 28 liệt kê hành vi xâm phạm quyền tác giả, trong đó sao chép tác phẩm
  khi chưa được phép của chủ sở hữu. [S] bài tổng hợp của các hãng luật; chưa đối chiếu văn bản gốc [?].
  Mức xử phạt hành chính hiện nằm ở Nghị định 341/2025/NĐ-CP, chưa đọc được mức tiền [?]; có khung hình sự cho
  mức nghiêm trọng, chưa xác minh con số [?].

Kết luận mục này: **tải video Douyin rồi ghép vào video bán hàng vi phạm điều khoản Douyin, rủi ro bản quyền
ở cả Trung Quốc lẫn Việt Nam, và vi phạm chính sách bản quyền của TikTok.** Cắt nhỏ hay đổi tốc độ không biến
nó thành "nội dung mới" (mục 2.1).

### 2.5 Mô tả gây hiểu lầm: cảnh của sản phẩm khác, kết quả không phải của mình

- TikTok Shop, *How to Avoid Misleading Content* (áp dụng toàn cầu): hậu quả "content removal or account
  suspension". [P] seller-us.tiktok.com (2026-06-25)
- Before/after phải cùng ánh sáng, góc máy, không dựng khác biệt; demo phải phản ánh hiệu quả thật. Xem
  `claims-and-compliance.md` §3.
- Video demo "kết quả" lấy từ sản phẩm khác (như clip Douyin) cho người xem tưởng là kết quả của sản phẩm đang bán là
  **quảng cáo sai sự thật**, chưa kể rủi ro bản quyền. Việt Nam: Luật Quảng cáo cấm quảng cáo gây nhầm lẫn;
  Nghị định 38/2021/NĐ-CP có khung phạt, nguồn thứ cấp ghi 60–80 triệu đồng cho quảng cáo không đúng hoặc gây
  nhầm lẫn, trần 100 triệu (cá nhân) và 200 triệu (tổ chức), và một nguồn nói đã đổi từ 2026-05-15 [S][?].
  Chưa đối chiếu văn bản; cần người kiểm.
- Nhắc lại luật của bộ công cụ: không gán nhãn "đánh giá thật của khách" cho đồ họa dựng sẵn (`CLAUDE.md`).

### 2.6 Giới hạn tần suất đăng

| Thị trường | Quy định | Nguồn |
|---|---|---|
| Mỹ | Từ 2026-05-11: tối đa 30 video mua sắm ngắn và 60 bài ảnh mỗi ngày; affiliate thử nghiệm dưới 5.000 follower: 3 video mỗi ngày và 3 LIVE mỗi tuần | [P] *Creator Eligibility Policy* (2026-09-25) |
| Malaysia | Đăng 5 video trở lên "tidak interaktif atau mengelirukan" (không tương tác hoặc gây hiểu lầm) trong 7 ngày thì bị giới hạn 7 video trong 7 ngày kế tiếp; video vượt hạn mức vẫn đăng nhưng **mất liên kết sản phẩm**. Lời đọc thu sẵn hoặc giọng máy được tính là "không tương tác" | [P] *Content Posting Limit* và bài *Non-interactive content* (seller-my, 2026-10-16 và 2026-11-05) |
| Việt Nam | **Chưa tìm được trang chính thức** | [?] — kiểm tra Seller Center / Creator Academy VN |

Video của bộ công cụ này dùng giọng thu sẵn, nên nếu thị trường áp dụng định nghĩa "không tương tác" như
Malaysia thì **hàng loạt video giọng thu sẵn có thể bị giới hạn** dù không trùng cảnh.

### 2.7 Quảng cáo trả phí

Chính sách quảng cáo TikTok không cho phép "product effect comparisons, such as before-and-after results"
trong quảng cáo và trang đích [P]; xem `before-after.md`. Hỏi người dùng có chạy Spark Ads hoặc quảng cáo không.

---

## 3. Leo thang xử lý

| Bước | Điều chính sách nói | Nguồn |
|---|---|---|
| Phân phối | Video "không gốc" mất quyền lên For You; tài khoản đăng nhiều nội dung không đủ điều kiện có thể bị cả tài khoản mất đủ điều kiện | [P] + [S] |
| Cảnh báo, hạn chế | "a warning, temporary feature or account restriction, or a full account ban, depending on what happened" | [P] *Accounts & features* |
| TikTok Shop (Mỹ) | Gỡ nội dung, giới hạn video mua sắm, đóng băng hoa hồng, đình chỉ kiếm tiền, giảm lượt tiếp cận. **Cùng một vi phạm 6 lần trong 90 ngày** thì có thể mất quyền thương mại điện tử và bị đóng băng hoa hồng. Cảnh cáo lần đầu không tính điểm | [P] *Creator Enforcement Policy* |
| Cấm tài khoản | "Repeated rule violations" hoặc "A single, severe violation"; vi phạm bản quyền nặng bị cấm ngay | [P] *Accounts & features*, *Copyright Policy* |
| Kháng nghị | Kháng nghị trong 30 ngày kể từ khi bị xử lý, một lần cho mỗi vi phạm; hoa hồng bị đóng băng có thể bị mất nếu kháng nghị muộn hoặc bị bác | [P] *Creator Enforcement Policy* (US) |

---

## 4. Áp dụng: một nguồn quay phải ra nhiều video

### 4.1 "Từ một nguồn phải ra 200–300 video": cần bao nhiêu cảnh quay

Một video 12 cảnh cần khoảng **42 giây nguồn riêng** (12 cảnh × 3,5 giây gồm khoảng đệm 0,5 giây giữa hai
đoạn của cùng một clip, xem `footage-ingest.md` §1b). Ví dụ một nguồn 587 giây ≈ 9,8 phút đủ cho khoảng 14
video khi không dùng lại cảnh nào. Gọi `r` là số video được dùng chung cùng một đoạn nguồn:

| Số video | `r = 1` (không dùng lại) | `r = 2` | `r = 3` | `r = 5` |
|---|---|---|---|---|
| 14 | 9,8 phút | | | |
| 200 | 140 phút | 70 phút | 47 phút | 28 phút |
| 250 | 175 phút | 88 phút | 58 phút | 35 phút |
| 300 | 210 phút | 105 phút | 70 phút | 42 phút |

(Cần bao nhiêu phút **cảnh quay dùng được** để đạt số video với mức dùng lại `r`.)

- Với một nguồn cỡ 10 phút, 200–300 video chỉ làm được nếu **mỗi đoạn nguồn dùng lại khoảng 14–21 lần**. Đó là mô
  hình "đăng lại, đổi thứ tự clip" mà TikTok Shop nêu tên là nội dung lặp (mục 2.2).
- Đổi giọng, nhạc, nền, crop, tốc độ **không** cứu: chính sách nói thay đổi nhỏ về nhạc, lời đọc, nền không
  làm hết lặp, và "visuals" nằm trong danh sách yếu tố so sánh.
- Ngưỡng an toàn không được công bố [?]. Quy ước của bộ công cụ [C]: **`r = 1`** là mặc định an toàn;
  `r = 2` chỉ khi hai video khác hẳn kịch bản, giọng, hook và thứ tự, và người dùng đã chấp nhận rủi ro.
- Kể cả có đủ cảnh quay, đăng 200–300 video từ một tài khoản đụng giới hạn tần suất (mục 2.6) và dễ bị coi là
  spam. Cách mở rộng hợp lệ là **nhiều creator thật, mỗi người quay và đăng nội dung của mình** (mục 6).

### 4.2 "Lấy khung cảnh từ video khác ghép vào"

| Nguồn cảnh | Kết luận | Lý do |
|---|---|---|
| Douyin, TikTok, Kuaishou, YouTube… của người khác | **Không** nếu chưa có giấy phép thương mại bằng văn bản | Mục 2.1, 2.4, 2.5 |
| Video của đối thủ hoặc shop khác | **Không** | Cùng lý do, thêm nguy cơ khiếu nại bản quyền và thương hiệu |
| Video khách hàng gửi | Chỉ khi có **đồng ý bằng văn bản** cho phép dùng thương mại và đăng lên kênh | Quyền thuộc về người quay |
| Video creator/KOC được thuê | **Được** nếu hợp đồng nêu rõ quyền dùng thương mại và quyền chỉnh sửa; Spark Ads cần mã ủy quyền | Có quyền chia sẻ (mục 2.1) |
| Kho video bản quyền (stock) | Chỉ làm **cảnh nền / không khí**, không làm "kết quả của sản phẩm" | Quyền dùng thương mại có, nhưng không phải cảnh của sản phẩm mình (mục 2.5) |
| Cảnh AI tạo | **Không** cho kết quả của sản phẩm | Cấm demo hiệu quả phi thực tế và phải gắn nhãn AI (`claims-and-compliance.md` §3) |
| Xem Douyin làm **tham khảo ý tưởng**, rồi tự quay lại | **Được** | Ý tưởng, kiểu cảnh không phải tác phẩm; quay mới là nội dung gốc |

### 4.3 Quy trình "tải Douyin → lồng tiếng → đăng lại" (đã đọc một repo mẫu, chỉ đọc, không chạy)

Các repo mã nguồn mở kiểu "crawl video Douyin" (một repo Python công khai đã được đọc làm mẫu) làm đúng một việc: **tải video
Douyin không watermark** (đổi `/playwm/` thành `/play/` trong đường dẫn playback, dựa vào cấu trúc trang
nội bộ của Douyin; hoặc yt-dlp; hoặc công cụ ngoài như `Douyin_TikTok_Download_API`, `f2` để tải hàng loạt
theo user / hashtag), rồi **STT → dịch → TTS → làm mờ caption gốc → chèn phụ đề → đăng lên TikTok** bằng
Content Posting API. Repo mẫu không có phần nào nhận diện nội dung sản phẩm hay cắt theo cảnh.

Vì sao **không** nên dùng cho video bán hàng:
- Tải bằng cách scrape trang nội bộ, tránh watermark = đúng các điều Douyin cấm (5.1, 5.3-4, 5.3-5, 2.4).
- Dùng thương mại bị cấm khi chưa có giấy phép viết tay (5.3-7).
- Quy trình "tải → lồng tiếng → đăng lại" là mô hình **nội dung tái sử dụng**, cùng loại mà mục 2.1 nói
  không đủ điều kiện lên For You và có thể bị gỡ.
- README của repo mẫu ghi: "Chỉ tải/lồng tiếng/đăng lại video công khai cho mục đích cá nhân/nghiên cứu …
  Không dùng để tải hàng loạt/re-upload thương mại … mà không có sự cho phép của chủ sở hữu."
- Phần đăng của repo mẫu dùng ứng dụng chưa qua audit của TikTok, chỉ đăng được ở chế độ riêng tư.

Nếu sau này cần cảnh từ Douyin: **xin giấy phép thương mại từ chủ video** (liên hệ trực tiếp, mua bản quyền),
lưu văn bản, rồi mới đưa vào kho cảnh quay với dòng ghi nguồn. Khi đó mới dùng công cụ cắt cảnh. Claude không
được tải trước "để thử".

---

## 5. Quy ước kiểm soát trùng cảnh của bộ công cụ [C]

Áp dụng cho mọi lô video:

1. **Sổ cái nguồn.** Mọi `edit-plan.md` của lô nằm cạnh nhau; chạy `footage_overlap_checker.py` với **tất cả**
   file kế hoạch (tên từng file). Kết quả phải là PASS (không trùng, mỗi đoạn cách nhau ≥ 0,5 giây).
2. **`r = 1` mặc định.** Hết đoạn nguồn chưa dùng thì **dừng và báo**, kèm số phút cần quay thêm (bảng ở mục 4.1).
3. **Biến thể thật, không phải xáo trộn.** Giữa hai video bất kỳ phải khác **kịch bản** và **giọng**; thêm ít nhất
   hai trong ba yếu tố: hook, cấu trúc cảnh, nhóm đồ họa. Chỉ đổi thứ tự clip, nhạc, nền, crop, tốc độ là **không
   đủ** (mục 2.2).
4. **Một kịch bản cho một sản phẩm.** Không dùng khung kịch bản chung cho nhiều sản phẩm.
5. **Không chia một lô giống nhau cho nhiều tài khoản.**
6. **Cảnh của đúng sản phẩm**; cảnh dựng sẵn và tua nhanh có nhãn.
7. **Trước khi đăng:** hỏi thị trường, kiểm tra giới hạn đăng, nhắc bật "Disclose commercial content", hỏi có chạy
   quảng cáo không.

---

## 6. Cách đi hợp lệ để có số lượng lớn

- **Quay theo ma trận biến thể** thay vì quay một lần rồi xáo: mỗi tổ hợp *đối tượng (loại vật liệu, màu, kiểu…) ×
  tình huống (vấn đề cần giải quyết) × mẫu sản phẩm (loại, cỡ, combo) × góc quay (từ trên, ngang, cận)* ra một bộ
  clip riêng gồm trước, thao tác, kết quả. Dự trù **~42 giây cảnh dùng được cho mỗi video**.
- **Mạng creator / KOC**: mỗi người tự quay và đăng nội dung của mình, bạn dùng quyền dùng lại bằng hợp đồng
  hoặc mã Spark Ads. Đây là cách TikTok Shop thiết kế để mở rộng quy mô [C].
- **Video khách hàng** có đồng ý bằng văn bản.
- **Kho stock** chỉ cho cảnh nền; không cho kết quả.
- **Ý tưởng từ Douyin** thì xem làm tham khảo rồi quay lại bằng sản phẩm của mình.
- Dựng bằng bộ công cụ này vẫn rẻ; thứ khan hiếm là **cảnh quay hợp lệ**, không phải khâu dựng.

---

## 7. Chưa kiểm chứng, cần người kiểm tra

- **Chính sách TikTok Shop Việt Nam** (nội dung lặp, giới hạn đăng, điểm vi phạm): chưa tìm được trang chính
  thức; các trang đã đọc là bản Mỹ và Malaysia. Kiểm tra Seller Center / Creator Academy VN.
- **Ngưỡng "giống nhau"** mà TikTok dùng để đánh lặp: không công bố; mọi con số trên blog là suy đoán.
- **Bài hỗ trợ TikTok về watermark của ứng dụng khác** (video có logo Douyin bị loại khỏi For You): trang trợ giúp
  không đọc được; chỉ có dòng "visible watermark … sign of unoriginal content" trong Content Policy của Shop.
- **Luật Việt Nam**: chưa đối chiếu Điều 28 Luật Sở hữu trí tuệ với văn bản gốc; chưa đọc mức phạt ở Nghị định
  341/2025/NĐ-CP; các con số của Nghị định 38/2021 mâu thuẫn giữa các nguồn.
- **Pháp luật Trung Quốc** chỉ qua báo chí (vụ 2018 và vụ hình sự Gia Hưng).
- Các nguồn thứ cấp nói TikTok Shop bắt đầu siết nội dung không gốc từ 2025-09-15 và nội dung lặp từ 2025-09-25:
  không có thông báo chính thức đi kèm [S][?].

## 8. Nguồn

Chính thức: TikTok Community Guidelines (`tiktok.com/community-guidelines/en/integrity-authenticity`,
`fyf-standards`, `accounts-features`, `enforcement`, `regulated-commercial-activities`); TikTok Copyright
Policy (`tiktok.com/legal/page/global/copyright-policy/en`); TikTok Shop Academy: *Content Policy* (US,
`knowledge_id=6837891779151617`), *Creator Enforcement Policy* (`6837869503317761`), *Creator Eligibility Policy*
(`6939143037667118`), *How to Avoid Misleading Content* (`4581457528194817`), *Content Posting Limit* (seller-my,
`6519771097237249`), *Non-interactive content* (seller-my, `752633581209360`); TikTok Ads policy *Misleading and
false content*; Thỏa thuận người dùng Douyin (`douyin.com/draft/douyin_agreement/douyin_agreement_user.html`).

Thứ cấp: BigSeller (bài 3778, 3766, 4377, 4203), PPC Land (hai bài tháng 6/2026), Calywire, TokPortal;
technode, caixin, ipkitten về vụ Douyin kiện Huopai; các bài tổng hợp luật của luatvietnam.vn, lsvn.vn,
thuvienphapluat.vn về Điều 28 Luật SHTT, Nghị định 341/2025 và Nghị định 38/2021.

Repo mẫu đã đọc: một repo mã nguồn mở công khai kiểu "crawl video Douyin" (đọc README và mã tải/đăng qua GitHub API;
không tải, không chạy).
