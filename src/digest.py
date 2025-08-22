from typing import List, Dict
from urllib.parse import quote

PRIORITY_ORDER = {"Critical": 0, "Time-Sensitive": 1, "FYI": 2}

CSS = """
  body { font-family: Arial, Helvetica, sans-serif; color:#111; }
  .title { font-size:20px; font-weight:700; margin:0 0 12px; }
  .banner { background:#fff8e1; border:1px solid #ffe082; padding:10px; border-radius:6px; margin:10px 0; }
  .section { margin:18px 0 10px; font-weight:700; font-size:16px; }
  .card {
    border:1px solid #eee; border-radius:8px; padding:12px; margin:10px 0;
    background:#fff;
  }
  .meta { color:#444; font-size:13px; margin:4px 0; }
  .sum { margin:6px 0 10px; }
  .btn {
    display:inline-block; padding:8px 12px; border-radius:6px; text-decoration:none;
    background:#0b57d0; color:#fff; font-weight:600; margin-right:8px;
  }
  .account { color:#666; font-size:12px; }
"""

def _gcal_url(it: Dict) -> str:
    """Generate a Google Calendar template URL if start/end available."""
    start = it.get("start_fmt", "")
    end = it.get("end_fmt", "")
    if not (start and end):
        return ""
    text = f"@{it.get('account','')} — Instagram event"
    details = f"{it.get('summary','')}\n\nPost: {it.get('url','#')}"
    location = it.get("venue_hint","")
    base = "https://calendar.google.com/calendar/render?action=TEMPLATE"
    return (
        f"{base}&text={quote(text)}&dates={quote(start + '/' + end)}"
        f"&details={quote(details)}"
        f"&location={quote(location)}"
    )

def _card_html(it: Dict) -> str:
    date_line = f"<div class='meta'><b>Date:</b> {it.get('date_hint','')}</div>" if it.get("date_hint") else ""
    time_line = f"<div class='meta'><b>Time:</b> {it.get('time_hint','')}</div>" if it.get("time_hint") else ""
    venue_line = f"<div class='meta'><b>Venue:</b> {it.get('venue_hint','').title()}</div>" if it.get("venue_hint") else ""
    cta_line = "<div class='meta'><b>Action:</b> Check link in bio</div>" if it.get("link_in_bio") else ""
    account = it.get("account","")
    url = it.get("url","#")
    importance = it.get("importance","FYI")
    gcal = _gcal_url(it)

    add_btn = f"<a class='btn' href=\"{gcal}\">Add to Google Calendar</a>" if gcal else ""
    open_btn = f"<a class='btn' href=\"{url}\">Open Post</a>"

    return f"""
      <div class="card">
        <div class="account">@{account} • <b>{importance}</b></div>
        {date_line}{time_line}{venue_line}{cta_line}
        <div class="sum">{it.get('summary','')}</div>
        {add_btn}{open_btn}
      </div>
    """

def build_markdown_digest(items: List[Dict], note: str | None = None) -> str:
    if not items and not note:
        return "# Jarvis Brief\n\nNo new posts from tracked accounts in the last 24h."
    lines = ["# Jarvis Brief\n"]
    if note:
        lines.append(f"> {note}\n")
    for it in sorted(items, key=lambda x: (PRIORITY_ORDER.get(x.get("importance","FYI"), 3), x.get("account",""))):
        line = f"- @{it['account']} [{it['importance']}] {it['url']}"
        if it.get("date_hint"):
            line += f" (Date: {it['date_hint']})"
        if it.get("time_hint"):
            line += f" (Time: {it['time_hint']})"
        lines.append(line)
    return "\n".join(lines)

def build_html_digest(items: List[Dict], note: str | None = None) -> str:
    if not items and not note:
        return f"<html><head><style>{CSS}</style></head><body><div class='title'>Jarvis Brief</div>No new posts from tracked accounts in the last 24h.</body></html>"

    groups = {"Critical": [], "Time-Sensitive": [], "FYI": []}
    for it in items:
        groups.get(it.get("importance","FYI"), groups["FYI"]).append(it)

    html = [f"<html><head><style>{CSS}</style></head><body>"]
    html.append("<div class='title'>Jarvis Brief</div>")
    if note:
        html.append(f"<div class='banner'>{note}</div>")

    for section in ["Critical", "Time-Sensitive", "FYI"]:
        if not groups[section]:
            continue
        html.append(f"<div class='section'>{section}</div>")
        for it in sorted(groups[section], key=lambda x: (x.get("account",""), x.get("date_hint",""))):
            html.append(_card_html(it))

    html.append("</body></html>")
    return "".join(html)
