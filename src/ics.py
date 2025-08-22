from datetime import datetime
from typing import List, Dict

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
    start = it.get("start_fmt")
    end = it.get("end_fmt")
    if not (start and end):
        return ""
    uid = f"{it.get('shortcode','')}-{start}@jarvis-brief"
    summary = f"@{it.get('account','')} — Instagram event"
    desc = f"{it.get('summary','')}\n\nPost: {it.get('url','#')}"
    loc = it.get("venue_hint","")
    return (
        "BEGIN:VEVENT\n"
        f"UID:{_escape(uid)}\n"
        f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}\n"
        f"DTSTART;TZID={tz}:{start}\n"
        f"DTEND;TZID={tz}:{end}\n"
        f"SUMMARY:{_escape(summary)}\n"
        f"DESCRIPTION:{_escape(desc)}\n"
        f"LOCATION:{_escape(loc)}\n"
        "END:VEVENT\n"
    )

def build_ics(items: List[Dict], tz="America/Toronto"):
    events = []
    for it in items:
        ve = _vevent(it, tz=tz)
        if ve:
            events.append(ve)
    if not events:
        return None, None
    content = ICS_HEADER + "".join(events) + ICS_FOOTER
    filename = f"jarvis-brief-{datetime.utcnow().strftime('%Y%m%d')}.ics"
    return filename, content.encode("utf-8")
