"""Interactive calculator pages. Each tool is plain HTML + inline JS rendered inside the site layout.

Only calculators whose math doesn't depend on frequently changing regulations are included,
so results stay correct without maintenance.
"""

TOOL_CSS = """
.tool{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:20px;margin:24px 0}
.tool label{display:block;font-size:15px;font-weight:600;margin:14px 0 6px}
.tool input,.tool select,.tool textarea{width:100%;font:inherit;padding:10px 12px;border:1px solid var(--line);
  border-radius:8px;background:var(--bg);color:var(--fg)}
.tool textarea{min-height:96px;resize:vertical;line-height:1.5}
.tool .hit{margin-top:14px;padding:14px 16px;border-radius:10px;background:var(--bg);border:1px solid var(--line)}
.tool .hit .raw{font-size:13px;color:var(--muted);word-break:break-all}
.tool .hit .name{font-size:18px;font-weight:700;margin:4px 0 2px}
.tool .hit .cat{display:inline-block;font-size:12px;padding:2px 8px;border-radius:999px;background:var(--surface);
  border:1px solid var(--line);color:var(--muted);margin-left:6px;vertical-align:middle}
.tool .hit .desc{margin:6px 0 10px;font-size:15px}
.tool .btns{display:flex;flex-wrap:wrap;gap:8px}
.tool .btns a{font-size:14px;padding:7px 12px;border-radius:8px;border:1px solid var(--line);background:var(--surface);
  color:var(--fg);text-decoration:none}
.tool .btns a:hover{border-color:var(--accent);color:var(--accent)}
.tool .btns a.pri{background:var(--accent);border-color:var(--accent);color:#fff}
.dict-filter{width:100%;font:inherit;padding:8px 12px;border:1px solid var(--line);border-radius:8px;
  background:var(--bg);color:var(--fg);margin:8px 0 12px}
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
    {
        "slug": "card-statement-lookup",
        "title": "카드 내역 가맹점명 검색기",
        "summary": "모르는 카드 결제 내역, 어느 회사인지 바로 확인",
        "description": "카드 명세서의 낯선 가맹점명(법인명·결제대행사·영문 표기)을 붙여 넣으면 어떤 서비스의 결제인지 알려 주고, 네이버·구글·지도 검색 링크를 바로 만들어 줍니다.",
        "form": """
<label for="q">카드 내역을 붙여 넣으세요 (여러 줄 가능)</label>
<textarea id="q" placeholder="예) (주)우아한형제들 23,500원&#10;KCP_엔에이치엔케이씨피&#10;GOOGLE *YouTubePremium&#10;APPLE.COM/BILL">(주)우아한형제들 23,500원
APPLE.COM/BILL 14,900원
에스씨케이컴퍼니 강남역점</textarea>
<p style="font-size:13px;color:var(--muted);margin:6px 0 0">입력한 내용은 이 브라우저 안에서만 처리되고 서버로 보내지 않습니다.</p>
<div id="out"></div>
""",
        "script": r"""
