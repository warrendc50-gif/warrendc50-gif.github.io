"""Memory boards: topic pages (/memory/<board>/) that archive news headlines.

Each board's entries live in data/memory/<board>.json (a list of items with date, headline, outlet,
url, summary_ko, topics, orgs). The page shows a mind-map style timeline (time on the x axis, one
branch per topic or per organization, one dot per article) and, below it, the headlines newest
first, grouped by month, with topic filters and a search box; each headline expands to a Korean
summary and a link to the original article. Clicking a dot on the timeline opens that headline.
A giscus widget (GitHub Discussions) for operator notes renders once giscus is configured.
Korean site only.
"""
import json
from collections import Counter, OrderedDict
from datetime import date, timedelta
from html import escape
from urllib.parse import quote_plus

from .config import DATA_DIR

GISCUS_SCRIPT = "https://giscus.app/client.js"
MEMORY_DATA_DIR = DATA_DIR / "memory"

# Topic key -> Korean label. AI boards and finance boards share this table.
TOPIC_LABELS = {
    "model": "모델·제품", "chips": "반도체·인프라", "policy": "정책·규제", "business": "투자·기업",
    "research": "연구·안전", "korea": "한국",
    "rates": "금리·통화정책", "fx": "환율·외환", "stocks": "증시", "realestate": "부동산·가계대출",
    "banks": "은행·금융사", "crypto": "가상자산", "global": "해외발 영향",
    "unrest": "시위·폭동", "conflict": "전쟁·분쟁", "disaster": "재난·기상", "accident": "사고",
    "terror": "테러·치안", "politics": "정치 격변", "health": "보건", "economy": "경제 충격",
    "fed": "미 연준·금리", "centralbank": "중앙은행", "markets": "글로벌 증시", "trade": "무역·관세",
    "energy": "에너지·원자재", "china": "중국 경제", "macro": "성장·물가·고용", "crisis": "위기·채무·환율",
}
YOUTUBE_SEARCH = "https://www.youtube.com/results?search_query="
# Branch colors for the timeline; chosen to read on both the light and the dark background.
LANE_COLORS = ["#2563eb", "#0f9f8f", "#d97706", "#7c3aed", "#dc2626", "#0891b2", "#65a30d", "#db2777", "#6b7280"]
# Second color per branch, used for a dot that sits right next to the previous one so the two
# dot-label pairs stay apart. Index-aligned with LANE_COLORS.
LANE_ALT_COLORS = ["#9333ea", "#0369a1", "#b91c1c", "#db2777", "#ea580c", "#4f46e5", "#047857", "#7c2d12", "#0f766e"]
CLOSE_PX = 26  # dots closer than this (center to center) alternate colors
MAX_ORG_LANES = 8

