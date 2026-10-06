# mon — 자동 수익형 블로그

매일 Claude가 정보성 글을 1편(07시 KST 무렵, config.json publish_hours_kst)씩 쓰고, 정적 사이트로 만들어 GitHub Pages에 자동 게시합니다.
서버 비용은 0원(GitHub Actions + Pages)이며, 수익은 **본인 명의** 계정으로 들어옵니다.

| 수익원 | 방식 | 지급 |
|---|---|---|
| Google AdSense | 모든 페이지에 자동 광고 | AdSense 계정에 등록한 본인 은행 계좌 |
| 쿠팡 파트너스 | 글 주제에 맞는 상품 카드(제휴 링크) 자동 삽입 | 파트너스 계정에 등록한 본인 계좌 |

> ⚠️ 수익은 보장되지 않습니다. 검색 유입이 생기기까지 보통 수개월이 걸리고, AdSense 승인도 거절될 수 있습니다.
> 매일 API 비용(글 1편당 대략 수십~수백 원)이 발생합니다. 가끔 글을 직접 읽고 다듬어 품질을 관리하세요.

## 동작 흐름

```
매시간 GitHub Actions가 확인 → 07:00 / 19:00 (KST) 슬롯에 아직 글이 없으면 작성
  → data/topics.txt 에서 안 쓴 주제 선택 (비면 Claude가 새 주제 20개 생성)
  → Claude가 글 작성 (SEO 제목·메타설명·FAQ 포함)
  → 쿠팡 파트너스 API로 관련 상품 검색 → 제휴 링크 카드 삽입 + 대가성 문구 표기
  → Claude가 영어·일본어로 번역 (번역 안 된 예전 글도 한 번에 최대 20건씩 채움)
  → content/posts/*.json 커밋
  → public/ 에 HTML·sitemap.xml·rss.xml·robots.txt·ads.txt·개인정보처리방침 생성
  → GitHub Pages 배포
```

## 설정 방법 (한 번만)

1. **Anthropic API 키** — https://console.anthropic.com 에서 발급
   → GitHub 저장소 `Settings → Secrets and variables → Actions → Secrets` 에 `ANTHROPIC_API_KEY` 등록
2. **GitHub Pages 켜기** — `Settings → Pages → Source: GitHub Actions`
   (비공개 저장소는 유료 플랜이 필요하므로 공개 저장소를 권장합니다.)
   이 브랜치를 기본 브랜치(`main`)로 병합하세요. 예약 실행은 기본 브랜치에서만 동작합니다.
3. **사이트 주소** — 저장소 이름을 `<아이디>.github.io` 로 만들면 자동으로 `https://<아이디>.github.io` 가 됩니다. 개인 도메인을 쓰려면 `Actions → Variables` 에 `SITE_URL` 등록
4. **쿠팡 파트너스**(선택) — https://partners.coupang.com 가입 → Open API 키 발급
   → Secrets 에 `COUPANG_ACCESS_KEY`, `COUPANG_SECRET_KEY` 등록
5. **AdSense**(선택) — 글이 20~30편 쌓인 뒤 https://adsense.google.com 에 사이트 신청
   → 승인 후 Variables 에 `ADSENSE_CLIENT` (예: `ca-pub-1234567890123456`) 등록
6. 정산 계좌는 **AdSense·쿠팡 파트너스 사이트의 지급 설정에서 직접** 등록하세요. 이 저장소에는 절대 적지 마세요.

첫 실행은 `Actions → autoblog → Run workflow` 로 바로 해볼 수 있습니다.

## 맞춤 설정

- `config.json` — 사이트 이름, 분야(`niche`), 하루 글 수(`posts_per_run`), 글 작성 모델(`model`), 번역 모델(`translate_model`)
- `data/topics.txt` — 쓰고 싶은 주제를 한 줄에 하나씩 추가
- `config.json` 의 `translations` — 번역할 언어와 언어별 사이트 이름·소개. 영어는 `/en/`, 일본어는 `/ja/` 에 게시되고
  hreflang 태그로 검색엔진에 언어별 페이지가 연결됩니다. 쿠팡 상품·계산기는 한국어 사이트에만 나옵니다.

## 로컬 실행

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
python -m autoblog run        # 글 생성 + 사이트 빌드
python -m http.server -d public 8000
python -m pytest -q
```
