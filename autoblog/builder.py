"""Builds the static site (HTML, sitemap, RSS, robots.txt, ads.txt) into public/.

The Korean site lives at the root. Each language in config["translations"] (e.g. en, ja) gets its
own site under /<lang>/, holding the posts that carry that translation (post["en"], post["ja"]).
"""
import json
import re
import shutil
from datetime import datetime, timezone
from html import escape
from pathlib import Path

import markdown

from .config import POSTS_DIR, PUBLIC_DIR, ROOT
from .memory import MEMORY_CSS, memory_pages
from . import words
from .tools import TOOL_CSS, TOOLS, render_tool_body, tool_list_html

FONT_CSS = "https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css"

CSS = """
:root{--bg:#fbfaf7;--surface:#fff;--fg:#1f2328;--muted:#6b6f76;--line:#e7e4dc;--card:#f3f1ea;
  --accent:#0f766e;--accent-soft:#e0f2ef;--work:#b45309;--work-soft:#fdf0e1;--life:#0f766e;--life-soft:#e0f2ef}
@media (prefers-color-scheme:dark){:root{--bg:#141517;--surface:#1c1d20;--fg:#ecedee;--muted:#9ea3aa;--line:#2c2e33;
  --card:#23252a;--accent:#5eead4;--accent-soft:#12302c;--work:#fbbf24;--work-soft:#33260f;--life:#5eead4;--life-soft:#12302c}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);-webkit-font-smoothing:antialiased;
  font:16px/1.7 "Pretendard Variable",Pretendard,-apple-system,"Apple SD Gothic Neo","Noto Sans KR","Hiragino Sans","Noto Sans JP",sans-serif;word-break:keep-all}
.wrap{max-width:960px;margin:0 auto;padding:0 16px}
a{color:var(--accent)}
.site-header{position:sticky;top:0;z-index:10;background:color-mix(in srgb,var(--bg) 88%,transparent);
  backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.site-header .wrap{display:flex;align-items:center;gap:12px;min-height:48px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:8px;color:var(--fg);text-decoration:none;font-weight:800;font-size:17px;letter-spacing:-.02em}
.brand .mark{display:grid;place-items:center;width:28px;height:28px;border-radius:8px;background:var(--accent);color:var(--bg);font-size:16px}
.nav{display:flex;flex-wrap:nowrap;gap:2px;margin-left:auto}
.navgroup{position:relative}
figure{margin:18px 0;text-align:center}figure svg{max-width:100%;height:auto}figcaption{color:var(--muted);font-size:13px;margin-top:6px}
.navgroup summary{list-style:none;cursor:pointer;white-space:nowrap;padding:5px 9px;border-radius:8px;color:var(--muted);font-size:14px;font-weight:600}
.navgroup summary::-webkit-details-marker{display:none}
.navgroup summary::after{content:" ▾";font-size:11px}
.navgroup.on summary,.navgroup summary:hover,.navgroup[open] summary{background:var(--card);color:var(--fg)}
.navgroup.langs .menu{left:auto;right:0;min-width:110px}
.navgroup .menu{position:absolute;top:100%;left:0;z-index:20;display:flex;flex-direction:column;min-width:150px;margin-top:4px;padding:6px;background:var(--bg);border:1px solid var(--line);border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.12)}
.nav a{white-space:nowrap;padding:5px 9px;border-radius:8px;color:var(--muted);text-decoration:none;font-size:14px;font-weight:600}
.nav a:hover,.nav a.on{background:var(--card);color:var(--fg)}
@media (max-width:560px){.nav{margin-left:0;width:100%;padding-bottom:6px;justify-content:space-between}.nav>a,.navgroup summary{padding:5px 4px;font-size:13px;letter-spacing:-.03em}.navgroup summary::after{content:""}.site-header .wrap{gap:4px;padding-top:6px}}
h1{font-size:28px;line-height:1.3;letter-spacing:-.03em;margin:20px 0 8px}
h2{font-size:22px;line-height:1.35;letter-spacing:-.02em;margin:30px 0 10px}
h3{font-size:18px;margin:22px 0 6px}
.meta{color:var(--muted);font-size:14px}
.hero{display:flex;align-items:baseline;flex-wrap:wrap;gap:4px 12px;padding:12px 0 0}
.hero .kicker{display:inline-block;font-size:12px;font-weight:700;color:var(--accent);background:var(--accent-soft);padding:2px 8px;border-radius:99px}
.hero h1{font-size:22px;margin:0}
.hero p{color:var(--muted);margin:0;font-size:14px}
.section-head{display:flex;align-items:baseline;justify-content:space-between;gap:12px;margin:22px 0 8px}
.section-head h2{margin:0;font-size:18px}
.section-head a{font-size:14px;font-weight:600;text-decoration:none;white-space:nowrap}
.cards{display:grid;gap:10px;grid-template-columns:repeat(auto-fill,minmax(290px,1fr))}
.card{display:block;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px 14px 11px;
  text-decoration:none;color:var(--fg);transition:border-color .15s,transform .15s}
.card:hover{border-color:var(--accent);transform:translateY(-1px)}
.card h3{margin:6px 0 4px;font-size:16px;line-height:1.4;letter-spacing:-.02em}
.card p{margin:0 0 6px;color:var(--muted);font-size:14px;line-height:1.5;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.card .meta{font-size:12.5px}
.badge{display:inline-block;font-size:12px;font-weight:700;padding:3px 8px;border-radius:6px}
.badge.work{color:var(--work);background:var(--work-soft)}
.badge.life{color:var(--life);background:var(--life-soft)}
.badge.broadcast{color:#7c3aed;background:rgba(124,58,237,.12)}
.badge.memory{color:#2563eb;background:rgba(37,99,235,.12)}
.badge.money{color:#047857;background:rgba(4,120,87,.12)}
.badge.tech{color:#0369a1;background:rgba(3,105,161,.12)}
.badge.science{color:#4338ca;background:rgba(67,56,202,.12)}
.badge.travel{color:#c2410c;background:rgba(194,65,12,.12)}
.badge.growth{color:#a16207;background:rgba(161,98,7,.12)}
.badge.math{color:#be185d;background:rgba(190,24,93,.12)}
.badge.english{color:#1d4ed8;background:rgba(29,78,216,.12)}
.badge.gram1,.badge.gram2,.badge.gram3{color:#0f766e;background:rgba(15,118,110,.12)}
.boards{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 24px}
.boards a{font-size:14px;font-weight:600;text-decoration:none;color:var(--muted);background:var(--card);padding:6px 12px;border-radius:99px}
.boards a:hover{color:var(--fg)}
.board-feed{margin-top:8px}
.qa{background:var(--surface);border:1px solid var(--accent);border-radius:12px;padding:10px 14px;margin:18px 0 0}
.qa a{font-weight:600;white-space:nowrap}
.author{display:flex;gap:12px;align-items:center;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:18px 0}
.author .avatar{flex:none;display:grid;place-items:center;width:48px;height:48px;border-radius:50%;background:var(--work-soft);font-size:22px}
.author b{display:block;font-size:15px}
.author span{display:block;color:var(--muted);font-size:14px;line-height:1.6}
article{max-width:800px;margin:0 auto}
article .post-head{padding-top:8px}
article .post-head h1{margin-top:8px}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin:20px 0 0}
.tags span{font-size:13px;color:var(--muted);background:var(--card);padding:3px 10px;border-radius:99px}
table{border-collapse:collapse;width:100%;display:block;overflow-x:auto;font-size:15px}
th,td{border:1px solid var(--line);padding:8px 12px;text-align:left}
th{background:var(--card)}
img{max-width:100%;height:auto}
hr{border:0;border-top:1px solid var(--line);margin:24px 0}
blockquote{margin:16px 0;padding:10px 14px;border-left:4px solid var(--accent);background:var(--surface);border-radius:0 10px 10px 0}
blockquote p{margin:0}
.products{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px;margin:16px 0}
.product{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px;text-decoration:none;color:var(--fg)}
.product img{width:100%;aspect-ratio:1;object-fit:contain;background:#fff;border-radius:8px}
.product .name{font-size:14px;line-height:1.4;margin:8px 0 4px}
.product .price{font-weight:700}
.disclosure{font-size:13px;color:var(--muted);background:var(--card);padding:10px 12px;border-radius:8px;line-height:1.6}
footer{border-top:1px solid var(--line);margin-top:28px;padding:16px 0 24px;color:var(--muted);font-size:13px}
footer a{color:var(--muted)}
footer .links{display:flex;flex-wrap:wrap;gap:6px 14px;margin-top:6px}
.ad{margin:14px 0;min-height:1px}
.cp-banner{margin:20px 0;overflow:hidden}
.cp-banner iframe{max-width:100%}
.nav a.lang{border:1px solid var(--line)}
"""

