#!/usr/bin/env python3
"""Lab 09 — render a deterministic animatic from storyboard frames.

IMPORTANT: the output is a DETERMINISTIC ANIMATIC produced by OpenCV from the
supplied storyboard art. It is NOT generative-model output. A persistent
"ANIMATIC - NOT AI-GENERATED VIDEO" banner is burned into every frame so the
artefact cannot be mistaken for a render.

Usage:
    python3 animatic.py --board reference/board \
                        --shots out/shot-list.csv \
                        --out out/animatic.mp4 --fps 24

Requires: opencv-python, numpy. No network access.
"""
import argparse
import csv
import glob
import os
import re

import cv2
import numpy as np

W, H = 1280, 720
BANNER = "ANIMATIC - NOT AI-GENERATED VIDEO"


def timecode(seconds, fps):
    total = int(round(seconds * fps))
    s, f = divmod(total, fps)
    m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}:{f:02d}"


def label(frame, shot, purpose, t, fps):
    out = frame.copy()
    # top banner
    cv2.rectangle(out, (0, 0), (W, 40), (18, 18, 22), -1)
    cv2.putText(out, BANNER, (16, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.62,
                (255, 255, 255), 1, cv2.LINE_AA)
    # bottom strip: shot, purpose, timecode
    cv2.rectangle(out, (0, H - 46), (W, H), (18, 18, 22), -1)
    cv2.putText(out, f"SHOT {shot}  |  {purpose[:64]}", (16, H - 17),
                cv2.FONT_HERSHEY_SIMPLEX, 0.58, (235, 235, 235), 1, cv2.LINE_AA)
    tc = timecode(t, fps)
    cv2.putText(out, tc, (W - 150, H - 17), cv2.FONT_HERSHEY_SIMPLEX, 0.62,
                (120, 220, 160), 1, cv2.LINE_AA)
    return out


def board_frames(board_dir, shot):
    paths = sorted(glob.glob(os.path.join(board_dir, f"shot{shot}_*.png")))
    if len(paths) != 3:
        raise SystemExit(f"require exactly three storyboard frames for shot {shot} in {board_dir}")
    frames = []
    for p in paths:
        img = cv2.imread(p, cv2.IMREAD_COLOR)
        if img is None:
            raise SystemExit(f"cannot read {p}")
        if img.shape[1] != W or img.shape[0] != H:
            img = cv2.resize(img, (W, H), interpolation=cv2.INTER_AREA)
        frames.append(img)
    return frames


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", default="reference/board")
    ap.add_argument("--shots", default="out/shot-list.csv")
    ap.add_argument("--out", default="out/animatic.mp4")
    ap.add_argument("--fps", type=int, default=24)
    args = ap.parse_args()

    if not os.path.exists(args.shots):
        raise SystemExit(f"{args.shots} not found — write the shot list first (step 2)")
    shots = list(csv.DictReader(open(args.shots)))
    if args.fps <= 0 or len(shots)!=3:
        raise SystemExit("require positive FPS and exactly three shots")
    ids=[int(re.sub(r"\D", "",r["shot"]) or 0) for r in shots]
    if ids != [1,2,3] or any(float(r["seconds"])!=8 or not r.get("purpose", "").strip() for r in shots):
        raise SystemExit("require shots 1,2,3, each eight seconds with a purpose")
    for shot in ids: board_frames(args.board,shot)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(args.out, fourcc, args.fps, (W, H))
    if not writer.isOpened():
        raise SystemExit("VideoWriter failed to open — try a different fourcc")

    written = 0
    for row in shots:
        shot = int(re.sub(r"\D", "", row["shot"]) or 0)
        seconds = float(row["seconds"])
        purpose = row.get("purpose", "")
        frames = board_frames(args.board, shot)

        total = int(round(seconds * args.fps))
        per_frame = max(1, total // len(frames))
        seq = []
        for f in frames:
            seq.extend([f] * per_frame)
        while len(seq) < total:          # pad with the last board frame
            seq.append(frames[-1])
        seq = seq[:total]

        for i, f in enumerate(seq):
            t = (written + i) / args.fps
            writer.write(label(f, shot, purpose, t, args.fps))
        written += total
        print(f"shot {shot}: {seconds:.1f}s -> {total} frames "
              f"({len(frames)} board frames x {per_frame})")

    writer.release()

    cap = cv2.VideoCapture(args.out)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    decoded=0
    while True:
        ok,_=cap.read()
        if not ok: break
        decoded+=1
    cap.release()
    if fps<=0 or abs(fps-args.fps)>0.01 or decoded!=written:
        raise SystemExit("output decode verification failed")
    print(f"\nWritten: {args.out}")
    print(f"Verify: {n} frames at {fps} fps = {n / fps:.2f}s "
          f"(shot list total {sum(float(r['seconds']) for r in shots):.2f}s)")
    print("\nPROVENANCE: this file is a DETERMINISTIC ANIMATIC rendered from storyboard")
    print("frames with OpenCV. It is NOT generative-model output.")


if __name__ == "__main__":
    main()
