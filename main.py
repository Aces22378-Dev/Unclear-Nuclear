import json
import os
import re
import hashlib
from html import unescape
from pathlib import Path

import feedparser
import requests

ROOT = Path(__file__).parent
SEEN_FILE = ROOT / "seen.json"
FEEDS_FILE = ROOT / "feeds.json"
WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"]
ROLE_ID = os.getenv("OUTSIDER_NEWS_ROLE_ID", "").strip()
MAX_SEEN = 1000
MAX_PER_RUN = 8

def clean(value, limit=350):
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = unescape(re.sub(r"\s+", " ", value)).strip()
    return value[:limit] + ("…" if len(value) > limit else "")

def load_seen():
    if SEEN_FILE.exists():
        try:
            return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass
    return set()

def save_seen(seen):
    SEEN_FILE.write_text(
        json.dumps(sorted(seen)[-MAX_SEEN:], indent=2),
        encoding="utf-8"
    )

def entry_id(entry):
    stable = entry.get("id") or entry.get("link") or (
        entry.get("title", "") + entry.get("published", "")
    )
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()

def send_to_discord(source, entry):
    title = clean(entry.get("title", "New nuclear science story"), 240)
    link = entry.get("link", "").strip()
    summary = clean(entry.get("summary", entry.get("description", "")), 500)
    if not link.startswith(("https://", "http://")):
        return

    payload = {
        "content": f"<@&{ROLE_ID}>" if ROLE_ID else None,
        "allowed_mentions": {"parse": [], "roles": [ROLE_ID] if ROLE_ID else []},
        "embeds": [{
            "title": title,
            "url": link,
            "description": summary or "Open the article for details.",
            "color": 0x64748B,
            "footer": {"text": f"Source: {source} • Unclear Nuclear"}
        }]
    }
    response = requests.post(WEBHOOK, json=payload, timeout=20)
    response.raise_for_status()

def main():
    seen = load_seen()
    fresh = []
    feeds = json.loads(FEEDS_FILE.read_text(encoding="utf-8"))

    for feed in feeds:
        parsed = feedparser.parse(feed["url"])
        if parsed.bozo and not parsed.entries:
            print(f"Feed unavailable: {feed['name']}")
            continue
        for entry in parsed.entries[:30]:
            key = entry_id(entry)
            if key not in seen:
                fresh.append((feed["name"], entry, key))

    fresh = fresh[:MAX_PER_RUN]
    for source, entry, key in fresh:
        send_to_discord(source, entry)
        seen.add(key)
        print(f"Posted: {entry.get('title', '(untitled)')}")

    save_seen(seen)
    print(f"Finished. Posted {len(fresh)} new item(s).")

if __name__ == "__main__":
    main()
