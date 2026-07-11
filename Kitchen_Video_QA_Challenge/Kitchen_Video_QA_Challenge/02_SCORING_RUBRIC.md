# Scoring Rubric & Budget Limits

## Score breakdown (100 points total)

| Component | Points | What it measures |
|---|---|---|
| Answer correctness | 65 | Structured answers across yes/no, counts, visible states, event order, timestamps, and correct "not visible" calls |
| Budget efficiency | 15 | Valid runs stay under the hard runtime/frame/model-API budget; cheaper valid runs get extra credit **only if accuracy holds** |
| Hidden generalization | 15 | Stable performance across different layouts, lighting, cuisines, camera angles, and video quality |
| Reproducibility | 5 | One-command run, logged frame sampling/model calls, deterministic or near-deterministic output |

## Timestamp precision (draft spec)
- **Full credit:** answer within 2 seconds of the correct time
- **Partial credit:** within 5 seconds
- **Zero credit:** beyond 5 seconds (unless the event span is long and the
  rubric explicitly says otherwise for that question)

## Budget hard limits (draft)
- **20 minutes** wall-clock for the full evaluation run
- **$3** model/API-equivalent cost maximum, if external APIs are permitted
- **1 frame/second** average sampling rate, or an equivalent fixed frame
  budget
- One reproducible command — no manual inspection allowed during scoring
- ⚠️ **Submissions that exceed the hard budget are ineligible.** This is a
  cutoff, not a soft penalty — going over doesn't cost you points, it removes
  you from scoring entirely.

## What this rewards in practice
- Being right on "not visible" cases is worth real points and is explicitly
  called out twice in the spec as something naive submissions get wrong by
  guessing instead.
- Temporal/ordering questions are a distinct skill from single-frame
  classification — worth building/testing separately.
- Because 15 of 100 points are pure budget efficiency and going over budget
  zeroes you out entirely, a cheap-but-slightly-less-accurate pipeline can
  beat an expensive, marginally-more-accurate one. Optimize for "clears the
  baseline reliably within budget," not "maximum possible accuracy."
