#!/usr/bin/env python3
"""Lab 04 — build masks, run classical inpainting, and audit what changed.

Produces the three masks, both inpaint variants, and out/mask-audit.csv proving
the unmasked region was preserved.

Usage:
    python3 mask_edit.py --image reference/nq-jacket-square.png \
                         --backdrop reference/nq-backdrop-harbour.png \
                         --jobs data/edit-jobs.json --out out

Requires: opencv-python, numpy. No network access.
"""
import argparse
import csv
import json
import os

import cv2
import numpy as np

TAG_HSV_LO = (20, 120, 120)      # yellow price tag
TAG_HSV_HI = (35, 255, 255)


def read(path):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"cannot read {path}")
    return img


def tag_mask(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, TAG_HSV_LO, TAG_HSV_HI)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)
    return cv2.dilate(mask, k, iterations=2)


def background_mask(img):
    """Foreground = largest saturated component; background = its complement."""
    sat = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[:, :, 1]
    _, fg = cv2.threshold(sat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(fg, 8)
    if n > 1:
        biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        fg = np.where(labels == biggest, 255, 0).astype(np.uint8)
    if n <= 1:
        raise SystemExit("no foreground component; inspect subject segmentation")
    contours, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    fg = np.zeros_like(fg)
    cv2.drawContours(fg, contours, -1, 255, cv2.FILLED)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, k)
    return cv2.bitwise_not(fg), fg


def outpaint_canvas(img, out_w=1820):
    h, w = img.shape[:2]
    if out_w <= w:
        raise ValueError("outpaint width must exceed source width")
    canvas = np.zeros((h, out_w, 3), np.uint8)
    x0 = (out_w - w) // 2
    canvas[:, x0:x0 + w] = img
    mask = np.full((h, out_w), 255, np.uint8)
    mask[:, x0:x0 + w] = 0
    return canvas, mask, x0


def mean_abs_diff(a, b, region):
    """Mean absolute difference over the pixels where `region` is non-zero, in 0-255 intensity levels."""
    if not np.any(region):
        raise ValueError("metric region is empty")
    diff = cv2.absdiff(a, b).astype(np.float64).mean(axis=2)
    return float(diff[region > 0].mean())


def hsv_bhattacharyya(a, b, region):
    if not np.any(region):
        raise ValueError("subject mask is empty")
    def hist(img):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h = cv2.calcHist([hsv], [0, 1], region, [30, 32], [0, 180, 0, 256])
        cv2.normalize(h, h, 0, 1, cv2.NORM_MINMAX)
        return h
    return float(cv2.compareHist(hist(a), hist(b), cv2.HISTCMP_BHATTACHARYYA))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", default="reference/nq-jacket-square.png")
    ap.add_argument("--backdrop", default="reference/nq-backdrop-harbour.png")
    ap.add_argument("--jobs", default="data/edit-jobs.json")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    img = read(args.image)
    if img.shape != (1024,1024,3):
        raise SystemExit("fixed lab geometry requires 1024x1024 BGR source")
    jobs = json.load(open(args.jobs))["jobs"]
    thresholds = {j["job"]: j["acceptance"] for j in jobs}
    rows = []

    # ---- job 1: remove the price tag -------------------------------------
    m_tag = tag_mask(img)
    if not np.any(m_tag) or np.all(m_tag):
        raise SystemExit("empty/full tag mask; inspect input and hue threshold")
    cv2.imwrite(os.path.join(args.out, "mask_tag.png"), m_tag)
    telea = cv2.inpaint(img, m_tag, 3, cv2.INPAINT_TELEA)
    ns = cv2.inpaint(img, m_tag, 3, cv2.INPAINT_NS)
    cv2.imwrite(os.path.join(args.out, "inpaint_telea.png"), telea)
    cv2.imwrite(os.path.join(args.out, "inpaint_ns.png"), ns)

    inside = mean_abs_diff(img, telea, m_tag)
    outside = mean_abs_diff(img, telea, cv2.bitwise_not(m_tag))
    limit = thresholds["remove-price-tag"]["max"]
    rows.append({
        "job": "remove-price-tag", "method": "INPAINT_TELEA",
        "mask_coverage_pct": round(100.0 * float((m_tag > 0).mean()), 3),
        "inside_mask_mad_255": round(inside, 4),
        "outside_mask_mad_255": round(outside, 6),
        "metric_value": round(outside, 6), "metric_name": "outside_MAD_255",
        "threshold": limit,
        "verdict": "PASS" if outside < limit and inside > 1.0 else "FAIL",
    })

    # ---- job 2: background swap -----------------------------------------
    m_bg, m_fg = background_mask(img)
    cv2.imwrite(os.path.join(args.out, "mask_bg.png"), m_bg)
    backdrop = cv2.resize(read(args.backdrop), (img.shape[1], img.shape[0]))
    swapped = np.where(m_bg[:, :, None] > 0, backdrop, img)
    cv2.imwrite(os.path.join(args.out, "bgswap_composite.png"), swapped)

    dist = hsv_bhattacharyya(img, swapped, m_fg)
    limit = thresholds["swap-background-harbour"]["max"]
    rows.append({
        "job": "swap-background-harbour", "method": "mask composite",
        "mask_coverage_pct": round(100.0 * float((m_bg > 0).mean()), 3),
        "inside_mask_mad_255": round(mean_abs_diff(img, swapped, m_bg), 4),
        "outside_mask_mad_255": round(mean_abs_diff(img, swapped, m_fg), 6),
        "metric_value": round(dist, 6), "metric_name": "subject_HS_distance",
        "threshold": limit,
        "verdict": "PASS" if dist <= limit else "FAIL",
    })
    print(f"subject HSV Bhattacharyya distance after swap: {dist:.4f} (limit {limit})")

    # ---- job 3: outpaint canvas -----------------------------------------
    canvas, m_out, x0 = outpaint_canvas(img)
    cv2.imwrite(os.path.join(args.out, "outpaint_canvas.png"), canvas)
    cv2.imwrite(os.path.join(args.out, "mask_outpaint.png"), m_out)
    white = int((m_out > 0).sum())
    expected_white = (canvas.shape[1] - img.shape[1]) * img.shape[0]
    identical = bool(np.array_equal(canvas[:, x0:x0 + img.shape[1]], img))
    rows.append({
        "job": "outpaint-1x1-to-16x9", "method": "canvas + mask",
        "mask_coverage_pct": round(100.0 * float((m_out > 0).mean()), 3),
        "inside_mask_mad_255": "n/a (empty canvas)",
        "outside_mask_mad_255": 0.0 if identical else "non-zero",
        "metric_value": identical, "metric_name": "central_columns_identical",
        "threshold": "central columns identical",
        "verdict": "PASS" if identical and white == expected_white else "FAIL",
    })
    print(f"outpaint white pixels: {white} (expected {expected_white}), "
          f"central columns identical: {identical}")

    out_csv = os.path.join(args.out, "mask-audit.csv")
    with open(out_csv, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    for r in rows:
        print(f"{r['job']:28} {r['verdict']}")
    print(f"\nWritten: {out_csv}")


if __name__ == "__main__":
    main()
