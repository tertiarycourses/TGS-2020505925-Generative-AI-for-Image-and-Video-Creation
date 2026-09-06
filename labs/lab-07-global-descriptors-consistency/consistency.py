#!/usr/bin/env python3
"""Lab 07 — global descriptors, combined consistency score, and logo template matching.

Writes out/consistency-scores.csv and out/logo-placement.csv.

Usage:
    python3 consistency.py --master reference/master/nq-master.png \
                           --assets reference/assets \
                           --template reference/nq-logo-template.png \
                           --thresholds data/consistency-thresholds.json \
                           --out out/consistency-scores.csv

Requires: opencv-python, numpy. No network access.
"""
import argparse
import csv
import glob
import json
import os

import cv2
import numpy as np


def read(path):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"cannot read {path}")
    return img


def hs_hist(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [30, 32], [0, 180, 0, 256])
    cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
    return hist


def mean_saturation(img):
    return float(cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[:, :, 1].mean())


def edge_density(img, lo=100, hi=200):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 1.0), lo, hi)
    return float(np.count_nonzero(edges)) / edges.size


def binary_subject(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, b = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return b


def log_hu(img_bin):
    """Readable log form of the seven Hu moments."""
    hu = cv2.HuMoments(cv2.moments(img_bin)).flatten()
    out = []
    for h in hu:
        out.append(0.0 if h == 0 else float(-np.sign(h) * np.log10(abs(h))))
    return [round(v, 4) for v in out]


def norm01(value, worst):
    """Map a distance-like value onto [0,1] where 0 is identical and 1 is `worst`."""
    return min(1.0, max(0.0, value / worst)) if worst else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", default="reference/master/nq-master.png")
    ap.add_argument("--assets", default="reference/assets")
    ap.add_argument("--template", default="reference/nq-logo-template.png")
    ap.add_argument("--thresholds", default="data/consistency-thresholds.json")
    ap.add_argument("--out", default="out/consistency-scores.csv")
    args = ap.parse_args()

    spec = json.load(open(args.thresholds))
    weights = spec["combined"]["weights"]
    reject_above = spec["combined"]["reject_above"]
    scales = spec["normalisation_worst"]
    expected_keys = {"hue_sat_histogram", "mean_saturation", "edge_density_ratio", "shape_match_I1"}
    if set(weights) != expected_keys or any(v < 0 for v in weights.values()) or not np.isclose(sum(weights.values()), 1.0):
        raise SystemExit("weights must cover all four descriptors, be nonnegative and sum to 1")
    if any(not np.isfinite(scales[k]) or scales[k] <= 0 for k in ("hist", "saturation", "edge_ratio", "shape")):
        raise SystemExit("normalisation_worst scales must be finite and positive")

    master = read(args.master)
    m_hist = hs_hist(master)
    m_sat = mean_saturation(master)
    m_edge = edge_density(master)
    if m_edge == 0:
        raise SystemExit("master has zero edge density; choose a valid reference before ratio scoring")
    m_bin = binary_subject(master)
    print("master log-Hu moments:", log_hu(m_bin))
    print(f"master mean saturation {m_sat:.2f}  edge density {m_edge:.5f}\n")

    paths = sorted(glob.glob(os.path.join(args.assets, "*.png")))
    if not paths:
        raise SystemExit(f"no assets found in {args.assets}")

    outdir = os.path.dirname(args.out) or "."
    os.makedirs(outdir, exist_ok=True)

    rows, logo_rows = [], []
    tpl = cv2.cvtColor(read(args.template), cv2.COLOR_BGR2GRAY)
    if float(tpl.std()) < 1e-6:
        raise SystemExit("logo template must have nonconstant intensity for CCOEFF_NORMED")
    box = spec["logo"]["required_box"]

    for path in paths:
        img = read(path)
        name = os.path.basename(path)

        d_hist = float(cv2.compareHist(m_hist, hs_hist(img), cv2.HISTCMP_BHATTACHARYYA))
        d_sat = abs(mean_saturation(img) - m_sat)
        r_edge = edge_density(img) / m_edge if m_edge else 1.0
        d_shape = float(cv2.matchShapes(m_bin, binary_subject(img),
                                        cv2.CONTOURS_MATCH_I1, 0.0))

        parts = {
            "hue_sat_histogram": norm01(d_hist, scales["hist"]),
            "mean_saturation": norm01(d_sat, scales["saturation"]),
            "edge_density_ratio": norm01(abs(r_edge - 1.0), scales["edge_ratio"]),
            "shape_match_I1": norm01(d_shape, scales["shape"]),
        }
        combined = sum(parts[k] * weights[k] for k in weights)
        verdict = "REJECT" if combined > reject_above else "ACCEPT"
        worst = max(parts, key=lambda k: parts[k] * weights[k])

        rows.append({
            "asset": name,
            "hist_bhattacharyya": round(d_hist, 4),
            "saturation_delta": round(d_sat, 2),
            "edge_density_ratio": round(r_edge, 3),
            "shape_match": round(d_shape, 4),
            "combined_score": round(combined, 4),
            "worst_descriptor": worst,
            "verdict": verdict,
        })

        # ---- logo template matching --------------------------------------
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if gray.shape[0] < tpl.shape[0] or gray.shape[1] < tpl.shape[1]:
            raise SystemExit(f"template larger than asset: {name}")
        res = cv2.matchTemplate(gray, tpl, cv2.TM_CCOEFF_NORMED)
        _, maxv, _, maxl = cv2.minMaxLoc(res)
        score_pass = maxv >= spec["logo"]["min_score"]
        place_pass = (box["x"][0] <= maxl[0] <= box["x"][1] and
                      box["y"][0] <= maxl[1] <= box["y"][1])
        logo_rows.append({
            "asset": name, "peak_score": round(float(maxv), 4),
            "peak_x": int(maxl[0]), "peak_y": int(maxl[1]),
            "score_pass": score_pass, "placement_pass": place_pass,
            "verdict": "ACCEPT" if (score_pass and place_pass) else "REJECT",
        })

    with open(args.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: -r["combined_score"]))

    logo_csv = os.path.join(outdir, "logo-placement.csv")
    with open(logo_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(logo_rows[0]))
        w.writeheader()
        w.writerows(logo_rows)

    print(f"{'asset':16} {'combined':>9} {'worst descriptor':>20}  verdict")
    for r in sorted(rows, key=lambda r: -r["combined_score"]):
        print(f"{r['asset']:16} {r['combined_score']:9.4f} "
              f"{r['worst_descriptor']:>20}  {r['verdict']}")
    rejects = [r['asset'] for r in rows if r['verdict'] == 'REJECT']
    print(f"\nREJECTED ({len(rejects)}): {', '.join(rejects) if rejects else '(none)'}")
    misplaced = [r['asset'] for r in logo_rows
                 if r['score_pass'] and not r['placement_pass']]
    print(f"Logo present but misplaced: {', '.join(misplaced) if misplaced else '(none)'}")
    print(f"\nWritten: {args.out}\nWritten: {logo_csv}")


if __name__ == "__main__":
    main()