MEMORY_CSS = """
.memory-page .wrap{max-width:1100px}
.hero .boards{display:flex;gap:4px;margin:0 0 0 auto}
.hero .boards a{font-size:12.5px;font-weight:600;text-decoration:none;color:var(--muted);background:var(--card);padding:3px 9px;border-radius:99px;white-space:nowrap}
.hero .boards a:hover{color:var(--fg)}
.news-bar{display:flex;flex-wrap:wrap;gap:6px 8px;align-items:center;margin:8px 0 0;padding-bottom:6px;border-bottom:2px solid var(--line)}
.news-bar input{flex:0 1 220px;min-width:120px;font:inherit;font-size:13.5px;padding:3px 10px;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--fg)}
.news-bar .meta{font-size:12.5px;margin:0 0 0 auto;white-space:nowrap}
.chips{display:flex;flex-wrap:wrap;gap:4px}
.chip{font:inherit;font-size:12px;font-weight:600;padding:2px 9px;border-radius:99px;border:1px solid var(--line);background:var(--surface);color:var(--muted);cursor:pointer;line-height:1.5}
.chip.on{background:var(--accent);border-color:var(--accent);color:var(--bg)}
.chips .chip:not([data-topic=all])::before{content:"☐";margin-right:4px;font-size:11px}
.chips .chip.on:not([data-topic=all])::before{content:"☑"}
.tl-panel{margin:6px 0 0;border:1px solid var(--line);border-radius:10px;background:var(--surface)}
.tl-panel summary{cursor:pointer;list-style:none;padding:4px 10px;font-size:13px;font-weight:700;display:flex;gap:8px;align-items:center;color:var(--muted)}
.tl-panel summary::before{content:"▸";font-size:12px;color:var(--accent)}
.tl-panel[open] summary::before{content:"▾"}
.tl-panel summary:hover{color:var(--fg)}
.tl-panel summary::-webkit-details-marker{display:none}
.tl-panel summary .hint{font-weight:500;font-size:12px}
.tl-panel .tl-mode{margin-left:auto;display:flex;gap:4px}
.tl-scroll{overflow-x:auto;padding:0 6px 4px}
svg.tl{display:block;font-family:inherit}
svg.tl[hidden]{display:none}
svg.tl .grid{stroke:var(--line);stroke-width:1}
svg.tl .spine{stroke:var(--accent);stroke-width:2;opacity:.5}
svg.tl .root{fill:var(--accent)}
svg.tl .mo{font-size:11px;fill:var(--muted)}
svg.tl .lane{font-size:12px;font-weight:700}
svg.tl .ln{stroke-width:2;opacity:.4}
svg.tl .br{fill:none;stroke-width:2;opacity:.55}
svg.tl .lb{font-size:11px}
svg.tl .tick{stroke-width:1;opacity:.45}
svg.tl .nd.bare circle{opacity:.55}
svg.tl .nd{cursor:pointer}
svg.tl .nd:hover .lb,svg.tl .nd:focus .lb{font-weight:700;text-decoration:underline}
svg.tl .nd:hover circle,svg.tl .nd:focus circle{r:6}
.news-month{margin:8px 0 0;font-size:12.5px;color:var(--muted);font-weight:700;position:sticky;top:48px;background:var(--bg);padding:3px 0 2px;z-index:1;border-bottom:1px solid var(--line)}
.news{border-bottom:1px solid var(--line);margin:0}
.news[open]{background:var(--surface);border-radius:8px;border:1px solid var(--accent);margin:3px 0}
.news.hl{box-shadow:0 0 0 3px var(--accent-soft)}
.news summary{list-style:none;cursor:pointer;padding:3px 6px;display:grid;grid-template-columns:3.1em 1fr auto;gap:0 10px;align-items:baseline}
.news summary:hover{background:var(--card)}
.news summary::-webkit-details-marker{display:none}
.news summary .d{font-size:12px;color:var(--muted);white-space:nowrap;font-variant-numeric:tabular-nums}
.news summary .h{font-size:14px;font-weight:600;line-height:1.4}
.news summary .o{font-size:12px;color:var(--muted);white-space:nowrap}
.news summary .o b{font-weight:600;color:var(--accent)}
.news .body{padding:0 10px 9px 10px;border-top:1px dashed var(--line)}
.news .body p{margin:8px 0 0;font-size:14px;line-height:1.6}
.news .body .orig{color:var(--muted);font-size:13px;margin-top:6px}
.news .body .tags{margin:8px 0 0;gap:4px}
.news .body .tags span{font-size:12px;padding:2px 8px}
.news .body .go{display:inline-block;margin-top:8px;font-size:14px;font-weight:700;text-decoration:none}
.news-empty{color:var(--muted);padding:16px 0}
.news summary .yt{margin-left:8px;color:#e11d48;text-decoration:none;font-size:11px;vertical-align:1px}
.news summary .yt.s{color:var(--muted);opacity:.55}
.news summary .yt:hover{opacity:1;color:#e11d48}
.news .body .yt-go{margin-left:14px;color:#e11d48}
.news .body .yt-go.s{color:var(--muted);font-weight:600}
.live-row{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:8px 0 0;padding:6px 10px;background:var(--surface);border:1px solid var(--line);border-radius:10px}
.live-row .live-dot{font-size:11px;font-weight:800;color:#fff;background:#e11d48;padding:2px 7px;border-radius:99px;letter-spacing:.04em}
.live-row .live-dot::before{content:"●";margin-right:4px;animation:blink 1.4s infinite}
@keyframes blink{50%{opacity:.3}}
.live-row a{font-size:13px;font-weight:600;text-decoration:none;color:var(--fg);background:var(--card);padding:3px 10px;border-radius:99px}
.live-row a:hover{color:#e11d48}
.board-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:10px;margin-top:10px}
.board-card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:10px 12px 8px;display:flex;flex-direction:column;min-width:0}
.board-card .head{display:flex;gap:10px;align-items:flex-start;text-decoration:none;color:var(--fg);padding-bottom:6px;border-bottom:1px solid var(--line)}
.board-card .head .emoji{font-size:20px;line-height:1.2}
.board-card .head b{display:block;font-size:15.5px;letter-spacing:-.02em}
.board-card .head small{display:block;color:var(--muted);font-size:12.5px;line-height:1.4;margin-top:1px}
.board-card .head .count{margin-left:auto;flex:none;font-size:12px;font-weight:700;color:var(--accent);background:var(--accent-soft);padding:2px 8px;border-radius:99px}
.board-card .preview{list-style:none;margin:4px 0 0;padding:0;flex:1}
.board-card .preview li{display:flex;gap:8px;align-items:baseline;padding:3px 0;border-bottom:1px dashed var(--line);min-width:0}
.board-card .preview li:last-child{border-bottom:0}
.board-card .preview .d{flex:none;font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums}
.board-card .preview a{font-size:13.5px;line-height:1.4;color:var(--fg);text-decoration:none;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.board-card .preview a:hover{color:var(--accent)}
.board-card .more{display:block;margin-top:6px;font-size:13px;font-weight:700;text-decoration:none;text-align:right}
.board-card .news-empty{padding:8px 0;font-size:13.5px;flex:1}
@media (max-width:560px){.news summary{grid-template-columns:3em 1fr;gap:0 8px}.news summary .o{grid-column:2;margin-top:-2px}.news-bar .meta{margin-left:0}.hero .boards{margin-left:0}}
"""

