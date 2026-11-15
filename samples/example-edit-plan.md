# Example plan (used by selftest.sh)

**Playbook:** product-demo

## Scenes

| # | Start | End | Source | In | Type | Transition | Camera | Shot | Audio |
|---|-------|-----|--------|----|------|------------|--------|------|-------|
| 1 | 0.0 | 1.4 | clip_05.mp4 | 2.0 | HOOK | – | push 1.1>1.0 | Dry, faded cutting board | VO |
| 2 | 1.4 | 3.0 | clip_01.mp4 | 0.5 | HOOK | wipe right | | Close-up of the wood grain | VO |
| 3 | 3.0 | 6.0 | clip_01.mp4 | 8.0 | PROBLEM | fade | | Holding up the whole board | VO |
| 4 | 6.0 | 9.5 | clip_02.mp4 | 1.0 | DEMO | slide up | | Pouring oil onto the board | VO |
| 5 | 9.5 | 13.0 | clip_03.mp4 | 12.4 | DEMO | fade | pan left 5% | Spreading it evenly with a cloth | VO |
| 6 | 13.0 | 16.5 | clip_03.mp4 | 28.1 | DEMO | fade | | Letting it soak in | VO |
| 7 | 16.5 | 20.0 | clip_04.mp4 | 0.0 | RE-HOOK | zoomThrough +flash | | Change of angle | VO |
| 8 | 20.0 | 23.5 | clip_04.mp4 | 5.0 | DEMO | fade | | Wide shot of the kitchen counter | music |
| 9 | 23.5 | 27.0 | clip_05.mp4 | 10.0 | REVEAL | wipe right +leak | hold | One take, no cut | silence |
| 10 | 27.0 | 30.5 | clip_05.mp4 | 14.0 | REVEAL | blurDissolve | | Sweeping a hand across the board | VO |
| 11 | 30.5 | 33.5 | clip_02.mp4 | 20.0 | CTA-CLOSE | slide up | | Holding the oil bottle | VO |

## Overlays

| # | Start | End | Component | Zone | Tone | Content |
|---|-------|-----|-----------|------|------|---------|
| 1 | 0.0 | 1.3 | title | top | before | style=outline; lines=The same board; sub=the board before oiling |
| 2 | 3.2 | 5.9 | title | top | before | style=marker; lines=Dry and faded; accent=faded |
| 3 | 6.2 | 9.4 | step | top | – | n=1; text=Pour oil onto the board |
| 4 | 9.7 | cut | cart | – | – | text=Cart is in the left corner |
| 5 | 13.2 | 16.4 | progress | lower | – | label=Soak for 20 minutes · time shortened |
| 6 | 16.7 | 19.9 | title | top | – | style=stack; lines=No need to / scrub hard; accent=scrub hard |
| 7 | 23.7 | 26.9 | title | top | after | style=gradient; lines=After 20 minutes |
| 8 | 27.2 | 30.4 | checklist | upper | – | items=Pour the oil / Spread evenly / Let it soak |
| 9 | 30.7 | 33.5 | cart | – | – | text=Cart is in the left corner |
| 10 | 13.2 | 16.4 | thumbs | top | – | cards=clip_01@8.0:Dry wood~0.3,0.4,1.8 / clip_02@1.0:Pouring oil+1.2 / clip_03@12.4:Soaked in+2.0 |
| 11 | 27.4 | 30.3 | compare | top | – | before=clip_05@2.0; after=clip_05@14.0; zoom=1.3; note=The same board · after 20 minutes (time shortened) |
