# eval-genius v0.2 — Implementation Plan

**Date:** 2026-09-12 · **Repo state verified against:** `main @ a12b4b3` (v0.1.2)
**Inputs:** PLANNING-INPUT.local.md (mission + gap list), Instinct review A (Anthropic docs + landscape), Instinct review B (Product Talk / Torres). Every claim below was re-verified in this clone by grep + full read of SKILL.md, references 00–11, templates/, scripts/, tests/, .github/, .claude-plugin/.
**This document is a plan, not content.** Nothing under `skills/` has been modified.

---

## 0. Verified repo state (facts the plan stands on)

- `skills/eval-genius/SKILL.md` — 150 lines. Frontmatter `description` is the trigger surface. Body: Step 0 (need-an-eval + stage table) → route table (12 rows, one per reference) → Steps 1–6 → 11 named anti-patterns.
- `references/` — 12 files, 00–11, all read. Numbered, flat, each ends with "Output of this file".
- `templates/` — preregistration.md, benchmark-assessment-scorecard.md, eval-report.md, quality-checklist.md, run-manifest.json.
- `scripts/` — check_gate.py (verdicts `pass|fail|error` only, exits 0/1/2), paired_bootstrap.py (paired cluster bootstrap on `score`), judge_agreement.py (kappa + PASS precision/recall, floors, exits 0/1/2), hash_fixture.py (canonical sha256). All stdlib-only, all `--help`, all nonzero-on-bad-input. Confirmed by read + tests.
- `skills/eval-genius/evals/evals.json` — 21 trigger cases: 14 `should_trigger: true`, 7 `false`. **Nothing executes it.** No CI step, no script, no test consumes this file. It is currently unenforced data — the "protect triggering" guardrail is aspirational until P0 lands.
- `tests/` — 3 unittest modules + 6 fixtures. Strong adversarial coverage of the four scripts and a manifest-template↔gate-contract test. No test touches evals.json, SKILL.md link integrity, or reference files.
- `.github/workflows/test.yml` — one workflow, two jobs: `test` (py_compile + unittest + gate exit-code contract, 3 OSes) and `plugin` (manifest + SKILL.md frontmatter check). No eval run anywhere.
- `.claude-plugin/plugin.json` + `marketplace.json` — v0.1.2, tags v0.1.0–v0.1.2 exist. No CI check ties plugin.json version to git tag.
- README.md + 4 localized READMEs (es, ja, ko, zh-CN); METHODOLOGY.md English-only.
- Official runner docs re-fetched live during planning: `claude plugin eval` is GA (≥ v2.1.269); case-dir format, six grader types, WITH/W/OUT/Δ ablation, `expect:`-guarded MCP mocks with `.replay/`, `--max-cost-usd` → exit 2 `partial: true`, CI recipe — all as review A described. Doc explicitly confirms `evals/evals.json` (skill-creator format) is a *separate* format from plugin-eval case dirs.

---

## 1. Gap verification table

