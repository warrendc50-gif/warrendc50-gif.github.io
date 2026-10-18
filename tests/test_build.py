import json

from autoblog import builder, config, memory


def test_build_site_with_sample_post(tmp_path, monkeypatch):
    posts_dir = tmp_path / "posts"
    public_dir = tmp_path / "public"
    posts_dir.mkdir()
    monkeypatch.setattr(builder, "POSTS_DIR", posts_dir)
    monkeypatch.setattr(builder, "PUBLIC_DIR", public_dir)

    (posts_dir / "2026-09-27_sample.json").write_text(json.dumps({
        "title": "샘플 글 <제목>",
        "slug": "sample",
        "description": "설명",
        "tags": ["절약"],
        "date": "2026-09-27T00:00:00+00:00",
        "body_markdown": "## 소제목\n\n| a | b |\n|---|---|\n| 1 | 2 |\n",
        "products": [{"name": "상품", "price": 12900, "image": "https://x/i.jpg", "url": "https://link.coupang.com/a/x"}],
    }, ensure_ascii=False), encoding="utf-8")

    cfg = config.load_config()
    cfg["adsense_client"] = "ca-pub-1234567890"
    cfg["coupang_banner"] = cfg.get("coupang_banner") or cfg.get("coupang_banner_paused")
    cfg["naver_site_verification"] = "abc123"
    assert builder.build_site(cfg) == 1

    html = (public_dir / "posts/sample/index.html").read_text(encoding="utf-8")
    assert "샘플 글 &lt;제목&gt;" in html
    assert "<table>" in html
    assert "12,900원" in html
    assert 'rel="sponsored nofollow noopener"' in html
    assert cfg["coupang_disclosure"] in html
    assert "adsbygoogle.js?client=ca-pub-1234567890" in html
    assert (public_dir / "ads.txt").read_text() == "google.com, pub-1234567890, DIRECT, f08c47fec0942fa0\n"
    assert "posts/sample/" in (public_dir / "sitemap.xml").read_text(encoding="utf-8")
    assert (public_dir / "privacy/index.html").exists()
    assert "ads-partners.coupang.com/g.js" in html
    assert '<meta name="naver-site-verification" content="abc123">' in (public_dir / "index.html").read_text(encoding="utf-8")
    assert '"trackingCode": "AF8654921"' in html
    tool = (public_dir / "tools/loan-interest/index.html").read_text(encoding="utf-8")
    assert "대출 이자 계산기" in tool and "function calc()" in tool
    assert "tools/pyeong-converter/" in (public_dir / "sitemap.xml").read_text(encoding="utf-8")
    fx = (public_dir / "tools/exchange-rate/index.html").read_text(encoding="utf-8")
    assert "환율 계산기" in fx and "open.er-api.com" in fx
    card = (public_dir / "tools/card-statement-lookup/index.html").read_text(encoding="utf-8")
    assert "카드 내역 가맹점명 검색기" in card and "우아한형제들" in card and "search.naver.com" in card


def test_translated_sites(tmp_path, monkeypatch):
    posts_dir = tmp_path / "posts"
    public_dir = tmp_path / "public"
    posts_dir.mkdir()
    monkeypatch.setattr(builder, "POSTS_DIR", posts_dir)
    monkeypatch.setattr(builder, "PUBLIC_DIR", public_dir)
    base = {"description": "설명", "tags": ["절약"], "date": "2026-09-27T00:00:00+00:00", "body_markdown": "본문",
            "products": [{"name": "상품", "price": 12900, "image": "https://x/i.jpg", "url": "https://link.coupang.com/a/x"}]}
    (posts_dir / "a.json").write_text(json.dumps({**base, "title": "번역된 글", "slug": "done", "en": {
        "title": "Translated post", "description": "Desc", "tags": ["saving"], "body_markdown": "## Body\n\nText"},
        "ja": {"title": "翻訳済みの記事", "description": "説明", "tags": ["節約"], "body_markdown": "本文"}},
        ensure_ascii=False), encoding="utf-8")
    (posts_dir / "b.json").write_text(json.dumps({**base, "title": "번역 안 된 글", "slug": "todo"},
                                                 ensure_ascii=False), encoding="utf-8")

    cfg = config.load_config()
    assert builder.build_site(cfg) == 2
    site = cfg["site_url"]

    en = (public_dir / "en/posts/done/index.html").read_text(encoding="utf-8")
    assert '<html lang="en">' in en and "Translated post" in en and "1 min read" in en
    assert f'hreflang="ko" href="{site}/posts/done/"' in en
    assert "coupang" not in en.lower() and "12,900원" not in en
    assert not (public_dir / "en/posts/todo").exists()
    assert not (public_dir / "en/tools").exists()
    en_home = (public_dir / "en/index.html").read_text(encoding="utf-8")
    assert cfg["translations"]["en"]["site_title"] in en_home and "번역 안 된 글" not in en_home
    assert "/tools/" not in en_home

    ko = (public_dir / "posts/done/index.html").read_text(encoding="utf-8")
    assert f'hreflang="en" href="{site}/en/posts/done/"' in ko and "12,900원" in ko
    untranslated = (public_dir / "posts/todo/index.html").read_text(encoding="utf-8")
    assert 'hreflang="en"' not in untranslated.split("</head>")[0]
    assert f'href="{site}/en/"' in untranslated  # language switch falls back to the English home
    sitemap = (public_dir / "sitemap.xml").read_text(encoding="utf-8")
    assert f"{site}/en/posts/done/" in sitemap and f"{site}/en/posts/todo/" not in sitemap
    assert (public_dir / "en/rss.xml").exists() and (public_dir / "en/privacy/index.html").exists()

    ja = (public_dir / "ja/posts/done/index.html").read_text(encoding="utf-8")
    assert '<html lang="ja">' in ja and "翻訳済みの記事" in ja and "分で読めます" in ja
    for lang, url in (("ko", f"{site}/posts/done/"), ("en", f"{site}/en/posts/done/"), ("x-default", f"{site}/posts/done/")):
        assert f'hreflang="{lang}" href="{url}"' in ja
    assert f'hreflang="ja" href="{site}/ja/posts/done/"' in ko
    assert f"{site}/ja/posts/done/" in sitemap
    assert cfg["translations"]["ja"]["site_title"] in (public_dir / "ja/index.html").read_text(encoding="utf-8")


