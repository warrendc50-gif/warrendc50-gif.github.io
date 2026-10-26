"""Middle-school English vocabulary pages (/words/): word list, flashcards and a quiz per grade.

Word lists live in data/words/grade{1,2,3}.json as [word, meaning, example, example_ko] rows.
Each word gets a scene illustration drawn by Claude, saved as data/words/art/<grade>/<slug>.svg.
"""
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from html import escape

from .config import DATA_DIR

ART_DIR = DATA_DIR / "words" / "art"
# Anything that could run code or load something from elsewhere is rejected.
UNSAFE_SVG = re.compile(r"<\s*(script|style|image|foreignObject|a|use|iframe)\b|\bon[a-z]+\s*=|href|javascript:|url\(", re.I)

GRADES = {
    1: ("중1 필수 영단어", "학교·가족·하루 일과처럼 매일 쓰는 기초 단어"),
    2: ("중2 필수 영단어", "경험·환경·건강·감정을 말할 때 쓰는 단어"),
    3: ("중3 필수 영단어", "사회·과학·의견 표현과 자주 나오는 숙어"),
}

WORDS_CSS = """
.wd-tabs{display:flex;gap:6px;margin:14px 0}
.wd-tabs button,.wd-btn{border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:10px;padding:8px 14px;font-weight:700;cursor:pointer;font-size:15px}
.wd-tabs button.on{background:var(--fg);color:var(--bg)}
.wd-bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:8px 0;color:var(--muted);font-size:14px}
.wd-list{list-style:none;padding:0;margin:0}
.wd-list li{display:flex;gap:12px;align-items:flex-start;border-bottom:1px solid var(--line);padding:12px 4px}
.wd-list .w{font-weight:800;font-size:18px;min-width:120px}
.wd-list .m{font-weight:700}
.wd-list .ex{color:var(--muted);font-size:14px;margin-top:2px}
.wd-list li.known .w{text-decoration:line-through;opacity:.5}
.wd-list input{margin-top:6px;width:18px;height:18px}
.wd-card{border:1px solid var(--line);border-radius:16px;background:var(--card);min-height:220px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:24px;cursor:pointer;user-select:none}
.wd-card .w{font-size:34px;font-weight:800}
.wd-card .m{font-size:22px;font-weight:700;margin-top:10px}
.wd-card .ex{color:var(--muted);margin-top:10px}
.wd-nav{display:flex;justify-content:space-between;align-items:center;margin-top:12px}
.wd-q{font-size:30px;font-weight:800;text-align:center;margin:18px 0}
.wd-opts{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.wd-opts button{border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:12px;padding:14px 10px;font-size:16px;font-weight:700;cursor:pointer}
.wd-opts button.ok{background:#16a34a;color:#fff;border-color:#16a34a}
.wd-opts button.no{background:#dc2626;color:#fff;border-color:#dc2626}
.wd-grades{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}
.wd-grades a{display:block;border:1px solid var(--line);border-radius:14px;padding:18px;background:var(--card);color:var(--fg);text-decoration:none}
.wd-grades b{font-size:20px}
.wd-list .wd-img{width:144px;height:90px;border-radius:10px;flex:none;border:1px solid var(--line)}
.wd-card .wd-img{width:100%;max-width:400px;aspect-ratio:8/5;border-radius:14px;margin-bottom:14px}
.wd-qimg{display:block;width:100%;max-width:320px;aspect-ratio:8/5;border-radius:14px;margin:0 auto 6px}
"""

