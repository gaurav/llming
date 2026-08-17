"""The one thing worth a test here: -o pointing at the input must not destroy it.

Input and output are opened in the same `with`, so without the guard the input is
truncated to zero bytes before a single row is read.
"""

import sys
from pathlib import Path

from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from enrich_mesh_types import main  # noqa: E402


def test_output_over_input_is_refused(tmp_path):
    src = tmp_path / "ids.tsv"
    src.write_text("CTD-ASSIGNED CONCEPT ID\tNAME\nMESH:D012345\tfoo\n")

    # A different spelling of the same path, to check we compare real paths.
    result = CliRunner().invoke(main, [str(src), "-o", str(tmp_path / "." / "ids.tsv")])

    assert result.exit_code != 0
    assert "would overwrite the input file" in result.output
    assert src.read_text().startswith("CTD-ASSIGNED CONCEPT ID")
