"""CLI entry point.

  python -m autoblog generate   # write N new posts with Claude (needs ANTHROPIC_API_KEY)
  python -m autoblog build      # build static site into public/
  python -m autoblog run        # generate + build (what the daily GitHub Action runs)
  python -m autoblog share      # post not-yet-shared posts to Threads (after deploy)
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

from . import coupang, threads, topics
from .builder import build_site, load_posts, post_path
from .config import POSTS_DIR, load_config


def _safe_slug(raw: str, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", raw.lower()).strip("-")[:80]
    return slug or fallback


KST = timezone(timedelta(hours=9))


def slot_due(cfg: dict, now: datetime | None = None) -> bool:
    """True if the most recent publishing slot (e.g. 07:00 / 19:00 KST) has no generated post yet.

    GitHub's cron often fires late or skips runs, so the workflow checks hourly and only
    writes when the current slot is still empty. Hand-written posts don't fill a slot.
    """
    now = (now or datetime.now(timezone.utc)).astimezone(KST)
    hours = sorted(cfg.get("publish_hours_kst", [7, 19]))
    today = now.replace(minute=0, second=0, microsecond=0)
    starts = [today.replace(hour=h) for h in hours if h <= now.hour]
    slot_start = starts[-1] if starts else (today - timedelta(days=1)).replace(hour=hours[-1])
    generated = [datetime.fromisoformat(p["date"]) for p in load_posts() if p.get("author") != "human"]
    return not any(d >= slot_start for d in generated)


def _report_output(name: str, value) -> None:
    """Expose a value to later GitHub Actions steps (no-op outside Actions)."""
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(f"{name}={value}\n")


def generate(cfg: dict, count: int) -> int:
    from .writer import Writer  # imported lazily so `build` works without the SDK configured

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit(
            "ANTHROPIC_API_KEY 가 비어 있습니다. GitHub 저장소 Settings → Secrets and variables → "
            "Actions → 'Secrets' 탭(Variables 아님)에 이름 ANTHROPIC_API_KEY 로 등록했는지 확인하세요."
        )
    writer = Writer(cfg["model"])
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    existing_slugs = {p.stem.split("_", 1)[-1] for p in POSTS_DIR.glob("*.json")}
    written = 0

    for _ in range(count):
        queue = topics.pending_topics()
        if not queue:
            print("[topics] queue empty, asking Claude for new topics")
            topics.add_topics(writer.suggest_topics(cfg["niche"], topics.load_state()["used_topics"]))
            queue = topics.pending_topics()
            if not queue:
                print("[topics] no topics available", file=sys.stderr)
                break
        topic = queue[0]
        print(f"[write] {topic}")

        post = writer.write_post(topic, cfg["niche"])
        now = datetime.now(timezone.utc)
        slug = _safe_slug(post["slug"], now.strftime("post-%Y%m%d%H%M%S"))
        if slug in existing_slugs:
            slug = f"{slug}-{now.strftime('%Y%m%d')}"
        existing_slugs.add(slug)

        post.update(slug=slug, topic=topic, date=now.isoformat(timespec="seconds"))
        keyword = post.pop("product_keyword", "").strip()
        post["products"] = coupang.search_products(keyword, cfg["coupang_products_per_post"]) if keyword else []

        out = POSTS_DIR / f"{now.strftime('%Y-%m-%d')}_{slug}.json"
        out.write_text(json.dumps(post, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        topics.mark_used(topic)
        written += 1
        print(f"[write] saved {out.name} ({len(post['products'])} products)")
    return written


def share(cfg: dict, limit: int = 2) -> int:
    token = os.environ.get("THREADS_ACCESS_TOKEN")
    if not token:
        print("[threads] THREADS_ACCESS_TOKEN not set, skipping")
        return 0
    threads.refresh_token(token)
    state = topics.load_state()
    shared = set(state.setdefault("threads_shared", []))
    pending = [p for p in load_posts() if p["slug"] not in shared]
    # Newest first; cap per run so enabling this on an existing site doesn't flood the feed.
    done = 0
    for post in pending[:limit]:
        url = f"{cfg['site_url']}/{post_path(post)}"
        try:
            media_id = threads.share(post, url, token)
        except Exception as exc:  # one failed share shouldn't block the rest of the run
            print(f"[threads] failed to share {post['slug']}: {exc}", file=sys.stderr)
            continue
        state["threads_shared"].append(post["slug"])
        done += 1
        print(f"[threads] shared {post['slug']} -> {media_id}")
    # Older posts beyond the cap are marked shared so they are never posted later out of order.
    for post in pending[limit:]:
        state["threads_shared"].append(post["slug"])
    topics.save_state(state)
    return done


def main() -> None:
    parser = argparse.ArgumentParser(prog="autoblog")
    parser.add_argument("command", choices=["generate", "build", "run", "share"])
    parser.add_argument("--count", type=int, help="posts to generate (default: posts_per_run)")
    parser.add_argument("--if-due", action="store_true",
                        help="only generate when the current publishing slot has no post yet")
    args = parser.parse_args()

    cfg = load_config()
    count = args.count or cfg["posts_per_run"]
    if args.command in ("generate", "run"):
        if args.if_due and not slot_due(cfg):
            print("current slot already has a post, skipping")
            n = 0
        else:
            n = generate(cfg, count)
        print(f"generated {n} post(s)")
        _report_output("generated", n)
    if args.command == "share":
        print(f"shared {share(cfg)} post(s) to Threads")
    if args.command in ("build", "run"):
        n = build_site(cfg)
        print(f"built site with {n} post(s) -> public/")


if __name__ == "__main__":
    main()
