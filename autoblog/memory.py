"""Memory boards: topic pages (/memory/<board>/) that archive news headlines.

Each board's entries live in data/memory/<board>.json (a list of items with date, headline, outlet,
url, summary_ko, topics, orgs). The page lists them newest first, grouped by month, with topic
filters and a search box; each headline expands to a Korean summary and a link to the original
article. Below the list, a giscus widget (GitHub Discussions) lets the operator add notes once
giscus is configured. Korean site only.
"""
import json
from collections import OrderedDict
from datetime import date
from html import escape

from .config import DATA_DIR

GISCUS_SCRIPT = "https://giscus.app/client.js"
MEMORY_DATA_DIR = DATA_DIR / "memory"

# Topic key -> Korean label. AI boards and finance boards share this table.
TOPIC_LABELS = {
    "model": "모델·제품", "chips": "반도체·인프라", "policy": "정책·규제", "business": "투자·기업",
    "research": "연구·안전", "korea": "한국",
    "rates": "금리·통화정책", "fx": "환율·외환", "stocks": "증시", "realestate": "부동산·가계대출",
    "banks": "은행·금융사", "crypto": "가상자산", "global": "해외발 영향",
}

MEMORY_CSS = """
.memory-page .wrap{max-width:980px}
.hero.compact{padding:14px 0 0}
.hero.compact h1{font-size:24px;margin:8px 0 2px}
.hero.compact p{font-size:14px}
.memory-page .boards{margin:10px 0 12px}
.memory-page .boards a{font-size:13px;padding:4px 10px}
.memory-page .meta{font-size:13px;margin:0 0 6px}
.news-tools{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:0 0 8px}
.news-tools input{flex:1 1 160px;min-width:0;font:inherit;font-size:14px;padding:5px 10px;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--fg)}
.chips{display:flex;flex-wrap:wrap;gap:4px}
.chip{font:inherit;font-size:12px;font-weight:600;padding:3px 9px;border-radius:99px;border:1px solid var(--line);background:var(--surface);color:var(--muted);cursor:pointer;line-height:1.5}
.chip.on{background:var(--accent);border-color:var(--accent);color:var(--bg)}
.news-month{margin:14px 0 4px;font-size:13px;color:var(--muted);font-weight:700;letter-spacing:0;position:sticky;top:60px;background:var(--bg);padding:4px 0;z-index:1}
.news{background:var(--surface);border:1px solid var(--line);border-radius:7px;margin:0 0 3px}
.news[open]{border-color:var(--accent)}
.news summary{list-style:none;cursor:pointer;padding:5px 10px;display:grid;grid-template-columns:3.2em 1fr auto;gap:0 10px;align-items:baseline}
.news summary::-webkit-details-marker{display:none}
.news summary .d{font-size:12px;color:var(--muted);white-space:nowrap;font-variant-numeric:tabular-nums}
.news summary .h{font-size:14.5px;font-weight:600;line-height:1.45}
.news summary .o{font-size:12px;color:var(--muted);white-space:nowrap}
.news summary .o b{font-weight:600;color:var(--accent)}
.news .body{padding:0 10px 9px 10px;border-top:1px dashed var(--line)}
.news .body p{margin:8px 0 0;font-size:14px;line-height:1.65}
.news .body .orig{color:var(--muted);font-size:13px;margin-top:6px}
.news .body .tags{margin:8px 0 0;gap:4px}
.news .body .tags span{font-size:12px;padding:2px 8px}
.news .body .go{display:inline-block;margin-top:8px;font-size:14px;font-weight:700;text-decoration:none}
.news-empty{color:var(--muted);padding:16px 0}
@media (max-width:560px){.news summary{grid-template-columns:3em 1fr;gap:0 8px}.news summary .o{grid-column:2;margin-top:-2px}}
"""

MEMORY_JS = """
(function(){
  var topic='all', q='';
  var chips=document.querySelectorAll('.chip'), items=document.querySelectorAll('.news'),
      months=document.querySelectorAll('.news-month'), box=document.getElementById('news-q'),
      count=document.getElementById('news-count');
  function apply(){
    var n=0, qq=q.trim().toLowerCase();
    items.forEach(function(el){
      var ok=(topic==='all'||(' '+el.dataset.topics+' ').indexOf(' '+topic+' ')>=0)
             &&(!qq||el.dataset.text.indexOf(qq)>=0);
      el.hidden=!ok; if(ok)n++;
    });
    months.forEach(function(m){
      var el=m.nextElementSibling, any=false;
      while(el&&!el.classList.contains('news-month')){ if(!el.hidden)any=true; el=el.nextElementSibling; }
      m.hidden=!any;
    });
    if(count)count.textContent=n;
  }
  chips.forEach(function(c){c.addEventListener('click',function(){
    chips.forEach(function(x){x.classList.remove('on')}); c.classList.add('on'); topic=c.dataset.topic; apply();
  })});
  if(box)box.addEventListener('input',function(){q=box.value;apply();});
})();
"""


def load_items(key: str) -> list[dict]:
    path = MEMORY_DATA_DIR / f"{key}.json"
    if not path.exists():
        return []
    items = json.loads(path.read_text(encoding="utf-8"))
    return sorted(items, key=lambda i: i["date"], reverse=True)


