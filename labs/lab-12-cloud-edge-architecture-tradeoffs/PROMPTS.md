# Lab 12 — Prompt and Specification Pack

**Cloud-Edge Architecture Design and Measured Trade-offs**  
Generative AI for Image and Video Creation (TGS-2020505925) · Version v11.0 · 6 September 2026

This pack is the architecture decision record and the review prompts that keep a cloud-versus-edge argument evidence-based. Every figure it produces carries its own provenance: MEASURED, MODELLED or ILLUSTRATIVE.

> **Currency note.** Model identifiers and API parameters quoted anywhere in this pack were verified against the official vendor documentation on 6 September 2026. Model IDs change; re-verify before relying on one. Identifiers known to be deprecated are marked as such rather than quietly removed, so you can recognise them in older material.

---

## Architecture decision record (ADR) template

```text
ADR-<n>: split point for the NorthQuay generative visual pipeline
STATUS: proposed | accepted | superseded

CONTEXT
  41 stores, <uplink> Mbit/s per store, camera feed classified <class>.
  Latency budget: <ms> for shelf alerts; <s> for asset generation.

CONSTRAINT GATES (applied first, not weighted)
  privacy: <which splits are eliminated and by which rule>
  uplink : <which splits are arithmetically infeasible>

MEASURED
  per-stage latency (median / p95 ms) on <CPU>, OpenCV <version>, <n> frames
  end-to-end median <ms> against a budget of <ms>

MODELLED
  generation latency proportional to S (image) and S x F (video); S=<n>, F=<n>
  INT8 parameter memory = 8/32 = 0.25 x FP32
  low-rank adapter trainable params r(d+m) = <n> against d*m = <n>

ILLUSTRATIVE
  monthly transferred data <GB> at <rate>/GB = <cost>  (classroom unit rates, not a quotation)
  energy per sample = overhead x energy-per-FLOP x FLOPs-per-sample

DECISION
  Split <X>. Runner-up split <Y>. Decided by: <the single number>.

CONSEQUENCES
  <what becomes easy, what becomes hard, what must be built>

RESIDUAL RISK
  1. <risk> -> closed by <action>
  2. ...
```

## Protocol selection table

```text
LINK                        PAYLOAD CLASS   LATENCY CLASS  PROTOCOL   REASON
camera -> edge node         live video      real-time      RTSP       standard camera
                                                                      transport, low
                                                                      setup cost
camera -> browser preview   live video      interactive    WebRTC     sub-second, NAT
                                                                      traversal built in
edge -> cloud telemetry     small events    seconds        MQTT       pub/sub, tiny
                                                                      header; configure retries for
                                                                      a poor link
constrained sensor -> edge  tiny events     seconds        CoAP       UDP-based, for
                                                                      very low-power
                                                                      devices
app -> model endpoint       request/reply   seconds        HTTPS/REST request/reply; caching
                                                                      depends on endpoint;
                                                                      verify support
service -> service          request/reply   sub-second     gRPC       binary, streaming,
                                                                      typed contracts
render -> asset store       large blobs     batch          HTTPS      object storage,
                                                                      resumable upload
```

Every row must state a payload class and a latency class. A protocol chosen without both is a preference, not a decision.

## Split-point comparison prompt for the review meeting

```text
For each of the four split points, give me exactly these six numbers:
  1. bytes per second per camera at the split;
  2. Mbit/s per store, and Gbit/s across 41 stores;
  3. feasible on the stated uplink? yes/no;
  4. measured end-to-end latency of everything left on the edge side;
  5. what personal data crosses the split, if any;
  6. illustrative monthly transferred data cost.
Then tell me which single number eliminates each rejected option.
Do not present a preference before presenting the six numbers.
```

## Evidence-provenance rule (put this at the top of every architecture deck)

```text
Every figure in this document is labelled:
  MEASURED     — timed or counted on stated hardware, with n and the percentile.
  MODELLED     — derived from a documented relationship, with the relationship shown.
  ILLUSTRATIVE — built on assumed unit rates; not a quotation and not a forecast.
An unlabelled figure is a defect and will be sent back.
```

## Edge-fit checklist

```text
[ ] Weights quantised to 8-bit where the accuracy loss is measured, not assumed
    (parameter memory scales by b/32, so 8-bit is 0.25x FP32).
[ ] Sensitive activations kept at higher precision for numerical stability.
[ ] Task specialisation via low-rank adapters: r(d+m) trainable parameters instead
    of d*m, so the base weights are not duplicated per task.
[ ] Sampler steps reduced by distillation, with the quality delta measured, not
    assumed.
[ ] Latent-space modelling used at high output resolution to cut memory traffic.
[ ] Structured pruning considered where the kernels support it.
[ ] Every one of the above reports a before/after quality number, not just a speed-up.
```

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W. Course material for TGS-2020505925, version v11.0.
