#!/usr/bin/env python3
"""Lab 05 — degrade, filter, and rank with PSNR and SSIM.

Builds a 3 (degradation) x 5 (filter) matrix plus a no-filter baseline row per
degradation, and writes out/enhancement-matrix.csv.

Usage:
    python3 enhance.py --clean reference/nq-hero-clean.png \
                       --degradations data/degradations.json \
                       --filters data/filter-bank.json \
                       --out out/enhancement-matrix.csv

Requires: opencv-python, numpy. No network access.
"""
import argparse
import csv
import json
import os
import time

import cv2
import numpy as np

from ssim import psnr, ssim


def degrade_gaussian(img, sigma, seed):
    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, sigma, img.shape)
    return np.clip(img.astype(np.float64) + noise, 0, 255).astype(np.uint8)


def degrade_salt_pepper(img, fraction, seed):
    rng = np.random.default_rng(seed)
    out = img.copy()
    h, w = img.shape[:2]
    n = int(fraction * h * w)
    if not 0 <= fraction <= 1:
        raise ValueError("fraction must be between 0 and 1")
    positions = rng.choice(h*w, n, replace=False)
    ys, xs = np.divmod(positions,w)
    half = n // 2
    out[ys[:half], xs[:half]] = 0
    out[ys[half:], xs[half:]] = 255
    return out


def degrade_defocus(img, sigma, seed=None):
    return cv2.GaussianBlur(img, (0, 0), sigma)


DEGRADERS = {
    "gaussian_noise": degrade_gaussian,
    "salt_pepper": degrade_salt_pepper,
    "defocus_blur": degrade_defocus,
}


def f_box(img, k=5):
    return cv2.blur(img, (k, k))


def f_gaussian(img, k=5):
    return cv2.GaussianBlur(img, (k, k), 0)


def f_median(img, k=5):
    return cv2.medianBlur(img, k)


def f_bilateral(img, d=9, sc=75, ss=75):
    return cv2.bilateralFilter(img, d, sc, ss)


def f_unsharp(img, sigma=3.0, amount=1.5):
    blurred = cv2.GaussianBlur(img, (0, 0), sigma)
    return cv2.addWeighted(img, amount, blurred, 1.0 - amount, 0)


FILTERS = {
    "box_5x5": f_box,
    "gaussian_5x5": f_gaussian,
    "median_5": f_median,
    "bilateral_9_75_75": f_bilateral,
    "unsharp_1.5": f_unsharp,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", default="reference/nq-hero-clean.png")
    ap.add_argument("--degradations", default="data/degradations.json")
    ap.add_argument("--filters", default="data/filter-bank.json")
    ap.add_argument("--out", default="out/enhancement-matrix.csv")
    args = ap.parse_args()

    clean = cv2.imread(args.clean, cv2.IMREAD_COLOR)
    if clean is None:
        raise SystemExit(f"cannot read {args.clean}")

    degs = json.load(open(args.degradations))["degradations"]
    fspec = json.load(open(args.filters))["filters"]
    wanted = [f["name"] for f in fspec]
    if len(degs)!=3 or len(fspec)!=5 or len(set(wanted))!=5:
        raise SystemExit("require three degradations and five distinct filters")
    filter_params = {f["name"]: f.get("params", {}) for f in fspec}

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    rows = []

    for d in degs:
        fn = DEGRADERS[d["kind"]]
        kwargs = dict(d.get("params", {}))
        if d["kind"] != "defocus_blur":
            kwargs["seed"] = d["seed"]
        damaged = fn(clean, **kwargs)
        cv2.imwrite(os.path.join(os.path.dirname(args.out) or ".",
                                 f"degraded_{d['name']}.png"), damaged)

        rows.append({"degradation": d["name"], "filter": "(baseline, no filter)",
                     "psnr_db": round(psnr(clean, damaged), 3),
                     "ssim": round(ssim(clean, damaged), 4), "ms": 0.0})

        for name in wanted:
            func = FILTERS[name]
            t0 = time.perf_counter()
            result = func(damaged, **filter_params[name])
            ms = (time.perf_counter() - t0) * 1000.0
            cv2.imwrite(os.path.join(os.path.dirname(args.out) or ".",
                                     f"fixed_{d['name']}_{name}.png"), result)
            rows.append({"degradation": d["name"], "filter": name,
                         "psnr_db": round(psnr(clean, result), 3),
                         "ssim": round(ssim(clean, result), 4),
                         "ms": round(ms, 2)})

    with open(args.out, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["degradation", "filter", "psnr_db", "ssim", "ms"])
        writer.writeheader()
        writer.writerows(rows)

    for d in degs:
        cells = [r for r in rows if r["degradation"] == d["name"] and "baseline" not in r["filter"]]
        best_ssim = max(cells, key=lambda r: r["ssim"])
        best_psnr = max(cells, key=lambda r: r["psnr_db"])
        base = next(r for r in rows if r["degradation"] == d["name"] and "baseline" in r["filter"])
        flag = "" if best_ssim["filter"] == best_psnr["filter"] else "   <-- METRICS DISAGREE"
        print(f"{d['name']:16} baseline SSIM {base['ssim']:.4f} | "
              f"best SSIM {best_ssim['filter']} ({best_ssim['ssim']:.4f}) | "
              f"best PSNR {best_psnr['filter']} ({best_psnr['psnr_db']:.2f} dB){flag}")

    print(f"\nWritten: {args.out}")


if __name__ == "__main__":
    main()
