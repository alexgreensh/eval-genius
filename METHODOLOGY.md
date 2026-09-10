# Evals & Benchmarks: A Working Methodology

*A portable, tool-agnostic guide to measuring whether your work is actually getting better. Share freely. This is the gist; the depth (harness code shapes, calibration procedures, full templates) lives in the companion skill.*

**By [Alex Greenshpun](https://github.com/alexgreensh)** · [github.com/alexgreensh](https://github.com/alexgreensh)

---

## TL;DR (start here)

Before you build a single benchmark, answer four plain-language questions:

1. **What are we trying to do, and what does "better" even mean here?** Name the goal in one sentence a non-expert would understand.
2. **Do we actually need to measure it?** Not everything needs a benchmark. Some things need a quick check, some need a gate, some need nothing.
3. **What exactly would we measure?** The real outcome you care about, in plain words, not the convenient proxy that's easy to count.
4. **What can we change, and what do we expect to move downstream?** List the levers you control and the effects that should shift if a lever works.

Only *after* those do you decide **where** a measurement belongs and **which kind** it is. Most bad eval work comes from jumping straight to "let's build a benchmark" before knowing what it's for.

**The one idea underneath all of it:** an eval is a claim you're willing to defend under hostile audit. You don't measure to produce a number. You measure to earn the right to say "this is better," and to have that hold up when someone smart tries to knock it down.

---

## Part 0 — Before benchmarks: what are you even measuring, and why?

This is the part everyone skips. Don't.

- **Start with the goal, not the metric.** Write the promise your work makes, in plain language. The metric comes *from* the promise. If you can't state the promise, you're not ready to measure.
- **Name your variables.** Levers (what you change), outcomes (what you watch), controls (what you hold constant). If you can't say which is which, you'll mistake drift or noise for a real effect.
- **Match the metric to the task.** Retrieval wants recall/precision/MRR; classification wants precision/recall/F1; generation wants faithfulness or a judged rubric; agentic work wants task success plus trajectory quality. Pick the one whose failure mode is the failure you care about.
- **Treat cost and latency as first-class outcomes**, not afterthoughts. Track tokens, p50/p95 latency, and cost-per-pass alongside quality. A quality win that triples cost is a trade, not a free win.

### Where a measurement belongs, and how heavy

Put evals at **decision points** (choosing between options), **risky seams** (where a mistake is expensive or invisible), and **anything you claim publicly**. Everywhere else, a lighter check or nothing is fine.

| Instrument | When | Cost |
|---|---|---|
| **Spot check** | One-off "does this look right?" during dev | Seconds, throwaway |
| **Eval** | Repeatable check on a capability you keep changing | Cheap to re-run, lives in the repo |
| **Benchmark** | Standardized, comparable across versions or rivals | Real setup cost, worth versioning |
| **Monitor** | Continuous measurement of live behavior | Ongoing, catches drift after ship |

A benchmark you run once was probably meant to be an eval. **Define "better" as a threshold before you look**, deciding the bar after seeing the number is how people ship noise.

---

## Part 1 — The first fork: deterministic vs non-deterministic

Name which *kind* of eval you're building. This choice drives everything downstream.

| | **Deterministic** (code-graded) | **Non-deterministic** (model/human-graded) |
|---|---|---|
| **Grader** | Exact match, regex, test suite, schema check, numeric threshold | LLM-as-judge, human rater, pairwise preference |
| **Use when** | There's a checkable right answer: code runs, JSON parses, value = X | Quality is subjective: tone, helpfulness, faithfulness |
| **Cost & speed** | Free, instant, reproducible | Slow, costs money or judge tokens, noisy |
| **Trust** | High, *if the check is correct* | Only as good as the judge, biased by default |

**Governing rule: push everything you can down to deterministic.** Reserve model or human judgment for the genuine judgment edge, the part no assertion can capture.

**Corollary: don't blend layers into one number.** Report the deterministic pass rate and the judged quality score *separately*. A blended score hides which half moved.

---

## Part 2 — LLM-as-a-judge, if you must use one

A model judge is useful and biased. Treat it as an *instrument that needs calibration*, never an oracle.

**The biases you inherit for free:**

| Bias | What it does | Mitigation |
|---|---|---|
| **Position** | Favors the answer shown first (or last) | Randomize order; run both and average |
| **Verbosity** | Rewards longer answers regardless of quality | Tell the judge how to treat length |
| **Self-preference** | Inflates its own model family's output | Judge with a *different* model than the one tested |

**Calibrate it like an instrument, not once but on a cadence:**

1. Build a small **human-labeled set** (a few dozen items with agreed correct verdicts).
2. Score the judge against it and measure **agreement** (Cohen's kappa for categorical, Spearman for ordinal). Set a pass threshold; below it, the judge isn't trusted yet.
3. **Re-check on drift**, whenever the judge model or its prompt changes. Pin the judge model + prompt hash in the run manifest so a score is traceable to the exact judge that produced it.

**Two more that matter:**
- **Reason before scoring**, and **anchor the rubric** (describe what a 1/3/5 looks like, not a bare 1-10).
- **Watch rubric-authorship bias.** Whoever built the system usually writes the rubric, which quietly encodes what the system already does well. Have someone else author the probes, or blind-swap authors.

**The deeper trap:** fixing a judge's *bias* is not the same as validating it measures what you *claim*. A perfectly de-biased comprehension judge may still only be checking whether text is *present*, not *understood*.

---

## Part 3 — Decide and design

### Adopt an existing benchmark, or build your own?

- **Adopt** when a public benchmark genuinely exercises your capability, free credibility and ground truth you didn't cook.
- **Build** the moment it measures a *proxy* your system doesn't target. A famous benchmark that doesn't stress your mechanism will quietly tell you your work does nothing.
- **When you build, reuse the public harness** where you can.

**Assess a candidate benchmark before adopting** (the scorecard): (1) what utility does it reward, and does it match your promise? (2) contamination, could the model have trained on it? (3) its own label-error ceiling; (4) does it exercise *your* mechanism or a neighbor's? (5) still maintained and comparable, or stale?

### Name the utility function first

Every benchmark implicitly defines "what good means." State it out loud, then pick the metric that measures *that*. Prefer the harder end-to-end outcome over the easy intermediate proxy.

### Pre-register before you run

Write, *before* seeing any number: the **baseline**, the **acceptance criteria**, the **falsifiers** (what would prove you wrong and what you'd conclude), the **outlier rule**, and a rough **sample size** (enough items that the effect you care about would clear the noise, see Part 5). This is the single highest-leverage habit; it's what stops you moving the goalposts.

### Build the dataset with discipline

- **Split dev from held-out test, and never tune on the gate set.** Tuning against your test set turns the gate green by teaching to it.
- **Cover the negative space.** Verified-absent negatives, near-miss distractors, refusals that *should* fire. A benchmark that only walks the happy path has tested half a promise.
- **Guard against contamination.** Prefer a held-out private set; check for leakage (n-gram overlap, canary strings, provenance); rotate the private set over time.
- **If you label by hand,** write label guidelines and measure inter-annotator agreement, disagreement means the task is underspecified, not that a rater is wrong.

### Guard against overfitting the benchmark (Goodhart's law)

The held-out split above stops the crude version (teaching to the test). The subtle version needs its own defense: iterate against one benchmark long enough and you optimize the *number* while the real capability stalls, even without touching the test set. "When a measure becomes a target, it stops being a good measure." Defenses:

- **Keep a private held-out set you touch rarely**, ideally only at release. The set you look at every run is the set you overfit.
- **Rotate or refresh test items** over time, so the target keeps moving faster than you can memorize it.
- **Watch for metric-reality divergence.** If the score climbs but spot checks, users, or a fresh eyeball pass don't agree, believe the reality, not the number.
- **Cap how often you look** at a given set, and keep one qualitative pass that no optimization loop can game.
- **Don't chase a single headline metric.** Optimizing one number is exactly what invites Goodhart, keep a small basket (quality, cost, a negative-space check) so gaming one shows up in another.

---

## Part 4 — Build a proper harness

A harness is four separable parts: **fixture** (the frozen inputs + expected answers), **runner** (executes the system under test), **scorer** (grades each item), **reporter** (aggregates + writes results). Keep them separate so you can swap one without disturbing the rest.

- **Emit per-item results, not just an aggregate.** You cannot debug or bisect a single number. Every regression investigation starts from the item that moved.
- **Write a run manifest**: the code/model version, fixture hash, judge version, seed, date, environment. A run you can't re-execute is an anecdote.
- **Three outcomes, never two: PASS / FAIL / CANNOT-MEASURE.** A crashed run, a timeout, a parse failure is *not* a fail and *not* a pass, it's unmeasured. Folding it into either silently corrupts the number. This is the most common way a harness lies.
- **Fingerprint the fixture and refuse mismatched comparisons.** The harness should hard-stop before comparing runs against different corpora, caches, or snapshots. Freeze and version baselines.
- **Beware the cache trap.** A benchmark that reads a pre-built cache never exercises the write path, so a broken write regresses silently. Force a fresh build for anything that could touch writes.
- **Liveness-check the treatment arm.** Assert the flag/config/model under test is *actually active* before the run. Silent misconfiguration produces a confident, fake comparison.

---

## Part 5 — Is the delta real? (the statistics you can't skip)

A number without noise bounds isn't a result.

- **Compare paired**, same items through both arms, and look at per-item differences. Paired comparison cancels item difficulty and finds real effects a between-groups comparison misses.
- **Put a confidence interval on the delta** (bootstrap over items is the simple, assumption-light default). If the interval crosses zero, you don't have an effect yet.
- **Size the test set to the effect.** A handful of items can't detect a 2% change. Decide the smallest difference worth catching, then use enough items to see it.
- **Don't run until it passes.** Re-running and keeping the good result is p-hacking; every extra look inflates false positives. Decide trials in advance.
- **A flaky gate is a broken gate.** Non-determinism in the harness (unpinned seeds, temperature, clock, ordering) has to be fixed or quarantined, not tolerated.

---

## Part 6 — Gate it in CI (when the eval guards a codebase)

- **Tier the gates by cost.** Fast deterministic checks on every PR; the fuller benchmark nightly; the expensive judged suite at release. Put a time/cost budget on each tier.
- **Give the baseline a lifecycle.** Say where it lives, who may promote a new one, and record *why* each promotion happened. An un-owned baseline drifts into fiction.
- **Wire the negative control into the gate.** The gate itself should include a known-bad case that *must* fail; if it ever passes, the gate is broken. Proving the verifier catches a plant is not optional.

---

## Part 7 — Trusting the number (validate the eval itself)

The eval can be wrong. Audit it before you audit the work.

- **A shocking result is a harness bug until proven otherwise.** Before believing a 0% or a 99%, confirm the harness ran what you think it ran.
- **Never tune against a broken gauge.** If the instrument is suspect, fix the instrument or stop. Changing the system to make a bad ruler read nicely is the one unforgivable move.
- **Triage a gate failure** with the per-item diff: which items moved, is it the system or the gauge, bisect to the change. "Fix the gauge vs fix the system" is the first fork.

---

## Part 8 — Reporting: honesty is the deliverable

Report in a fixed shape so a reader can audit it:

- **The pre-registration block** (baseline, criteria, falsifiers) up front, so nobody wonders if you moved the goalposts.
- **The manifest** (versions, fixture hash, judge version, seed).
- **Per-layer numbers** (deterministic and judged, separately), each with its noise bound.
- **Tiers labeled**: *measured* vs *estimated* vs *aspirational*, never summed across those lines.
- **Caveats that weaken your own number**: conservative setup, older snapshot, small sample. The disclosure is what makes the number believable.
- **Say when a benchmark is self-run** rather than independent.
- **Report negative and null results too**, and retire a benchmark (with a written reason) when it stops discriminating.

**Versioning & comparability:** version the dataset and the harness. Two scores may sit side by side *only* when fixture hash, harness version, and judge version match. State the comparability rule in the report, don't leave it to the reader to assume.

---

## The one-page checklist

**Before:**
- [ ] Goal in one plain sentence; levers / outcomes / controls named
- [ ] Metric matched to the task; cost + latency tracked as outcomes
- [ ] *Where* the measurement belongs and its *weight* decided
- [ ] Deterministic vs non-deterministic chosen deliberately
- [ ] Acceptance bar + sample size set *before* looking
- [ ] Adopt-vs-build decided; candidate scored on the 5 questions
- [ ] Dataset split (dev vs held-out); contamination + negatives handled
- [ ] Pre-registration written (baseline, criteria, falsifiers, outlier rule)

**During:**
- [ ] Harness split into fixture / runner / scorer / reporter; per-item results emitted
- [ ] Run manifest recorded (versions, hashes, seed)
- [ ] Outcomes are PASS / FAIL / CANNOT-MEASURE
- [ ] Fixture fingerprinted; only the change varies; cache trap avoided
- [ ] Treatment arm liveness-checked
- [ ] Judge calibrated against human labels (agreement above threshold)

**After:**
- [ ] Delta has a confidence interval; paired comparison used
- [ ] Shocking numbers investigated as possible harness bugs
- [ ] Verifier proven to catch a known-bad case (negative control in the gate)
- [ ] Layers reported separately; tiers labeled; caveats disclosed
- [ ] Comparability rule stated; benchmark + baseline versioned
- [ ] Overfitting guarded: private held-out reserved, watched for metric-reality divergence

---

*This is a methodology, not a framework. Tool-agnostic on purpose, the discipline is the point, not the library. Share freely.*

*By [Alex Greenshpun](https://github.com/alexgreensh). If this helped, a star or a share helps others find it.*
