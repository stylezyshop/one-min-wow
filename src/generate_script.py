"""
Generates a short video script using Groq's free-tier LLM API
(OpenAI-compatible endpoint).

Niche: Psychology + Human Behavior

The generator creates short, curiosity-driven psychology and human
behavior videos for the One Minute Wow YouTube Shorts channel.
"""

import os
import json
import urllib.error
import urllib.request
from pathlib import Path

from config import END_CTA, TARGET_DURATION_SECONDS

USED_TOPICS_PATH = (
    Path(__file__).resolve().parent.parent
    / "reports"
    / "used_topics.json"
)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Groq model fallbacks.
GROQ_MODELS = (
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
)

# Counted after the follow CTA is attached.
# ~2.7 words/sec on GuyNeural lands around 45 seconds.
MIN_SCRIPT_WORDS = 122
MAX_SCRIPT_WORDS = 148

SCRIPT_ATTEMPTS = 6


def _with_cta(script: str) -> str:
    """Make sure the spoken follow line is at the end, once."""
    text = (script or "").strip()
    lowered = text.lower()

    if (
        "follow one minute wow" in lowered
        or "follow this channel" in lowered
        or "subscribe" in lowered
    ):
        return text

    if text and text[-1] not in ".!?":
        text += "."

    return f"{text} {END_CTA}".strip()


