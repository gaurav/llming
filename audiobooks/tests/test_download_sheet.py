"""Checks on the download CLI — chiefly the guard that keeps a sign-in page off the disk."""

import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import download_sheet  # noqa: E402

CSV = b"Title,Author,Genre\nPiranesi,Susanna Clarke,Fantasy\n"


class FakeResponse:
    """Just the bits of requests.Response that download_sheet touches."""

    def __init__(self, content, content_type):
        self.content = content
        self.headers = {"content-type": content_type}

    def raise_for_status(self):
        pass


@pytest.fixture
def respond_with(monkeypatch):
    """Answer the download with a canned response, and point .env at a sheet that needs no network."""

    def _respond_with(content, content_type):
        monkeypatch.setattr("audiobooks.load_dotenv", lambda *a, **k: False)
        monkeypatch.setenv("GOOGLE_SHEET_ID", "SHEET")
        monkeypatch.delenv("ENRICHMENT_GID", raising=False)  # or load() goes looking for that tab
        monkeypatch.setattr(
            download_sheet.requests, "get", lambda *a, **k: FakeResponse(content, content_type)
        )

    return _respond_with


def test_a_sign_in_page_is_refused_rather_than_saved(respond_with, tmp_path):
    # An unshared Sheet answers 200 with HTML. Without the guard this lands on disk as a .csv and
    # only fails much later, as a parse error a long way from the cause.
    respond_with(b"<html>Sign in</html>", "text/html; charset=utf-8")
    output = tmp_path / "data" / "audiobooks.csv"

    result = CliRunner().invoke(download_sheet.main, ["--output", str(output)])

    assert result.exit_code != 0
    assert "not shared" in result.output
    assert not output.exists()


def test_a_csv_is_saved_verbatim_and_parses_back(respond_with, tmp_path):
    respond_with(CSV, "text/csv")
    # data/ is gitignored and so absent after a fresh clone; the CLI has to create it.
    output = tmp_path / "data" / "audiobooks.csv"

    result = CliRunner().invoke(download_sheet.main, ["--output", str(output)])

    assert result.exit_code == 0, result.output
    assert output.read_bytes() == CSV
