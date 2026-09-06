#!/usr/bin/env python3
"""Lab 02 — measure how an image and a video are actually represented.

Writes a JSON report of array shape, dtype, channel statistics, HSV ranges,
video properties and the uncompressed byte rate.

Usage:
    python3 represent.py --image reference/nq-product-flatlay.png \
                         --video reference/nq-shelf-pan.mp4 \
                         --out out/representation-report.json

Requires: opencv-python, numpy. No network access.
"""
import argparse
import json
import os

import cv2
import numpy as np


def measure_image(path):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"cannot read image: {path}")
    if min(img.shape[:2]) <= 10:
        raise SystemExit("image must be at least 11x11 for calibration pixel")
    b, g, r = cv2.split(img)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return {
        "image_path": path,
        "image_shape": list(img.shape),
        "image_dtype": str(img.dtype),
        "pixel_10_10_bgr": [int(x) for x in img[10, 10]],
        "channel_means_bgr": [round(float(c.mean()), 2) for c in (b, g, r)],
        "gray_shape": list(gray.shape),
        "hsv_ranges": {"H": [int(h.min()), int(h.max())],
                       "S": [int(s.min()), int(s.max())],
                       "V": [int(v.min()), int(v.max())]},
    }


def measure_video(path):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise SystemExit(f"cannot open video: {path}")
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    if not np.isfinite(fps) or fps <= 0 or w <= 0 or h <= 0:
        cap.release()
        raise SystemExit("invalid dimensions/FPS: inspect metadata or replace input; do not estimate from decode speed")
    reported = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    decoded = 0
    while True:
        ok, _ = cap.read()
        if not ok:
            break
        decoded += 1
    cap.release()

    if decoded == 0:
        raise SystemExit("video contains no decodable frames")
    encoded_bytes = os.path.getsize(path)
    uncompressed_bps = w * h * 3 * fps
    duration = decoded / fps if fps else 0.0
    return {
        "video_path": path,
        "video_width": w,
        "video_height": h,
        "video_fps": round(fps, 3),
        "video_frames_reported": reported,
        "video_frames_decoded": decoded,
        "video_duration_s": round(duration, 2),
        "encoded_bytes_on_disk": encoded_bytes,
        "uncompressed_bytes_per_second": uncompressed_bps,
        "compression_ratio": round(uncompressed_bps * duration / encoded_bytes, 1)
        if encoded_bytes else None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", default="reference/nq-product-flatlay.png")
    ap.add_argument("--video", default="reference/nq-shelf-pan.mp4")
    ap.add_argument("--out", default="out/representation-report.json")
    args = ap.parse_args()

    report = {}
    report.update(measure_image(args.image))
    report.update(measure_video(args.video))

    # The bit-rate comparison that Topic 5 relies on.
    report["reference_rates_MBps"] = {
        "640x360@25": round(640 * 360 * 3 * 25 / 1e6, 2),
        "1920x1080@30": round(1920 * 1080 * 3 * 30 / 1e6, 2),
    }

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(report, fh, indent=2)

    for key, value in report.items():
        print(f"{key:34} {value}")
    print(f"\nWritten: {args.out}")


if __name__ == "__main__":
    main()
