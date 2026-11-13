# Example plan (used by selftest.sh)

**Playbook:** product-demo

## Scenes

| # | Start | End | Source | In | Type | Transition | Camera | Shot | Audio |
|---|-------|-----|--------|----|------|------------|--------|------|-------|
| 1 | 0.0 | 1.4 | clip_05.mp4 | 2.0 | HOOK | – | push 1.1>1.0 | Thớt khô, bạc màu | VO |
| 2 | 1.4 | 3.0 | clip_01.mp4 | 0.5 | HOOK | wipe right | | Cận cảnh vân gỗ | VO |
| 3 | 3.0 | 6.0 | clip_01.mp4 | 8.0 | PROBLEM | fade | | Giơ cả cái thớt | VO |
| 4 | 6.0 | 9.5 | clip_02.mp4 | 1.0 | DEMO | slide up | | Rót dầu lên mặt thớt | VO |
| 5 | 9.5 | 13.0 | clip_03.mp4 | 12.4 | DEMO | fade | pan left 5% | Dàn đều bằng khăn | VO |
| 6 | 13.0 | 16.5 | clip_03.mp4 | 28.1 | DEMO | fade | | Để thấm | VO |
| 7 | 16.5 | 20.0 | clip_04.mp4 | 0.0 | RE-HOOK | zoomThrough +flash | | Đổi góc | VO |
| 8 | 20.0 | 23.5 | clip_04.mp4 | 5.0 | DEMO | fade | | Wide mặt bàn bếp | nhạc |
| 9 | 23.5 | 27.0 | clip_05.mp4 | 10.0 | REVEAL | wipe right +leak | hold | Một take, không cắt | im lặng |
| 10 | 27.0 | 30.5 | clip_05.mp4 | 14.0 | REVEAL | blurDissolve | | Vuốt tay lên mặt thớt | VO |
| 11 | 30.5 | 33.5 | clip_02.mp4 | 20.0 | CTA-CLOSE | slide up | | Cầm chai dầu | VO |

## Overlays

| # | Start | End | Component | Zone | Tone | Content |
|---|-------|-----|-----------|------|------|---------|
| 1 | 0.0 | 1.3 | title | top | before | style=outline; lines=Cùng 1 cái thớt; sub=mặt thớt trước khi thoa |
| 2 | 3.2 | 5.9 | title | top | before | style=marker; lines=Khô và bạc màu; accent=bạc màu |
| 3 | 6.2 | 9.4 | step | top | – | n=1; text=Rót dầu lên mặt thớt |
| 4 | 9.7 | cut | cart | – | – | text=Giỏ hàng ở góc trái |
| 5 | 13.2 | 16.4 | progress | lower | – | label=Để thấm 20 phút · đã rút gọn thời gian |
| 6 | 16.7 | 19.9 | title | top | – | style=stack; lines=Không cần / chà mạnh; accent=chà mạnh |
| 7 | 23.7 | 26.9 | title | top | after | style=gradient; lines=Sau 20 phút |
| 8 | 27.2 | 30.4 | checklist | upper | – | items=Rót dầu / Dàn đều / Để thấm |
| 9 | 30.7 | 33.5 | cart | – | – | text=Giỏ hàng ở góc trái |
| 10 | 13.2 | 16.4 | thumbs | top | – | cards=clip_01@8.0:Gỗ khô~0.3,0.4,1.8 / clip_02@1.0:Rót dầu+1.2 / clip_03@12.4:Đã thấm+2.0 |
| 11 | 27.4 | 30.3 | compare | top | – | before=clip_05@2.0; after=clip_05@14.0; zoom=1.3; note=Cùng một cái thớt · sau 20 phút (đã rút gọn thời gian) |
