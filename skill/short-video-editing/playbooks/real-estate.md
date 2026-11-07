# Playbook: real-estate — property tour (căn hộ, nhà phố, villa, homestay, đất nền)

A tour cut to music: the best view first, then the route a visitor walks, the facts on screen, and how
to book a viewing. Goal: leads (Zalo/DM/calls, viewing bookings), bookings for rentals, saves and shares.

Variant: `real-estate:voiceover` when an agent's voice (recorded or on camera) carries the tour; cuts
then follow the voice and captions are on (`karaoke`; switch to `plain` for a calm, static style).

Labels: **[S]** sourced, **[C]** craft convention, **[L]** law (research, not legal advice).

## When to use it

- Footage: wide interiors and exteriors, the camera walking or gliding through rooms (gimbal, slider,
  drone), windows and views, furniture details; nobody talking to camera, or one agent presenting.
- Intent: sell or rent a property, present a project, a homestay or villa for booking, a plot of land.

## Questions to ask when the brief does not say

1. **The facts** the footage cannot give, exactly as the documents say: price (tỷ/triệu, rent per
   month or night), area and **whether it is thông thủy or tim tường**, bedrooms and bathrooms,
   direction, floor, legal status, address or area name. Never invent or round them.
2. For an off-plan project: is it **legally eligible to be sold** (đủ điều kiện kinh doanh)? If unsure,
   the video presents the place, not a sale offer, and says so.
3. Voice or music only? Show the agent's name/phone (only if asked)? A floor plan image to show?

## Structure (35–50 s; `playbook.py skeleton real-estate --duration 42`)

| Phase | Share | Purpose | Graphics |
|---|---|---|---|
| HOOK | 0–3 s | The single best shot (view, living room, pool), then the facts | `title` with location or price |
| ARRIVAL | 12% | Exterior or entrance: where it is, the approach; speed ramp through the door | `pin` |
| LIVING | 20% | The main space, light and volume, walk-through | `label` (room, m²) |
| KITCHEN | 12% | Kitchen and dining, one detail | `label`, `callout` |
| BEDROOM | 20% | Bedrooms, the master first | `label` |
| BATH | 8% | One clean bathroom frame | `label` |
| FEATURE | 18% | The selling point: balcony, view, pool, rooftop, amenities | `title` or `stat` ("5 phút tới…", labelled as an estimate) |
| SPECS | 4 s | A calm wide shot under the facts | `specs` + `price`; `image` for a floor plan |
| CTA | 3.5 s | Agent or brand, how to book a viewing | `lowerThird`, `title` |

