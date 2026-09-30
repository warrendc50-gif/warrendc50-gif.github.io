"""Interactive calculator pages. Each tool is plain HTML + inline JS rendered inside the site layout.

Only calculators whose math doesn't depend on frequently changing regulations are included,
so results stay correct without maintenance.
"""

TOOL_CSS = """
.tool{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:20px;margin:24px 0}
.tool label{display:block;font-size:15px;font-weight:600;margin:14px 0 6px}
.tool input,.tool select{width:100%;font:inherit;padding:10px 12px;border:1px solid var(--line);
  border-radius:8px;background:var(--bg);color:var(--fg)}
.tool .row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.tool .result{margin-top:20px;padding:16px;border-radius:10px;background:var(--bg);border:1px solid var(--line)}
.tool .result b{font-size:22px;color:var(--accent)}
.tool .result p{margin:6px 0}
.tool details{margin-top:12px}
.tool-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;margin:0 0 8px}
.tool-list a{display:block;background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px 18px;text-decoration:none;color:var(--fg);transition:border-color .15s}
.tool-list a:hover{border-color:var(--accent)}
.tool-list a b{display:block;color:var(--accent);margin-bottom:4px}
.tool-list a span{font-size:14px;color:var(--muted)}
"""

# Shared JS helpers: number parsing (accepts commas) and Korean-formatted output.
_JS_HELPERS = """
const $ = id => document.getElementById(id);
const num = id => parseFloat(String($(id).value).replace(/,/g, '')) || 0;
const won = v => Math.round(v).toLocaleString('ko-KR') + '원';
const fmt = (v, d = 2) => v.toLocaleString('ko-KR', {maximumFractionDigits: d});
"""

