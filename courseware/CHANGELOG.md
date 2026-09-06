# Changelog — Generative AI for Image and Video Creation (TGS-2020505925)

Append-only. Newest release first. Historical entries are never edited or collapsed.

---

## v11.0 — 6 September 2026

**Release type:** Major rebuild for the registered title change. Predecessor: v10.0,
delivered as *Image and Video Processing with OpenCV*.

### Why

The course is registered and publicly listed as **WSQ – Generative AI for Image and Video
Creation** with five generative-AI delivery topics, while the approved Course Proposal
(CA-WSQ-2020-013290-v2) and Assessment Plan (TGS-2020505925 V1.0) carry six Learning
Units, ELO1–ELO6, K1–K13 and A1–A8 against TSC *Computer Vision Technology*
(ICT-DIT-4022-1.1). The v10.0 courseware still delivered the legacy OpenCV title and
included Raspberry Pi provisioning and a Darknet build. v11.0 aligns the delivered
material with the registered listing **without** altering any approved competency,
instrument, count, code mapping or timing.

### Material changes

**Structure and alignment**
- Content restructured onto the five published delivery topics, each mapped explicitly to
  its approved Learning Unit and ELO. Topic 04 consolidates LU4 and LU5 concept delivery;
  both units retain their full practical allocation (120 + 60 = 180 minutes).
- Programme hours reconciled against the approved proposal and asserted in the build:
  450 min classroom facilitation + 360 min practical + 150 min assessment = 960 min
  (16 hours). Administration, tea breaks and lunch are additional, non-instructional time
  and are shown separately on the Lesson Plan.
- The published course page states a 2-hour assessment. The registered Assessment Plan and
  Course Proposal both specify WA 60 min + PP 90 min = 2.5 hours, which is what the
  authenticated LMS record carries. The 2.5-hour figure is used throughout and the
  discrepancy is stated explicitly in the Lesson Plan.

**Slide deck**
- New 204-slide deck (previous: 182) in the current all-white Tertiary house design.
  No legacy master, layout, geometry or raster slide was carried over; the legacy deck was
  used as a content and coverage authority only.
- 18 **native, editable PowerPoint charts** (`pptx.chart` objects, not images). Every
  chart carries an explicit data-provenance band: MEASURED, MODELLED, PUBLISHED or
  ILLUSTRATIVE.
- Diagrams are built from real shapes and real PowerPoint connectors with arrowheads —
  no typed arrow glyphs.
- Zero slides classified as unanchored; every instructional slide carries code, a formula,
  a native chart, a named architecture or mechanism, an annotated interface, a sourced
  case or a measurement. See `qa/TECHNICAL-ANCHOR-INVENTORY.md`.
- No practice-exam slide. This is a skills-application course with no external
  certification exam, so the practice-exam rule does not apply.
- Course cover now carries the supplied AI-generated hero image with its provenance
  caption.

**Labs**
- Twelve new self-contained labs replace the legacy in-slide activity list. Each folder
  carries its own numbered steps, mock data, local reference media, prompt pack, expected
  outputs, evidence checklist and troubleshooting table, and completes with no paid
  service and no downloaded model.
- Every learner-facing Markdown file has a same-basename PDF counterpart in the same
  folder (33 Markdown / 33 PDF).
- All reference media is present locally. Nothing is downloaded during the class.
- Provenance is labelled on every asset: SIMULATED (deterministic OpenCV render),
  AI-GENERATED (copied unchanged with a `PROVENANCE.md`), REAL PRERECORDED (source URL,
  retrieval date and SHA-256), or ANIMATIC (labelled on every frame).

**Removed from v10.0**
- Raspberry Pi hardware overview, OS download, image burning, VNC and static-IP
  configuration (legacy slides 27–35) — not in K1–K13 or A1–A8, and the course is now
  delivered on learner laptops.
- The `opencv-python==4.4.0.46` plus libjasper/libqtgui4 install sequence (legacy slide
  37) — obsolete on current distributions.
- Darknet clone/build and the YOLOv4-on-Jetson-Nano run sequence (legacy slides 149–152) —
  requires a downloaded weights file and a build toolchain. Detection now uses the two
  machine-learning detectors that ship inside `opencv-python`, so it runs offline.
- Third-party demo links (Google Vision, IBM Watson, SegNet, Teachable Machine) — link rot
  and external-service dependency.
