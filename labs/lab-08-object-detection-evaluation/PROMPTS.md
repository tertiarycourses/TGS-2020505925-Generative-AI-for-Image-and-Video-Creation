# Lab 08 — Prompt and Specification Pack

**Object Detection and Quantitative Evaluation**  
Generative AI for Image and Video Creation (TGS-2020505925) · Version v11.0 · 6 September 2026

Detection work produces numbers that get quoted out of context. This pack is the evaluation-report template and the wording that keeps a headline accuracy honest.

> **Currency note.** Model identifiers and API parameters quoted anywhere in this pack were verified against the official vendor documentation on 6 September 2026. Model IDs change; re-verify before relying on one. Identifiers known to be deprecated are marked as such rather than quietly removed, so you can recognise them in older material.

---

## Detector evaluation report template

```text
DETECTOR:        <name and exact parameters>
DATASET:         <name, n frames, n ground-truth boxes per class>
DISTRIBUTION:    <real capture | synthetic | curated benchmark>
IoU THRESHOLD:   <value>       MATCHING: greedy, one truth per prediction
RESULTS:         TP=<n> FP=<n> FN=<n>
                 precision=<TP/(TP+FP)>  recall=<TP/(TP+FN)>  F1=<2PR/(P+R)>
OPERATING POINT: <parameters>  chosen by <rule>
NOT MEASURED:    <classes, conditions or scales absent from this dataset>
```

## Honest-accuracy wording (use this whenever a single number is quoted)

```text
<metric> = <value> at IoU <t> on <dataset>, <n> boxes, <distribution type>.
This number does not transfer to <named different condition> and has not been measured there.
```

Published figures illustrate why the qualifier matters: AI-generated-image classifiers report 99%+ test accuracy on curated benchmarks, while deepfake-detection backbones report validation accuracies in the mid-to-high 70s on harder, shifted data. Same metric name, different problem, non-comparable numbers.

## Ground-truth labelling instruction

```text
Label every instance of <class> that is:
  - at least <n> pixels in the smaller dimension;
  - less than <p>% occluded;
  - fully or partially inside the frame (clip the box to the frame).
Box convention: [x, y, w, h] in pixels, origin top-left, integer values.
Ambiguous instances go in a separate 'uncertain' list and are EXCLUDED from both
the recall denominator and the false-positive count — do not silently drop them.
```

## Review-queue operating point rule

```json
{
  "application": "human review queue",
  "rule": "maximise recall subject to precision >= 0.60",
  "rationale": "a false positive costs one reviewer glance; a false negative never reaches a human at all",
  "contrast": "an auto-publish pipeline inverts this: maximise precision subject to recall >= 0.40, because the cost asymmetry is reversed"
}
```

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W. Course material for TGS-2020505925, version v11.0.
