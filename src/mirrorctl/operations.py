import subprocess
import sys

from pydantic import AnyUrl

from mirrorctl.types import RepoData, RepoGroup
from mirrorctl.utils import join_url


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


def format_baseurl_list(baseurl_list: list[AnyUrl]) -> str:
    """
    Format baseurl list for DNF config-manager.

    Desired final output in `99-config_manager.repo`:
        ```
        baseurl=https://dl.fedoraproject.org/pub/fedora/linux
            https://dl.fedoraproject.org/pub/fedora/linux
            https://dl.fedoraproject.org/pub/fedora/linux
        ```
    """
    if len(baseurl_list) == 0:
        raise ValueError("`baseurl_list` is empty")

    formatted_lines = [str(baseurl_list[0])]

    for baseurl in baseurl_list[1:]:
        formatted_lines.append(f"\t{baseurl}")

    return "\n".join(formatted_lines)


def run_dnf_config_manager(command: str) -> None:
    full_command = f"dnf config-manager {command}"

    try:
        subprocess.run(
            full_command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(e.stderr, file=sys.stderr)
        sys.exit(1)


def set_baseurl(repo_group: RepoGroup, urls: list[AnyUrl]) -> None:
    # Disable metalink
    for repo_data in repo_group.repo_data_list:
        run_dnf_config_manager(f"setopt {repo_data.repo_id}.metalink=''")

    # Enable baseurl
    for repo_data in repo_group.repo_data_list:
        full_baseurls = build_full_baseurl_list(repo_data, urls)
        formatted_baseurls = format_baseurl_list(full_baseurls)
        run_dnf_config_manager(
            f"setopt {repo_data.repo_id}.baseurl='{formatted_baseurls}'"
        )


def set_metalink(
    repo_group: RepoGroup,
    country: list[str] | None = None,
    protocol: list[str] | None = None,
) -> None:
    # Disable baseurl
    for repo_data in repo_group.repo_data_list:
        run_dnf_config_manager(f"setopt {repo_data.repo_id}.baseurl=''")

    # Enable metalink
    for repo_data in repo_group.repo_data_list:
        metalink_url = metalink_builder(
            metalink_base=repo_group.metalink_base_url,
            repo_id=repo_data.metalink_repo_id,
            country=country,
            protocol=protocol,
        )
        run_dnf_config_manager(f"setopt {repo_data.repo_id}.metalink='{metalink_url}'")
