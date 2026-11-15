# Example plan: a music-driven property tour (used by selftest.sh)

**Playbook:** real-estate

## Scenes

| # | Start | End | Source | In | Type | Transition | Camera | Speed | Shot | Audio |
|---|-------|-----|--------|----|------|------------|--------|-------|------|-------|
| 1 | 0.0 | 1.5 | clip_02.mov | 11.0 | HOOK | – | pull 1.18>1.0 | | Pool from the balcony | beat 1 |
| 2 | 1.5 | 3.0 | clip_01.mov | 2.0 | HOOK | cut | | | Living room, wide | |
| 3 | 3.0 | 5.6 | clip_02.mov | 0.0 | ARRIVAL | whip left | | ramp 1>2>1 | Walk in from the door | |
| 4 | 5.6 | 8.4 | clip_01.mov | 8.0 | LIVING | cut | | | Sofa and windows | |
| 5 | 8.4 | 11.2 | clip_03.mov | 1.0 | KITCHEN | slide left | | | Island, pendant lights | |
| 6 | 11.2 | 14.0 | clip_03.mov | 9.0 | BEDROOM | fade 10f | | | Master bedroom | |
| 7 | 14.0 | 16.4 | clip_04.mov | 0.5 | FEATURE | zoomThrough +leak | | 0.5x | Sunset from the rooftop | |
| 8 | 16.4 | 20.4 | clip_04.mov | 6.0 | SPECS | blurDissolve | | | Calm wide of the terrace | |
| 9 | 20.4 | 23.4 | clip_05.mov | 3.0 | BATH | cut | | | Bathroom, one clean frame | |
| 10 | 23.4 | 26.6 | clip_01.mov | 20.0 | CTA | fade 16f | | | Front door closing | |

## Overlays

| # | Start | End | Component | Zone | Tone | Content |
|---|-------|-----|-----------|------|------|---------|
| 1 | 0.0 | 2.9 | title | top | – | style=glass; lines=3-bedroom villa with a pool / Area A; accent=pool |
| 2 | 3.2 | +2.2 | pin | top | – | title=Area A, City X; sub=About 15 minutes from the centre (estimate) |
| 3 | 5.8 | +2.3 | label | – | – | text=Room name; sub=42 m² |
| 4 | 14.2 | 16.2 | stat | upper | – | value=120; unit= m²; label=Rooftop terrace |
| 5 | 16.6 | 20.2 | specs | upper | – | title=Details; items=area:320 m² land / bed:3 BR / bath:4 WC / compass:Southeast |
| 6 | 17.0 | 20.2 | price | lower | cta | value=28.5; decimals=1; unit= billion; label=Sale price |
| 7 | 23.6 | 26.4 | lowerThird | lower | – | name=Agent name; role=Book a viewing |
| 8 | 8.6 | 11.0 | chart | upper | – | title=Natural light; items=Room A#9 / Room B#7 / Room C#8; unit= hours |
| 9 | 11.4 | 13.8 | image | – | – | src=images/floorplan.png; at=0.5,0.3; width=600; caption=Floor plan, level 2 |
