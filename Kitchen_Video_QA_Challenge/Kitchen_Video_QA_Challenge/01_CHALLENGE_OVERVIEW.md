# Challenge Overview

**Source:** https://builderr.ai/kitchen-video
**Draft spec:** https://builderr.ai/kitchen-video-challenge-draft.md
**Prize:** $300 (top valid score, if it clears the benchmark)
**Register interest:** mailto:submit@builderr.ai — subject "Kitchen video QA interest"

## The pitch
Build an agent that answers *operational* questions from messy, fixed-camera
kitchen/restaurant footage — not a general-purpose video captioner. Target user
is a small restaurant or cloud kitchen that already has this footage and wants
plain, reliable answers out of it: who did what, did a required step happen,
was something visible/missing/late, or is it simply undeterminable from frame.

Typical footage style: prep counter, packing station, fryer line, handoff
shelf, dish area, storage corner. Fixed camera, real working kitchen, not
staged.

## What you build
One reproducible CLI program:

```bash
python answer.py --videos ./clips --questions questions.json --out answers.json
```

- **Input:** short fixed-camera clips + a JSON file of questions per clip.
- **Output:** one JSON file of answers + a log file (runtime, frame sampling
  rate, model/API calls made, estimated cost).
- **No manual review during evaluation.** It has to run unattended, end to end,
  on hidden clips it has never seen.

## Question types you need to handle

**a. Objective answers** — yes/no, multiple choice, counts, timestamps,
durations, "not visible." Freeform scene description does not decide the
winner; structured correctness does.

**b. Operational facts** — cap/hairnet visible? container sealed before
handoff? tray left unattended too long? which station was active? when did a
bottleneck start?

**c. No guessing credit** — if an order number, face, label, or action isn't
actually visible in frame, the correct answer is "not visible." Guessing is
penalized, not rewarded. This is called out explicitly and is a common trap.

**d. Temporal reasoning** — requires event ordering across frames, not a
single-frame read: first sealed bag, last item added, duration unattended,
step immediately before serving, etc.

**e. Answer format types** (from the draft spec):
`yes/no`, `multiple choice`, `count`, `timestamp`, `duration`,
`short structured object`, `not visible`

## Dataset structure
- **Public sample clips** (1–2): come with questions AND example answers.
- **Public validation clips** (optional): questions only, no answers given.
- **Hidden final clips** (4–5): rights-cleared, anonymized, not discoverable
  online — this is what actually decides the prize. Faces, payment screens,
  receipts, phone numbers, order IDs will be blurred/excluded in these.

Public reference clips (YouTube CCTV footage builderr looked at while
designing this) will **not** be the actual scoring clips — don't over-fit to
them.

## The baseline you have to beat
1. Sample frames at 1 fps
2. Run a common vision-language model or video model
3. Run OCR where relevant
4. Answer each question independently
5. Write structured JSON output

Target baseline score is roughly 35–50% correct. If a baseline scores above
70%, the challenge is considered too easy and gets reworked; below 25%, the
questions are considered too ambiguous and get reworked. Your submission needs
to clear this baseline on the hidden clips, inside budget, to be prize-eligible.
