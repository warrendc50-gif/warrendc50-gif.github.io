"""Builds the static site (HTML, sitemap, RSS, robots.txt, ads.txt) into public/."""
import json
import shutil
from datetime import datetime, timezone
from html import escape
from pathlib import Path

import markdown

from .config import POSTS_DIR, PUBLIC_DIR, ROOT
from .tools import TOOL_CSS, TOOLS, render_tool_body, tool_list_html

FONT_CSS = "https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css"

CSS = """
:root{--bg:#fbfaf7;--surface:#fff;--fg:#1f2328;--muted:#6b6f76;--line:#e7e4dc;--card:#f3f1ea;
  --accent:#0f766e;--accent-soft:#e0f2ef;--work:#b45309;--work-soft:#fdf0e1;--life:#0f766e;--life-soft:#e0f2ef}
@media (prefers-color-scheme:dark){:root{--bg:#141517;--surface:#1c1d20;--fg:#ecedee;--muted:#9ea3aa;--line:#2c2e33;
  --card:#23252a;--accent:#5eead4;--accent-soft:#12302c;--work:#fbbf24;--work-soft:#33260f;--life:#5eead4;--life-soft:#12302c}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);-webkit-font-smoothing:antialiased;
  font:17px/1.8 "Pretendard Variable",Pretendard,-apple-system,"Apple SD Gothic Neo","Noto Sans KR",sans-serif;word-break:keep-all}
.wrap{max-width:760px;margin:0 auto;padding:0 16px}
a{color:var(--accent)}
.site-header{position:sticky;top:0;z-index:10;background:color-mix(in srgb,var(--bg) 88%,transparent);
  backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.site-header .wrap{display:flex;align-items:center;gap:16px;min-height:60px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:10px;color:var(--fg);text-decoration:none;font-weight:800;font-size:18px;letter-spacing:-.02em}
.brand .mark{display:grid;place-items:center;width:32px;height:32px;border-radius:9px;background:var(--accent);color:var(--bg);font-size:16px}
.nav{display:flex;gap:4px;margin-left:auto;overflow-x:auto}
.nav a{white-space:nowrap;padding:6px 10px;border-radius:8px;color:var(--muted);text-decoration:none;font-size:15px;font-weight:600}
.nav a:hover,.nav a.on{background:var(--card);color:var(--fg)}
@media (max-width:560px){.nav{margin-left:0;width:100%;padding-bottom:8px}.site-header .wrap{gap:4px;padding-top:8px}}
h1{font-size:30px;line-height:1.35;letter-spacing:-.03em;margin:36px 0 10px}
h2{font-size:23px;line-height:1.4;letter-spacing:-.02em;margin:44px 0 12px}
h3{font-size:19px;margin:32px 0 8px}
.meta{color:var(--muted);font-size:14px}
.hero{padding:40px 0 8px}
.hero .kicker{display:inline-block;font-size:13px;font-weight:700;color:var(--accent);background:var(--accent-soft);padding:4px 10px;border-radius:99px}
.hero h1{font-size:32px;margin:14px 0 8px}
.hero p{color:var(--muted);margin:0}
.section-head{display:flex;align-items:baseline;justify-content:space-between;gap:12px;margin:48px 0 14px}
.section-head h2{margin:0;font-size:21px}
.section-head a{font-size:14px;font-weight:600;text-decoration:none;white-space:nowrap}
.cards{display:grid;gap:12px}
.card{display:block;background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px 18px 16px;
  text-decoration:none;color:var(--fg);transition:border-color .15s,transform .15s}
.card:hover{border-color:var(--accent);transform:translateY(-1px)}
.card h3{margin:8px 0 6px;font-size:18px;line-height:1.45;letter-spacing:-.02em}
.card p{margin:0 0 10px;color:var(--muted);font-size:15px;line-height:1.6;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.card .meta{font-size:13px}
.badge{display:inline-block;font-size:12px;font-weight:700;padding:3px 8px;border-radius:6px}
.badge.work{color:var(--work);background:var(--work-soft)}
.badge.life{color:var(--life);background:var(--life-soft)}
.author{display:flex;gap:14px;align-items:center;background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin:28px 0}
.author .avatar{flex:none;display:grid;place-items:center;width:48px;height:48px;border-radius:50%;background:var(--work-soft);font-size:22px}
.author b{display:block;font-size:15px}
.author span{display:block;color:var(--muted);font-size:14px;line-height:1.6}
article .post-head{padding-top:12px}
article .post-head h1{margin-top:14px}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin:32px 0 0}
.tags span{font-size:13px;color:var(--muted);background:var(--card);padding:3px 10px;border-radius:99px}
table{border-collapse:collapse;width:100%;display:block;overflow-x:auto;font-size:15px}
th,td{border:1px solid var(--line);padding:8px 12px;text-align:left}
th{background:var(--card)}
img{max-width:100%;height:auto}
hr{border:0;border-top:1px solid var(--line);margin:36px 0}
blockquote{margin:22px 0;padding:14px 18px;border-left:4px solid var(--accent);background:var(--surface);border-radius:0 10px 10px 0}
blockquote p{margin:0}
.products{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin:24px 0}
.product{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px;text-decoration:none;color:var(--fg)}
.product img{width:100%;aspect-ratio:1;object-fit:contain;background:#fff;border-radius:8px}
.product .name{font-size:14px;line-height:1.4;margin:8px 0 4px}
.product .price{font-weight:700}
.disclosure{font-size:13px;color:var(--muted);background:var(--card);padding:10px 12px;border-radius:8px;line-height:1.6}
footer{border-top:1px solid var(--line);margin-top:64px;padding:28px 0 40px;color:var(--muted);font-size:14px}
footer a{color:var(--muted)}
footer .links{display:flex;flex-wrap:wrap;gap:6px 14px;margin-top:6px}
.ad{margin:24px 0;min-height:1px}
.cp-banner{margin:36px 0;overflow:hidden}
.cp-banner iframe{max-width:100%}
"""


