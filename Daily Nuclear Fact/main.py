"""Daily Nuclear Fact — posts one unused fact per run to a Discord webhook."""
import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
FACTS_FILE = HERE / "facts.json"
POSTED_FILE = HERE / "posted.json"

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL2", "").strip()
ROLE_ID = os.environ.get("DAILY_FACT_ROLE_ID", "").strip()


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def main():
    if not WEBHOOK_URL:
        sys.exit("DISCORD_WEBHOOK_URL2 is not set.")

    facts = load_json(FACTS_FILE, [])
    if not facts:
        sys.exit("facts.json is empty or missing.")

    posted = set(load_json(POSTED_FILE, []))
    unused = [i for i in range(len(facts)) if i not in posted]

    # Every fact used once? Start a new cycle.
    if not unused:
        posted.clear()
        unused = list(range(len(facts)))

    idx = random.choice(unused)
    fact = facts[idx]

    payload = {
        "username": "Daily Nuclear Fact",
        "content": f"<@&{ROLE_ID}>" if ROLE_ID else None,
        "allowed_mentions": {"roles": [ROLE_ID]} if ROLE_ID else {"parse": []},
        "embeds": [{
            "title": "Daily Nuclear Fact",
            "description": fact,
            "color": 0xB6FF3B,
            "footer": {"text": f"Fact #{idx + 1} of {len(facts)} · Unclear Nuclear"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }],
    }

    r = requests.post(WEBHOOK_URL, json=payload, timeout=20)
    if r.status_code >= 300:
        sys.exit(f"Discord webhook failed: {r.status_code} {r.text}")

    posted.add(idx)
    POSTED_FILE.write_text(json.dumps(sorted(posted), indent=2) + "\n", encoding="utf-8")
    print(f"Posted fact #{idx + 1}")


if __name__ == "__main__":
    main()