def test_tool_as_post_wraps_calculator_for_threads():
    from autoblog.__main__ import tool_as_post
    from autoblog.tools import TOOLS

    tool = next(t for t in TOOLS if t["slug"] == "card-statement-lookup")
    post = tool_as_post({"site_url": "https://example.com"}, tool)
    assert post["slug"] == "tool:card-statement-lookup"
    assert post["url"] == "https://example.com/tools/card-statement-lookup/"
    assert "<" not in post["body_markdown"] and "카드사" in post["body_markdown"]


def test_memory_boards(tmp_path, monkeypatch):
    posts_dir = tmp_path / "posts"
    public_dir = tmp_path / "public"
    data_dir = tmp_path / "memory"
    posts_dir.mkdir()
    data_dir.mkdir()
    monkeypatch.setattr(builder, "POSTS_DIR", posts_dir)
    monkeypatch.setattr(builder, "PUBLIC_DIR", public_dir)
    monkeypatch.setattr(memory, "MEMORY_DATA_DIR", data_dir)
    (data_dir / "ai-news.json").write_text(json.dumps([
        {"date": "2026-01-05", "headline": "Old <story>", "headline_ko": "오래된 소식", "outlet": "Reuters",
         "url": "https://example.com/a?x=1&y=2", "summary_ko": "요약 A", "topics": ["model"], "orgs": ["OpenAI"]},
        {"date": "2026-03-09", "headline": "새 소식", "headline_ko": "새 소식", "outlet": "연합뉴스",
         "url": "https://example.com/b", "summary_ko": "요약 B", "topics": ["policy", "korea"], "orgs": ["과기정통부"]},
    ], ensure_ascii=False), encoding="utf-8")

    cfg = config.load_config()
    cfg["giscus"] = {"repo": "o/r", "repo_id": "R_1", "category": "Memory", "category_id": ""}
    builder.build_site(cfg)
    index = (public_dir / "memory/index.html").read_text(encoding="utf-8")
    assert "AI 최신 뉴스" in index and "/memory/korea-economy/" in index and "전체 2건 보기" in index
    assert index.index("새 소식") < index.index("오래된 소식")  # preview shows newest first
    board = (public_dir / "memory/ai-news/index.html").read_text(encoding="utf-8")
    assert board.index("새 소식") < board.index("오래된 소식")  # newest first
    assert "2026년 3월" in board and "2026년 1월" in board
    assert "Old &lt;story&gt;" in board and 'href="https://example.com/a?x=1&amp;y=2"' in board
    assert 'data-topic="policy"' in board and "정책·규제" in board
    assert "giscus.app" not in board  # not configured yet
    empty = (public_dir / "memory/world-economy/index.html").read_text(encoding="utf-8")
    assert "아직 모아 둔 기사가 없습니다" in empty
    assert "memory/ai-news/" in (public_dir / "sitemap.xml").read_text(encoding="utf-8")
    assert "/memory/" in (public_dir / "index.html").read_text(encoding="utf-8")  # nav link
    assert "/memory/" not in (public_dir / "en/index.html").read_text(encoding="utf-8")  # Korean only
    privacy = (public_dir / "privacy/index.html").read_text(encoding="utf-8")
    assert "<h1>개인정보처리방침</h1>" in privacy and "giscus" in privacy  # Korean page, not the English one

    cfg["giscus"]["category_id"] = "DIC_1"
    builder.build_site(cfg)
    board = (public_dir / "memory/world-economy/index.html").read_text(encoding="utf-8")
    assert 'src="https://giscus.app/client.js"' in board
    assert 'data-term="memory/world-economy"' in board and 'data-category-id="DIC_1"' in board
