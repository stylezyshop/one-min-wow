"""
Central config for the daily Shorts automation.

Niche: Psychology + Human Behavior

The bot rotates through psychology and human-behavior topics
so the channel stays focused while still having variety.
"""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


# ============================================================
# CONTENT NICHE
# ============================================================

TOPICS = [
    {
        "niche": "everyday_psychology",
        "prompt_hint": (
            "one surprising, evidence-based psychology insight about "
            "everyday human behavior. Focus on something people commonly "
            "experience but rarely understand, such as why we procrastinate, "
            "why certain memories stick, why habits are difficult to break, "
            "why people seek approval, or why emotions can affect decisions. "
            "Explain the psychological mechanism clearly without exaggeration "
            "or pop-psychology myths."
        ),
        "visual_keywords": [
            "person thinking",
            "person making decision",
            "human brain",
            "person working",
            "person looking thoughtful",
        ],
        "hashtags": "#psychology #humanbehavior #mindset #education #shorts",
    },
    {
        "niche": "social_behavior",
        "prompt_hint": (
            "one surprising, evidence-based insight about how people behave "
            "around other people. Focus on topics such as social influence, "
            "group behavior, conformity, first impressions, social norms, "
            "attention, cooperation, or why people behave differently in "
            "groups. Make the explanation concrete and relatable. Do not "
            "claim that one behavior can reveal someone's personality or "
            "intentions with certainty."
        ),
        "visual_keywords": [
            "people talking",
            "friends conversation",
            "crowd people",
            "people meeting",
            "social interaction",
        ],
        "hashtags": "#psychology #humanbehavior #socialpsychology #facts #shorts",
    },
    {
        "niche": "cognitive_biases",
        "prompt_hint": (
            "one fascinating, well-established cognitive bias or mental "
            "shortcut that affects everyday decisions. Explain what the "
            "bias is, give a simple real-life example, and explain why the "
            "human brain can fall into this pattern. Prefer well-established "
            "concepts such as confirmation bias, anchoring, availability "
            "heuristic, framing effects, or the sunk cost effect. Avoid "
            "invented psychology terminology."
        ),
        "visual_keywords": [
            "person making decision",
            "brain thinking",
            "choice decision",
            "person comparing options",
            "abstract brain",
        ],
        "hashtags": "#psychology #cognitivebias #humanbehavior #science #shorts",
    },
    {
        "niche": "relationships_communication",
        "prompt_hint": (
            "one evidence-based psychology insight about communication, "
            "relationships, or interpersonal behavior. Focus on topics such "
            "as listening, misunderstandings, emotional reactions, conflict, "
            "communication patterns, trust, boundaries, or how people "
            "interpret social signals. Keep it educational rather than "
            "giving absolute relationship advice. Never claim that a single "
            "texting pattern, gesture, or behavior proves that someone likes, "
            "hates, loves, or is manipulating another person."
        ),
        "visual_keywords": [
            "couple talking",
            "friends talking",
            "conversation",
            "person listening",
            "people communicating",
        ],
        "hashtags": "#psychology #relationships #communication #humanbehavior #shorts",
    },
]


# ============================================================
# UPLOAD SETTINGS
# ============================================================

VIDEOS_PER_DAY = 3


# Uploads and reports must target this channel.
SILENTVISION_CHANNEL_ID = "UCkZ3jcHOWcMfFJ9jvGAkeOw"
SILENTVISION_CHANNEL_TITLE = "One Minute Wow"


# ============================================================
# POSTING WINDOWS
# ============================================================

# These are fallback/manual scheduling values.
# The GitHub Actions workflow controls the normal scheduled runs
# using US Eastern time:
# 12 PM / 6 PM / 9 PM America/New_York

POST_WINDOWS = (
    {"name": "morning", "utc_hour": 16},
    {"name": "afternoon", "utc_hour": 22},
    {"name": "night", "utc_hour": 1},
)

SLOT_NAMES = {window["name"]: index for index, window in enumerate(POST_WINDOWS)}


def slot_for_now(name: str | None = None) -> int:
    """
    Map a window name or the current UTC hour to slot 0, 1, or 2.

    Scheduled GitHub Actions runs normally provide POST_SLOT directly,
    so this function mainly supports manual/local execution.
    """
    if name:
        key = name.strip().lower()

        if key.isdigit():
            return max(0, min(VIDEOS_PER_DAY - 1, int(key)))

        if key in SLOT_NAMES:
            return SLOT_NAMES[key]

    from datetime import datetime, timezone

    hour = datetime.now(timezone.utc).hour

    if hour < 19:
        return 0

    if hour < 23:
        return 1

    return 2


def pick_topic_for_slot(slot: int = 0):
    """
    Each daily window posts one psychology niche.

    Slot 0, 1, 2 rotate through TOPICS, shifted by day-of-year
    so the order changes from day to day.
    """
    import datetime

    day_index = datetime.date.today().timetuple().tm_yday

    return TOPICS[(day_index + int(slot)) % len(TOPICS)]


def pick_topic_for_today():
    return pick_topic_for_slot(slot_for_now())


# ============================================================
# VIDEO SETTINGS
# ============================================================

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920  # vertical, for Shorts

TARGET_DURATION_SECONDS = 45
MIN_DURATION_SECONDS = 40

# TTS jitter allowance.
MAX_DURATION_SECONDS = 55


# Spoken at the end of every Short.
END_CTA = "Follow One Minute Wow for more psychology and human behavior."


# ============================================================
# CAPTIONS
# ============================================================

FONT_SIZE = 60
CAPTION_COLOR = "white"
CAPTION_HIGHLIGHT_COLOR = "#FFD700"


# ============================================================
# TEXT-TO-SPEECH
# ============================================================

TTS_VOICE = "en-US-GuyNeural"


# ============================================================
# OUTPUT
# ============================================================

WORKDIR = "workdir"
