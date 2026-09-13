"""Tests for scripts/rate_interval.py: known Wilson bounds, edge behavior at
k = 0 and k = n, nonzero exits on bad input. Stdlib only, runs in the free job."""
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "eval-genius" / "scripts" / "rate_interval.py"

INTERVAL_RE = re.compile(r"\[(\d+\.\d+), (\d+\.\d+)\]")


def cli(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)],
        text=True, capture_output=True,
    )


def bounds(result):
    match = INTERVAL_RE.search(result.stdout)
    assert match, f"no interval in output: {result.stdout!r} {result.stderr!r}"
    return float(match.group(1)), float(match.group(2))


class WilsonKnownValuesTest(unittest.TestCase):
    # Reference values for the Wilson score interval at 95% confidence,
    # checked to four decimals against the published formula.
    def test_known_bounds(self):
        cases = [
            (5, 10, 0.2366, 0.7634),
            (0, 10, 0.0000, 0.2775),
            (10, 10, 0.7225, 1.0000),
            (1, 1, 0.2065, 1.0000),
            (31, 40, 0.6250, 0.8768),
        ]
        for k, n, low, high in cases:
            with self.subTest(k=k, n=n):
                result = cli("--k", k, "--n", n)
                self.assertEqual(result.returncode, 0, result.stderr)
                got_low, got_high = bounds(result)
                self.assertAlmostEqual(got_low, low, places=4)
                self.assertAlmostEqual(got_high, high, places=4)

    def test_point_estimate_printed(self):
        result = cli("--k", "15", "--n", "50")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("point estimate 0.3000", result.stdout)

    def test_edges_stay_inside_zero_one(self):
        for k, n in ((0, 1), (0, 5), (7, 7), (999, 1000), (1, 1000)):
            with self.subTest(k=k, n=n):
                low, high = bounds(cli("--k", k, "--n", n))
                self.assertGreaterEqual(low, 0.0)
                self.assertLessEqual(high, 1.0)

    def test_interval_narrows_as_n_grows(self):
        width_small = bounds(cli("--k", "5", "--n", "10"))
        width_large = bounds(cli("--k", "500", "--n", "1000"))
        self.assertLess(width_large[1] - width_large[0],
                        width_small[1] - width_small[0])

    def test_higher_confidence_widens(self):
        narrow = bounds(cli("--k", "5", "--n", "10", "--confidence", "0.90"))
        wide = bounds(cli("--k", "5", "--n", "10", "--confidence", "0.99"))
        self.assertGreater(wide[1] - wide[0], narrow[1] - narrow[0])

    def test_confidence_label_in_output(self):
        result = cli("--k", "5", "--n", "10", "--confidence", "0.99")
        self.assertIn("99% Wilson interval", result.stdout)
        result = cli("--k", "5", "--n", "10", "--confidence", "0.999")
        self.assertIn("99.9% Wilson interval", result.stdout)


class DegenerateInputTest(unittest.TestCase):
    def test_fractional_counts_refused(self):
        for k, n in (("31.5", "40"), ("31", "40.7"), ("31.5", "40.7"), ("0.5", "10")):
            with self.subTest(k=k, n=n):
                result = cli("--k", k, "--n", n)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("whole numbers", result.stderr)
                self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_whole_valued_floats_accepted(self):
        result = cli("--k", "31.0", "--n", "40.0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("point estimate 0.7750", result.stdout)

    def test_zero_width_interval_carries_caution(self):
        result = cli("--k", "31", "--n", "40", "--confidence", "1e-20")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("caution: the interval is a single point", result.stderr)
        self.assertIn("[0.7750, 0.7750]", result.stdout)

    def test_normal_confidence_is_silent(self):
        for confidence in ("0.90", "0.95", "0.99"):
            with self.subTest(confidence=confidence):
                result = cli("--k", "31", "--n", "40", "--confidence", confidence)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, "")


class BadInputTest(unittest.TestCase):
    def test_k_greater_than_n(self):
        self.assertNotEqual(cli("--k", "11", "--n", "10").returncode, 0)

    def test_zero_and_negative_n(self):
        for n in ("0", "-3"):
            with self.subTest(n=n):
                self.assertNotEqual(cli("--k", "1", "--n", n).returncode, 0)

    def test_negative_k(self):
        self.assertNotEqual(cli("--k", "-1", "--n", "10").returncode, 0)

    def test_confidence_out_of_range(self):
        for c in ("0", "1", "1.5", "-0.5"):
            with self.subTest(confidence=c):
                self.assertNotEqual(
                    cli("--k", "1", "--n", "2", "--confidence", c).returncode, 0)

    def test_nonfinite_values(self):
        for value in ("nan", "inf", "-inf"):
            with self.subTest(value=value):
                self.assertNotEqual(cli("--k", value, "--n", "10").returncode, 0)
                self.assertNotEqual(cli("--k", "1", "--n", value).returncode, 0)

    def test_non_numeric_and_missing_args(self):
        self.assertNotEqual(cli("--k", "abc", "--n", "10").returncode, 0)
        self.assertNotEqual(cli("--k", "5").returncode, 0)
        self.assertNotEqual(cli().returncode, 0)

    def test_no_traceback_on_bad_input(self):
        result = cli("--k", "11", "--n", "10")
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_help_exits_zero(self):
        self.assertEqual(cli("--help").returncode, 0)


if __name__ == "__main__":
    unittest.main()
