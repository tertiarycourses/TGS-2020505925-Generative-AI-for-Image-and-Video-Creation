#!/usr/bin/env python3
"""Lab 10 — background subtraction, three trackers, optical flow and continuity metrics.

Writes out/tracking.csv, out/continuity-report.json and one annotated overlay
video per tracker.

Only the base opencv-python wheel is required. Note that cv2.TrackerCSRT_create
and cv2.TrackerKCF_create are NOT in that wheel (they are contrib-only), which is
why cv2.TrackerMIL_create is used here.

Usage:
    python3 motion.py --video reference/nq-motion-clip.mp4 \
                      --truth reference/nq-motion-truth.json \
                      --config data/tracking-config.json --out out

Requires: opencv-python, numpy. No network access.
"""
import argparse
import csv
import json
import os

import cv2
import numpy as np

from ssim import ssim


def iou(a, b):
    ax2, ay2 = a[0] + a[2], a[1] + a[3]
    bx2, by2 = b[0] + b[2], b[1] + b[3]
    iw = max(0, min(ax2, bx2) - max(a[0], b[0]))
    ih = max(0, min(ay2, by2) - max(a[1], b[1]))
    inter = iw * ih
    union = a[2] * a[3] + b[2] * b[3] - inter
    return inter / union if union > 0 else 0.0


def read_frames(path):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise SystemExit(f"cannot open {path}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not np.isfinite(fps) or fps <= 0:
        cap.release()
        raise SystemExit("source FPS must be finite and positive; constant-FPS fixture required")
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    cap.release()
    if not frames:
        raise SystemExit(f"no decodable frames in {path}")
    return frames, fps


def hue_histogram(frame, window):
    x, y, w, h = window
    if w <= 0 or h <= 0 or x < 0 or y < 0 or x+w > frame.shape[1] or y+h > frame.shape[0]:
        raise SystemExit("initial_window must be a positive box inside the frame")
    roi = frame[y:y + h, x:x + w]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (0, 60, 32), (180, 255, 255))
    hist = cv2.calcHist([hsv], [0], mask, [180], [0, 180])
    if not np.any(hist):
        raise SystemExit("initial subject has no pixels above the saturation/value floors")
    cv2.normalize(hist, hist, 0, 255, cv2.NORM_MINMAX)
    return hist


def track_shift(frames, window, hist, camshift):
    term = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
    win = tuple(window)
    boxes = [list(window)]
    for frame in frames[1:]:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        bp = cv2.calcBackProject([hsv], [0], hist, [0, 180], 1)
        bp = cv2.bitwise_and(bp, cv2.inRange(hsv, (0,60,32), (179,255,255)))
        if win[2] <= 0 or win[3] <= 0:
            boxes.append([0,0,0,0])
            continue
        if camshift:
            _, win = cv2.CamShift(bp, win, term)
        else:
            _, win = cv2.meanShift(bp, win, term)
        boxes.append([int(v) for v in win])
    return boxes


def track_mil(frames, window):
    tracker = cv2.TrackerMIL_create()
    tracker.init(frames[0], tuple(int(v) for v in window))
    boxes = [[int(v) for v in window]]
    for frame in frames[1:]:
        ok, box = tracker.update(frame)
        boxes.append([int(v) for v in box] if ok else [0, 0, 0, 0])
    return boxes


def background_stats(frames, subtractor):
    counts = []
    for frame in frames:
        fg = subtractor.apply(frame)
        _, hard = cv2.threshold(fg, 200, 255, cv2.THRESH_BINARY)
        counts.append(int(np.count_nonzero(hard)))
    return counts


