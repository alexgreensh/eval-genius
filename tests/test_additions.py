"""Tests for the additions in this change: hash_fixture.py and the judge-hash
consistency check in check_gate.py. Kept in a separate module from test_scripts.py."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "eval-genius" / "scripts"


class Base(unittest.TestCase):
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


class HashFixtureTest(Base):
    def items(self):
        return [{"id": "a", "input": "x"}, {"id": "b", "input": "y"}]

    def test_prints_sha256_prefixed(self):
        p = self.write("f.json", {"items": self.items()})
        out = self.cli("hash_fixture.py", p)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertTrue(out.stdout.strip().startswith("sha256:"))
        self.assertEqual(len(out.stdout.strip().split(":")[1]), 64)

    def test_raw_flag_drops_prefix(self):
        p = self.write("f.json", {"items": self.items()})
        prefixed = self.cli("hash_fixture.py", p).stdout.strip()
        raw = self.cli("hash_fixture.py", p, "--raw").stdout.strip()
        self.assertEqual(prefixed, f"sha256:{raw}")

    def test_record_order_does_not_change_hash(self):
        a = self.write("a.json", {"items": self.items()})
        b = self.write("b.json", {"items": list(reversed(self.items()))})
        self.assertEqual(self.cli("hash_fixture.py", a).stdout,
                         self.cli("hash_fixture.py", b).stdout)

    def test_key_order_and_whitespace_do_not_change_hash(self):
        a = self.dir / "a.json"
        a.write_text('{"items":[{"id":"a","input":"x"}]}', encoding="utf-8")
        b = self.dir / "b.json"
        b.write_text('{\n  "items": [ {\n    "input": "x",\n    "id": "a"\n  } ]\n}\n', encoding="utf-8")
        self.assertEqual(self.cli("hash_fixture.py", a).stdout,
                         self.cli("hash_fixture.py", b).stdout)

    def test_json_doc_and_jsonl_agree(self):
        doc = self.write("doc.json", {"items": self.items()})
        jsonl = self.dir / "f.jsonl"
        jsonl.write_text("\n".join(json.dumps(r) for r in self.items()), encoding="utf-8")
        self.assertEqual(self.cli("hash_fixture.py", doc).stdout,
                         self.cli("hash_fixture.py", jsonl).stdout)

    def test_different_content_different_hash(self):
        a = self.write("a.json", {"items": self.items()})
        b = self.write("b.json", {"items": [{"id": "a", "input": "CHANGED"}, {"id": "b", "input": "y"}]})
        self.assertNotEqual(self.cli("hash_fixture.py", a).stdout,
                            self.cli("hash_fixture.py", b).stdout)

    def test_missing_file_is_error_exit_2(self):
        out = self.cli("hash_fixture.py", self.dir / "nope.json")
        self.assertEqual(out.returncode, 2)
        self.assertIn("not found", out.stderr)

    def test_non_json_is_error_exit_2(self):
        p = self.dir / "bad.txt"
        p.write_text("not json at all", encoding="utf-8")
        self.assertEqual(self.cli("hash_fixture.py", p).returncode, 2)


class JudgeHashConsistencyTest(Base):
    @staticmethod
    def gate(judge=None, layer=None):
        manifest = {"fixture_hash": "fx", "liveness": "passed", "negative_control_id": "bad"}
        if judge is not None:
            manifest["judge"] = judge
        item = {"id": "ok", "verdict": "pass"}
        if layer is not None:
            item["layer"] = layer
        return {"manifest": manifest,
                "items": [{"id": "bad", "verdict": "fail", "layer": "deterministic"}, item]}

    def run_gate(self, base_judge, treat_judge):
        a = self.write("a.json", self.gate(base_judge))
        b = self.write("b.json", self.gate(treat_judge))
        return self.cli("check_gate.py", "--baseline", a, "--treatment", b)

    def test_matching_prompt_hash_passes(self):
        out = self.run_gate({"prompt_hash": "h1"}, {"prompt_hash": "h1"})
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_mismatched_prompt_hash_is_cannot_measure(self):
        out = self.run_gate({"prompt_hash": "h1"}, {"prompt_hash": "h2"})
        self.assertEqual(out.returncode, 2)
        self.assertIn("judge prompt_hash differs", out.stderr)

    def test_mismatched_model_snapshot_is_cannot_measure(self):
        out = self.run_gate({"model_snapshot": "m1"}, {"model_snapshot": "m2"})
        self.assertEqual(out.returncode, 2)
        self.assertIn("judge model_snapshot differs", out.stderr)

    def test_absent_judge_block_is_skipped(self):
        self.assertEqual(self.run_gate(None, None).returncode, 0)

    def test_one_sided_judge_field_is_cannot_measure(self):
        out = self.run_gate({"prompt_hash": "h1"}, {"prompt_hash": None})
        self.assertEqual(out.returncode, 2)
        self.assertIn("judge prompt_hash differs or is missing on one arm", out.stderr)

    def test_one_sided_judge_block_is_cannot_measure(self):
        out = self.run_gate({"model_snapshot": "judge-v1"}, None)
        self.assertEqual(out.returncode, 2)
        self.assertIn("judge model_snapshot differs or is missing on one arm", out.stderr)

    def test_judged_items_require_both_fingerprints(self):
        for judge in (None, {}, {"prompt_hash": "prompt-only"},
                      {"model_snapshot": "model-only"},
                      {"prompt_hash": "   ", "model_snapshot": "judge-v1"}):
            with self.subTest(judge=judge):
                a = self.write("a.json", self.gate(judge, layer="judged"))
                b = self.write("b.json", self.gate(judge, layer="judged"))
                out = self.cli("check_gate.py", "--baseline", a, "--treatment", b)
                self.assertEqual(out.returncode, 2)
                self.assertIn("judged items require a non-empty judge", out.stderr)

    def test_judged_items_pass_with_pinned_fingerprints(self):
        judge = {"prompt_hash": "sha256:prompt", "model_snapshot": "judge-v1"}
        a = self.write("a.json", self.gate(judge, layer="judged"))
        b = self.write("b.json", self.gate(judge, layer="judged"))
        out = self.cli("check_gate.py", "--baseline", a, "--treatment", b)
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_deterministic_items_do_not_require_judge_fingerprints(self):
        a = self.write("a.json", self.gate(None, layer="deterministic"))
        b = self.write("b.json", self.gate(None, layer="deterministic"))
        out = self.cli("check_gate.py", "--baseline", a, "--treatment", b)
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_judged_items_outside_selected_layer_do_not_require_fingerprints(self):
        data = self.gate(None, layer="judged")
        data["items"].append({"id": "det", "verdict": "pass", "layer": "deterministic"})
        a = self.write("a.json", data)
        b = self.write("b.json", data)
        out = self.cli("check_gate.py", "--baseline", a, "--treatment", b, "--layer", "deterministic")
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_malformed_judge_metadata_is_cannot_measure(self):
        out = self.run_gate(["not", "an", "object"], None)
        self.assertEqual(out.returncode, 2)
        self.assertIn("judge metadata must be an object or null", out.stderr)


class RunManifestTemplateTest(Base):
    def test_shipped_template_matches_gate_contract(self):
        template = json.loads((ROOT / "skills" / "eval-genius" / "templates" / "run-manifest.json").read_text(encoding="utf-8"))
        self.assertIn("manifest", template)
        self.assertIn("items", template)
        for field in ("fixture_hash", "liveness", "negative_control_id"):
            self.assertIn(field, template["manifest"])
        template["manifest"]["fixture_hash"] = "sha256:test-fixture"
        template["manifest"]["liveness"] = "passed"
        template["manifest"]["negative_control_id"] = "known-bad-item-id"
        template["manifest"]["judge"] = {"model_snapshot": None, "prompt_hash": None}
        template["items"].append({"id": "case-1", "verdict": "pass", "score": 1.0, "layer": "deterministic", "error": None})
        baseline = self.write("template-baseline.json", template)
        treatment = self.write("template-treatment.json", template)
        out = self.cli("check_gate.py", "--baseline", baseline, "--treatment", treatment)
        self.assertEqual(out.returncode, 0, out.stderr)


if __name__ == "__main__":
    unittest.main()
