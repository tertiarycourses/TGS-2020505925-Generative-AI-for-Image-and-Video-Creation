#!/usr/bin/env python3
"""Lab 11 — burn captions, composite a logo, and export a measured delivery ladder.

Writes one rendition per profile plus out/export-report.csv and
out/safe-area-check.csv.

Usage:
    python3 export_ladder.py --video reference/nq-approved-cut.mp4 \
                             --captions data/captions.json \
                             --profiles data/export-profiles.json \
                             --logo reference/nq-logo-overlay.png --out out

Requires: opencv-python, numpy. No network access.
"""
import argparse
import csv
import json
import os

import cv2
import numpy as np

FONT = cv2.FONT_HERSHEY_SIMPLEX


def cue_at(cues, t):
    for c in cues:
        if c["start"] <= t < c["end"]:
            return c
    return None


def font_scale_for(cap_height_px, thickness=2):
    """Solve for the cv2 font scale that yields the requested H-glyph height."""
    (_, h1), _ = cv2.getTextSize("Hg", FONT, 1.0, thickness)
    scale = cap_height_px / float(h1)
    while cv2.getTextSize("H", FONT, scale, thickness)[0][1] < cap_height_px:
        scale += 0.01
    return scale


def reframe(frame, out_w, out_h, mode):
    h, w = frame.shape[:2]
    if mode == "none" and (w, h) == (out_w, out_h):
        return frame.copy(), (0, 0)
    dst_ar = out_w / out_h
    if mode == "letterbox":
        scale = min(out_w / w, out_h / h)
        rs = cv2.resize(frame, (int(w * scale), int(h * scale)),
                        interpolation=cv2.INTER_AREA)
        top = (out_h - rs.shape[0]) // 2
        left = (out_w - rs.shape[1]) // 2
        out = cv2.copyMakeBorder(rs, top, out_h - rs.shape[0] - top,
                                 left, out_w - rs.shape[1] - left,
                                 cv2.BORDER_CONSTANT, value=(0, 0, 0))
        return out, (left, top)
    # centre crop then scale
    src_ar = w / h
    if src_ar > dst_ar:
        new_w = int(round(h * dst_ar))
        x0 = (w - new_w) // 2
        crop = frame[:, x0:x0 + new_w]
    else:
        new_h = int(round(w / dst_ar))
        y0 = (h - new_h) // 2
        crop = frame[y0:y0 + new_h, :]
    return cv2.resize(crop, (out_w, out_h), interpolation=cv2.INTER_AREA), (0, 0)


def draw_caption(frame, text, safe, cap_h, thickness=2):
    """Draw a plated caption inside `safe` = (x0, y0, x1, y1). Returns its rect."""
    scale = font_scale_for(cap_h, thickness)
    x0, y0, x1, y1 = safe
    pad = max(6, int(cap_h * 0.25))
    available = x1 - x0 - 2*pad
    lines = []
    line = ""
    for word in text.split():
        candidate = (line + " " + word).strip()
        if cv2.getTextSize(candidate, FONT, scale, thickness)[0][0] <= available:
            line = candidate
        else:
            if not line or cv2.getTextSize(word, FONT, scale, thickness)[0][0] > available:
                raise SystemExit("caption word cannot fit safe width at required font size")
            lines.append(line); line = word
    if line: lines.append(line)
    if not lines or len(lines) > 2:
        raise SystemExit("caption must fit one or two lines; shorten text without reducing font size")
    metrics = [cv2.getTextSize(v, FONT, scale, thickness) for v in lines]
    th = cv2.getTextSize("H", FONT, scale, thickness)[0][1]
    line_h = max(m[0][1] + m[1] for m in metrics) + pad
    total_h = len(lines)*line_h + pad
    if total_h > y1-y0:
        raise SystemExit("caption plate cannot fit safe height")
    width = max(m[0][0] for m in metrics) + 2*pad
    left = x0 + ((x1-x0)-width)//2
    rect = (left, y1-total_h, left+width, y1)
    cv2.rectangle(frame, (rect[0],rect[1]), (rect[2]-1,rect[3]-1), (18,18,22), -1)
    for j,(line,metric) in enumerate(zip(lines,metrics)):
        y = rect[1] + pad + metric[0][1] + j*line_h
        cv2.putText(frame,line,(left+pad,y),FONT,scale,(245,245,245),thickness,cv2.LINE_AA)
    return rect, th