def overlay(frames, boxes, truth, path, fps):
    h, w = frames[0].shape[:2]
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    if not writer.isOpened():
        raise SystemExit(f"could not open writer for {path}")
    for i, frame in enumerate(frames):
        vis = frame.copy()
        if i < len(truth):
            x, y, bw, bh = truth[i]
            cv2.rectangle(vis, (x, y), (x + bw, y + bh), (0, 200, 0), 2)
        x, y, bw, bh = boxes[i]
        cv2.rectangle(vis, (x, y), (x + bw, y + bh), (0, 90, 255), 2)
        cv2.putText(vis, f"f{i:03d}  green=truth  orange=track", (8, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (20, 20, 20), 1, cv2.LINE_AA)
        writer.write(vis)
    writer.release()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", default="reference/nq-motion-clip.mp4")
    ap.add_argument("--truth", default="reference/nq-motion-truth.json")
    ap.add_argument("--config", default="data/tracking-config.json")
    ap.add_argument("--thresholds", default="data/continuity-thresholds.json")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()

    cfg = json.load(open(args.config))
    thr = json.load(open(args.thresholds))
    truth_data = json.load(open(args.truth))
    truth = truth_data["boxes"]
    frames, fps = read_frames(args.video)
    if len(frames) < 2 or len(truth) != len(frames):
        raise SystemExit("need at least two frames and one truth box per decoded frame")
    if any(len(b) != 4 or b[2] <= 0 or b[3] <= 0 for b in truth):
        raise SystemExit("truth boxes must have positive width and height")
    excluded = set(cfg.get("excluded_transition_frames", []))
    os.makedirs(args.out, exist_ok=True)
    print(f"{len(frames)} frames at {fps} fps ({len(frames)/fps:.2f}s)\n")

    # ---- background subtraction -----------------------------------------
    mog2 = background_stats(frames, cv2.createBackgroundSubtractorMOG2(
        history=200, varThreshold=16, detectShadows=True))
    knn = background_stats(frames, cv2.createBackgroundSubtractorKNN(
        history=200, dist2Threshold=400.0, detectShadows=True))
    print(f"MOG2 foreground px, frames 0-9 : {mog2[:10]}")
    print(f"KNN  foreground px, frames 0-9 : {knn[:10]}\n")

    # ---- three trackers --------------------------------------------------
    init = cfg["initial_window"]
    hist = hue_histogram(frames[0], init)
    tracks = {
        "meanshift": track_shift(frames, init, hist, camshift=False),
        "camshift": track_shift(frames, init, hist, camshift=True),
        "mil": track_mil(frames, init),
    }

    rows = []
    for name, boxes in tracks.items():
        for i, box in enumerate(boxes):
            t = truth[i] if i < len(truth) else [0, 0, 0, 0]
            rows.append({
                "frame": i, "tracker": name,
                "cx": box[0] + box[2] / 2.0, "cy": box[1] + box[3] / 2.0,
                "w": box[2], "h": box[3],
                "iou_vs_truth": round(iou(box, t), 4),
            })
    track_csv = os.path.join(args.out, "tracking.csv")
    with open(track_csv, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    # ---- dense optical flow ---------------------------------------------
    mags = []
    prev = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
    for frame in frames[1:]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(prev, gray, None,
                                            0.5, 3, 15, 3, 5, 1.2, 0)
        mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        mags.append(float(mag.mean()))
        prev = gray
    med = float(np.median(mags))
    spikes = [i + 1 for i, m in enumerate(mags) if m > max(4.0 * med, 0.1)]

    # ---- inter-frame SSIM -----------------------------------------------
    step = 1  # Every adjacent pair; sparse sampling can miss the known jump.
    ssims = [ssim(cv2.cvtColor(frames[i - 1], cv2.COLOR_BGR2GRAY),
                  cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY))
             for i in range(step, len(frames), step)]

    # ---- continuity metrics per tracker ---------------------------------
    truth_ratio = (truth[-1][2] * truth[-1][3]) / (truth[0][2] * truth[0][3])
    report = {
        "frames": len(frames), "fps": fps,
        "optical_flow_median_magnitude": round(med, 4),
        "discontinuity_frames": spikes,
        "interframe_ssim_mean": round(float(np.mean(ssims)), 4),
        "interframe_ssim_min": round(float(np.min(ssims)), 4),
        "interframe_ssim_sampling": f"every {step} frames",
        "truth_area_ratio_first_to_last": round(truth_ratio, 3),
        "trackers": {},
        "excluded_transition_frames": sorted(excluded),
        "flow_spike_rule": "whole-clip mean-flow median x4, with 0.1 px noise floor; candidate flag only",
        "flow_magnitudes_px_per_frame": mags,
        "background_foreground_counts": {"mog2": mog2, "knn": knn},
    }

    for name, boxes in tracks.items():
        cents = np.array([[b[0] + b[2] / 2.0, b[1] + b[3] / 2.0] for b in boxes])
        steps = np.linalg.norm(np.diff(cents, axis=0), axis=1)
        valid = [b[2] > 0 and b[3] > 0 and iou(b, truth[i]) >= 0.1 for i,b in enumerate(boxes)]
        keep = np.array([i for i in range(len(steps)) if (i + 1) not in excluded and valid[i] and valid[i+1]], dtype=int)
        jitter = float(steps[keep].std()) if len(keep) else None

        a0 = max(1, boxes[0][2] * boxes[0][3])
        a1 = boxes[-1][2] * boxes[-1][3]
        ratio = a1 / a0
        # RELATIVE drift normalises error by the true growth ratio; when the
        # truth ratio is itself large. |measured/truth - 1| answers the question
        # actually being asked - "by what fraction did the tracker mis-report the
        # subject's growth?"
        drift = abs(ratio / truth_ratio - 1.0) if truth_ratio else 0.0
        mean_iou = float(np.mean([r["iou_vs_truth"] for r in rows
                                  if r["tracker"] == name]))

        report["trackers"][name] = {
            "centroid_jitter_px": round(jitter, 3) if jitter is not None else None,
            "jitter_verdict": "PASS" if jitter is not None and all(valid) and jitter <= thr["centroid_jitter_px"]["max"] else "FAIL",
            "area_ratio_first_to_last": round(ratio, 3),
            "scale_drift": round(drift, 3),
            "drift_verdict": "PASS" if all(valid) and drift <= thr["scale_drift"]["max"] else "FAIL",
            "mean_iou_vs_truth": round(mean_iou, 4),
            "invalid_tracking_frames": [i for i,v in enumerate(valid) if not v],
            "centroid_steps_px": steps.tolist(),
        }
        overlay(frames, boxes, truth,
                os.path.join(args.out, f"track_{name}.mp4"), fps)

    report["interframe_ssim_verdict"] = (
        "PASS" if report["interframe_ssim_mean"] >= thr["mean_interframe_ssim"]["min"]
        else "FAIL")

    out_json = os.path.join(args.out, "continuity-report.json")
    with open(out_json, "w") as fh:
        json.dump(report, fh, indent=2, allow_nan=False)

    print(f"truth area ratio first->last : {truth_ratio:.3f}")
    for name, v in report["trackers"].items():
        print(f"{name:10} jitter {str(v['centroid_jitter_px']):>6} px [{v['jitter_verdict']}]  "
              f"area ratio {v['area_ratio_first_to_last']:5.3f} "
              f"drift {v['scale_drift']:5.3f} [{v['drift_verdict']}]  "
              f"mean IoU {v['mean_iou_vs_truth']:.3f}")
    print(f"\ndiscontinuity frames (flow > 4x median): {spikes}")
    print(f"inter-frame SSIM mean {report['interframe_ssim_mean']} "
          f"[{report['interframe_ssim_verdict']}]")
    print(f"\nWritten: {track_csv}\nWritten: {out_json}")


if __name__ == "__main__":
    main()
