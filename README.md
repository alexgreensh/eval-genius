<p align="center">
  <img src="assets/img/eval-genius.png" alt="Eval Genius, the star-cloaked measurement sage" width="280">
</p>

<h1 align="center">Eval Genius</h1>
<p align="center"><strong>Defensible answers about your AI system, instead of vibes.</strong></p>

<p align="center">
  A skill for any AI coding agent that tells you <em>when</em> you need an eval,<br>
  where it fits, how to build it, and how to read what comes out.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue" alt="License: Apache 2.0"></a>
  <img src="https://img.shields.io/badge/works%20across-Claude%20Code%20·%20Codex%20·%20Cursor%20·%20any%20agent-8A5CF6" alt="Works across any agent">
  <img src="https://img.shields.io/badge/scripts-stdlib%20Python%20·%20zero%20deps-2ea44f" alt="Stdlib Python, zero dependencies">
</p>

<p align="center">
  <strong>English</strong> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.es.md">Español</a> · <a href="README.ko.md">한국어</a> · <a href="README.ja.md">日本語</a>
</p>

---

### Everyone says "you need evals." Almost nobody says *when*.

## The problem

<p align="center"><img src="assets/img/problem.png" alt="Eval Genius at a crossroads of floating paths, unsure which way the evals go" width="100%"></p>

Evals are suddenly everywhere. Every AI talk, every launch post, every hiring thread says you need them. Then you sit down to actually do it, and the questions start.

Does a prompt tweak really need an eval, or is that overkill? At which point in the build does the first one go in? What is an "eval harness", concretely, beyond a folder named `evals/`? Which metric, how many examples, does a judge model even count? And when a number finally comes out, is 34 out of 40 good? Is a 3-point gain real, or noise? Or did the run just crash quietly and report a pass?

Answer these by feel and you get exactly what most teams have: a benchmark nobody trusts, a gate that has been green for a month because it grades nothing, and a number in the README that would not survive one sharp question.

## Meet Eval Genius

<p align="center"><img src="assets/img/solution.png" alt="Eval Genius with a compass and a star-map, weighing results on a set of scales" width="100%"></p>

Eval Genius is that missing judgment, packaged as a skill your AI agent runs *with* you. It thinks like a measurement engineer: decide what "better" means before you look, push every check you can down to plain code, treat a crash as *unmeasured* rather than a pass, and trust the number last.

It is not a course you have to read first. You describe where you are, in plain words, and it takes the next step, whether that step is "you don't need one yet" or "here is the gate, and here is why this run cannot be trusted."

It is tool-agnostic and dependency-free: a `SKILL.md` plus a few standard-library Python scripts. It runs in Claude Code, or any agent that loads skills, or from your terminal on its own.

## What you can ask it

<p align="center"><img src="assets/img/ask.png" alt="Eval Genius working hands-on, pulling a star-map into a laptop" width="100%"></p>

Real questions, answered from wherever you actually are:

- *"Do I need evals for my chatbot, or is that overkill right now?"*
- *"Where does an eval even go in my build?"*
- *"I got 34 out of 40, is that good?"*
- *"Is this 3-point gain real, or noise?"*
- *"Calibrate my LLM judge against some human labels."*

No setup ritual, no vocabulary you have to learn first. Describe the situation, get the next move.

## What it does for you

<p align="center"><img src="assets/img/what-it-does.png" alt="Eval Genius crossing floating platforms through a pass/fail gate toward the results" width="100%"></p>

It walks the whole path, and meets you at any point on it, including the start:

- **Decides whether you need an eval at all**, and which kind belongs at your stage, from first prototype to production.
- **Picks the eval:** what to measure, which grader (code first, a judge only where no assertion works), which metric, how many examples, adopt a public benchmark or build your own.
- **Builds and gates it:** fixture, runner, scorer, reporter, a bar written before the run, and a CI gate that ends in PASS, FAIL, or CANNOT-MEASURE and only compares two runs when they truly measured the same thing, the same way.
- **Reads the result with you:** against the bar you wrote, with noise bounds, per-item diffs, and a harness-bug check before any surprising number is believed.
- **Writes it up honestly,** with caveats, tiers, and the comparison rule stated out loud.
- **Refuses the shortcuts** that produce pretty lies: bars moved after the fact, blended scores, run-until-green, and judges nobody calibrated.

## The parts that are easiest to get wrong, handled

<p align="center"><img src="assets/img/scripts.png" alt="Eval Genius at a desk with a checklist, a bell curve, and a judge-vs-human scale" width="100%"></p>

Four standard-library scripts ship with the skill and run standalone:

| Script | What it settles |
|---|---|
| `check_gate.py` | Compares a change against its baseline per item; exits **0 PASS**, **1 FAIL**, **2 CANNOT-MEASURE**, so a crash can never masquerade as a pass |
| `paired_bootstrap.py` | Puts a confidence interval on the difference, so "it improved" actually means something |
| `judge_agreement.py` | Measures how much your LLM judge agrees with human labels, before you let it grade anything |
| `hash_fixture.py` | Fingerprints your test set, so you know two runs are measuring the same thing before you trust the comparison |

## Install

Eval Genius is a Claude Code plugin. Add the marketplace once, then install:

```bash
# in Claude Code
/plugin marketplace add alexgreensh/eval-genius
/plugin install eval-genius@eval-genius
```

Prefer a plain skill folder, or using another agent? The skill lives at `skills/eval-genius/` — copy it wherever your agent looks for skills:

```bash
cp -R skills/eval-genius ~/.claude/skills/eval-genius
# Any other agent: point it at skills/eval-genius/SKILL.md
```

Then talk to it in plain language (*"do I need evals for my chatbot?"*, *"is this delta real?"*, *"calibrate my judge"*). The scripts also run on their own:

```bash
python3 skills/eval-genius/scripts/check_gate.py --baseline base.json --treatment treat.json
```

On Windows, use `py -3` instead of `python3` if that is how Python is installed.

## Curious about the reasoning?

The full method behind the skill, in one plain-language document, lives in **[METHODOLOGY.md](METHODOLOGY.md)**. You do not need it to use the skill; it is there if you want to see the thinking.

---

<div align="center">

Built by **Alex Greenshpun**. If it helps, a star or a share helps others find it.

<a href="https://github.com/alexgreensh"><img src="https://img.shields.io/badge/GitHub-alexgreensh-181717?logo=github&logoColor=white" alt="GitHub"></a>
<a href="https://alexgreenshpun.com"><img src="https://img.shields.io/badge/Website-alexgreenshpun.com-8A5CF6" alt="Website"></a>
<a href="https://x.com/alexgreensh"><img src="https://img.shields.io/badge/X-%40alexgreensh-000000?logo=x&logoColor=white" alt="X"></a>

**License:** [Apache 2.0](LICENSE)

</div>
