import json, os
from datetime import datetime
from pytz import timezone
from .config import SEEN_POSTS_PATH, LAST_RUN_PATH, TZ

os.makedirs(os.path.dirname(SEEN_POSTS_PATH), exist_ok=True)

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
