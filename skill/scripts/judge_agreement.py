#!/usr/bin/env python3
"""Agreement between a judge's labels and human labels on a calibration set.

Reports Cohen's kappa (chance-corrected), raw agreement (for contrast, never for the
decision), and precision / recall of the judge's positive label against the human
positive label. Works for any two label files; use it human-vs-human first to check
the guideline, then judge-vs-human.

Input: two files, JSON {"items":[{"id","label"}]} or JSONL, or CSV with header id,label.
Labels are compared as strings. --positive names the label treated as PASS.

Usage:
  judge_agreement.py --human human.jsonl --judge judge.jsonl [--positive pass] [--floor 0.8]
Exit 0 if kappa >= floor, 1 if below (judge is a diagnostic, not a grader), 2 on bad input.
"""
import argparse, csv, json, sys
from collections import Counter


def load(path):
    try:
        text = open(path).read().strip()
    except FileNotFoundError:
        print(f"CANNOT-MEASURE: file not found: {path}", file=sys.stderr); sys.exit(2)
    try:
        if text.lower().startswith("id,"):
            rows = list(csv.DictReader(text.splitlines()))
        else:
            try:
                data = json.loads(text)
                rows = data["items"] if isinstance(data, dict) else data
            except json.JSONDecodeError:
                rows = [json.loads(l) for l in text.splitlines() if l.strip()]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"CANNOT-MEASURE: {path} is not JSON/JSONL/CSV with id,label ({e})", file=sys.stderr); sys.exit(2)
    out = {}
    for r in rows:
        if "id" not in r or "label" not in r:
            print(f"CANNOT-MEASURE: record {r!r} in {path} needs 'id' and 'label'", file=sys.stderr); sys.exit(2)
        out[str(r["id"])] = str(r["label"]).strip().lower()
    return out


def kappa(pairs):
    n = len(pairs)
    po = sum(1 for h, j in pairs if h == j) / n
    labels = set(h for h, _ in pairs) | set(j for _, j in pairs)
    ch, cj = Counter(h for h, _ in pairs), Counter(j for _, j in pairs)
    pe = sum((ch[l] / n) * (cj[l] / n) for l in labels)
    return po, (po - pe) / (1 - pe) if pe < 1 else 1.0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--human", required=True)
    ap.add_argument("--judge", required=True)
    ap.add_argument("--positive", default="pass")
    ap.add_argument("--floor", type=float, default=0.8, help="0.67 diagnostic use, 0.8 gate (default), 0.9 where a wrong grade harms a user")
    a = ap.parse_args()

    H, J = load(a.human), load(a.judge)
    common = sorted(set(H) & set(J))
    if len(common) < 50:
        print(f"CANNOT-MEASURE: only {len(common)} shared ids; a calibration set this small is anecdote, not agreement.", file=sys.stderr); sys.exit(2)
    missing = (set(H) | set(J)) - set(common)
    pairs = [(H[i], J[i]) for i in common]
    po, k = kappa(pairs)
    pos = a.positive.lower()
    tp = sum(1 for h, j in pairs if h == pos and j == pos)
    fp = sum(1 for h, j in pairs if h != pos and j == pos)
    fn = sum(1 for h, j in pairs if h == pos and j != pos)
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    base_rate = sum(1 for h, _ in pairs if h == pos) / len(pairs)

    print(f"n {len(common)} shared items" + (f" ({len(missing)} unmatched ids ignored)" if missing else ""))
    print(f"human positive rate {base_rate:.3f}   judge positive rate {sum(1 for _, j in pairs if j == pos)/len(pairs):.3f}")
    print(f"raw agreement {po:.3f}   (inflated by class imbalance; do not use for the decision)")
    print(f"Cohen's kappa {k:.3f}   floor {a.floor}")
    print(f"judge PASS precision {prec:.3f}   recall {rec:.3f}   (vs human PASS)")
    dis = [i for i, (h, j) in zip(common, pairs) if h != j]
    if dis:
        print("disagreements (first 20): " + ", ".join(dis[:20]))
    if k >= a.floor:
        print("OK: judge meets the floor on this set; pin model + prompt hash in the manifest.")
        sys.exit(0)
    print("BELOW FLOOR: judge is a diagnostic, not a grader. Inspect disagreements, fix rubric or guideline, re-run on the held-out slice.")
    sys.exit(1)


if __name__ == "__main__":
    main()
