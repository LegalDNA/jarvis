import re
from typing import Dict

# Simple, dependency-free summarizer:
# - Takes first 2 sentences or first 280 chars as a fallback.
SENT_SPLIT = re.compile(r'(?<=[.!?])\s+|\n+')

DATE_PAT = re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s?\d{1,2}\b", re.I)
KEYWORDS_CRITICAL = [
    "deadline", "register", "registration", "apply", "application",
    "today", "tomorrow", "closes", "limited spots", "rsvp", "now open",
]
KEYWORDS_TIMED = ["event", "workshop", "seminar", "webinar", "meeting", "tonight", "this week"]

def summarize_text(caption: str, max_sentences: int = 2, max_chars: int = 280) -> str:
    cap = (caption or "").strip()
    if not cap:
        return "(No caption)"
    # naive sentence split
    parts = [p.strip() for p in SENT_SPLIT.split(cap) if p.strip()]
    if parts:
        summary = " ".join(parts[:max_sentences])
    else:
        summary = cap[:max_chars]
    if len(summary) > max_chars:
        summary = summary[:max_chars].rstrip() + "…"
    return summary

def classify_importance(caption: str) -> str:
    low = (caption or "").lower()
    if any(k in low for k in KEYWORDS_CRITICAL):
        return "Critical"
    if any(k in low for k in KEYWORDS_TIMED) or DATE_PAT.search(caption or ""):
        return "Time-Sensitive"
    return "FYI"

def extract_date_hint(caption: str) -> str:
    m = DATE_PAT.search(caption or "")
    return m.group(0) if m else ""

def analyze_item(item: Dict) -> Dict:
    cap = item.get("caption", "")
    return {
        **item,
        "summary": summarize_text(cap, max_sentences=2, max_chars=280),
        "importance": classify_importance(cap),
        "date_hint": extract_date_hint(cap),
    }