// [찾을 문자열(소문자·공백 제거 기준), 표시 이름, 분류, 설명]. 위에서부터 먼저 맞는 항목이 적용됩니다.
const DICT = [
  // 결제대행(PG)·간편결제: 실제 가맹점은 뒤에 붙은 이름입니다.
  ['nhn케이씨피|엔에이치엔케이씨피|nhnkcp|kcp_|kcp*', 'NHN KCP (결제대행)', '결제대행', '온라인 쇼핑몰·앱이 쓰는 결제대행사입니다. 뒤에 붙은 이름이 실제로 결제한 곳이고, 없으면 결제한 날짜의 주문 내역(쇼핑몰·앱)을 확인하세요.'],
  ['케이지이니시스|kg이니시스|inicis|이니시스', 'KG이니시스 (결제대행)', '결제대행', '온라인 결제대행사입니다. 실제 가맹점은 뒤에 붙은 이름이며, 이니시스 고객센터(1588-4954)에서 결제 내역 조회가 됩니다.'],
  ['토스페이먼츠|tosspayments', '토스페이먼츠 (결제대행)', '결제대행', '온라인 결제대행사입니다. 토스 앱의 결제 내역이 아니라 토스페이먼츠를 쓰는 다른 쇼핑몰·앱의 결제일 수 있습니다.'],
  ['나이스페이|nicepay|나이스페이먼츠', '나이스페이먼츠 (결제대행)', '결제대행', '온라인·오프라인 결제대행사입니다. 실제 가맹점은 뒤에 붙은 이름을 확인하세요.'],
  ['다날|danal', '다날 (결제대행·휴대폰결제)', '결제대행', '휴대폰 소액결제와 온라인 결제대행을 하는 회사입니다. 게임·웹툰·콘텐츠 결제가 이 이름으로 찍히는 경우가 많습니다.'],
  ['kg모빌리언스|모빌리언스|mobilians', 'KG모빌리언스 (휴대폰결제)', '결제대행', '휴대폰 소액결제·온라인 결제대행사입니다. 콘텐츠·게임 결제가 많습니다.'],
  ['페이레터|payletter', '페이레터 (결제대행)', '결제대행', '게임·콘텐츠 쪽 결제대행사입니다.'],
  ['헥토파이낸셜|세틀뱅크|settlebank', '헥토파이낸셜(구 세틀뱅크, 결제대행)', '결제대행', '간편 계좌결제·결제대행사입니다. 실제 가맹점은 뒤에 붙은 이름을 확인하세요.'],
  ['갤럭시아머니트리|갤럭시아', '갤럭시아머니트리 (결제대행)', '결제대행', '온라인 결제대행·휴대폰결제 회사입니다.'],
  ['네이버파이낸셜|네이버페이|naverpay|npay', '네이버페이', '간편결제', '네이버페이로 결제한 건입니다. 네이버페이 앱·페이지의 결제 내역에서 실제 가맹점을 확인할 수 있습니다.'],
  ['카카오페이|kakaopay', '카카오페이', '간편결제', '카카오페이로 결제한 건입니다. 카카오톡 > 더보기 > 페이 > 결제 내역에서 실제 가맹점이 나옵니다.'],
  ['비바리퍼블리카|토스페이|tosspay', '토스 (비바리퍼블리카)', '간편결제', '토스 운영사 이름입니다. 토스페이 결제나 토스 서비스 이용료일 수 있으니 토스 앱 내역을 확인하세요.'],
  ['엔에이치엔페이코|페이코|payco', '페이코 (PAYCO)', '간편결제', '페이코 간편결제입니다. 페이코 앱 결제 내역에서 실제 가맹점을 확인하세요.'],
  ['스마일페이|smilepay', '스마일페이', '간편결제', 'G마켓·옥션·SSG 등에서 쓰는 간편결제입니다. 해당 쇼핑몰 주문 내역을 확인하세요.'],
  ['쿠팡페이|coupangpay', '쿠팡페이', '간편결제', '쿠팡 결제입니다. 쿠팡 앱 > 주문목록, 또는 쿠팡이츠·쿠팡플레이·와우멤버십 결제일 수 있습니다.'],
  ['paypal', '페이팔 (PayPal)', '해외결제', '"PAYPAL *가맹점" 형태로 찍힙니다. 별표 뒤 이름이 실제 가맹점이고, 페이팔 계정의 거래 내역에서 자세히 볼 수 있습니다.'],
  // 구독·디지털
  ['apple.com/bill|applecom|애플|apple', '애플 (App Store·iCloud·구독)', '구독', '앱 유료 결제, 앱 내 구독, iCloud+ 저장공간, 애플뮤직·TV+ 등입니다. 아이폰 설정 > 맨 위 이름 > 구독 / 미디어 및 구입에서 어떤 결제인지 확인할 수 있습니다.'],
  ['youtube|유튜브', '유튜브 프리미엄·멤버십', '구독', '유튜브 프리미엄, 채널 멤버십, 슈퍼챗 결제입니다. 유튜브 앱 > 프로필 > 구매 항목 및 멤버십에서 확인·해지합니다.'],
  ['google*|google|구글', '구글 (Google Play·구독)', '구독', '"GOOGLE *앱이름" 형태입니다. 구글플레이 앱 결제·구독, 구글원(저장공간), 유튜브 등입니다. play.google.com > 결제 및 정기결제에서 확인하세요.'],
  ['netflix|넷플릭스', '넷플릭스', '구독', '넷플릭스 월 구독료입니다. 계정 > 멤버십 관리에서 요금제·해지를 확인합니다.'],
  ['disney|디즈니', '디즈니+', '구독', '디즈니플러스 구독료입니다.'],
  ['콘텐츠웨이브|웨이브|wavve', '웨이브 (wavve)', '구독', 'OTT 웨이브 구독료입니다. 운영사 이름은 콘텐츠웨이브입니다.'],
  ['티빙|tving', '티빙', '구독', 'OTT 티빙 구독료입니다.'],
  ['왓챠|watcha', '왓챠', '구독', '왓챠 OTT·왓챠피디아 구독료입니다.'],
  ['카카오엔터테인먼트|카카오엔터|멜론|melon', '멜론 (카카오엔터테인먼트)', '구독', '멜론 음악 이용권일 가능성이 큽니다. 카카오페이지·카카오웹툰 결제도 같은 회사 이름으로 찍힐 수 있습니다.'],
  ['지니뮤직|genie', '지니뮤직', '구독', '지니 음악 이용권입니다.'],
  ['드림어스|flo|플로', '플로 (FLO, 드림어스컴퍼니)', '구독', '음악 서비스 FLO 이용권입니다.'],
  ['spotify|스포티파이', '스포티파이', '구독', '스포티파이 프리미엄 구독료입니다.'],
  ['밀리의서재', '밀리의서재', '구독', '전자책 구독 서비스입니다.'],
  ['리디|ridi', '리디 (RIDI)', '구독', '리디북스 전자책 구매 또는 리디셀렉트 구독입니다.'],
  ['openai|chatgpt|오픈에이아이', 'OpenAI (ChatGPT)', '구독', 'ChatGPT Plus 등 OpenAI 구독·API 요금입니다.'],
  ['anthropic|claude', 'Anthropic (Claude)', '구독', 'Claude 구독 또는 API 사용 요금입니다.'],
  ['adobe|어도비', '어도비 (Adobe)', '구독', '포토샵·라이트룸·아크로뱃 등 Creative Cloud 구독료입니다. account.adobe.com에서 플랜을 확인하세요.'],
  ['microsoft|msft|마이크로소프트', '마이크로소프트', '구독', 'Microsoft 365, OneDrive, Xbox Game Pass, Copilot 등입니다. account.microsoft.com > 서비스 및 구독에서 확인하세요.'],
  ['notion', '노션 (Notion)', '구독', '노션 유료 플랜입니다.'],
  ['canva', '캔바 (Canva)', '구독', '캔바 프로 구독료입니다.'],
  ['dropbox', '드롭박스', '구독', '드롭박스 저장공간 구독료입니다.'],
  ['github', '깃허브 (GitHub)', '구독', 'GitHub 유료 플랜·Copilot 요금입니다.'],
  ['amazon web|aws', 'AWS (아마존 웹 서비스)', '구독', '클라우드 서버 사용 요금입니다. 프리티어가 끝나면 자동 과금되니 AWS 콘솔 결제 대시보드를 확인하세요.'],
  ['amzn|amazon|아마존', '아마존 (Amazon)', '해외결제', '아마존 직구(AMZN Mktp)나 아마존 프라임·킨들 구독입니다. 아마존 계정 주문 내역을 확인하세요.'],
  ['aliexpress|알리익스프레스|알리', '알리익스프레스', '해외결제', '알리익스프레스 주문입니다. 앱 > 내 주문에서 확인하세요.'],
  ['temu|테무', '테무 (Temu)', '해외결제', '테무 주문입니다.'],
  ['shein|쉬인', '쉬인 (SHEIN)', '해외결제', '쉬인 의류 주문입니다.'],
  ['ebay|이베이', '이베이', '해외결제', '이베이 구매입니다.'],
  ['steam|valve', '스팀 (Steam)', '게임', 'Steam 게임 구매입니다. 계정 > 구매 내역에서 확인하세요.'],
  ['nintendo|닌텐도', '닌텐도', '게임', '닌텐도 e숍 구매·온라인 멤버십입니다.'],
  ['playstation|sony|플레이스테이션|소니', '플레이스테이션 (소니)', '게임', 'PS 스토어 구매 또는 PS Plus 구독입니다.'],
  ['blizzard|블리자드', '블리자드', '게임', '블리자드 게임·배틀넷 결제입니다.'],
  ['riot|라이엇', '라이엇 게임즈', '게임', '리그 오브 레전드·발로란트 RP/VP 결제입니다.'],
  ['epic games|epicgames|에픽게임즈', '에픽게임즈', '게임', '포트나이트·에픽 스토어 결제입니다.'],
  ['넥슨|nexon', '넥슨', '게임', '넥슨 게임 캐시 충전입니다.'],
  ['엔씨소프트|ncsoft', '엔씨소프트', '게임', '엔씨 게임 결제입니다.'],
  ['카카오게임즈', '카카오게임즈', '게임', '카카오게임즈 게임 결제입니다.'],
  ['넷마블', '넷마블', '게임', '넷마블 게임 결제입니다.'],
  // 배달·쇼핑
  ['우아한형제들|배달의민족|배민', '배달의민족 (우아한형제들)', '배달·쇼핑', '배달의민족 주문입니다. 배민클럽 멤버십 결제일 수도 있습니다.'],
  ['위대한상상|요기요', '요기요 (위대한상상)', '배달·쇼핑', '요기요 주문입니다.'],
  ['쿠팡이츠', '쿠팡이츠', '배달·쇼핑', '쿠팡이츠 배달 주문입니다.'],
  ['쿠팡|coupang', '쿠팡', '배달·쇼핑', '쿠팡 주문 또는 와우멤버십 월회비입니다. 쿠팡 앱 > 마이쿠팡 > 주문목록을 확인하세요.'],
  ['컬리|kurly', '컬리 (마켓컬리)', '배달·쇼핑', '마켓컬리·뷰티컬리 주문입니다.'],
  ['에스에스지닷컴|ssg.com|ssg닷컴|쓱', 'SSG.COM', '배달·쇼핑', 'SSG닷컴·이마트몰 주문입니다.'],
  ['지마켓|gmarket|옥션|auction', 'G마켓·옥션', '배달·쇼핑', 'G마켓 또는 옥션 주문입니다. 두 곳은 같은 회사(지마켓)입니다.'],
  ['11번가|십일번가', '11번가', '배달·쇼핑', '11번가 주문입니다.'],
  ['네이버|naver', '네이버', '배달·쇼핑', '네이버 쇼핑·멤버십·클라우드 등 네이버 서비스 결제입니다. 네이버페이 결제 내역을 확인하세요.'],
  ['당근마켓|당근', '당근', '배달·쇼핑', '당근 광고비 또는 당근페이 결제입니다.'],
  ['번개장터', '번개장터', '배달·쇼핑', '번개장터 안전결제(번개페이)입니다.'],
  ['kream', '크림 (KREAM)', '배달·쇼핑', '리셀 플랫폼 크림 구매·수수료입니다.'],
  ['무신사|musinsa', '무신사', '배달·쇼핑', '무신사·29CM·솔드아웃 주문입니다.'],
  ['에이블리', '에이블리', '배달·쇼핑', '에이블리 쇼핑 주문입니다.'],
  ['카카오스타일|지그재그', '지그재그 (카카오스타일)', '배달·쇼핑', '지그재그 쇼핑 주문입니다.'],
  ['버킷플레이스|오늘의집', '오늘의집 (버킷플레이스)', '배달·쇼핑', '오늘의집 주문입니다.'],
  ['백패커|아이디어스', '아이디어스 (백패커)', '배달·쇼핑', '핸드메이드 마켓 아이디어스 주문입니다.'],
  ['더블유컨셉|w컨셉|wconcept', 'W컨셉', '배달·쇼핑', 'W컨셉 패션 주문입니다.'],
  // 편의점·마트·프랜차이즈 (법인명이 브랜드와 다른 곳)
  ['지에스리테일|gs리테일|gs25|지에스25', 'GS25·GS더프레시 (GS리테일)', '매장', 'GS25 편의점 또는 GS더프레시 슈퍼마켓 결제입니다.'],
  ['비지에프리테일|bgf리테일|cu편의점|씨유', 'CU (BGF리테일)', '매장', 'CU 편의점 결제입니다.'],
  ['코리아세븐|세븐일레븐|7-eleven|7eleven', '세븐일레븐 (코리아세븐)', '매장', '세븐일레븐 편의점 결제입니다.'],
  ['이마트24|emart24', '이마트24', '매장', '이마트24 편의점 결제입니다.'],
  ['이마트|emart', '이마트·트레이더스', '매장', '이마트, 트레이더스, 노브랜드 매장 결제입니다.'],
  ['홈플러스', '홈플러스', '매장', '홈플러스·홈플러스 익스프레스 결제입니다.'],
  ['롯데쇼핑', '롯데마트·롯데백화점 (롯데쇼핑)', '매장', '롯데마트, 롯데백화점, 롯데슈퍼, 롯데온이 모두 롯데쇼핑 이름으로 찍힐 수 있습니다.'],
  ['코스트코|costco', '코스트코', '매장', '코스트코 매장·온라인 결제 또는 연회비입니다.'],
  ['아성다이소|다이소', '다이소 (아성다이소)', '매장', '다이소 매장·다이소몰 결제입니다.'],
  ['씨제이올리브영|올리브영|oliveyoung', '올리브영 (CJ올리브영)', '매장', '올리브영 매장·온라인 결제입니다.'],
  ['에프알엘코리아|유니클로|uniqlo', '유니클로 (에프알엘코리아)', '매장', '유니클로 결제입니다.'],
  ['자라리테일|zara', '자라 (ZARA)', '매장', '자라 매장·온라인 결제입니다.'],
  ['에이치앤엠|h&m|hennes', 'H&M', '매장', 'H&M 결제입니다.'],
  ['무지코리아|무인양품|muji', '무인양품 (무지코리아)', '매장', '무인양품 결제입니다.'],
  ['이케아|ikea', '이케아', '매장', '이케아 매장·온라인 결제입니다.'],
  ['에스씨케이컴퍼니|스타벅스|starbucks', '스타벅스 (SCK컴퍼니)', '카페·식당', '스타벅스 매장 결제 또는 앱 카드 충전입니다. 운영사 이름이 에스씨케이컴퍼니입니다.'],
  ['투썸플레이스', '투썸플레이스', '카페·식당', '투썸플레이스 결제입니다.'],
  ['이디야', '이디야커피', '카페·식당', '이디야 매장 결제입니다.'],
  ['앤하우스|메가엠지씨|메가커피', '메가MGC커피 (앤하우스)', '카페·식당', '메가커피 결제입니다. 운영사 이름이 앤하우스입니다.'],
  ['컴포즈', '컴포즈커피', '카페·식당', '컴포즈커피 결제입니다.'],
  ['할리스', '할리스', '카페·식당', '할리스커피 결제입니다.'],
  ['더본코리아|빽다방', '더본코리아 (빽다방·홍콩반점 등)', '카페·식당', '빽다방, 홍콩반점, 한신포차, 역전우동 등 더본코리아 직영 매장 결제입니다.'],
  ['한국맥도날드|맥도날드|mcdonald', '맥도날드', '카페·식당', '맥도날드 결제입니다.'],
  ['비케이알|버거킹|burgerking', '버거킹 (비케이알)', '카페·식당', '버거킹 결제입니다. 운영사 이름이 비케이알입니다.'],
  ['롯데지알에스|롯데리아|엔제리너스', '롯데리아·엔제리너스 (롯데GRS)', '카페·식당', '롯데리아, 엔제리너스, 크리스피크림 결제입니다.'],
  ['파리크라상|파리바게뜨|파리바게트', '파리바게뜨 (파리크라상)', '카페·식당', '파리바게뜨·파스쿠찌 결제입니다.'],
  ['비알코리아|배스킨|던킨', '배스킨라빈스·던킨 (비알코리아)', '카페·식당', '배스킨라빈스 또는 던킨 결제입니다.'],
  ['씨제이푸드빌|뚜레쥬르|빕스', '뚜레쥬르·빕스 (CJ푸드빌)', '카페·식당', '뚜레쥬르, 빕스, 더플레이스 결제입니다.'],
  ['교촌에프앤비|교촌', '교촌치킨 (교촌에프앤비)', '카페·식당', '교촌치킨 결제입니다.'],
  ['제너시스비비큐|비비큐|bbq', 'BBQ (제너시스BBQ)', '카페·식당', 'BBQ치킨 결제입니다.'],
  ['비에이치씨|bhc', 'bhc치킨', '카페·식당', 'bhc 결제입니다.'],
  ['청오디피케이|도미노', '도미노피자 (청오DPK)', '카페·식당', '도미노피자 결제입니다.'],
  ['한국피자헛|피자헛', '피자헛', '카페·식당', '피자헛 결제입니다.'],
  // 교통·이동
  ['한국도로공사|하이패스|통행료', '고속도로 통행료 (하이패스)', '교통', '하이패스 후불 통행료입니다. 한국도로공사 하이패스 사이트에서 통행 내역을 조회할 수 있습니다.'],
  ['티머니|tmoney', '티머니', '교통', '티머니 교통카드 충전·후불 교통요금입니다.'],
  ['로카모빌리티|캐시비|이즐', '이즐(캐시비, 로카모빌리티)', '교통', '캐시비 교통카드 충전·후불 요금입니다.'],
  ['코레일|korail|레츠코레일', '코레일 (KTX·기차표)', '교통', '기차표 결제입니다. 코레일톡 앱에서 예매 내역을 확인하세요.'],
  ['에스알|srt', 'SRT (에스알)', '교통', 'SRT 승차권 결제입니다.'],
  ['카카오모빌리티|카카오t|카카오택시', '카카오T (카카오모빌리티)', '교통', '카카오택시, 대리, 주차, 바이크 등 카카오T 결제입니다.'],
  ['티맵모빌리티|티맵', '티맵 (티맵모빌리티)', '교통', '티맵 주차·대리·택시 결제입니다.'],
  ['쏘카|socar', '쏘카', '교통', '쏘카 카셰어링 이용료입니다.'],
  ['그린카', '그린카', '교통', '그린카 카셰어링 이용료입니다.'],
  ['우버|uber', '우버 (Uber)', '교통', '우버 택시·우버이츠 결제입니다.'],
  ['파킹클라우드|아이파킹', '아이파킹 (파킹클라우드)', '교통', '아이파킹 주차장 요금입니다.'],
  ['모두컴퍼니|모두의주차장', '모두의주차장', '교통', '모두의주차장 주차 요금입니다.'],
  ['에스케이에너지|sk에너지|sk주유', 'SK 주유소', '교통', 'SK에너지 주유소 결제입니다.'],
  ['지에스칼텍스|gs칼텍스', 'GS칼텍스 주유소', '교통', 'GS칼텍스 주유소 결제입니다.'],
  ['에쓰오일|에스오일|s-oil|soil', 'S-OIL 주유소', '교통', 'S-OIL 주유소 결제입니다.'],
  ['현대오일뱅크|오일뱅크', 'HD현대오일뱅크 주유소', '교통', '현대오일뱅크 주유소 결제입니다.'],
  // 여행
  ['야놀자', '야놀자', '여행', '숙박·레저 예약입니다.'],
  ['여기어때', '여기어때', '여행', '숙박 예약입니다.'],
  ['인터파크', '인터파크', '여행', '공연·항공·숙박 예약입니다.'],
  ['agoda|아고다', '아고다', '여행', '아고다 숙박 예약입니다. 해외 결제로 처리돼 수수료가 붙을 수 있습니다.'],
  ['booking.com|부킹닷컴', '부킹닷컴', '여행', '부킹닷컴 숙박 예약입니다.'],
  ['airbnb|에어비앤비', '에어비앤비', '여행', '에어비앤비 숙박 예약입니다.'],
  ['expedia|익스피디아|hotels.com', '익스피디아·호텔스닷컴', '여행', '숙박·항공 예약입니다.'],
  ['trip.com|트립닷컴', '트립닷컴', '여행', '항공·숙박 예약입니다.'],
  ['klook|클룩', '클룩', '여행', '현지 투어·입장권 예약입니다.'],
  // 통신·공과금·공공
  ['에스케이텔레콤|skt|sk텔레콤', 'SK텔레콤', '통신·공과금', '휴대폰 요금 자동납부, 또는 "정보이용료·소액결제"가 붙어 있으면 휴대폰으로 결제한 콘텐츠입니다. T월드 앱 > 소액결제 내역을 확인하세요.'],
  ['케이티앤지|kt&g', 'KT&G', '매장', '담배·전자담배(릴) 관련 결제입니다.'],
  ['케이티|kt', 'KT', '통신·공과금', 'KT 통신 요금 자동납부 또는 휴대폰 소액결제입니다. 마이케이티 앱에서 확인하세요.'],
  ['엘지유플러스|lg유플러스|lgu+|유플러스', 'LG유플러스', '통신·공과금', 'LG유플러스 요금 자동납부 또는 휴대폰 소액결제입니다.'],
  ['한국전력|한전', '한국전력 (전기요금)', '통신·공과금', '전기요금 카드 자동납부입니다.'],
  ['도시가스|삼천리|예스코|코원에너지|경동도시가스|서울가스', '도시가스 요금', '통신·공과금', '도시가스 요금 카드 자동납부입니다.'],
  ['지역난방', '한국지역난방공사', '통신·공과금', '지역난방 요금입니다.'],
  ['국민건강보험|건강보험', '국민건강보험공단', '통신·공과금', '건강보험료·장기요양보험료 납부입니다.'],
  ['국민연금', '국민연금공단', '통신·공과금', '국민연금 보험료 납부입니다.'],
  ['카드로택스|금융결제원', '카드로택스 (국세 카드납부)', '통신·공과금', '국세(종합소득세·부가세 등)를 카드로 낸 건입니다. 납부 대행 수수료가 붙습니다.'],
  ['위택스|wetax|이택스|etax', '위택스·이택스 (지방세)', '통신·공과금', '자동차세·재산세·주민세 등 지방세, 또는 과태료 카드 납부입니다.'],
  ['정부24|행정안전부', '정부24 (민원 수수료)', '통신·공과금', '주민등록등본 등 민원 서류 발급 수수료입니다.'],
  ['인터넷등기소|대법원', '대법원 인터넷등기소', '통신·공과금', '등기부등본 열람·발급 수수료입니다.'],
  ['우정사업본부|우체국', '우체국', '통신·공과금', '우편·택배 요금 또는 우체국 쇼핑입니다.'],
  ['화재해상|해상화재|손해보험|손보|생명보험|생명', '보험료', '통신·공과금', '보험사 이름이면 보험료 자동이체(카드납)입니다. 보험사 앱에서 계약을 확인하세요.'],
  // 카드사 항목
  ['연회비', '카드 연회비', '카드사', '카드 연회비입니다. 1년 안에 해지하면 남은 기간만큼 돌려받을 수 있습니다.'],
  ['해외이용수수료|해외서비스수수료|국제브랜드수수료', '해외 이용 수수료', '카드사', '해외 결제에 붙는 국제브랜드(비자·마스터) 수수료와 카드사 해외서비스 수수료입니다.'],
  ['리볼빙|일부결제금액이월', '리볼빙 수수료', '카드사', '일부결제금액이월약정(리볼빙) 이자입니다. 금리가 높으니 카드 앱에서 약정 해지를 검토하세요.'],
  ['현금서비스|단기카드대출', '현금서비스', '카드사', '단기카드대출(현금서비스) 이용 내역입니다.'],
];
const PG_PREFIX = /^(kcp|kg|이니시스|inicis|nice|나이스|다날|danal|npay|naverpay|네이버페이|카카오페이|kakaopay|토스페이|tosspay|페이코|payco|스마일페이|smilepay|paypal|google|sq|sp)\s*[\*_:\-]\s*/i;
const norm = s => s.toLowerCase().replace(/\s+/g, '');
const clean = s => s
  .replace(/\d{2,4}[.\/-]\d{1,2}([.\/-]\d{1,2})?/g, ' ')      // 날짜
  .replace(/[\d,]+\s*(원|krw|usd|\$)/gi, ' ')               // 금액
  .replace(/\*{2,}\d*|\d{4}-\*{4}/g, ' ')                     // 마스킹된 카드번호
  .replace(/\(주\)|㈜|주식회사|\(유\)|유한회사|유한책임회사|농업회사법인|의료법인|학교법인|재단법인|사단법인/g, ' ')
  .replace(/[()\[\]_|]/g, ' ').replace(/\s+/g, ' ').trim();