def load_posts() -> list[dict]:
    posts = [json.loads(p.read_text(encoding="utf-8")) for p in POSTS_DIR.glob("*.json")]
    return sorted(posts, key=lambda p: p["date"], reverse=True)


def post_path(post: dict) -> str:
    return f"posts/{post['slug']}/"


def post_category(post: dict) -> str:
    """Author-written posts are workplace essays; generated ones are life tips unless set explicitly."""
    return post.get("category") or ("work" if post.get("author") == "human" else "life")


def _reading_minutes(post: dict) -> int:
    return max(1, round(len(post["body_markdown"]) / 500))


def _badge(cfg: dict, key: str) -> str:
    return f'<span class="badge {key}">{escape(cfg["categories"][key]["name"])}</span>'


def _cards(cfg: dict, posts: list[dict]) -> str:
    if not posts:
        return '<p class="meta">아직 글이 없습니다.</p>'
    return '<div class="cards">' + "".join(
        f'<a class="card" href="{cfg["site_url"]}/{post_path(p)}">{_badge(cfg, post_category(p))}'
        f'<h3>{escape(p["title"])}</h3><p>{escape(p["description"])}</p>'
        f'<span class="meta">{p["date"][:10]} · {_reading_minutes(p)}분 읽기</span></a>'
        for p in posts
    ) + "</div>"


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
    base = cfg["site_url"]
    items = [(key, f"{base}/category/{key}/", c["name"]) for key, c in cfg["categories"].items()]
    items.append(("tools", f"{base}/tools/", "계산기"))
    return "".join(
        f'<a href="{href}"{" class=on" if key == current else ""}>{escape(name)}</a>'
        for key, href, name in items
    )


def _page(cfg: dict, title: str, body: str, *, description: str = "", canonical: str = "",
          extra_head: str = "", nav: str = "") -> str:
    description = description or cfg["site_description"]
    canonical = canonical or cfg["site_url"] + "/"
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
<link rel="stylesheet" href="{FONT_CSS}">
{_verification_meta(cfg)}<style>{CSS}{TOOL_CSS}</style>
{_adsense_head(cfg)}
{extra_head}
</head>
<body>
<header class="site-header"><div class="wrap">
<a class="brand" href="{cfg['site_url']}/"><span class="mark">{site_title[:1]}</span>{site_title}</a>
<nav class="nav">{_nav_links(cfg, nav)}</nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer><div class="wrap">
<div>© {datetime.now(timezone.utc).year} {site_title}</div>
<div class="links">
<a href="{cfg['site_url']}/about/">소개</a>
<a href="{cfg['site_url']}/privacy/">개인정보처리방침</a>
<a href="{cfg['site_url']}/rss.xml">RSS</a>
</div>
</div></footer>
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


def _related(posts: list[dict], post: dict, n: int = 3) -> list[dict]:
    others = [p for p in posts if p["slug"] != post["slug"]]
    same = [p for p in others if post_category(p) == post_category(post)]
    return (same + [p for p in others if p not in same])[:n]


def _render_post(cfg: dict, post: dict, posts: list[dict]) -> str:
    url = f"{cfg['site_url']}/{post_path(post)}"
    body_html = markdown.markdown(post["body_markdown"], extensions=["tables", "fenced_code", "sane_lists"])
    has_affiliate = bool(post.get("products") or cfg.get("coupang_banner"))
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
    }, ensure_ascii=False)
    body = f"""
<article>
<div class="post-head">{_badge(cfg, category)}
<h1>{escape(post['title'])}</h1>
<p class="meta">{post['date'][:10]} · {_reading_minutes(post)}분 읽기</p></div>
{disclosure}
{body_html}
{'<div class="tags">' + tags + '</div>' if tags else ''}
{_products_html(cfg, post.get('products', []))}
{_author_box(cfg)}
{_banner_html(cfg)}
</article>
<div class="section-head"><h2>함께 읽으면 좋은 글</h2></div>
{_cards(cfg, _related(posts, post))}
"""
    return _page(cfg, post["title"], body, description=post["description"], canonical=url, nav=category,
                 extra_head=f'<script type="application/ld+json">{json_ld}</script>')


