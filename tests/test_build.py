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
