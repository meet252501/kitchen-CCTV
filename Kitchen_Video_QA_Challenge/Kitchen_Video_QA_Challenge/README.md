# Kitchen Video QA Challenge — Prep Folder

Everything gathered from a deep scan of https://builderr.ai/kitchen-video and
https://builderr.ai/kitchen-video-challenge-draft.md, plus a working code skeleton
so you can start building before the dataset officially drops.

**Status at time of scan (July 10, 2026): Upcoming — dataset still being assembled. No live submission window yet.**

## Files in this folder

| File | What it's for |
|---|---|
| `01_CHALLENGE_OVERVIEW.md` | What the challenge is, what you build, question types, output format |
| `02_SCORING_RUBRIC.md` | Full 100-point scoring breakdown + budget hard limits |
| `03_DATASET_LEADS.md` | Every candidate video source builderr referenced while designing this, rated by usefulness |
| `04_PREP_CHECKLIST.md` | Concrete action list to be ready the day it goes live |
| `answer.py` | Starter CLI skeleton matching the required `--videos --questions --out` interface |
| `questions_schema.json` | Example structure of the input questions file |
| `answers_schema.json` | Example structure of the required output file |

## Fastest path to being ready
1. Read `01_CHALLENGE_OVERVIEW.md` and `02_SCORING_RUBRIC.md` first — they define what "correct" even means here.
2. Get `answer.py` running end-to-end on any local kitchen-style clip, even with a dumb baseline (1fps sampling + a VLM call).
3. Use `04_PREP_CHECKLIST.md` to track what's left before submission opens.
4. Register interest: mailto:submit@builderr.ai (subject: "Kitchen video QA interest") — this is currently the only official way to get notified.