WORDS_JS = """
(function(){
const W=JSON.parse(document.getElementById('wd-data').textContent), KEY='wd-known-'+document.getElementById('wd').dataset.grade;
let known={};try{known=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}
const save=()=>{try{localStorage.setItem(KEY,JSON.stringify(known))}catch(e){}};
const $=s=>document.querySelector(s), view=$('#wd-view'), esc=s=>s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const img=(w,c)=>w[4]?'<img class="'+c+'" src="'+w[4]+'" alt="" loading="lazy">':'';
let hide=false, order=W.map((_,i)=>i), pos=0, flipped=false, score=0, tries=0;
const pool=()=>order.filter(i=>!(hide&&known[W[i][0]]));
const count=()=>{$('#wd-count').textContent='외운 단어 '+W.filter(w=>known[w[0]]).length+' / '+W.length};
function list(){
  view.innerHTML='<ul class="wd-list">'+pool().map(i=>{const w=W[i];return '<li class="'+(known[w[0]]?'known':'')+'"><input type="checkbox" data-w="'+esc(w[0])+'"'+(known[w[0]]?' checked':'')+' aria-label="외웠어요">'+img(w,'wd-img')+'<div><div><span class="w">'+esc(w[0])+'</span> <span class="m">'+esc(w[1])+'</span></div><div class="ex">'+esc(w[2])+'<br>'+esc(w[3])+'</div></div></li>'}).join('')+'</ul>';
  view.querySelectorAll('input').forEach(b=>b.onchange=()=>{known[b.dataset.w]=b.checked;if(!b.checked)delete known[b.dataset.w];save();count();b.closest('li').classList.toggle('known',b.checked)});
}
function card(){
  const p=pool(); if(!p.length){view.innerHTML='<p>모든 단어를 외웠어요! 🎉</p>';return}
  pos=(pos+p.length)%p.length; const w=W[p[pos]];
  view.innerHTML='<div class="wd-card" id="wd-c">'+img(w,'wd-img')+'<div class="w">'+esc(w[0])+'</div>'+(flipped?'<div class="m">'+esc(w[1])+'</div><div class="ex">'+esc(w[2])+'<br>'+esc(w[3])+'</div>':'<div class="ex">눌러서 뜻 보기</div>')+'</div>'
   +'<div class="wd-nav"><button class="wd-btn" id="wd-prev">← 이전</button><span>'+(pos+1)+' / '+p.length+'</span><button class="wd-btn" id="wd-know">'+(known[w[0]]?'✅ 외웠어요':'외웠어요')+'</button><button class="wd-btn" id="wd-next">다음 →</button></div>';
  $('#wd-c').onclick=()=>{flipped=!flipped;card()};
  $('#wd-prev').onclick=()=>{pos--;flipped=false;card()};
  $('#wd-next').onclick=()=>{pos++;flipped=false;card()};
  $('#wd-know').onclick=()=>{if(known[w[0]])delete known[w[0]];else known[w[0]]=true;save();count();card()};
}
function quiz(){
  const p=pool(); if(p.length<4){view.innerHTML='<p>남은 단어가 4개보다 적어요. 외운 단어 숨기기를 꺼 보세요.</p>';return}
  const ans=p[Math.floor(Math.random()*p.length)], opts=[ans];
  while(opts.length<4){const r=Math.floor(Math.random()*W.length);if(!opts.includes(r))opts.push(r)}
  opts.sort(()=>Math.random()-.5);
  view.innerHTML='<p class="wd-bar">점수 '+score+' / '+tries+'</p>'+img(W[ans],'wd-qimg')+'<div class="wd-q">'+esc(W[ans][0])+'</div><div class="wd-opts">'+opts.map(i=>'<button data-i="'+i+'">'+esc(W[i][1])+'</button>').join('')+'</div><p class="wd-bar" id="wd-ex"></p>';
  view.querySelectorAll('.wd-opts button').forEach(b=>b.onclick=()=>{
    if(view.dataset.done)return; view.dataset.done=1; tries++; const ok=+b.dataset.i===ans; if(ok)score++;
    b.classList.add(ok?'ok':'no'); view.querySelector('[data-i="'+ans+'"]').classList.add('ok');
    $('#wd-ex').innerHTML=esc(W[ans][2])+' — '+esc(W[ans][3])+' <button class="wd-btn" id="wd-nx">다음 문제 →</button>';
    $('#wd-nx').onclick=()=>{delete view.dataset.done;quiz()};
  });
}
const modes={list,card,quiz}; let mode='list';
document.querySelectorAll('.wd-tabs button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.wd-tabs button').forEach(x=>x.classList.remove('on'));b.classList.add('on');mode=b.dataset.m;flipped=false;delete view.dataset.done;modes[mode]()});
$('#wd-hide').onchange=e=>{hide=e.target.checked;pos=0;modes[mode]()};
$('#wd-shuffle').onclick=()=>{order.sort(()=>Math.random()-.5);pos=0;modes[mode]()};
count(); list();
})();
"""


