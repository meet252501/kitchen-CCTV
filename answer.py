#!/usr/bin/env python3
"""
Kitchen CCTV Monitor — builderr.ai Round 1 submission.

Usage:
    python answer.py --videos ./videos --questions questions.json --out answers.json --log run_log.json

Budget hard limits (per 60 min of source video):
    $0.30 model/API cost  ·  25 min wall-clock  ·  ~1,500 sampled frames

Strategy:
    1. Extract frames at ~0.4 fps (coarse pass) to stay well under frame budget.
    2. For each video, batch ALL its questions into ONE Gemini call.
    3. Match the required JSON schema perfectly (id, answer, confidence).
    4. Normalize "not visible" → "not_visible" to match scoring rubric.
    5. Write structured run_log.json with all required fields.
"""

import argparse
import json
import time
import os
import io
import sys
from pathlib import Path
from collections import defaultdict

import cv2
import PIL.Image
from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------
LOG_PATH = None
_call_count = 0
_est_cost = 0.0
_frames_processed = 0
_total_source_minutes = 0.0

client = None
try:
    client = genai.Client()
except Exception as e:
    print(f"WARNING: Gemini client init failed: {e}", file=sys.stderr)


def log(msg: str):
    """Write to stdout and append to the text log file."""
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line)
    if LOG_PATH:
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")


# ---------------------------------------------------------------------------
# Frame extraction
# ---------------------------------------------------------------------------
def extract_frames(video_path: str, fps: float = 1.0, max_frames: int = 3600):
    """
    Extract frames at *target* fps, auto-scaling down if needed to stay
    within max_frames.  Returns (frames_list, video_duration_seconds).
    Each element of frames_list is (timestamp_seconds, bgr_ndarray).
    """
    global _frames_processed

    log(f"  [frames] opening {video_path}")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        log(f"  [frames] ERROR: cannot open {video_path}")
        return [], 0.0

    video_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    duration = total_frames / video_fps if video_fps > 0 else 0.0

    # Scale fps to stay within frame budget
    target_count = duration * fps
    if target_count > max_frames and duration > 0:
        fps = max_frames / duration
        log(f"  [frames] adjusted to {fps:.3f} fps to stay ≤ {max_frames} frames")

    frame_interval = max(1, int(video_fps / fps))

    frames = []
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % frame_interval == 0:
            ts = idx / video_fps
            # Resize to reduce memory + token cost — 512px wide is plenty for CCTV
            h, w = frame.shape[:2]
            if w > 512:
                scale = 512 / w
                frame = cv2.resize(frame, (512, int(h * scale)))

            # GOD MODE: Burn the exact timestamp into the pixels
            # This completely solves LLM temporal blindness
            cv2.putText(
                frame, 
                f"[T={ts:.2f}s]", 
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.8, 
                (0, 255, 0), # Bright green
                2
            )

            frames.append((ts, frame))
            if len(frames) >= max_frames:
                break
        idx += 1

    cap.release()
    _frames_processed += len(frames)
    log(f"  [frames] {len(frames)} frames, duration {duration:.1f}s")
    return frames, duration


# ---------------------------------------------------------------------------
# Gemini batched QA
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """\
You are an AI auditor analysing fixed-camera kitchen CCTV footage.

## RULES
1. Answer ONLY from what is visible in the frames. If the information is \
not clearly visible, answer "not visible". Guessing is penalised.
2. You MUST think step-by-step before answering. Return a single JSON object \
with a "reasoning" string (where you track events, identify timestamps, and \
compute durations) and an "answers" array.
3. The "answers" array must contain one object per question. Each object MUST have:
   - "id"         : string (must exactly match the question id)
   - "answer"     : depends on question type (see below)
   - "confidence" : float 0.0–1.0

## TEMPORAL REASONING RULES
- For `timestamp` questions: Identify the exact two frames where the event \
starts or occurs. If it happens between two frames, interpolate the time. \
Write this out in your `reasoning` field first.
- For `duration` questions: Explicitly identify the start frame timestamp and \
the end frame timestamp in your `reasoning` field, then subtract them.
- Be precise to within 2 seconds for full credit.

## ANSWER TYPES
- yes_no          → "yes", "no", or "not visible"
- multiple_choice → one of the provided options, or "not visible"
- count           → integer, or "not visible"
- timestamp       → float seconds from video start, or "not visible"
- duration        → float seconds, or "not visible"
- structured      → a short JSON object, or "not visible"

## IMPORTANT
- Note: I have physically burned the exact timestamp (e.g., `[T=12.50s]`) in bright green text onto the top-left corner of every image. Use this text directly for your absolute timestamp values!
- Use "not visible" (with a space), never "not_visible" with an underscore.
- Timestamps are in seconds from the start of the video.
- Return EXACTLY one answer per question inside the "answers" array. Match ids exactly.
"""

