#!/usr/bin/env python3
"""Paired bootstrap interval on the per-item delta between two runs.

Input: two per-item files (JSON {"items":[...]} or JSONL, one record per line), each
record with "id" and a numeric "score" (0/1 for pass/fail works). Items are matched
on id; unmatched ids are an error, because an unpaired comparison is a different,
weaker test.

Optional "cluster" field on records: when present, resampling is done over clusters
(documents, repos, conversations), which is the honest interval when items share a
parent. Naive item-level intervals on clustered data have been measured at a third
of the true width.

Usage:
  paired_bootstrap.py --a baseline.json --b treatment.json [--reps 5000] [--seed 0]
Prints mean delta (b - a), 95% interval, and improved/regressed/held counts.
Exit 0 on valid input (the decision rule lives in the pre-registration); exit 1 on bad or unpaired input.
"""
import argparse, json, random, statistics, sys


def parse_records(text):
    """Accept {"items":[...]}, a bare JSON array, or JSONL (one object per line)."""
    try:
        data = json.loads(text)
        return data["items"] if isinstance(data, dict) else data
    except json.JSONDecodeError:
        return [json.loads(l) for l in text.splitlines() if l.strip()]


def load(path):
    try:
        text = open(path).read()
    except FileNotFoundError:
        sys.exit(f"error: file not found: {path}")
    text = text.strip()
    try:
        items = parse_records(text)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        sys.exit(f"error: {path} is not a per-item JSON/JSONL file ({e}). Need records with 'id' and numeric 'score'.")
    out = {}
    for it in items:
        if "id" not in it or not isinstance(it.get("score"), (int, float)) or isinstance(it.get("score"), bool):
            sys.exit(f"error: record {it!r} in {path} needs 'id' and a numeric 'score'.")
        item_id = str(it["id"])
        if item_id in out:
            sys.exit(f"error: {path} contains duplicate item id {item_id!r}.")
        out[item_id] = it
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a", required=True, help="baseline per-item file")
    ap.add_argument("--b", required=True, help="treatment per-item file")
    ap.add_argument("--reps", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    if args.reps < 1:
        sys.exit("error: --reps must be at least 1.")

    A, B = load(args.a), load(args.b)
    if set(A) != set(B):
        sys.exit(f"error: item ids differ ({len(set(A)-set(B))} only in a, {len(set(B)-set(A))} only in b). Paired analysis needs identical item sets.")
    ids = sorted(A)
    if len(ids) < 2:
        sys.exit("error: need at least 2 paired items.")

    cluster_mismatches = [i for i in ids if A[i].get("cluster", i) != B[i].get("cluster", i)]
    if cluster_mismatches:
        sys.exit("error: cluster assignments differ between arms for ids: " + ", ".join(cluster_mismatches[:20]))

    deltas = {i: B[i]["score"] - A[i]["score"] for i in ids}
    clusters = {}
    for i in ids:
        clusters.setdefault(A[i].get("cluster", i), []).append(deltas[i])
    units = list(clusters.values())
    unit_name = "clusters" if len(units) < len(ids) else "items"

    rng = random.Random(args.seed)
    means = []
    for _ in range(args.reps):
        sample = [rng.choice(units) for _ in units]
        flat = [d for u in sample for d in u]
        means.append(sum(flat) / len(flat))
    means.sort()
    lo, hi = means[int(0.025 * args.reps)], means[int(0.975 * args.reps) - 1]
    mean = statistics.fmean(deltas.values())
    imp = sum(1 for d in deltas.values() if d > 0)
    reg = sum(1 for d in deltas.values() if d < 0)

    print(f"n {len(ids)} items, resampled over {len(units)} {unit_name}, {args.reps} reps, seed {args.seed}")
    print(f"mean delta (b - a) {mean:+.4f}   95% interval [{lo:+.4f}, {hi:+.4f}]")
    print(f"improved {imp}  regressed {reg}  held {len(ids)-imp-reg}")
    if lo <= 0 <= hi:
        print("interval includes zero: not distinguishable from noise on this fixture")
    else:
        print("interval excludes zero on this fixture (still subject to fixture validity and label error)")


if __name__ == "__main__":
    main()