Walk order follows a visitor: exterior → entry → living → kitchen → bedrooms → baths → outdoor. Move the
view or the pool earlier when it is the selling point [S: esoft, Property Finder]. One logical path, so
nobody wonders what is down a corridor [S: Property Finder]. A 15–30 s teaser is the same structure
with fewer rooms (set `--duration 25`; the playbook's floor is 25 s).

## Shots the footage needs

Exterior hero (golden hour if possible) and an entry push-in · each room as wide, medium and detail ·
kitchen macro · bathroom · the view, amenities, neighbourhood B-roll; drone where legal · constant-speed
gimbal walks in 4K60 (they are what speed ramps are made from) · 10 s of room tone per room · the
floor plan and a confirmed facts sheet [S: HomeJab, Property Finder]. Manual exposure reset per room
[S: HomeJab]. Shot-library kinds this playbook's camera knows: `EXTERIOR`, `ROOM`, `WALK`, `DETAIL`, `VIEW`.

## Editing

- **Cut on the music**: `suggest_cuts.py --music track.wav --end 42 --playbook real-estate` cuts on
  beats, bar starts first; at 95–125 bpm a scene of 2–4 beats lasts 1.9–2.5 s, cut on bars, not on
  every beat [C]. With a voiceover (variant), cut on its pauses and pass `--music` to nudge cuts onto beats.
- **Transitions** [C]: cuts on movement, a whip between rooms in the direction the camera travels, a
  slide as the camera passes a door frame, a blur dissolve into the facts; no gimmicky shaders.
- **Speed ramps** [C]: corridors, stairs, doorways at `ramp 1>2>1` (the fast middle carries the viewer
  to the next room and lands at normal speed as the room opens); needs a constant-speed gimbal take.
  The skeleton puts one on ARRIVAL and FEATURE; add or remove them by the footage.
- **Camera**: the footage already moves, so the virtual camera stays subtle (pans of 5–6%, pushes to
  ~1.12), and `plan_to_project.py --auto-camera --analysis analysis.json` holds still on clips measured
  as moving. Slow, eased motion reads as calm and premium [S: SVGator on kinetic type].

## Sound

Music carries it: warm, modern, steady 4/4, 95–125 bpm (luxury slower, rentals and homestays brighter)
[C]; licensed for commercial use on a business account. Room tone under cuts, a soft whoosh on whips
(the playbook mutes the shutter on the hook). Level the track with `process_audio.py music`, master the
render with `process_audio.py master`.

## Picture

Grade `bright-interior` (lifted shadows, clean whites, slightly warm, verticals straight), corrections
**per clip**: interiors mix daylight and warm lamps, so white balance and exposure are measured and
corrected clip by clip (`prepare_footage.py`). Converging verticals from a tilted phone are corrected
with `--level` / perspective only where the analysis or your eye says so (`references/image-processing.md`).
Theme `luxe` (ivory, champagne, charcoal).

## Graphics (Overlays rows)

```
| 1 | 0.1 | 2.9 | title | top | – | style=glass; lines=Căn 2PN view sông / Thảo Điền; accent=view sông |
| 2 | 3.1 | +2.5 | pin | top | – | title=Thảo Điền, TP Thủ Đức; sub=Cách Q1 ~15 phút (ước tính) |
| 3 | 6.2 | +2.2 | label | – | – | text=Phòng khách; sub=32 m² |
| 4 | 34.2 | 38.0 | specs | upper | – | title=Thông tin; items=area:72 m² thông thủy / bed:2 PN / bath:2 WC / compass:Đông Nam |
| 5 | 34.6 | 38.0 | price | lower | cta | value=5.2; decimals=1; unit= tỷ; label=Giá bán |
| 6 | 38.3 | 41.8 | lowerThird | lower | – | name=Tên môi giới; role=Đặt lịch xem nhà |
```

Write decimals with a point in the plan (`value=5.2; decimals=1`): it is shown as "5,2" (vi-VN), and
"5,2" in a cell would be read as a point x,y. A floor plan is `image`
(`src=images/floorplan.png; at=0.5,0.3; width=640`, the file in the render project's `public/images/`).

## Compliance [L]

- **Luật Kinh doanh bất động sản 2023** (29/2023/QH15, in force 01/08/2024): Điều 6 requires the
  business to publish full, truthful information (approvals, legal papers, the ownership certificate,
  mortgages) before selling; Điều 8 bans distorting information, not disclosing it, and doing business
  without meeting the conditions. Advertising itself falls under Luật Quảng cáo.
- Penalties: **NĐ 339/2026/NĐ-CP** (in force 26/08/2026, replaces NĐ 16/2022), fines up to 1 tỷ.
- The plan's checklist (printed by the skeleton): facts match the documents; legal status only as
  documented; no promised returns or price rises; renders and virtual staging labelled "hình minh hoạ";
  travel times labelled as estimates; broker identified; neighbours and other houses' numbers out of frame.
- TikTok does not restrict real-estate ads in Vietnam; its general rules (licensed advertiser,
  advertiser details on the landing page) apply [S: TikTok ads policy].

## Commands

```bash
python scripts/inspect_footage.py CLIPS --measure --json analysis.json
python scripts/new_remotion_project.py ~/renders/can-ho --playbook real-estate --proxies CLIPS --install
python scripts/process_audio.py music track.mp3 --out ~/renders/can-ho/public/audio/music.wav
python scripts/suggest_cuts.py --music ~/renders/can-ho/public/audio/music.wav --end 42 --playbook real-estate --json > cuts.json
python scripts/playbook.py skeleton real-estate --cuts cuts.json --title "Căn 2PN Thảo Điền" > edit-plan.md
python scripts/plan_scenes.py --library library.json --plan edit-plan.md --kinds "VIEW,ROOM,EXTERIOR,..." > scenes.md
python scripts/plan_to_project.py edit-plan.md --out ~/renders/can-ho/v1.json --music audio/music.wav \
    --auto-camera --analysis analysis.json --auto-sfx
```
