import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Iterable
from itertools import islice

import instaloader
from .utils import load_json, save_json
from .config import SEEN_POSTS_PATH, LAST_RUN_PATH, IG_USERNAME, IG_PASSWORD

POST_URL = "https://www.instagram.com/p/{shortcode}/"

# Pull at most N posts per account (prevents heavy pagination that triggers rate limits)
MAX_POSTS_PER_ACCOUNT = int(os.getenv("MAX_POSTS_PER_ACCOUNT", "8"))
# Only look back this many days
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "7"))

def _login_if_needed(L: instaloader.Instaloader):
    if IG_USERNAME and IG_PASSWORD:
        try:
            L.login(IG_USERNAME, IG_PASSWORD)
        except Exception:
            # If login fails, continue unauthenticated
            pass

def read_accounts(file_path: str) -> List[str]:
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip().lstrip("@") for line in f if line.strip()]

def _safe_iter_posts(profile) -> Iterable:
    """
    Wrap profile.get_posts() so that transient GraphQL errors (KeyError: 'data')
    or rate limit responses don't crash the whole job.
    """
    try:
        for post in profile.get_posts():
            yield post
    except Exception:
        # If Instagram blocks pagination, just stop gracefully
        return

def fetch_new_posts(accounts_file: str) -> List[Dict]:
    seen = load_json(SEEN_POSTS_PATH, default={})  # {shortcode: true}
    last_run = load_json(LAST_RUN_PATH, default={})  # {"timestamp": iso}

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

    for idx, username in enumerate(usernames):
        try:
            profile = instaloader.Profile.from_username(L.context, username)
        except Exception:
            # Skip unknown or blocked accounts
            continue

        count = 0
        for post in islice(_safe_iter_posts(profile), MAX_POSTS_PER_ACCOUNT):
            try:
                sc = getattr(post, "shortcode", None)
                if not sc or sc in seen:
                    continue

                # Skip older than cutoff
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
                count += 1
            except KeyError:
                # GraphQL “data” missing—skip this post and continue
                continue
            except Exception:
                # Any other weirdness—skip this post, keep going
                continue

        # polite tiny delay between accounts to reduce throttling
        time.sleep(0.7)

    save_json(SEEN_POSTS_PATH, seen)
    save_json(LAST_RUN_PATH, {"timestamp": datetime.utcnow().isoformat()})
    return new_items