MEMORY_JS = """
(function(){
  var sel=new Set(), q='';
  var chips=document.querySelectorAll('.chips .chip'), items=document.querySelectorAll('.news'),
      months=document.querySelectorAll('.news-month'), box=document.getElementById('news-q'),
      count=document.getElementById('news-count');
  var byId={}; items.forEach(function(el){byId[el.dataset.id]=el;});
  function matchTopic(list){ if(!sel.size)return true; return list.split(' ').some(function(t){return sel.has(t)}); }
  function apply(){
    var n=0, qq=q.trim().toLowerCase();
    items.forEach(function(el){
      var ok=matchTopic(el.dataset.topics)&&(!qq||el.dataset.text.indexOf(qq)>=0);
      el.hidden=!ok; if(ok)n++;
    });
    months.forEach(function(m){
      var el=m.nextElementSibling, any=false;
      while(el&&!el.classList.contains('news-month')){ if(!el.hidden)any=true; el=el.nextElementSibling; }
      m.hidden=!any;
    });
    if(count)count.textContent=n;
    chips.forEach(function(c){c.classList.toggle('on', c.dataset.topic==='all' ? !sel.size : sel.has(c.dataset.topic));});
    applyTl();
  }
  chips.forEach(function(c){c.addEventListener('click',function(){
    var t=c.dataset.topic;
    if(t==='all')sel.clear(); else if(sel.has(t))sel.delete(t); else sel.add(t);
    apply();
  })});
  if(box)box.addEventListener('input',function(){q=box.value;apply();});
  document.querySelectorAll('.news summary .yt').forEach(function(a){a.addEventListener('click',function(e){
    e.preventDefault(); e.stopPropagation(); window.open(a.href,'_blank','noopener');
  })});
  // timeline: show the chosen mode, keep only selected branches (topic mode), hide filtered dots, re-pack rows
  function tlMode(){var b=document.querySelector('.tl-mode button.on');return b?b.dataset.mode:'topic';}
  function applyTl(){
    var mode=tlMode();
    document.querySelectorAll('svg.tl').forEach(function(s){
      s.hidden=s.dataset.mode!==mode; if(s.hidden)return;
      var top=+s.dataset.top, lh=+s.dataset.lane, w=+s.dataset.w, idx=0;
      s.querySelectorAll('.lane-g').forEach(function(g){
        var show=(mode!=='topic')||!sel.size||sel.has(g.dataset.key);
        g.style.display=show?'':'none'; if(!show)return;
        g.setAttribute('transform','translate(0,'+(top+idx*lh)+')'); idx++;
        g.querySelectorAll('.nd').forEach(function(d){var el=byId[d.dataset.id]; d.style.display=(el&&el.hidden)?'none':'';});
      });
      var h=top+Math.max(idx,1)*lh+8, y1=top+lh/2, y2=top+(Math.max(idx,1)-1)*lh+lh/2;
      s.setAttribute('height',h); s.setAttribute('viewBox','0 0 '+w+' '+h);
      var sp=s.querySelector('.spine'), rt=s.querySelector('.root');
      if(sp){sp.setAttribute('y1',y1);sp.setAttribute('y2',y2);} if(rt)rt.setAttribute('cy',(y1+y2)/2);
    });
  }
  document.querySelectorAll('.tl-mode button').forEach(function(b){b.addEventListener('click',function(e){
    e.preventDefault(); e.stopPropagation();
    document.querySelectorAll('.tl-mode button').forEach(function(x){x.classList.remove('on')}); b.classList.add('on');
    applyTl();
  })});
  function openItem(id){
    var el=byId[id]; if(!el)return;
    if(el.hidden){ sel.clear(); q=''; if(box)box.value=''; apply(); }
    el.open=true; el.scrollIntoView({behavior:'smooth',block:'center'});
    el.classList.add('hl'); setTimeout(function(){el.classList.remove('hl')},1600);
  }
  document.querySelectorAll('svg.tl .nd').forEach(function(g){
    g.addEventListener('click',function(){openItem(g.dataset.id)});
    g.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();openItem(g.dataset.id);}});
  });
})();
"""


