"""Tests for mirrorctl CLI commands."""

from pathlib import Path
from subprocess import CalledProcessError, CompletedProcess
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from mirrorctl.cli import app
from mirrorctl.data.fedora import FEDORA_REPO_GROUP

runner = CliRunner()


@patch("mirrorctl.cli.set_metalink")
@patch("mirrorctl.cli.get_repo_group")
def test_auto_mirrors_no_options(
    mock_get_repo_group: MagicMock,
    mock_set_metalink: MagicMock,
) -> None:
    mock_get_repo_group.return_value = FEDORA_REPO_GROUP
    mock_set_metalink.return_value = Path(
        "/etc/dnf/repos.override.d/999-mirrorctl.repo"
    )

    result = runner.invoke(app, ["auto"])

    assert result.exit_code == 0
    mock_set_metalink.assert_called_once_with(
        FEDORA_REPO_GROUP,
        country=None,
        protocol=None,
    )


@patch("mirrorctl.cli.set_official_only")
@patch("mirrorctl.cli.get_repo_group")
def test_pin_official_only(
    mock_get_repo_group: MagicMock,
    mock_set_official_only: MagicMock,
) -> None:
    mock_get_repo_group.return_value = FEDORA_REPO_GROUP
    mock_set_official_only.return_value = Path(
        "/etc/dnf/repos.override.d/999-mirrorctl.repo"
    )

    result = runner.invoke(app, ["pin", "--official-only"])

    assert result.exit_code == 0
    mock_set_official_only.assert_called_once_with(FEDORA_REPO_GROUP)


@patch("mirrorctl.cli.set_official_only")
@patch("mirrorctl.cli.get_repo_group")
def test_pin_official_only_with_group(
    mock_get_repo_group: MagicMock,
    mock_set_official_only: MagicMock,
) -> None:
    mock_get_repo_group.return_value = FEDORA_REPO_GROUP
    mock_set_official_only.return_value = Path(
        "/etc/dnf/repos.override.d/999-mirrorctl.repo"
    )

    result = runner.invoke(
        app,
        ["pin", "--official-only", "--group", "rpmfusion-free"],
    )

    assert result.exit_code == 0
    mock_get_repo_group.assert_called_once()
    mock_set_official_only.assert_called_once_with(FEDORA_REPO_GROUP)


def test_pin_official_only_rejects_url() -> None:
    result = runner.invoke(
        app,
        [
            "pin",
            "--official-only",
            "--url",
            "https://dl.fedoraproject.org/pub/fedora/linux",
        ],
    )

    assert result.exit_code == 1


@patch("mirrorctl.cli.subprocess.run")
def test_refresh_cache_success(mock_run: MagicMock) -> None:
    mock_run.return_value = CompletedProcess(["dnf"], 0)
    result = runner.invoke(app, ["refresh"])

    assert result.exit_code == 0
    assert mock_run.call_count == 2
    assert mock_run.call_args_list[0][0][0] == ["dnf", "clean", "all"]
    assert mock_run.call_args_list[1][0][0] == ["dnf", "makecache", "--refresh"]


@patch("mirrorctl.cli.subprocess.run")
def test_refresh_cache_clean_fails(mock_run: MagicMock) -> None:
    mock_run.side_effect = CalledProcessError(1, ["dnf", "clean", "all"])
    result = runner.invoke(app, ["refresh"])

    assert result.exit_code == 1
    assert mock_run.call_count == 1


@patch("mirrorctl.cli.subprocess.run")
def test_refresh_cache_makecache_fails(mock_run: MagicMock) -> None:
    mock_run.side_effect = [
        CompletedProcess(["dnf", "clean", "all"], 0),
        CalledProcessError(1, ["dnf", "makecache", "--refresh"]),
    ]
    result = runner.invoke(app, ["refresh"])

    assert result.exit_code == 1
    assert mock_run.call_count == 2


@patch("mirrorctl.cli.subprocess.run")
def test_refresh_cache_dnf_not_found(mock_run: MagicMock) -> None:
    mock_run.side_effect = FileNotFoundError()
    result = runner.invoke(app, ["refresh"])

    assert result.exit_code == 1
    assert mock_run.call_count == 1