# UI strings per site language. Content strings (site title, categories...) come from config.json,
# with English overrides under config["en"].
UI = {
    "ko": {"min_read": "{}분 읽기", "no_posts": "아직 글이 없습니다.", "about": "소개",
           "privacy": "개인정보처리방침", "related": "함께 읽으면 좋은 글", "see_all": "전체 보기 →",
           "category": "카테고리", "all_posts": "전체 글 {}편",
           "qa": "vMix·방송 관련해서 궁금한 점은 쓰레드로 질문해 주시면 답해 드립니다.", "qa_link": "쓰레드에서 질문하기 →"},
    "en": {"min_read": "{} min read", "no_posts": "No posts yet.", "about": "About",
           "privacy": "Privacy Policy", "related": "You might also like", "see_all": "See all →",
           "category": "Category", "all_posts": "{} posts",
           "qa": "Questions about vMix or broadcasting? Ask me on Threads and I'll answer.", "qa_link": "Ask on Threads →"},
    "ja": {"min_read": "{}分で読めます", "no_posts": "まだ記事がありません。", "about": "このブログについて",
           "privacy": "プライバシーポリシー", "related": "あわせて読みたい", "see_all": "すべて見る →",
           "category": "カテゴリー", "all_posts": "全{}件",
           "qa": "vMixや放送についての質問はThreadsでどうぞ。お答えします。", "qa_link": "Threadsで質問する →"},
}
LANG_LABEL = {"ko": "한국어", "en": "English", "ja": "日本語"}
# Characters per minute of reading, for the "N min read" label.
READ_SPEED = {"ko": 500, "en": 1200, "ja": 600}


