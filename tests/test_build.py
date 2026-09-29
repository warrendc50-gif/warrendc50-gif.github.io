import json

from autoblog import builder, config


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
