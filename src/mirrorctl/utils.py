import subprocess

from pydantic import AnyUrl


def join_url(base_url: AnyUrl, path: str) -> AnyUrl:
    return AnyUrl(str(base_url).removesuffix("/") + path)


def check_package_installed(package_name: str) -> bool:
    return (
        subprocess.run(
            ["rpm", "-q", package_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )


def is_rpm_free_installed() -> bool:
    return check_package_installed("rpmfusion-free-release")


def is_rpm_nonfree_installed() -> bool:
    return check_package_installed("rpmfusion-nonfree-release")
