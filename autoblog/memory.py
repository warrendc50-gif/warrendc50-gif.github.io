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
.chip[data-topic]:not([data-topic=all])::before,.pchip.mo::before{content:"☐";margin-right:4px;font-size:11px}
.chip.on[data-topic]:not([data-topic=all])::before,.pchip.mo.on::before{content:"☑"}
.tl-bar{display:flex;flex-wrap:wrap;gap:4px 8px;align-items:center;padding:4px 10px 6px;border-bottom:1px dashed var(--line);font-size:12px;color:var(--muted)}
.tl-bar .pgroup{display:inline-flex;flex-wrap:wrap;gap:3px;align-items:center;padding:2px 4px;border:1px dashed var(--line);border-radius:99px}
.tl-bar .pchip.yr{font-weight:800}
.tl-bar .tl-mode{margin-left:auto;display:flex;gap:4px}
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
svg.tl .grid.wk{opacity:.6;stroke-dasharray:2 3}
svg.tl .today{stroke:var(--accent);stroke-width:1.5;stroke-dasharray:3 3;opacity:.85}
svg.tl .today-lb{font-size:10px;font-weight:700;fill:var(--accent)}
svg.tl .mo.wk{font-size:10px}
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
  var sel=new Set(), q='', per=new Set();  // selected topics, search text, selected months (YYYY-MM; empty = all)
  var chips=document.querySelectorAll('.news-bar .chips .chip'), items=document.querySelectorAll('.news'),
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
    renderTl();
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
  function openItem(id){
    var el=byId[id]; if(!el)return;
    if(el.hidden){ sel.clear(); q=''; if(box)box.value=''; apply(); }
    el.open=true; el.scrollIntoView({behavior:'smooth',block:'center'});
    el.classList.add('hl'); setTimeout(function(){el.classList.remove('hl')},1600);
  }

  // ---------- timeline: drawn in the browser from #tl-data, newest on the left ----------
  var dataEl=document.getElementById('tl-data'), host=document.getElementById('tl-host'), bar=document.getElementById('tl-period');
  var panel=document.querySelector('.tl-panel');
  function renderTl(){ if(dataEl&&host&&panel&&panel.open) draw(); }
  if(!dataEl||!host||!bar) return;
  var D=JSON.parse(dataEl.textContent), COLORS=D.colors, ALT=D.alt;
  var allMonths=[]; D.items.forEach(function(it){var m=it.d.slice(0,7); if(allMonths.indexOf(m)<0)allMonths.push(m);});
  allMonths.sort().reverse();
  var years=[]; allMonths.forEach(function(m){var y=m.slice(0,4); if(years.indexOf(y)<0)years.push(y);});
  function monthsOf(y){return allMonths.filter(function(m){return m.slice(0,4)===y;});}
  function buildBar(){
    var h='<button class="chip pchip on" data-all="1">전체</button>';
    years.forEach(function(y){
      h+='<span class="pgroup"><button class="chip pchip yr" data-year="'+y+'">'+y+'</button>';
      monthsOf(y).forEach(function(m){h+='<button class="chip pchip mo" data-month="'+m+'">'+parseInt(m.slice(5),10)+'월</button>';});
      h+='</span>';
    });
    bar.innerHTML=h;
    bar.querySelectorAll('.pchip').forEach(function(b){b.addEventListener('click',function(){
      if(b.dataset.all){per.clear();}
      else if(b.dataset.year){var ms=monthsOf(b.dataset.year), all=ms.every(function(m){return per.has(m);});
        ms.forEach(function(m){ if(all)per.delete(m); else per.add(m); });}
      else { if(per.has(b.dataset.month))per.delete(b.dataset.month); else per.add(b.dataset.month); }
      syncBar(); draw();
    });});
    syncBar();
  }
  function syncBar(){
    bar.querySelectorAll('.pchip').forEach(function(b){
      if(b.dataset.all)b.classList.toggle('on',!per.size);
      else if(b.dataset.year){var ms=monthsOf(b.dataset.year); b.classList.toggle('on',ms.length>0&&ms.every(function(m){return per.has(m);}));}
      else b.classList.toggle('on',per.has(b.dataset.month));
    });
  }
  function tlMode(){var b=document.querySelector('.tl-mode button.on');return b?b.dataset.mode:'topic';}
  function tw(t){var w=0;for(var i=0;i<t.length;i++)w+=t.charCodeAt(i)>0x2E7F?11:6.05;return w;}
  function esc(t){return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;');}
  function fit(t,n){var b=n*2,o='';for(var i=0;i<t.length;i++){b-=t.charCodeAt(i)>0x2E7F?2:1;if(b<0)return o.replace(/\\s+$/,'')+'…';o+=t[i];}return o;}
  function draw(){
    var mode=tlMode();
    var ms=per.size?allMonths.filter(function(m){return per.has(m);}):allMonths.slice();
    var vis=D.items.filter(function(it){var el=byId[it.i]; return ms.indexOf(it.d.slice(0,7))>=0&&!(el&&el.hidden);});
    if(!vis.length){host.innerHTML='<p class="news-empty">선택한 기간에 해당하는 기사가 없습니다.</p>';return;}
    var lanes=[];
    if(mode==='topic'){
      var cnt={}; vis.forEach(function(it){it.t.forEach(function(t){cnt[t]=(cnt[t]||0)+1;});});
      Object.keys(cnt).filter(function(t){return !sel.size||sel.has(t);}).sort(function(a,b){return cnt[b]-cnt[a];})
        .forEach(function(t){lanes.push({label:D.labels[t]||t,items:vis.filter(function(it){return it.t.indexOf(t)>=0;})});});
    } else {
      var oc={}; vis.forEach(function(it){oc[it.o]=(oc[it.o]||0)+1;});
      var top=Object.keys(oc).filter(function(o){return o!=='기타';}).sort(function(a,b){return oc[b]-oc[a];}).slice(0,8);
      top.forEach(function(o){lanes.push({label:o,items:vis.filter(function(it){return it.o===o;})});});
      var rest=vis.filter(function(it){return top.indexOf(it.o)<0;}); if(rest.length)lanes.push({label:'기타',items:rest});
    }
    // Only days that have news get a column (newest on the left, starting at today), so empty
    // stretches of time are skipped instead of drawn as blank space.
    var now=new Date(), td=now.getFullYear()+'-'+('0'+(now.getMonth()+1)).slice(-2)+'-'+('0'+now.getDate()).slice(-2);
    var days=[]; vis.forEach(function(it){if(days.indexOf(it.d)<0)days.push(it.d);}); days.sort().reverse();
    if(ms.indexOf(td.slice(0,7))>=0&&days.indexOf(td)<0)days.unshift(td);
    var perDay={}; lanes.forEach(function(l){var c={}; l.items.forEach(function(it){c[it.d]=(c[it.d]||0)+1;});
      Object.keys(c).forEach(function(d){perDay[d]=Math.max(perDay[d]||0,c[d]);});});
    var left=128,right=40,top=30,laneH=84;
    var colX={}, colW={}, cx=left;
    days.forEach(function(d){colW[d]=perDay[d]?Math.max(72,62*perDay[d]):40; colX[d]=cx; cx+=colW[d];});
    var width=Math.round(cx+right), height=top+lanes.length*laneH+8;
    function x(d,k,n){return colX[d]+(k+0.5)*colW[d]/n;}
    var s='<svg class="tl" viewBox="0 0 '+width+' '+height+'" width="'+width+'" height="'+height+'" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="타임라인">';
    days.forEach(function(d,i){
      var x0=colX[d], newMonth=i===0||days[i-1].slice(0,7)!==d.slice(0,7);
      s+='<line class="grid'+(newMonth?'':' wk')+'" x1="'+x0+'" y1="'+(top-6)+'" x2="'+x0+'" y2="'+(height-4)+'"/>';
      s+='<text class="mo wk" x="'+(x0+colW[d]/2)+'" y="'+(top-12)+'" text-anchor="middle">'+(+d.slice(8,10))+'일</text>';
      if(newMonth)s+='<text class="mo" x="'+(x0+3)+'" y="'+(top-22)+'">'+d.slice(2,4)+'.'+d.slice(5,7)+'</text>';
    });
    if(colX[td]!==undefined){ var tx=colX[td]+colW[td]/2;
      s+='<line class="today" x1="'+tx+'" y1="'+(top-4)+'" x2="'+tx+'" y2="'+(height-4)+'"/><text class="today-lb" x="'+(tx+4)+'" y="'+(top-2)+'">오늘</text>'; }
    var y1=top+laneH/2, y2=top+(lanes.length-1)*laneH+laneH/2;
    s+='<line class="spine" x1="14" y1="'+y1+'" x2="14" y2="'+y2+'"/><circle class="root" cx="14" cy="'+((y1+y2)/2)+'" r="6"/>';
    var slots=[-11,17,-24,30,-37];
    lanes.forEach(function(l,li){
      var y=top+li*laneH+laneH/2, c0=COLORS[li%COLORS.length], c1=ALT[li%ALT.length];
      s+='<path class="br" d="M14 '+y+' C 20 '+y+', 20 '+y+', 26 '+y+'" style="stroke:'+c0+'"/><text class="lane" x="28" y="'+(y+4)+'" style="fill:'+c0+'">'+esc(fit(l.label,8))+'</text><line class="ln" x1="'+left+'" y1="'+y+'" x2="'+(width-right)+'" y2="'+y+'" style="stroke:'+c0+'"/>';
      var edge=[-1e9,-1e9,-1e9,-1e9,-1e9], prevX=-1e9, prevAlt=false, nDay={}, kDay={};
      l.items.forEach(function(it){nDay[it.d]=(nDay[it.d]||0)+1;});
      l.items.slice().sort(function(a,b){return a.d<b.d?1:a.d>b.d?-1:0;}).forEach(function(it){
        var k=kDay[it.d]||0; kDay[it.d]=k+1;
        var nx=x(it.d,k,nDay[it.d]), useAlt=(nx-prevX<26)&&!prevAlt; prevX=nx; prevAlt=useAlt; var c=useAlt?c1:c0;
        var half=tw(it.h)/2, si=-1; for(var j=0;j<slots.length;j++){ if(nx-half>edge[j]+8){si=j;break;} }
        var lbl='';
        if(si>=0){ edge[si]=nx+half; var dy=slots[si], ya=dy<0?y-5:y+5, yb=dy<0?y+dy+3:y+dy-10;
          lbl='<line class="tick" x1="'+nx+'" y1="'+ya+'" x2="'+nx+'" y2="'+yb+'" style="stroke:'+c+'"/><text class="lb" x="'+nx+'" y="'+(y+dy)+'" text-anchor="middle" style="fill:'+c+'">'+esc(it.h)+'</text>'; }
        s+='<g class="nd'+(lbl?'':' bare')+'" data-id="'+it.i+'" tabindex="0"><title>'+esc(it.d+' · '+it.f)+'</title><circle cx="'+nx+'" cy="'+y+'" r="4" style="fill:'+c+'"/>'+lbl+'</g>';
      });
    });
    host.innerHTML=s+'</svg>';
    host.querySelectorAll('.nd').forEach(function(g){
      g.addEventListener('click',function(){openItem(g.dataset.id);});
      g.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();openItem(g.dataset.id);}});
    });
  }
  document.querySelectorAll('.tl-mode button').forEach(function(b){b.addEventListener('click',function(){
    document.querySelectorAll('.tl-mode button').forEach(function(x){x.classList.remove('on');}); b.classList.add('on'); draw();
  });});
  panel.addEventListener('toggle',function(){ if(panel.open) draw(); });
  var rt; window.addEventListener('resize',function(){clearTimeout(rt); rt=setTimeout(renderTl,150);});
  buildBar(); renderTl();
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

