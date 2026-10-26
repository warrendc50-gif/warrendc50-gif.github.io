# 블로그 운영 메모 (Claude용)

## 카테고리
- `work` 직장생활 이야기 / `life` 생활 꿀팁 / `broadcast` 영상·방송 노트 / `money` 재테크·경제 /
  `tech` IT·AI 활용 / `science` 교양·과학 / `travel` 여행·음식 / `growth` 자기계발 /
  `math` 중3 수학 / `english` 중3 영어(2015 개정 교육과정 단원별, 연습문제·정답 포함) /
  `gram1`·`gram2`·`gram3` 중1·중2·중3 영문법('중N 영문법 M강' 시리즈, 규칙마다 예문 5개 이상) (config.json `categories`)
- 상단 메뉴는 config.json `nav_groups`로 묶는다(드롭다운). 새 카테고리를 만들면 알맞은 그룹 `keys`에도 넣는다.
- 공부 카테고리(math·english·gram1~3) 글은 짧은 목록·표·이모지 블록과 인라인 SVG 그림 2~3개로 쓴다(niche의 [쓰기 방식]·[그림]).
- `/words/` 중1·중2·중3 필수 영단어(목록·카드·퀴즈): 단어는 `data/words/grade{1,2,3}.json`의 [단어, 뜻, 예문, 해석] 행. 화면은 autoblog/words.py.
- 대량 생성(workflow_dispatch count=N)이 도는 동안에는 push하지 않는다. 워크플로가 마지막에 pull 없이 push하므로
  그 사이 다른 커밋이 올라가면 생성한 글 전체가 거부된다. 로컬에 커밋해 두고 실행이 끝난 뒤 push한다.
  (워크플로 파일 수정은 현재 gh 토큰에 workflow 권한이 없어 push가 거부된다.)
  수동 실행은 `GH_TOKEN=$(gh auth token -u warrendc50-gif) gh workflow run autoblog.yml --ref claude/zen-pascal-k5i0k2 -f count=N`.
  대기 중인 실행은 다음 정기 실행이 오면 취소되므로, 진행 중인 실행이 없을 때 건다.
- 자동 글 주제는 `data/topics.txt`에 `[money] 주제`처럼 카테고리 키를 붙여 넣는다(키가 없으면 `life`).
  카테고리별 `niche`가 글쓰기 프롬프트의 분야로 쓰인다.
- 자동 글은 웹 검색 리서치 → 심층 가이드(5,000~8,000자) 순서로 쓰고, 하루 4편(07·12·17·21시) 발행한다.
  API 월 지출 한도(Console)에 걸리면 생성이 실패하므로 빈도를 올리기 전에 한도를 확인한다.

## 운영자 글 다듬기 규칙
- 운영자가 보낸 글은 말투(1인칭 "~다")와 내용을 살리고, 없던 일화·사실을 지어내지 않는다.
- 덧붙인 연결 문장은 발행 후 운영자에게 목록으로 알린다.
- "20년 차" 같은 연차 표현은 쓰지 않는다. 회사명·직무·특정 가능한 인물은 넣지 않는다.
- 원문은 `drafts/<제목>.md`에 그대로 보관한다. "임시저장"이면 drafts에만 저장하고 발행하지 않는다.
- 운영자 직접 작성 글은 `"author": "human"`.

## 발행·공유
- 글은 `content/posts/YYYY-MM-DD_<slug>.json`으로 추가하고 push하면 자동 배포된다.
- Threads에 특정 글 하나만 올리기: workflow_dispatch에 `count=0`, `share_only=<slug>`.
- 수익화(쿠팡 배너, AdSense), 자동 글 빈도 같은 설정은 **운영자에게 먼저 묻고** 바꾼다.

## Memory 게시판 (/memory/)
- config.json `memory.boards`에 분야(ai-news, world-economy, korea-economy)가 있다. 한국어·영어(/en/memory/)·일본어(/ja/memory/) 사이트에 모두 만들어진다.
  영어·일본어 게시판 이름과 설명은 config.json `translations.<lang>.memory`에 있다. 운영자 메모(giscus)는 한국어 사이트에만 둔다.
- 각 분야의 기사 목록은 `data/memory/<board-key>.json`(배열)에 있다. 항목 키: date(YYYY-MM-DD), headline(원문), headline_ko, outlet, url, summary_ko(2~3문장), topics(목록), orgs(목록).
  각 항목에는 headline_en·summary_en·headline_ja·summary_ja도 넣는다. 한국어 제목·요약을 그대로 옮긴 번역이고(새 사실을 더하지 않는다), 원문 제목이 영어면 headline_en은 원문 그대로 쓴다. 이 칸이 없는 항목은 영어·일본어 페이지에서 원문 제목만 보인다.
  topics 값은 autoblog/memory.py `TOPIC_LABELS`에 있는 키만 쓴다. 페이지는 최신순·월별로 묶고, 헤드라인을 누르면 요약과 원문 링크가 열린다.
- 기사 추가: 운영자가 링크나 주제를 주면 **실제 검색 결과에서 확인한 URL만** 항목으로 추가한다. 헤드라인·날짜·URL을 지어내지 않는다. 같은 사건은 한 건만.
- 운영자 메모는 giscus(GitHub Discussions) 위젯. `giscus.category_id`가 비어 있으면 위젯이 나오지 않는다.
  설정 후: Discussion 제목 `memory/<board-key>`(data-mapping=specific, strict), 카테고리 `Memory`(Announcement), 토론은 잠가서 운영자만 쓴다.
- 항목에 `video`(확인된 YouTube watch URL)와 `video_channel`을 넣으면 ▶ 영상 링크가 붙는다. 없으면 자동으로 YouTube 검색 링크가 붙는다. 영상 URL도 검색 결과에서 본 것만 쓴다.
- `world-live`(전세계 긴급 Live) 데이터 파일은 객체 형태 `{"live_channels": [{name,url}], "items": [...]}`다. live_channels는 뉴스 채널의 `https://www.youtube.com/@핸들/live` 주소. topics: unrest, conflict, disaster, accident, terror, politics, health, economy.
- 새 기사 반영: 수집 결과를 `{"<board-key>": [항목...]}` JSON으로 만들고 `python scripts/update_memory.py <파일>`을 돌린다. 날짜·분류·링크·영상을 검증하고 중복(같은 URL 또는 거의 같은 헤드라인)을 걸러 data/memory에 넣는다. 그다음 commit·push.
- 분야 추가·이름 변경은 config.json `memory.boards`만 고치면 된다.
