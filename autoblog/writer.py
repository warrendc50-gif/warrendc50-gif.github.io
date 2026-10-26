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
- 직접 가 보거나 써 본 것처럼 경험담을 지어내지 않습니다. 여행·음식 글도 정보 가이드로 씁니다.
- 리서치 노트가 주어지면 그 안의 사실과 수치를 우선 쓰고, 노트에 없는 최신 수치는 단정하지 않습니다.
  본문 끝에 '참고 자료' 소제목을 두고 노트에서 실제로 쓴 출처(기관·매체명과 URL)를 2~5개 적습니다.
- 본문은 5,000~8,000자 분량의 심층 가이드 Markdown으로 씁니다. 제목(# 헤더)은 본문에 넣지 않습니다."""

RESEARCH_SYSTEM_PROMPT = """당신은 한국어 블로그 에디터를 돕는 리서처입니다.
주어진 주제에 대해 웹 검색으로 최신의 정확한 사실을 모읍니다.

원칙:
- 공공기관, 공식 발표, 주요 언론, 제조사·서비스 공식 페이지를 우선합니다.
- 수치·가격·제도·날짜는 출처 URL과 함께 적고, 출처마다 다르면 차이를 그대로 적습니다.
- 확인하지 못한 내용은 '확인 못 함'으로 표시하고 추측하지 않습니다.
- 결과는 한국어 Markdown 글머리표 노트로, 3,000자 이내로 정리합니다."""

RESEARCH_TOOLS = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 5}]

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

LANGUAGE_NAMES = {"en": "English", "ja": "Japanese"}

TRANSLATE_SYSTEM_PROMPT = """You translate posts from a Korean lifestyle blog into natural, fluent {language}
for international readers.

Rules:
- Write idiomatic {language}, not a word-for-word translation. Keep the author's voice: personal essays stay
  personal and informal; practical guides stay clear and scannable.
- Keep the Markdown structure (headings, lists, tables). Do not add a # title to the body.
- Readers may not know Korea. Briefly explain Korea-specific terms, services and customs the first time
  (e.g. "hoesik (after-work team dinners)", "pyeong (about 3.3 m²)").
- Keep prices in Korean won; you may add a rough figure in the reader's currency in parentheses. Never invent new facts, numbers,
  products or claims that are not in the original.
- Drop sentences that only make sense for Korean shoppers, such as references to Coupang product links.
- Write the title, description and tags in {language} too, as people searching in {language} would phrase them."""

TRANSLATION_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "SEO-friendly title in the target language"},
        "description": {"type": "string", "description": "Meta description (under 160 characters)"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "body_markdown": {"type": "string"},
    },
    "required": ["title", "description", "tags", "body_markdown"],
    "additionalProperties": False,
}

THREADS_SYSTEM_PROMPT = """당신은 블로그 운영자 본인으로서 새 글을 쓰레드(Threads)에 소개하는 짧은 글을 씁니다.
운영자는 회사를 오래 다닌 평범한 한국 직장인이고, 영상·방송 제작(vMix)에도 익숙합니다.

원칙:
- 한국어 2~4문장, 250자 이내. 링크는 붙이지 않습니다(시스템이 따로 붙입니다).
- 첫 문장은 공감되는 상황, 솔직한 한마디, 또는 질문으로 시작합니다. 매번 같은 틀을 쓰지 않습니다.
- 글의 핵심 한두 가지를 구체적으로 알려 주되, 전부 요약하지는 않습니다.
- 광고 문구, 과장, 낚시성 표현, 이모지 남발을 하지 않습니다. 해시태그는 쓰지 않거나 1개까지만.
- 직접 쓴 에세이라면 글쓴이의 말투와 생각을 살립니다."""

