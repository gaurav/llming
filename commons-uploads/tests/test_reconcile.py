import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reconcile import reconcile  # noqa: E402


def commons(title, w=4032, h=3024):
    return {"title": title, "url": f"https://commons.wikimedia.org/wiki/{title}", "width": w, "height": h}


def flickr(pid):
    return {"id": pid, "url": f"https://flickr.com/photos/x/{pid}/"}


def test_reconcile_statuses_and_notes():
    local = [
        {"file": "match.jpeg", "taken": "2024:04:08 12:00:00", "width": 4032, "height": 3024},
        {"file": "new.jpeg", "taken": "2024:04:08 12:00:01", "width": 4032, "height": 3024},
        {"file": "burst-a.jpeg", "taken": "2024:04:08 12:00:02", "width": 4032, "height": 3024},
        {"file": "burst-b.jpeg", "taken": "2024:04:08 12:00:02", "width": 4032, "height": 3024},
        {"file": "cropped.jpeg", "taken": "2024:04:08 12:00:03", "width": 4032, "height": 3024},
        {"file": "noexif.jpeg", "taken": None, "width": 4032, "height": 3024},
    ]
    on_commons = {
        "2024:04:08 12:00:00": [commons("File:Match.jpg")],
        "2024:04:08 12:00:03": [commons("File:Cropped.jpg", 3604, 2372)],
        "2024:04:08 13:00:00": [commons("File:Orphan.jpg")],
    }
    on_flickr = {
        "2024:04:08 12:00:00": [flickr("1")],
        "2024:04:08 12:00:01": [flickr("2")],
        "2024:04:08 14:00:00": [flickr("9")],
    }

    rows, unmatched_commons, unmatched_flickr = reconcile(local, on_commons, on_flickr)
    by_file = {r["file"]: r for r in rows}

    assert by_file["match.jpeg"]["status"] == "on-commons"
    assert by_file["match.jpeg"]["commons_title"] == "File:Match.jpg"
    assert by_file["match.jpeg"]["flickr_id"] == "1"
    assert by_file["new.jpeg"]["status"] == "to-upload"
    assert by_file["new.jpeg"]["flickr_id"] == "2"
    assert by_file["burst-a.jpeg"]["status"] == "needs-review"
    assert "burst-b.jpeg" in by_file["burst-a.jpeg"]["note"]
    assert by_file["cropped.jpeg"]["status"] == "on-commons"
    assert "3604x2372" in by_file["cropped.jpeg"]["note"]
    assert by_file["noexif.jpeg"]["status"] == "needs-review"
    assert [h["title"] for h in unmatched_commons] == ["File:Orphan.jpg"]
    assert [h["id"] for h in unmatched_flickr] == ["9"]


def test_move_files_sorts_by_status_and_leaves_on_commons(tmp_path):
    from reconcile import move_files

    src = tmp_path / "export"
    src.mkdir()
    for name in ("keep.jpeg", "new.jpeg", "burst.jpeg"):
        (src / name).write_bytes(b"x")
    rows = [
        {"file": "keep.jpeg", "status": "on-commons"},
        {"file": "new.jpeg", "status": "to-upload"},
        {"file": "burst.jpeg", "status": "needs-review"},
    ]
    move_files(rows, src, tmp_path / "to-upload", tmp_path / "needs-review")
    assert sorted(p.name for p in src.iterdir()) == ["keep.jpeg"]
    assert (tmp_path / "to-upload" / "new.jpeg").exists()
    assert (tmp_path / "needs-review" / "burst.jpeg").exists()


def test_move_files_refuses_to_overwrite_and_moves_nothing(tmp_path):
    import click
    import pytest
    from reconcile import move_files

    src = tmp_path / "export"
    src.mkdir()
    (src / "a.jpeg").write_bytes(b"new a")
    (src / "b.jpeg").write_bytes(b"b")
    dest = tmp_path / "to-upload"
    dest.mkdir()
    (dest / "a.jpeg").write_bytes(b"old a")
    rows = [{"file": "a.jpeg", "status": "to-upload"}, {"file": "b.jpeg", "status": "to-upload"}]
    with pytest.raises(click.ClickException):
        move_files(rows, src, dest, tmp_path / "needs-review")
    assert (dest / "a.jpeg").read_bytes() == b"old a"
    assert (src / "b.jpeg").exists()


def test_load_env_sets_only_unset_keys(tmp_path, monkeypatch):
    from reconcile import load_env

    env = tmp_path / ".env"
    env.write_text("# comment\n\nFLICKR_API_KEY=abc\nFLICKR_API_SECRET = s=1\nBROKEN LINE\n")
    monkeypatch.delenv("FLICKR_API_KEY", raising=False)
    monkeypatch.setenv("FLICKR_API_SECRET", "already")
    load_env(env)
    import os
    assert os.environ["FLICKR_API_KEY"] == "abc"
    assert os.environ["FLICKR_API_SECRET"] == "already"
    load_env(tmp_path / "missing.env")  # no file is fine
