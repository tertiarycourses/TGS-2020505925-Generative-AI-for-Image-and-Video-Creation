# Hands-On Labs — Generative AI for Image and Video Creation

**WSQ Course Code:** TGS-2020505925 · **Version v11.0** · 6 September 2026  
**Conducted by:** Tertiary Infotech Academy Pte Ltd (UEN 201200696W)

Twelve labs across the five delivery topics. Every folder is independently usable: it carries its own steps, its own mock data, its own local media and its own prompt pack, and needs no network access once the Python dependencies are installed.

| Lab | Title | Topic | Outcome | A | K | In-class |
|---:|---|---|---|---|---|---|
| 01 | [Vision-System Needs Analysis and Generative Pipeline Specification](lab-01-vision-needs-analysis/README.md) | 01 | ELO1 | A1 | K1, K2 | within LU1 facilitation |
| 02 | [Image and Video Data Representation](lab-02-image-video-representation/README.md) | 02 | ELO2 | A2 | K3 | 15 min |
| 03 | [Prompt Experiment Matrix for Controlled Image Generation](lab-03-prompt-experiment-matrix/README.md) | 02 | ELO2 | A2 | K3, K4 | 15 min |
| 04 | [Masking, Inpainting, Outpainting and Background Swap](lab-04-masking-inpainting-outpainting/README.md) | 02 | ELO2 | A2 | K3, K4 | 15 min |
| 05 | [Filtering, Enhancement and Restoration Measured with PSNR and SSIM](lab-05-filtering-enhancement-metrics/README.md) | 02 | ELO2 | A2 | K4 | 15 min |
| 06 | [Local Features: Colour Segmentation, Canny Edges and Corner Keypoints](lab-06-local-features-edges-keypoints/README.md) | 03 | ELO3 | A4 | K5, K6 | 30 min |
| 07 | [Global Descriptors, Template Matching and Brand-Consistency Scoring](lab-07-global-descriptors-consistency/README.md) | 03 | ELO3 | A3, A4 | K7 | 30 min |
| 08 | [Object Detection and Quantitative Evaluation](lab-08-object-detection-evaluation/README.md) | 04 | ELO4 | A5 | K8, K9 | 60 min |
| 09 | [Storyboard to Video Prompt Pack and Deterministic Animatic](lab-09-storyboard-video-prompting/README.md) | 04 | ELO5 | A6 | K10 | 30 min |
| 10 | [Motion, Tracking and Temporal Continuity Measurement](lab-10-motion-tracking-continuity/README.md) | 04 | ELO5 | A6 | K10 | 60 min |
| 11 | [Captions, Overlays, Safe Areas and Export Profiles](lab-11-captions-overlays-export/README.md) | 04 | ELO5 | A6 | K10 | 30 min |
| 12 | [Cloud-Edge Architecture Design and Measured Trade-offs](lab-12-cloud-edge-architecture-tradeoffs/README.md) | 05 | ELO6 | A7, A8 | K11, K12, K13 | 60 min |

**Total scheduled practical time: 360 minutes (6 hours)** — matching the 360-minute practical allocation in the approved course proposal.

## Coverage

| Code | Statement | Labs |
|---|---|---|
| A1 | Identify the needs of vision systems technology in industrial applications | 01 |
| A2 | Apply the principles of processing, filtering and analysis methods for video data | 02, 03, 04, 05 |
| A3 | Analyse global feature descriptions | 07 |
| A4 | Design and implement feature extraction and representation methods | 06, 07 |
| A5 | Design and apply machine-learning based methods for object detection, object tracking and activity recognition | 08 |
| A6 | Design and apply video analytics algorithms for high-level video analytics tasks | 09, 10, 11 |
| A7 | Design the architecture of applied vision systems | 12 |
| A8 | Design, develop and evaluate edge-based and cloud-based systems | 12 |
| K1 | Vision system concepts | 01 |
| K2 | Business applications of vision systems | 01 |
| K3 | Methods to represent image and video data | 02, 03, 04 |
| K4 | Image and video processing, filtering and transformation methods | 03, 04, 05 |
| K5 | Feature extraction and representation techniques | 06 |
| K6 | Local feature descriptions, edge, colour, texture and motion | 06 |
| K7 | Global feature descriptions, statistical and geometrical methods | 07 |
| K8 | Deep learning concepts | 08 |
| K9 | Object segmentation, detection and recognition | 08 |
| K10 | Activity tracking, generative models, scene understanding and event discovery | 09, 10, 11 |
| K11 | Vision system architecture | 12 |
| K12 | Vision communication protocols | 12 |
| K13 | Real-world design constraints and solution options | 12 |

## Environment

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install "opencv-python>=4.10" numpy
```

No lab requires a paid service. Where a generative model can optionally be used, the lab supplies a local reference set so the deliverable can be completed offline, and asks you to record which path you took.

## Provenance rules that apply to every lab

1. A **SIMULATED** asset is a deterministic OpenCV rendering. It is never described as a photograph and never as generative-model output.
2. An **AI-generated** reference is copied unchanged and travels with a `PROVENANCE.md` recording the tool, date and prompt.
3. A **real prerecorded** sequence records its source URL, retrieval date and SHA-256.
4. A deterministic rendered animatic is labelled ANIMATIC on every frame and is never submitted as a generated film.
5. Anything you generate yourself is recorded with the model ID, the prompt version and the watermark expectation.

---

© 2026 Tertiary Infotech Academy Pte Ltd. UEN: 201200696W.
