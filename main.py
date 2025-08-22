import os
from datetime import datetime
from src.scrape import fetch_new_posts
from src.analyze import analyze_item
from src.digest import build_markdown_digest, build_html_digest
from src.send_email import send_email
from src.ics import build_ics
from src.utils import load_json
from src.config import SEEN_POSTS_PATH

try:
    from src.notion_push import push_to_notion
except Exception:
    def push_to_notion(*args, **kwargs):
        return

ACCOUNTS_FILE = os.path.join(os.path.dirname(__file__), "accounts.txt")

def run():
    # Log current seen state size
    seen_before = load_json(SEEN_POSTS_PATH, default={})
    print(f"[RUN] Seen before: {len(seen_before)} entries")

    print("[RUN] Fetching posts…")
    raw_items, meta = fetch_new_posts(ACCOUNTS_FILE)
    rate_limited = meta.get("rate_limited", False)
    print(f"[RUN] Raw items fetched: {len(raw_items)} | rate_limited={rate_limited}")

    print("[RUN] Analyzing items…")
    analyzed = [analyze_item(it) for it in raw_items]
    print(f"[RUN] Analyzed items: {len(analyzed)}")

    # Log seen state after fetch (the scraper marks newly seen)
    seen_after = load_json(SEEN_POSTS_PATH, default={})
    print(f"[RUN] Seen after: {len(seen_after)} entries (+{len(seen_after) - len(seen_before)})")

    note = "Instagram rate-limited some accounts this run; results may be partial." if rate_limited else None

    print("[RUN] Building digest…")
    md = build_markdown_digest(analyzed, note=note)
    html = build_html_digest(analyzed, note=note)
    today = datetime.utcnow().strftime("%Y-%m-%d")

    fname, ics_bytes = build_ics(analyzed)
    attachments = []
    if fname and ics_bytes:
        attachments.append((fname, ics_bytes, "text/calendar"))

    print("[RUN] Sending email…")
    send_email(subject=f"Jarvis Brief — {today}", html_body=html, text_body=md, attachments=attachments)

    for it in analyzed:
        push_to_notion(it)

    print("[RUN] Done.")

if __name__ == "__main__":
    run()
