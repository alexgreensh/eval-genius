#!/usr/bin/env python3
"""Compare a treatment run against a baseline run, per item, with a three-way outcome.

Exit codes (CI must honor all three):
  0  PASS            bar met on the same fixture with a live treatment arm
  1  FAIL            ran correctly, bar not met
  2  CANNOT-MEASURE  fingerprint mismatch, missing items, error budget blown,
                     liveness failed, negative control passed, bad input

Input: two files, each JSON {"manifest": {...}, "items": [{"id", "verdict", ...}]} or
JSONL whose first line is {"manifest": {...}} followed by one item record per line.
  manifest.fixture_hash        required, must match between runs
  manifest.liveness            required on treatment: "passed" | "failed" | "not-applicable"
  manifest.negative_control_id required unless --no-negative-control; that item must
                               have verdict "fail" in both runs (verify the verifier)
  items[].verdict              "pass" | "fail" | "error"

Usage:
  check_gate.py --baseline base.json --treatment treat.json [--tolerance 0.0]
                [--error-budget 0.02] [--layer deterministic]
  --tolerance     allowed drop in pass rate (0.0 = no aggregate regression)
  --max-regressions N   fail if more than N items flip pass->fail (default 0)
"""
import argparse, json, sys

PASS, FAIL, CANNOT = 0, 1, 2


def die(msg, code=CANNOT):
    print(f"CANNOT-MEASURE: {msg}" if code == CANNOT else msg, file=sys.stderr)
    sys.exit(code)


def load(path, role):
    try:
        text = open(path).read().strip()
    except FileNotFoundError:
        die(f"{role} file not found: {path}. Pass the per-item results JSON written by the scorer.")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # JSONL: first line {"manifest": {...}}, then one item record per line
        try:
            lines = [json.loads(l) for l in text.splitlines() if l.strip()]
            data = {"manifest": lines[0].get("manifest", lines[0]), "items": lines[1:]}
        except (json.JSONDecodeError, IndexError, AttributeError) as e:
            die(f"{role} file {path} is neither JSON {{'manifest','items'}} nor JSONL (manifest line then item lines) ({e}).")
    if not isinstance(data, dict) or "manifest" not in data or "items" not in data:
        die(f"{role} file {path} must be an object with 'manifest' and 'items' keys.")
    if "fixture_hash" not in data["manifest"]:
        die(f"{role} manifest has no 'fixture_hash'. Every run must record the fixture content hash; a run without one cannot be compared.")
    for it in data["items"]:
        if "id" not in it or it.get("verdict") not in ("pass", "fail", "error"):
            die(f"{role} item {it!r} needs an 'id' and a verdict in pass|fail|error.")
    return data


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--treatment", required=True)
    ap.add_argument("--tolerance", type=float, default=0.0)
    ap.add_argument("--max-regressions", type=int, default=0)
    ap.add_argument("--error-budget", type=float, default=0.02)
    ap.add_argument("--layer", default=None, help="only compare items whose 'layer' field equals this")
    ap.add_argument("--no-negative-control", action="store_true", help="waive the mandatory negative control (state the reason in the pre-registration)")
    a = ap.parse_args()

    base, treat = load(a.baseline, "baseline"), load(a.treatment, "treatment")

    bh, th = base["manifest"]["fixture_hash"], treat["manifest"]["fixture_hash"]
    if bh != th:
        die(f"fixture fingerprint mismatch: baseline={bh} treatment={th}. Runs on different fixtures are not comparable; re-run both on one fixture.")

    live = treat["manifest"].get("liveness")
    if live not in ("passed", "not-applicable"):
        die(f"treatment liveness is {live!r}; must be 'passed' or 'not-applicable'. Assert the arm under test is active before scoring.")

    bi = {i["id"]: i for i in base["items"] if a.layer is None or i.get("layer") == a.layer}
    ti = {i["id"]: i for i in treat["items"] if a.layer is None or i.get("layer") == a.layer}
    if not bi or not ti:
        die("no items to compare (check --layer or the items array).")
    if set(bi) != set(ti):
        only_b, only_t = sorted(set(bi) - set(ti))[:5], sorted(set(ti) - set(bi))[:5]
        die(f"item id sets differ (baseline-only e.g. {only_b}, treatment-only e.g. {only_t}). Both runs must cover the same items.")

    nc = treat["manifest"].get("negative_control_id") or base["manifest"].get("negative_control_id")
    if not nc and not a.no_negative_control:
        die("no negative_control_id in either manifest. Every gate run must include a known-bad item that the scorer fails; add one, or pass --no-negative-control to waive it with a written reason in the pre-registration.")
    if nc:
        if nc not in ti:
            die(f"negative control item {nc!r} missing from the run. The gate must exercise its known-bad case every run.")
        if ti[nc]["verdict"] != "fail" or bi[nc]["verdict"] != "fail":
            die(f"negative control {nc!r} did not fail (baseline={bi[nc]['verdict']}, treatment={ti[nc]['verdict']}). The scorer is not catching a known-bad case; nothing else in this run is trusted.")
        del bi[nc]; del ti[nc]

    n = len(ti)
    errs = sum(1 for i in ti.values() if i["verdict"] == "error")
    if n and errs / n > a.error_budget:
        die(f"{errs}/{n} treatment items errored ({errs/n:.1%}) > error budget {a.error_budget:.1%}. Fix the harness; a run with holes is not a scored run.")

    improved = sorted(i for i in ti if bi[i]["verdict"] != "pass" and ti[i]["verdict"] == "pass")
    regressed = sorted(i for i in ti if bi[i]["verdict"] == "pass" and ti[i]["verdict"] != "pass")
    bp = sum(1 for i in bi.values() if i["verdict"] == "pass") / n
    tp = sum(1 for i in ti.values() if i["verdict"] == "pass") / n

    print(f"fixture {th}  items {n}  errors {errs}")
    print(f"pass rate  baseline {bp:.4f}  treatment {tp:.4f}  delta {tp-bp:+.4f}")
    print(f"improved {len(improved)}  regressed {len(regressed)}  held {n-len(improved)-len(regressed)}")
    if regressed:
        print("regressed ids: " + ", ".join(regressed[:20]) + (" ..." if len(regressed) > 20 else ""))

    if len(regressed) > a.max_regressions:
        print(f"FAIL: {len(regressed)} regressions > allowed {a.max_regressions}")
        sys.exit(FAIL)
    if tp < bp - a.tolerance:
        print(f"FAIL: pass rate dropped {bp-tp:.4f} > tolerance {a.tolerance}")
        sys.exit(FAIL)
    print("PASS")
    sys.exit(PASS)


if __name__ == "__main__":
    main()
