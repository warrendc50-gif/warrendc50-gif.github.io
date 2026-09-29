import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "content" / "posts"
DATA_DIR = ROOT / "data"
PUBLIC_DIR = ROOT / "public"


def load_config() -> dict:
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    # Secrets / per-deployment overrides come from the environment (GitHub Actions secrets).
    overrides = {
        "site_url": os.environ.get("SITE_URL"),
        "adsense_client": os.environ.get("ADSENSE_CLIENT"),
    }
    for key, value in overrides.items():
        if value:
            cfg[key] = value
    if not cfg.get("site_url"):
        # On GitHub Actions a user site lives at https://<owner>.github.io, so no setting is needed.
        owner = os.environ.get("GITHUB_REPOSITORY_OWNER")
        cfg["site_url"] = f"https://{owner}.github.io" if owner else "http://localhost:8000"
    cfg["site_url"] = cfg["site_url"].rstrip("/")
    return cfg
