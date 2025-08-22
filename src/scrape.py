import os
from datetime import datetime
from typing import List, Dict

import instaloader
from .utils import load_json, save_json
from .config import SEEN_POSTS_PATH, LAST_RUN_PATH, IG_USERNAME, IG_PASSWORD

POST_URL = "https://www.instagram.com/p/{shortcode}/"

def _login_if_needed(L):
    if IG_USERNAME and IG_PASSWORD:
        L.login(IG_USERNAME, IG_PASSWORD)

def read_accounts(file_path: str) -> List[str]:
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip().lstrip("@") for line in f if line.strip()]

def fetch_new_posts(accounts_file: str) -> List[Dict]:
    seen = load_json(SEEN_POSTS_PATH, default={})
    last_run = load_json(LAST_RUN_PATH, default={})

    L = instaloader.Instaloader(download_pictures=False,
                                download_videos=False,
                                download_video_thumbnails=False,
                                download_geotags=False,
                                download_comments=False,
                                save_metadata=False,
                                quiet=True)
    _login_if_needed(L)

    usernames = read_accounts(accounts_file)
    new_items = []

    for username in usernames:
        try:
            profile = instaloader.Profile.from_username(L.context, username)
        except Exception:
            continue

        for post in profile.get_posts():
            sc = post.shortcode
            if sc in seen:
                continue
            # Only consider posts from the last 7 days
            if (datetime.now() - post.date_utc).days > 7:
                continue

            caption = post.caption or ""
            item = {
                "account": username,
                "shortcode": sc,
                "url": POST_URL.format(shortcode=sc),
                "taken_at": post.date_utc.isoformat(),
                "caption": caption.strip(),
            }
            new_items.append(item)

    # Mark as seen
    for it in new_items:
        seen[it["shortcode"]] = True

    save_json(SEEN_POSTS_PATH, seen)
    save_json(LAST_RUN_PATH, {"timestamp": datetime.utcnow().isoformat()})

    return new_items
