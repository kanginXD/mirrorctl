import re
from enum import StrEnum
from pathlib import Path
from typing import Annotated, NoReturn

import click
import distro
import pydantic
import typer
from pydantic import AnyUrl

from mirrorctl.data.fedora import FEDORA_REPO_GROUP
from mirrorctl.data.rpmfusion_free import RPMFUSION_FREE_REPO_GROUP
from mirrorctl.data.rpmfusion_nonfree import RPMFUSION_NONFREE_REPO_GROUP
from mirrorctl.operations import (
    reset_overrides,
    set_baseurl,
    set_metalink,
    set_official_only,
    unset_all_mirrors,
)
from mirrorctl.types import RepoGroup
from mirrorctl.validation import validate_metalink_preferences

MANAGED_REPO_GROUPS: tuple[RepoGroup, ...] = (
    FEDORA_REPO_GROUP,
    RPMFUSION_FREE_REPO_GROUP,
    RPMFUSION_NONFREE_REPO_GROUP,
)

_DISTRO_REPO_MAP: dict[str, RepoGroup] = {
    "fedora": FEDORA_REPO_GROUP,
}


class ExternalGroup(StrEnum):
    RPMFUSION_FREE = "rpmfusion-free"
    RPMFUSION_NONFREE = "rpmfusion-nonfree"


_EXTERNAL_GROUP_REPO_MAP: dict[ExternalGroup, RepoGroup] = {
    ExternalGroup.RPMFUSION_FREE: RPMFUSION_FREE_REPO_GROUP,
    ExternalGroup.RPMFUSION_NONFREE: RPMFUSION_NONFREE_REPO_GROUP,
}


def _exit_with_error(message: str) -> NoReturn:
    typer.echo(f"Error: {message}", err=True)
    raise typer.Exit(1)


def get_repo_group(
    group: str | None = None,
) -> RepoGroup:
    if group is None:
        # Default to system's repo
        distro_id = distro.id()
        if distro_id not in _DISTRO_REPO_MAP:
            _exit_with_error(f"Not supported distro: {distro_id}")

        return _DISTRO_REPO_MAP[distro_id]

    # Use specified external group
    if group not in _EXTERNAL_GROUP_REPO_MAP:
        _exit_with_error(f"Unknown group: {group}")

    return _EXTERNAL_GROUP_REPO_MAP[ExternalGroup(group)]


_GROUP_OPTION_HELP = (
    "Which repository bundle to change. "
    "Omitted: your distro's default (Fedora on Fedora). "
    "Use rpmfusion-free or rpmfusion-nonfree for RPM Fusion "
    "(different mirror pool; configure separately from Fedora)."
)

_APP_HELP = (
    "Change DNF mirrors in a simple way. "
    "All changes are written to /etc/dnf/repos.override.d/999-ultimate.repo. "
    "Fedora and RPM Fusion use different mirror pools; "
    "for add-ons such as RPM Fusion, use --group."
)

app = typer.Typer(help=_APP_HELP, no_args_is_help=True)


class AnyUrlTypeParser(click.ParamType):
    name = "AnyUrl"

    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> AnyUrl:
        try:
            return AnyUrl(value)
        except pydantic.ValidationError:
            self.fail(f"Invalid URL: {value}", param, ctx)


def _validate_country_codes(value: list[str]) -> list[str]:
    for country_code in value:
        if not re.match("^[A-Za-z]{2}$", country_code):
            _exit_with_error(
                f"Invalid country code: {country_code}. "
                "Country code must be exactly 2 letters "
                "(ISO 3166-1 Alpha-2)"
            )

    return [code.upper() for code in value]


@app.command(
    "auto-mirrors",
    help=(
        "Mirrors are chosen for you automatically (GeoIP based). "
        "You can say which countries or protocol (http/https/rsync) you prefer; "
        "those are only hints and another mirror may still be picked. "
        "Unless --no-check is set, the metalink is fetched and country/protocol "
        "choices are checked against it (needs network). "
        "To use only the mirrors you choose, use `pin-mirrors`."
    ),
)
def auto_mirrors(
    country: Annotated[
        list[str] | None,
        typer.Option(
            help=(
                "Prefer mirrors in these countries. "
                "Codes are ISO 3166-1 Alpha-2 (two Latin letters); case-insensitive. "
                "Pass the flag once per code, e.g. --country KR --country US."
            ),
            callback=_validate_country_codes,
        ),
    ] = None,
    protocol: Annotated[
        list[str] | None,
        typer.Option(
            help=(
                "Prefer https, http, rsync, or a mix "
                "(e.g. --protocol https --protocol rsync). "
                "If none match, another option may still be used."
            ),
        ),
    ] = None,
    no_check: Annotated[
        bool,
        typer.Option(
            "--no-check",
            help="Skip country/protocol availability checks.",
        ),
    ] = False,
    group: Annotated[
        ExternalGroup | None,
        typer.Option(help=_GROUP_OPTION_HELP),
    ] = None,
) -> None:
    repo_group = get_repo_group(group=group)

    if not no_check and (country or protocol):
        try:
            validate_metalink_preferences(
                repo_group,
                countries=country,
                protocols=protocol,
            )

        except ValueError as e:
            _exit_with_error(str(e))

    override_file = set_metalink(
        repo_group,
        country=country,
        protocol=protocol,
    )
    _print_success_message(override_file)


@app.command(
    "pin-mirrors",
    help="Use only the mirror addresses you list (fixed list).",
)
def pin_mirrors(
    urls: Annotated[
        list[AnyUrl],
        typer.Argument(
            help="Mirror addresses, space-separated.",
            click_type=AnyUrlTypeParser(),
        ),
    ],
    group: Annotated[
        ExternalGroup | None,
        typer.Option(help=_GROUP_OPTION_HELP),
    ] = None,
) -> None:
    if len(urls) == 0:
        raise typer.BadParameter(
            "At least one mirror URL must be provided for pin-mirrors"
        )

    repo_group = get_repo_group(group=group)
    override_file = set_baseurl(repo_group, urls)
    _print_success_message(override_file)


@app.command(
    "official-only",
    help=(
        "Download only from the official project sites, "
        "not from volunteer mirror networks."
    ),
)
def official_only(
    group: Annotated[
        ExternalGroup | None,
        typer.Option(help=_GROUP_OPTION_HELP),
    ] = None,
) -> None:
    repo_group = get_repo_group(group=group)
    override_file = set_official_only(repo_group)
    _print_success_message(override_file)


@app.command(
    "unset-all-mirrors",
    help=(
        "Write empty mirror overrides for every repo mirrorctl manages to block "
        "DNF automatic mirror selection."
    ),
)
def unset_all_mirrors_command() -> None:
    override_file = unset_all_mirrors(MANAGED_REPO_GROUPS)
    _print_success_message(override_file)


@app.command(
    "reset",
    help="Delete mirrorctl override file.",
)
def reset_command() -> None:
    override_file = reset_overrides()
    print(f"Removed override file: {override_file}")


def _print_success_message(override_file: Path) -> None:
    print(
        f"Wrote DNF repo overrides on {override_file}\n\n"
        "IMPORTANT: Refresh metadata by running `dnf clean all && dnf repo info --all`"
    )


if __name__ == "__main__":
    app()