def record_used_topic(topic_key: str) -> None:
    """
    Remember a topic only after the Short is long enough to upload.
    """
    key = (topic_key or "").strip().lower()

    if not key:
        return

    used = []

    if USED_TOPICS_PATH.exists():
        try:
            used = json.loads(
                USED_TOPICS_PATH.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError:
            used = []

    if key in [str(item).lower() for item in used]:
        return

    used.append(key)

    USED_TOPICS_PATH.parent.mkdir(parents=True, exist_ok=True)

    USED_TOPICS_PATH.write_text(
        json.dumps(used, indent=2),
        encoding="utf-8",
    )


def generate_script(topic: dict, length_hint: str = "") -> dict:
    """
    Returns:

    {
        "title": "...",
        "script": "...",
        "keywords": [...],
        "topic_key": "..."
    }

    'script' is the exact narration text that the TTS voice will read.
    """

    api_key = os.environ["GROQ_API_KEY"]

    used = []

    if USED_TOPICS_PATH.exists():
        try:
            used = json.loads(
                USED_TOPICS_PATH.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError:
            used = []

    # ============================================================
    # SYSTEM PROMPT
    # ============================================================

    system_prompt = (
        "You write YouTube Shorts for One Minute Wow, a channel focused "
        "on psychology and human behavior. "

        "The channel explains fascinating, evidence-based psychological "
        "effects, cognitive biases, social behavior, communication patterns, "
        "decision-making, habits, memory, attention, emotions, and everyday "
        "human behavior. "

        "The goal is to make viewers think: "
        "'Wait, I do that.' or 'I never knew that's why people do that.' "

        "Do NOT write about animals, space, anatomy facts, finance, "
        "motivation, generic self-help, celebrity gossip, or random trivia. "

        "Do NOT use fake psychology, invented studies, fake statistics, "
        "made-up psychological terms, or viral social-media myths. "

        "Do NOT diagnose people. "

        "Do NOT claim that one behavior proves someone is a narcissist, "
        "liar, psychopath, manipulator, insecure, attracted to someone, "
        "or any other personality or mental-health condition. "

        "Do NOT present body-language myths as scientific facts. "

        "When discussing a psychological effect, explain the actual "
        "mechanism in simple language and use a relatable everyday example. "

        "If a claim is uncertain, controversial, poorly supported, or "
        "depends heavily on context, choose a different topic. "

        "Structure the narration in this order: "

        "1) HOOK: The first sentence must be 8-12 words and immediately "
        "create curiosity. Open with a surprising psychological observation, "
        "contradiction, question-like claim, or hidden mechanism. "

        "Never start with 'Did you know', 'Imagine', 'What if', "
        "'Hey guys', or 'Welcome back'. "

        "2) PSYCHOLOGY: Explain the psychological concept in clear, "
        "simple language. Avoid academic jargon unless you immediately "
        "explain it. "

        "3) EVERYDAY EXAMPLE: Give a concrete situation viewers can "
        "recognize from normal life, such as texting, shopping, working, "
        "studying, arguing, making decisions, remembering something, "
        "or interacting with friends. "

        "4) TWIST: Reveal the less obvious part of the psychology that "
        "makes the viewer rethink the behavior. "

        "5) CLOSE: End with one short memorable sentence that rewards "
        "the viewer for watching. Do not ask people to follow, subscribe, "
        "like, or comment because the follow line is added automatically. "

        f"Spoken length must land near {TARGET_DURATION_SECONDS} seconds. "

        "Write enough narration to produce a natural 40-55 second Short. "

        "Use punchy spoken English. Short sentences are preferred. "
        "No filler. No stage directions. No emojis in the script. "

        "The content should sound like a smart friend explaining something "
        "fascinating, not like a university lecture. "

        "The opening should create curiosity without using clickbait that "
        "makes an unsupported scientific claim. "

        "Titles must be under 70 characters and contain no hashtags. "

        "Title style should be curiosity-driven and specific. "
        "Examples of acceptable styles include: "
        "'Why Your Brain Keeps Thinking About That One Person', "
        "'The Psychology Behind Why You Procrastinate', "
        "'Why Rejection Can Feel So Much Worse Than Expected', "
        "'Your Brain Does This When You See a Price First', "
        "'Why Arguments Rarely Go the Way You Expect'. "

        "Do not copy these examples. Create an original title based on "
        "the actual psychology topic. "

        "Keywords must be concrete stock-footage search terms related "
        "to the scene or concept. Avoid abstract keywords like "
        "'psychology' or 'human behavior' by themselves. "

        "For example, use terms such as "
        "'person checking phone', 'friends arguing', "
        "'person making decision', 'shopping aisle', "
        "'person studying', or 'people talking'. "

        "Output ONLY valid JSON. No markdown fences. "

        "JSON schema: "
        '{"title": "<catchy title>", '
        '"script": "<narration text>", '
        '"keywords": ["<3-5 concrete visual search keywords>"], '
        '"topic_key": "<short lowercase phrase naming the exact psychology concept>"}'
    )

    # ============================================================
    # USER PROMPT
    # ============================================================

    avoid = "; ".join(used[:40]) if used else "none yet"

    user_prompt = (
        f"Write a Psychology + Human Behavior YouTube Short based on "
        f"this topic direction:\n\n"
        f"{topic['prompt_hint']}\n\n"

        f"Make the first sentence the strongest curiosity hook. "

        f"Explain one specific psychological concept rather than listing "
        f"multiple unrelated facts. "

        f"Make the explanation useful and easy for a U.S. audience to "
        f"understand without requiring psychology knowledge. "

        f"Use a realistic everyday example. "

        f"Target about {TARGET_DURATION_SECONDS} seconds spoken. "

        f"Write enough for a {TARGET_DURATION_SECONDS} second read-aloud: "
        f"{MIN_SCRIPT_WORDS - 12}-{MAX_SCRIPT_WORDS - 12} words before "
        f"the follow line. "

        f"Do not reuse any of these already-posted topics or facts: "
        f"{avoid}"
    )

    if length_hint:
        user_prompt += f"\n{length_hint}"

    last_error = None
    data = None
    best = None
    best_distance = None

    target_words = (
        MIN_SCRIPT_WORDS + MAX_SCRIPT_WORDS
    ) // 2

    # ============================================================
    # CANDIDATE VALIDATION
    # ============================================================

    def _score_candidate(candidate, model):
        nonlocal last_error
        nonlocal data
        nonlocal best
        nonlocal best_distance

        candidate["script"] = _with_cta(
            candidate.get("script") or ""
        )

        script = candidate["script"]

        word_count = len(script.split())

        print(
            f"Groq model used: {model} "
            f"({word_count} words with CTA)"
        )

        if not script or not candidate.get("title"):
            last_error = (
                f"{model} returned empty title or script"
            )
            print(last_error)
            return False

        distance = abs(word_count - target_words)

        if best is None or distance < best_distance:
            best = candidate
            best_distance = distance

        if (
            word_count < MIN_SCRIPT_WORDS
            or word_count > MAX_SCRIPT_WORDS
        ):
            last_error = (
                f"{model} wrote {word_count} words, "
                f"need {MIN_SCRIPT_WORDS}-{MAX_SCRIPT_WORDS}"
            )
            print(last_error)
            return False

        data = candidate

        return True

    # ============================================================
    # GROQ REQUEST
    # ============================================================

    def _chat(model, messages, force_json):
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
        }

        if force_json:
            payload["response_format"] = {
                "type": "json_object"
            }

        req = urllib.request.Request(
            GROQ_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "yt-automation/1.0",
                "Accept": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(
            req,
            timeout=60,
        ) as resp:
            return json.loads(
                resp.read().decode("utf-8")
            )

    # ============================================================
    # MODEL FALLBACK / RETRY LOOP
    # ============================================================

    for attempt in range(SCRIPT_ATTEMPTS):

        model = GROQ_MODELS[
            attempt % len(GROQ_MODELS)
        ]

        extra = ""

        if attempt > 0:
            extra = (
                f" Previous draft was the wrong length. "
                f"Rewrite it to {MIN_SCRIPT_WORDS}-"
                f"{MAX_SCRIPT_WORDS} spoken words including "
                f"a natural ending. "

                "Keep the same core psychology concept but expand "
                "the explanation, everyday example, and twist with "
                "specific useful detail. "

                "Do not pad with filler. "
                "Do not introduce another unrelated psychology topic."
            )

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt + extra,
            },
        ]

        try:

            result = _chat(
                model,
                messages,
                force_json=True,
            )

        except urllib.error.HTTPError as exc:

            body = exc.read().decode(
                "utf-8",
                errors="replace",
            )[:400]

            last_error = (
                f"{exc.code} {exc.reason}: {body}"
            )

            print(
                f"Groq model {model} failed: "
                f"{last_error}"
            )

            if "json_validate_failed" not in body:
                continue

            try:

                print(
                    f"Retrying {model} without forced JSON mode"
                )

                result = _chat(
                    model,
                    messages,
                    force_json=False,
                )

            except urllib.error.HTTPError as retry_exc:

                retry_body = retry_exc.read().decode(
                    "utf-8",
                    errors="replace",
                )[:400]

                last_error = (
                    f"{retry_exc.code} "
                    f"{retry_exc.reason}: "
                    f"{retry_body}"
                )

                print(
                    f"Groq model {model} failed: "
                    f"{last_error}"
                )

                continue

        # ========================================================
        # PARSE JSON
        # ========================================================

        content = (
            result["choices"][0]["message"]["content"]
            or ""
        ).strip()

        if content.startswith("```"):

            content = content.strip("`")

            if content.lower().startswith("json"):
                content = content[4:].strip()

        try:

            candidate = json.loads(content)

        except json.JSONDecodeError as exc:

            last_error = (
                f"invalid JSON from {model}: {exc}"
            )

            print(last_error)

            continue

        # ========================================================
        # VALIDATE CANDIDATE
        # ========================================================

        if _score_candidate(
            candidate,
            model,
        ):
            break

    # ============================================================
    # USE CLOSEST VALID DRAFT IF NECESSARY
    # ============================================================

    if data is None and best is not None:

        print(
            "Using closest draft after "
            "word-count retries"
        )

        data = best

    if data is None:

        raise RuntimeError(
            f"Groq script generation failed "
            f"(no {MIN_SCRIPT_WORDS}-"
            f"{MAX_SCRIPT_WORDS} word draft): "
            f"{last_error}"
        )

    # ============================================================
    # FINALIZE
    # ============================================================

    print("CTA:", END_CTA)

    if not data.get("keywords"):
        data["keywords"] = topic["visual_keywords"]

    return data


# ================================================================
# LOCAL TEST
# ================================================================

if __name__ == "__main__":

    from config import pick_topic_for_today

    topic = pick_topic_for_today()

    output = generate_script(topic)

    print(
        json.dumps(
            output,
            indent=2,
        )
    )
