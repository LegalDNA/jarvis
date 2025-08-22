import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Iterable
from itertools import islice

import instaloader
from .utils import load_json, save_json
from .config import SEEN_POSTS_PATH, LAST_RUN_PATH, IG_USERNAME, IG_PASSWORD

POST_URL = "https://www.instagram.com/p/{shortcode}/"

MAX_POSTS_PER_ACCOUNT = int(os.getenv("MAX_POSTS_PER_ACCOUNT", "5"))
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "5"))

def _login_if_needed(L: instaloader.Instaloader):
    if IG_USERNAME and IG_PASSWORD:
        try:
            L.login(IG_USERNAME, IG_PASSWORD)
        except Exception:
            pass

def read_accounts(file_path: str) -> List[str]:
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip().lstrip("@") for line in f if line.strip()]

def _safe_iter_posts(profile) -> Iterable:
    try:
        for post in profile.get_posts():
            yield post
    except Exception:
        return

def fetch_new_posts(accounts_file: str):
    """
    Returns (items, meta) where:
      - items: List[Dict]
      - meta: {"rate_limited": bool}
    """
    seen = load_json(SEEN_POSTS_PATH, default={})
    _ = load_json(LAST_RUN_PATH, default={})

    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        quiet=True,
    )
    _login_if_needed(L)

    usernames = read_accounts(accounts_file)
    new_items: List[Dict] = []
    cutoff = datetime.utcnow() - timedelta(days=LOOKBACK_DAYS)
    rate_limited = False

    for username in usernames:
        try:
            profile = instaloader.Profile.from_username(L.context, username)
        except Exception:
            rate_limited = True
            continue

        for post in islice(_safe_iter_posts(profile), MAX_POSTS_PER_ACCOUNT):
            try:
                sc = getattr(post, "shortcode", None)
                if not sc or sc in seen:
                    continue
                if getattr(post, "date_utc", datetime(1970, 1, 1)) < cutoff:
                    continue

                caption = (post.caption or "").strip()
                item = {
                    "account": username,
                    "shortcode": sc,
                    "url": POST_URL.format(shortcode=sc),
                    "taken_at": post.date_utc.isoformat(),
                    "caption": caption,
                }
                new_items.append(item)
                seen[sc] = True
            except Exception:
                rate_limited = True
                continue

        time.sleep(1)

    save_json(SEEN_POSTS_PATH, seen)
    save_json(LAST_RUN_PATH, {"timestamp": datetime.utcnow().isoformat()})
    return new_items, {"rate_limited": rate_limited}
