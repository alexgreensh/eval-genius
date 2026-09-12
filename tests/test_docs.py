"""Routing and docs integrity for skills/eval-genius:

(a) every references/, templates/, scripts/ path named in SKILL.md exists;
(b) every file under those dirs is routed from SKILL.md (directly, by a named
    ancestor directory, or as a backticked basename) or sits on a small
    allowlist with a reason, so orphans fail loudly;
(c) every reference file ends with an 'Output of this file' section;
(d) SKILL.md frontmatter carries name and description.

Stdlib only, runs in the free job."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "eval-genius"
SKILL_MD = SKILL_DIR / "SKILL.md"

ROUTED_DIRS = ("references", "templates", "scripts")
PATH_RE = re.compile(r"(?:references|templates|scripts)/[\w./-]+")
BACKTICK_RE = re.compile(r"`([^`\s]+)`")

# Files allowed to exist without a SKILL.md mention, with the reason they are
# still reachable. Anything not routed and not listed here is an orphan and
# fails the test.
ALLOWLIST = {
    "templates/error-analysis-log.md":
        "loaded from references/12-error-analysis.md, which is routed",
    "templates/run-manifest.json":
        "loaded from references/06-harness-design.md, which is routed",
}

# Sections allowed to sit after "## Output of this file" in a reference, with
# the reason. Anything else must keep Output last.
TRAILING_SECTIONS = {
    "## CI shell contract":
        "CI integration appendix kept after the output contract in "
        "07-gates-and-ci.md",
}


def mentioned_paths(text):
    return {match.group(0).rstrip(".,;:") for match in PATH_RE.finditer(text)}


# A bare top-level dir mention ("templates/", "scripts/") describes the
# collection in prose; it does not route the files inside. A mention of a
# subdirectory ("references/walkthroughs/") does route everything under it.
TOP_LEVEL_DIRS = {d + "/" for d in ROUTED_DIRS}


def is_routed(rel, name, mentioned, backticked):
    for entry in mentioned:
        if rel == entry:
            return True
        if entry.endswith("/") and entry not in TOP_LEVEL_DIRS \
                and rel.startswith(entry):
            return True
    return name in backticked


class DocsIntegrityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SKILL_MD.read_text(encoding="utf-8")
        cls.mentioned = mentioned_paths(cls.text)
        cls.backticked = set(BACKTICK_RE.findall(cls.text))

    def test_every_mentioned_path_exists(self):
        for rel in sorted(self.mentioned):
            with self.subTest(path=rel):
                self.assertTrue(
                    (SKILL_DIR / rel).exists(),
                    f"SKILL.md routes to {rel} but it does not exist on disk")

    def test_no_orphan_files(self):
        for subdir in ROUTED_DIRS:
            for path in sorted((SKILL_DIR / subdir).rglob("*")):
                if not path.is_file():
                    continue
                # Ignore build artifacts (CI runs py_compile before the tests, which
                # writes scripts/__pycache__/*.pyc); they are not shipped source.
                if "__pycache__" in path.parts or path.suffix == ".pyc":
                    continue
                rel = path.relative_to(SKILL_DIR).as_posix()
                with self.subTest(file=rel):
                    if is_routed(rel, path.name, self.mentioned, self.backticked):
                        continue
                    self.assertIn(
                        rel, ALLOWLIST,
                        f"orphan file {rel}: not routed from SKILL.md and not "
                        "on the allowlist with a reason")

    def test_allowlist_stays_current(self):
        for rel in ALLOWLIST:
            with self.subTest(file=rel):
                self.assertTrue(
                    (SKILL_DIR / rel).is_file(),
                    f"allowlisted {rel} no longer exists; remove the entry")

    def test_every_reference_ends_with_output_section(self):
        for path in sorted((SKILL_DIR / "references").rglob("*.md")):
            with self.subTest(file=path.name):
                headings = [line for line in
                            path.read_text(encoding="utf-8").splitlines()
                            if line.startswith("## ")]
                self.assertTrue(headings, f"{path.name} has no sections")
                self.assertIn(
                    "## Output of this file", headings,
                    f"{path.name} has no 'Output of this file' section")
                trailing = headings[headings.index("## Output of this file") + 1:]
                for heading in trailing:
                    self.assertIn(
                        heading, TRAILING_SECTIONS,
                        f"{path.name}: section {heading!r} follows 'Output of "
                        "this file' without an allowlist reason")

    def test_frontmatter_has_name_and_description(self):
        lines = self.text.splitlines()
        self.assertTrue(lines and lines[0].strip() == "---",
                        "SKILL.md missing opening frontmatter fence")
        end = next((i for i in range(1, len(lines))
                    if lines[i].strip() == "---"), None)
        self.assertIsNotNone(end, "SKILL.md missing closing frontmatter fence")
        keys = {line.split(":", 1)[0].strip()
                for line in lines[1:end] if ":" in line}
        self.assertIn("name", keys)
        self.assertIn("description", keys)


if __name__ == "__main__":
    unittest.main()
