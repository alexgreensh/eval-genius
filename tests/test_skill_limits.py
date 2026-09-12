"""Locks the SKILL.md size caps: the file must stay under 150 lines and the
frontmatter description under 50 tokens (approximated as whitespace words x 1.3,
ceiling). Stdlib only, runs in the free test job."""
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_MD = ROOT / "skills" / "eval-genius" / "SKILL.md"

MAX_LINES = 149          # strictly under 150
MAX_DESC_TOKENS = 50     # description must not exceed this
WORD_TO_TOKEN = 1.3      # rough whitespace-word to token ratio


def parse_description(text):
    """Return the frontmatter `description` value (folded or inline scalar)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise AssertionError("SKILL.md missing opening frontmatter fence")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise AssertionError("SKILL.md missing closing frontmatter fence")
    fm = lines[1:end]
    for i, line in enumerate(fm):
        if not line.startswith("description:"):
            continue
        value = line.split(":", 1)[1].strip()
        if value not in (">-", ">", "|-", "|"):
            return value
        parts = []
        for cont in fm[i + 1:]:
            if cont.startswith((" ", "\t")):
                parts.append(cont.strip())
            else:
                break
        return " ".join(parts).strip()
    raise AssertionError("SKILL.md frontmatter has no description")


class SkillLimitsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SKILL_MD.read_text(encoding="utf-8")

    def test_skill_md_stays_under_150_lines(self):
        count = len(self.text.splitlines())
        self.assertLessEqual(
            count, MAX_LINES,
            f"SKILL.md is {count} lines; the cap is {MAX_LINES} (strictly under 150). "
            "Cut an equal amount elsewhere before adding.")

    def test_description_stays_under_50_tokens(self):
        desc = parse_description(self.text)
        words = len(desc.split())
        approx_tokens = math.ceil(words * WORD_TO_TOKEN)
        self.assertLessEqual(
            approx_tokens, MAX_DESC_TOKENS,
            f"description is ~{approx_tokens} tokens ({words} words); "
            f"the cap is {MAX_DESC_TOKENS}. Shorten the description.")


if __name__ == "__main__":
    unittest.main()
