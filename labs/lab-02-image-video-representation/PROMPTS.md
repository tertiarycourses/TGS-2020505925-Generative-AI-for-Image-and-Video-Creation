# Lab 02 — Prompt and Specification Pack

**Image and Video Data Representation**  
Generative AI for Image and Video Creation (TGS-2020505925) · Version v11.0 · 6 September 2026

This lab is measurement, not generation, so the prompt pack holds the structured specification prompts you use to state a media contract to a supplier, a model or a downstream team. Nothing here needs a paid service.

> **Currency note.** Model identifiers and API parameters quoted anywhere in this pack were verified against the official vendor documentation on 6 September 2026. Model IDs change; re-verify before relying on one. Identifiers known to be deprecated are marked as such rather than quietly removed, so you can recognise them in older material.

---

## Media contract prompt (put this in the brief, not in a chat window)

```json
{
  "asset_class": "product_flatlay",
  "still":  {"width": 1280, "height": 720, "channels": 3,
             "dtype": "uint8", "channel_order": "BGR_on_read",
             "colour_space_of_record": "sRGB"},
  "clip":   {"width": 640, "height": 360, "fps": 25,
             "duration_s": 6, "container": "mp4", "codec": "mp4v"},
  "budget": {"uncompressed_Bps": 17280000,
             "max_encoded_Bps": 400000},
  "acceptance": ["shape and dtype verified on read",
                  "decoded frame count equals declared frame count exactly for this fixed supplied asset",
                  "hue of brand patch within 5 of reference"]
}
```

## Aspect-ratio request template

State the delivery ladder as pixel dimensions, never as a ratio name alone — 9:16 is ambiguous between 720x1280 and 1080x1920.

```text
Deliver each asset in three sizes:
  feed     1080 x 1080   (1:1)
  story     1080 x 1920   (9:16)
  hero      1920 x 1080   (16:9)
Crop rule: subject centroid must stay inside the central 80% safe area in all three.
```

## Verification prompt for a supplied asset

```text
For the attached file, report exactly these fields and nothing else:
  shape (H, W, C), dtype, channel order as read,
  fps, decodable frame count, duration in seconds,
  encoded bytes on disk, uncompressed bytes per second,
  compression ratio.
If any field cannot be determined, write UNKNOWN — do not estimate.
```

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W. Course material for TGS-2020505925, version v11.0.
