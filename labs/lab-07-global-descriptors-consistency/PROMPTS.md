# Lab 07 — Prompt and Specification Pack

**Global Descriptors, Template Matching and Brand-Consistency Scoring**  
Generative AI for Image and Video Creation (TGS-2020505925) · Version v11.0 · 6 September 2026

This pack is the brand-consistency review gate itself: the descriptor specification, the creator feedback template, and the wording that keeps a numeric gate from being presented as an aesthetic judgement.

> **Currency note.** Model identifiers and API parameters quoted anywhere in this pack were verified against the official vendor documentation on 6 September 2026. Model IDs change; re-verify before relying on one. Identifiers known to be deprecated are marked as such rather than quietly removed, so you can recognise them in older material.

---

## Brand-consistency descriptor specification

```json
{
  "gate": "campaign_consistency",
  "reference": "reference/master/nq-master.png",
  "descriptors": [
    {"name": "hue_sat_histogram", "bins": [30, 32],
     "compare": "HISTCMP_BHATTACHARYYA", "good": "low", "max": 0.35,
     "catches": "recolour, palette drift"},
    {"name": "mean_saturation", "good": "close", "max_delta": 22,
     "catches": "desaturated or oversaturated treatment"},
    {"name": "edge_density_ratio", "good": "near 1",
     "range": [0.7, 1.4], "catches": "over-sharpening, over-smoothing"},
    {"name": "shape_match_I1", "good": "low", "max": 0.6,
     "catches": "silhouette or crop change"}
  ],
  "combined": {"weights": {"hue_sat_histogram": 0.4, "mean_saturation": 0.2,
                            "edge_density_ratio": 0.2, "shape_match_I1": 0.2},
               "reject_above": 0.45},
  "limits": "these descriptors do not assess copy, legal claims, or whether the asset is on-message. Numerical similarity is a proxy, not semantic brand approval."
}
```

## Creator feedback template (numeric, not aesthetic)

```text
Asset: <file>   Creator: <name>   Verdict: REJECT
Failing descriptor: <name>
  measured: <value>    threshold: <value>
  this means: <one supported sentence, e.g. histogram distance exceeds the fixture threshold; this alone does not localise a jacket colour or quantify a hue shift>
Passing descriptors: <list with values>
Action: <the single specific change that would bring it inside threshold>
Re-submit to: <queue>
```

Never send 'it feels off-brand'. Send the number, the threshold and the one change.

## Logo-placement gate

```json
{
  "gate": "logo_present_and_placed",
  "template": "reference/nq-logo-template.png",
  "method": "TM_CCOEFF_NORMED", "peak": "maxLoc",
  "min_score": 0.70,
  "required_box": {"x": [620, 880], "y": [20, 140]},
  "both_must_pass": ["score", "placement"],
  "known_limits": ["not scale invariant", "not rotation invariant",
                   "degrades under strong illumination change"],
  "escalation": "if score fails but the logo is visibly present, re-test with ORB matching before rejecting"
}
```

## Consistency prompt for a generative variant request

```text
Generate three variants of the approved master. Hold these constant and state them back to me before generating:
  - jacket shell hue and saturation (measured band, not a colour name);
  - subject silhouette and crop;
  - lighting direction and contrast;
  - logo position within the stated placement box.
Vary only: background setting and time of day.
Each variant will be scored against the master on hue-saturation histogram distance, mean saturation, edge density ratio and shape match, and rejected above a combined score of 0.45.
```

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W. Course material for TGS-2020505925, version v11.0.
