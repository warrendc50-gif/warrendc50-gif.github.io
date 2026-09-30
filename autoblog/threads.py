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
    try:
        with urllib.request.urlopen(urllib.request.Request(f"{API}{path}", data=data), timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        # Meta puts the actual reason in the response body; surface it in the workflow log.
        raise RuntimeError(f"{exc} {exc.read().decode(errors='replace')[:500]}") from None


def compose(post: dict, url: str, intro: str | None = None) -> str:
    """Intro (or title + summary) + link, trimmed to the Threads length limit."""
    tail = f"\n\n👉 {url}"
    body = intro or f"{post['title']}\n\n{post['description']}"
    room = MAX_CHARS - len(tail)
    if len(body) > room:
        body = body[: room - 1].rstrip() + "…"
    return body + tail


def refresh_token(token: str) -> str | None:
    """Extend the long-lived token's lifetime. Returns the new token if Meta issued a different one."""
    query = urllib.parse.urlencode({"grant_type": "th_refresh_token", "access_token": token})
    try:
        with urllib.request.urlopen(f"{API}/refresh_access_token?{query}", timeout=30) as resp:
            data = json.load(resp)
    except urllib.error.URLError as exc:
        detail = exc.read().decode(errors="replace")[:300] if isinstance(exc, urllib.error.HTTPError) else ""
        print(f"[threads] token refresh failed: {exc} {detail}")
        return None
    days = int(data.get("expires_in", 0)) // 86400
    print(f"[threads] token valid for ~{days} more days")
    new = data.get("access_token")
    return new if new and new != token else None


def share(post: dict, url: str, token: str, intro: str | None = None) -> str:
    """Create and publish a text post with a link preview. Returns the Threads media id."""
    container = _post("/v1.0/me/threads", {
        "media_type": "TEXT",
        "text": compose(post, url, intro),
        "link_attachment": url,
        "access_token": token,
    })
    published = _post("/v1.0/me/threads_publish", {
        "creation_id": container["id"],
        "access_token": token,
    })
    return published["id"]