- Legacy LMS URL `ai-lms-tms.tertiaryinfo.tech`, replaced with
  `https://lms-tms.tertiaryinfotech.com/`.
- Legacy slide 7 carried a Day 2 lesson-plan line from an unrelated course
  ("Topic 5 Create User Defined Forms"). The v11.0 Lesson Plan is generated from the
  single source, so this class of error cannot recur.

**API and vendor currency — verified 6 September 2026**
- `cv2.TrackerCSRT_create` and `cv2.TrackerKCF_create` are **not** in the base
  `opencv-python` wheel (contrib-only). Labs use the built-in `cv2.TrackerMIL_create`.
- The `cv2.quality` SSIM module is also contrib-only. The course ships its own NumPy SSIM
  implementation rather than adding a dependency for one function.
- The `imagen-4.0-*` model family used in the reference ebook is documented as deprecated
  with shutdown on 17 August 2026. Current Gemini image model identifiers are taught
  instead, and the deprecated identifier is shown explicitly so learners recognise it in
  older material.
- `veo-3.0-generate-001` is documented as deprecated; the Veo 3.1 identifiers, durations,
  aspect ratios and resolutions are taught instead.
- The HOG default people detector returns a padded box; the conventional 15% width / 5%
  height correction is taught and measured (mean IoU 0.38 → 0.59 on the course dataset).

**Assessment — preserved exactly, content revised**
- Instruments, counts, ordering, code mapping and timings preserved from the registered
  papers: WA (SAQ) 13 questions covering K1–K13 in order, 60 minutes; PP 5 tasks with
  Task 1 → A1, Task 2 → A2 and A3, Task 3 → A4, Task 4 → A5 and A6, Task 5 → A7 and A8,
  90 minutes. All questions open-ended; zero multiple choice.
- Scenarios, question wording and model answers rewritten from this course's slides and
  labs. Answer keys cite the exact slides and labs.
- Two items were brought back onto their own criterion: Q12 now genuinely tests K12
  (vision communication protocols) while still covering the original edge-system question,
  and PP Task 1 now genuinely tests A1 (identifying the need) rather than a segmentation
  operation. Counts, order, codes, instrument types and timings are untouched.

**Documents**
- Lesson Plan and Learner Guide rebuilt with the WSQ cover page, a Document Version
  Control Record carrying both the v10.0 predecessor row and this release, a
  page-numbered Table of Contents, Arial 11pt body and a footer on every page.
- The Lesson Plan's slide references are generated from the built deck, so they cannot
  cite a slide that has moved.
- The Learner Guide carries the full numbered procedure for all twelve labs, and a
  Markdown mirror rendered from the same content stream so the two cannot diverge.
- A page-cited source register appears in the deck, the Lesson Plan and the Learner Guide.

### Affected artifacts

| Artifact | Path |
|---|---|
| Slide deck | `courseware/Generative AI for Image and Video Creation-v11.0.pptx` + `.pdf` |
| Lesson Plan | `courseware/LP-Generative AI for Image and Video Creation.docx` + `.pdf` |
| Learner Guide | `courseware/LG-Generative AI for Image and Video Creation.docx` + `.pdf` + `.md` |
| Labs | `labs/lab-01-…` through `labs/lab-12-…`, plus `labs/README.md` |
| Assessment (confidential, not published to GitHub) | `assessment/` — four DOCX |
| QA records | `qa/LOCAL-QA.md`, `qa/SOURCE-TO-OUTPUT-MAP.md`, `qa/TECHNICAL-ANCHOR-INVENTORY.md` |

### Publication note

Nothing in this release has been published. No GitHub push, no LMS/TMS update and no
Google Drive upload has been performed. The assessment folder is git-ignored and is
Drive-only when it is eventually distributed; answer keys are trainer-only and never go to
the LMS.

---

## v10.0 — legacy release (superseded)

Delivered as **Image and Video Processing with OpenCV** under the same course code
TGS-2020505925. 182 slides across six OpenCV topics: overview of computer vision, image
processing, feature extraction and description, machine-learning based computer vision,
video analytics, and edge computing based vision systems. Included Raspberry Pi
provisioning, OpenCV installation on Raspberry Pi OS, and a Darknet/YOLOv4 build and run
sequence. Retained in `reference/` as the content-coverage authority for the v11.0
revision; its visual design is **not** the design authority.
