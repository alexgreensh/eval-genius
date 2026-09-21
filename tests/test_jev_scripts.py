"""Tests for the optional judged-lane scripts: jev_cascade_cost.py (cost
projection for the residue that reaches a decision-model judge) and
jev_confidence_route.py (three-way routing on the judge's `noul` confidence).
Both are deterministic and offline: no network, no model calls. Stdlib only,
runs in the free job."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "eval-genius" / "scripts"
COST = SCRIPTS / "jev_cascade_cost.py"
ROUTE = SCRIPTS / "jev_confidence_route.py"


def cli(script, *args, stdin=None):
    return subprocess.run(
        [sys.executable, str(script), *map(str, args)],
        input=stdin, text=True, capture_output=True,
    )


def jsonl(records):
    return "\n".join(json.dumps(record) for record in records) + "\n"


class CascadeCostHappyPathTest(unittest.TestCase):
    def test_known_cost(self):
        # 100000 items at 5% residue -> 5000 judged items x 2000 tokens
        # = 10M tokens at $42/Btok = $0.42.
        result = cli(COST, "--items", "100000", "--residue-rate", "0.05",
                     "--tokens-per-item", "2000")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("judged items 5000", result.stdout)
        self.assertIn("judged tokens 10000000", result.stdout)
        self.assertIn("projected cost $0.4200", result.stdout)
        self.assertIn("note:", result.stdout)

    def test_json_output(self):
        result = cli(COST, "--items", "1000", "--residue-rate", "0.1",
                     "--tokens-per-item", "500", "--price-per-btok", "30",
                     "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["judged_items"], 100)
        self.assertEqual(data["judged_tokens"], 50000)
        self.assertEqual(data["projected_cost_usd"], 0.0015)
        self.assertIn("escalation", data)

    def test_cost_rounds_to_four_decimals(self):
        result = cli(COST, "--items", "3", "--residue-rate", "1",
                     "--tokens-per-item", "1", "--price-per-btok", "1",
                     "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["projected_cost_usd"], round(3e-9, 4))

    def test_residue_rate_zero_judges_nothing(self):
        result = cli(COST, "--items", "100000", "--residue-rate", "0.0",
                     "--tokens-per-item", "2000")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("judged items 0", result.stdout)
        self.assertIn("projected cost $0.0000", result.stdout)

    def test_residue_rate_one_judges_everything(self):
        result = cli(COST, "--items", "50", "--residue-rate", "1.0",
                     "--tokens-per-item", "100")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("judged items 50", result.stdout)

    def test_zero_price_is_free(self):
        result = cli(COST, "--items", "100", "--residue-rate", "0.5",
                     "--tokens-per-item", "100", "--price-per-btok", "0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("projected cost $0.0000", result.stdout)

    def test_help_exits_zero(self):
        self.assertEqual(cli(COST, "--help").returncode, 0)


class CascadeCostBadInputTest(unittest.TestCase):
    def test_residue_rate_out_of_range(self):
        for rate in ("-0.1", "1.1", "nan", "inf"):
            with self.subTest(rate=rate):
                result = cli(COST, "--items", "10", "--residue-rate", rate,
                             "--tokens-per-item", "5")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("residue-rate", result.stderr)

    def test_nonpositive_items_and_tokens(self):
        for flag in ("--items", "--tokens-per-item"):
            for value in ("0", "-3"):
                with self.subTest(flag=flag, value=value):
                    args = {"--items": "10", "--tokens-per-item": "5"}
                    args[flag] = value
                    result = cli(COST, "--items", args["--items"],
                                 "--residue-rate", "0.5",
                                 "--tokens-per-item", args["--tokens-per-item"])
                    self.assertNotEqual(result.returncode, 0)

    def test_fractional_counts_refused(self):
        result = cli(COST, "--items", "10.5", "--residue-rate", "0.5",
                     "--tokens-per-item", "5")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("whole number", result.stderr)

    def test_negative_price_refused(self):
        result = cli(COST, "--items", "10", "--residue-rate", "0.5",
                     "--tokens-per-item", "5", "--price-per-btok", "-1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("price", result.stderr)

    def test_missing_and_non_numeric_args(self):
        self.assertNotEqual(cli(COST).returncode, 0)
        self.assertNotEqual(
            cli(COST, "--items", "abc", "--residue-rate", "0.5",
                "--tokens-per-item", "5").returncode, 0)

    def test_no_traceback_on_bad_input(self):
        result = cli(COST, "--items", "0", "--residue-rate", "2",
                     "--tokens-per-item", "5")
        self.assertNotIn("Traceback", result.stdout + result.stderr)


class ConfidenceRouteHappyPathTest(unittest.TestCase):
    def routes(self, stdin_text, *args):
        result = cli(ROUTE, *args, stdin=stdin_text)
        assert result.returncode == 0, result.stderr
        return result

    def test_three_way_split_and_summary(self):
        records = [{"id": "a", "noul": 0.9}, {"id": "b", "noul": 0.1},
                   {"id": "c", "noul": 0.5}]
        result = self.routes(jsonl(records))
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], "a\tauto-accept")
        self.assertEqual(lines[1], "b\tauto-reject")
        self.assertEqual(lines[2], "c\tescalate")
        summary = lines[-1]
        self.assertIn("auto-accept 1", summary)
        self.assertIn("auto-reject 1", summary)
        self.assertIn("escalate 1", summary)
        self.assertIn("total 3", summary)

    def test_boundaries_escalate(self):
        # noul exactly on --low or --high is neither strictly below nor
        # strictly above: both default boundaries route to escalate.
        records = [{"id": "at-low", "noul": 0.3}, {"id": "at-high", "noul": 0.7}]
        result = self.routes(jsonl(records))
        self.assertIn("at-low\tescalate", result.stdout)
        self.assertIn("at-high\tescalate", result.stdout)

    def test_just_outside_boundaries(self):
        records = [{"id": "above-high", "noul": 0.7000001},
                   {"id": "below-low", "noul": 0.2999999}]
        result = self.routes(jsonl(records))
        self.assertIn("above-high\tauto-accept", result.stdout)
        self.assertIn("below-low\tauto-reject", result.stdout)

    def test_extreme_confidence_values(self):
        records = [{"id": "sure", "noul": 1.0}, {"id": "hopeless", "noul": 0.0},
                   {"id": "int-one", "noul": 1}]
        result = self.routes(jsonl(records))
        self.assertIn("sure\tauto-accept", result.stdout)
        self.assertIn("hopeless\tauto-reject", result.stdout)
        self.assertIn("int-one\tauto-accept", result.stdout)

    def test_custom_thresholds(self):
        records = [{"id": "x", "noul": 0.5}, {"id": "y", "noul": 0.95},
                   {"id": "z", "noul": 0.05}]
        result = self.routes(jsonl(records), "--low", "0.1", "--high", "0.9")
        self.assertIn("x\tescalate", result.stdout)
        self.assertIn("y\tauto-accept", result.stdout)
        self.assertIn("z\tauto-reject", result.stdout)

    def test_equal_thresholds_is_a_single_boundary(self):
        records = [{"id": "on", "noul": 0.5}, {"id": "over", "noul": 0.5001}]
        result = self.routes(jsonl(records), "--low", "0.5", "--high", "0.5")
        self.assertIn("on\tescalate", result.stdout)
        self.assertIn("over\tauto-accept", result.stdout)

    def test_input_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scores.jsonl"
            path.write_text(jsonl([{"id": "a", "noul": 0.9}]), encoding="utf-8")
            result = cli(ROUTE, "--input", str(path))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("a\tauto-accept", result.stdout)

    def test_non_string_ids(self):
        records = [{"id": 7, "noul": 0.9}, {"id": None, "noul": 0.1},
                   {"id": ["x", 1], "noul": 0.5}]
        result = self.routes(jsonl(records))
        self.assertIn("7\tauto-accept", result.stdout)
        self.assertIn("null\tauto-reject", result.stdout)
        self.assertIn('["x", 1]\tescalate', result.stdout)

    def test_blank_lines_skipped_and_empty_input_ok(self):
        result = self.routes("\n\n{\"id\": \"a\", \"noul\": 0.5}\n\n")
        self.assertIn("a\tescalate", result.stdout)
        empty = self.routes("")
        self.assertEqual(empty.returncode, 0)
        self.assertIn("total 0", empty.stdout)

    def test_json_output_shape(self):
        records = [{"id": "a", "noul": 0.9}, {"id": "b", "noul": 0.5}]
        result = self.routes(jsonl(records), "--json")
        data = json.loads(result.stdout)
        self.assertEqual(len(data["routes"]), 2)
        self.assertEqual(data["routes"][0],
                         {"id": "a", "noul": 0.9, "route": "auto-accept"})
        self.assertEqual(data["summary"],
                         {"auto-accept": 1, "auto-reject": 0, "escalate": 1})
        self.assertEqual(data["thresholds"], {"low": 0.3, "high": 0.7})

    def test_help_exits_zero(self):
        self.assertEqual(cli(ROUTE, "--help", stdin="").returncode, 0)


class ConfidenceRouteBadInputTest(unittest.TestCase):
    def test_malformed_json(self):
        result = cli(ROUTE, stdin="not-json\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("malformed JSON", result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_non_object_record(self):
        for line in ("[1,2]", "\"str\"", "42"):
            with self.subTest(line=line):
                self.assertNotEqual(cli(ROUTE, stdin=line + "\n").returncode, 0)

    def test_missing_fields(self):
        for record in ({"noul": 0.5}, {"id": "a"}):
            with self.subTest(record=record):
                result = cli(ROUTE, stdin=jsonl([record]))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("missing", result.stderr)

    def test_noul_out_of_range(self):
        for noul in ("-0.1", "1.1", "NaN", "Infinity"):
            with self.subTest(noul=noul):
                stdin = f'{{"id": "a", "noul": {noul}}}\n'
                result = cli(ROUTE, stdin=stdin)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("[0,1]", result.stderr)

    def test_noul_wrong_type(self):
        for record in ({"id": "a", "noul": "0.9"}, {"id": "a", "noul": True},
                       {"id": "a", "noul": None}, {"id": "a", "noul": [0.9]}):
            with self.subTest(record=record):
                result = cli(ROUTE, stdin=jsonl([record]))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("must be a number", result.stderr)

    def test_low_above_high_refused(self):
        result = cli(ROUTE, "--low", "0.8", "--high", "0.2",
                     stdin=jsonl([{"id": "a", "noul": 0.5}]))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--low", result.stderr)

    def test_thresholds_out_of_range(self):
        for flag, value in (("--low", "-0.1"), ("--low", "1.1"),
                            ("--high", "2"), ("--high", "nan")):
            with self.subTest(flag=flag, value=value):
                self.assertNotEqual(
                    cli(ROUTE, flag, value, stdin="").returncode, 0)

    def test_duplicate_keys_refused(self):
        result = cli(ROUTE, stdin='{"id": "a", "noul": 0.5, "noul": 0.9}\n')
        self.assertNotEqual(result.returncode, 0)

    def test_id_with_tab_refused(self):
        result = cli(ROUTE, stdin='{"id": "a\\tb", "noul": 0.5}\n')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_missing_input_file(self):
        result = cli(ROUTE, "--input", "/nonexistent/scores.jsonl")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not found", result.stderr)

    def test_no_traceback_on_bad_input(self):
        result = cli(ROUTE, stdin="garbage{{{")
        self.assertNotIn("Traceback", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