THREADS_SCHEMA = {
    "type": "object",
    "properties": {"text": {"type": "string"}},
    "required": ["text"],
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

    def _ask_json(self, prompt: str, schema: dict, system: str | None = None, effort: str = "medium") -> dict:
        kwargs = {"system": system} if system else {}
        # Streaming so long posts at high effort don't hit the non-streaming HTTP timeout.
        with self.client.beta.messages.stream(
            model=self.model,
            max_tokens=64000,
            thinking={"type": "adaptive"},
            output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
            # Server-side fallback re-runs a policy-declined request on a recommended model.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        ) as stream:
            response = stream.get_final_message()
        if response.stop_reason == "refusal":
            raise RuntimeError(f"Claude declined the request: {response.stop_details}")
        if response.stop_reason == "max_tokens":
            raise RuntimeError("Response hit max_tokens before finishing")
        text = next(b.text for b in response.content if b.type == "text")
        return json.loads(text)

    def research(self, topic: str, niche: str) -> str:
        """Collect current facts with sources via web search; returns Markdown notes ("" on failure)."""
        messages = [{"role": "user", "content": (
            f"블로그 분야: {niche}\n주제: {topic}\n\n"
            "이 주제로 심층 가이드를 쓰기 전에 필요한 최신 사실, 수치, 제도, 비교 기준을 조사해 노트로 정리하세요."
        )}]
        for _ in range(4):  # web search can pause a long turn; resume it a few times at most
            with self.client.messages.stream(
                model=self.model,
                max_tokens=32000,
                thinking={"type": "adaptive"},
                output_config={"effort": "medium"},
                system=RESEARCH_SYSTEM_PROMPT,
                tools=RESEARCH_TOOLS,
                messages=messages,
            ) as stream:
                response = stream.get_final_message()
            if response.stop_reason != "pause_turn":
                break
            messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason in ("refusal", "pause_turn"):
            return ""
        return "".join(b.text for b in response.content if b.type == "text").strip()

    def write_post(self, topic: str, niche: str, notes: str = "") -> dict:
        prompt = (
            f"블로그 분야: {niche}\n"
            f"오늘의 주제: {topic}\n\n"
            + (f"리서치 노트(웹 검색 결과):\n{notes}\n\n" if notes else "")
            + "이 주제로 블로그 글 한 편을 작성하세요. "
            "마지막에는 핵심 요약(3~5줄)과 자주 묻는 질문(FAQ) 3~5개를 넣으세요."
        )
        return self._ask_json(prompt, POST_SCHEMA, system=SYSTEM_PROMPT, effort="high")

    def translate_post(self, post: dict, lang: str) -> dict:
        language = LANGUAGE_NAMES[lang]
        prompt = (
            f"Translate this Korean blog post into {language}.\n\n"
            f"Title: {post['title']}\n"
            f"Description: {post['description']}\n"
            f"Tags: {', '.join(post.get('tags', []))}\n\n"
            f"Body (Markdown):\n{post['body_markdown']}"
        )
        return self._ask_json(prompt, TRANSLATION_SCHEMA, system=TRANSLATE_SYSTEM_PROMPT.format(language=language))

    def threads_text(self, post: dict) -> str:
        kind = "운영자가 직접 쓴 에세이" if post.get("author") == "human" else "정보성 글"
        prompt = (
            f"글 종류: {kind}\n제목: {post['title']}\n설명: {post['description']}\n\n"
            f"본문:\n{post['body_markdown'][:4000]}"
        )
        return self._ask_json(prompt, THREADS_SCHEMA, system=THREADS_SYSTEM_PROMPT)["text"].strip()

    def suggest_topics(self, categories: dict[str, str], used: list[str], count: int = 20) -> list[str]:
        """categories maps a category key to its niche; each topic comes back as "[key] 주제"."""
        recent = "\n".join(f"- {t}" for t in used[-100:]) or "(없음)"
        fields = "\n".join(f"- [{key}] {niche}" for key, niche in categories.items())
        prompt = (
            f"블로그 분야(카테고리 키와 설명):\n{fields}\n\n"
            f"이미 쓴 주제:\n{recent}\n\n"
            f"사람들이 실제로 검색할 만한 새 블로그 글 주제를 {count}개 제안하세요. "
            "분야를 골고루 돌아가며 섞고, 각 주제 앞에 카테고리 키를 '[money] 주제' 형식으로 붙이세요. "
            "이미 쓴 주제와 겹치지 않게, 구체적인 롱테일 키워드 형태로, 전문적으로 깊이 다룰 수 있는 주제를 우선하세요."
        )
        return self._ask_json(prompt, TOPICS_SCHEMA)["topics"]
