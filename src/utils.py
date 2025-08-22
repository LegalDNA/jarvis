import json, os, re
from datetime import datetime, timedelta
from pytz import timezone
from dateparser.search import search_dates
from .config import SEEN_POSTS_PATH, LAST_RUN_PATH, TZ

os.makedirs(os.path.dirname(SEEN_POSTS_PATH), exist_ok=True)

EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+", flags=re.UNICODE
)

def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def now_local_iso():
    return datetime.now(timezone(TZ)).isoformat()

def strip_emojis(s: str) -> str:
    return EMOJI_RE.sub("", s or "")

def squeeze_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def truncate(s: str, n: int) -> str:
    s = s or ""
    return s if len(s) <= n else s[:n-1].rstrip() + "…"

def find_dates(text: str, base=None):
    """Return list of (text, dt) timezone-naive; we’ll display only."""
    if not text:
        return []
    try:
        return search_dates(text, settings={"PREFER_DATES_FROM": "future"}, languages=["en"]) or []
    except Exception:
        return []

def nearest_future(dts):
    """Pick the nearest future datetime from a list of parsed date results."""
    now = datetime.now()
    future = [dt for (_, dt) in dts if dt >= now]
    if future:
        return min(future)
    # else fallback: any date, choose max
    anyd = [dt for (_, dt) in dts]
    return max(anyd) if anyd else None
