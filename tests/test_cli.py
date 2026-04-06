"""Tests for mirrorctl CLI commands."""

from subprocess import CalledProcessError, CompletedProcess
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from mirrorctl.cli import app

runner = CliRunner()


@patch("mirrorctl.cli.subprocess.run")
def test_refresh_cache_success(mock_run: MagicMock) -> None:
    mock_run.return_value = CompletedProcess(["dnf"], 0)
    result = runner.invoke(app, ["refresh-cache"])

    assert result.exit_code == 0
    assert mock_run.call_count == 2
    assert mock_run.call_args_list[0][0][0] == ["dnf", "clean", "all"]
    assert mock_run.call_args_list[1][0][0] == ["dnf", "makecache", "--refresh"]


@patch("mirrorctl.cli.subprocess.run")
def test_refresh_cache_clean_fails(mock_run: MagicMock) -> None:
    mock_run.side_effect = CalledProcessError(1, ["dnf", "clean", "all"])
    result = runner.invoke(app, ["refresh-cache"])

    assert result.exit_code == 1
    assert mock_run.call_count == 1


@patch("mirrorctl.cli.subprocess.run")
def test_refresh_cache_makecache_fails(mock_run: MagicMock) -> None:
    mock_run.side_effect = [
        CompletedProcess(["dnf", "clean", "all"], 0),
        CalledProcessError(1, ["dnf", "makecache", "--refresh"]),
    ]
    result = runner.invoke(app, ["refresh-cache"])

    assert result.exit_code == 1
    assert mock_run.call_count == 2


@patch("mirrorctl.cli.subprocess.run")
def test_refresh_cache_dnf_not_found(mock_run: MagicMock) -> None:
    mock_run.side_effect = FileNotFoundError()
    result = runner.invoke(app, ["refresh-cache"])

    assert result.exit_code == 1
    assert mock_run.call_count == 1
