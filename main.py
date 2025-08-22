import os
from datetime import datetime
from src.scrape import fetch_new_posts
from src.analyze import analyze_item
from src.digest import build_markdown_digest, build_html_digest
from src.send_email import send_email
from src.ics import build_ics, build_per_event_ics
from src.utils import load_json
from src.config import SEEN_POSTS_PATH, DIST_EVENTS_DIR

try:
    from src.notion_push import push_to_notion
except Exception:
    def push_to_notion(*args, **kwargs): return

ACCOUNTS_FILE = os.path.join(os.path.dirname(__file__), "accounts.txt")

def run():
    seen_before = load_json(SEEN_POSTS_PATH, default={})
    print(f"[RUN] Seen before: {len(seen_before)} entries")

    print("[RUN] Fetching posts…")
    raw_items, meta = fetch_new_posts(ACCOUNTS_FILE)
    rate_limited = meta.get("rate_limited", False)
    print(f"[RUN] Raw items fetched: {len(raw_items)} | rate_limited={rate_limited}")

    print("[RUN] Analyzing items…")
    analyzed = [analyze_item(it) for it in raw_items]
    print(f"[RUN] Analyzed items: {len(analyzed)}")

    # Prepare per-event ICS files & attach them
    per_event = build_per_event_ics(analyzed)  # list of (fname, bytes, title)
    attachments = []
    for fname, data, _title in per_event:
        # write into dist/events for hosted links
        out_path = os.path.join(DIST_EVENTS_DIR, fname)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(data)
        attachments.append((fname, data, "text/calendar"))

    # Combined ICS as well (backup / one-click import)
    combo_name, combo_bytes = build_ics(analyzed)
    if combo_name and combo_bytes:
        attachments.append((combo_name, combo_bytes, "text/calendar"))

    seen_after = load_json(SEEN_POSTS_PATH, default={})
    print(f"[RUN] Seen after: {len(seen_after)} entries (+{len(seen_after) - len(seen_before)})")

    note = "Instagram rate-limited some accounts this run; results may be partial." if rate_limited else None

    print("[RUN] Building digest…")
    md = build_markdown_digest(analyzed, note=note)
    html = build_html_digest(analyzed, note=note)
    today = datetime.utcnow().strftime("%Y-%m-%d")

    print("[RUN] Sending email…")
    send_email(subject=f"Jarvis Brief — {today}", html_body=html, text_body=md, attachments=attachments)

    for it in analyzed:
        push_to_notion(it)

    print("[RUN] Done.")

if __name__ == "__main__":
    run()
