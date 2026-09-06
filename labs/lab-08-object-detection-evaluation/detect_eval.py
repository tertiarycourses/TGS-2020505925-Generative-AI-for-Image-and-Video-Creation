#!/usr/bin/env python3
"""Lab 08 — run two built-in OpenCV detectors and evaluate them properly.

Both detectors ship inside the base opencv-python wheel:
  * Viola-Jones Haar cascade  (cv2.data.haarcascades)
  * HOG + linear SVM people detector (cv2.HOGDescriptor_getDefaultPeopleDetector)

No weights are downloaded and no network access is used.

Usage:
    python3 detect_eval.py --frames reference/frames \
                           --truth data/ground-truth.json \
                           --config data/eval-config.json --out out

Requires: opencv-python, numpy.
"""
import argparse
import csv
import glob
import json
import os

import cv2
import numpy as np


def iou(a, b):
    """Intersection over union for two [x, y, w, h] boxes."""
    if len(a)!=4 or len(b)!=4 or min(a[2:])<=0 or min(b[2:])<=0:
        raise ValueError("boxes require positive width/height")
    ax2, ay2 = a[0] + a[2], a[1] + a[3]
    bx2, by2 = b[0] + b[2], b[1] + b[3]
    iw = max(0, min(ax2, bx2) - max(a[0], b[0]))
    ih = max(0, min(ay2, by2) - max(a[1], b[1]))
    inter = iw * ih
    union = a[2] * a[3] + b[2] * b[3] - inter
    return inter / union if union > 0 else 0.0


def match(preds, truths, thr):
    """Greedy matching, highest score first, each truth used at most once.

    Returns (tp, fp, fn).
    """
    if not 0 < thr <= 1:
        raise ValueError("IoU threshold must be in (0,1]")
    order = sorted(range(len(preds)), key=lambda i: -preds[i]["score"])
    used = set()
    tp = 0
    for i in order:
        best_j, best_iou = -1, 0.0
        for j, t in enumerate(truths):
            if j in used or preds[i]["class"] != t["class"]:
                continue
            v = iou(preds[i]["box"], t["box"])
            if v > best_iou:
                best_iou, best_j = v, j
        if best_j >= 0 and best_iou >= thr:
            used.add(best_j)
            tp += 1
    return tp, len(preds) - tp, len(truths) - tp


def prf(tp, fp, fn):
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return round(p, 4), round(r, 4), round(f, 4)


def run_cascade(gray, min_neighbors, scale_factor=1.05, min_size=(24, 24)):
    path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    cas = cv2.CascadeClassifier(path)
    if cas.empty():
        raise SystemExit(f"cascade failed to load from {path}")
    found, _, weights = cas.detectMultiScale3(gray, scaleFactor=scale_factor,
                                 minNeighbors=min_neighbors, minSize=min_size, outputRejectLevels=True)
    # levelWeights rank detections; they are not calibrated probabilities.
    return [{"box": [int(v) for v in b], "score": float(w), "class": "face"}
            for b,w in zip(found, np.ravel(weights))]