def _render_index(cfg: dict, posts: list[dict]) -> str:
    base = cfg["site_url"]
    sections = []
    for key, limit in (("work", 4), ("life", 6)):
        c = cfg["categories"][key]
        chosen = [p for p in posts if post_category(p) == key][:limit]
        sections.append(
            f'<div class="section-head"><h2>{c["emoji"]} {escape(c["name"])}</h2>'
            f'<a href="{base}/category/{key}/">전체 보기 →</a></div>{_cards(cfg, chosen)}'
        )
        if key == "work":
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
    body = (f'<section class="hero"><span class="kicker">{c["emoji"]} 카테고리</span>'
            f'<h1>{escape(c["name"])}</h1><p>{escape(c["desc"])}</p></section>'
            f'<div class="section-head"><h2>전체 글 {len(chosen)}편</h2></div>{_cards(cfg, chosen)}')
    return _page(cfg, c["name"], body, description=c["desc"],
                 canonical=f"{cfg['site_url']}/category/{key}/", nav=key)


def _static_pages(cfg: dict) -> dict[str, tuple[str, str]]:
    name = escape(cfg["site_title"])
    return {
        "about": ("소개", f"""<h1>소개</h1>
<p>{escape(cfg['author_bio'])}</p>
<p>'직장생활 이야기'는 운영자가 직접 겪고 쓴 글입니다. '생활 꿀팁'의 정보성 글은 AI 도구의 도움을 받아 작성되며, 가격·사양·정책 등은 변동될 수 있으니 구매나 적용 전 공식 정보를 꼭 확인해 주세요.</p>
<p>일부 글에는 제휴 링크(쿠팡 파트너스 등)가 포함될 수 있으며, 이를 통해 구매가 이루어지면 운영자가 일정 수수료를 받습니다.</p>"""),
        "privacy": ("개인정보처리방침", f"""<h1>개인정보처리방침</h1>
<p>{name}은(는) 회원가입이나 댓글 기능이 없으며 방문자의 개인정보를 직접 수집하지 않습니다.</p>
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


def build_site(cfg: dict) -> int:
    posts = load_posts()
    if PUBLIC_DIR.exists():
        shutil.rmtree(PUBLIC_DIR)
    PUBLIC_DIR.mkdir(parents=True)
    base = cfg["site_url"]

    _write(PUBLIC_DIR / "index.html", _render_index(cfg, posts))
    for post in posts:
        _write(PUBLIC_DIR / post_path(post) / "index.html", _render_post(cfg, post, posts))
    for key in cfg["categories"]:
        _write(PUBLIC_DIR / "category" / key / "index.html", _render_category(cfg, key, posts))
    affiliate = ""
    if cfg.get("coupang_banner"):
        affiliate = f'<p class="disclosure">{escape(cfg["coupang_disclosure"])}</p>{_banner_html(cfg)}'
    for tool in TOOLS:
        _write(PUBLIC_DIR / "tools" / tool["slug"] / "index.html",
               _page(cfg, tool["title"], render_tool_body(tool) + affiliate, nav="tools",
                     description=tool["description"], canonical=f"{base}/tools/{tool['slug']}/"))
    _write(PUBLIC_DIR / "tools" / "index.html",
           _page(cfg, "생활 계산기", '<section class="hero"><span class="kicker">🧮 도구</span><h1>생활 계산기</h1>'
                 '<p>숫자만 넣으면 바로 계산되는 생활 계산기 모음</p></section>' + tool_list_html(base),
                 canonical=f"{base}/tools/", nav="tools"))
    for slug, (title, body) in _static_pages(cfg).items():
        _write(PUBLIC_DIR / slug / "index.html", _page(cfg, title, body, canonical=f"{base}/{slug}/"))

    urls = [f"{base}/", f"{base}/tools/"] + [f"{base}/category/{k}/" for k in cfg["categories"]] + [f"{base}/tools/{t['slug']}/" for t in TOOLS] \
        + [f"{base}/{post_path(p)}" for p in posts]
    sitemap = "".join(f"<url><loc>{escape(u)}</loc></url>" for u in urls)
    _write(PUBLIC_DIR / "sitemap.xml",
           f'<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sitemap}</urlset>\n')

    items = "".join(
        f"<item><title>{escape(p['title'])}</title><link>{base}/{post_path(p)}</link>"
        f"<guid>{base}/{post_path(p)}</guid><description>{escape(p['description'])}</description>"
        f"<pubDate>{datetime.fromisoformat(p['date']).strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate></item>"
        for p in posts[:30]
    )
    _write(PUBLIC_DIR / "rss.xml",
           f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
           f"<title>{escape(cfg['site_title'])}</title><link>{base}/</link>"
           f"<description>{escape(cfg['site_description'])}</description>{items}</channel></rss>\n")

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
