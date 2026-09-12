---
type: llm
---
Judge the assistant's reply to "Our LLM judge gives the new prompt 9/10 but users complain. How do I calibrate the judge?"

PASS if the reply treats the judge as an instrument to be measured against ground truth, not trusted. It must center on:
- Building a set of human-labeled examples and measuring the judge's AGREEMENT with those labels (e.g. Cohen's kappa, or PASS precision/recall of the judge vs the human labels), so "9/10" is checked against what humans actually consider good. The user complaints are evidence the judge is miscalibrated and a source of labels.
- At least one concrete hardening step for the judge as an instrument: blind it / remove identifying cues, randomize or control answer order to counter position bias, decompose the rubric into concrete per-dimension checks, give the judge an "unknown/abstain" option, and pin the judge model and prompt so the gauge is reproducible.

FAIL if the reply mainly suggests improving the product prompt, "asking the judge to be stricter," or raising the score threshold, without measuring the judge against human labels; or if it accepts the 9/10 as basically valid; or if it gives generic advice with no agreement measurement against a human-labeled set.