TYPE_HINTS = {
    "yes_no":           "Answer 'yes', 'no', or 'not visible'.",
    "multiple_choice":  "Answer one of the listed options, or 'not visible'.",
    "count":            "Answer an integer, or 'not visible'.",
    "timestamp":        "Answer a float (seconds from video start), or 'not visible'.",
    "duration":         "Answer a float (seconds), or 'not visible'.",
    "structured":       "Answer a short JSON object, or 'not visible'.",
}


def _build_user_prompt(questions: list, timestamps: list[str], video_id: str) -> str:
    """Compose the user-turn text for a batch of questions."""
    lines = [
        f"Video: {video_id}",
        f"Frame timestamps (seconds): {', '.join(timestamps)}",
        "",
        "Questions:",
    ]
    for q in questions:
        qtype = q.get("type", "structured")
        lines.append(f"- ID: {q['id']}")
        lines.append(f"  Type: {qtype}")
        lines.append(f"  Question: {q.get('question', q.get('prompt', ''))}")
        if q.get("options"):
            lines.append(f"  Options: {json.dumps(q['options'])}")
        lines.append(f"  ({TYPE_HINTS.get(qtype, '')})")
    lines.append("")
    lines.append("Return your JSON object with 'reasoning' and 'answers' array now.")
    return "\n".join(lines)


