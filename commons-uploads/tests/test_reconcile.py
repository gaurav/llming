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
