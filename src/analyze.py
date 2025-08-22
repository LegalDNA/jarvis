import re
from datetime import timedelta
from typing import Dict, Optional
from .utils import strip_emojis, squeeze_ws, truncate, find_dates, nearest_future

CRITICAL = [
    "deadline", "register", "registration", "apply", "application",
    "closes", "last day", "final day", "spots left", "limited spots", "rsvp",
    "today only", "ends today"
]
TIMEY = ["event", "workshop", "seminar", "webinar", "orientation", "meeting", "tonight", "this week", "tomorrow", "today"]

TIME_PAT = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s?(am|pm)\b", re.I)
VENUE_PAT = re.compile(r"\b(room\s?[A-Z]?\d{1,4}|hall|auditorium|center|centre|building|lab|theatre|theater|atrium|lobby|boat|cruise|field|gym|court|campus)\b", re.I)
URL_IN_BIO_PAT = re.compile(r"(link\s+in\s+bio)", re.I)
SENT_SPLIT = re.compile(r'(?<=[.!?])\s+|\n+')

def classify_importance(text: str) -> str:
    low = (text or "").lower()
    if any(k in low for k in CRITICAL):
        return "Critical"
    if any(k in low for k in TIMEY):
        return "Time-Sensitive"
    return "FYI"

def smart_summary(caption: str) -> str:
    cap = squeeze_ws(strip_emojis(caption))
    if not cap:
        return "(No caption)"
    parts = [p.strip() for p in SENT_SPLIT.split(cap) if p.strip()]
    score = []
    for p in parts[:6]:
        cta = sum(1 for w in ["register", "apply", "rsvp", "join", "sign up", "tickets", "deadline"] if w in p.lower())
        dates = 1 if find_dates(p) else 0
        times = 1 if TIME_PAT.search(p) else 0
        score.append((cta + dates + times, p))
    score.sort(reverse=True, key=lambda x: x[0])
    best = score[0][1] if score else parts[0]
    return truncate(best, 260)

def _parse_time_to_hm(text: str) -> Optional[tuple]:
    m = TIME_PAT.search(text or "")
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2) or 0)
    ampm = (m.group(3) or "").lower()
    if ampm == "pm" and hour != 12:
        hour += 12
    if ampm == "am" and hour == 12:
        hour = 0
    return hour, minute

def extract_event_fields(caption: str):
    cap = caption or ""
    date_hits = find_dates(cap)
    date_obj = nearest_future(date_hits) if date_hits else None

    hm = _parse_time_to_hm(cap)
    time_text = f"{hm[0]:02d}:{hm[1]:02d}" if hm else ""

    venue_hit = VENUE_PAT.search(cap)
    venue_text = venue_hit.group(0) if venue_hit else ""

    link_bio = bool(URL_IN_BIO_PAT.search(cap))

    start_dt = None
    end_dt = None
    if date_obj:
        if hm:
            start_dt = date_obj.replace(hour=hm[0], minute=hm[1], second=0, microsecond=0)
        else:
            start_dt = date_obj.replace(hour=9, minute=0, second=0, microsecond=0)
        end_dt = start_dt + timedelta(hours=1)

    return date_obj, time_text, venue_text, link_bio, start_dt, end_dt

def analyze_item(item: Dict) -> Dict:
    cap = item.get("caption", "") or ""
    summary = smart_summary(cap)
    importance = classify_importance(cap)
    date_obj, time_text, venue_text, link_bio, start_dt, end_dt = extract_event_fields(cap)

    return {
        **item,
        "summary": summary,
        "importance": importance,
        "date_hint": date_obj.strftime("%b %d") if date_obj else "",
        "time_hint": time_text,
        "venue_hint": venue_text,
        "link_in_bio": link_bio,
        "start_fmt": start_dt.strftime("%Y%m%dT%H%M%S") if start_dt else "",
        "end_fmt": end_dt.strftime("%Y%m%dT%H%M%S") if end_dt else "",
    }