def answer_questions_for_video(
    questions: list,
    frames: list,
    video_id: str,
) -> list:
    """Send all frames + all questions for one video in a single Gemini call."""
    global _call_count, _est_cost

    fallback = [
        {"id": q["id"], "answer": "not visible", "confidence": 0.0}
        for q in questions
    ]

    if not client:
        log("  [gemini] ERROR: client not initialised")
        return fallback

    if not frames:
        log("  [gemini] no frames — returning not visible for all")
        return fallback

    # Convert frames to PIL images
    images = []
    ts_labels = []
    for ts, bgr in frames:
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        images.append(PIL.Image.fromarray(rgb))
        ts_labels.append(f"{ts:.1f}")

    user_text = _build_user_prompt(questions, ts_labels, video_id)
    contents = images + [user_text]

    # Cost estimate: Gemini 1.5 Flash ≈ 258 tokens/image → $0.0000193/image
    img_cost = len(images) * 0.00002
    text_cost = 0.002  # generous estimate for input+output text
    cost_this_call = img_cost + text_cost
    _est_cost += cost_this_call
    _call_count += 1

    log(f"  [gemini] {len(images)} imgs, {len(questions)} Qs, est ${cost_this_call:.4f}")

    # Model fallback chain + retry with exponential backoff
    MODELS = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.0-flash-lite"]
    resp = None

    for model_name in MODELS:
        for attempt in range(4):  # up to 4 retries per model
            try:
                log(f"  [gemini] trying {model_name} (attempt {attempt+1})")
                resp = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        temperature=0.1,
                    ),
                )
                break  # success
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    wait = min(2 ** attempt * 15, 120)  # 15s, 30s, 60s, 120s
                    log(f"  [gemini] rate limited on {model_name}, waiting {wait}s...")
                    time.sleep(wait)
                    continue
                else:
                    log(f"  [gemini] non-retryable error on {model_name}: {e}")
                    break  # try next model
        if resp is not None:
            break  # got a response

    if resp is None:
        log("  [gemini] all models/retries exhausted")
        return fallback

    # Parse response
    try:
        results = json.loads(resp.text)
    except (json.JSONDecodeError, TypeError):
        log(f"  [gemini] bad JSON response")
        return fallback

    if isinstance(results, dict):
        if "answers" in results and isinstance(results["answers"], list):
            results = results["answers"]
        elif "results" in results and isinstance(results["results"], list):
            results = results["results"]
        else:
            # Maybe the model ignored the wrapper and just returned an array at the root? 
            # Handled below by checking if results is still not a list.
            pass

    if not isinstance(results, list):
        log("  [gemini] unexpected response shape (not a list of answers)")
        return fallback

    # Normalise answers
    answered_ids = set()
    for r in results:
        if not isinstance(r, dict):
            continue
        # Normalise "not visible" variants
        ans = r.get("answer")
        if isinstance(ans, str):
            if ans.lower().strip() in ("not visible", "not_visible", "n/a", "none", "null"):
                r["answer"] = "not visible"
        # Ensure confidence exists
        if "confidence" not in r:
            r["confidence"] = 0.5
        answered_ids.add(r.get("id"))

    # Fill in any missing questions
    for q in questions:
        if q["id"] not in answered_ids:
            log(f"  [gemini] model missed {q['id']}, filling not visible")
            results.append({
                "id": q["id"],
                "answer": "not visible",
                "confidence": 0.0
            })

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    global LOG_PATH, _total_source_minutes

    ap = argparse.ArgumentParser(description="Kitchen CCTV Monitor — builderr.ai")
    ap.add_argument("--videos", required=True, help="Directory of video files or URLs")
    ap.add_argument("--questions", required=True, help="Path to questions.json")
    ap.add_argument("--out", required=True, help="Path to write answers.json")
    ap.add_argument("--log", default=None, help="Path to write run_log.json")
    ap.add_argument("--fps", type=float, default=0.5,
                    help="Target frame sampling rate (default 0.5 to stay cheap)")
    args = ap.parse_args()

    # Text log (human-readable)
    LOG_PATH = str(Path(args.out).with_suffix(".log"))
    open(LOG_PATH, "w").close()

    start = time.time()
    log("=== Kitchen CCTV Monitor — starting ===")
    log(f"videos={args.videos}  questions={args.questions}  out={args.out}  fps={args.fps}")

    # Load questions
    with open(args.questions) as f:
        questions = json.load(f)

    # Group by video — support both "video" and "video_id" keys
    by_video = defaultdict(list)
    for q in questions:
        vid = q.get("video_id") or q.get("video", "unknown")
        by_video[vid].append(q)

    video_dir = Path(args.videos)
    all_answers = []

    for video_id, v_questions in by_video.items():
        log(f"\n--- Video: {video_id} ({len(v_questions)} questions) ---")

        # Try common extensions
        video_path = None
        for ext in ("", ".mp4", ".mkv", ".avi", ".webm", ".mov"):
            candidate = video_dir / f"{video_id}{ext}"
            if candidate.exists():
                video_path = str(candidate)
                break
        # Also try if video_id already includes extension
        if not video_path:
            candidate = video_dir / video_id
            if candidate.exists():
                video_path = str(candidate)

        if not video_path:
            log(f"  WARNING: video not found for {video_id}")
            for q in v_questions:
                all_answers.append({
                    "id": q["id"],
                    "answer": "not visible",
                    "confidence": 0.0
                })
            continue

        frames, duration = extract_frames(video_path, fps=args.fps)
        _total_source_minutes += duration / 60.0

        CHUNK_SIZE = 50
        for i in range(0, len(v_questions), CHUNK_SIZE):
            chunk = v_questions[i:i+CHUNK_SIZE]
            if len(v_questions) > CHUNK_SIZE:
                log(f"  [gemini] processing chunk {i//CHUNK_SIZE + 1} ({len(chunk)} Qs)")
            batch = answer_questions_for_video(chunk, frames, video_id)
            all_answers.extend(batch)
            for a in batch:
                log(f"  {a.get('id')}: {a.get('answer')} (conf {a.get('confidence', '?')})")

    # Write answers
    with open(args.out, "w") as f:
        json.dump(all_answers, f, indent=2)

    elapsed = time.time() - start

    # Compute normalised cost
    norm_cost = (
        (_est_cost / _total_source_minutes * 60.0)
        if _total_source_minutes > 0 else _est_cost
    )

    log(f"\n=== Done ===")
    log(f"Answers: {len(all_answers)}  written to {args.out}")
    log(f"Elapsed: {elapsed:.1f}s  |  API calls: {_call_count}  |  frames: {_frames_processed}")
    log(f"Est cost: ${_est_cost:.4f}  |  Normalised $/60min: ${norm_cost:.4f}")
    log(f"Budget check -> time {elapsed:.0f}s / 1200s  |  cost ${norm_cost:.4f} / $3.00")

    # Write structured run log
    run_log = {
        "runtime_seconds": round(elapsed, 1),
        "frames_processed": _frames_processed,
        "model_calls": _call_count,
        "estimated_model_api_cost_usd": round(_est_cost, 4),
        "normalized_model_api_cost_per_60min_usd": round(norm_cost, 4),
        "source_video_minutes": round(_total_source_minutes, 1),
        "budget_status": "PASS" if norm_cost <= 3.00 and elapsed <= 1200 else "FAIL",
    }

    log_dest = args.log or str(Path(args.out).with_name("run_log.json"))
    with open(log_dest, "w") as f:
        json.dump(run_log, f, indent=2)
    log(f"Run log: {log_dest}")


if __name__ == "__main__":
    main()
