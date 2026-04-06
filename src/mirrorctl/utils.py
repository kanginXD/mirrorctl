from pydantic import AnyUrl


def join_url(base_url: AnyUrl, path: str) -> AnyUrl:
    return AnyUrl(str(base_url).removesuffix("/") + path)
