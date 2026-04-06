import configparser
import sys
from collections.abc import Sequence
from pathlib import Path

from pydantic import AnyUrl

from mirrorctl.types import RepoData, RepoGroup
from mirrorctl.utils import join_url

OVERRIDE_DIR = Path("/etc/dnf/repos.override.d")
OVERRIDE_FILE = OVERRIDE_DIR / "999-ultimate.repo"


def _preserve_option_key(optionstr: str) -> str:
    return optionstr


def _new_repo_config() -> configparser.RawConfigParser:
    config = configparser.RawConfigParser()
    config.optionxform = _preserve_option_key
    return config


def _read_existing_config() -> configparser.RawConfigParser:
    config = _new_repo_config()
    if OVERRIDE_FILE.exists():
        config.read(OVERRIDE_FILE)

    return config


def _write_override_config(config: configparser.RawConfigParser) -> Path:
    try:
        OVERRIDE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with OVERRIDE_FILE.open("w") as f:
            config.write(f, space_around_delimiters=False)

    except PermissionError:
        print(
            f"Error: Permission denied writing to {OVERRIDE_FILE}\n"
            "Try running with sudo.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    return OVERRIDE_FILE


def _merge_and_write(
    repo_group: RepoGroup,
    new_config: configparser.RawConfigParser,
) -> Path:
    merged = _read_existing_config()

    for repo_data in repo_group.repo_data_list:
        if merged.has_section(repo_data.repo_id):
            merged.remove_section(repo_data.repo_id)

    for section in new_config.sections():
        merged.add_section(section)
        for key, value in new_config.items(section):
            merged.set(section, key, value)

    return _write_override_config(merged)


def unset_all_mirrors(repo_groups: Sequence[RepoGroup]) -> Path:
    config = _new_repo_config()
    seen: set[str] = set()

    for group in repo_groups:
        for repo_data in group.repo_data_list:
            rid = repo_data.repo_id

            if rid in seen:
                continue

            seen.add(rid)
            config.add_section(rid)
            config.set(rid, "baseurl", "")
            config.set(rid, "metalink", "")

    return _write_override_config(config)


def reset_overrides() -> Path:
    try:
        OVERRIDE_FILE.unlink(missing_ok=True)

    except PermissionError:
        print(
            f"Error: Permission denied deleting {OVERRIDE_FILE}\n"
            "Try running with sudo.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    return OVERRIDE_FILE


def metalink_builder(
    metalink_base: AnyUrl,
    repo_id: str,
    country: list[str] | None = None,
    protocol: list[str] | None = None,
) -> AnyUrl:
    query_params = {
        "repo": repo_id,
        "arch": "$basearch",
    }
    if country:
        query_params["country"] = ",".join(country)

    if protocol:
        query_params["protocol"] = ",".join(protocol)

    query_string = "&".join([f"{key}={value}" for key, value in query_params.items()])

    return join_url(metalink_base, f"/metalink?{query_string}")


def build_full_baseurl_list(
    repo_data: RepoData, mirror_urls: list[AnyUrl]
) -> list[AnyUrl]:
    if len(mirror_urls) == 0:
        raise ValueError("`mirror_urls` is empty")

    full_baseurl_list: list[AnyUrl] = []

    for url in mirror_urls:
        full_baseurl = AnyUrl(str(url).removesuffix("/") + repo_data.baseurl_path)
        full_baseurl_list.append(full_baseurl)

    return full_baseurl_list


def _generate_metalink_config(
    repo_group: RepoGroup,
    country: list[str] | None = None,
    protocol: list[str] | None = None,
) -> configparser.RawConfigParser:
    config = _new_repo_config()

    for repo_data in repo_group.repo_data_list:
        metalink_url = metalink_builder(
            metalink_base=repo_group.metalink_base_url,
            repo_id=repo_data.metalink_repo_id,
            country=country,
            protocol=protocol,
        )
        config.add_section(repo_data.repo_id)
        config.set(repo_data.repo_id, "metalink", str(metalink_url))
        config.set(repo_data.repo_id, "baseurl", "")

    return config


def _generate_baseurl_config(
    repo_group: RepoGroup,
    urls: list[AnyUrl],
) -> configparser.RawConfigParser:
    config = _new_repo_config()

    for repo_data in repo_group.repo_data_list:
        full_baseurls = build_full_baseurl_list(repo_data, urls)
        baseurl_value = "\n".join(str(url) for url in full_baseurls)

        config.add_section(repo_data.repo_id)
        config.set(repo_data.repo_id, "baseurl", baseurl_value)
        config.set(repo_data.repo_id, "metalink", "")

    return config


def set_baseurl(repo_group: RepoGroup, urls: list[AnyUrl]) -> Path:
    config = _generate_baseurl_config(repo_group, urls)
    return _merge_and_write(repo_group, config)


def set_official_only(repo_group: RepoGroup) -> Path:
    config = _generate_baseurl_config(
        repo_group,
        list(repo_group.official_base_urls),
    )
    return _merge_and_write(repo_group, config)


def set_metalink(
    repo_group: RepoGroup,
    country: list[str] | None = None,
    protocol: list[str] | None = None,
) -> Path:
    config = _generate_metalink_config(repo_group, country=country, protocol=protocol)
    return _merge_and_write(repo_group, config)