def _t(cfg: dict, key: str) -> str:
    return UI[cfg["language"]][key]


def _is_ko(cfg: dict) -> bool:
    return cfg["language"] == "ko"


def _root(cfg: dict) -> str:
    """URL of the Korean (root) site, whichever language cfg is for."""
    return cfg.get("root_url", cfg["site_url"])


def _lang_home(cfg: dict, lang: str) -> str:
    return _root(cfg) if lang == "ko" else f"{_root(cfg)}/{lang}"


def site_languages(cfg: dict) -> list[str]:
    return ["ko", *cfg.get("translations", {})]


def lang_config(cfg: dict, lang: str) -> dict:
    """Config for the /<lang>/ site: texts from cfg["translations"][lang], URLs under /<lang>."""
    return {**cfg, **cfg["translations"][lang], "language": lang,
            "site_url": f"{cfg['site_url']}/{lang}", "root_url": cfg["site_url"]}


def lang_posts(posts: list[dict], lang: str) -> list[dict]:
    """Posts that have a translation into lang, with the translated fields swapped in."""
    return [{**p, **p[lang], "lang": lang} for p in posts if p.get(lang)]


def post_languages(cfg: dict, post: dict) -> list[str]:
    return ["ko", *(lang for lang in cfg.get("translations", {}) if post.get(lang))]


def load_posts() -> list[dict]:
    posts = [json.loads(p.read_text(encoding="utf-8")) for p in POSTS_DIR.glob("*.json")]
    return sorted(posts, key=lambda p: p["date"], reverse=True)


def post_path(post: dict) -> str:
    return f"posts/{post['slug']}/"


def post_category(post: dict) -> str:
    """Author-written posts are workplace essays; generated ones are life tips unless set explicitly."""
    return post.get("category") or ("work" if post.get("author") == "human" else "life")


def _reading_minutes(post: dict) -> int:
    return max(1, round(len(post["body_markdown"]) / READ_SPEED[post.get("lang", "ko")]))


def _badge(cfg: dict, key: str) -> str:
    return f'<span class="badge {key}">{escape(cfg["categories"][key]["name"])}</span>'


def _cards(cfg: dict, posts: list[dict]) -> str:
    if not posts:
        return f'<p class="meta">{_t(cfg, "no_posts")}</p>'
    return '<div class="cards">' + "".join(
        f'<a class="card" href="{cfg["site_url"]}/{post_path(p)}">{_badge(cfg, post_category(p))}'
        f'<h3>{escape(p["title"])}</h3><p>{escape(p["description"])}</p>'
        f'<span class="meta">{p["date"][:10]} · {_t(cfg, "min_read").format(_reading_minutes(p))}</span></a>'
        for p in posts
    ) + "</div>"


