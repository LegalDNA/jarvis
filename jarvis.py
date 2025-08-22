import os, re, json, smtplib, time
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from dateutil import tz
import pandas as pd
import instaloader

# ---- Time setup ----
LOCAL_TZ = tz.gettz("America/Toronto")
NOW_UTC = datetime.now(timezone.utc)
SINCE_UTC = NOW_UTC - timedelta(days=int(os.getenv("LOOKBACK_DAYS", "1")))

# ---- Accounts ----
with open("accounts.txt", "r", encoding="utf-8") as f:
    ACCOUNTS = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

# ---- Instaloader config ----
L = instaloader.Instaloader(
    download_pictures=False,
    download_video_thumbnails=False,
    download_videos=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False,
    dirname_pattern=".",
    filename_pattern="{shortcode}"
)

IG_USER = os.getenv("IG_USERNAME")
IG_PASS = os.getenv("IG_PASSWORD")
if IG_USER and IG_PASS:
    try:
        L.login(IG_USER, IG_PASS)
        print("Logged in to Instagram.")
    except Exception as e:
        print("Login failed; continuing without login:", e)

def clean_text(t):
    t = re.sub(r'\s+', ' ', t or '').strip()
    return t

posts_data = []
for i, handle in enumerate(ACCOUNTS, 1):
    try:
        profile = instaloader.Profile.from_username(L.context, handle)
        count_added = 0
        for post in profile.get_posts():
            created_utc = post.date_utc.replace(tzinfo=timezone.utc)
            if created_utc < SINCE_UTC:
                break  # posts are reverse-chronological
            caption = clean_text(post.caption)
            posts_data.append({
                "account": handle,
                "shortcode": post.shortcode,
                "url": f"https://www.instagram.com/p/{post.shortcode}/",
                "created_utc": created_utc.isoformat(),
                "created_local": created_utc.astimezone(LOCAL_TZ).strftime("%Y-%m-%d %H:%M"),
                "caption": caption
            })
            count_added += 1
        print(f"@{handle}: {count_added} posts in window.")
    except Exception as e:
        print(f"Failed on @{handle}: {e}")
    time.sleep(float(os.getenv("ACCOUNT_DELAY_SEC", "2")))  # gentle throttle

df = pd.DataFrame(posts_data).sort_values("created_utc", ascending=False)

# ---- Summarizer (local HF model) ----
MODEL_NAME = os.getenv("MODEL_NAME", "sshleifer/distilbart-cnn-12-6")  # good quality & fast
MAX_LEN = int(os.getenv("SUM_MAX_TOKENS", "96"))
MIN_LEN = int(os.getenv("SUM_MIN_TOKENS", "24"))

summary_available = False
try:
    from transformers import pipeline
    summarizer = pipeline("summarization", model=MODEL_NAME, framework="pt")
    summary_available = True
    print(f"Loaded summarizer model: {MODEL_NAME}")
except Exception as e:
    print("Summarizer not available, will fallback to truncated captions. Error:", e)

def summarize_text(txt, max_chars=1200):
    txt = (txt or "").strip()
    if not txt:
        return ""
    txt = txt[:max_chars]
    if summary_available:
        try:
            out = summarizer(txt, max_length=MAX_LEN, min_length=MIN_LEN, do_sample=False)
            return out[0]["summary_text"].strip()
        except Exception as e:
            print("Summarization error:", e)
    # fallback
    return (txt[:180] + ("…" if len(txt) > 180 else ""))

def reason_tag(txt):
    t = (txt or "").lower()
    # weight-based quick scoring
    rules = [
        ("Deadline", ["deadline", "apply", "register", "due", "closes", "last day", "rsvp by"]),
        ("Event", ["event", "workshop", "seminar", "talk", "webinar", "info session", "orientation", "panel"]),
        ("Hiring", ["hiring", "recruit", "applications open", "positions", "intern", "apply now", "join our team"]),
        ("Funding", ["scholarship", "grant", "bursary", "funding"]),
        ("Competition", ["case competition", "hackathon", "pitch", "moot", "debate"]),
        ("Academic", ["exam", "midterm", "lecture", "class", "tutorial", "assignment"]),
        ("Admin", ["closure", "hours", "update", "policy", "procedure"]),
    ]
    for tag, keys in rules:
        if any(k in t for k in keys):
            return tag
    return "General"

if not df.empty:
    df["summary"] = df["caption"].apply(summarize_text)
    df["tag"] = df["caption"].apply(reason_tag)
else:
    df["summary"] = []
    df["tag"] = []

# ---- Build Markdown report ----
date_str = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d")
title = f"Instagram Morning Brief — {date_str}"
lines = [f"# {title}", "", f"_Covers posts since last {int(os.getenv('LOOKBACK_DAYS','1'))} day(s) — generated {datetime.now(LOCAL_TZ).strftime('%Y-%m-%d %H:%M %Z')}_", ""]

if df.empty:
    lines.append("> No new posts from your tracked accounts in the last window.")
else:
    grouped = df.groupby("account")
    for acct, g in grouped:
        lines.append(f"## @{acct}")
        for _, r in g.iterrows():
            lines.append(f"- **{r['tag']}** — {r['created_local']} — {r['url']}")
            if r["summary"]:
                lines.append(f"  - {r['summary']}")
            if r["caption"]:
                cap = r["caption"][:320]
                lines.append(f"  - _Orig:_ {cap}{'…' if len(r['caption'])>320 else ''}")
        lines.append("")

report_md = "\n".join(lines)

os.makedirs("reports", exist_ok=True)
report_path = f"reports/{date_str}.md"
with open(report_path, "w", encoding="utf-8") as f:
    f.write(report_md)

print(f"Report generated at {report_path}")

# ---- Email delivery (optional) ----
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL", GMAIL_USER or "")

def send_email(subject, body, to_email):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = to_email
    import smtplib
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, [to_email], msg.as_string())

if GMAIL_USER and GMAIL_APP_PASSWORD and TO_EMAIL:
    try:
        send_email(title, report_md, TO_EMAIL)
        print("Email sent.")
    except Exception as e:
        print("Email failed:", e)
else:
    print("Email not configured; skipping email send.")

# ---- Notion delivery (optional) ----
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")
if NOTION_TOKEN and NOTION_PAGE_ID:
    import requests
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    payload = {
        "parent": {"page_id": NOTION_PAGE_ID},
        "properties": {
            "title": [{"type": "text", "text": {"content": title}}]
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": report_md}}]
                }
            }
        ]
    }
    try:
        r = requests.post("https://api.notion.com/v1/pages",
                          headers=headers, data=json.dumps(payload))
        print("Notion status:", r.status_code)
    except Exception as e:
        print("Notion push failed:", e)
