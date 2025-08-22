import os

TZ = os.getenv("TZ", "America/Toronto")

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# Calendar UX
GCAL_AUTHUSER = os.getenv("GCAL_AUTHUSER")  # e.g., your_calendar@gmail.com

# For hosted ICS links (GitHub raw)
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")  # e.g., user/repo
GITHUB_REF_NAME = os.getenv("GITHUB_REF_NAME") or os.getenv("GITHUB_REF", "").split("/")[-1] or "main"
RAW_ICS_BASE = os.getenv("RAW_ICS_BASE")  # optional override; else auto-built

REPO_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.dirname(REPO_DIR)
REPO_DATA_DIR = os.path.join(REPO_DIR, "data")
SEEN_POSTS_PATH = os.path.join(REPO_DATA_DIR, "seen_posts.json")
LAST_RUN_PATH = os.path.join(REPO_DATA_DIR, "last_run.json")

# Where we'll write per-event ICS files
DIST_EVENTS_DIR = os.path.join(REPO_ROOT, "dist", "events")
os.makedirs(DIST_EVENTS_DIR, exist_ok=True)

def compute_raw_ics_base() -> str | None:
    if RAW_ICS_BASE:
        return RAW_ICS_BASE.rstrip("/")
    if GITHUB_REPOSITORY and GITHUB_REF_NAME:
        return f"https://raw.githubusercontent.com/{GITHUB_REPOSITORY}/{GITHUB_REF_NAME}/dist/events"
    return None
