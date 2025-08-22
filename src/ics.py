from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from pytz import timezone, utc
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
        "STATUS:CONFIRMED\n"
        "TRANSP:OPAQUE\n"
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

# ---------- Inline INVITE blocks (METHOD:REQUEST) for Gmail/Apple ----------
INVITE_HEADER = """BEGIN:VCALENDAR
PRODID:-//Jarvis Brief//EN
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:REQUEST
"""
INVITE_FOOTER = "END:VCALENDAR\n"

def _local_fmt_to_utc_z(fmt_str: str, tz_name: str = "America/Toronto") -> str:
    """Convert 'YYYYMMDDTHHMMSS' (local) to UTC 'YYYYMMDDTHHMMSSZ'."""
    tz = timezone(tz_name)
    dt_local = tz.localize(datetime.strptime(fmt_str, "%Y%m%dT%H%M%S"))
    dt_utc = dt_local.astimezone(utc)
    return dt_utc.strftime("%Y%m%dT%H%M%SZ")

def _invite_vevent(it: Dict, organizer_email: str, attendee_email: str, tz_name="America/Toronto") -> str:
    start = it.get("start_fmt"); end = it.get("end_fmt")
    if not (start and end): return ""
    uid = f"{it.get('shortcode','')}-{start}@jarvis-brief"
    title = it.get("event_title") or f"@{it.get('account','')} — Instagram event"
    desc = f"{squeeze_ws(it.get('summary',''))}\\n\\nPost: {it.get('url','#')}"
    loc = it.get("venue_hint","")
    dtstart_z = _local_fmt_to_utc_z(start, tz_name)
    dtend_z = _local_fmt_to_utc_z(end, tz_name)
    dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    return (
        "BEGIN:VEVENT\n"
        f"UID:{_escape(uid)}\n"
        f"DTSTAMP:{dtstamp}\n"
        f"DTSTART:{dtstart_z}\n"
        f"DTEND:{dtend_z}\n"
        f"SUMMARY:{_escape(title)}\n"
        f"DESCRIPTION:{desc}\n"
        f"LOCATION:{_escape(loc)}\n"
        "STATUS:CONFIRMED\n"
        "TRANSP:OPAQUE\n"
        f"ORGANIZER:mailto:{organizer_email}\n"
        f"ATTENDEE;ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=TRUE:mailto:{attendee_email}\n"
        "SEQUENCE:0\n"
        "END:VEVENT\n"
    )

def build_invite_blocks(items: List[Dict], organizer_email: str, attendee_email: str, tz_name="America/Toronto") -> List[Tuple[str, bytes]]:
    """
    Return a list of (filename, bytes) where each bytes is a text/calendar
    iCalendar invite (METHOD:REQUEST) for a single event.
    """
    invites = []
    for it in items:
        if not (it.get("start_fmt") and it.get("end_fmt")):
            continue
        ve = _invite_vevent(it, organizer_email, attendee_email, tz_name)
        if not ve:
            continue
        fname = f"invite-{it.get('shortcode','')}.ics"
        content = INVITE_HEADER + ve + INVITE_FOOTER
        invites.append((fname, content.encode("utf-8")))
    return invites
