# Prep Checklist

## Right now (before dataset drops)
- [ ] Send interest email to submit@builderr.ai, subject "Kitchen video QA interest"
- [ ] Get `answer.py` skeleton running end-to-end on any local kitchen-style clip
- [ ] Wire up basic 1fps frame sampling — matches the baseline you have to beat
- [ ] Pick your VLM/OCR combo now and sanity-test cost per clip against the $3 budget cap
- [ ] Build explicit "not visible" branch logic — don't let the model guess when nothing's in frame
- [ ] Build a separate temporal-reasoning path (event ordering / duration / "before X happened") — this is a distinct failure mode from single-frame QA
- [ ] Add logging from day one: runtime, frames sampled, model/API calls, running cost estimate
- [ ] Test on both a short real-CCTV-style clip and a longer clip to check runtime scales inside the 20-minute cap

## Once the dataset/spec goes live
- [ ] Re-check this doc against the actual published spec — draft rules may shift
- [ ] Run against the public sample clip(s) with provided answers — this is your ground truth to tune against
- [ ] Run against public validation clips (questions only) as a blind check
- [ ] Confirm total runtime + cost on the full clip set stays under budget with margin — going over is disqualifying, not just a point loss
- [ ] Do a full clean-environment run (fresh clone, no cached state) to make sure the one-command interface actually works unattended
- [ ] Submit via the process builderr specifies at launch

## Common trap to avoid
Don't optimize purely for accuracy. Budget efficiency (15 pts) and going over
the hard budget (disqualifying) mean a leaner, slightly-less-accurate pipeline
that reliably finishes in budget will beat a heavier one that risks timing out
or blowing the cost cap.
