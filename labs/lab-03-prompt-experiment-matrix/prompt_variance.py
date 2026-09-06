#!/usr/bin/env python3
"""Lab 03 — score within-cell variance of a prompt experiment.

For each experiment cell (files in one flat directory named cell<X>_<NN>.png) this
reports four numbers:

  hist_distance_mean  mean pairwise Bhattacharyya distance between the HSV
                      histograms of the central 60% subject crop  (subject drift)
  centroid_std_px     standard deviation of the thresholded-bright-pixel centroid            (composition drift)
  edge_density_std    standard deviation of the Canny edge density           (style drift)
  saturation_std      standard deviation of mean HSV saturation              (style drift)

Usage:
    python3 prompt_variance.py --variants reference/variants \
                               --out out/variance-report.csv

Requires: opencv-python, numpy. No network access.
"""
import argparse
import collections
import csv
import glob
import itertools
import os
import re

import cv2
import numpy as np

CELL_RE = re.compile(r"(cell[A-Z])_(\d+)\.png$")


def subject_mask(img):
    """Isolate the subject BEFORE measuring anything.

    Measuring the whole frame is the classic mistake: a backdrop gradient and a
    ground texture dominate both the histogram and the centroid, so the numbers
    end up describing the background rather than the product. Here the subject is
    the largest strongly saturated region, which is what a product occupying a
    muted scene looks like. Check the mask before you trust the number.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1]
    _, mask = cv2.threshold(sat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    if n > 1:
        biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        mask = np.where(labels == biggest, 255, 0).astype(np.uint8)
    return mask


def hsv_hist(img, mask):
    """Smoothed, normalised 2-D hue/saturation histogram of the SUBJECT ONLY.

    The smoothing matters. A flat-coloured product puts almost all of its mass in
    one or two bins, and a bin-wise distance between two single-bin spikes is ~1
    no matter how close the two hues actually are - so an unsmoothed histogram
    reports "completely different" for a 3-degree hue shift and for a 60-degree
    one alike. A small Gaussian over the bins restores the ordering, which is
    what you want when you are measuring HOW FAR the colour drifted.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], mask, [30, 32], [0, 180, 0, 256])
    hist = cv2.GaussianBlur(hist, (0, 0), 2.0)
    cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
    return hist


def centroid(mask, shape):
    """Centroid of the subject mask, in pixels."""
    moments = cv2.moments(mask)
    if moments["m00"] == 0:
        return shape[1] / 2.0, shape[0] / 2.0
    return moments["m10"] / moments["m00"], moments["m01"] / moments["m00"]


def edge_density(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    return float(np.count_nonzero(edges)) / edges.size


def mean_saturation_subject(img, mask):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    sel = hsv[:, :, 1][mask > 0]
    return float(sel.mean()) if sel.size else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", default="reference/variants")
    ap.add_argument("--out", default="out/variance-report.csv")
    args = ap.parse_args()

    cells = collections.defaultdict(list)
    for path in sorted(glob.glob(os.path.join(args.variants, "*.png"))):
        match = CELL_RE.search(os.path.basename(path))
        if match:
            cells[match.group(1)].append(path)
    if set(cells) != {"cellA", "cellB", "cellC", "cellD"}:
        raise SystemExit("require exactly cells A, B, C and D in a flat directory")
    shapes = set()
    for cell, paths in cells.items():
        if len(paths) != 4 or len({int(CELL_RE.search(os.path.basename(p)).group(2)) for p in paths}) != 4:
            raise SystemExit(f"{cell}: require exactly four unique variant IDs")
        for p in paths:
            im = cv2.imread(p)
            if im is None:
                raise SystemExit(f"cannot read {p}")
            shapes.add(im.shape)
    if len(shapes) != 1:
        raise SystemExit("all variants require the same dimensions for pixel comparisons")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    fields = ["cell", "n_variants", "hist_distance_mean",
              "centroid_std_px", "edge_density_std", "saturation_std"]

    with open(args.out, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for cell in sorted(cells):
            paths = sorted(cells[cell])
            if len(paths) != 4:
                raise SystemExit(f"{cell}: need 4 variants per cell, found {len(paths)}")
            imgs = []
            for p in paths:
                im = cv2.imread(p, cv2.IMREAD_COLOR)
                if im is None:
                    raise SystemExit(f"cannot read {p}")
                imgs.append(im)

            masks = [subject_mask(i) for i in imgs]
            hists = [hsv_hist(i, m) for i, m in zip(imgs, masks)]
            dists = [cv2.compareHist(a, b, cv2.HISTCMP_BHATTACHARYYA)
                     for a, b in itertools.combinations(hists, 2)]

            cents = np.array([centroid(m, i.shape) for i, m in zip(imgs, masks)])
            cent_std = float(np.sqrt(cents[:, 0].std() ** 2 + cents[:, 1].std() ** 2))

            row = {
                "cell": cell,
                "n_variants": len(imgs),
                "hist_distance_mean": round(float(np.mean(dists)), 4),
                "centroid_std_px": round(cent_std, 2),
                "edge_density_std": round(float(np.std([edge_density(i) for i in imgs])), 5),
                "saturation_std": round(float(np.std([mean_saturation_subject(i, m) for i, m in zip(imgs, masks)])), 3),
            }
            writer.writerow(row)
            print("  ".join(f"{k}={row[k]}" for k in fields))

    print(f"\nWritten: {args.out}")
    print("Report the observed trend; simulated ordering is designed and real-model results may differ.")


if __name__ == "__main__":
    main()
