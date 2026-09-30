from autoblog import threads


def test_compose_fits_limit_and_keeps_link():
    post = {"title": "제목", "description": "가" * 1000}
    text = threads.compose(post, "https://example.github.io/posts/x/")
    assert len(text) <= threads.MAX_CHARS
    assert text.endswith("https://example.github.io/posts/x/")
    assert text.startswith("제목\n\n")


def test_share_creates_then_publishes(monkeypatch):
    calls = []

    def fake_post(path, params):
        calls.append((path, params))
        return {"id": "container-1"} if path.endswith("/threads") else {"id": "media-9"}

    monkeypatch.setattr(threads, "_post", fake_post)
    media_id = threads.share({"title": "t", "description": "d"}, "https://x/p/", "tok")
    assert media_id == "media-9"
    assert calls[0][0] == "/v1.0/me/threads" and calls[0][1]["link_attachment"] == "https://x/p/"
    assert calls[1] == ("/v1.0/me/threads_publish", {"creation_id": "container-1", "access_token": "tok"})


def test_compose_uses_intro_when_given():
    post = {"title": "제목", "description": "설명"}
    text = threads.compose(post, "https://x/p/", "회사에서 이런 사람 보신 적 있나요?")
    assert text == "회사에서 이런 사람 보신 적 있나요?\n\n👉 https://x/p/"
