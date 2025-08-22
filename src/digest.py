from typing import List, Dict
from datetime import datetime, timedelta

PRIORITY_ORDER = {"Critical": 0, "Time-Sensitive": 1, "FYI": 2}

CSS = """
  body { font-family: Arial, Helvetica, sans-serif; color:#0f172a; }
  .title { font-size:20px; font-weight:800; margin:0 0 12px; }
  .section { margin:22px 0 6px; font-weight:800; font-size:15px; text-transform:uppercase; letter-spacing:0.5px; color:#334155; }
  .card { border:1px solid #e5e7eb; border-radius:10px; padding:12px; margin:10px 0; background:#ffffff; }
  .meta { color:#475569; font-size:13px; margin:3px 0; }
  .sum { margin:8px 0 6px; line-height:1.35; }
  .k { font-weight:700; color:#0f172a; }
  .account { color:#64748b; font-size:12px; margin-bottom:6px; }
  .pill { display:inline-block; font-size:11px; padding:2px 8px; border-radius:999px; background:#eef2ff; color:#3730a3; margin-left:6px; }
  .btn { display:inline-block; padding:8px 12px; border-radius:8px; text-decoration:none; background:#0b57d0; color:#fff; font-weight:600; }
"""

def _parse_start_date(it: Dict):
    sf = it.get("start_fmt", "")
    if not sf:
        return None
    try:
        return datetime.strptime(sf, "%Y%m%dT%H%M%S")
    except Exception:
        return None

def _bucket_label(dt: datetime | None) -> str:
    if dt is None:
        return "Upcoming"  # unknown date → bottom group
    today = datetime.now().date()
    d = dt.date()
    if d == today:
        return "Today"
    if 0 < (d - today).days <= 7:
        return "This Week"
    return "Upcoming"

def _when_line(it: Dict) -> str:
    datep = it.get("date_hint","")
    timep = it.get("time_hint","")
    if datep and timep:
        return f"{datep} @ {timep}"
    return datep or timep or "TBD"

def _action_line(it: Dict) -> str:
    if it.get("url_found"):
        return f"Use link: {it['url_found']}"
    if it.get("link_in_bio"):
        return "Link in bio"
    return "See post"

def _card_html(it: Dict) -> str:
    account = it.get("account","")
    url = it.get("url","#")
    importance = it.get("importance","FYI")
    when = _when_line(it)
    where = it.get("venue_hint","")
    price = it.get("price_hint","")
    contact = it.get("contact_hint","")
    title = it.get("event_title","Event")

    rows = [
        f"<div class='meta'><span class='k'>What:</span> {title}</div>",
        f"<div class='meta'><span class='k'>When:</span> {when}</div>",
    ]
    if where:
        rows.append(f"<div class='meta'><span class='k'>Where:</span> {where.title()}</div>")
    if price:
        rows.append(f"<div class='meta'><span class='k'>Cost:</span> {price}</div>")
    action = _action_line(it)
    rows.append(f"<div class='meta'><span class='k'>Action:</span> {action}</div>")
    if contact:
        rows.append(f"<div class='meta'><span class='k'>Contact:</span> {contact}</div>")

    return f"""
      <div class="card">
        <div class="account">@{account} <span class="pill">{importance}</span></div>
        {' '.join(rows)}
        <div class="sum">{it.get('summary','')}</div>
        <a class="btn" href="{url}">Open Post</a>
      </div>
    """

def build_markdown_digest(items: List[Dict], note: str | None = None) -> str:
    # Plaintext fallback (kept simple)
    if not items and not note:
        return "# Jarvis Brief\n\nNo new posts."
    lines = ["# Jarvis Brief\n"]
    if note: lines.append(f"> {note}\n")
    for it in sorted(items, key=lambda x: (PRIORITY_ORDER.get(x.get("importance","FYI"), 3), x.get("account",""))):
        when = _when_line(it)
        lines.append(f"- @{it['account']} [{it['importance']}] {it.get('event_title','Event')} — {when} — {it['url']}")
    return "\n".join(lines)

def build_html_digest(items: List[Dict], note: str | None = None) -> str:
    if not items and not note:
        return f"<html><head><style>{CSS}</style></head><body><div class='title'>Jarvis Brief</div>No new posts.</body></html>"

    # Group into Today / This Week / Upcoming by start date (unknown → Upcoming)
    buckets = {"Today": [], "This Week": [], "Upcoming": []}
    for it in items:
        buckets[_bucket_label(_parse_start_date(it))].append(it)

    html = [f"<html><head><style>{CSS}</style></head><body>"]
    html.append("<div class='title'>Jarvis Brief</div>")
    if note:
        html.append(f"<div class='section' style='text-transform:none;color:#334155;background:#f1f5f9;padding:8px;border-radius:8px'>{note}</div>")

    # Within each section, sort by (priority, date, account)
    for section in ["Today", "This Week", "Upcoming"]:
        group = buckets[section]
        if not group: continue
        html.append(f"<div class='section'>{section}</div>")
        group_sorted = sorted(
            group,
            key=lambda x: (
                PRIORITY_ORDER.get(x.get("importance","FYI"), 3),
                x.get("start_fmt","99999999999999"),
                x.get("account",""),
            )
        )
        for it in group_sorted:
            html.append(_card_html(it))

    html.append("</body></html>")
    return "".join(html)
