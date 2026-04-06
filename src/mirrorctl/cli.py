import re
from enum import Enum
from pathlib import Path
from textwrap import dedent
from typing import Annotated, NoReturn

import click
import distro
import pydantic
import typer
from pydantic import AnyUrl

from mirrorctl.data.fedora import FEDORA_REPO_GROUP
from mirrorctl.data.rpmfusion_free import RPMFUSION_FREE_REPO_GROUP
from mirrorctl.data.rpmfusion_nonfree import RPMFUSION_NONFREE_REPO_GROUP
from mirrorctl.operations import set_baseurl, set_metalink, unset_all_mirrors
from mirrorctl.types import RepoGroup
from mirrorctl.validation import validate_country_mirrors

MANAGED_REPO_GROUPS: tuple[RepoGroup, ...] = (
    FEDORA_REPO_GROUP,
    RPMFUSION_FREE_REPO_GROUP,
    RPMFUSION_NONFREE_REPO_GROUP,
)

_DISTRO_REPO_MAP: dict[str, RepoGroup] = {
    "fedora": FEDORA_REPO_GROUP,
}


class ExternalGroup(str, Enum):
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


app = typer.Typer(help="Manage repository mirrors", no_args_is_help=True)


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


@app.command("auto-mirrors", help="Auto-select mirrors for repositories")
def auto_mirrors(
    country: Annotated[
        list[str] | None,
        typer.Option(
            help=(
                "ISO 3166-1 Alpha-2 country codes to prefer (space-separated). "
                "Note: if mirrors are not available in the specified countries, "
                "the server will choose closest available ones. If you don't want this, "
                "pin mirrors using 'pin-mirrors' command."
            ),
            callback=_validate_country_codes,
        ),
    ] = None,
    protocol: Annotated[
        list[str] | None,
        typer.Option(
            help=(
                "Protocols to prefer (space-separated, e.g., --protocol https http). "
                "Note: if there's no mirrors available with the specified protocols, "
                "the server will choose closest available ones. "
                "If you don't want this, pin mirrors using 'pin-mirrors' command."
            ),
        ),
    ] = None,
    group: Annotated[
        ExternalGroup | None,
        typer.Option(
            help="Repository group to apply changes to. "
            "If not provided, defaults to system's repo group",
        ),
    ] = None,
) -> None:
    repo_group = get_repo_group(group=group)

    if country:
        try:
            validate_country_mirrors(repo_group, country)

        except ValueError as e:
            _exit_with_error(str(e))

    override_file = set_metalink(
        repo_group,
        country=country,
        protocol=protocol,
    )
    _print_success_message(override_file)


@app.command("pin-mirrors", help="Pin mirrors for repositories")
def pin_mirrors(
    urls: Annotated[
        list[AnyUrl],
        typer.Argument(
            help=(
                "Mirror URLs to use (space-separated). "
                "Copy & paste exact urls from the mirrost list website."
            ),
            click_type=AnyUrlTypeParser(),
        ),
    ],
    group: Annotated[
        ExternalGroup | None,
        typer.Option(
            help="Extra repository group to apply changes to. "
            "If not provided, defaults to system's repo group",
        ),
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
    "unset-all-mirrors",
    help=(
        "Clear mirrorctl overrides for all managed repos "
        "(empty baseurl and metalink) to avoid unintended mirror use"
    ),
)
def unset_all_mirrors_command() -> None:
    override_file = unset_all_mirrors(MANAGED_REPO_GROUPS)
    _print_success_message(override_file)


def _print_success_message(override_file: Path) -> None:
    print(
        dedent(f"""
        --------------------------
        Changes made successfully!

        Steps you must take:
        1. Check config at {override_file}
        2. Apply config by running `dnf clean all && dnf repo info --all`
        """)
    )


if __name__ == "__main__":
    app()