def is_broadcast(post: dict) -> bool:
    return post_category(post) == "broadcast" or any("vmix" in t.lower() for t in post.get("tags", []))


def _qa_box(cfg: dict, post: dict) -> str:
    """vMix posts invite questions on Threads, since the blog has no comments."""
    if not cfg.get("threads_url") or not is_broadcast(post):
        return ""
    return (f'<div class="qa">💬 {_t(cfg, "qa")} '
            f'<a href="{escape(cfg["threads_url"])}" target="_blank" rel="noopener">{_t(cfg, "qa_link")}</a></div>')


def _author_box(cfg: dict) -> str:
    return (f'<div class="author"><div class="avatar">👔</div><div><b>{escape(cfg["author_name"])}</b>'
            f'<span>{escape(cfg["author_bio"])}</span></div></div>')


def _adsense_head(cfg: dict) -> str:
    if not cfg.get("adsense_client"):
        return ""
    client = escape(cfg["adsense_client"])
    return (
        f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
        f'?client={client}" crossorigin="anonymous"></script>'
    )


def _verification_meta(cfg: dict) -> str:
    tags = {"naver-site-verification": "naver_site_verification",
            "google-site-verification": "google_site_verification"}
    return "".join(
        f'<meta name="{name}" content="{escape(cfg[key])}">\n'
        for name, key in tags.items() if cfg.get(key)
    )


def _nav_links(cfg: dict, current: str) -> str:
    """Categories listed in config "nav_groups" go into dropdown menus; the rest stay top-level."""
    base = cfg["site_url"]

    def link(key: str, href: str, name: str) -> str:
        return f'<a href="{href}"{" class=on" if key == current else ""}>{escape(name)}</a>'

    # Non-category pages that can sit in a group; Korean-only like the calculators.
    pages = {"words": (f"{base}/words/", "필수 영단어"), "tools": (f"{base}/tools/", "생활 계산기")} if _is_ko(cfg) else {}

    def cat(key: str) -> str:
        if key in pages:
            return link(key, *pages[key])
        return link(key, f"{base}/category/{key}/", cfg["categories"][key]["name"])

    groups = [g for g in cfg.get("nav_groups", []) if any(k in cfg["categories"] for k in g["keys"])]
    grouped = {k for g in groups for k in g["keys"]}
    parts = [cat(k) for k in cfg["categories"] if k not in grouped]
    for g in groups:
        keys = [k for k in g["keys"] if k in cfg["categories"] or k in pages]
        name = g["names"].get(cfg["language"], g["names"]["ko"])
        on = " on" if current in keys else ""
        parts.append(f'<details class="navgroup{on}"><summary>{escape(name)}</summary>'
                     f'<div class="menu">{"".join(cat(k) for k in keys)}</div></details>')
    if _is_ko(cfg) and "tools" not in grouped:  # the calculators are Korea-specific (KRW, pyeong), so Korean-only
        parts.append(link("tools", f"{base}/tools/", "계산기"))
    if cfg.get("memory", {}).get("boards"):
        parts.append(link("memory", f"{base}/memory/", cfg["memory"]["title"]))
    return "".join(parts)


