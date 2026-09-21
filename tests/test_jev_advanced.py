"""Tests for the round-2 judged-lane scripts: jev_choice_route.py (three-way
routing for choice/score items on confidence or top-two margin),
jev_calibrate.py (temperature-scaling fit with ECE before/after), and the
batching plus escalation-tier additions to jev_cascade_cost.py. All are
deterministic and offline: no network, no model calls. Stdlib only."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "eval-genius" / "scripts"
CHOICE = SCRIPTS / "jev_choice_route.py"
COST = SCRIPTS / "jev_cascade_cost.py"
CALIB = SCRIPTS / "jev_calibrate.py"


def cli(script, *args, stdin=None):
    return subprocess.run(
        [sys.executable, str(script), *map(str, args)],
        input=stdin, text=True, capture_output=True,
    )


def jsonl(records):
    return "\n".join(json.dumps(record) for record in records) + "\n"


def choice_record(item_id, confidence=0.5, probabilities=None, answer=None,
                  item_type="choice"):
    record = {"id": item_id, "type": item_type, "confidence": confidence,
              "probabilities": probabilities if probabilities is not None
              else {"yes": 0.6, "no": 0.4}}
    if answer is not None:
        record["answer"] = answer
    return record


def calibration_records(n_per_level=10):
    # Perfectly calibrated by construction: at each raw level p the observed
    # frequency is exactly p, so the optimal temperature is ~1 and ECE ~0.
    records = []
    serial = 0
    for p10 in range(1, 10):
        for k in range(n_per_level):
            records.append({"id": f"i{serial}", "raw": p10 / 10,
                            "label": 1 if k < round(p10 * n_per_level / 10) else 0})
            serial += 1
    return records


class ChoiceRouteHappyPathTest(unittest.TestCase):
    def routes(self, stdin_text, *args):
        result = cli(CHOICE, *args, stdin=stdin_text)
        assert result.returncode == 0, result.stderr
        return result

    def test_three_way_split_by_confidence_and_summary(self):
        records = [
            choice_record("a", confidence=0.9, answer="yes"),
            choice_record("b", confidence=0.1, answer="no"),
            choice_record("c", confidence=0.5, answer="yes"),
        ]
        result = self.routes(jsonl(records))
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], "a\tyes\tauto-accept")
        self.assertEqual(lines[1], "b\tno\tauto-reject")
        self.assertEqual(lines[2], "c\tyes\tescalate")
        summary = lines[-1]
        self.assertIn("auto-accept 1", summary)
        self.assertIn("auto-reject 1", summary)
        self.assertIn("escalate 1", summary)
        self.assertIn("total 3", summary)

    def test_missing_answer_falls_back_to_argmax(self):
        records = [choice_record("x", confidence=0.9,
                                 probabilities={"cats": 0.3, "dogs": 0.7})]
        result = self.routes(jsonl(records))
        self.assertIn("x\tdogs\tauto-accept", result.stdout)

    def test_score_type_with_numeric_answer(self):
        records = [choice_record("s", confidence=0.9, answer=5,
                                 item_type="score",
                                 probabilities={"1": 0.1, "5": 0.9})]
        result = self.routes(jsonl(records))
        self.assertIn("s\t5\tauto-accept", result.stdout)

    def test_confidence_boundaries_escalate(self):
        # A value exactly on --low or --high is neither strictly below nor
        # strictly above: both default boundaries route to escalate.
        records = [choice_record("at-low", confidence=0.3),
                   choice_record("at-high", confidence=0.7)]
        result = self.routes(jsonl(records))
        self.assertIn("at-low\tyes\tescalate", result.stdout)
        self.assertIn("at-high\tyes\tescalate", result.stdout)

    def test_confidence_just_outside_boundaries(self):
        records = [choice_record("above-high", confidence=0.7000001),
                   choice_record("below-low", confidence=0.2999999)]
        result = self.routes(jsonl(records))
        self.assertIn("above-high\tyes\tauto-accept", result.stdout)
        self.assertIn("below-low\tyes\tauto-reject", result.stdout)

    def test_margin_mode_routes_on_top_two_gap(self):
        records = [
            choice_record("wide", confidence=0.5,
                          probabilities={"a": 0.9, "b": 0.1}),   # margin 0.8
            choice_record("tight", confidence=0.5,
                          probabilities={"a": 0.55, "b": 0.45}),  # margin 0.1
            choice_record("mid", confidence=0.5,
                          probabilities={"a": 0.7, "b": 0.3}),    # margin 0.4
        ]
        result = self.routes(jsonl(records), "--by", "margin")
        self.assertIn("wide\ta\tauto-accept", result.stdout)
        self.assertIn("tight\ta\tauto-reject", result.stdout)
        self.assertIn("mid\ta\tescalate", result.stdout)

    def test_margin_boundaries_escalate(self):
        # Dyadic probabilities so the margin lands exactly on the threshold.
        records = [
            choice_record("at-high", probabilities={"a": 0.875, "b": 0.125}),
            choice_record("at-low", probabilities={"a": 0.6875, "b": 0.3125}),
        ]
        result = self.routes(jsonl(records), "--by", "margin",
                             "--low", "0.375", "--high", "0.75")
        self.assertIn("at-high\ta\tescalate", result.stdout)
        self.assertIn("at-low\ta\tescalate", result.stdout)

    def test_margin_just_outside_boundaries(self):
        records = [
            choice_record("above-high", probabilities={"a": 0.9375, "b": 0.0625}),
            choice_record("below-low", probabilities={"a": 0.625, "b": 0.375}),
        ]
        result = self.routes(jsonl(records), "--by", "margin",
                             "--low", "0.375", "--high", "0.75")
        self.assertIn("above-high\ta\tauto-accept", result.stdout)
        self.assertIn("below-low\ta\tauto-reject", result.stdout)

    def test_single_label_probability_is_its_own_margin(self):
        # A one-label distribution must put all mass on it; margin = 1.0 - 0.0.
        records = [choice_record("solo", probabilities={"only": 1.0})]
        result = self.routes(jsonl(records), "--by", "margin")
        self.assertIn("solo\tonly\tauto-accept", result.stdout)

    def test_probability_sum_within_tolerance_accepted(self):
        records = [choice_record("loose", confidence=0.9,
                                 probabilities={"a": 0.69, "b": 0.3})]
        result = self.routes(jsonl(records))
        self.assertIn("loose\ta\tauto-accept", result.stdout)

    def test_input_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "answers.jsonl"
            path.write_text(jsonl([choice_record("a", confidence=0.9)]),
                            encoding="utf-8")
            result = cli(CHOICE, "--input", str(path))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("a\tyes\tauto-accept", result.stdout)

    def test_non_string_ids_and_answers(self):
        records = [choice_record(7, confidence=0.9, answer="yes"),
                   choice_record(None, confidence=0.1, answer="no"),
                   choice_record(["x", 1], confidence=0.5, answer="yes")]
        result = self.routes(jsonl(records))
        self.assertIn("7\tyes\tauto-accept", result.stdout)
        self.assertIn("null\tno\tauto-reject", result.stdout)
        self.assertIn('["x", 1]\tyes\tescalate', result.stdout)

    def test_blank_lines_skipped_and_empty_input_ok(self):
        result = self.routes(
            '\n\n{"id": "a", "type": "choice", "confidence": 0.5, '
            '"probabilities": {"x": 1.0}}\n\n')
        self.assertIn("a\tx\tescalate", result.stdout)
        empty = self.routes("")
        self.assertEqual(empty.returncode, 0)
        self.assertIn("total 0", empty.stdout)

    def test_json_output_shape(self):
        records = [choice_record("a", confidence=0.9, answer="yes"),
                   choice_record("b", confidence=0.5)]
        result = self.routes(jsonl(records), "--json")
        data = json.loads(result.stdout)
        self.assertEqual(len(data["routes"]), 2)
        self.assertEqual(data["routes"][0]["id"], "a")
        self.assertEqual(data["routes"][0]["answer"], "yes")
        self.assertEqual(data["routes"][0]["route"], "auto-accept")
        self.assertEqual(data["routes"][0]["value"], 0.9)
        self.assertEqual(data["summary"],
                         {"auto-accept": 1, "auto-reject": 0, "escalate": 1})
        self.assertEqual(data["by"], "confidence")
        self.assertEqual(data["thresholds"], {"low": 0.3, "high": 0.7})

    def test_help_exits_zero(self):
        self.assertEqual(cli(CHOICE, "--help", stdin="").returncode, 0)


class ChoiceRouteBadInputTest(unittest.TestCase):
    def test_malformed_json(self):
        result = cli(CHOICE, stdin="not-json\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("malformed JSON", result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_non_object_record(self):
        for line in ("[1,2]", "\"str\"", "42"):
            with self.subTest(line=line):
                self.assertNotEqual(cli(CHOICE, stdin=line + "\n").returncode, 0)

    def test_missing_fields(self):
        base = choice_record("a")
        for field in ("id", "type", "confidence", "probabilities"):
            with self.subTest(field=field):
                record = {k: v for k, v in base.items() if k != field}
                result = cli(CHOICE, stdin=jsonl([record]))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("missing", result.stderr)

    def test_bad_type_values(self):
        for bad in ("noul", "yesno", "CHOICE", 1, None, ["choice"]):
            with self.subTest(bad=bad):
                record = choice_record("a", item_type=bad)
                result = cli(CHOICE, stdin=jsonl([record]))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("type", result.stderr)

    def test_empty_probabilities_refused(self):
        record = choice_record("a", probabilities={})
        result = cli(CHOICE, stdin=jsonl([record]))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("non-empty", result.stderr)

    def test_probabilities_not_summing_to_one_refused(self):
        # Every individual value is in [0,1]; only the sum is off.
        for probabilities in ({"a": 0.5, "b": 0.4}, {"a": 0.9, "b": 0.6},
                              {"a": 0.3, "b": 0.3, "c": 0.3}):
            with self.subTest(probabilities=probabilities):
                record = choice_record("a", probabilities=probabilities)
                result = cli(CHOICE, stdin=jsonl([record]))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("sum", result.stderr)

    def test_probability_value_out_of_range(self):
        for probabilities in ({"a": 1.5, "b": -0.5}, {"a": "0.9", "b": 0.1},
                              {"a": True, "b": 1.0}, {"a": None, "b": 1.0}):
            with self.subTest(probabilities=probabilities):
                record = choice_record("a", probabilities=probabilities)
                result = cli(CHOICE, stdin=jsonl([record]))
                self.assertNotEqual(result.returncode, 0)

    def test_confidence_out_of_range(self):
        for confidence in ("-0.1", "1.1", "NaN", "Infinity"):
            with self.subTest(confidence=confidence):
                stdin = ('{"id": "a", "type": "choice", "confidence": '
                         + confidence + ', "probabilities": {"x": 1.0}}\n')
                result = cli(CHOICE, stdin=stdin)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("[0,1]", result.stderr)

    def test_confidence_wrong_type(self):
        for record in (choice_record("a", confidence="0.9"),
                       choice_record("a", confidence=True),
                       choice_record("a", confidence=None),
                       choice_record("a", confidence=[0.9])):
            with self.subTest(record=record):
                result = cli(CHOICE, stdin=jsonl([record]))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("must be a number", result.stderr)

    def test_low_above_high_refused(self):
        result = cli(CHOICE, "--low", "0.8", "--high", "0.2",
                     stdin=jsonl([choice_record("a")]))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--low", result.stderr)

    def test_thresholds_out_of_range(self):
        for flag, value in (("--low", "-0.1"), ("--low", "1.1"),
                            ("--high", "2"), ("--high", "nan")):
            with self.subTest(flag=flag, value=value):
                self.assertNotEqual(
                    cli(CHOICE, flag, value, stdin="").returncode, 0)

    def test_by_invalid_choice_refused(self):
        result = cli(CHOICE, "--by", "bogus", stdin="")
        self.assertNotEqual(result.returncode, 0)

    def test_duplicate_keys_refused(self):
        result = cli(CHOICE, stdin='{"id": "a", "id": "b", "type": "choice", '
                     '"confidence": 0.5, "probabilities": {"x": 1.0}}\n')
        self.assertNotEqual(result.returncode, 0)

    def test_tab_in_id_or_answer_refused(self):
        result = cli(CHOICE, stdin='{"id": "a\\tb", "type": "choice", '
                     '"confidence": 0.5, "probabilities": {"x": 1.0}}\n')
        self.assertNotEqual(result.returncode, 0)
        result = cli(CHOICE, stdin='{"id": "a", "type": "choice", '
                     '"confidence": 0.5, "probabilities": {"x": 1.0}, '
                     '"answer": "x\\ty"}\n')
        self.assertNotEqual(result.returncode, 0)

    def test_missing_input_file(self):
        result = cli(CHOICE, "--input", "/nonexistent/answers.jsonl")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not found", result.stderr)

    def test_no_traceback_on_bad_input(self):
        result = cli(CHOICE, stdin="garbage{{{")
        self.assertNotIn("Traceback", result.stdout + result.stderr)


class CascadeCostBatchingTest(unittest.TestCase):
    def test_batching_math_and_billed_tokens(self):
        # Q=3, S=4000, T=2000: unbatched 3*(4000+2000)=18000,
        # batched 4000+3*2000=10000; billed tokens are the batched figure.
        result = cli(COST, "--items", "1000", "--residue-rate", "0.1",
                     "--state-tokens", "4000", "--question-tokens", "2000",
                     "--questions-per-item", "3")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("unbatched tokens per item 18000", result.stdout)
        self.assertIn("batched tokens per item 10000", result.stdout)
        self.assertIn("savings 1.80x", result.stdout)
        self.assertIn("judged tokens 1000000", result.stdout)
        self.assertIn("projected cost $0.0420", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_batching_json_keys(self):
        result = cli(COST, "--items", "1000", "--residue-rate", "0.1",
                     "--state-tokens", "4000", "--question-tokens", "2000",
                     "--questions-per-item", "3", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["questions_per_item"], 3)
        self.assertEqual(data["unbatched_tokens_per_item"], 18000)
        self.assertEqual(data["batched_tokens_per_item"], 10000)
        self.assertEqual(data["token_savings_ratio"], 1.8)
        self.assertEqual(data["judged_tokens"], 1000000)

    def test_flat_model_unchanged_without_batching_flags(self):
        result = cli(COST, "--items", "100000", "--residue-rate", "0.05",
                     "--tokens-per-item", "2000")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("judged tokens 10000000", result.stdout)
        self.assertIn("projected cost $0.4200", result.stdout)
        self.assertNotIn("batched", result.stdout)

    def test_tokens_per_item_still_required_without_state_flags(self):
        result = cli(COST, "--items", "10", "--residue-rate", "0.5")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("tokens-per-item", result.stderr)

    def test_over_budget_batch_warns_but_succeeds(self):
        # S=50000, Q=4, T=5000 -> batched 70000 > 64000 request budget.
        result = cli(COST, "--items", "100", "--residue-rate", "0.5",
                     "--state-tokens", "50000", "--question-tokens", "5000",
                     "--questions-per-item", "4")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("batched tokens per item 70000", result.stdout)
        self.assertIn("64000", result.stderr)

    def test_state_and_question_tokens_must_be_given_together(self):
        for args in (("--state-tokens", "100"), ("--question-tokens", "100")):
            with self.subTest(args=args):
                result = cli(COST, "--items", "10", "--residue-rate", "0.5",
                             *args)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("together", result.stderr)

    def test_flat_and_batched_models_are_mutually_exclusive(self):
        result = cli(COST, "--items", "10", "--residue-rate", "0.5",
                     "--tokens-per-item", "100", "--state-tokens", "50",
                     "--question-tokens", "50")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not both", result.stderr)

    def test_questions_per_item_validation(self):
        for value in ("0", "-2", "1.5", "nan"):
            with self.subTest(value=value):
                result = cli(COST, "--items", "10", "--residue-rate", "0.5",
                             "--state-tokens", "50", "--question-tokens", "50",
                             "--questions-per-item", value)
                self.assertNotEqual(result.returncode, 0)

    def test_negative_or_zero_token_budget_refused(self):
        for s, t in (("-1", "50"), ("50", "-1"), ("0", "0")):
            with self.subTest(s=s, t=t):
                result = cli(COST, "--items", "10", "--residue-rate", "0.5",
                             "--state-tokens", s, "--question-tokens", t)
                self.assertNotEqual(result.returncode, 0)


class CascadeCostEscalationTest(unittest.TestCase):
    def test_escalation_additivity(self):
        # 5000 judged items; judge cost $0.42; escalation 5000*0.1*$0.5=$250.
        result = cli(COST, "--items", "100000", "--residue-rate", "0.05",
                     "--tokens-per-item", "2000", "--escalation-rate", "0.1",
                     "--escalation-cost-per-item", "0.5")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("projected cost $0.4200", result.stdout)
        self.assertIn("escalation cost $250.0000", result.stdout)
        self.assertIn("total cascade cost $250.4200", result.stdout)

    def test_escalation_json_additivity(self):
        result = cli(COST, "--items", "100000", "--residue-rate", "0.05",
                     "--tokens-per-item", "2000", "--escalation-rate", "0.1",
                     "--escalation-cost-per-item", "0.5", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["projected_cost_usd"], 0.42)
        self.assertEqual(data["escalation_cost_usd"], 250.0)
        self.assertAlmostEqual(
            data["total_cascade_cost_usd"],
            data["projected_cost_usd"] + data["escalation_cost_usd"])

    def test_escalation_off_by_default(self):
        result = cli(COST, "--items", "100", "--residue-rate", "0.5",
                     "--tokens-per-item", "100")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("escalation cost", result.stdout)
        self.assertNotIn("total cascade cost", result.stdout)
        data = json.loads(cli(COST, "--items", "100", "--residue-rate", "0.5",
                              "--tokens-per-item", "100", "--json").stdout)
        self.assertNotIn("total_cascade_cost_usd", data)

    def test_escalation_rate_out_of_range(self):
        for rate in ("-0.1", "1.1", "nan", "inf"):
            with self.subTest(rate=rate):
                result = cli(COST, "--items", "10", "--residue-rate", "0.5",
                             "--tokens-per-item", "5",
                             "--escalation-rate", rate)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("escalation-rate", result.stderr)

    def test_escalation_cost_per_item_negative_refused(self):
        result = cli(COST, "--items", "10", "--residue-rate", "0.5",
                     "--tokens-per-item", "5",
                     "--escalation-cost-per-item", "-1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("escalation-cost-per-item", result.stderr)


class CalibrateHappyPathTest(unittest.TestCase):
    def test_near_calibrated_data_fits_temperature_near_one(self):
        result = cli(CALIB, stdin=jsonl(calibration_records()))
        self.assertEqual(result.returncode, 0, result.stderr)
        data_line = [l for l in result.stdout.splitlines()
                     if l.startswith("temperature")][0]
        temperature = float(data_line.split()[1])
        self.assertGreaterEqual(temperature, 0.8)
        self.assertLessEqual(temperature, 1.25)
        self.assertIn("ECE before", result.stdout)
        self.assertIn("note:", result.stdout)

    def test_json_output_shape(self):
        result = cli(CALIB, "--json", stdin=jsonl(calibration_records()))
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["items"], 90)
        self.assertGreaterEqual(data["temperature"], 0.8)
        self.assertLessEqual(data["temperature"], 1.25)
        self.assertEqual(data["bins"], 10)
        self.assertIn("ece_before", data)
        self.assertIn("ece_after", data)
        self.assertIn("re-fit", data["note"])

    def test_overconfident_data_softens_and_improves_ece(self):
        # raw 0.9 but only half the labels are positive: the fit must soften
        # (T > 1) and the calibrated ECE must beat the raw one.
        records = [{"id": f"p{i}", "raw": 0.9, "label": 1} for i in range(50)]
        records += [{"id": f"n{i}", "raw": 0.9, "label": 0} for i in range(50)]
        result = cli(CALIB, "--json", stdin=jsonl(records))
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertGreater(data["temperature"], 1.0)
        self.assertLess(data["ece_after"], data["ece_before"])

    def test_extreme_raw_values_are_clamped_not_fatal(self):
        records = [{"id": f"z{i}", "raw": 0.0, "label": 0} for i in range(30)]
        records += [{"id": f"o{i}", "raw": 1.0, "label": 1} for i in range(30)]
        result = cli(CALIB, stdin=jsonl(records))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_input_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "calibration.jsonl"
            path.write_text(jsonl(calibration_records()), encoding="utf-8")
            result = cli(CALIB, "--input", str(path))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("items 90", result.stdout)

    def test_help_exits_zero(self):
        self.assertEqual(cli(CALIB, "--help", stdin="").returncode, 0)


class CalibrateBadInputTest(unittest.TestCase):
    def test_fewer_than_50_items_is_cannot_measure(self):
        records = [{"id": i, "raw": 0.5, "label": i % 2} for i in range(49)]
        result = cli(CALIB, stdin=jsonl(records))
        self.assertEqual(result.returncode, 2)
        self.assertIn("CANNOT-MEASURE", result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_empty_input_is_cannot_measure(self):
        result = cli(CALIB, stdin="")
        self.assertEqual(result.returncode, 2)
        self.assertIn("CANNOT-MEASURE", result.stderr)

    def test_label_outside_zero_one_is_cannot_measure(self):
        base = [{"id": i, "raw": 0.5, "label": i % 2} for i in range(50)]
        for bad_label in (2, -1, 0.5):
            with self.subTest(bad_label=bad_label):
                records = [dict(r) for r in base]
                records[0]["label"] = bad_label
                result = cli(CALIB, stdin=jsonl(records))
                self.assertEqual(result.returncode, 2)
                self.assertIn("CANNOT-MEASURE", result.stderr)

    def test_raw_out_of_range_is_cannot_measure(self):
        base = [{"id": i, "raw": 0.5, "label": i % 2} for i in range(50)]
        for bad_raw in (1.5, -0.1):
            with self.subTest(bad_raw=bad_raw):
                records = [dict(r) for r in base]
                records[0]["raw"] = bad_raw
                result = cli(CALIB, stdin=jsonl(records))
                self.assertEqual(result.returncode, 2)
                self.assertIn("CANNOT-MEASURE", result.stderr)

    def test_malformed_json_is_bad_input(self):
        result = cli(CALIB, stdin="not-json\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotEqual(result.returncode, 2)
        self.assertIn("malformed JSON", result.stderr)

    def test_non_object_and_missing_fields(self):
        self.assertNotEqual(cli(CALIB, stdin="[1,2]\n").returncode, 0)
        for record in ({"raw": 0.5, "label": 1}, {"id": "a", "label": 1},
                       {"id": "a", "raw": 0.5}):
            with self.subTest(record=record):
                result = cli(CALIB, stdin=jsonl([record]))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("missing", result.stderr)

    def test_wrong_types_refused(self):
        for record in ({"id": "a", "raw": "0.5", "label": 1},
                       {"id": "a", "raw": 0.5, "label": True},
                       {"id": "a", "raw": None, "label": 0}):
            with self.subTest(record=record):
                self.assertNotEqual(cli(CALIB, stdin=jsonl([record])).returncode, 0)

    def test_missing_input_file(self):
        result = cli(CALIB, "--input", "/nonexistent/calibration.jsonl")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not found", result.stderr)

    def test_no_traceback_on_bad_input(self):
        result = cli(CALIB, stdin="garbage{{{")
        self.assertNotIn("Traceback", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
