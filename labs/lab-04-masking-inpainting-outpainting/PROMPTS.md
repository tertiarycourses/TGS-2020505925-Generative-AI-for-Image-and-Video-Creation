# Lab 04 — Prompt and Specification Pack

**Masking, Inpainting, Outpainting and Background Swap**  
Generative AI for Image and Video Creation (TGS-2020505925) · Version v11.0 · 6 September 2026

The generative edit prompts below pair one-for-one with the three masks you built. Each states the mask semantics explicitly, because an edit request without stated mask semantics is ambiguous and can be interpreted incorrectly.

> **Currency note.** Model identifiers and API parameters quoted anywhere in this pack were verified against the official vendor documentation on 6 September 2026. Model IDs change; re-verify before relying on one. Identifiers known to be deprecated are marked as such rather than quietly removed, so you can recognise them in older material.

---

## Job 1 — inpaint removal (mask-based)

```json
{
  "job": "remove-price-tag",
  "edit_mode": "inpaint_removal",
  "base_image": "reference/nq-jacket-square.png",
  "mask_image": "out/mask_tag.png",
  "mask_semantics": "white = editable, black = preserved",
  "mask_dilation_kernel": "5x5 ellipse, 2 iterations (approximately 4 px reach)",
  "prompt": "continue the jacket shell fabric and its weave across the masked region; match the existing seam direction, sheen and shadow falloff",
  "preserve": ["jacket silhouette", "collar", "backdrop", "all lighting"],
  "acceptance": {"metric": "outside_mask_mean_abs_diff",
                 "max": 0.5, "units": "intensity levels, 0-255"}
}
```

## Job 1b — the mask-free alternative, for comparison only

```json
{
  "job": "remove-price-tag-maskfree",
  "edit_mode": "default",
  "base_image": "reference/nq-jacket-square.png",
  "prompt": "remove the yellow price tag from the jacket; change nothing else",
  "note": "the model infers its own edit region. Faster to author, but the preserved region is inferred rather than guaranteed. Verify all preserved details before use in a commercial master."
}
```

## Job 2 — background swap

```json
{
  "job": "swap-background-harbour",
  "edit_mode": "background_swap",
  "base_image": "reference/nq-jacket-square.png",
  "mask_image": "out/mask_bg.png",
  "mask_semantics": "white = background (editable), black = subject (preserved)",
  "prompt": "a harbour boardwalk at first light: wet timber decking, mooring bollards mid-ground, rigging and low cloud beyond; match the existing warm key from camera left and keep the subject's cast shadow consistent with it",
  "preserve": ["subject pixels", "subject edge", "jacket colour"],
  "acceptance": {"metric": "subject_hsv_bhattacharyya_vs_source",
                 "max": 0.15}
}
```

## Job 3 — outpaint to approximately 16:9

```json
{
  "job": "outpaint-1x1-to-16x9",
  "edit_mode": "outpaint",
  "canvas": {"width": 1820, "height": 1024,
             "source_placed_at_x": 398, "source_size": 1024},
  "mask_image": "out/mask_outpaint.png",
  "mask_semantics": "white = new canvas (editable), black = original (preserved)",
  "prompt": "continue the harbour boardwalk left and right: the same decking planks running to the frame edges, further bollards, and the same low cloud horizon line held level",
  "preserve": ["the original 1024 central columns, bit-identical"],
  "acceptance": {"metric": "central_1024_columns_identical",
                 "expected": true}
}
```

## Review-gate wording to attach to any masked edit

```text
An edit is accepted only when ALL of the following hold:
  1. the stated acceptance metric is within threshold;
  2. the preserve list is verified, not asserted;
  3. the mask semantics recorded here match the semantics the API applied;
  4. the output provenance (model + prompt version, or SIMULATED) is recorded.
```

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W. Course material for TGS-2020505925, version v11.0.