def _page(cfg: dict, title: str, body: str, *, description: str = "", canonical: str = "",
          extra_head: str = "", nav: str = "", path: str = "", langs: list[str] | None = None,
          body_class: str = "") -> str:
    """path: the page's path relative to each language's home. langs: the languages this page
    exists in (default: all). They get hreflang links; the language switcher sends the other
    languages to their home page."""
    description = description or cfg["site_description"]
    canonical = canonical or cfg["site_url"] + "/"
    langs = site_languages(cfg) if langs is None else langs
    hreflang = ""
    if len(langs) > 1:
        hreflang = "".join(f'<link rel="alternate" hreflang="{lang}" href="{_lang_home(cfg, lang)}/{path}">\n'
                           for lang in langs)
        hreflang += f'<link rel="alternate" hreflang="x-default" href="{_lang_home(cfg, "ko")}/{path}">\n'
    switcher = "".join(
        f'<a href="{_lang_home(cfg, lang)}/{path if lang in langs else ""}" hreflang="{lang}">'
        f'{LANG_LABEL[lang]}</a>'
        for lang in site_languages(cfg) if lang != cfg["language"]
    )
    if switcher:  # one globe menu instead of a link per language keeps the menu bar on one line
        switcher = (f'<details class="navgroup langs"><summary aria-label="Language">🌐</summary>'
                    f'<div class="menu">{switcher}</div></details>')
    site_title = escape(cfg["site_title"])
    full_title = escape(title) if title == cfg["site_title"] else f"{escape(title)} | {site_title}"
    return f"""<!doctype html>
<html lang="{cfg['language']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{full_title}</title>
<meta name="description" content="{escape(description)}">
<link rel="canonical" href="{escape(canonical)}">
<link rel="alternate" type="application/rss+xml" title="{site_title}" href="{cfg['site_url']}/rss.xml">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(description)}">
<meta property="og:url" content="{escape(canonical)}">
<meta property="og:type" content="website">
{hreflang}<link rel="stylesheet" href="{FONT_CSS}">
{_verification_meta(cfg)}<style>{CSS}{TOOL_CSS}{MEMORY_CSS}</style>
{_adsense_head(cfg)}
{extra_head}
</head>
<body{f' class="{body_class}"' if body_class else ''}>
<header class="site-header"><div class="wrap">
<a class="brand" href="{cfg['site_url']}/"><span class="mark">{site_title[:1]}</span>{site_title}</a>
<nav class="nav">{_nav_links(cfg, nav)}{switcher}</nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer><div class="wrap">
<div>© {datetime.now(timezone.utc).year} {site_title}</div>
<div class="links">
<a href="{cfg['site_url']}/about/">{_t(cfg, "about")}</a>
<a href="{cfg['site_url']}/privacy/">{_t(cfg, "privacy")}</a>
<a href="{cfg['site_url']}/rss.xml">RSS</a>
{f'<a href="{escape(cfg["youtube_url"])}" rel="me noopener" target="_blank">YouTube</a>' if cfg.get("youtube_url") else ""}
{f'<a href="{escape(cfg["threads_url"])}" rel="me noopener" target="_blank">Threads</a>' if cfg.get("threads_url") else ""}
</div>
</div></footer>
<script>document.addEventListener("click",e=>{{document.querySelectorAll("details.navgroup[open]").forEach(d=>{{if(!d.contains(e.target))d.open=false}})}});</script>
</body>
</html>
"""


def _products_html(cfg: dict, products: list[dict]) -> str:
    if not products:
        return ""
    cards = []
    for p in products:
        price = f"{p['price']:,}원" if isinstance(p.get("price"), int) else ""
        cards.append(
            f'<a class="product" href="{escape(p["url"])}" target="_blank" rel="sponsored nofollow noopener">'
            f'<img src="{escape(p["image"])}" alt="{escape(p["name"])}" loading="lazy">'
            f'<div class="name">{escape(p["name"])}</div><div class="price">{price}</div></a>'
        )
    return (
        "<h2>관련 추천 상품</h2>"
        f'<div class="products">{"".join(cards)}</div>'
    )


def _banner_html(cfg: dict) -> str:
    banner = cfg.get("coupang_banner")
    if not banner:
        return ""
    return (
        '<div class="cp-banner"><script src="https://ads-partners.coupang.com/g.js"></script>'
        f"<script>if (window.PartnersCoupang) new PartnersCoupang.G({json.dumps(banner)});</script></div>"
    )


