from typing import Literal

from pydantic import AnyUrl, BaseModel


class RepoData(BaseModel):
    repo_id: str
    metalink_repo_id: str
    baseurl_path: str


class RepoGroup(BaseModel):
    group_name: str
    metalink_base_url: AnyUrl
    repo_data_list: list[RepoData]


MirrorProtocol = Literal["https", "http", "rsync"]
