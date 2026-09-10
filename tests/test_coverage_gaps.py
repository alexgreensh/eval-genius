import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "eval-genius" / "scripts"


class CLITest(unittest.TestCase):
    """Copy of the CLITest helper pattern from tests/test_scripts.py."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, data):
        path = self.dir / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def cli(self, script, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / script), *map(str, args)],
            text=True, capture_output=True,
        )

    @staticmethod
    def gate(items, *, fixture="fixture-1", live="passed", control="bad"):
        return {
            "manifest": {"fixture_hash": fixture, "liveness": live,
                         "negative_control_id": control},
            "items": items,
        }

    def write_jsonl(self, name, records):
        """Write one JSON object per line (JSONL). ``records`` is a list of dicts."""
        path = self.dir / name
        path.write_text(
            "\n".join(json.dumps(rec) for rec in records) + "\n",
            encoding="utf-8",
        )
        return path


class CoverageGapTest(CLITest):
    """New coverage for five gaps not exercised by tests/test_scripts.py."""

    # (1) --layer filtering interacts with the negative control: only items whose
    # 'layer' field matches are compared, but the control is still enforced.
    def test_gate_layer_filters_items_but_control_still_enforced(self):
        def items():
            return [
                {"id": "bad", "verdict": "fail"},
                {"id": "d1", "verdict": "pass", "layer": "deterministic"},
                {"id": "d2", "verdict": "fail", "layer": "deterministic"},
                {"id": "n1", "verdict": "pass", "layer": "nondeterministic"},
            ]
        a = self.write("a.json", self.gate(items()))
        # Treatment regresses n1 (nondeterministic layer); with --layer deterministic
        # that regression must be ignored, and the control must still be enforced.
        treat = self.gate(items())
        for it in treat["items"]:
            if it["id"] == "n1":
                it["verdict"] = "fail"
        b = self.write("b.json", treat)

        result = self.cli("check_gate.py", "--baseline", a, "--treatment", b,
                          "--layer", "deterministic")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("items 2", result.stdout)

        # Without --layer the n1 regression is visible and the gate fails.
        result_all = self.cli("check_gate.py", "--baseline", a, "--treatment", b)
        self.assertEqual(result_all.returncode, 1, result_all.stderr + result_all.stdout)
        self.assertIn("items 3", result_all.stdout)

        # Control that passes must still fail the gate even with --layer active.
        bad_control = self.gate(items())
        bad_control_treat = self.gate(items())
        for coll in (bad_control["items"], bad_control_treat["items"]):
            for it in coll:
                if it["id"] == "bad":
                    it["verdict"] = "pass"
        ca = self.write("ca.json", bad_control)
        cb = self.write("cb.json", bad_control_treat)
        result_bad = self.cli("check_gate.py", "--baseline", ca, "--treatment", cb,
                              "--layer", "deterministic")
        self.assertEqual(result_bad.returncode, 2, result_bad.stderr)
        self.assertIn("negative control", result_bad.stderr)

    # (2) JSONL input: manifest line then item lines accepted by check_gate.py,
    # and JSONL accepted by paired_bootstrap.py.
    def test_gate_accepts_jsonl_manifest_then_items(self):
        manifest = {"fixture_hash": "fixture-1", "liveness": "passed",
                    "negative_control_id": "bad"}
        records = [manifest,
                   {"id": "bad", "verdict": "fail"},
                   {"id": "x", "verdict": "pass"}]
        a = self.write_jsonl("a.jsonl", records)
        b = self.write_jsonl("b.jsonl", records)
        result = self.cli("check_gate.py", "--baseline", a, "--treatment", b)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("items 1", result.stdout)

    def test_bootstrap_accepts_jsonl(self):
        a = self.write_jsonl("a.jsonl", [{"id": "x", "score": 0},
                                         {"id": "y", "score": 1}])
        b = self.write_jsonl("b.jsonl", [{"id": "x", "score": 1},
                                         {"id": "y", "score": 1}])
        result = self.cli("paired_bootstrap.py", "--a", a, "--b", b, "--reps", "100")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("95% interval", result.stdout)

    # (3) judge_agreement.py exits 1 (not 0 or 2) when kappa is below the floor.
    def test_judge_below_kappa_floor_exits_1(self):
        # 50 shared ids; human alternates pass/fail; judge flips the first 20,
        # giving observed agreement 0.6 and kappa 0.2 (well below the 0.8 floor).
        human = {"items": [{"id": str(i), "label": "pass" if i % 2 == 0 else "fail"}
                           for i in range(50)]}
        judge = {"items": []}
        for i, rec in enumerate(human["items"]):
            label = rec["label"]
            if i < 20:
                label = "fail" if label == "pass" else "pass"
            judge["items"].append({"id": rec["id"], "label": label})
        a = self.write("human.json", human)
        b = self.write("judge.json", judge)
        result = self.cli("judge_agreement.py", "--human", a, "--judge", b)
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertIn("BELOW FLOOR", result.stdout)
        self.assertNotIn("Traceback", result.stderr + result.stdout)

    # (4) paired_bootstrap.py seed determinism: same seed => identical printed
    # interval across two runs; different seeds can differ.
    def test_bootstrap_seed_determinism_and_seed_sensitivity(self):
        # Varied deltas so resampling is sensitive to the seed.
        a_data = {"items": [{"id": str(i), "score": 0} for i in range(30)]}
        b_data = {"items": [{"id": str(i), "score": i} for i in range(30)]}
        a = self.write("a.json", a_data)
        b = self.write("b.json", b_data)

        run1 = self.cli("paired_bootstrap.py", "--a", a, "--b", b,
                        "--reps", "2000", "--seed", "42")
        run2 = self.cli("paired_bootstrap.py", "--a", a, "--b", b,
                        "--reps", "2000", "--seed", "42")
        self.assertEqual(run1.returncode, 0, run1.stderr)
        self.assertEqual(run1.stdout, run2.stdout)

        # Different seeds should be able to produce different intervals.
        intervals = set()
        for seed in range(8):
            r = self.cli("paired_bootstrap.py", "--a", a, "--b", b,
                         "--reps", "2000", "--seed", str(seed))
            self.assertEqual(r.returncode, 0, r.stderr)
            interval_line = [ln for ln in r.stdout.splitlines()
                             if "95% interval" in ln][0]
            intervals.add(interval_line)
        self.assertGreater(len(intervals), 1,
                           "different seeds produced identical intervals: "
                           + repr(sorted(intervals)))

    # (5) judge_agreement.py custom --labels and --positive vocabularies.
    def test_judge_custom_labels_and_positive(self):
        # 50 shared ids with good/bad; judge flips one item so kappa is defined
        # (expected != 1) yet well above the floor (kappa ~0.96).
        human = {"items": [{"id": str(i), "label": "good" if i % 2 == 0 else "bad"}
                           for i in range(50)]}
        judge = {"items": []}
        for i, rec in enumerate(human["items"]):
            label = rec["label"]
            if i == 0:
                label = "bad"
            judge["items"].append({"id": rec["id"], "label": label})
        a = self.write("human.json", human)
        b = self.write("judge.json", judge)

        result = self.cli("judge_agreement.py", "--human", a, "--judge", b,
                          "--labels", "good,bad", "--positive", "good")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("OK", result.stdout)

        # Default (pass,fail) vocabulary must reject good/bad labels.
        result_default = self.cli("judge_agreement.py", "--human", a, "--judge", b)
        self.assertEqual(result_default.returncode, 2, result_default.stderr)
        self.assertNotIn("Traceback", result_default.stderr)


if __name__ == "__main__":
    unittest.main()