def run_hog(img, weight_threshold, hog, candidate_floor=0.0,
            shrink_w=0.15, shrink_h=0.05):
    """Apply the declared fixture-specific box adjustment; not a universal accuracy fix."""
    found, weights = hog.detectMultiScale(img, winStride=(8, 8),
                                          padding=(8, 8), scale=1.05,
                                          hitThreshold=candidate_floor)
    out = []
    for b, w in zip(found, np.ravel(weights) if len(found) else []):
        if float(w) < weight_threshold:
            continue
        x, y, bw, bh = (int(v) for v in b)
        pw, ph = int(shrink_w * bw), int(shrink_h * bh)
        out.append({"box": [x + pw, y + ph, bw - 2 * pw, bh - 2 * ph],
                    "score": float(w), "class": "person"})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", default="reference/frames")
    ap.add_argument("--truth", default="data/ground-truth.json")
    ap.add_argument("--config", default="data/eval-config.json")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()

    cfg = json.load(open(args.config))
    truth = json.load(open(args.truth))["frames"]
    paths = sorted(glob.glob(os.path.join(args.frames, "*.png")))
    if not paths:
        raise SystemExit(f"no frames found in {args.frames}")
    if set(truth) != {os.path.basename(p) for p in paths}:
        raise SystemExit("frame files and truth frame keys must match exactly; use empty lists for negative frames")
    if not cfg["iou_thresholds"] or not cfg["cascade"]["min_neighbors_sweep"] or not cfg["hog"]["weight_threshold_sweep"]:
        raise SystemExit("evaluation and parameter sweeps cannot be empty")
    os.makedirs(args.out, exist_ok=True)

    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    # Self-test of the IoU implementation, so a broken metric is caught immediately.
    check = iou([0, 0, 100, 100], [50, 0, 100, 100])
    assert abs(check - 1.0 / 3.0) < 1e-6, f"IoU self-test failed: {check}"
    print(f"IoU self-test passed: {check:.4f} (expected 0.3333)\n")

    detections = {}
    default_mn = cfg["cascade"]["default_min_neighbors"]
    default_wt = cfg["hog"]["default_weight_threshold"]
    candidate_floor = min([default_wt] + cfg["hog"]["weight_threshold_sweep"])

    for path in paths:
        name = os.path.basename(path)
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is None:
            raise SystemExit(f"cannot read {path}")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        detections[name] = {
            "face": run_cascade(gray, default_mn),
            "person": run_hog(img, default_wt, hog, candidate_floor),
        }

    with open(os.path.join(args.out, "detections.json"), "w") as fh:
        json.dump(detections, fh, indent=2)

    # ---- evaluation at each IoU threshold -------------------------------
    rows = []
    for cls, detector in (("face", "haar_cascade"), ("person", "hog_svm")):
        for thr in cfg["iou_thresholds"]:
            tp = fp = fn = 0
            for name in detections:
                preds = detections[name][cls]
                truths = [b for b in truth.get(name, []) if b["class"] == cls]
                a, b, c = match(preds, truths, thr)
                tp += a
                fp += b
                fn += c
            p, r, f = prf(tp, fp, fn)
            rows.append({"detector": detector, "class": cls, "iou_threshold": thr,
                         "TP": tp, "FP": fp, "FN": fn,
                         "precision": p, "recall": r, "f1": f})

    # ---- parameter sweeps for a real PR curve ---------------------------
    sweep_rows = []
    thr = cfg["sweep_iou_threshold"]
    for mn in cfg["cascade"]["min_neighbors_sweep"]:
        tp = fp = fn = 0
        for path in paths:
            name = os.path.basename(path)
            gray = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2GRAY)
            preds = run_cascade(gray, mn)
            truths = [b for b in truth.get(name, []) if b["class"] == "face"]
            a, b, c = match(preds, truths, thr)
            tp += a
            fp += b
            fn += c
        p, r, f = prf(tp, fp, fn)
        sweep_rows.append({"detector": "haar_cascade", "parameter": "minNeighbors",
                           "value": mn, "TP": tp, "FP": fp, "FN": fn,
                           "precision": p, "recall": r, "f1": f})

    for wt in cfg["hog"]["weight_threshold_sweep"]:
        tp = fp = fn = 0
        for path in paths:
            name = os.path.basename(path)
            img = cv2.imread(path)
            preds = run_hog(img, wt, hog, candidate_floor)
            truths = [b for b in truth.get(name, []) if b["class"] == "person"]
            a, b, c = match(preds, truths, thr)
            tp += a
            fp += b
            fn += c
        p, r, f = prf(tp, fp, fn)
        sweep_rows.append({"detector": "hog_svm", "parameter": "svm_weight",
                           "value": wt, "TP": tp, "FP": fp, "FN": fn,
                           "precision": p, "recall": r, "f1": f})

    eval_csv = os.path.join(args.out, "evaluation.csv")
    with open(eval_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    sweep_csv = os.path.join(args.out, "pr-sweep.csv")
    with open(sweep_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(sweep_rows[0]))
        w.writeheader()
        w.writerows(sweep_rows)

    # ---- overlay for visual evidence -------------------------------------
    first = os.path.basename(paths[0])
    vis = cv2.imread(paths[0])
    for b in truth.get(first, []):
        x, y, bw, bh = b["box"]
        cv2.rectangle(vis, (x, y), (x + bw, y + bh), (0, 200, 0), 2)
    for cls, colour in (("face", (255, 80, 0)), ("person", (0, 80, 255))):
        for d in detections[first][cls]:
            x, y, bw, bh = d["box"]
            cv2.rectangle(vis, (x, y), (x + bw, y + bh), colour, 2)
    cv2.putText(vis, "green=ground truth  blue=face  red=person", (8, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (20, 20, 20), 1, cv2.LINE_AA)
    cv2.imwrite(os.path.join(args.out, f"overlay_{first}"), vis)

    for r in rows:
        print(f"{r['detector']:14} {r['class']:7} IoU {r['iou_threshold']:<4} "
              f"TP={r['TP']:<3} FP={r['FP']:<3} FN={r['FN']:<3} "
              f"P={r['precision']:.3f} R={r['recall']:.3f} F1={r['f1']:.3f}")
    print(f"\nWritten: {eval_csv}\nWritten: {sweep_csv}")
    print(f"Operating-point rule from config: {cfg['operating_point_rule']}")


if __name__ == "__main__":
    main()