def _load(key: str) -> dict:
    path = MEMORY_DATA_DIR / f"{key}.json"
    if not path.exists():
        return {"items": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {"items": data}


def load_items(key: str) -> list[dict]:
    return sorted(_load(key)["items"], key=lambda i: i["date"], reverse=True)


def live_channels(key: str) -> list[dict]:
    return _load(key).get("live_channels", [])


def _video_links(item: dict) -> tuple[str, str]:
    """(icon for the headline row, link line for the expanded body)."""
    search = YOUTUBE_SEARCH + quote_plus(item.get("headline_ko") or item["headline"])
    if item.get("video"):
        return (f'<a class="yt" href="{escape(item["video"])}" title="영상 보기 (YouTube)">▶</a>',
                f'<a class="go yt-go" href="{escape(item["video"])}" target="_blank" rel="noopener nofollow">▶ 영상 보기'
                f'{" · " + escape(item["video_channel"]) if item.get("video_channel") else ""}</a>')
    return (f'<a class="yt s" href="{escape(search)}" title="YouTube에서 관련 영상 검색">▶</a>',
            f'<a class="go yt-go s" href="{escape(search)}" target="_blank" rel="noopener nofollow">▶ YouTube에서 영상 검색</a>')


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


# ---------------------------------------------------------------- timeline (mind-map over time)

def _lanes(items: list[dict], mode: str) -> list[tuple[str, str, list[dict]]]:
    """(key, label, items) per branch. mode "topic": one branch per topic (an item can sit on several);
    mode "org": one branch per main organization (the item's first org), top N plus '기타'."""
    if mode == "topic":
        counts = Counter(t for i in items for t in i.get("topics", []))
        return [(t, TOPIC_LABELS.get(t, t), [i for i in items if t in i.get("topics", [])])
                for t, _ in counts.most_common()]
    primary = {i["_id"]: (i.get("orgs") or ["기타"])[0] for i in items}
    counts = Counter(primary.values())
    top = [o for o, _ in counts.most_common(MAX_ORG_LANES) if o != "기타"]
    lanes = [(o, o, [i for i in items if primary[i["_id"]] == o]) for o in top]
    rest = [i for i in items if primary[i["_id"]] not in top]
    if rest:
        lanes.append(("etc", "기타", rest))
    return lanes


def _fit(text: str, cjk_chars: int) -> str:
    """Truncate to roughly the width of `cjk_chars` Korean characters (Latin letters count half)."""
    budget, out = cjk_chars * 2, ""
    for ch in text:
        budget -= 2 if ord(ch) > 0x2E7F else 1
        if budget < 0:
            return out.rstrip() + "…"
        out += ch
    return out


def _text_w(text: str, px: float = 11) -> float:
    """Approximate rendered width: CJK glyphs are square, Latin glyphs about half as wide."""
    return sum(px if ord(ch) > 0x2E7F else px * 0.55 for ch in text)


def timeline_svg(items: list[dict], mode: str, title: str, hidden: bool = False) -> str:
    """Inline SVG: newest on the left, one colored branch per lane, one dot per article.
    Each lane is a <g class="lane-g" data-key> positioned by transform, so the page script can show
    a subset of branches and re-pack them; each dot carries data-id to open the matching headline."""
    lanes = _lanes(items, mode)
    dates = [date.fromisoformat(i["date"]) for i in items]
    d0, d1 = min(dates).replace(day=1), max(dates)
    months, d = [], d0
    while d <= d1:
        months.append(d)
        d = (d + timedelta(days=32)).replace(day=1)
    span = max(1, (d1 - d0).days + 1)
    left, right, top, lane_h = 128, 40, 30, 84
    # Month width grows with the busiest lane-month so labels keep room (clamped to 230..420px).
    busiest = max(Counter((li, i["date"][:7]) for li, (_, _, lane_items) in enumerate(lanes) for i in lane_items).values())
    width = max(1000, len(months) * min(420, max(230, 70 * busiest)) + left + right)
    height = top + len(lanes) * lane_h + 8

    def x(day: date) -> float:  # newest on the left, older to the right
        return left + (d1 - day).days / span * (width - left - right)

    out = [f'<svg class="tl" data-mode="{mode}" data-top="{top}" data-lane="{lane_h}" data-w="{width}"'
           f'{" hidden" if hidden else ""} viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
           f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{escape(title)} 타임라인 ({"분야별" if mode == "topic" else "회사별"})">']
    for md in months:
        mx = x(md)
        # the line marks the month's first day; the month itself extends to the left of it
        out.append(f'<line class="grid" x1="{mx:.0f}" y1="{top - 6}" x2="{mx:.0f}" y2="4000"/>'
                   f'<text class="mo" x="{mx - 3:.0f}" y="{top - 12}" text-anchor="end">{md.year % 100}.{md.month:02d}</text>')
    y_first, y_last = top + lane_h / 2, top + (len(lanes) - 1) * lane_h + lane_h / 2
    out.append(f'<line class="spine" x1="14" y1="{y_first:.0f}" x2="14" y2="{y_last:.0f}"/>'
               f'<circle class="root" cx="14" cy="{(y_first + y_last) / 2:.0f}" r="6"/>')
    slots = (-11, 17, -24, 30, -37)  # label baseline offsets from the branch line (5 rows)
    y = lane_h / 2  # lane-relative; the group transform places the lane
    for li, (key, label, lane_items) in enumerate(lanes):
        # colors by branch position, so every branch on a board gets its own color
        color = LANE_COLORS[li % len(LANE_COLORS)]
        alt = LANE_ALT_COLORS[li % len(LANE_ALT_COLORS)]
        out.append(f'<g class="lane-g" data-key="{escape(key)}" transform="translate(0,{top + li * lane_h})">'
                   f'<path class="br" d="M14 {y:.0f} C 20 {y:.0f}, 20 {y:.0f}, 26 {y:.0f}" style="stroke:{color}"/>'
                   f'<text class="lane" x="28" y="{y + 4:.0f}" style="fill:{color}">{escape(_fit(label, 8))}</text>'
                   f'<line class="ln" x1="{left}" y1="{y:.0f}" x2="{width - right}" y2="{y:.0f}" style="stroke:{color}"/>')
        right_edge = [-1e9] * len(slots)  # right-most occupied x per label row
        prev_x, prev_alt = -1e9, False
        for it in sorted(lane_items, key=lambda i: i["date"], reverse=True):
            nx = x(date.fromisoformat(it["date"]))
            use_alt = (nx - prev_x < CLOSE_PX) and not prev_alt  # alternate within a tight cluster
            prev_x, prev_alt = nx, use_alt
            c = alt if use_alt else color
            text = it.get("headline_ko") or it["headline"]
            short = _fit(text, 12)
            half = _text_w(short) / 2
            free = [j for j in range(len(slots)) if nx - half > right_edge[j] + 8]
            lbl = ""
            if free:
                si = free[0]
                right_edge[si] = nx + half
                dy = slots[si]
                # a hairline from the dot to the label so the pairing stays clear
                y1, y2 = (y - 5, y + dy + 3) if dy < 0 else (y + 5, y + dy - 10)
                lbl = (f'<line class="tick" x1="{nx:.0f}" y1="{y1:.0f}" x2="{nx:.0f}" y2="{y2:.0f}" style="stroke:{c}"/>'
                       f'<text class="lb" x="{nx:.0f}" y="{y + dy:.0f}" text-anchor="middle" style="fill:{c}">{escape(short)}</text>')
            out.append(f'<g class="nd{"" if lbl else " bare"}" data-id="{it["_id"]}" tabindex="0"><title>{escape(it["date"])} · {escape(text)}</title>'
                       f'<circle cx="{nx:.0f}" cy="{y:.0f}" r="4" style="fill:{c}"/>{lbl}</g>')
        out.append("</g>")
    out.append("</svg>")
    return "".join(out)


def timeline_panel(items: list[dict], title: str) -> str:
    return (f'<details class="tl-panel"><summary>🗺 타임라인 <span class="hint">누르면 펼쳐집니다 · 왼쪽이 최신, 오른쪽이 과거 · 위에서 고른 분류·검색이 그대로 적용됩니다</span>'
            f'<span class="tl-mode"><button class="chip on" data-mode="topic">분야별</button>'
            f'<button class="chip" data-mode="org">회사·기관별</button></span></summary>'
            f'<div class="tl-scroll">{timeline_svg(items, "topic", title)}{timeline_svg(items, "org", title, hidden=True)}</div></details>')


# ---------------------------------------------------------------- headline list

def _item_html(item: dict) -> str:
    d = date.fromisoformat(item["date"])
    head_ko = item.get("headline_ko") or item["headline"]
    orig = item["headline"] if item["headline"] != head_ko else ""
    topics = " ".join(item.get("topics", []))
    text = " ".join([head_ko, item["headline"], item.get("outlet", ""), *item.get("orgs", []),
                     *(TOPIC_LABELS.get(t, t) for t in item.get("topics", []))]).lower()
    tags = "".join(f"<span>{escape(TOPIC_LABELS.get(t, t))}</span>" for t in item.get("topics", []))
    tags += "".join(f"<span>{escape(o)}</span>" for o in item.get("orgs", []))
    yt_icon, yt_link = _video_links(item)
    return (f'<details class="news" data-id="{item["_id"]}" data-topics="{escape(topics)}" data-text="{escape(text)}">'
            f'<summary><span class="d">{d.month}.{d.day:02d}</span><span class="h">{escape(head_ko)}</span>'
            f'<span class="o"><b>{escape(item.get("outlet", ""))}</b>{yt_icon}</span></summary>'
            f'<div class="body"><p>{escape(item.get("summary_ko", ""))}</p>'
            f'{f"<p class=orig>원제: {escape(orig)}</p>" if orig else ""}'
            f'<div class="tags">{tags}</div>'
            f'<a class="go" href="{escape(item["url"])}" target="_blank" rel="noopener nofollow">원문 보기 ↗</a> {yt_link}'
            f'</div></details>')


def news_list_html(items: list[dict], title: str = "") -> str:
    if not items:
        return '<p class="news-empty">아직 모아 둔 기사가 없습니다.</p>'
    items = [{**i, "_id": n} for n, i in enumerate(items)]
    topics = OrderedDict()
    for i in items:
        for t in i.get("topics", []):
            topics[t] = topics.get(t, 0) + 1
    chips = '<button class="chip on" data-topic="all">전체</button>' + "".join(
        f'<button class="chip" data-topic="{escape(t)}">{escape(TOPIC_LABELS.get(t, t))} {n}</button>'
        for t, n in sorted(topics.items(), key=lambda x: -x[1]))
    out = [f'<div class="news-bar"><input id="news-q" type="search" placeholder="검색: 회사, 키워드, 언론사">'
           f'<div class="chips">{chips}</div>'
           f'<span class="meta"><span id="news-count">{len(items)}</span>건 · {items[0]["date"]} 기준</span></div>',
           timeline_panel(items, title)]
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


# ---------------------------------------------------------------- pages

def board_cards(cfg: dict, preview: int = 6) -> str:
    """One card per board: name, count, and the latest headlines (linking to the originals)."""
    m = cfg["memory"]
    base = cfg["site_url"]
    cards = []
    for key, b in m["boards"].items():
        items = load_items(key)
        href = f"{base}/memory/{key}/"
        if items:
            rows = "".join(
                f'<li><span class="d">{i["date"][5:].replace("-", ".")}</span>'
                f'<a href="{escape(i["url"])}" target="_blank" rel="noopener nofollow" title="{escape(i.get("headline_ko") or i["headline"])}">'
                f'{escape(i.get("headline_ko") or i["headline"])}</a></li>'
                for i in items[:preview])
            body = f'<ul class="preview">{rows}</ul><a class="more" href="{href}">전체 {len(items)}건 보기 →</a>'
        else:
            body = f'<p class="news-empty">아직 모아 둔 기사가 없습니다.</p><a class="more" href="{href}">게시판 열기 →</a>'
        cards.append(
            f'<section class="board-card"><a class="head" href="{href}"><span class="emoji">{b["emoji"]}</span>'
            f'<span><b>{escape(b["name"])}</b><small>{escape(b["desc"])}</small></span>'
            f'{f"<span class=count>{len(items)}</span>" if items else ""}</a>{body}</section>')
    return '<div class="board-grid">' + "".join(cards) + "</div>"


def index_body(cfg: dict) -> str:
    m = cfg["memory"]
    return (f'<section class="hero compact"><span class="kicker">🗂 {escape(m["title"])}</span>'
            f'<h1>{escape(m["title"])}</h1><p>{escape(m["desc"])}</p></section>'
            f'{board_cards(cfg)}')


def board_body(cfg: dict, key: str) -> str:
    m = cfg["memory"]
    b = m["boards"][key]
    others = "".join(
        f'<a href="{cfg["site_url"]}/memory/{k}/">{o["emoji"]} {escape(o["name"])}</a>'
        for k, o in m["boards"].items() if k != key
    )
    live = "".join(f'<a href="{escape(ch["url"])}" target="_blank" rel="noopener nofollow">{escape(ch["name"])}</a>'
                   for ch in live_channels(key))
    live_row = f'<div class="live-row"><span class="live-dot">LIVE</span>{live}</div>' if live else ""
    # One line: kicker · board name · description · links to the other boards
    return (f'<section class="hero compact"><span class="kicker">{b["emoji"]} {escape(m["title"])}</span>'
            f'<h1>{escape(b["name"])}</h1><p>{escape(b["desc"])}</p><nav class="boards">{others}</nav></section>'
            f'{live_row}'
            f'<section class="board-feed">{news_list_html(load_items(key), b["name"])}</section>'
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