Verdicts: **CONFIRMED** (absent, worth adding) · **PARTIAL** (adjacent coverage exists, specific claim still missing) · **PRESENT** (already covered — protect, don't regress).

### Review A claims (Anthropic docs + landscape)

| # | Claim | Verdict | Evidence |
|---|-------|---------|----------|
| A0 | Dogfood `claude plugin eval`; evals.json is legacy format | **CONFIRMED** | No case dirs exist anywhere; docs state the formats are separate; nothing runs evals.json at all |
| A1 | Capability-vs-regression suite lifecycle + graduation | **CONFIRMED** | `graduate`/lifecycle absent. `saturation` exists only in 04-search-vs-build.md (benchmark adoption) and 09-reporting.md (retirement) — no concept of a task moving between suites |
| A2 | Partial credit / weighted graders | **CONFIRMED** | Zero hits for "partial credit"; `weighted` appears once re: strata. `check_gate.py` verdicts are strictly `pass|fail|error`; per-item `score` field exists and flows to paired_bootstrap — the reconciliation path already exists, it is just never taught |
| A3 | Grader hack-resistance (subject-side gaming) | **CONFIRMED** | "loophole", "gaming", "cheat" absent. Anti-patterns cover author-side cheating only (gate-set tuning, run-until-green). 02 does say "tests must be hidden" for code — one clause, not a treatment |
| A4 | Ablation arm as named comparison design | **CONFIRMED** | "ablation" absent. 06's liveness check proves the arm is *on* but never names "run without the component" as the control |
| A5 | Dependency mocks with contract-checked fakes + replay | **CONFIRMED** | "mock|stub|replay|fake" — zero hits in skills/. 06 covers fixture freezing but not dependency stubbing with input guards |
| A6 | Partial-results exclusion + cost ceilings in 07 | **CONFIRMED** | No "cost ceiling", "partial" result handling, or rate-limit-mid-suite discussion. 07 has error budgets per run but not suite-level partials |
| A7 | Transcript review as standing cadence in 11 | **CONFIRMED** | 11 has "reproduce one flipped item by hand" only; no read-N-transcripts-per-run practice. 10 actively says "transcript is not consulted for the outcome verdict" — the cadence must be framed as audit, not grading, to avoid contradicting it |
| A8 | Monitor-stage label loop in 03 | **CONFIRMED** | Monitor = "same scorer on sampled live traffic" (00, 01) and nothing more. No annotation-queue→label→recalibration loop |
| A9 | Trigger-F1 as a first-class eval category | **CONFIRMED** | "trigger" appears only in evals.json data. 02 has a "Classification / routing / triggering" metric table but no trigger-eval pattern (balanced should/shouldn't set, activation-rate CI, description as lever) |
| A10 | Ahead of field: three-way outcome, fixture fingerprinting, kappa calibration, paired bootstrap, negative control, baseline lifecycle | **PRESENT — verified** | 06 + check_gate.py (0/1/2, fingerprint refusal, liveness, negative control); 03 + judge_agreement.py (kappa, floors 0.67/0.8/0.9, held-out slice); 08 + paired_bootstrap.py (cluster-aware); 07 baseline promotion/re-baseline rules |
| A11 | Positioning: cite "invest in the evals themselves" + dead-framework receipts + runner-classes table | **CONFIRMED absent** from README/METHODOLOGY | No citations, no landscape table. Guardrail: stays out of `skills/` entirely |

### Review B claims (Product Talk / Torres)

| # | Claim | Verdict | Evidence |
|---|-------|---------|----------|
| B1 (D1) | Error analysis as generative origin of evals (traces→annotate→categorize→one eval per error→per-error scores) | **CONFIRMED** | "error analysis", "annotat" — zero hits. This is the largest confirmed gap: the skill's only entry is top-down promise-writing; nothing teaches bottom-up discovery of *what* to measure from real failures |
| B2 (D2) | Customer feedback as a fourth eval type, esp. implicit signals (regenerate, edit-then-regenerate, follow-up, edit-the-output) | **CONFIRMED** | "customer feedback|implicit|regenerat|thumbs" — zero hits. 02's grader catalog has no user-behavior family |
| B3 (D3) | Guardrail: third placement, inline before user sees output, with remediation path | **CONFIRMED** | "guardrail|inline" — zero hits. 01 §3 lists three placements (decision point / risky seam / public claim); none is "between system and user" |
| B4 (D4) | Cost cascade: cheap deterministic filter on every item, judge only suspects | **CONFIRMED** | "cascade" absent. 02 has "deterministic first" as *selection order*, not a runtime filter architecture |
| B5 (D5) | Eval-vs-human alignment for ALL eval types incl. code assertions + permanent drift-monitoring label stream | **PARTIAL** | 03 calibrates *judges*; 05 measures inter-annotator agreement on *labels*. Neither scores a code assertion against human labels nor prescribes a permanent sampled-trace labeling stream after alignment is achieved |
| B6 (D6) | "Don't aim for 100%" — error detector at 100% measures nothing; retire/refresh | **PARTIAL** | Retirement exists in 09 (saturated/contaminated/pointless), rotation in 05, saturation in 04. The error-detector-specific framing ("if the error isn't in your data, the eval measures nothing") is absent and sharper than what exists |
| B7 (D7) | PM / domain-expert audience underserved; needs plain-language error-analysis-first on-ramp | **CONFIRMED** | No persona routing anywhere. SKILL.md already says "plain language first" and 00 is beginner-readable — the voice is compatible — but there is no entry path for the reader who arrives with user complaints, not a promise |

### Gaps both reviews missed (fresh read)

| # | Gap | Why it matters |
|---|-----|----------------|
| M1 | **evals.json is dead data.** No CI job, script, or test executes the 21 trigger cases | The #1 guardrail ("protect triggering") has no enforcement mechanism *today*. This is sharper than review A's framing — P0 isn't just dogfooding for credibility, it creates the safety net every later SKILL.md edit requires. Sequencing consequence: P0 must land before any description/SKILL.md content edit |
| M2 | **No fork on *what is being evaluated*.** Step 0 forks on stage; the route table forks on job. The mission's three targets (one product step / the whole AI system / a benchmark) are never a first-class question | "All-encompassing" requires a "unit under test" fork: step → scoped eval; system → end-to-end + 10; benchmark candidate → 04. Belongs in 00's four forks; at most one line in SKILL.md |
| M3 | **No integrity test for the routing surface.** SKILL.md names 12 reference files, 5 templates, 4 scripts by path; nothing asserts they exist or that new files get routed | As references grow to 14+ files, link rot and un-routed orphans become likely. A stdlib unittest is nearly free |
| M4 | **No "evaluate my own skill/plugin" route row.** The dogfooded suite makes trigger-evals salient, but the skill can't route a user who asks "is my skill's description firing?" | Add exactly one route-table row when the trigger-eval content lands (P2), tested against the suite |
| M5 | **Localization drift.** 4 translated READMEs exist; any P3 positioning edit lands in English only | Sequence README.md first, batch translations as one follow-up, or mark them stale. Never edit five files in five passes |
| M6 | **evals/results/ will need gitignoring** when case dirs land | Official docs say add results to .gitignore. `.gitignore` already carries an uncommitted `*.local.md` line — leave that alone, append the results path in the dogfood PR |
| M7 | **A/B testing is deliberately out of scope** (evals.json shouldn't-trigger case: "A/B test for the new checkout button color") | The multi-method table (A's gap #4) must present A/B tests, user studies, and observability platforms as *adjacent methods the skill doesn't run*, or it silently expands the trigger surface and invites scope creep. The reviews missed this tension |
| M8 | **No version↔tag check.** plugin.json 0.1.2 matches tag v0.1.2 today by hand, not by CI | Small P3 hygiene item; the `plugin` job can assert tag==version on release events |

---

## 2. Restructure recommendation (the decision, not a list)

**Keep the top-down "promise" spine. Add a second front door, not a new spine.**

The promise-first spine is the skill's differentiator — the entire landscape review found nobody else occupying "should you measure this and what does the number permit you to claim." Replacing it with error-analysis-first would trade the moat for a commodity tutorial flow. But review B is right that error analysis is the missing *front half*: a user with a shipped system and a folder of bad outputs cannot start from "state the promise" — they don't know what's worth promising yet.

The two entries converge at the same place, which is what makes this clean: **an error category *is* a promise** — "the system does not produce output of failure-class X." Error analysis is how you discover promises from evidence; preregistration is where they get written down. The spine stays; the on-ramp widens.

Concretely:

1. **SKILL.md Step 0** gains one sentence — a fork on *what the user has in hand*: a promise to test → Step 1 as today; a live system and failures → the error-analysis path; a "what should I even measure" PM/domain question → the same error-analysis path in plainer words. One sentence, not a restructure. Plus one new route-table row for the new reference file. (Two small edits, both re-tested against the trigger suite.)
2. **New `references/12-error-analysis.md`** carries the whole bottom-up workflow: sample real traces (production > synthetic) → annotate failure modes free-form → categorize → prioritize by user impact → write one eval per error category → report per-error counts, not aggregates → the loop never ends (a fix surfaces the next error class). Includes Torres's citable corollary: vendor metrics measure the vendor's errors, not yours.
3. **Persona on-ramps live in `references/00-start-here.md`, not SKILL.md.** A three-bullet block at the top: *domain expert / PM* → start at error analysis, you own "what good looks like"; *engineer* → stage table as today; *researcher / comparing systems* → benchmark path via 04. This keeps SKILL.md's trigger surface stable while giving the "who are you" question a home. Mission-relevant: PMs are the underserved audience and the same "what's worth measuring" layer the skill already owns.
4. **`00`'s four forks gain a zeroth question**: "what is the unit under test — one step in the product, the whole system, or a benchmark claim?" — mapping to scoped eval / end-to-end + `10` / `04` respectively. This is the mission's three-target coverage made explicit.

Anti-bloat rule for all of it: SKILL.md changes are capped at the fork sentence + route rows + at most one stage-table row (guardrail placement, §3.4 below). Everything else loads on demand.

---

## 3. Sequenced backlog (P0 → P3)

Sizes: **S** < half a day · **M** ~a day · **L** 2+ days. Track: **senior** (voice/judgment-sensitive) or **GLM-5.2-on-Devin** (mechanical, spec'd tightly enough to delegate).

### P0 — Dogfood the official runner (safety net + credibility)

| ID | Change | Files | Acceptance criteria | Size | Track |
|----|--------|-------|---------------------|------|-------|
| P0-1 | Convert all 21 evals.json queries to plugin-eval case dirs. `should_trigger:true` → `prompt.md` (body = query verbatim, `max_turns`, `allowed_tools: [Read, Glob, Grep, Skill]`) + `graders/skill-fired.md` (`type: tool_used`, `tool: Skill`, `input_match` regex for `eval-genius` incl. namespaced form). `false` → same grader with `min: 0, max: 0` and `arm: both` so it scores in both arms | `skills/eval-genius/evals/<slug>/{prompt.md,graders/*.md}` ×21 | `claude plugin eval . --runs 1 --ablation none` completes; each true-case fires the skill, each false-case doesn't; evals.json (a file, not a case dir) is ignored by the loader — verified by a real run, not assumed | M | GLM (mechanical transform), senior spot-checks 3 cases |
| P0-2 | Point the runner at the suite: `"experimental": {"evals": "skills/eval-genius/evals"}` in plugin.json (suite travels with the copyable skill dir; alternative repo-root `evals/` rejected — it would strand the suite outside the skill) | `.claude-plugin/plugin.json` | `claude plugin eval .` from repo root finds the suite; `plugin` CI job still passes manifest validation | S | senior (manifest semantics) |
| P0-3 | Add 3 quality cases with `llm` rubric graders (these produce the headline Δ that trigger-only cases structurally can't — `tool_used: Skill` is excluded from scoring in two-arm mode): e.g. "do I need evals for my chatbot" graded on routes-to-stage-appropriate-answer; "is this delta real" graded on refuses-to-claim-without-interval; a shouldn't-trigger case graded on *does not pivot into eval design* | `skills/eval-genius/evals/quality-*/` | Rubrics written as concrete PASS/FAIL conditions; stable across 3 runs under pinned `--judge-model`; positive mean Δ on the with-arm | M | senior (rubric wording is judgment) |
| P0-4 | Sync guard: stdlib unittest asserting every evals.json entry maps to exactly one case dir whose prompt.md body matches the query verbatim, and `should_trigger:false` ⟺ grader has `min:0/max:0` | `tests/test_evals_sync.py` | Test fails if a case is added/renamed without updating evals.json and vice versa; runs in existing `test` job free (no model calls) | S | GLM |
| P0-5 | Eval CI workflow: separate `eval.yml` — `workflow_dispatch` + PRs touching `skills/eval-genius/SKILL.md`, `skills/eval-genius/evals/**`, `.claude-plugin/plugin.json`. Recipe per official docs: `--trust-plugin --json results.json --threshold 0.8 --model <pin> --judge-model <pin> --no-publish --max-cost-usd <cap>`; upload `results.json` + `report.html` as artifacts. Exit 1 → fail the job; exit 2 → CANNOT-MEASURE: warning annotation + partial results uploaded + **not** trended (per our own 06/07 philosophy and their guidance). PR runs advisory; a blocking run is reserved for pre-release dispatch | `.github/workflows/eval.yml` | Workflow runs green on a manual dispatch; exit-2 path exercised once and visibly marked unmeasured, not green | M | senior (CI + secrets) — **needs Alex: ANTHROPIC_API_KEY repo secret + cost ceiling number** |
| P0-6 | Housekeeping: add `skills/eval-genius/evals/results/` to .gitignore; keep evals.json as the human-readable source of truth the sync test enforces | `.gitignore` | `git status` clean after a local eval run | S | GLM |
| P0-7 | After ≥2 stable green runs: quote the measured Δ in README.md ("WITH/W/OUT/Δ on its own trigger + quality suite") with manifest links. Measured tier only — never estimate | `README.md` | Number in README traces to a committed results artifact; translations deferred to P3-M5 batch | S | senior |

### P1 — Content gaps (confirmed above)

Order matters: B1 first (front door), then grader-catalog items, then harness/CI items, then monitor/transcript, then walkthroughs last (they must teach settled content).

| ID | Change | Files | Acceptance criteria | Size | Track |
|----|--------|-------|---------------------|------|-------|
| P1-1 | **Error-analysis reference** (B1/D1, the front door): traces→annotate→categorize→prioritize-by-impact→one eval per error category→per-error scores; the-loop-never-ends; eval-authoring-as-rubric-clarification; "vendor metrics measure the vendor's errors." Ends by handing each error category to Step 1 preregistration as a promise | NEW `references/12-error-analysis.md`; SKILL.md (one route row + fork sentence); `00` (persona block + link) | File follows house format (ends "Output of this file"); route row phrasing doesn't disturb existing 12 rows; trigger suite re-run green (P0 gate); a new should-trigger case for "review my production failures" added to evals.json + case dir (sync test catches it) | L | senior |
| P1-2 | **Error-annotation template**: free-form failure-mode log → category table → eval-per-category worksheet. Field-minimal, spreadsheet-pasteable (PM audience, D7) | NEW `templates/error-analysis-log.md`; `12`; quality-checklist gains one box | Template referenced from 12 and routeable; checklist item added without breaking template-contract test | S | GLM from senior's field spec |
| P1-3 | **Unit-under-test fork + persona on-ramps + multi-method table** (M2, D7, A's Swiss-cheese): zeroth fork (step/system/benchmark); three persona bullets; adjacent-methods table (A/B, user studies, observability platforms labeled *not this skill* per M7) | `references/00-start-here.md` | A/B tests remain shouldn't-trigger in the suite; table names methods, not frameworks; file stays plain-language | M | senior |
| P1-4 | **Customer-feedback eval family** (D2): explicit vs implicit signals; implicit as labeled proxies (regenerate, edit-then-regenerate, follow-up = incomplete, edit-the-output = labeled diff); where it sits (monitor-stage input, feeds error analysis) | `references/02-grading-and-metrics.md` (new catalog family), `references/12` (cross-link) | Family slots into the existing fork table format; notes low-information caveat on explicit ratings | M | senior |
| P1-5 | **Cascade pattern** (D4): cheap deterministic filter on every item, judge only items that trip it; judge spend → near zero at volume; contrast with "deterministic first" selection rule already present | `references/02-grading-and-metrics.md` | One section, one worked shape (e.g., per-node-count filter → judged suspects); explicitly framed as runtime architecture, not selection preference | S | senior |
| P1-6 | **Partial credit / weighted scoring, reconciled** (A2): partial credit for capability measurement, binary verdicts for gates; the `score` field already carries it to paired_bootstrap; `check_gate.py` stays binary **by design** — say so | `references/02`, `references/08`; `check_gate.py` docstring one line | No script behavior change (verdict contract untouched); doc states which layer each tool serves | M | senior |
| P1-7 | **Ablation arm as named design** (A4): with-component vs without-component as control; generalizes liveness (prove arm on) to ablation (prove what arm contributes); canonical use = skill/plugin/prompt presence | `references/01` (levers), `references/06` (comparison designs) | Names the pattern once, teaches it, links liveness; no framework names | S | senior |
| P1-8 | **Dependency mocks + contract-checked fakes + replay** (A5): external deps stubbed with `expect:`-style input guards (the mock grades what the system *asked*); recorded answers replayed in CI for determinism; ties to fixture-freezing rules | `references/06` new subsection | Taught harness-agnostically (pattern, not the plugin runner's syntax); cross-links per-trial isolation | M | senior |
| P1-9 | **Grader hack-resistance** (A3): subject-side gaming — hidden tests stay hidden, grade outcomes not intentions, "passed by loophole" is a task-spec bug (fix the spec, not the score), reward-hunting as an anti-pattern | `references/05` or `06` (decide at write time: 05 task-admission is the better home — loophole = under-specified prompt variant); SKILL.md anti-patterns list gains at most one entry | One paragraph + anti-pattern entry; τ2-bench-style anecdote told generically inside skills/ | S | senior |
| P1-10 | **Suite lifecycle + graduation** (A1 + B6 merged): capability suite (low pass, a hill to climb) vs regression suite (near-100%); saturated items graduate; an error-detector at 100% measures nothing → retire/refresh, linking 09's retirement rules | `references/07-gates-and-ci.md` (new "suite lifecycle" section beside baseline lifecycle), `references/00` stage table footnote | Distinguishes the three saturation contexts (benchmark adoption in 04, benchmark retirement in 09, suite-internal graduation here); no contradictions | M | senior |
| P1-11 | **Partial results + cost ceilings** (A6): exit-2-with-partial analog — partial suite docs never enter trend charts; rate-limited-mid-suite looks like a regression (their own admission) = our silent-crash anti-pattern made concrete; cost ceiling as pre-registered budget | `references/07` | Names the mapping to CANNOT-MEASURE explicitly | S | senior |
| P1-12 | **Monitor-stage label loop** (A8 + B5): annotation-queue→human-label→judge-recalibration cycle; alignment applies to code assertions too, not just judges; a permanent sampled-trace labeling stream continues *after* floor is met, to catch drift; where labels come from in a live system | `references/03` (extend beyond judges), `references/01` monitor row one line | 03's calibration section re-scoped to "any scorer vs humans"; permanent-stream cadence stated as a % of traces | M | senior |
| P1-13 | **Transcript-review cadence** (A7): read N transcripts per run, always; transcript is the arbiter of agent-error-vs-grader-error; framed as audit so it doesn't collide with 10's "transcript not consulted for outcome verdict" | `references/11-reading-results.md` | Cadence is concrete (N per run, which runs); explicitly separated from grading | S | senior |
| P1-14 | **Inline guardrail placement** (D3): third placement — eval between system and user; must be fast, must have a remediation path (retry / route-to-fixer); different cost/latency profile than gate or monitor | `references/00` stage table or `01` §3 placement list + `07` note; SKILL.md stage table gains the row only if it survives the voice-length budget — decide at write time | Placement named distinctly from gate and monitor; remediation-path requirement stated; latency constraint stated | S | senior |

### P2 — Trigger-evals + integrity + walkthroughs

| ID | Change | Files | Acceptance criteria | Size | Track |
|----|--------|-------|---------------------|------|-------|
| P2-1 | **Trigger-F1 as a taught category** (A9): balanced should/shouldn't-trigger set; activation rate = a classification problem (precision/recall on firing); description is the lever; the repo's own suite as the worked instance; Wilson CI on activation rate | `references/02` triggering section expanded, or NEW `references/13-trigger-evals.md` if >40 lines; `00` mention | Self-referential ("this skill ships exactly this") stated; should/shouldn't balance rule given; cites no external tools | M | senior |
| P2-2 | **Wilson interval script**: `rate_interval.py` — stdlib Wilson score interval on k/n (activation rate, judge positive rate, any proportion); complements paired_bootstrap (deltas) for single rates | NEW `scripts/rate_interval.py` + `tests/` cases | `--help`, exits nonzero on bad input, same CLI conventions as the other four; unittest coverage in existing job | S | GLM (spec: Wilson score interval, k/n args, validate 0≤k≤n) |
| P2-3 | **Routing integrity test**: every `references/`, `templates/`, `scripts/` path named in SKILL.md exists; every file in those dirs is either routed or deliberately unlisted (allowlist with reason); frontmatter `name`/`description` present | `tests/test_docs.py` | Fails on orphaned reference or dead path; runs free in existing CI | S | GLM |
| P2-4 | **"Evaluate my own skill/plugin" route row** (M4) | SKILL.md route table + description wording reviewed | Row added; full 21+3 case suite re-run green; description diff minimal | S | senior |
| P2-5 | **Three walkthroughs** (specs in §4) | NEW `references/walkthroughs/{product-step,ai-system,benchmark}.md` + route rows | Each is beginner-followable A→Z, exercises real templates+scripts, ends at an eval-report; each names which references it loads and when | L | senior (voice-critical) |

### P3 — Positioning, distribution, hygiene

| ID | Change | Files | Acceptance criteria | Size | Track |
|----|--------|-------|---------------------|------|-------|
| P3-1 | Positioning paragraph: Anthropic's "invest in the evals themselves" + dead-harness receipts (a big-name eval framework months-stale; a big-name prompt benchmark archived) as the empirical case for harness-agnosticism; "runner classes" comparison table (config runners / pytest-style / observability platforms / agent sandboxes / official plugin runner) mapped to the four-seam contract, no endorsements | `METHODOLOGY.md`, `README.md` | Framework names stay out of `skills/` entirely (assert via P3-4 lint); tone matches existing docs | M | senior |
| P3-2 | Localized READMEs: batch-update all four in one pass after README.md settles, or add a visible "translation of v0.1.x" stamp | `README.{es,ja,ko,zh-CN}.md` | No partial-drift state where some translations carry positioning and others don't | M | GLM (translation) + senior review |
| P3-3 | Version↔tag check in `plugin` CI job (on release tags: tag == plugin.json version == marketplace.json version) | `.github/workflows/test.yml` | Mismatched tag fails the job | S | GLM |
| P3-4 | Voice lint: stdlib test scanning `SKILL.md`, `references/`, `templates/` for a denylist of framework/tool proper nouns (allowlist file for legitimate exceptions like SWE-bench inside quoted examples) | `tests/test_voice.py` + allowlist | A framework name inside skills/ fails CI | S | GLM |
| P3-5 | Watch item, documented: `claude plugin eval init`-generated graders are exactly the artifact eval-genius exists to critique (uncalibrated judge, no fixture fingerprint, mean-of-3 no interval) — a future "audit an auto-generated suite" route row is the moat if adoption grows | PLAN.md note → future issue, not this cycle | Recorded as a follow-up, no code | S | senior |

---

## 4. Walkthrough specs (write in P2-5, after P1 content settles)

Format for all three: a narrative in the skill's voice that loads the same references a real session would, in order, and produces real artifacts (filled templates, script outputs). No fabricated results — numbers shown are labeled illustrative or generated by actually running the scripts on included toy fixture files. Ship the toy fixtures under `references/walkthroughs/fixtures/` so every printed number is reproducible.

### W1 — "Evaluating one step in my product" (beginner, smallest scope)
- **Persona:** engineer or PM, has a working feature (e.g., a summarizer step inside a larger app), zero eval knowledge.
- **Path:** 00 (stage = first working version → smoke eval) → optional 12 (if they have user complaints) → Step 1 preregistration (fill promise/lever/baseline/bar only) → 02 (decompose "good summary" into deterministic checks) → collect 30 real inputs incl. 5 refusals → run baseline → write bar → change one thing → per-item diff → `check_gate.py` + `paired_bootstrap.py` on shipped fixtures → verdict + `eval-report.md`.
- **Teaches:** the whole spine at minimum weight. Exit criteria: reader could repeat it on their own step.

### W2 — "Evaluating the AI system itself" (end-to-end, agentic)
- **Persona:** engineer with a multi-step agent; needs task success + reliability, not vibes.
- **Path:** 00 → 01 (levers incl. "the harness is a lever") → 10 (outcome vs trajectory, pass@k vs pass^k, per-trial sandboxing, known-good + known-bad admission, simulated user as pinned fixture, infrastructure-failure = CANNOT-MEASURE) → 06 (mocks with contract-checked fakes — P1-8 content) → judged layer for process quality with 03 calibration → 07 tiers → report.
- **Teaches:** where agentic evals differ; why outcome and trajectory never blend.

### W3 — "Building a benchmark I can publish" (highest stakes)
- **Persona:** researcher/engineer making a comparative or public claim.
- **Path:** 04 (search first, scorecard on 2–3 real candidates incl. a deliberately stale one → build decision with stated reason) → 05 (labeling guideline, IAA, negative space, splits, contamination checks, manifest) → 06 (full harness, manifest, fingerprint refusal) → 08 (intervals, MDE, repeated-run noise floor) → 09 (tiers, disclosure, self-run labeling, attack pass, retirement note).
- **Teaches:** the full A→Z at benchmark weight; what a number may claim publicly.

---

## 5. Dogfood/CI plan — detail (P0)

**Suite layout** (travels inside the copyable skill dir):

```
skills/eval-genius/evals/
├── evals.json                     # source of truth, kept (skill-creator format, separate per docs)
├── trigger-*/                     # 21 case dirs, one per evals.json query
│   ├── prompt.md                  # body = query verbatim; frontmatter: max_turns, allowed_tools
│   └── graders/skill-fired.md     # tool_used: Skill; should_trigger=false → min:0, max:0, arm: both
├── quality-*/                     # 3 llm-grader cases (the Δ-bearing cases)
└── results/                       # gitignored
```

**plugin.json:** `"experimental": {"evals": "skills/eval-genius/evals"}` so `claude plugin eval .` from repo root resolves the suite (verified mechanism in current docs; re-verify field name at implementation time — it sits under `experimental` and could move).

**CI workflow (`eval.yml`):** advisory on PRs that touch the trigger surface; blocking on pre-release dispatch. Pinned `--model`/`--judge-model`, `--threshold 0.8`, `--max-cost-usd`, `--no-publish`, `--trust-plugin`, `--json`. Three-way handling of the runner's own exit codes mirrors our 07 contract: 0 pass · 1 fail · 2 = CANNOT-MEASURE (partial/auth) → artifacts uploaded, loudly marked unmeasured, never trended.

**Credibility loop:** once ≥2 green runs exist, README quotes the measured Δ (measured tier, linked artifacts). The skill's own trigger suite becomes the canonical worked example cited by the P2 trigger-eval reference — the methodology passing its own audit, which nothing else in the plugin ecosystem does.

**Open dependency on Alex:** Anthropic credential in repo secrets + a monthly cost ceiling number. Without it, P0-5 can't run in CI; local runs still work. If CI cost is declined, downgrade to a documented `workflow_dispatch`-only gate and note it.

---

## 6. Risk & regression notes

| Risk | Mechanism | Guard |
|------|-----------|-------|
| **Triggering regression** — any description/SKILL.md edit can silently break firing (has happened before to RAG prompts) | Every P1/P2 item that touches SKILL.md or frontmatter must re-run the 21-case suite (P0 artifact) and keep all should-trigger cases firing | P0-1/P0-4/P0-5 gate; no SKILL.md edit ships before P0 lands |
| **Bloat** — 12 new topics could double the skill and dilute the route table | Hard budget: SKILL.md changes ≤ ~10 lines total (fork sentence, 2 route rows, optional stage row). Everything else lives in on-demand references. New files only where the content is a loadable unit (12, maybe 13); catalog extensions stay inside 02 | Reviewer checks SKILL.md diff line count; P2-3 integrity test catches un-routed orphans |
| **Voice drift** — framework name-dropping, vendor comparisons, or hype inside skills/ | Guardrail stands: the landscape argument lives in README/METHODOLOGY only. Torres/Anthropic ideas get rewritten into the measurement-engineer register, not pasted | P3-4 voice lint in CI; senior track owns all prose |
| **Scope creep via the multi-method table** — naming A/B tests or observability platforms could teach (and trigger on) things the skill deliberately refuses | Table labels adjacent methods as *not this skill*; evals.json's A/B shouldn't-trigger case is the regression test | P1-3 acceptance criterion |
| **Dual-format drift** — evals.json and case dirs diverging | Sync test (P0-4) makes drift a CI failure | tests/test_evals_sync.py |
| **Paid-eval flakes/cost** — llm graders are noisy; CI spend is real money | Pin judge model, quality rubrics as concrete PASS/FAIL, threshold 0.8, `--max-cost-usd`, advisory-not-blocking on PRs, partials never trended | eval.yml flags; P1-11 content teaches the same discipline |
| **check_gate contract creep** — partial credit could pressure the binary verdict contract | Verdicts stay pass/fail/error; partial credit flows through the existing `score` field to paired_bootstrap; doc says the split is deliberate | P1-6 explicitly no-behavior-change |
| **Contradiction: transcripts** — 10 says transcript isn't consulted for outcome verdict; new cadence says always read transcripts | Frame P1-13 as audit/debug, never grading | Acceptance criterion on P1-13 |
| **evals.json loader conflict** — a stray non-case file inside the eval dir could confuse the runner | Verified by a real `--runs 1` execution in P0-1, not assumed | P0-1 acceptance criterion |
| **Translation drift** | Batch-update once (P3-2), never piecemeal | Sequencing rule |

---

## 7. Delegation map

- **GLM-5.2-on-Devin** (mechanical, spec'd above): P0-1 case-dir generation, P0-4 sync test, P0-6 gitignore, P1-2 template (from senior field spec), P2-2 Wilson script + tests, P2-3 integrity test, P3-2 translations, P3-3 version check, P3-4 voice lint.
- **Senior** (voice, judgment, rubric wording, sequencing): P0-2, P0-3, P0-5, P0-7, all of P1 prose, P2-1, P2-4, P2-5 walkthroughs, P3-1.
- **Alex decisions needed:** Anthropic API key in repo secrets + cost ceiling (P0-5); sign-off on the second-front-door restructure before P1-1 writes prose; whether eval CI is advisory-only or also blocking pre-release.

## 8. Non-goals this cycle

- No new harness/runner — eval-genius stays the decision layer above runners (`claude plugin eval` runs suites; eval-genius decides whether a suite is worth running).
- No expansion into A/B testing, observability platforms, or human-study design (M7) — named as adjacent, not taught.
- No edits to `tests/fixtures/` semantics; new tests only.
- No commit/push from this planning pass; PLAN.md is the only new file.
