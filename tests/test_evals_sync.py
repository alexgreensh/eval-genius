"""Sync test: every evals.json entry maps to exactly one trigger-* case dir, and
every trigger-* dir maps back to an entry. Stdlib only, no PyYAML, no model calls."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# skill-creator's trigger file stays under the skill; the plugin-eval case dirs
# live at repo-root evals/ (the runner refuses experimental.evals inside skills/).
EVALS_JSON = ROOT / "skills" / "eval-genius" / "evals" / "evals.json"
CASES_DIR = ROOT / "evals"

TRIGGER_RE = re.compile(r"^trigger-\d{2}-.+$")


def parse_frontmatter(text):
    """Split on the first two `---` lines. Return (frontmatter_str, body_str)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise AssertionError("missing opening ---")
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        raise AssertionError("missing closing ---")
    fm = "\n".join(lines[1:end])
    body = "\n".join(lines[end + 1:]).strip()
    return fm, body


def parse_kv(frontmatter):
    """Tiny hand-rolled YAML-ish parser for `key: value` lines (no nesting)."""
    out = {}
    for line in frontmatter.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        out[key.strip()] = val.strip()
    return out


class EvalsSyncTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = json.loads(EVALS_JSON.read_text())
        cls.trigger_dirs = sorted(
            d for d in CASES_DIR.iterdir()
            if d.is_dir() and TRIGGER_RE.match(d.name)
        )

    def test_case_count_matches_evals_json(self):
        self.assertEqual(len(self.entries), 21)
        self.assertEqual(len(self.trigger_dirs), 21)
        self.assertEqual(len(self.trigger_dirs), len(self.entries))

    def test_trigger_true_false_counts(self):
        true = sum(1 for e in self.entries if e["should_trigger"])
        false = sum(1 for e in self.entries if not e["should_trigger"])
        self.assertEqual(true, 14)
        self.assertEqual(false, 7)

    def test_every_entry_has_matching_prompt_body(self):
        bodies = []
        for d in self.trigger_dirs:
            prompt = (d / "prompt.md").read_text()
            _, body = parse_frontmatter(prompt)
            bodies.append(body)
        # Each entry's query must appear exactly once among the prompt bodies.
        for entry in self.entries:
            matches = bodies.count(entry["query"])
            self.assertEqual(
                matches, 1,
                f"query not exactly once: {entry['query']!r} (count={matches})",
            )

    def test_no_orphan_trigger_dirs(self):
        queries = {e["query"] for e in self.entries}
        for d in self.trigger_dirs:
            prompt = (d / "prompt.md").read_text()
            _, body = parse_frontmatter(prompt)
            self.assertIn(
                body, queries,
                f"orphan trigger dir {d.name}: prompt body not in evals.json",
            )

    def test_grader_frontmatter_matches_should_trigger(self):
        # Map query -> should_trigger for lookup by prompt body.
        by_query = {e["query"]: e["should_trigger"] for e in self.entries}
        for d in self.trigger_dirs:
            prompt = (d / "prompt.md").read_text()
            _, body = parse_frontmatter(prompt)
            should = by_query[body]
            grader = (d / "graders" / "skill-fired.md").read_text()
            fm, _ = parse_frontmatter(grader)
            kv = parse_kv(fm)
            self.assertEqual(kv.get("type"), "tool_used")
            self.assertEqual(kv.get("tool"), "Skill")
            if should:
                # Defaults: none of min/max/arm set.
                self.assertNotIn("min", kv, f"{d.name}: min set on true grader")
                self.assertNotIn("max", kv, f"{d.name}: max set on true grader")
                self.assertNotIn("arm", kv, f"{d.name}: arm set on true grader")
            else:
                self.assertEqual(kv.get("min"), "0", f"{d.name}: min != 0")
                self.assertEqual(kv.get("max"), "0", f"{d.name}: max != 0")
                self.assertEqual(kv.get("arm"), "both", f"{d.name}: arm != both")

    def test_quality_cases_are_wellformed(self):
        # The judge-scored quality cases (not in evals.json) must each have a prompt and
        # both a skill-fired (tool_used) and a quality (llm) grader.
        quality_dirs = sorted(
            d for d in CASES_DIR.iterdir()
            if d.is_dir() and d.name.startswith("quality-")
        )
        self.assertTrue(quality_dirs, "no quality-* cases found")
        for d in quality_dirs:
            self.assertTrue((d / "prompt.md").is_file(), f"{d.name}: no prompt.md")
            sf = parse_kv(parse_frontmatter((d / "graders" / "skill-fired.md").read_text())[0])
            self.assertEqual(sf.get("type"), "tool_used", f"{d.name}: skill-fired not tool_used")
            q = parse_kv(parse_frontmatter((d / "graders" / "quality.md").read_text())[0])
            self.assertEqual(q.get("type"), "llm", f"{d.name}: quality grader not llm")

    def test_ignores_quality_results_and_evals_json(self):
        # Sanity: quality-* and results dirs must not be counted as trigger dirs.
        names = {d.name for d in self.trigger_dirs}
        self.assertFalse(any(n.startswith("quality-") for n in names))
        self.assertNotIn("results", names)
        self.assertNotIn("evals.json", names)


if __name__ == "__main__":
    unittest.main()
