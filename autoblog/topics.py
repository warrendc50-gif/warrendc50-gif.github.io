"""Topic queue: data/topics.txt holds candidates, data/state.json records what was used."""
import json

from .config import DATA_DIR

TOPICS_FILE = DATA_DIR / "topics.txt"
STATE_FILE = DATA_DIR / "state.json"


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"used_topics": []}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def pending_topics() -> list[str]:
    if not TOPICS_FILE.exists():
        return []
    used = set(load_state()["used_topics"])
    lines = TOPICS_FILE.read_text(encoding="utf-8").splitlines()
    return [t.strip() for t in lines if t.strip() and not t.startswith("#") and t.strip() not in used]


def add_topics(topics: list[str]) -> None:
    existing = TOPICS_FILE.read_text(encoding="utf-8") if TOPICS_FILE.exists() else ""
    if existing and not existing.endswith("\n"):
        existing += "\n"
    TOPICS_FILE.write_text(existing + "\n".join(topics) + "\n", encoding="utf-8")


def mark_used(topic: str) -> None:
    state = load_state()
    state["used_topics"].append(topic)
    save_state(state)