def _insert_mid(body_html: str, block: str) -> str:
    """Put block before the middle <h2> of the body; short posts (under 3 sections) are left as is."""
    heads = [m.start() for m in re.finditer(r"<h2[ >]", body_html)]
    if not block or len(heads) < 3:
        return body_html
    at = heads[len(heads) // 2]
    return body_html[:at] + block + body_html[at:]


def _related(posts: list[dict], post: dict, n: int = 3) -> list[dict]:
    others = [p for p in posts if p["slug"] != post["slug"]]
    same = [p for p in others if post_category(p) == post_category(post)]
    return (same + [p for p in others if p not in same])[:n]


def _render_post(cfg: dict, post: dict, posts: list[dict]) -> str:
    url = f"{cfg['site_url']}/{post_path(post)}"
    body_html = markdown.markdown(post["body_markdown"], extensions=["tables", "fenced_code", "sane_lists"])
    if _is_ko(cfg):
        body_html = _insert_mid(body_html, _banner_html(cfg))
    # Coupang only ships within Korea, so affiliate blocks appear on the Korean site only.
    has_affiliate = _is_ko(cfg) and bool(post.get("products") or cfg.get("coupang_banner"))
    disclosure = f'<p class="disclosure">{escape(cfg["coupang_disclosure"])}</p>' if has_affiliate else ""
    tags = "".join(f"<span>#{escape(t)}</span>" for t in post.get("tags", []))
    category = post_category(post)
    json_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post["title"],
        "description": post["description"],
        "datePublished": post["date"],
        "mainEntityOfPage": url,
        "keywords": post.get("tags", []),
        "inLanguage": cfg["language"],
    }, ensure_ascii=False)
    body = f"""
<article>
<div class="post-head">{_badge(cfg, category)}
<h1>{escape(post['title'])}</h1>
<p class="meta">{post['date'][:10]} · {_t(cfg, "min_read").format(_reading_minutes(post))}</p></div>
{disclosure}
{body_html}
{'<div class="tags">' + tags + '</div>' if tags else ''}
{_products_html(cfg, post.get('products', [])) if _is_ko(cfg) else ''}
{_qa_box(cfg, post)}
{_author_box(cfg)}
{_banner_html(cfg) if _is_ko(cfg) else ''}
</article>
<div class="section-head"><h2>{_t(cfg, "related")}</h2></div>
{_cards(cfg, _related(posts, post))}
"""
    return _page(cfg, post["title"], body, description=post["description"], canonical=url, nav=category,
                 path=post_path(post), langs=post_languages(cfg, post),
                 extra_head=f'<script type="application/ld+json">{json_ld}</script>')


# Cards per category on the home page; categories not listed show 4.
HOME_LIMITS = {"work": 4, "life": 6}


def _render_index(cfg: dict, posts: list[dict]) -> str:
    base = cfg["site_url"]
    sections = []
    for key, c in cfg["categories"].items():
        chosen = [p for p in posts if post_category(p) == key][:HOME_LIMITS.get(key, 4)]
        if not chosen and key != "work":
            continue
        sections.append(
            f'<div class="section-head"><h2>{c["emoji"]} {escape(c["name"])}</h2>'
            f'<a href="{base}/category/{key}/">{_t(cfg, "see_all")}</a></div>{_cards(cfg, chosen)}'
        )
        if key == "work" and _is_ko(cfg):
            sections.append(f'<div class="section-head"><h2>🧮 생활 계산기</h2>'
                            f'<a href="{base}/tools/">전체 보기 →</a></div>{tool_list_html(base)}')
    body = f"""<section class="hero">
<span class="kicker">{escape(cfg['site_title'])}</span>
<h1>{escape(cfg['hero_title'])}</h1>
<p>{escape(cfg['site_description'])}</p>
</section>
{_author_box(cfg)}
{''.join(sections)}"""
    return _page(cfg, cfg["site_title"], body)


def _render_category(cfg: dict, key: str, posts: list[dict]) -> str:
    c = cfg["categories"][key]
    chosen = [p for p in posts if post_category(p) == key]
    body = (f'<section class="hero"><span class="kicker">{c["emoji"]} {_t(cfg, "category")}</span>'
            f'<h1>{escape(c["name"])}</h1><p>{escape(c["desc"])}</p></section>'
            f'<div class="section-head"><h2>{_t(cfg, "all_posts").format(len(chosen))}</h2></div>'
            f'{_cards(cfg, chosen)}')
    return _page(cfg, c["name"], body, description=c["desc"],
                 canonical=f"{cfg['site_url']}/category/{key}/", nav=key, path=f"category/{key}/")


