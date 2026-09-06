# Lab 06 — Prompt and Specification Pack

**Local Features: Colour Segmentation, Canny Edges and Corner Keypoints**  
Generative AI for Image and Video Creation (TGS-2020505925) · Version v11.0 · 6 September 2026

Feature extraction is where a QC gate stops being an opinion. This pack holds the gate specification and the wording that turns each feature measurement into a pass/fail rule a reviewer can apply without you in the room.

> **Currency note.** Model identifiers and API parameters quoted anywhere in this pack were verified against the official vendor documentation on 6 September 2026. Model IDs change; re-verify before relying on one. Identifiers known to be deprecated are marked as such rather than quietly removed, so you can recognise them in older material.

---

## Brand-colour QC gate

```json
{
  "gate": "brand_colour_present",
  "colour_space": "HSV (OpenCV 8-bit: H 0-179, S 0-255, V 0-255)",
  "band": {"lo": [100, 90, 60], "hi": [115, 255, 255]},
  "coverage_pct": {"min": 6.0, "max": 28.0},
  "centroid_quadrant": "upper_left",
  "rationale": "HSV is used because hue survives the exposure variation seen in this synthetic V-scaling test provided the V floor is still passed; validate on real deliveries.",
  "on_fail": "reject and return to the creator with the measured coverage"
}
```

## Silhouette-crispness gate

```json
{
  "gate": "silhouette_crisp",
  "operator": "Canny",
  "thresholds": {"low": 100, "high": 200, "ratio": "1:2"},
  "measure": "edge pixel density over the full frame after 5x5 Gaussian smoothing (sigma=1)",
  "min_density": 0.012,
  "note": "illustrative bounds only; calibrate with labelled assets at the same resolution. Density cannot uniquely diagnose blur or sharpening",
  "max_density": 0.075
}
```

## Master-match gate (is this really a variant of the approved asset?)

```json
{
  "gate": "matches_approved_master",
  "detector": "ORB", "nfeatures": 500,
  "descriptor_bytes": 32,
  "matcher": "BFMatcher(NORM_HAMMING, crossCheck=true)",
  "filter": "distance <= 0.75 * median(distance); heuristic, not Lowe ratio test",
  "min_filtered_matches": 10,
  "robustness_to_validate": ["rotation", "moderate scale"],
  "not_guaranteed_for": ["heavy crop", "style transfer", "recolour"]
}
```

The last two keys are the honest part: state what the gate cannot detect, or someone will assume it detects everything.

## Detector selection note for the team wiki

```text
Harris        rotation-covariant in theory, fixed-window scale-sensitive; response map
Shi-Tomasi    structure-tensor minimum eigenvalue + minimum spacing; point set
FAST          efficient; benchmark speed on your workload; detector only, no descriptor, cannot match alone
ORB           rotation and moderate-scale robustness, 32-byte binary descriptor
SIFT          scale/rotation robustness, 128-float descriptor; quality is task-dependent,
              16x the storage of ORB per keypoint
SURF          NOT in the standard opencv-python wheel (non-free); do not specify it
```

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W. Course material for TGS-2020505925, version v11.0.