def load_words(grade: int) -> list[list[str]]:
    return json.loads((DATA_DIR / "words" / f"grade{grade}.json").read_text(encoding="utf-8"))


def render_grade(grade: int, base: str) -> str:
    title, desc = GRADES[grade]
    words = load_words(grade)
    # A fifth column carries the picture URL ("" until the word has been illustrated).
    rows = [row + [f"{base}/words/art/{grade}/{art_slug(row[0])}.svg" if art_path(grade, row[0]).exists() else ""]
            for row in words]
    data = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    others = " · ".join(f'<a href="{base}/words/{g}/">{escape(GRADES[g][0])}</a>' for g in GRADES if g != grade)
    return f"""<style>{WORDS_CSS}</style>
<section class="hero"><span class="kicker">🔤 영단어</span><h1>{escape(title)} {len(words)}개</h1>
<p>{escape(desc)}. 그림으로 상황을 떠올리며 목록으로 훑어보고, 카드로 외우고, 퀴즈로 확인하세요. 외운 단어 표시는 이 기기에만 저장됩니다.</p></section>
<div id="wd" data-grade="{grade}">
<div class="wd-tabs"><button class="on" data-m="list">📋 목록</button><button data-m="card">🃏 카드</button><button data-m="quiz">❓ 퀴즈</button></div>
<div class="wd-bar"><span id="wd-count"></span><label><input type="checkbox" id="wd-hide"> 외운 단어 숨기기</label><button class="wd-btn" id="wd-shuffle">🔀 섞기</button></div>
<div id="wd-view"></div>
</div>
<p class="wd-bar">다른 학년: {others}</p>
<script type="application/json" id="wd-data">{data}</script>
<script>{WORDS_JS}</script>"""


def render_index(base: str) -> str:
    cards = "".join(
        f'<a href="{base}/words/{g}/"><b>{escape(t)}</b><br><span>{escape(d)}</span><br><small>{len(load_words(g))}개</small></a>'
        for g, (t, d) in GRADES.items())
    return f"""<style>{WORDS_CSS}</style>
<section class="hero"><span class="kicker">🔤 영단어</span><h1>중학생 학년별 필수 영단어</h1>
<p>학년을 고르면 단어 목록·카드·퀴즈로 외울 수 있어요.</p></section>
<div class="wd-grades">{cards}</div>"""


def art_slug(word: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", word.lower()).strip("-") or "word"


def art_path(grade: int, word: str):
    return ART_DIR / str(grade) / f"{art_slug(word)}.svg"


def clean_svg(svg: str) -> str | None:
    svg = svg.strip()
    if not (svg.startswith("<svg") and svg.endswith("</svg>")) or len(svg) > 12000 or UNSAFE_SVG.search(svg):
        return None
    return svg


def illustrate_missing(writer, limit: int = 500, batch: int = 8, workers: int = 4) -> int:
    """Draw scene pictures for words that have none yet; returns how many were saved."""
    todo = [(g, row) for g in GRADES for row in load_words(g) if not art_path(g, row[0]).exists()][:limit]
    chunks = [todo[i:i + batch] for i in range(0, len(todo), batch)]

    def draw(chunk):
        try:
            return chunk, writer.draw_word_scenes([row for _, row in chunk])
        except Exception as exc:  # one failed batch shouldn't stop the others
            print(f"[words] drawing failed: {exc}", file=sys.stderr)
            return chunk, {}

    saved = 0
    with ThreadPoolExecutor(workers) as pool:
        for chunk, svgs in pool.map(draw, chunks):
            for grade, row in chunk:
                svg = clean_svg(svgs.get(row[0], ""))
                if svg:
                    path = art_path(grade, row[0])
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(svg + "\n", encoding="utf-8")
                    saved += 1
    print(f"[words] drew {saved} of {len(todo)} missing pictures")
    return saved
