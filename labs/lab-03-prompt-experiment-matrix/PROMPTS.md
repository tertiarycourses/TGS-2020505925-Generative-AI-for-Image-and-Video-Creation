# Lab 03 — Prompt and Specification Pack

**Prompt Experiment Matrix for Controlled Image Generation**  
Generative AI for Image and Video Creation (TGS-2020505925) · Version v11.0 · 6 September 2026

This is the reusable prompt pack for the experiment. Cells A to D are written so that several factor groups may change per step; this is a progressive-specification comparison. Model IDs and parameters below were verified against the official Gemini API documentation on 6 September 2026; the imagen-4.0-* IDs that appear in older tutorials are deprecated and are not used here.

> **Currency note.** Model identifiers and API parameters quoted anywhere in this pack were verified against the official vendor documentation on 6 September 2026. Model IDs change; re-verify before relying on one. Identifiers known to be deprecated are marked as such rather than quietly removed, so you can recognise them in older material.

---

## Cell A — subject only (under-specified baseline)

```text
A person wearing the Harbour Line jacket.
```

Everything else — setting, time of day, framing, lens, lighting and register — is left to the sampler. This is the condition the marketing team is complaining about.

## Cell B — subject named + context named

```text
A person wearing the Harbour Line jacket, standing on a harbour boardwalk at first light, with mooring bollards and rigging behind them.
```

## Cell C — subject LOCKED + context named + style named

```text
Subject: the Harbour Line jacket, slate-blue shell with a single chest seam and a stand collar, worn open over a plain cream tee by an adult model facing three-quarters to camera.
Context: harbour boardwalk at first light, mooring bollards and rigging behind.
Style: documentary product photography, restrained colour, no lens flare.
```

## Cell D — all four factors LOCKED, as structured JSON

```json
{
  "prompt_version": "v3",
  "brief_reference": "NQ-HARBOUR-LINE-AW26",
  "subject": "the Harbour Line jacket: slate-blue shell, single chest seam, stand collar, worn open over a plain cream tee by an adult model, three-quarters to camera, hands at sides",
  "context": "harbour boardwalk at first light; mooring bollards and rigging in the mid-ground; wet timber underfoot",
  "style": "documentary product photography, restrained colour palette, natural contrast",
  "technical": {"lens": "35mm", "depth_of_field": "shallow",
                "lighting": "low-angle warm key from camera left, soft fill",
                "aspect_ratio": "4:5", "image_size": "2K"},
  "negative_constraints": ["no text or logos rendered in the image",
                            "no lens flare", "no additional people",
                            "no colour cast on the jacket shell"]
}
```

One key per factor is the point: to test a tighter framing you change `lens` alone and the other three input fields stay unchanged; the generated appearance is not guaranteed unchanged.

## Optional API call — current documented pattern (verified 6 Sep 2026)

Only run this if you have your own free-tier key. It is NOT required to complete the lab.

Before using this optional route, install a current google-genai package online, set GEMINI_API_KEY privately in your environment, and prepare one JSON prompt per bundle before scoring. Access/quotas are account-dependent. Run once for each of four variants per bundle, changing prompt path and output name. No seed control is assumed.

```python
from google import genai
from pathlib import Path
import base64, json

Path('out/gen').mkdir(parents=True, exist_ok=True)
client = genai.Client()
spec = json.load(open('out/prompt-D.json'))

interaction = client.interactions.create(
    model="gemini-3.1-flash-image",   # current; imagen-4.0-* is deprecated
    input=json.dumps(spec),
    response_format={"type": "image", "aspect_ratio": "4:5", "image_size": "2K", "mime_type": "image/png"},
)

if not interaction.output_image: raise RuntimeError('No image returned; record refusal and use offline route')
open('out/gen/cellD_01.png', 'wb').write(
    base64.b64decode(interaction.output_image.data))
```

Documented aspect ratios include 1:1, 3:2, 2:3, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9 and 21:9; output sizes are 1K/2K/4K depending on the model. All generated images carry a SynthID watermark — record that in your provenance note.

## Governance note to attach to any generated asset

```text
asset_id:        <file name>
generated_by:    <model id> | SIMULATED CLASSROOM ASSET
prompt_version:  v3  (out/prompt-v3.json, sha256 <hash>)
brief_reference: NQ-HARBOUR-LINE-AW26
watermark:       provider documents SynthID; not independently detected | n/a (simulated)
reviewed_by:     <name>   review_date: <date>
```

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W. Course material for TGS-2020505925, version v11.0.
