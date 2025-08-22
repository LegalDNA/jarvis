import os
from datetime import datetime
from src.scrape import fetch_new_posts
from src.analyze import analyze_item
from src.digest import build_markdown_digest, md_to_html
from src.send_email import send_email

# --- Optional Notion support ---
try:
    from src.notion_push import push_to_notion
    NOTION_AVAILABLE = True
except Exception:
    # No-op if Notion module isn't present
    def push_to_notion(*args, **kwargs):
        return
    NOTION_AVAILABLE = False
# --------------------------------

ACCOUNTS_FILE = os.path.join(os.path.dirname(__file__), "accounts.txt")

def run():
    raw_items = fetch_new_posts(ACCOUNTS_FILE)
    analyzed = [analyze_item(it) for it in raw_items]

    # Build and send email digest
    md = build_markdown_digest(analyzed)
    html = md_to_html(md)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    send_email(subject=f"Jarvis Brief — {today}", html_body=html, text_body=md)

    # Optional: push to Notion if available
    for it in analyzed:
        push_to_notion(it)

if __name__ == "__main__":
    run()