FOREIGN_STATIC_PAGES = {
    "en": lambda name, bio, work: {
        "about": ("About", f"""<h1>About</h1>
<p>{bio}</p>
<p>This is the English edition of a Korean blog. Posts are translated from Korean with the help of AI tools.
Stories under '{work}' are written by the author from personal experience; the practical tips are researched
and drafted with AI assistance. Prices, specs and policies change, and many details are specific to Korea,
so please check official sources before you buy or apply anything.</p>"""),
        "privacy": ("Privacy Policy", f"""<h1>Privacy Policy</h1>
<p>{name} has no accounts or comments and does not directly collect visitors' personal information.</p>
<h2>Advertising and cookies</h2>
<p>This site may show third-party ads such as Google AdSense. Google and other third-party vendors use cookies to
serve ads based on your prior visits. You can opt out of personalized advertising in
<a href="https://adssettings.google.com" rel="nofollow">Google Ads Settings</a>.</p>"""),
    },
    "ja": lambda name, bio, work: {
        "about": ("このブログについて", f"""<h1>このブログについて</h1>
<p>{bio}</p>
<p>このサイトは韓国語ブログの日本語版です。記事はAIツールの助けを借りて韓国語から翻訳しています。
「{work}」の記事は筆者が実際に経験したことをもとに書いたもので、暮らしのヒントはAIの支援を受けて作成しています。
価格・仕様・制度は変わることがあり、韓国特有の内容も多いため、購入や利用の前に必ず公式情報をご確認ください。</p>"""),
        "privacy": ("プライバシーポリシー", f"""<h1>プライバシーポリシー</h1>
<p>{name}には会員登録やコメント機能がなく、訪問者の個人情報を直接収集することはありません。</p>
<h2>広告とCookie</h2>
<p>当サイトではGoogle AdSenseなどの第三者配信の広告を掲載することがあります。Googleなどの第三者配信事業者は
Cookieを使用して、ユーザーの過去のアクセス情報に基づいて広告を配信します。
<a href="https://adssettings.google.com" rel="nofollow">Googleの広告設定</a>でパーソナライズ広告を無効にできます。</p>"""),
    },
}


def _static_pages(cfg: dict) -> dict[str, tuple[str, str]]:
    name = escape(cfg["site_title"])
    if not _is_ko(cfg):
        work = escape(cfg["categories"]["work"]["name"])
        return FOREIGN_STATIC_PAGES[cfg["language"]](name, escape(cfg["author_bio"]), work)
    return {
        "about": ("소개", f"""<h1>소개</h1>
<p>{escape(cfg['author_bio'])}</p>
<p>'직장생활 이야기'는 운영자가 직접 겪고 쓴 글입니다. '생활 꿀팁'의 정보성 글은 AI 도구의 도움을 받아 작성되며, 가격·사양·정책 등은 변동될 수 있으니 구매나 적용 전 공식 정보를 꼭 확인해 주세요.</p>
<p>일부 글에는 제휴 링크(쿠팡 파트너스 등)가 포함될 수 있으며, 이를 통해 구매가 이루어지면 운영자가 일정 수수료를 받습니다.</p>"""),
        "privacy": ("개인정보처리방침", f"""<h1>개인정보처리방침</h1>
<p>{name}은(는) 회원가입 기능이 없으며 방문자의 개인정보를 직접 수집하지 않습니다.</p>
<p>Memory 게시판은 GitHub Discussions 기반의 giscus 위젯으로 표시됩니다. 해당 영역은 GitHub에서 제공하며
<a href="https://docs.github.com/site-policy/privacy-policies/github-general-privacy-statement" rel="nofollow">GitHub 개인정보 보호 정책</a>이 적용됩니다.
게시판 글은 운영자만 작성합니다.</p>
<h2>광고 및 쿠키</h2>
<p>본 사이트는 Google AdSense 등 제3자 광고를 게재할 수 있습니다. Google을 비롯한 제3자 공급업체는 쿠키를 사용하여
사용자의 이전 방문 기록을 바탕으로 광고를 게재합니다. 사용자는
<a href="https://adssettings.google.com" rel="nofollow">Google 광고 설정</a>에서 맞춤 광고를 해제할 수 있습니다.</p>
<h2>제휴 링크</h2>
<p>일부 링크는 제휴 마케팅 링크이며, 해당 링크를 통해 구매 시 운영자가 수수료를 받을 수 있습니다.</p>"""),
    }


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_lang(cfg: dict, posts: list[dict], out: Path) -> list[str]:
    """Render one language's pages into out/ and return their URLs for the sitemap."""
    base = cfg["site_url"]
    _write(out / "index.html", _render_index(cfg, posts))
    for post in posts:
        _write(out / post_path(post) / "index.html", _render_post(cfg, post, posts))
    for key in cfg["categories"]:
        _write(out / "category" / key / "index.html", _render_category(cfg, key, posts))
    for slug, (title, body) in _static_pages(cfg).items():
        _write(out / slug / "index.html", _page(cfg, title, body, canonical=f"{base}/{slug}/", path=f"{slug}/"))

    items = "".join(
        f"<item><title>{escape(p['title'])}</title><link>{base}/{post_path(p)}</link>"
        f"<guid>{base}/{post_path(p)}</guid><description>{escape(p['description'])}</description>"
        f"<pubDate>{datetime.fromisoformat(p['date']).strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate></item>"
        for p in posts[:30]
    )
    _write(out / "rss.xml",
           f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
           f"<title>{escape(cfg['site_title'])}</title><link>{base}/</link>"
           f"<description>{escape(cfg['site_description'])}</description>{items}</channel></rss>\n")
    return [f"{base}/"] + [f"{base}/category/{k}/" for k in cfg["categories"]] \
        + [f"{base}/{post_path(p)}" for p in posts]


