# Lab 10 — Prompt and Specification Pack

**Motion, Tracking and Temporal Continuity Measurement**  
Generative AI for Image and Video Creation (TGS-2020505925) · Version v11.0 · 6 September 2026

Motion work produces the acceptance evidence for a delivered clip. This pack is the continuity acceptance gate and the review wording that keeps 'it feels jittery' out of a defect report.

> **Currency note.** Model identifiers and API parameters quoted anywhere in this pack were verified against the official vendor documentation on 6 September 2026. Model IDs change; re-verify before relying on one. Identifiers known to be deprecated are marked as such rather than quietly removed, so you can recognise them in older material.

---

## Temporal continuity acceptance gate

```json
{
  "gate": "clip_continuity_accept",
  "applies_to": "any delivered clip, generated or captured",
  "metrics": [
    {"name": "centroid_jitter_px", "definition": "std dev of frame-to-frame subject centroid step, excluding declared cuts", "max": 3.5},
    {"name": "scale_drift", "definition": "|tracker area ratio / expected area ratio - 1| over the clip", "max": 0.50},
    {"name": "mean_interframe_ssim", "definition": "mean SSIM between consecutive frames", "min": 0.82},
    {"name": "discontinuity_count", "definition": "frames where mean flow magnitude exceeds max(4x whole-clip median, 0.1 px); review candidates", "max_undeclared": 0}
  ],
  "note": "a declared cut is not a defect; an undeclared one is",
  "on_fail": "return with the failing metric, its value and the frame index"
}
```

## Defect report wording (replace 'feels jittery')

```text
CLIP: <file>   DURATION: <s>   FPS: <n>
DEFECT: centroid jitter 6.4 px (limit 3.5) measured on the subject track,
        concentrated between frames 88 and 112.
DEFECT: undeclared discontinuity at frame 100 — mean optical-flow magnitude
        11.2 px against a whole-clip median of 1.8 px.
NOT A DEFECT: scale change from frame 0 to 199 (expected, per shot list).
EVIDENCE: out/tracking.csv, out/continuity-report.json, out/track_camshift.mp4
```

## Tracker selection note

```text
mean shift    fixed window size; use only when the subject's apparent size is
              constant. Cheapest of the three.
CAMShift      recomputes window size and orientation from the back-projection each
              iteration; use when the subject approaches or recedes.
TrackerMIL    learns an appearance model online; benchmark partial occlusion robustness,
              slower, and built into the base opencv-python wheel.
CSRT / KCF    alternative trackers; benchmark quality. They are in opencv-contrib-python, NOT the base wheel.
              Specify the dependency explicitly if you require them.
```

## Continuity brief for a generated sequence

```text
For each generated shot, deliver alongside the clip:
  1. the subject track (per-frame centre and box) as CSV;
  2. centroid jitter, scale drift and mean inter-frame SSIM;
  3. a list of every frame index where a cut or transition is INTENDED.
Any discontinuity not on that list is a defect.
Do not smooth the track before reporting it — report the measured series.
```

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W. Course material for TGS-2020505925, version v11.0.
