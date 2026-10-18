# 블로그 운영 메모 (Claude용)

## 카테고리
- `work` 직장생활 이야기 / `life` 생활 꿀팁 / `broadcast` 영상·방송 노트 (config.json `categories`)
- 교양·과학 글(예: `solar-system-rotation-direction-exceptions`)은 지금 `life`에 있다.
  **교양·과학 글이 3편 이상 쌓이면** `science`(교양·과학) 카테고리를 config.json에 만들고,
  해당 글들의 `"category"`를 `science`로 옮긴 뒤 운영자에게 알린다.

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
- config.json `memory.boards`에 분야(ai-news, world-economy, korea-economy)가 있고, 각 분야 페이지는 giscus(GitHub Discussions) 위젯으로 글을 보여 준다. 한국어 사이트 전용.
- 글은 **운영자만** 쓴다: 각 분야의 Discussion은 GitHub에서 잠가(lock) 두고, 운영자가 Discussion 댓글로 기사 링크·메모를 추가한다. 댓글 하나 = 기사 하나.
- Discussion 제목은 `memory/<board-key>` (data-mapping=specific, strict). 저장소 Discussions 카테고리는 `Memory`(Announcement 형식).
- `giscus.category_id`가 비어 있으면 "준비 중" 안내만 나온다. 저장소에서 Discussions를 켜고 giscus 앱을 설치한 뒤 category_id를 채운다.
- 분야 추가·이름 변경은 config.json `memory.boards`만 고치면 된다.