TOOLS = [
    {
        "slug": "electricity-cost",
        "title": "가전제품 전기요금 계산기",
        "summary": "소비전력과 사용시간으로 한 달 전기요금 계산",
        "description": "가전제품의 소비전력(W)과 하루 사용시간을 입력하면 한 달 전력량(kWh)과 예상 전기요금을 바로 계산합니다.",
        "form": """
<label for="w">소비전력 (W)</label><input id="w" inputmode="decimal" value="1800">
<div class="row">
  <div><label for="h">하루 사용시간 (시간)</label><input id="h" inputmode="decimal" value="4"></div>
  <div><label for="d">한 달 사용일수</label><input id="d" inputmode="decimal" value="30"></div>
</div>
<label for="p">kWh당 단가 (원)</label><input id="p" inputmode="decimal" value="200">
<div class="result" id="out"></div>
""",
        "script": """
function calc() {
  const kwh = num('w') * num('h') * num('d') / 1000;
  $('out').innerHTML = `<p>한 달 사용량 <b>${fmt(kwh, 1)} kWh</b></p>
    <p>예상 전기요금 <b>${won(kwh * num('p'))}</b></p>
    <p>하루 약 ${won(kwh * num('p') / Math.max(num('d'), 1))}</p>`;
}
""",
        "notes": """
<h2>계산 방법</h2>
<p>전력량(kWh) = 소비전력(W) × 사용시간(h) × 사용일수 ÷ 1,000 이고, 요금은 전력량에 kWh당 단가를 곱해 구합니다.</p>
<p>주택용 전기요금은 사용량이 많을수록 단가가 올라가는 누진제가 적용되고, 기본요금·기후환경요금·부가세 등이 더해집니다.
여기서는 평균 단가 하나로 단순 계산하므로 <strong>실제 고지서와는 차이가 날 수 있습니다.</strong>
정확한 요금은 한국전력 사이버지점의 요금 계산기를 이용하세요.</p>
<h2>주요 가전 소비전력 예시</h2>
<table><tr><th>가전</th><th>대략적 소비전력</th></tr>
<tr><td>에어컨(벽걸이)</td><td>600~1,000W</td></tr>
<tr><td>전기히터·온풍기</td><td>1,000~2,000W</td></tr>
<tr><td>전자레인지</td><td>1,000~1,500W</td></tr>
<tr><td>드럼세탁기(건조 포함)</td><td>1,000~2,000W</td></tr>
<tr><td>TV(55인치)</td><td>100~200W</td></tr>
<tr><td>노트북</td><td>30~90W</td></tr></table>
<p>정확한 값은 제품 뒷면 정격 라벨이나 설명서의 "소비전력"을 확인하세요.</p>
""",
    },
    {
        "slug": "loan-interest",
        "title": "대출 이자 계산기",
        "summary": "원리금균등·원금균등·만기일시 월 상환액 비교",
        "description": "대출금액, 금리, 기간을 입력하면 원리금균등·원금균등·만기일시상환 방식별 월 상환액과 총 이자를 계산합니다.",
        "form": """
<label for="amt">대출금액 (원)</label><input id="amt" inputmode="numeric" value="100,000,000">
<div class="row">
  <div><label for="rate">연 금리 (%)</label><input id="rate" inputmode="decimal" value="4.5"></div>
  <div><label for="months">기간 (개월)</label><input id="months" inputmode="numeric" value="360"></div>
</div>
<label for="type">상환 방식</label>
<select id="type">
  <option value="annuity">원리금균등상환</option>
  <option value="principal">원금균등상환</option>
  <option value="bullet">만기일시상환</option>
</select>
<div class="result" id="out"></div>
""",
        "script": """
function schedule(P, r, n, type) {
  const rows = [];
  let bal = P;
  const annuity = r === 0 ? P / n : P * r * Math.pow(1 + r, n) / (Math.pow(1 + r, n) - 1);
  for (let k = 1; k <= n; k++) {
    const interest = bal * r;
    let principal;
    if (type === 'annuity') principal = annuity - interest;
    else if (type === 'principal') principal = P / n;
    else principal = k === n ? bal : 0;
    bal -= principal;
    rows.push([k, principal + interest, principal, interest, Math.max(bal, 0)]);
  }
  return rows;
}
function calc() {
  const P = num('amt'), n = Math.max(Math.round(num('months')), 1), r = num('rate') / 100 / 12;
  const rows = schedule(P, r, n, $('type').value);
  const totalInterest = rows.reduce((s, x) => s + x[3], 0);
  const first = rows[0][1], last = rows[rows.length - 1][1];
  const monthly = Math.abs(first - last) < 1 ? `<b>${won(first)}</b>`
    : `첫 달 <b>${won(first)}</b> → 마지막 달 ${won(last)}`;
  const table = rows.map(x => `<tr><td>${x[0]}</td><td>${won(x[1])}</td><td>${won(x[2])}</td><td>${won(x[3])}</td><td>${won(x[4])}</td></tr>`).join('');
  $('out').innerHTML = `<p>월 상환액 ${monthly}</p>
    <p>총 이자 <b>${won(totalInterest)}</b></p>
    <p>총 상환액 ${won(P + totalInterest)}</p>
    <details><summary>월별 상환 스케줄 보기</summary>
    <table><tr><th>회차</th><th>상환액</th><th>원금</th><th>이자</th><th>잔액</th></tr>${table}</table></details>`;
}
""",
        "notes": """
<h2>상환 방식 차이</h2>
<ul>
<li><strong>원리금균등상환</strong>: 매달 같은 금액을 갚습니다. 초반엔 이자 비중이 크고 갈수록 원금 비중이 커집니다.</li>
<li><strong>원금균등상환</strong>: 매달 같은 원금에 남은 잔액의 이자를 더해 갚습니다. 초반 부담이 크지만 총 이자는 가장 적습니다.</li>
<li><strong>만기일시상환</strong>: 매달 이자만 내고 원금은 만기에 한꺼번에 갚습니다. 총 이자가 가장 많습니다.</li>
</ul>
<p>이 계산기는 고정금리를 가정한 참고용입니다. 변동금리, 거치기간, 중도상환수수료 등은 반영하지 않으니 실제 조건은 금융기관에 확인하세요.</p>
""",
    },
    {
        "slug": "savings-interest",
        "title": "예금·적금 이자 계산기",
        "summary": "단리·월복리, 세후 실수령액까지 계산",
        "description": "예금·적금의 원금, 금리, 기간을 입력하면 단리·월복리 기준 이자와 이자소득세를 뺀 세후 수령액을 계산합니다.",
        "form": """
<label for="kind">상품 종류</label>
<select id="kind"><option value="saving">적금 (매달 납입)</option><option value="deposit">예금 (한 번에 예치)</option></select>
<label for="amt" id="amtLabel">월 납입액 (원)</label><input id="amt" inputmode="numeric" value="500,000">
<div class="row">
  <div><label for="rate">연 금리 (%)</label><input id="rate" inputmode="decimal" value="3.5"></div>
  <div><label for="months">기간 (개월)</label><input id="months" inputmode="numeric" value="12"></div>
</div>
<div class="row">
  <div><label for="comp">이자 방식</label>
    <select id="comp"><option value="simple">단리</option><option value="monthly">월복리</option></select></div>
  <div><label for="tax">과세</label>
    <select id="tax"><option value="0.154">일반과세 15.4%</option><option value="0.095">세금우대 9.5%</option><option value="0">비과세</option></select></div>
</div>
<div class="result" id="out"></div>
""",
        "script": """
function calc() {
  const saving = $('kind').value === 'saving';
  $('amtLabel').textContent = saving ? '월 납입액 (원)' : '예치금액 (원)';
  const A = num('amt'), m = Math.max(Math.round(num('months')), 1), i = num('rate') / 100 / 12;
  const simple = $('comp').value === 'simple';
  let principal, interest;
  if (saving) {
    principal = A * m;
    interest = simple ? A * i * m * (m + 1) / 2
      : (i === 0 ? 0 : A * ((1 + i) * (Math.pow(1 + i, m) - 1) / i - m));
  } else {
    principal = A;
    interest = simple ? A * i * m : A * (Math.pow(1 + i, m) - 1);
  }
  const tax = Math.floor(interest * parseFloat($('tax').value) / 10) * 10;
  $('out').innerHTML = `<p>원금 합계 ${won(principal)}</p>
    <p>세전 이자 ${won(interest)}</p>
    <p>이자소득세 ${won(tax)}</p>
    <p>세후 수령액 <b>${won(principal + interest - tax)}</b></p>`;
}
""",
        "notes": """
<h2>알아두면 좋은 점</h2>
<ul>
<li>적금의 "연 3.5%"는 첫 달 납입금에만 1년 치 이자가 붙고, 마지막 달 납입금에는 한 달 치 이자만 붙습니다.
그래서 적금 이자는 같은 금리의 예금보다 훨씬 적게 느껴집니다.</li>
<li>이자소득세는 일반적으로 15.4%(소득세 14% + 지방소득세 1.4%)가 원천징수됩니다.</li>
<li>은행마다 이자 계산·절사 방식이 조금씩 달라 실제 금액과 몇 원~몇십 원 차이가 날 수 있습니다.</li>
</ul>
""",
    },
    {
        "slug": "pyeong-converter",
        "title": "평수 ㎡ 변환 계산기",
        "summary": "평 ↔ 제곱미터(㎡) 즉시 변환",
        "description": "평을 제곱미터(㎡)로, 제곱미터를 평으로 바로 변환합니다. 1평은 약 3.3058㎡입니다.",
        "form": """
<div class="row">
  <div><label for="py">평</label><input id="py" inputmode="decimal" value="25"></div>
  <div><label for="m2">제곱미터 (㎡)</label><input id="m2" inputmode="decimal"></div>
</div>
<div class="result" id="out"></div>
""",
        "script": """
const PY = 400 / 121;  // 1평 = 400/121 ㎡ ≈ 3.3058
let last = 'py';
function calc(e) {
  if (e && e.target) last = e.target.id === 'm2' ? 'm2' : 'py';
  if (last === 'py') $('m2').value = fmt(num('py') * PY);
  else $('py').value = fmt(num('m2') / PY);
  $('out').innerHTML = `<p><b>${$('py').value}평</b> = <b>${$('m2').value}㎡</b></p>`;
}
""",
        "notes": """
<h2>자주 찾는 평수</h2>
<table><tr><th>평</th><th>㎡</th><th>참고</th></tr>
<tr><td>18평</td><td>약 59.5㎡</td><td>전용 59㎡ 아파트</td></tr>
<tr><td>25평</td><td>약 82.6㎡</td><td>전용 84㎡(흔히 "34평형")</td></tr>
<tr><td>32평</td><td>약 105.8㎡</td><td></td></tr></table>
<p>아파트 "34평형"은 보통 공용면적을 포함한 공급면적 기준이라, 전용면적(약 84㎡ ≈ 25.4평)과 다릅니다.</p>
""",
    },
    {
        "slug": "exchange-rate",
        "title": "환율 계산기",
        "summary": "최신 환율로 원화 ↔ 달러·엔·유로 등 변환",
        "description": "최신 환율을 자동으로 불러와 원화와 달러·엔·유로·위안 등 주요 외화를 바로 변환합니다. 1,000원·10,000원 단위 변환표도 함께 보여 줍니다.",
        "form": """
<div class="row">
  <div><label for="cur">통화</label><select id="cur"></select></div>
  <div><label for="dir">변환 방향</label><select id="dir">
    <option value="k2f">원화 → 외화</option><option value="f2k">외화 → 원화</option></select></div>
</div>
<label for="amt" id="amtlab">금액 (원)</label><input id="amt" inputmode="decimal" value="10,000">
<label for="rate" id="ratelab">적용 환율 (원)</label><input id="rate" inputmode="decimal">
<p id="src" style="font-size:13px;color:var(--muted);margin:6px 0 0">환율을 불러오는 중입니다…</p>
<div class="result" id="out"></div>
<div id="tbl"></div>
""",
        "script": """
// [이름, 표시 단위(엔·동·루피아는 100 단위로 고시), 소수 자릿수]
const CUR = {
  USD: ['미국 달러', 1, 2], JPY: ['일본 엔', 100, 0], EUR: ['유로', 1, 2], CNY: ['중국 위안', 1, 2],
  GBP: ['영국 파운드', 1, 2], HKD: ['홍콩 달러', 1, 2], TWD: ['대만 달러', 1, 0], VND: ['베트남 동', 100, 0],
  THB: ['태국 바트', 1, 2], PHP: ['필리핀 페소', 1, 2], SGD: ['싱가포르 달러', 1, 2], AUD: ['호주 달러', 1, 2],
  CAD: ['캐나다 달러', 1, 2], CHF: ['스위스 프랑', 1, 2], MYR: ['말레이시아 링깃', 1, 2], IDR: ['인도네시아 루피아', 100, 0],
};
$('cur').innerHTML = Object.entries(CUR).map(([c, [n]]) => `<option value="${c}">${n} (${c})</option>`).join('');
let rates = null;  // 1원당 외화 금액

const unitName = c => (CUR[c][1] === 100 ? '100' : '1') + ' ' + c;
function setRate() {
  const c = $('cur').value;
  $('ratelab').textContent = `적용 환율 (${unitName(c)}당 원)`;
  if (rates && rates[c]) $('rate').value = fmt(CUR[c][1] / rates[c], 2);
}

async function loadRates() {
  const sources = [
    ['https://open.er-api.com/v6/latest/KRW', d => [d.rates, d.time_last_update_utc,
      '<a href="https://www.exchangerate-api.com" target="_blank" rel="nofollow noopener">Rates By Exchange Rate API</a>']],
    ['https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/krw.json', d => [
      Object.fromEntries(Object.entries(d.krw).map(([k, v]) => [k.toUpperCase(), v])), d.date, 'fawazahmed0/currency-api']],
  ];
  for (const [url, parse] of sources) {
    try {
      const res = await fetch(url);
      if (!res.ok) continue;
      const [r, when, credit] = parse(await res.json());
      if (!r || !r.USD) continue;
      rates = r;
      const d = new Date(when);
      const date = isNaN(d) ? when : d.toLocaleString('ko-KR', {dateStyle: 'medium', timeStyle: 'short'});
      $('src').innerHTML = `기준: ${date} 고시 환율 · ${credit}`;
      setRate(); calc();
      return;
    } catch (e) { /* 다음 소스로 */ }
  }
  $('src').textContent = '환율을 불러오지 못했습니다. 적용 환율을 직접 입력하세요.';
}

function calc(e) {
  if (e && e.target && e.target.id === 'cur') setRate();
  const c = $('cur').value, [name, unit, dp] = CUR[c];
  const toWon = $('dir').value === 'f2k';
  $('amtlab').textContent = toWon ? `금액 (${c})` : '금액 (원)';
  const perOne = num('rate') / unit;  // 외화 1단위당 원
  if (!perOne) {
    $('out').innerHTML = '<p>환율을 불러오는 중입니다…</p>';
    $('tbl').innerHTML = '';
    return;
  }
  const f = v => fmt(v, dp) + ' ' + c;
  const a = num('amt');
  $('out').innerHTML = toWon
    ? `<p>${f(a)} = <b>${won(a * perOne)}</b></p>`
    : `<p>${won(a)} = <b>${f(a / perOne)}</b></p>`;
  const kr = [1000, 5000, 10000, 50000, 100000, 1000000];
  const fx = unit === 100 ? [100, 1000, 5000, 10000, 50000, 100000] : [1, 10, 50, 100, 500, 1000];
  const rows = kr.map((k, i) => `<tr><td>${won(k)}</td><td>${f(k / perOne)}</td>` +
    `<td>${f(fx[i])}</td><td>${won(fx[i] * perOne)}</td></tr>`).join('');
  $('tbl').innerHTML = `<h3 style="margin:20px 0 8px">${name} 기본 변환표</h3>
    <table><tr><th>원화</th><th>${c}</th><th>${c}</th><th>원화</th></tr>${rows}</table>`;
}
loadRates();
""",
        "notes": """
<h2>이 계산기의 환율은</h2>
<p>무료 환율 API가 하루 한 번 이상 갱신하는 <strong>기준 환율(중간값)</strong>을 사용합니다.
실시간 외환시장 시세나 은행이 고시하는 매매기준율과는 조금 차이가 날 수 있습니다.
은행 앱에서 본 환율로 계산하고 싶다면 <strong>적용 환율</strong> 칸에 직접 입력하세요.</p>
<h2>실제로 환전할 때는 수수료가 붙습니다</h2>
<ul>
<li><strong>현찰 살 때·팔 때</strong>: 은행은 기준 환율에 보통 1~2% 안팎의 수수료(스프레드)를 더하거나 뺍니다. 통화와 은행에 따라 다릅니다.</li>
<li><strong>환전 우대</strong>: 은행 앱·모바일 환전을 쓰면 이 수수료를 50~90%까지 깎아 주는 경우가 많습니다.</li>
<li><strong>해외 카드 결제</strong>: 결제 금액에 국제 브랜드 수수료와 카드사 해외 이용 수수료가 더해질 수 있습니다.</li>
</ul>
<p>일본 엔, 베트남 동, 인도네시아 루피아는 국내 은행 고시 방식에 맞춰 <strong>100단위</strong> 기준 환율로 보여 줍니다.</p>
""",
    },
]


def render_tool_body(tool: dict) -> str:
    return f"""
<article>
<h1>{tool['title']}</h1>
<p class="meta">{tool['description']}</p>
<div class="tool">{tool['form']}</div>
{tool['notes']}
</article>
<script>
{_JS_HELPERS}
{tool['script']}
document.querySelectorAll('.tool input, .tool select').forEach(el => el.addEventListener('input', calc));
calc();
</script>
"""


def tool_list_html(base: str) -> str:
    items = "".join(
        f'<a href="{base}/tools/{t["slug"]}/"><b>{t["title"]}</b><span>{t["summary"]}</span></a>'
        for t in TOOLS
    )
    return f'<div class="tool-list">{items}</div>'
