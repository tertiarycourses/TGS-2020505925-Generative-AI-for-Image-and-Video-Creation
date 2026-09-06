#!/usr/bin/env python3
"""Lab 01 — weighted needs-analysis scorer.

Reads the candidate use cases and the weighted criteria, applies the banding rules
described in the README, and writes a scored CSV with a preliminary REVIEW_GATES/REJECT verdict.

Usage:
    python3 score_needs.py --csv data/candidate-use-cases.csv \
                           --criteria data/need-criteria.json \
                           --out out/baseline-scores.csv

Standard library only — no third-party packages, no network access.
"""
import argparse
import csv
import json
import os


def band(value, high, mid):
    """Return 5 / 3 / 1 for a value above `high`, at/above `mid`, or below `mid`."""
    if value >= high:
        return 5
    if value >= mid:
        return 3
    return 1


LATENCY_SCORE = {"batch": 5, "interactive": 3, "realtime": 1}
PRIVACY_SCORE = {"none": 5, "internal": 3, "personal": 1}
TOLERANCE_SCORE = {"reviewed": 5, "sampled": 3, "unreviewed": 1}


def score_row(row):
    """Score one candidate use case on the six need criteria (each 0-5)."""
    volume = int(row["instances_per_month"])
    manual = float(row["current_manual_cost_sgd_per_month"])
    auto = float(row["estimated_automated_cost_sgd_per_month"])
    cost_gap = (manual - auto) / manual if manual else 0.0
    return {
        "volume": band(volume, 500, 50),
        "repeatability": int(row["repeatability_0_5"]),
        "latency_class": LATENCY_SCORE[row["latency_class"]],
        "accuracy_tolerance": TOLERANCE_SCORE[row["review_mode"]],
        "privacy_risk": PRIVACY_SCORE[row["privacy_class"]],
        "cost_gap": band(cost_gap, 0.6, 0.3),
    }, cost_gap


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="data/candidate-use-cases.csv")
    ap.add_argument("--criteria", default="data/need-criteria.json")
    ap.add_argument("--out", default="out/needs-scores.csv")
    args = ap.parse_args()

    spec = json.load(open(args.criteria))
    weights = spec["weights"]
    threshold = spec["accept_threshold"]

    rows = list(csv.DictReader(open(args.csv)))
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    fields = (["case_id", "name"] + list(weights) +
              ["cost_gap_ratio", "weighted_total", "verdict"])
    accepted = []
    with open(args.out, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            scores, cost_gap = score_row(row)
            total = sum(scores[k] * weights[k] for k in weights)
            verdict = "REVIEW_GATES" if total >= threshold else "REJECT"
            if verdict == "REVIEW_GATES":
                accepted.append(row["case_id"])
            out = {"case_id": row["case_id"], "name": row["name"],
                   "cost_gap_ratio": round(cost_gap, 3),
                   "weighted_total": round(total, 2), "verdict": verdict}
            out.update(scores)
            writer.writerow(out)
            print(f"{row['case_id']:>6}  total={total:6.2f}  {verdict}")

    print(f"\nAccept threshold: {threshold}")
    print("No final acceptance is established by this scorer. Complete out/eligibility.csv and the manual final verdicts.")
    print(f"Score-qualified: {', '.join(accepted) if accepted else '(none)'}")
    print(f"Written:  {args.out}")


if __name__ == "__main__":
    main()