def composite_logo(frame, logo, safe):
    x0, y0, x1, y1 = safe
    lh, lw = logo.shape[:2]
    x = x1 - lw
    y = y0
    if x < x0 or y + lh > y1:
        return None
    roi = frame[y:y + lh, x:x + lw]
    if logo.shape[2] == 4:
        bgr = logo[:, :, :3].astype(np.float32)
        alpha = logo[:, :, 3:4].astype(np.float32) / 255.0
        frame[y:y + lh, x:x + lw] = (alpha * bgr +
                                     (1 - alpha) * roi.astype(np.float32)).astype(np.uint8)
    else:
        frame[y:y + lh, x:x + lw] = logo
    return (x, y, x + lw, y + lh)


def inside(rect, safe):
    return (rect[0] >= safe[0] and rect[1] >= safe[1] and
            rect[2] <= safe[2] and rect[3] <= safe[3])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", default="reference/nq-approved-cut.mp4")
    ap.add_argument("--captions", default="data/captions.json")
    ap.add_argument("--profiles", default="data/export-profiles.json")
    ap.add_argument("--logo", default="reference/nq-logo-overlay.png")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()

    cues = json.load(open(args.captions))["cues"]
    overlaps = [i for i in range(1, len(cues)) if cues[i]["start"] < cues[i - 1]["end"]]
    if overlaps:
        raise SystemExit(f"overlapping cues at indices {overlaps} — fix the cue list first")

    profiles = json.load(open(args.profiles))["profiles"]
    logo_src = cv2.imread(args.logo, cv2.IMREAD_UNCHANGED)
    if logo_src is None:
        raise SystemExit(f"cannot read {args.logo}")

    if logo_src.ndim != 3 or logo_src.shape[2] != 4:
        raise SystemExit("logo must be a four-channel PNG with alpha")
    if not cues or not profiles:
        raise SystemExit("at least one cue and profile required")
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise SystemExit(f"cannot open {args.video}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not np.isfinite(fps) or fps <= 0:
        raise SystemExit("constant-FPS source with valid FPS is required")
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    cap.release()
    if not frames:
        raise SystemExit("source has no decodable frames")
    duration = len(frames)/fps
    for cue in cues:
        if not (0 <= cue["start"] < cue["end"] <= duration) or cue["end"]-cue["start"] < 1.2:
            raise SystemExit("cues must be within duration and last at least 1.2 seconds")
        if not cue["text"].strip() or not cue["text"].isascii():
            raise SystemExit("this Hershey-font lab supports nonempty ASCII caption text only")
    print(f"source: {frames[0].shape[1]}x{frames[0].shape[0]} "
          f"{fps} fps  {len(frames)} frames  {len(frames)/fps:.2f}s\n")

    os.makedirs(args.out, exist_ok=True)
    export_rows, safe_rows = [], []

    for prof in profiles:
        name = prof["name"]
        ow, oh = prof["width"], prof["height"]
        inset = prof["safe_inset"]
        if ow <= 0 or oh <= 0 or ow % 2 or oh % 2 or not 0 <= inset < 0.5:
            raise SystemExit("profile needs positive even dimensions and safe_inset in [0,0.5)")
        if prof["reframe"] not in ("none", "centre_crop", "letterbox"):
            raise SystemExit("unknown reframe mode")
        if prof["reframe"] == "none" and frames[0].shape[1]/frames[0].shape[0] != ow/oh:
            raise SystemExit("none mode requires source aspect ratio; choose crop or letterbox")
        cap_h = max(prof["min_cap_height_px"], int(np.ceil(0.03*oh)))
        safe = (int(ow * inset), int(oh * inset),
                int(ow * (1 - inset)), int(oh * (1 - inset)))

        scale = min(1.0, (ow * 0.22) / logo_src.shape[1])
        logo = cv2.resize(logo_src, (max(1, int(logo_src.shape[1] * scale)),
                                     max(1, int(logo_src.shape[0] * scale))),
                          interpolation=cv2.INTER_AREA)

        path = os.path.join(args.out, f"export_{name}.mp4")
        writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (ow, oh))
        if not writer.isOpened():
            raise SystemExit(f"VideoWriter failed for {path}")

        seen_cues, achieved_h, plate_ratio = set(), None, None
        for i, frame in enumerate(frames):
            out, _ = reframe(frame, ow, oh, prof["reframe"])
            assert out.shape[:2] == (oh, ow), f"reframe produced {out.shape[:2]}"
            t = i / fps
            c = cue_at(cues, t)
            if c is not None:
                rect, th = draw_caption(out, c["text"], safe, cap_h)
                achieved_h = min(achieved_h, th) if achieved_h is not None else th
                cue_index = next(j for j,v in enumerate(cues) if v is c)
                if cue_index not in seen_cues:
                    seen_cues.add(cue_index)
                    safe_rows.append({
                        "profile": name, "item": f"cue:{cue_index}:{c['text'][:28]}",
                        "x0": rect[0], "y0": rect[1], "x1": rect[2], "y1": rect[3],
                        "safe_x0": safe[0], "safe_y0": safe[1],
                        "safe_x1": safe[2], "safe_y1": safe[3],
                        "verdict": "PASS" if inside(rect, safe) else "FAIL",
                    })
                if plate_ratio is None:
                    # Relative sRGB luminance of chosen solid design colours, not encoded pixels.
                    def luminance(bgr):
                        rgb = np.asarray(bgr[::-1], dtype=float)/255
                        linear = np.where(rgb <= 0.04045, rgb/12.92, ((rgb+0.055)/1.055)**2.4)
                        return float(linear @ [0.2126,0.7152,0.0722])
                    plate_ratio = round((luminance((245,245,245))+0.05)/(luminance((18,18,22))+0.05),2)
            lrect = composite_logo(out, logo, safe)
            if i == 0:
                safe_rows.append({
                    "profile": name, "item": "logo",
                    "x0": lrect[0] if lrect else -1, "y0": lrect[1] if lrect else -1,
                    "x1": lrect[2] if lrect else -1, "y1": lrect[3] if lrect else -1,
                    "safe_x0": safe[0], "safe_y0": safe[1],
                    "safe_x1": safe[2], "safe_y1": safe[3],
                    "verdict": "PASS" if (lrect and inside(lrect, safe)) else "FAIL",
                })
            cv2.putText(out, "SIMULATED classroom source", (safe[0], safe[1]+16), FONT, 0.45, (245,245,245), 1, cv2.LINE_AA)
            if c is not None and len(seen_cues) == 1:
                cv2.imwrite(os.path.join(args.out, f"still_{name}.png"), out)
            writer.write(out)
        writer.release()

        size = os.path.getsize(path)
        vcap = cv2.VideoCapture(path)
        n = 0
        while True:
            ok, decoded = vcap.read()
            if not ok: break
            if decoded.shape[:2] != (oh,ow):
                raise SystemExit("decoded export dimensions differ from profile")
            n += 1
        vcap.release()
        if n != len(frames):
            raise SystemExit(f"export frame loss: {n} versus {len(frames)}")
        if len(seen_cues) != len(cues):
            raise SystemExit("some cues never appeared on a decoded frame")
        duration = n / fps if fps else 0.0
        export_rows.append({
            "profile": name, "width": ow, "height": oh, "reframe": prof["reframe"],
            "frames": n, "duration_s": round(duration, 2),
            "bytes": size, "bits_per_second": int(size * 8 / duration) if duration else 0,
            "max_bytes": prof["max_bytes"],
            "size_verdict": "PASS" if size <= prof["max_bytes"] else "FAIL",
            "cap_height_px": achieved_h or 0,
            "cap_height_pct_of_frame": round(100.0 * (achieved_h or 0) / oh, 2),
            "cap_height_verdict": "PASS" if (achieved_h or 0) >= cap_h else "FAIL",
            "plate_text_luminance_ratio": plate_ratio,
        })
        print(f"{name:5} {ow}x{oh} {prof['reframe']:12} {n:4} frames "
              f"{duration:5.2f}s {size:>9} B  size {export_rows[-1]['size_verdict']}  "
              f"cap {achieved_h}px {export_rows[-1]['cap_height_verdict']}")

    exp_csv = os.path.join(args.out, "export-report.csv")
    with open(exp_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(export_rows[0]))
        w.writeheader()
        w.writerows(export_rows)

    safe_csv = os.path.join(args.out, "safe-area-check.csv")
    with open(safe_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(safe_rows[0]))
        w.writeheader()
        w.writerows(safe_rows)

    fails = [r for r in safe_rows if r["verdict"] == "FAIL"]
    print(f"\nsafe-area failures: {len(fails)}")
    print(f"Written: {exp_csv}\nWritten: {safe_csv}")
    print("\nPROVENANCE: all renditions derive from a SIMULATED classroom source clip and")
    print("inherit that label. They are not generative-model output.")


if __name__ == "__main__":
    main()