def _fit(text: str, cjk_chars: int) -> str:
    """Truncate to roughly the width of `cjk_chars` Korean characters (Latin letters count half)."""
    budget, out = cjk_chars * 2, ""
    for ch in text:
        budget -= 2 if ord(ch) > 0x2E7F else 1
        if budget < 0:
            return out.rstrip() + "…"
        out += ch
    return out


def timeline_panel(items: list[dict], title: str) -> str:
    """The timeline panel: a period picker (years and months, multi-select), the branch mode switch,
    and the data the page script draws the SVG from (one record per article)."""
    records = [{"i": it["_id"], "d": it["date"], "t": it.get("topics", []),
                "o": (it.get("orgs") or ["기타"])[0],
                "h": _fit(it.get("headline_ko") or it["headline"], 12),
                "f": it.get("headline_ko") or it["headline"]} for it in items]
    labels = {t: TOPIC_LABELS[t] for t in {t for it in items for t in it.get("topics", [])} if t in TOPIC_LABELS}
    data = json.dumps({"title": title, "items": records, "labels": labels,
                       "colors": LANE_COLORS, "alt": LANE_ALT_COLORS}, ensure_ascii=False).replace("</", "<\\/")
    return (f'<details class="tl-panel"><summary>🗺 타임라인 <span class="hint">누르면 펼쳐집니다 · 왼쪽 끝이 오늘 ·'
            f'연도·월을 여러 개 골라 볼 수 있고, 위의 분류·검색도 그대로 적용됩니다</span></summary>'
            f'<div class="tl-bar"><span>기간</span><span id="tl-period" class="chips"></span>'
            f'<span class="tl-mode"><button class="chip on" data-mode="topic">분야별</button>'
            f'<button class="chip" data-mode="org">회사·기관별</button></span></div>'
            f'<div class="tl-scroll" id="tl-host"></div></details>'
            f'<script type="application/json" id="tl-data">{data}</script>')


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