def build_site(cfg: dict) -> int:
    posts = load_posts()
    if PUBLIC_DIR.exists():
        shutil.rmtree(PUBLIC_DIR)
    PUBLIC_DIR.mkdir(parents=True)
    base = cfg["site_url"]

    urls = _build_lang(cfg, posts, PUBLIC_DIR)
    for lang in cfg.get("translations", {}):
        urls += _build_lang(lang_config(cfg, lang), lang_posts(posts, lang), PUBLIC_DIR / lang)
    affiliate = ""
    if cfg.get("coupang_banner"):
        affiliate = f'<p class="disclosure">{escape(cfg["coupang_disclosure"])}</p>{_banner_html(cfg)}'
    for tool in TOOLS:
        _write(PUBLIC_DIR / "tools" / tool["slug"] / "index.html",
               _page(cfg, tool["title"], render_tool_body(tool) + affiliate, nav="tools",
                     description=tool["description"], canonical=f"{base}/tools/{tool['slug']}/", langs=["ko"]))
    _write(PUBLIC_DIR / "tools" / "index.html",
           _page(cfg, "생활 계산기", '<section class="hero"><span class="kicker">🧮 도구</span><h1>생활 계산기</h1>'
                 '<p>숫자만 넣으면 바로 계산되는 생활 계산기 모음</p></section>' + tool_list_html(base),
                 canonical=f"{base}/tools/", nav="tools", langs=["ko"]))

    urls += [f"{base}/tools/"] + [f"{base}/tools/{t['slug']}/" for t in TOOLS]
    # Korean-only vocabulary pages for middle schoolers.
    _write(PUBLIC_DIR / "words" / "index.html",
           _page(cfg, "중학생 학년별 필수 영단어", words.render_index(base), nav="words",
                 description="중1·중2·중3 학년별 필수 영단어를 목록·카드·퀴즈로 외우는 페이지",
                 canonical=f"{base}/words/", path="words/", langs=["ko"]))
    for grade, (title, desc) in words.GRADES.items():
        _write(PUBLIC_DIR / "words" / str(grade) / "index.html",
               _page(cfg, title, words.render_grade(grade, base), nav="words", description=desc,
                     canonical=f"{base}/words/{grade}/", path=f"words/{grade}/", langs=["ko"]))
    urls += [f"{base}/words/"] + [f"{base}/words/{g}/" for g in words.GRADES]
    # Memory boards exist in every site language; the /<lang>/ pages read headline_<lang>/summary_<lang>.
    for lang in site_languages(cfg):
        lcfg = cfg if lang == "ko" else lang_config(cfg, lang)
        out = PUBLIC_DIR if lang == "ko" else PUBLIC_DIR / lang
        for path, title, description, body in memory_pages(lcfg):
            _write(out / path / "index.html",
                   _page(lcfg, title, body, nav="memory", description=description,
                         canonical=f"{lcfg['site_url']}/{path}", path=path, body_class="memory-page"))
            urls.append(f"{lcfg['site_url']}/{path}")
    sitemap = "".join(f"<url><loc>{escape(u)}</loc></url>" for u in urls)
    _write(PUBLIC_DIR / "sitemap.xml",
           f'<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sitemap}</urlset>\n')

    _write(PUBLIC_DIR / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n")
    if cfg.get("adsense_client"):
        pub_id = cfg["adsense_client"].removeprefix("ca-")
        _write(PUBLIC_DIR / "ads.txt", f"google.com, {pub_id}, DIRECT, f08c47fec0942fa0\n")
    _write(PUBLIC_DIR / ".nojekyll", "")
    # Files in static/ (e.g. search engine verification files) are copied verbatim.
    static_dir = ROOT / "static"
    if static_dir.is_dir():
        shutil.copytree(static_dir, PUBLIC_DIR, dirs_exist_ok=True)
    return len(posts)
