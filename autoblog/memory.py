"""Memory boards: topic pages (/memory/<board>/) that collect links and notes as giscus comments.

giscus (https://giscus.app) stores each board's entries as comments on a GitHub Discussion in the
blog's repository, so the static site needs no server. The operator writes the entries (the
discussions are locked on GitHub, so visitors can read but not post). Korean site only.
"""
from html import escape

GISCUS_SCRIPT = "https://giscus.app/client.js"


def giscus_html(cfg: dict, term: str) -> str:
    """The giscus embed for one board, or a notice while giscus is not configured yet."""
    g = cfg.get("giscus") or {}
    if not (g.get("repo") and g.get("repo_id") and g.get("category_id")):
        return '<p class="disclosure">게시판을 준비 중입니다. 곧 글이 올라옵니다.</p>'
    return (f'<div class="giscus"></div>\n'
            f'<script src="{GISCUS_SCRIPT}" data-repo="{escape(g["repo"])}" data-repo-id="{escape(g["repo_id"])}" '
            f'data-category="{escape(g.get("category", "Memory"))}" data-category-id="{escape(g["category_id"])}" '
            f'data-mapping="specific" data-term="{escape(term)}" data-strict="1" '
            f'data-reactions-enabled="0" data-emit-metadata="0" data-input-position="top" '
            f'data-theme="preferred_color_scheme" data-lang="ko" data-loading="lazy" '
            f'crossorigin="anonymous" async></script>')


def board_cards(cfg: dict) -> str:
    m = cfg["memory"]
    base = cfg["site_url"]
    return '<div class="cards">' + "".join(
        f'<a class="card board" href="{base}/memory/{key}/"><span class="badge memory">{b["emoji"]} Memory</span>'
        f'<h3>{escape(b["name"])}</h3><p>{escape(b["desc"])}</p></a>'
        for key, b in m["boards"].items()
    ) + "</div>"


def index_body(cfg: dict) -> str:
    m = cfg["memory"]
    return (f'<section class="hero"><span class="kicker">🗂 {escape(m["title"])}</span>'
            f'<h1>{escape(m["title"])}</h1><p>{escape(m["desc"])}</p></section>'
            f'<div class="section-head"><h2>분야</h2></div>{board_cards(cfg)}')


def board_body(cfg: dict, key: str) -> str:
    m = cfg["memory"]
    b = m["boards"][key]
    others = "".join(
        f'<a href="{cfg["site_url"]}/memory/{k}/">{o["emoji"]} {escape(o["name"])}</a>'
        for k, o in m["boards"].items() if k != key
    )
    return (f'<section class="hero"><span class="kicker">{b["emoji"]} {escape(m["title"])}</span>'
            f'<h1>{escape(b["name"])}</h1><p>{escape(b["desc"])}</p></section>'
            f'<nav class="boards">{others}</nav>'
            f'<section class="board-feed">{giscus_html(cfg, f"memory/{key}")}</section>')


def memory_pages(cfg: dict) -> list[tuple[str, str, str, str]]:
    """(path, title, description, body) for the memory index and each board."""
    m = cfg.get("memory")
    if not m or not m.get("boards"):
        return []
    pages = [("memory/", m["title"], m["desc"], index_body(cfg))]
    pages += [(f"memory/{key}/", f'{b["name"]} | {m["title"]}', b["desc"], board_body(cfg, key))
              for key, b in m["boards"].items()]
    return pages
