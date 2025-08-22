import os
from datetime import datetime
from src.scrape import fetch_new_posts
from src.analyze import analyze_item
from src.digest import build_markdown_digest, md_to_html
from src.send_email import send_email

# --- Optional Notion support (safe import) ---
try:
    from src.notion_push import push_to_notion
except Exception:
    def push_to_notion(*args, **kwargs):  # no-op
        return
# --------------------------------------------

ACCOUNTS_FILE = os.path.join(os.path.dirname(__file__), "accounts.txt")

def run():
    print("[RUN] Fetching posts…")
    raw_items = fetch_new_posts(ACCOUNTS_FILE)
    print(f"[RUN] Raw items fetched: {len(raw_items)}")

    print("[RUN] Analyzing items…")
    analyzed = [analyze_item(it) for it in raw_items]
    print(f"[RUN] Analyzed items: {len(analyzed)}")

    print("[RUN] Building digest…")
    md = build_markdown_digest(analyzed)
    html = md_to_html(md)
    today = datetime.utcnow().strftime("%Y-%m-%d")

    print("[RUN] Sending email…")
    send_email(subject=f"Jarvis Brief — {today}", html_body=html, text_body=md)

    # Optional: push to Notion
    for it in analyzed:
        push_to_notion(it)

    print("[RUN] Done.")

if __name__ == "__main__":
    run()
