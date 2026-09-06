#!/usr/bin/env python3
"""Lab 12 — measure real per-stage pipeline latency and model the bandwidth of each split.

MEASURED  : per-stage milliseconds on this machine, median and p95, first five
            frames discarded.
MODELLED  : generation latency from the documented S (image) and S x F (video)
            relationships; INT8 and low-rank-adapter arithmetic.
ILLUSTRATIVE: monthly transferred data cost from the unit rates in the constraints file.

The three are kept in separate output tables on purpose — mixing them is the mistake
this lab exists to prevent.

Usage:
    python3 pipeline_bench.py --video reference/nq-pipeline-clip.mp4 \
                              --constraints data/deployment-constraints.json \
                              --out out

Requires: opencv-python, numpy. No network access.
"""
import argparse
import csv
import json
import os
import platform
import time

import cv2
import numpy as np


def timed(fn, frames, warmup=5):
    """Run fn over every frame, discard the warm-up, return (median_ms, p95_ms, n)."""
    times = []
    for i, f in enumerate(frames):
        t0 = time.perf_counter()
        fn(f)
        dt = (time.perf_counter() - t0) * 1000.0
        if i >= warmup:
            times.append(dt)
    if not times:
        raise ValueError("need more frames than the five-frame warm-up")
    arr = np.array(times)
    return round(float(np.median(arr)), 3), round(float(np.percentile(arr, 95)), 3), len(arr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", default="reference/nq-pipeline-clip.mp4")
    ap.add_argument("--constraints", default="data/deployment-constraints.json")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()

    cons = json.load(open(args.constraints))
    os.makedirs(args.out, exist_ok=True)

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise SystemExit(f"cannot open {args.video}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not np.isfinite(fps) or fps<=0:
        cap.release()
        raise SystemExit("valid playback FPS required; no silent fallback")
    frames = []
    t_decode = []
    while True:
        t0 = time.perf_counter()
        ok, f = cap.read()
        dt = (time.perf_counter() - t0) * 1000.0
        if not ok:
            break
        frames.append(f)
        t_decode.append(dt)
    cap.release()
    if len(frames)<=5:
        raise SystemExit("need at least six decodable frames for warm-up exclusion")
    h, w = frames[0].shape[:2]

    env = (f"{platform.processor() or platform.machine()} | "
           f"{platform.system()} {platform.release()} | "
           f"Python {platform.python_version()} | OpenCV {cv2.__version__}")
    print(f"MEASURED ON: {env}")
    print(f"clip: {w}x{h} {fps} fps, {len(frames)} frames\n")

    # ---- stage definitions (the real Lab 02-11 stages) -------------------
    sub = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=16)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades +
                                    "haarcascade_frontalface_default.xml")
    if cascade.empty():
        raise SystemExit("installed cascade unavailable")
    orb = cv2.ORB_create(nfeatures=500)
    prev = {"g": cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)}

    def s_colour(f):
        cv2.cvtColor(f, cv2.COLOR_BGR2HSV)

    def s_gray(f):
        cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)

    def s_denoise(f):
        cv2.GaussianBlur(f, (5, 5), 0)

    def s_bgsub(f):
        sub.apply(f)

    def s_edges(f):
        cv2.Canny(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), 100, 200)

    def s_features(f):
        orb.detectAndCompute(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), None)

    def s_detect(f):
        cascade.detectMultiScale(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY),
                                 scaleFactor=1.1, minNeighbors=4, minSize=(24, 24))

    def s_flow(f):
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        cv2.calcOpticalFlowFarneback(prev["g"], g, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        prev["g"] = g

    def s_encode(f):
        cv2.imencode(".jpg", f, [int(cv2.IMWRITE_JPEG_QUALITY), 85])

    stages = [
        ("decode", "edge", None),
        ("colour_convert_bgr2hsv", "edge", s_colour),
        ("grayscale", "edge", s_gray),
        ("denoise_gaussian_5x5", "edge", s_denoise),
        ("background_subtraction_mog2", "edge", s_bgsub),
        ("canny_edges", "edge", s_edges),
        ("orb_features_500", "edge", s_features),
        ("haar_cascade_detect", "edge", s_detect),
        ("optical_flow_farneback", "edge", s_flow),
        ("jpeg_encode_q85", "edge", s_encode),
    ]

    rows = []
    dec = np.array(t_decode[5:]) if len(t_decode) > 5 else np.array(t_decode)
    rows.append({"stage": "decode", "layer": "edge", "evidence": "MEASURED",
                 "median_ms": round(float(np.median(dec)), 3),
                 "p95_ms": round(float(np.percentile(dec, 95)), 3),
                 "frames": len(dec)})
    for name, layer, fn in stages[1:]:
        med, p95, n = timed(fn, frames)
        rows.append({"stage": name, "layer": layer, "evidence": "MEASURED",
                     "median_ms": med, "p95_ms": p95, "frames": n})

    # Direct sequential harness timing includes decode and all listed operations.
    # This is local processing only; no network, queue, cloud model or publishing.
    sub = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=16)
    prev["g"] = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
    cap2=cv2.VideoCapture(args.video)
    totals=[]
    idx=0
    while True:
        t0=time.perf_counter()
        ok,frame=cap2.read()
        if not ok: break
        for _,_,fn in stages[1:]: fn(frame)
        if idx>=5: totals.append((time.perf_counter()-t0)*1000)
        idx+=1
    cap2.release()
    if idx!=len(frames) or not totals:
        raise SystemExit("sequential harness decode count changed")
    rows.append({"stage":"local_harness_end_to_end", "layer":"edge", "evidence":"MEASURED",
                 "median_ms":round(float(np.median(totals)),3),
                 "p95_ms":round(float(np.percentile(totals,95)),3),"frames":len(totals)})

    # MODELLED generation stages — never mixed with the measured ones.
    S = cons["generation"]["denoising_steps"]
    step_ms = cons["generation"]["assumed_ms_per_step"]
    F = cons["generation"]["video_frames"]
    rows.append({"stage": f"image_generation_modelled_S{S}", "layer": "cloud",
                 "evidence": "MODELLED", "median_ms": S * step_ms,
                 "p95_ms": "", "frames": ""})
    rows.append({"stage": f"video_generation_modelled_S{S}xF{F}", "layer": "cloud",
                 "evidence": "MODELLED", "median_ms": S * F * step_ms,
                 "p95_ms": "", "frames": ""})

    modelled_rows=[r for r in rows if r["evidence"]=="MODELLED"]
    rows=[r for r in rows if r["evidence"]=="MEASURED"]
    with open(os.path.join(args.out,"generation-model.csv"),"w",newline="") as fh:
        writer=csv.DictWriter(fh,fieldnames=list(modelled_rows[0]));writer.writeheader();writer.writerows(modelled_rows)
    with open(os.path.join(args.out,"environment.json"),"w") as fh:
        json.dump({"hardware":env,"width":w,"height":h,"fps":fps,"frames":len(frames),"warmup_frames":5,"note":"CPU architecture fallback is not a full CPU model; record actual hardware in decision"},fh,indent=2)
    lat_csv = os.path.join(args.out, "stage-latency.csv")
    with open(lat_csv, "w", newline="") as fh:
        wtr = csv.DictWriter(fh, fieldnames=["stage", "layer", "evidence",
                                             "median_ms", "p95_ms", "frames"])
        wtr.writeheader()
        wtr.writerows(rows)

    edge_total = next(r["median_ms"] for r in rows if r["stage"]=="local_harness_end_to_end")
    budget = cons["latency_budget_ms"]["shelf_alert"]
    print(f"{'stage':32} {'median ms':>10} {'p95 ms':>9}  evidence")
    for r in rows:
        print(f"{r['stage']:32} {str(r['median_ms']):>10} {str(r['p95_ms']):>9}  {r['evidence']}")
    print(f"\nMEASURED local harness end-to-end median (no network/cloud/queue): {edge_total:.2f} ms per frame")
    print(f"Shelf-alert budget: {budget} ms -> "
          f"{'WITHIN' if edge_total <= budget else 'OVER'} budget "
          f"by {abs(budget - edge_total):.2f} ms")
    print(f"MODELLED image generation ({S} steps): {S*step_ms} ms")
    print(f"MODELLED video generation ({S} steps x {F} frames): {S*F*step_ms} ms "
          f"({S*F*step_ms/1000:.1f} s) -> {F}x the image cost\n")

    # ---- bandwidth model at each split point ----------------------------
    stores = cons["stores"]
    uplink_mbps = cons["uplink_mbit_per_store"]
    hours = cons["operating_hours_per_month"]
    rate = cons["illustrative_cost_per_gb_sgd"]

    cameras=cons.get("cameras_per_store",1)
    if cameras<=0 or stores<=0 or uplink_mbps<=0 or hours<0 or rate<0:
        raise SystemExit("invalid deployment scale, hours or rate")
    raw_bps = w * h * 3 * fps
    encoded_bps = cons["encoded_bitrate_kbit_per_camera"] * 1000 / 8.0
    orb_bps = cons["features"]["keypoints_per_frame"] * (32 + cons["features"].get("metadata_bytes_per_keypoint",0)) * fps
    event_bps = cons["events"]["per_minute"] / 60.0 * cons["events"]["bytes_each"]

    splits = [
        ("A_raw_frames", "cut above decode: uncompressed frames to cloud", raw_bps),
        ("B_encoded_video", "cut above analysis: encoded stream to cloud", encoded_bps),
        ("C_feature_vectors", "cut above detection: ORB descriptors to cloud", orb_bps),
        ("D_events_only", "cut above application: JSON events to cloud", event_bps),
    ]

    bw_rows = []
    for name, desc, bps in splits:
        mbps_store = bps * cameras * 8 / 1e6
        gbps_estate = mbps_store * stores / 1000.0
        monthly_gb = bps * 3600 * hours / 1e9
        bw_rows.append({
            "split": name, "description": desc,
            "bytes_per_second_per_camera": round(bps,6),
            "cameras_per_store": cameras, "evidence": "ILLUSTRATIVE_MODEL",
            "assumption": "payload only; network overhead omitted; direction-specific transfer charge assumed",
            "mbit_per_second_per_store": round(mbps_store, 6),
            "gbit_per_second_at_estate": round(gbps_estate, 9),
            "feasible_on_uplink": "YES" if mbps_store <= uplink_mbps else "NO",
            "monthly_gb_per_camera": round(monthly_gb, 2),
            "illustrative_monthly_cost_sgd_estate":
                round(monthly_gb * cameras * stores * rate, 2),
        })

    bw_csv = os.path.join(args.out, "bandwidth-model.csv")
    with open(bw_csv, "w", newline="") as fh:
        wtr = csv.DictWriter(fh, fieldnames=list(bw_rows[0]))
        wtr.writeheader()
        wtr.writerows(bw_rows)

    print(f"{'split':20} {'Mbit/s/store':>13} {'Gbit/s estate':>14} feasible")
    for r in bw_rows:
        print(f"{r['split']:20} {r['mbit_per_second_per_store']:13.6f} "
              f"{r['gbit_per_second_at_estate']:14.9f} {r['feasible_on_uplink']}")

    # ---- edge-fit arithmetic (MODELLED) ---------------------------------
    params = cons["model"]["parameters"]
    d, m, r_rank = cons["model"]["layer_d"], cons["model"]["layer_m"], cons["model"]["lora_rank"]
    fp32_gb = params * 4 / 1e9
    int8_gb = params * 1 / 1e9
    print(f"\nMODELLED edge fit for a {params/1e9:.2f}B-parameter model:")
    print(f"  FP32 parameter memory {fp32_gb:.2f} GB -> INT8 {int8_gb:.2f} GB "
          f"(ratio {8/32:.2f})")
    print(f"  full fine-tune of one {d}x{m} layer: {d*m:,} trainable parameters")
    print(f"  low-rank adapter r={r_rank}:        {r_rank*(d+m):,} trainable parameters "
          f"({100.0*r_rank*(d+m)/(d*m):.2f}%)")

    e = cons["energy"]
    e_sample = e["overhead_factor"] * e["joules_per_flop"] * e["flops_per_sample"]
    print(f"\nILLUSTRATIVE energy per generated sample: {e_sample:.2f} J "
          f"(overhead {e['overhead_factor']} x {e['joules_per_flop']} J/FLOP "
          f"x {e['flops_per_sample']:.2e} FLOPs)")
    print("  A real figure additionally requires: hardware inventory, total kWh,")
    print("  measured utilisation, grid carbon intensity, and joules per sample.")

    print(f"\nWritten: {lat_csv}\nWritten: {bw_csv}")
    print("Next: write out/split-decision.md — apply the privacy gate FIRST,")
    print("then choose among the splits that survive it.")


if __name__ == "__main__":
    main()
