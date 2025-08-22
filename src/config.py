import os

TZ = os.getenv("TZ", "America/Toronto")

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# New: hint Calendar which Google account to open (optional)
GCAL_AUTHUSER = os.getenv("GCAL_AUTHUSER")  # e.g., "my.calendar@gmail.com"

REPO_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SEEN_POSTS_PATH = os.path.join(REPO_DATA_DIR, "seen_posts.json")
LAST_RUN_PATH = os.path.join(REPO_DATA_DIR, "last_run.json")
