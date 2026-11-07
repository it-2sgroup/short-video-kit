# Example plan: a music-driven property tour (used by selftest.sh)

**Playbook:** real-estate

## Scenes

| # | Start | End | Source | In | Type | Transition | Camera | Speed | Shot | Audio |
|---|-------|-----|--------|----|------|------------|--------|-------|------|-------|
| 1 | 0.0 | 1.5 | villa_02.mov | 11.0 | HOOK | – | pull 1.18>1.0 | | Pool from the balcony | beat 1 |
| 2 | 1.5 | 3.0 | villa_01.mov | 2.0 | HOOK | cut | | | Living room, wide | |
| 3 | 3.0 | 5.6 | villa_02.mov | 0.0 | ARRIVAL | whip left | | ramp 1>2>1 | Walk in from the door | |
| 4 | 5.6 | 8.4 | villa_01.mov | 8.0 | LIVING | cut | | | Sofa and windows | |
| 5 | 8.4 | 11.2 | villa_03.mov | 1.0 | KITCHEN | slide left | | | Island, pendant lights | |
| 6 | 11.2 | 14.0 | villa_03.mov | 9.0 | BEDROOM | fade 10f | | | Master bedroom | |
| 7 | 14.0 | 16.4 | villa_04.mov | 0.5 | FEATURE | zoomThrough +leak | | 0.5x | Sunset from the rooftop | |
| 8 | 16.4 | 20.4 | villa_04.mov | 6.0 | SPECS | blurDissolve | | | Calm wide of the terrace | |
| 9 | 20.4 | 23.4 | villa_05.mov | 3.0 | BATH | cut | | | Bathroom, one clean frame | |
| 10 | 23.4 | 26.6 | villa_01.mov | 20.0 | CTA | fade 16f | | | Front door closing | |

## Overlays

| # | Start | End | Component | Zone | Tone | Content |
|---|-------|-----|-----------|------|------|---------|
| 1 | 0.0 | 2.9 | title | top | – | style=glass; lines=Villa 3PN có hồ bơi / Thảo Điền; accent=hồ bơi |
| 2 | 3.2 | +2.2 | pin | top | – | title=Thảo Điền, TP Thủ Đức; sub=Cách Q1 ~15 phút (ước tính) |
| 3 | 5.8 | +2.3 | label | – | – | text=Phòng khách; sub=42 m² |
| 4 | 14.2 | 16.2 | stat | upper | – | value=120; unit= m²; label=Sân thượng |
| 5 | 16.6 | 20.2 | specs | upper | – | title=Thông tin; items=area:320 m² đất / bed:3 PN / bath:4 WC / compass:Đông Nam |
| 6 | 17.0 | 20.2 | price | lower | cta | value=28.5; decimals=1; unit= tỷ; label=Giá bán |
| 7 | 23.6 | 26.4 | lowerThird | lower | – | name=Tên môi giới; role=Đặt lịch xem nhà |
| 8 | 8.6 | 11.0 | chart | upper | – | title=Ánh sáng tự nhiên; items=Phòng khách#9 / Bếp#7 / Phòng ngủ#8; unit= giờ |
| 9 | 11.4 | 13.8 | image | – | – | src=images/floorplan.png; at=0.5,0.3; width=600; caption=Mặt bằng tầng 2 |
