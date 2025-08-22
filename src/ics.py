from datetime import datetime
from typing import List, Dict, Tuple, Optional
from .utils import squeeze_ws

ICS_HEADER = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Jarvis Brief//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
"""
ICS_FOOTER = "END:VCALENDAR\n"

def _escape(s: str) -> str:
    return (s or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

def _vevent(it: Dict, tz="America/Toronto") -> str:
    start = it.get("start_fmt"); end = it.get("end_fmt")
    if not (start and end): return ""
    uid = f"{it.get('shortcode','')}-{start}@jarvis-brief"
    title = it.get("event_title") or f"@{it.get('account','')} — Instagram event"
    desc = f"{squeeze_ws(it.get('summary',''))}\n\nPost: {it.get('url','#')}"
    loc = it.get("venue_hint","")
    return (
        "BEGIN:VEVENT\n"
        f"UID:{_escape(uid)}\n"
        f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}\n"
        f"DTSTART;TZID={tz}:{start}\n"
        f"DTEND;TZID={tz}:{end}\n"
        f"SUMMARY:{_escape(title)}\n"
        f"DESCRIPTION:{_escape(desc)}\n"
        f"LOCATION:{_escape(loc)}\n"
        "END:VEVENT\n"
    )

def build_ics(items: List[Dict], tz="America/Toronto") -> Tuple[Optional[str], Optional[bytes]]:
    events = [ _vevent(it, tz=tz) for it in items if it.get("start_fmt") and it.get("end_fmt") ]
    events = [e for e in events if e]
    if not events:
        return None, None
    content = ICS_HEADER + "".join(events) + ICS_FOOTER
    filename = f"jarvis-brief-{datetime.utcnow().strftime('%Y%m%d')}.ics"
    return filename, content.encode("utf-8")

def build_per_event_ics(items: List[Dict], tz="America/Toronto") -> List[Tuple[str, bytes, str]]:
    files = []
    for it in items:
        if not (it.get("start_fmt") and it.get("end_fmt")):
            continue
        ve = _vevent(it, tz=tz)
        if not ve:
            continue
        fname = f"event-{it.get('shortcode','')}.ics"
        content = ICS_HEADER + ve + ICS_FOOTER
        files.append((fname, content.encode("utf-8"), it.get("event_title","Event")))
    return files