def giscus_html(cfg: dict, term: str) -> str:
    """The giscus embed for one board, or nothing while giscus is not configured yet."""
    g = cfg.get("giscus") or {}
    if not (g.get("repo") and g.get("repo_id") and g.get("category_id")):
        return ""
    return (f'<h2>운영자 메모</h2><div class="giscus"></div>\n'
            f'<script src="{GISCUS_SCRIPT}" data-repo="{escape(g["repo"])}" data-repo-id="{escape(g["repo_id"])}" '
            f'data-category="{escape(g.get("category", "Memory"))}" data-category-id="{escape(g["category_id"])}" '
            f'data-mapping="specific" data-term="{escape(term)}" data-strict="1" '
            f'data-reactions-enabled="0" data-emit-metadata="0" data-input-position="top" '
            f'data-theme="preferred_color_scheme" data-lang="ko" data-loading="lazy" '
            f'crossorigin="anonymous" async></script>')


def _item_html(item: dict) -> str:
    d = date.fromisoformat(item["date"])
    head_ko = item.get("headline_ko") or item["headline"]
    orig = item["headline"] if item["headline"] != head_ko else ""
    topics = " ".join(item.get("topics", []))
    text = " ".join([head_ko, item["headline"], item.get("outlet", ""), *item.get("orgs", []),
                     *(TOPIC_LABELS.get(t, t) for t in item.get("topics", []))]).lower()
    tags = "".join(f"<span>{escape(TOPIC_LABELS.get(t, t))}</span>" for t in item.get("topics", []))
    tags += "".join(f"<span>{escape(o)}</span>" for o in item.get("orgs", []))
    return (f'<details class="news" data-topics="{escape(topics)}" data-text="{escape(text)}">'
            f'<summary><span class="d">{d.month}.{d.day:02d}</span><span class="h">{escape(head_ko)}</span>'
            f'<span class="o"><b>{escape(item.get("outlet", ""))}</b></span></summary>'
            f'<div class="body"><p>{escape(item.get("summary_ko", ""))}</p>'
            f'{f"<p class=orig>원제: {escape(orig)}</p>" if orig else ""}'
            f'<div class="tags">{tags}</div>'
            f'<a class="go" href="{escape(item["url"])}" target="_blank" rel="noopener nofollow">원문 보기 ↗</a>'
            f'</div></details>')


def news_list_html(items: list[dict]) -> str:
    if not items:
        return '<p class="news-empty">아직 모아 둔 기사가 없습니다.</p>'
    topics = OrderedDict()
    for i in items:
        for t in i.get("topics", []):
            topics[t] = topics.get(t, 0) + 1
    chips = '<button class="chip on" data-topic="all">전체</button>' + "".join(
        f'<button class="chip" data-topic="{escape(t)}">{escape(TOPIC_LABELS.get(t, t))} {n}</button>'
        for t, n in sorted(topics.items(), key=lambda x: -x[1]))
    out = [f'<p class="meta">총 <span id="news-count">{len(items)}</span>건 · {items[0]["date"]} 기준 · '
           f'제목을 누르면 요약·원문 링크</p>',
           f'<div class="news-tools"><input id="news-q" type="search" placeholder="검색: 회사, 키워드, 언론사">'
           f'<div class="chips">{chips}</div></div>']
    month = None
    for i in items:
        m = i["date"][:7]
        if m != month:
            month = m
            y, mo = m.split("-")
            out.append(f'<h2 class="news-month">{y}년 {int(mo)}월</h2>')
        out.append(_item_html(i))
    out.append(f"<script>{MEMORY_JS}</script>")
    return "".join(out)


def board_cards(cfg: dict) -> str:
    m = cfg["memory"]
    base = cfg["site_url"]
    cards = []
    for key, b in m["boards"].items():
        n = len(load_items(key))
        meta = f'<div class="meta">{n}건</div>' if n else ""
        cards.append(f'<a class="card board" href="{base}/memory/{key}/"><span class="badge memory">{b["emoji"]} Memory</span>'
                     f'<h3>{escape(b["name"])}</h3><p>{escape(b["desc"])}</p>{meta}</a>')
    return '<div class="cards">' + "".join(cards) + "</div>"


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
    return (f'<section class="hero compact"><span class="kicker">{b["emoji"]} {escape(m["title"])}</span>'
            f'<h1>{escape(b["name"])}</h1><p>{escape(b["desc"])}</p></section>'
            f'<nav class="boards">{others}</nav>'
            f'<section class="board-feed">{news_list_html(load_items(key))}</section>'
            f'<section class="board-notes">{giscus_html(cfg, f"memory/{key}")}</section>')


def memory_pages(cfg: dict) -> list[tuple[str, str, str, str]]:
    """(path, title, description, body) for the memory index and each board."""
    m = cfg.get("memory")
    if not m or not m.get("boards"):
        return []
    pages = [("memory/", m["title"], m["desc"], index_body(cfg))]
    pages += [(f"memory/{key}/", f'{b["name"]} | {m["title"]}', b["desc"], board_body(cfg, key))
              for key, b in m["boards"].items()]
    return pages
