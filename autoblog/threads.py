"""Share newly published posts to Threads via the official Threads API.

Requires THREADS_ACCESS_TOKEN (a long-lived token from a Meta developer app with the
Threads use case and the threads_basic + threads_content_publish permissions).
Without it, sharing is skipped.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request

API = "https://graph.threads.net"
MAX_CHARS = 500


def _post(path: str, params: dict) -> dict:
    data = urllib.parse.urlencode(params).encode()
    with urllib.request.urlopen(urllib.request.Request(f"{API}{path}", data=data), timeout=30) as resp:
        return json.load(resp)


def compose(post: dict, url: str) -> str:
    """Title + summary + link, trimmed to the Threads length limit."""
    tail = f"\n\n👉 {url}"
    body = f"{post['title']}\n\n{post['description']}"
    room = MAX_CHARS - len(tail)
    if len(body) > room:
        body = body[: room - 1].rstrip() + "…"
    return body + tail


def refresh_token(token: str) -> None:
    """Extend the long-lived token's lifetime; warn if Meta hands back a different token."""
    query = urllib.parse.urlencode({"grant_type": "th_refresh_token", "access_token": token})
    try:
        with urllib.request.urlopen(f"{API}/refresh_access_token?{query}", timeout=30) as resp:
            data = json.load(resp)
    except urllib.error.URLError as exc:
        print(f"[threads] token refresh failed: {exc}")
        return
    days = int(data.get("expires_in", 0)) // 86400
    print(f"[threads] token valid for ~{days} more days")
    if data.get("access_token") and data["access_token"] != token:
        print("[threads] WARNING: Meta issued a new token; update the THREADS_ACCESS_TOKEN secret.")


def share(post: dict, url: str, token: str) -> str:
    """Create and publish a text post with a link preview. Returns the Threads media id."""
    container = _post("/v1.0/me/threads", {
        "media_type": "TEXT",
        "text": compose(post, url),
        "link_attachment": url,
        "access_token": token,
    })
    published = _post("/v1.0/me/threads_publish", {
        "creation_id": container["id"],
        "access_token": token,
    })
    return published["id"]
