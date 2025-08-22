import re
from datetime import timedelta
from typing import Dict, Optional
from .utils import strip_emojis, squeeze_ws, truncate, find_dates, nearest_future

# Importance signals
CRITICAL = [
    "deadline", "register", "registration", "apply", "application",
    "closes", "last day", "final day", "spots left", "limited spots", "rsvp",
    "today only", "ends today", "tickets"
]
TIMEY = [
    "event", "workshop", "seminar", "webinar", "orientation", "meeting",
    "tonight", "this week", "tomorrow", "today", "info session",
    "career fair", "case competition", "boat cruise", "tryouts", "auditions",
]

# Patterns we’ll detect
TIME_PAT = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s?(am|pm)\b", re.I)
VENUE_PAT = re.compile(r"\b(room\s?[A-Z]?\d{1,4}|hall|auditorium|center|centre|building|lab|theatre|theater|atrium|lobby|boat|cruise|field|gym|court|campus)\b", re.I)
URL_IN_BIO_PAT = re.compile(r"(link\s+in\s+bio|see\s+bio|bio\s+link)", re.I)
MONEY_PAT = re.compile(r"(\$|CAD\s?)\s?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)|\bfree\b", re.I)
EMAIL_PAT = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
URL_PAT = re.compile(r"https?://\S+")
HASHTAG_PAT = re.compile(r"#\w+")

SENT_SPLIT = re.compile(r'(?<=[.!?])\s+|\n+')
TITLE_HINT_PAT = re.compile(
    r"(orientation|boat cruise|info session|workshop|seminar|webinar|career fair|case competition|tryouts|auditions|meeting|town hall|open house|social|mixer)",
    re.I
)

def _clean_caption(caption: str) -> str:
    cap = strip_emojis(caption or "")
    cap = HASHTAG_PAT.sub("", cap)
    cap = squeeze_ws(cap)
    return cap

def classify_importance(text: str) -> str:
    low = (text or "").lower()
    if any(k in low for k in CRITICAL):
        return "Critical"
    if any(k in low for k in TIMEY):
        return "Time-Sensitive"
    return "FYI"

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

def _best_sentences(cap: str, max_chars: int = 360) -> str:
    parts = [p.strip() for p in SENT_SPLIT.split(cap) if p.strip()]
    if not parts:
        return "(No caption)"
    scored = []
    for p in parts[:8]:  # scan first few
        s = 0
        low = p.lower()
        for w in ["register", "apply", "rsvp", "join", "sign up", "tickets", "deadline", "limited", "free"]:
            if w in low: s += 2
        if find_dates(p): s += 2
        if TIME_PAT.search(p): s += 1
        scored.append((s, p))
    scored.sort(reverse=True, key=lambda x: (x[0], -len(x[1])))
    take = []
    seen = set()
    for _, sent in scored:
        if sent not in seen:
            take.append(sent)
            seen.add(sent)
        if len(take) == 2:
            break
    return truncate(" ".join(take) if take else parts[0], max_chars)

def _event_title(account: str, caption: str, date_str: str, time_str: str) -> str:
    """Hyper-specific title: '@Account — <Hint> (Mon DD, HH:MM)'"""
    hint = ""
    m = TITLE_HINT_PAT.search(caption or "")
    if m:
        hint = m.group(1).title()
    else:
        words = _clean_caption(caption).split()
        hint = " ".join(words[:5]).strip().rstrip(",.:;") or "Event"
        hint = hint.title()
    when = date_str or ""
    if time_str:
        when = f"{when}, {time_str}" if when else time_str
    return f"@{account} — {hint}" + (f" ({when})" if when else "")

def extract_event_fields(caption: str, account: str):
    cap = _clean_caption(caption)
    # Dates
    date_hits = find_dates(cap)
    date_obj = nearest_future(date_hits) if date_hits else None
    date_hint = date_obj.strftime("%b %d") if date_obj else ""

    # Time
    hm = _parse_time_to_hm(cap)
    time_hint = f"{hm[0]:02d}:{hm[1]:02d}" if hm else ""

    # Venue-ish
    venue_hit = VENUE_PAT.search(cap)
    venue_hint = venue_hit.group(0) if venue_hit else ""

    # Costs / Free
    price_hint = None
    money = MONEY_PAT.search(cap)
    if money:
        price_hint = "Free" if money.group(0).lower().strip() == "free" else money.group(0)

    # Contact / URLs
    contact_hint = EMAIL_PAT.search(cap).group(0) if EMAIL_PAT.search(cap) else ""
    url_found = URL_PAT.search(cap).group(0) if URL_PAT.search(cap) else ""
    link_bio = bool(URL_IN_BIO_PAT.search(cap))

    # Start/end (for future use or attachments)
    start_dt = end_dt = None
    if date_obj:
        if hm:
            start_dt = date_obj.replace(hour=hm[0], minute=hm[1], second=0, microsecond=0)
        else:
            start_dt = date_obj.replace(hour=9, minute=0, second=0, microsecond=0)
        end_dt = start_dt + timedelta(hours=1)

    title = _event_title(account, cap, date_hint, time_hint)

    return {
        "date_hint": date_hint,
        "time_hint": time_hint,
        "venue_hint": venue_hint,
        "price_hint": price_hint or "",
        "contact_hint": contact_hint,
        "url_found": url_found,
        "link_in_bio": link_bio,
        "start_fmt": start_dt.strftime("%Y%m%dT%H%M%S") if start_dt else "",
        "end_fmt": end_dt.strftime("%Y%m%dT%H%M%S") if end_dt else "",
        "event_title": title,
    }

def analyze_item(item: Dict) -> Dict:
    cap = item.get("caption", "") or ""
    account = item.get("account", "")
    clean_cap = _clean_caption(cap)

    # Importance & summary
    importance = classify_importance(clean_cap)
    summary = _best_sentences(clean_cap, max_chars=360)

    fields = extract_event_fields(clean_cap, account)

    return {
        **item,
        "summary": summary,
        "importance": importance,
        **fields,
    }
