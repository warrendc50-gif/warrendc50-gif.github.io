"""Merge newly collected news items into the Memory board data files.

usage: python scripts/update_memory.py <update.json> [--no-net]

<update.json> is an object {"<board-key>": [item, ...], ...}. Each item needs date, headline,
headline_ko, outlet, url, summary_ko, topics, orgs and may carry video (YouTube watch URL).

For every item: the date must be valid, topics are reduced to the keys allowed for that board,
the article URL must respond (404/410 drops the item; blocked or timing-out hosts are kept),
a video must resolve through YouTube's oEmbed (its channel name is stored as video_channel),
and items already present (same URL, or near-identical headline) are skipped. Items are then
appended to data/memory/<board>.json, newest first. Prints what was added and what was skipped.
"""
import concurrent.futures as cf
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "memory"
sys.path.insert(0, str(ROOT))
from autoblog.memory import TOPIC_LABELS  # noqa: E402

BOARD_TOPICS = {
    "ai-news": {"model", "chips", "policy", "business", "research", "korea"},
    "korea-economy": {"rates", "fx", "stocks", "realestate", "banks", "policy", "crypto", "global"},
    "world-economy": {"fed", "centralbank", "markets", "trade", "energy", "china", "macro", "crisis", "crypto"},
    "world-live": {"unrest", "conflict", "disaster", "accident", "terror", "politics", "health", "economy"},
}
REQUIRED = {"date", "headline", "headline_ko", "outlet", "url", "summary_ko", "topics", "orgs"}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}


def _norm_url(u: str) -> str:
    return u.rstrip("/").lower()


def _norm_head(h: str) -> str:
    return re.sub(r"\W+", "", h.lower())[:60]


def _load(board: str):
    path = DATA / f"{board}.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    items = data["items"] if isinstance(data, dict) else data
    return data, items


def _save(board: str, data, items: list[dict]) -> None:
    items.sort(key=lambda i: i["date"], reverse=True)
    if isinstance(data, dict):
        data["items"] = items
    else:
        data = items
    (DATA / f"{board}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _url_status(url: str):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=15) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:  # timeouts, TLS quirks, bot walls: unknown, not dead
        return f"ERR {type(e).__name__}"


def _video_channel(video: str):
    """Channel name via oEmbed, or None when the video does not exist."""
    q = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(video, safe="")
    try:
        with urllib.request.urlopen(urllib.request.Request(q, headers=UA), timeout=15) as r:
            return json.load(r).get("author_name", "")
    except Exception:
        return None


def _check(item: dict, net: bool):
    status = _url_status(item["url"]) if net else 200
    channel = None
    if item.get("video") and net:
        channel = _video_channel(item["video"])
    return item, status, channel


def main(path: str, net: bool = True) -> int:
    update = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    total_added = 0
    for board, new_items in update.items():
        if board not in BOARD_TOPICS:
            print(f"[{board}] unknown board, skipped")
            continue
        data, items = _load(board)
        seen_url = {_norm_url(i["url"]) for i in items}
        seen_head = {_norm_head(i["headline"]) for i in items}
        candidates, skipped = [], []
        for it in new_items:
            miss = REQUIRED - set(it)
            if miss:
                skipped.append(f"missing {sorted(miss)}: {it.get('headline', '')[:50]}"); continue
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", it["date"]) or not it["url"].startswith("http"):
                skipped.append(f"bad date/url: {it['date']} {it['url'][:60]}"); continue
            if _norm_url(it["url"]) in seen_url or _norm_head(it["headline"]) in seen_head:
                skipped.append(f"duplicate: {it['date']} {it['headline'][:60]}"); continue
            it["topics"] = [t for t in it["topics"] if t in BOARD_TOPICS[board]] or [sorted(BOARD_TOPICS[board])[0]]
            seen_url.add(_norm_url(it["url"])); seen_head.add(_norm_head(it["headline"]))
            candidates.append(it)
        added = []
        with cf.ThreadPoolExecutor(8) as ex:
            for it, status, channel in ex.map(lambda i: _check(i, net), candidates):
                if status in (404, 410):
                    skipped.append(f"dead link {status}: {it['url']}"); continue
                if isinstance(status, str):
                    print(f"[{board}] unverified (kept): {status} {it['url']}")
                if it.get("video"):
                    if channel is None and net:
                        print(f"[{board}] video dropped (not found): {it['video']}")
                        it["video"] = ""
                    else:
                        it["video_channel"] = channel or it.get("video_channel", "")
                it.pop("_id", None)
                added.append(it)
        if added:
            _save(board, data, items + added)
        total_added += len(added)
        print(f"[{board}] added {len(added)}, skipped {len(skipped)}")
        for a in added:
            print(f"   + {a['date']} {a['outlet']} | {a['headline_ko'][:60]}{'  ▶' if a.get('video') else ''}")
        for s_ in skipped:
            print(f"   - {s_}")
    return total_added


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__); sys.exit(2)
    n = main(args[0], net="--no-net" not in sys.argv)
    print(f"total added: {n}")
