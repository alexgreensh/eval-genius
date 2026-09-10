import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skill" / "scripts"


class CLITest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, data):
        path = self.dir / name
        path.write_text(json.dumps(data))
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

    def test_gate_pass_uses_post_control_denominator(self):
        items = [{"id": "bad", "verdict": "fail"}, {"id": "ok", "verdict": "pass"}]
        a, b = self.write("a.json", self.gate(items)), self.write("b.json", self.gate(items))
        result = self.cli("check_gate.py", "--baseline", a, "--treatment", b)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("items 1", result.stdout)
        self.assertIn("baseline 1.0000  treatment 1.0000", result.stdout)
        self.assertIn("held 1", result.stdout)

    def test_gate_missing_file_is_cannot_measure(self):
        result = self.cli("check_gate.py", "--baseline", self.dir / "missing.json",
                          "--treatment", self.dir / "also-missing.json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("file not found", result.stderr)

    def test_gate_malformed_input_is_cannot_measure(self):
        bad = self.dir / "bad.json"
        bad.write_text("not-json")
        result = self.cli("check_gate.py", "--baseline", bad, "--treatment", bad)
        self.assertEqual(result.returncode, 2)
        self.assertIn("neither JSON", result.stderr)

    def test_gate_duplicate_id_is_cannot_measure(self):
        items = [{"id": "bad", "verdict": "fail"}, {"id": "x", "verdict": "pass"},
                 {"id": "x", "verdict": "fail"}]
        a, b = self.write("a.json", self.gate(items)), self.write("b.json", self.gate(items))
        result = self.cli("check_gate.py", "--baseline", a, "--treatment", b)
        self.assertEqual(result.returncode, 2)
        self.assertIn("duplicate item id", result.stderr)

    def test_gate_rejects_only_control(self):
        data = self.gate([{"id": "bad", "verdict": "fail"}])
        a, b = self.write("a.json", data), self.write("b.json", data)
        result = self.cli("check_gate.py", "--baseline", a, "--treatment", b)
        self.assertEqual(result.returncode, 2)
        self.assertIn("no scored items remain", result.stderr)

    def test_gate_fixture_mismatch(self):
        items = [{"id": "bad", "verdict": "fail"}, {"id": "x", "verdict": "pass"}]
        a = self.write("a.json", self.gate(items, fixture="a"))
        b = self.write("b.json", self.gate(items, fixture="b"))
        self.assertEqual(self.cli("check_gate.py", "--baseline", a, "--treatment", b).returncode, 2)

    def test_gate_liveness_failure(self):
        items = [{"id": "bad", "verdict": "fail"}, {"id": "x", "verdict": "pass"}]
        a = self.write("a.json", self.gate(items))
        b = self.write("b.json", self.gate(items, live="failed"))
        self.assertEqual(self.cli("check_gate.py", "--baseline", a, "--treatment", b).returncode, 2)

    def test_gate_item_set_mismatch(self):
        a_items = [{"id": "bad", "verdict": "fail"}, {"id": "x", "verdict": "pass"}]
        b_items = [{"id": "bad", "verdict": "fail"}, {"id": "y", "verdict": "pass"}]
        a, b = self.write("a.json", self.gate(a_items)), self.write("b.json", self.gate(b_items))
        self.assertEqual(self.cli("check_gate.py", "--baseline", a, "--treatment", b).returncode, 2)

    def test_gate_bad_negative_control(self):
        items = [{"id": "bad", "verdict": "pass"}, {"id": "x", "verdict": "pass"}]
        a, b = self.write("a.json", self.gate(items)), self.write("b.json", self.gate(items))
        self.assertEqual(self.cli("check_gate.py", "--baseline", a, "--treatment", b).returncode, 2)

    def test_gate_error_budget(self):
        items = [{"id": "bad", "verdict": "fail"}, {"id": "x", "verdict": "error"}]
        a, b = self.write("a.json", self.gate(items)), self.write("b.json", self.gate(items))
        self.assertEqual(self.cli("check_gate.py", "--baseline", a, "--treatment", b).returncode, 2)

    def test_gate_measured_regression_is_fail(self):
        a_items = [{"id": "bad", "verdict": "fail"}, {"id": "x", "verdict": "pass"}]
        b_items = [{"id": "bad", "verdict": "fail"}, {"id": "x", "verdict": "fail"}]
        a, b = self.write("a.json", self.gate(a_items)), self.write("b.json", self.gate(b_items))
        self.assertEqual(self.cli("check_gate.py", "--baseline", a, "--treatment", b).returncode, 1)

    def test_gate_rejects_invalid_numeric_options(self):
        items = [{"id": "bad", "verdict": "fail"}, {"id": "x", "verdict": "pass"}]
        a, b = self.write("a.json", self.gate(items)), self.write("b.json", self.gate(items))
        for flag, value in (("--tolerance", "1.1"), ("--error-budget", "-0.1"),
                            ("--max-regressions", "-1")):
            with self.subTest(flag=flag):
                self.assertEqual(self.cli("check_gate.py", "--baseline", a, "--treatment", b,
                                          flag, value).returncode, 2)

    def test_bootstrap_rejects_mismatched_item_sets(self):
        a_data = {"items": [{"id": "x", "score": 0}, {"id": "y", "score": 1}]}
        b_data = {"items": [{"id": "x", "score": 0}, {"id": "z", "score": 1}]}
        a, b = self.write("a.json", a_data), self.write("b.json", b_data)
        self.assertEqual(self.cli("paired_bootstrap.py", "--a", a, "--b", b).returncode, 1)

    def test_bootstrap_rejects_zero_reps_cleanly(self):
        data = {"items": [{"id": "x", "score": 0}, {"id": "y", "score": 1}]}
        a, b = self.write("a.json", data), self.write("b.json", data)
        result = self.cli("paired_bootstrap.py", "--a", a, "--b", b, "--reps", "0")
        self.assertEqual(result.returncode, 1)
        self.assertIn("--reps must be at least 1", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_bootstrap_rejects_duplicate_ids(self):
        dup = {"items": [{"id": "x", "score": 0}, {"id": "x", "score": 1}]}
        ok = {"items": [{"id": "x", "score": 0}, {"id": "y", "score": 1}]}
        a, b = self.write("a.json", dup), self.write("b.json", ok)
        result = self.cli("paired_bootstrap.py", "--a", a, "--b", b)
        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate item id", result.stderr)

    def test_bootstrap_rejects_cluster_mismatch(self):
        a_data = {"items": [{"id": "x", "score": 0, "cluster": "a"},
                             {"id": "y", "score": 1, "cluster": "b"}]}
        b_data = {"items": [{"id": "x", "score": 1, "cluster": "changed"},
                             {"id": "y", "score": 1, "cluster": "b"}]}
        a, b = self.write("a.json", a_data), self.write("b.json", b_data)
        result = self.cli("paired_bootstrap.py", "--a", a, "--b", b)
        self.assertEqual(result.returncode, 1)
        self.assertIn("cluster assignments differ", result.stderr)

    def test_bootstrap_valid_pair(self):
        a_data = {"items": [{"id": "x", "score": 0}, {"id": "y", "score": 1}]}
        b_data = {"items": [{"id": "x", "score": 1}, {"id": "y", "score": 1}]}
        a, b = self.write("a.json", a_data), self.write("b.json", b_data)
        self.assertEqual(self.cli("paired_bootstrap.py", "--a", a, "--b", b,
                                  "--reps", "100").returncode, 0)

    def test_judge_rejects_small_calibration_set(self):
        data = {"items": [{"id": str(i), "label": "pass"} for i in range(49)]}
        a, b = self.write("human.json", data), self.write("judge.json", data)
        self.assertEqual(self.cli("judge_agreement.py", "--human", a, "--judge", b).returncode, 2)

    def test_judge_rejects_duplicate_ids(self):
        dup = {"items": [{"id": "x", "label": "pass"}, {"id": "x", "label": "fail"}]}
        a, b = self.write("human.json", dup), self.write("judge.json", dup)
        result = self.cli("judge_agreement.py", "--human", a, "--judge", b)
        self.assertEqual(result.returncode, 2)
        self.assertIn("duplicate item id", result.stderr)

    def test_judge_rejects_invalid_floor(self):
        data = {"items": [{"id": str(i), "label": "pass"} for i in range(50)]}
        a, b = self.write("human.json", data), self.write("judge.json", data)
        result = self.cli("judge_agreement.py", "--human", a, "--judge", b, "--floor", "2")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--floor must be between -1 and 1", result.stderr)

    def test_judge_valid_agreement(self):
        data = {"items": [{"id": str(i), "label": "pass" if i % 2 else "fail"}
                          for i in range(50)]}
        a, b = self.write("human.json", data), self.write("judge.json", data)
        self.assertEqual(self.cli("judge_agreement.py", "--human", a, "--judge", b).returncode, 0)


if __name__ == "__main__":
    unittest.main()
