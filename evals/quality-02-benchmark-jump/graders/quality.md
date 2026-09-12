---
type: llm
---
Judge the assistant's reply to "The benchmark jumped from 40% to 97% after a one-line change. Is that real?"

PASS if the reply treats the jump as suspect until the instrument is proven, not as a win to celebrate. It must do BOTH:
- Say plainly that a swing that large from a one-line change is most likely a measurement/harness artifact (e.g. a broken or short-circuited scorer, a cache or fixture change, a parsing/format shift, contamination, comparing across mismatched runs) until shown otherwise.
- Prescribe verifying the gauge before believing the number: inspect individual items/regressions by hand, confirm the negative control still fails, check nothing but the intended lever changed, and re-run to see the spread. It must NOT advise tuning or shipping against the number while it is still unexplained.

FAIL if the reply accepts 97% at face value, congratulates the change, attributes the gain to genuine model/quality improvement without first suspecting the instrument, or gives generic advice with no concrete gauge-verification step.
