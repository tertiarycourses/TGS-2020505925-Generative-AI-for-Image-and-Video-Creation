#!/usr/bin/env python3
"""Lab 06 — local feature extraction: colour, edge and corner.

Writes out/features-report.json covering HSV brand segmentation (with an
synthetic exposure-robustness test against a raw-channel threshold), a Canny threshold
sweep, five keypoint detectors, a Harris rotation/scale response-count comparison, and an
ORB match against the rotated variant.

Usage:
    python3 features.py --image reference/nq-asset-master.png \
                        --variant reference/nq-asset-variant.png \
                        --brand data/brand-colour.json \
                        --out out/features-report.json

Requires: opencv-python, numpy. No network access.
"""
import argparse
import json
import os

import cv2
import numpy as np


def read(path):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"cannot read {path}")
    return img


def coverage(mask):
    return round(100.0 * float((mask > 0).mean()), 3)


def quadrant(mask):
    m = cv2.moments(mask)
    if m["m00"] == 0:
        return "none"
    cx, cy = m["m10"] / m["m00"], m["m01"] / m["m00"]
    h, w = mask.shape[:2]
    return ("upper" if cy < h / 2 else "lower") + "_" + ("left" if cx < w / 2 else "right")


def edge_density(gray, lo, hi):
    edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 1.0), lo, hi)
    return round(float(np.count_nonzero(edges)) / edges.size, 5)


def harris_count(gray):
    dst = cv2.cornerHarris(np.float32(gray), 2, 3, 0.04)
    dst = cv2.dilate(dst, None)
    return int((dst > 0.01 * dst.max()).sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", default="reference/nq-asset-master.png")
    ap.add_argument("--variant", default="reference/nq-asset-variant.png")
    ap.add_argument("--brand", default="data/brand-colour.json")
    ap.add_argument("--out", default="out/features-report.json")
    args = ap.parse_args()

    img = read(args.image)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    spec = json.load(open(args.brand))
    lo, hi = tuple(spec["lo"]), tuple(spec["hi"])

    report = {"image": args.image}

    # ---- colour ---------------------------------------------------------
    mask = cv2.inRange(hsv, lo, hi)
    report["brand_coverage_pct"] = coverage(mask)
    report["brand_centroid_quadrant"] = quadrant(mask)
    report["brand_required_quadrant"] = spec["required_quadrant"]
    report["brand_placement_ok"] = (report["brand_centroid_quadrant"] ==
                                    spec["required_quadrant"])

    # synthetic exposure-robustness test: HSV hue band vs a raw blue-channel threshold
    dark_hsv = hsv.copy()
    dark_hsv[:, :, 2] = (dark_hsv[:, :, 2].astype(np.float32) * 0.6).astype(np.uint8)
    report["brand_coverage_pct_dark_hsv"] = coverage(cv2.inRange(dark_hsv, lo, hi))

    blue_thresh = cv2.inRange(img[:, :, 0], spec["raw_blue_min"], 255)
    dark_bgr = (img.astype(np.float32) * 0.6).astype(np.uint8)
    blue_thresh_dark = cv2.inRange(dark_bgr[:, :, 0], spec["raw_blue_min"], 255)
    report["raw_blue_coverage_pct"] = coverage(blue_thresh)
    report["raw_blue_coverage_pct_dark"] = coverage(blue_thresh_dark)

    # red wrap-around demonstration (kept because every HSV pipeline meets red)
    red = cv2.bitwise_or(cv2.inRange(hsv, (0, 120, 80), (8, 255, 255)),
                         cv2.inRange(hsv, (172, 120, 80), (179, 255, 255)))
    report["red_wraparound_coverage_pct"] = coverage(red)

    # ---- edges ----------------------------------------------------------
    report["canny_density"] = {
        "50_150": edge_density(gray, 50, 150),
        "100_200": edge_density(gray, 100, 200),
        "150_300": edge_density(gray, 150, 300),
    }
    report["canny_ratio_sweep_high200"] = {
        "1:1 (200,200)": edge_density(gray, 200, 200),
        "1:2 (100,200)": edge_density(gray, 100, 200),
        "1:3 (66,200)": edge_density(gray, 66, 200),
    }
    report["canny_stages"] = ["gaussian smoothing", "sobel gradient magnitude and direction",
                             "non-maximum suppression", "hysteresis thresholding"]

    # ---- corners and keypoints -----------------------------------------
    report["harris_points"] = harris_count(gray)

    st = cv2.goodFeaturesToTrack(gray, maxCorners=200, qualityLevel=0.01, minDistance=10)
    report["shi_tomasi_points"] = 0 if st is None else int(len(st))

    h, w = gray.shape
    rot_m = cv2.getRotationMatrix2D((w / 2, h / 2), 30, 1.0)
    rotated = cv2.warpAffine(gray, rot_m, (w, h))
    scaled = cv2.resize(gray, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
    report["harris_invariance"] = {
        "rot_0": report["harris_points"],
        "rot_30": harris_count(rotated),
        "scale_0.5": harris_count(scaled),
    }

    fast = cv2.FastFeatureDetector_create()
    report["fast_points"] = len(fast.detect(gray, None))

    orb = cv2.ORB_create(nfeatures=500)
    kp1, des1 = orb.detectAndCompute(gray, None)
    report["orb_points"] = len(kp1)
    report["orb_descriptor_bytes"] = 0 if des1 is None else int(des1.shape[1])

    sift = cv2.SIFT_create()
    kps, dess = sift.detectAndCompute(gray, None)
    report["sift_points"] = len(kps)
    report["sift_descriptor_floats"] = 0 if dess is None else int(dess.shape[1])
    report["descriptor_storage_ratio_sift_over_orb"] = round(
        (report["sift_descriptor_floats"] * 4) / max(report["orb_descriptor_bytes"], 1), 1)

    # ---- match the rotated / scaled variant ------------------------------
    var = cv2.cvtColor(read(args.variant), cv2.COLOR_BGR2GRAY)
    kp2, des2 = orb.detectAndCompute(var, None)
    report["orb_matches_filtered"] = 0
    report["orb_match_median_distance"] = None
    if des1 is not None and des2 is not None:
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = sorted(bf.match(des1, des2), key=lambda m: m.distance)
        report["orb_matches_raw"] = len(matches)
        if matches:
            median = float(np.median([m.distance for m in matches]))
            kept = [m for m in matches if m.distance <= 0.75 * median]
            report["orb_match_median_distance"] = round(median, 2)
            report["orb_matches_filtered"] = len(kept)
            vis = cv2.drawMatches(gray, kp1, var, kp2, kept[:40], None,
                                  flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
            os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
            cv2.imwrite(os.path.join(os.path.dirname(args.out) or ".",
                                     "orb_matches.png"), vis)
    else:
        report["orb_matches_raw"] = 0
        report["orb_matches_filtered"] = 0

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(report, fh, indent=2)

    for key in ("brand_coverage_pct", "brand_coverage_pct_dark_hsv",
                "raw_blue_coverage_pct", "raw_blue_coverage_pct_dark",
                "harris_invariance", "orb_descriptor_bytes",
                "sift_descriptor_floats", "orb_matches_filtered"):
        print(f"{key:34} {report.get(key)}")
    print(f"\nWritten: {args.out}")


if __name__ == "__main__":
    main()
