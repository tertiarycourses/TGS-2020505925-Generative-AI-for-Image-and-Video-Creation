# Lab 05 — Prompt and Specification Pack

**Filtering, Enhancement and Restoration Measured with PSNR and SSIM**  
Generative AI for Image and Video Creation (TGS-2020505925) · Version v11.0 · 6 September 2026

Enhancement is measurement work, so this pack holds the acceptance-gate wording and the prompt you would use to specify a generative restoration — including the honesty clause that stops a restored asset being passed off as an original capture.

> **Currency note.** Model identifiers and API parameters quoted anywhere in this pack were verified against the official vendor documentation on 6 September 2026. Model IDs change; re-verify before relying on one. Identifiers known to be deprecated are marked as such rather than quietly removed, so you can recognise them in older material.

---

## Enhancement acceptance gate (drop into the asset pipeline)

```json
{
  "gate": "enhancement_accept",
  "reference": "the pre-degradation master, not the degraded input",
  "metrics": [
    {"name": "PSNR", "min_db": 30.0, "role": "catches gross error"},
    {"name": "SSIM", "min": 0.90, "role": "catches lost structure"}
  ],
  "rule": "example thresholds only; both must pass; disagreement routes to human review",
  "on_fail": "route to human review, do not auto-publish"
}
```

## Generative restoration request

```text
Restore the attached frame. Constraints:
  - remove sensor noise and recover fine texture in the fabric weave;
  - do NOT invent detail that is not implied by the surrounding pixels;
  - preserve the subject silhouette, colour and all lighting direction;
  - preserve the original aspect ratio and resolution.
Return the restored frame plus a statement of what was changed.
Provenance: the output is a RESTORED asset and must be labelled as such — it is not an original capture.
```

## Super-resolution request with an honest acceptance clause

```text
Upscale the attached 800x600 frame to 1600x1200.
Acceptance:
  - PSNR and SSIM are computed against a true 1600x1200 capture where one exists;
  - where no true capture exists, the output is reviewed by a human and labelled
    UPSCALED — no numeric fidelity claim may be made against a reference that does
    not exist.
```

That second clause matters: super-resolution invents plausible detail. Reporting a fidelity score against the upscaled input rather than a real high-resolution capture is a meaningless number.

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W. Course material for TGS-2020505925, version v11.0.
