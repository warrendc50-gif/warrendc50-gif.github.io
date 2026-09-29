from datetime import datetime, timezone

import autoblog.__main__ as cli


def _posts(monkeypatch, *posts):
    monkeypatch.setattr(cli, "load_posts", lambda: list(posts))


def test_due_when_slot_empty(monkeypatch):
    # 2026-09-28 10:30 UTC = 19:30 KST -> evening slot started 19:00 KST (10:00 UTC)
    _posts(monkeypatch, {"date": "2026-09-28T00:45:00+00:00"})
    assert cli.slot_due({}, datetime(2026, 9, 28, 10, 30, tzinfo=timezone.utc))


def test_not_due_after_generated_post(monkeypatch):
    _posts(monkeypatch, {"date": "2026-09-28T10:20:00+00:00"})
    assert not cli.slot_due({}, datetime(2026, 9, 28, 11, 0, tzinfo=timezone.utc))


def test_human_posts_do_not_fill_slot(monkeypatch):
    _posts(monkeypatch, {"date": "2026-09-28T10:20:00+00:00", "author": "human"})
    assert cli.slot_due({}, datetime(2026, 9, 28, 11, 0, tzinfo=timezone.utc))


def test_before_first_slot_uses_previous_evening(monkeypatch):
    # 05:00 KST (20:00 UTC previous day): slot is previous day 19:00 KST (10:00 UTC)
    _posts(monkeypatch, {"date": "2026-09-28T10:20:00+00:00"})
    assert not cli.slot_due({}, datetime(2026, 9, 28, 20, 0, tzinfo=timezone.utc))
    _posts(monkeypatch, {"date": "2026-09-28T00:45:00+00:00"})
    assert cli.slot_due({}, datetime(2026, 9, 28, 20, 0, tzinfo=timezone.utc))
