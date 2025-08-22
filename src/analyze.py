import re
from typing import Dict
from .utils import strip_emojis, squeeze_ws, truncate, find_dates, nearest_future

# Signals for importance & events
CRITICAL = [
    "deadline", "register", "registration", "apply", "application",
    "closes", "last day", "final day", "spots left", "limited spots", "rsvp",
    "today only", "ends today"
]
TIMEY = ["event", "workshop", "seminar", "webinar", "orientation", "meeting", "tonight", "this week", "tomorrow", "today"]

# Simple time/venue patterns
TIME_PAT = re.compile(r"\b(\d{1,2}(:\d{2})?\s?(am|pm))\b", re.I)
VENUE_PAT = re.compile(r"\b(room\s?[A-Z]?\d{1,4}|hall|auditorium|center|centre|building|lab|theatre|theater|atrium|lobby|boat|cruise|field|gym|court|campus)\b", re.I)
URL_IN_BIO_PAT = re.compile(r"(link\s+in\s+bio)", re.I)

# Lightweight sentence split
SENT_SPLIT = re.compile(r'(?<=[.!?])\s+|\n+')

def classify_importance(text: str) -> str:
    low = (text or "").lower()
    if any(k in low for k in CRITICAL):
        return "Critical"
    if any(k in low for k in TIMEY):
        return "Time-Sensitive"
    return "FYI"

def smart_summary(caption: str) -> str:
    """Generate a one-liner that favors action + info instead of raw caption."""
    cap = squeeze_ws(strip_emojis(caption))
    if not cap:
        return "(No caption)"
    # Prefer first 2 short sentences that contain action words
    parts = [p.strip() for p in SENT_SPLIT.split(cap) if p.strip()]
    # Scoring: prioritize lines with CTA verbs
    score = []
    for p in parts[:6]:  # inspect first few
        cta = sum(1 for w in ["register", "apply", "rsvp", "join", "sign up", "tickets", "deadline"] if w in p.lower())
        dates = 1 if find_dates(p) else 0
        times = 1 if TIME_PAT.search(p) else 0
        score.append((cta + dates + times, p))
    score.sort(reverse=True, key=lambda x: x[0])
    best = score[0][1] if score else parts[0]
    return truncate(best, 260)

def extract_event_fields(caption: str):
    cap = caption or ""
    # dates
    date_hits = find_dates(cap)
    date_obj = nearest_future(date_hits) if date_hits else None
    # time
    time_hit = TIME_PAT.search(cap)
    time_text = time_hit.group(0) if time_hit else ""
    # venue-ish
    venue_hit = VENUE_PAT.search(cap)
    venue_text = venue_hit.group(0) if venue_hit else ""
    # link-in-bio cue
    link_bio = bool(URL_IN_BIO_PAT.search(cap))
    return date_obj, time_text, venue_text, link_bio

def analyze_item(item: Dict) -> Dict:
    cap = item.get("caption", "") or ""
    summary = smart_summary(cap)
    importance = classify_importance(cap)
    date_obj, time_text, venue_text, link_bio = extract_event_fields(cap)

    fields = {
        **item,
        "summary": summary,
        "importance": importance,
        "date_hint": date_obj.strftime("%b %d") if date_obj else "",
        "time_hint": time_text,
        "venue_hint": venue_text,
        "link_in_bio": link_bio,
    }
    return fields
