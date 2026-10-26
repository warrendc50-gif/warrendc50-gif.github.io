"""Middle-school English vocabulary pages (/words/): word list, flashcards and a quiz per grade.

Word lists live in data/words/grade{1,2,3}.json as [word, meaning, example, example_ko] rows.
"""
import json
from html import escape

from .config import DATA_DIR

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
"""

WORDS_JS = """
(function(){
const W=JSON.parse(document.getElementById('wd-data').textContent), KEY='wd-known-'+document.getElementById('wd').dataset.grade;
let known={};try{known=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}
const save=()=>{try{localStorage.setItem(KEY,JSON.stringify(known))}catch(e){}};
const $=s=>document.querySelector(s), view=$('#wd-view'), esc=s=>s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let hide=false, order=W.map((_,i)=>i), pos=0, flipped=false, score=0, tries=0;
const pool=()=>order.filter(i=>!(hide&&known[W[i][0]]));
const count=()=>{$('#wd-count').textContent='외운 단어 '+W.filter(w=>known[w[0]]).length+' / '+W.length};
function list(){
  view.innerHTML='<ul class="wd-list">'+pool().map(i=>{const w=W[i];return '<li class="'+(known[w[0]]?'known':'')+'"><input type="checkbox" data-w="'+esc(w[0])+'"'+(known[w[0]]?' checked':'')+' aria-label="외웠어요"><div><div><span class="w">'+esc(w[0])+'</span> <span class="m">'+esc(w[1])+'</span></div><div class="ex">'+esc(w[2])+'<br>'+esc(w[3])+'</div></div></li>'}).join('')+'</ul>';
  view.querySelectorAll('input').forEach(b=>b.onchange=()=>{known[b.dataset.w]=b.checked;if(!b.checked)delete known[b.dataset.w];save();count();b.closest('li').classList.toggle('known',b.checked)});
}
function card(){
  const p=pool(); if(!p.length){view.innerHTML='<p>모든 단어를 외웠어요! 🎉</p>';return}
  pos=(pos+p.length)%p.length; const w=W[p[pos]];
  view.innerHTML='<div class="wd-card" id="wd-c"><div class="w">'+esc(w[0])+'</div>'+(flipped?'<div class="m">'+esc(w[1])+'</div><div class="ex">'+esc(w[2])+'<br>'+esc(w[3])+'</div>':'<div class="ex">눌러서 뜻 보기</div>')+'</div>'
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
  view.innerHTML='<p class="wd-bar">점수 '+score+' / '+tries+'</p><div class="wd-q">'+esc(W[ans][0])+'</div><div class="wd-opts">'+opts.map(i=>'<button data-i="'+i+'">'+esc(W[i][1])+'</button>').join('')+'</div><p class="wd-bar" id="wd-ex"></p>';
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
    data = json.dumps(words, ensure_ascii=False).replace("</", "<\\/")
    others = " · ".join(f'<a href="{base}/words/{g}/">{escape(GRADES[g][0])}</a>' for g in GRADES if g != grade)
    return f"""<style>{WORDS_CSS}</style>
<section class="hero"><span class="kicker">🔤 영단어</span><h1>{escape(title)} {len(words)}개</h1>
<p>{escape(desc)}. 목록으로 훑어보고, 카드로 외우고, 퀴즈로 확인하세요. 외운 단어 표시는 이 기기에만 저장됩니다.</p></section>
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
