# Lab 01 — Prompt and Specification Pack

**Vision-System Needs Analysis and Generative Pipeline Specification**  
Generative AI for Image and Video Creation (TGS-2020505925) · Version v11.0 · 6 September 2026

Lab 01 is an analysis lab, so the 'prompts' here are the structured briefing and review prompts you would put in front of a stakeholder or an assistant model. They are reusable templates — nothing here requires a paid service.

> **Currency note.** Model identifiers and API parameters quoted anywhere in this pack were verified against the official vendor documentation on 6 September 2026. Model IDs change; re-verify before relying on one. Identifiers known to be deprecated are marked as such rather than quietly removed, so you can recognise them in older material.

---

## Stakeholder needs-elicitation prompt

Use this verbatim in the discovery meeting. It forces the six criteria out of a vague request.

```text
You have asked for AI-generated imagery for <use case>.
Before specifying a pipeline, provide six evidence fields (numeric or categorical):
1. VOLUME     — how many assets of this exact type per month?
2. REPEAT     — is the framing, subject class and output format identical each time? Give an example of the most different two instances.
3. LATENCY    — what is the longest acceptable turnaround: overnight, minutes, or sub-second?
4. TOLERANCE  — who reviews the output before a customer sees it, and what happens if a wrong asset ships?
5. PRIVACY    — does any input or output contain an identifiable person or customer record? Which system holds it?
6. COST       — what does this cost today per month, in staff hours and in dollars?
Also provide estimated automated monthly cost, per-asset ceiling, maximum turnaround and privacy rule. Use a table: field | value | unit | evidence. Mark missing facts UNKNOWN; never infer them. Identify a responsible person.
```

## Pipeline specification template

```text
USE CASE: <id> — <name>
1. SENSE       source=<catalogue asset | store camera | text prompt> resolution=<WxH> rate=<per day>
2. REPRESENT   colour space=<BGR|RGB|HSV> working size=<WxH> store=<location>
3. ANALYSE     after candidate generation, measurement=<named metric> computed on=<what> reference=<what it is compared against>
4. DECIDE      provisional threshold=<number> pass action=<...> fail action=<...>
5. ACT         publish reviewed output or loop to generate; output=<artefact> formats=<aspect ratios> consumer=<team/system>
   stage type = ANALYTICAL | GENERATIVE
```

## Rejection rationale template

```text
<case id> REJECTED. <criterion> scored <n>/5: <the number that caused it>. Revisit when <the specific condition that would change that number>.
```

Example: `NQ-04 REJECTED. Repeatability scored 1/5: every store event has a different subject, framing and copy deck. Revisit when the events team adopts a fixed three-layout template.`

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W. Course material for TGS-2020505925, version v11.0.
