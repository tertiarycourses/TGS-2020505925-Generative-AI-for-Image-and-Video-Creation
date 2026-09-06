# Lab 11 — Prompt and Specification Pack

**Captions, Overlays, Safe Areas and Export Profiles**  
Generative AI for Image and Video Creation (TGS-2020505925) · Version v11.0 · 6 September 2026

Export is where a good asset gets ruined quietly. This pack is the delivery specification, the caption style rules and the acceptance checklist that make the constraints testable.

> **Currency note.** Model identifiers and API parameters quoted anywhere in this pack were verified against the official vendor documentation on 6 September 2026. Model IDs change; re-verify before relying on one. Identifiers known to be deprecated are marked as such rather than quietly removed, so you can recognise them in older material.

---

## Delivery ladder specification

```json
{
  "ladder": "NQ-HARBOUR-AW26",
  "source": {"width": 1920, "height": 1080, "fps": 25, "duration_s": 12},
  "profiles": [
    {"name": "16x9", "width": 1920, "height": 1080, "reframe": "none",
     "safe_inset": 0.05, "min_cap_height_px": 34, "max_bytes": 12000000},
    {"name": "1x1",  "width": 1080, "height": 1080, "reframe": "centre_crop",
     "safe_inset": 0.06, "min_cap_height_px": 30, "max_bytes": 9000000},
    {"name": "9x16", "width": 1080, "height": 1920, "reframe": "centre_crop",
     "safe_inset": 0.08, "min_cap_height_px": 36, "max_bytes": 12000000}
  ],
  "rule": "caption plate and logo must lie ENTIRELY inside the safe rectangle in every profile; verify, do not assume"
}
```

## Caption style rules

```text
1. Every caption sits on an opaque plate. Never bare text over picture.
2. Measured H-glyph height is at least the profile minimum AND at least 3% of frame height.
3. Plate-to-text luminance ratio at least 4:1, measured, not judged.
4. One line where possible; two maximum; never three.
5. A cue is on screen for at least 1.2 s regardless of how short the text is.
6. Cues never overlap. Verify programmatically before rendering.
7. Caption origin is computed from the safe rectangle, never a fixed offset.
```

## Reframing decision record

```text
PROFILE: 9x16
DECISION: centre crop
LOSES: 68.36% of the source width (the boardwalk on both sides)
REASON: the subject occupies the central third in every shot, and a letterbox would
        leave about 68.36% of a phone screen as bars. The lost boardwalk is context, not
        product.
ALTERNATIVE CONSIDERED: letterbox — rejected on screen-use grounds.
RE-SHOOT NOTE: shots 2 and 3 should be framed with a 9:16 protect area next time.
```

## Export acceptance checklist

```text
[ ] Three renditions exist at the specified dimensions.
[ ] Each rendition duration equals the source duration to within one frame.
[ ] Every caption cue verified inside the safe rectangle, per profile.
[ ] Logo verified inside the safe rectangle, per profile.
[ ] Achieved H-glyph height recorded in px and as % of frame height, per profile.
[ ] Plate-to-text luminance ratio measured and recorded.
[ ] File size and bit-rate recorded against the profile limit, PASS or FAIL stated.
[ ] Any size failure reported WITH the lever that would fix it — not hidden by a
    silent re-encode.
[ ] Provenance label inherited from the source and present on every derivative.
```

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W. Course material for TGS-2020505925, version v11.0.
