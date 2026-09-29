"""Uses Claude to write SEO-friendly posts and to refill the topic queue."""
import json

import anthropic

SYSTEM_PROMPT = """당신은 한국어 정보성 블로그의 전문 에디터입니다.
독자가 실제로 따라 할 수 있는 구체적이고 정확한 정보를 씁니다.

원칙:
- 검색 사용자의 질문에 첫 문단에서 바로 답합니다.
- 소제목(##, ###), 번호 목록, 표를 적절히 써서 훑어보기 쉽게 만듭니다.
- 확실하지 않은 수치·가격·법령은 지어내지 말고, "구매/적용 전 최신 정보를 확인하세요"처럼 확인을 권합니다.
- 의료·법률·투자 판단이 필요한 내용은 일반 정보임을 밝히고 전문가 상담을 권합니다.
- 과장 광고 문구, 낚시성 표현, 키워드 반복 나열을 하지 않습니다.
- 본문은 2,000~3,500자 분량의 Markdown으로 씁니다. 제목(# 헤더)은 본문에 넣지 않습니다."""

POST_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "검색 친화적인 글 제목 (60자 이내)"},
        "slug": {"type": "string", "description": "영문 소문자와 하이픈만 쓴 URL 슬러그"},
        "description": {"type": "string", "description": "메타 설명 (150자 이내)"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "product_keyword": {
            "type": "string",
            "description": "글과 관련해 쿠팡에서 검색할 상품 키워드 1개. 관련 상품이 없으면 빈 문자열",
        },
        "body_markdown": {"type": "string"},
    },
    "required": ["title", "slug", "description", "tags", "product_keyword", "body_markdown"],
    "additionalProperties": False,
}

TOPICS_SCHEMA = {
    "type": "object",
    "properties": {"topics": {"type": "array", "items": {"type": "string"}}},
    "required": ["topics"],
    "additionalProperties": False,
}


class Writer:
    def __init__(self, model: str):
        self.client = anthropic.Anthropic()
        self.model = model

    def _ask_json(self, prompt: str, schema: dict, system: str | None = None) -> dict:
        kwargs = {"system": system} if system else {}
        response = self.client.beta.messages.create(
            model=self.model,
            max_tokens=16000,
            thinking={"type": "adaptive"},
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": schema}},
            # Server-side fallback re-runs a policy-declined request on a recommended model.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
        if response.stop_reason == "refusal":
            raise RuntimeError(f"Claude declined the request: {response.stop_details}")
        if response.stop_reason == "max_tokens":
            raise RuntimeError("Response hit max_tokens before finishing")
        text = next(b.text for b in response.content if b.type == "text")
        return json.loads(text)

    def write_post(self, topic: str, niche: str) -> dict:
        prompt = (
            f"블로그 분야: {niche}\n"
            f"오늘의 주제: {topic}\n\n"
            "이 주제로 블로그 글 한 편을 작성하세요. "
            "마지막에는 핵심 요약(3~5줄)과 자주 묻는 질문(FAQ) 2~3개를 넣으세요."
        )
        return self._ask_json(prompt, POST_SCHEMA, system=SYSTEM_PROMPT)

    def suggest_topics(self, niche: str, used: list[str], count: int = 20) -> list[str]:
        recent = "\n".join(f"- {t}" for t in used[-100:]) or "(없음)"
        prompt = (
            f"블로그 분야: {niche}\n"
            f"이미 쓴 주제:\n{recent}\n\n"
            f"사람들이 실제로 검색할 만한 새 블로그 글 주제를 {count}개 제안하세요. "
            "이미 쓴 주제와 겹치지 않게, 구체적인 롱테일 키워드 형태로, 가능하면 "
            "관련 상품 추천을 자연스럽게 곁들일 수 있는 주제를 우선하세요."
        )
        return self._ask_json(prompt, TOPICS_SCHEMA)["topics"]
