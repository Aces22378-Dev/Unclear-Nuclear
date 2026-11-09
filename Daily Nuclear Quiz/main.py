"""Daily Nuclear Quiz — posts one unused multiple-choice question per run to a Discord webhook."""
import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
QUIZ_FILE = HERE / "quiz.json"
POSTED_FILE = HERE / "posted.json"

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL3", "").strip()
ROLE_ID = os.environ.get("DAILY_QUIZ_ROLE_ID", "").strip()
LETTERS = ["🇦", "🇧", "🇨", "🇩"]


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def main():
    if not WEBHOOK_URL:
        sys.exit("DISCORD_WEBHOOK_URL3 is not set.")

    quiz = load_json(QUIZ_FILE, [])
    if not quiz:
        sys.exit("quiz.json is empty or missing.")

    posted = set(load_json(POSTED_FILE, []))
    unused = [i for i in range(len(quiz)) if i not in posted]
    if not unused:  # all used — start a new cycle
        posted.clear()
        unused = list(range(len(quiz)))

    idx = random.choice(unused)
    item = quiz[idx]
    options = "\n".join(f"{LETTERS[i]}  {opt}" for i, opt in enumerate(item["options"]))
    correct = f"{LETTERS[item['answer']]} {item['options'][item['answer']]}"

    payload = {
        "username": "Daily Nuclear Quiz",
        "content": f"<@&{ROLE_ID}>" if ROLE_ID else None,
        "allowed_mentions": {"roles": [ROLE_ID]} if ROLE_ID else {"parse": []},
        "embeds": [{
            "title": "Daily Nuclear Quiz",
            "description": f"**{item['q']}**\n\n{options}",
            "color": 0xFFCC00,
            "fields": [{
                "name": "Answer (click to reveal)",
                "value": f"||{correct} — {item['why']}||",
            }],
            "footer": {"text": f"Question #{idx + 1} of {len(quiz)} · Reply with your guess before peeking!"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }],
    }

    r = requests.post(WEBHOOK_URL, json=payload, timeout=20)
    if r.status_code >= 300:
        sys.exit(f"Discord webhook failed: {r.status_code} {r.text}")

    posted.add(idx)
    POSTED_FILE.write_text(json.dumps(sorted(posted), indent=2) + "\n", encoding="utf-8")
    print(f"Posted question #{idx + 1}")


if __name__ == "__main__":
    main()
