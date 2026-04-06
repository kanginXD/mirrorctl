import re
import subprocess

import httpx

from mirrorctl.operations import metalink_builder
from mirrorctl.types import RepoGroup

_REQUEST_TIMEOUT = 10.0


def get_dnf_variables() -> dict[str, str]:
    try:
        result = subprocess.run(
            ["dnf", "--dump-variables"],
            capture_output=True,
            text=True,
            check=True,
        )

    except FileNotFoundError as e:
        raise ValueError("dnf command not found") from e

    except subprocess.CalledProcessError as e:
        raise ValueError(
            f"Failed to get DNF variables: {e.stderr}"
        ) from e

    variables: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if " = " not in line:
            continue

        key, _, value = line.partition(" = ")
        variables[key.strip()] = value.strip()

    return variables


def _resolve_dnf_variables(
    template: str, variables: dict[str, str]
) -> str:
    result = template
    for key in sorted(variables, key=len, reverse=True):
        result = result.replace(f"${key}", variables[key])

    return result


def validate_country_mirrors(
    repo_group: RepoGroup,
    countries: list[str],
) -> None:
    """
    Fetch metalink XML and verify that mirrors exist
    for each given country code.

    Raises ValueError if validation fails.
    """
    dnf_vars = get_dnf_variables()
    first_repo = repo_group.repo_data_list[0]

    for country in countries:
        metalink_url = metalink_builder(
            metalink_base=repo_group.metalink_base_url,
            repo_id=first_repo.metalink_repo_id,
            country=[country],
        )
        resolved_url = _resolve_dnf_variables(
            str(metalink_url), dnf_vars
        )

        try:
            response = httpx.get(resolved_url, timeout=_REQUEST_TIMEOUT)
            response.raise_for_status()

        except httpx.HTTPError as e:
            raise ValueError(
                f"Failed to fetch mirror info for "
                f"country '{country}': {e}"
            ) from e

        locations = re.findall(
            r'location="([^"]+)"', response.text
        )

        if not any(
            country.upper() == loc.upper() for loc in locations
        ):
            raise ValueError(
                f"No mirrors found for country '{country.upper()}'"
            )
