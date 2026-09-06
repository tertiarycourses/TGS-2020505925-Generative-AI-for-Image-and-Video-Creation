# Lab 09 — Prompt and Specification Pack

**Storyboard to Video Prompt Pack and Deterministic Animatic**  
Generative AI for Image and Video Creation (TGS-2020505925) · Version v11.0 · 6 September 2026

This is the deliverable prompt pack. Parameters were verified against the official Veo documentation on 6 September 2026. The continuity block is written once and copied byte-for-byte into every shot, then verified visually; input consistency alone cannot ensure output consistency.

> **Currency note.** Model identifiers and API parameters quoted anywhere in this pack were verified against the official vendor documentation on 6 September 2026. Model IDs change; re-verify before relying on one. Identifiers known to be deprecated are marked as such rather than quietly removed, so you can recognise them in older material.

---

## Pack header — documented parameters

```json
{
  "pack_version": "v1",
  "brief_reference": "NQ-HARBOUR-FILM-AW26",
  "model": "veo-3.1-generate-preview",
  "model_alternatives": ["veo-3.1-fast-generate-preview",
                          "veo-3.1-lite-generate-preview"],
  "deprecated_do_not_use": ["veo-3.0-generate-001"],
  "durationSeconds": 8,
  "aspectRatio": "16:9",
  "resolution": "1080p",
  "native_audio": true,
  "continuity_mechanism": "image-to-video from a fixed reference frame, or, as a separate supported mode, up to three reference images to guide the product",
  "verified": "official documentation, 6 September 2026"
}
```

## The continuity block — written ONCE, pasted identically into all three shots

```json
"continuity": {
  "product": "the Harbour Line jacket: slate-blue shell, single chest seam, stand collar, matte finish, no visible branding",
  "wardrobe": "jacket worn open over a plain cream tee, dark trousers, brown boots",
  "model": "one adult, mid-thirties, short dark hair, no jewellery",
  "time_of_day": "first light, sun low on the horizon",
  "weather": "clear with low sea haze, no rain",
  "lighting": "warm key from camera left at a low angle, soft ambient fill, no practical lights in frame",
  "palette": "slate blue, weathered timber brown, cool grey water, warm highlight",
  "lens": "35mm, shallow depth of field"
}
```

## Shot 1 — full prompt

```json
{
  "shot": 1, "seconds": 8,
  "purpose": "establish the place and the hour",
  "subject": "the model walking away from camera along a harbour boardwalk",
  "action": "steady walk, three paces, then a half-turn to look out over the water",
  "camera": {"framing": "wide", "move": "slow dolly forward, following",
             "height": "chest height"},
  "location": "timber boardwalk, mooring bollards mid-ground, masts beyond",
  "continuity": "<<< paste the continuity block verbatim >>>",
  "audio": {
    "0-1s": "harbour ambience: distant halyards, water against pilings",
    "1-2s": "ambience continues; footfall on timber begins",
    "2-3s": "footfall, one gull call far off",
    "3-4s": "ambience; low sustained string enters underneath",
    "4-5s": "ambience and string; footfall slows",
    "5-6s": "footfall stops; ambience opens out",
    "6-7s": "ambience; string holds",
    "7-8s": "ambience settles, string resolves"
  },
  "negative": ["no rendered text or logos in frame", "no additional people",
               "no lens flare", "no change to the jacket shell colour",
               "no camera shake"]
}
```

## Shot 2 and shot 3 — what changes and what must not

```text
CHANGES between shots:  purpose, subject, action, camera framing and move,
                        location detail, audio track.
MUST NOT CHANGE:        every key inside the continuity block, and the negative list.

Shot 2 (8s)  purpose: show the product working
             subject: mid shot, the model fastening the collar against the wind
             camera : mid, static, slight rack focus from water to collar
Shot 3 (8s)  purpose: land the feeling
             subject: close on the shoulder seam, then the model's eyeline to horizon
             camera : close, slow push in
```

## Animatic provenance label (use verbatim)

```text
out/animatic.mp4 is a DETERMINISTIC ANIMATIC rendered from storyboard frames with OpenCV. It is not generative-model output and must not be presented as such.
Purpose: verify shot timing and beat coverage before any generation spend.
Rendered: <date>   Source frames: reference/board/ (SIMULATED storyboard art)
```

## Shot-review prompt for the director

```text
Watch the animatic once at speed, then answer only these:
  1. Which beat from the brief is NOT covered by any of the three shots?
  2. Which shot is too long for what it does? By how many seconds?
  3. Which continuity field are you least confident will hold in shot 3?
  4. What is the one change that most improves the film?
Do not comment on colour or grade — the animatic has neither.
```

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W. Course material for TGS-2020505925, version v11.0.
