---
type: llm
---
Judge the assistant's reply to "I built a small chatbot on top of an LLM. Do I even need evals for this?"

PASS if the reply treats "do you need one" as a real question with a threshold, not a foregone yes. It must do BOTH:
- Tie the decision to concrete conditions (does the output vary; will it change again and would a quiet regression cost something; is a decision or public claim coming), rather than reflexively answering "yes, always write evals."
- Size the first step to the project's stage (e.g. a hand/spot check of a handful of inputs for an exploratory chatbot, a small smoke eval only once there is a first working version), rather than prescribing a full eval suite, CI gate, or benchmark up front.

FAIL if the reply reflexively says to build comprehensive evals regardless of stage, jumps straight to tooling/frameworks/metrics without asking whether an eval is even warranted, or gives a generic "evals are important" answer with no decision criterion and no stage-sizing.