const reEsc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
function lookup(raw) {
  const low = raw.toLowerCase(), n = norm(raw);
  const has = k => /^[a-z0-9.&+-]{1,4}$/.test(k)   // 짧은 영문 키는 단어 경계로만
    ? new RegExp('(^|[^a-z0-9])' + reEsc(k) + '($|[^a-z0-9])').test(low)
    : n.includes(norm(k));
  for (const [keys, name, cat, desc] of DICT) {
    if (keys.split('|').some(has)) return {name, cat, desc};
  }
  return null;
}
const enc = encodeURIComponent;
const btn = (href, label, pri) => `<a class="${pri ? 'pri' : ''}" href="${href}" target="_blank" rel="noopener nofollow">${label}</a>`;
function calc() {
  const lines = $('q').value.split(/\n/).map(l => l.trim()).filter(Boolean);
  if (!lines.length) { $('out').innerHTML = ''; return; }
  $('out').innerHTML = lines.map(raw => {
    const hit = lookup(raw);
    let kw = clean(raw.replace(PG_PREFIX, '')).replace(/\*/g, ' ').trim() || raw;
    const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
    const head = hit
      ? `<div class="name">${esc(hit.name)}<span class="cat">${esc(hit.cat)}</span></div><p class="desc">${esc(hit.desc)}</p>`
      : `<div class="name">${esc(kw)}</div><p class="desc">사전에 없는 가맹점입니다. 아래 검색으로 상호를 확인하고, 지도에서 결제한 날 갔던 곳인지 맞춰 보세요.</p>`;
    return `<div class="hit"><div class="raw">${esc(raw)}</div>${head}<div class="btns">
      ${btn('https://search.naver.com/search.naver?query=' + enc(kw), '네이버 검색', true)}
      ${btn('https://www.google.com/search?q=' + enc(kw + ' 결제'), '구글 검색')}
      ${btn('https://map.naver.com/p/search/' + enc(kw), '네이버 지도')}
      ${btn('https://map.kakao.com/?q=' + enc(kw), '카카오맵')}
    </div></div>`;
  }).join('');
}
$('q').addEventListener('input', calc);
// 아래 "자주 나오는 이름" 표
const rows = DICT.map(([k, name, cat, desc]) => `<tr><td>${name}</td><td>${cat}</td><td>${desc}</td></tr>`).join('');
$('dict').innerHTML = `<table><tr><th>표시 이름</th><th>분류</th><th>설명</th></tr>${rows}</table>`;
$('dictq').addEventListener('input', () => {
  const q = norm($('dictq').value);
  $('dict').querySelectorAll('tr').forEach((tr, i) => { if (i) tr.style.display = !q || norm(tr.textContent).includes(q) ? '' : 'none'; });
});
""",
        "notes": """
