import re
import subprocess
from collections.abc import Iterator

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
        raise ValueError(f"Failed to get DNF variables: {e.stderr}") from e

    variables: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if " = " not in line:
            continue

        key, _, value = line.partition(" = ")
        variables[key.strip()] = value.strip()

    return variables


def _resolve_dnf_variables(template: str, variables: dict[str, str]) -> str:
    result = template
    for key in sorted(variables, key=len, reverse=True):
        result = result.replace(f"${key}", variables[key])

    return result


def _iter_metalink_url_attrs(metalink_xml: str) -> Iterator[tuple[str, str | None]]:
    """Yield (protocol_lower, location_upper_or_none) per <url ...> tag."""
    for match in re.finditer(r"<url\s+([^>]+)>", metalink_xml):
        attrs = match.group(1)
        protocol_m = re.search(r'protocol="([^"]*)"', attrs)

        if not protocol_m:
            continue

        protocol = protocol_m.group(1).lower()
        location_m = re.search(r'location="([^"]*)"', attrs)
        location = location_m.group(1).upper() if location_m else None
        yield protocol, location


def validate_metalink_preferences(
    repo_group: RepoGroup,
    *,
    countries: list[str] | None,
    protocols: list[str] | None,
) -> None:
    """
    Fetch metalink (same query as set_metalink) and verify XML lists
    matching location and/or protocol attributes on <url> tags.

    Raises ValueError if validation fails.
    """
    if not countries and not protocols:
        return

    dnf_vars = get_dnf_variables()
    first_repo = repo_group.repo_data_list[0]
    metalink_url = metalink_builder(
        metalink_base=repo_group.metalink_base_url,
        repo_id=first_repo.metalink_repo_id,
        country=countries,
        protocol=protocols,
    )
    resolved_url = _resolve_dnf_variables(str(metalink_url), dnf_vars)

    try:
        response = httpx.get(resolved_url, timeout=_REQUEST_TIMEOUT)
        response.raise_for_status()

    except httpx.HTTPError as e:
        raise ValueError(f"Failed to fetch mirror info: {e}") from e

    pairs = list(_iter_metalink_url_attrs(response.text))
    proto_set = {p.lower() for p in protocols} if protocols else None

    if countries:
        for country in countries:
            cu = country.upper()
            found = False

            for ploc, loc in pairs:
                if loc != cu:
                    continue

                if proto_set is None:
                    found = True
                    break

                if ploc in proto_set:
                    found = True
                    break

            if not found:
                if proto_set:
                    want = ", ".join(sorted(proto_set))
                    raise ValueError(
                        f"No mirrors for country '{cu}' with protocol {want}"
                    )

                raise ValueError(f"No mirrors found for country '{cu}'")

    if protocols and not countries:
        required_protocols = {p.lower() for p in protocols}

        if not any(ploc in required_protocols for ploc, _ in pairs):
            want = ", ".join(sorted(required_protocols))
            raise ValueError(f"No mirrors found for protocol(s) {want}")
