"""Tests for chart.py output-path resolution."""
import sys
import subprocess
from pathlib import Path
import pytest

CHART_PY = (
    Path(__file__).parent.parent
    / "skills" / "view-builder" / "templates" / "chart.py"
)


class TestChartOutputPath:
    def test_writes_to_vault_views_assets(self, tmp_path):
        """Chart PNG must land in wiki/views/assets/ under the vault root."""
        vault = tmp_path / "vault"
        (vault / "wiki" / "views" / "assets").mkdir(parents=True)
        result = subprocess.run(
            [sys.executable, str(CHART_PY), "--vault", str(vault)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        expected = vault / "wiki" / "views" / "assets" / "chart.png"
        assert expected.exists(), (
            f"Expected PNG at {expected}. stdout: {result.stdout}"
        )

    def test_does_not_write_next_to_template(self, tmp_path):
        """Chart PNG must NOT land next to the template file."""
        vault = tmp_path / "vault"
        (vault / "wiki" / "views" / "assets").mkdir(parents=True)
        subprocess.run(
            [sys.executable, str(CHART_PY), "--vault", str(vault)],
            capture_output=True,
        )
        sidecar = CHART_PY.parent / "assets" / "chart.png"
        assert not sidecar.exists(), "PNG landed next to template — path fix not applied"