<h2>사용 방법</h2>
<ol>
<li>카드사 앱이나 문자에 찍힌 내역을 그대로 복사해 붙여 넣습니다. 금액·날짜가 섞여 있어도 됩니다. 여러 줄을 한 번에 넣어도 각각 찾아 줍니다.</li>
<li>결제대행사(KCP, 이니시스, 네이버페이 등)나 법인명(우아한형제들, 에스씨케이컴퍼니 등)으로 찍힌 내역은 어떤 서비스인지 바로 보여 줍니다.</li>
<li>사전에 없는 가맹점은 정리된 이름으로 네이버·구글·지도 검색 링크를 만들어 줍니다. 동네 가게는 <strong>지도 검색</strong>이 가장 빠릅니다.</li>
</ol>
<h2>그래도 모르겠다면: 카드사 앱에서 가맹점 정보 보기</h2>
<p>모든 카드사 앱은 이용 내역을 누르면 <strong>가맹점 상호·업종·주소·전화번호</strong>를 보여 줍니다. 결제한 날짜와 시간, 주소를 보면 대부분 기억이 납니다.
온라인 결제라면 같은 날짜의 쇼핑몰·앱 주문 내역이나 결제 완료 이메일·문자를 함께 찾아보세요.</p>
<h2>내가 안 한 결제라면</h2>
<ul>
<li><strong>정기결제·구독</strong>: 애플·구글·넷플릭스처럼 매달 같은 금액이면 가족이 쓰는 구독이거나 무료 체험이 유료로 바뀐 경우가 많습니다. 각 서비스의 구독 관리 화면에서 확인·해지합니다.</li>
<li><strong>휴대폰 소액결제</strong>: 통신사 이름으로 찍힌 콘텐츠 결제는 통신사 앱의 소액결제 내역에서 확인하고, 필요하면 소액결제 차단을 신청합니다.</li>
<li><strong>전혀 모르는 결제</strong>: 카드사 고객센터에 바로 연락해 <strong>이의신청(부정사용 신고)</strong>을 하고 카드를 정지·재발급합니다. 해외 결제라면 결제 취소에 시간이 걸릴 수 있으니 빨리 신고할수록 유리합니다.</li>
</ul>
<h2>자주 나오는 이름 목록</h2>
<p>이 검색기가 알고 있는 이름입니다. 법인명·영문 표기 기준으로 찾아보세요.</p>
<input class="dict-filter" id="dictq" placeholder="목록에서 찾기 (예: 쿠팡, 애플, 통행료)">
<div id="dict" style="overflow-x:auto"></div>
<p style="font-size:13px;color:var(--muted)">법인명과 운영 브랜드는 바뀔 수 있습니다. 정확한 가맹점 정보는 카드사 앱의 이용 내역 상세에서 확인하세요.</p>
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
