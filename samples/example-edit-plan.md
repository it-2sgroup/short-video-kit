# Example plan (used by selftest.sh)

## Scenes

| # | Start | End | Source | In | Type | Transition | Camera | Shot | Audio |
|---|-------|-----|--------|----|------|------------|--------|------|-------|
| 1 | 0.0 | 1.4 | clip_05.mp4 | 2.0 | HOOK | – | push 1.1>1.0 | Áo nhấc lên, vết mờ | VO |
| 2 | 1.4 | 3.0 | clip_01.mp4 | 0.5 | HOOK | wipe right | | Macro vết ố | VO |
| 3 | 3.0 | 6.0 | clip_01.mp4 | 8.0 | PROBLEM | fade | | Giơ cả áo | VO |
| 4 | 6.0 | 9.5 | clip_02.mp4 | 1.0 | DEMO | slide up | | Đổ chai hồng | VO |
| 5 | 9.5 | 13.0 | clip_03.mp4 | 12.4 | DEMO | fade | pan left 5% | Dí cho ngấm | VO |
| 6 | 13.0 | 16.5 | clip_03.mp4 | 28.1 | DEMO | fade | | Thả vào thau | VO |
| 7 | 16.5 | 20.0 | clip_04.mp4 | 0.0 | RE-HOOK | zoomThrough +flash | | Đổi góc | VO |
| 8 | 20.0 | 23.5 | clip_04.mp4 | 5.0 | DEMO | fade | | Wide thau | nhạc |
| 9 | 23.5 | 27.0 | clip_05.mp4 | 10.0 | REVEAL | wipe right +leak | hold | Một take, không cắt | im lặng |
| 10 | 27.0 | 30.5 | clip_05.mp4 | 14.0 | REVEAL | blurDissolve | | Vuốt vải | VO |
| 11 | 30.5 | 33.5 | clip_02.mp4 | 20.0 | CTA-CLOSE | slide up | | Cầm 2 chai | VO |

## Overlays

| # | Start | End | Component | Zone | Tone | Content |
|---|-------|-----|-----------|------|------|---------|
| 1 | 0.0 | 1.3 | title | top | before | style=outline; lines=Cùng 1 cái áo; sub=vết thử bằng thuốc đỏ |
| 2 | 3.2 | 5.9 | title | top | before | style=marker; lines=Ố 2 tháng; accent=Ố |
| 3 | 6.2 | 9.4 | step | top | – | n=1; text=Đổ chai hồng |
| 4 | 9.7 | cut | cart | upper | – | text=Giỏ hàng ở góc trái |
| 5 | 13.2 | 16.4 | progress | lower | – | label=Ngâm 2 tiếng · đã rút gọn thời gian |
| 6 | 16.7 | 19.9 | title | top | – | style=stack; lines=Chưa chà / lần nào; accent=lần nào |
| 7 | 23.7 | 26.9 | title | top | after | style=gradient; lines=Sau 2 tiếng |
| 8 | 27.2 | 30.4 | checklist | upper | – | items=Chai hồng / Ngâm 2 tiếng / Xả nước |
| 9 | 30.7 | 33.5 | cart | upper | – | text=Giỏ hàng ở góc trái |
