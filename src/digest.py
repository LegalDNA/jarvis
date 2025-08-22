from collections import defaultdict
from typing import List, Dict

def build_markdown_digest(items: List[Dict]) -> str:
    if not items:
        return "# Jarvis Brief\n\nNo new posts from tracked accounts in the last 24h."

    grouped = defaultdict(list)
    for it in items:
        grouped[it["account"]].append(it)

    lines = ["# Jarvis Brief\n"]
    for account in sorted(grouped.keys()):
        lines.append(f"## @{account}")
        for it in sorted(grouped[account], key=lambda x: x.get("importance", "z")):
            lines.append(f"- **{it['importance']}** — [{it['url']}]({it['url']})")
            if it.get("date_hint"):
                lines.append(f"  - **Date hint:** {it['date_hint']}")
            lines.append(f"  - {it['summary']}")
            lines.append("")
    return "\n".join(lines)

def md_to_html(md: str) -> str:
    # Minimal HTML for email — no external deps
    html = md.replace("\n\n", "<br><br>").replace("\n", "<br>")
    html = html.replace("**", "")
    return f"<html><body>{html}</body></html>"
