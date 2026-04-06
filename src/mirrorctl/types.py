from pydantic import AnyUrl, BaseModel, field_validator


class RepoData(BaseModel):
    repo_id: str
    metalink_repo_id: str
    baseurl_path: str


class RepoGroup(BaseModel):
    group_name: str
    metalink_base_url: AnyUrl
    repo_data_list: list[RepoData]

    @field_validator("repo_data_list")
    @classmethod
    def check_non_empty(cls, v: list[RepoData]) -> list[RepoData]:
        if len(v) == 0:
            raise ValueError("repo_data_list must not be empty")

        return v
