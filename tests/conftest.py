from unittest.mock import patch

import pytest

from mirrorctl.types import RepoData, RepoGroup


@pytest.fixture
def sample_repo_group() -> RepoGroup:
    return RepoGroup(
        group_name="test-group",
        metalink_base_url="https://mirrors.fedoraproject.org",
        official_base_urls=["https://dl.fedoraproject.org/pub/fedora/linux"],
        repo_data_list=[
            RepoData(
                repo_id="test-updates",
                metalink_repo_id="updates-released-f$releasever",
                baseurl_path="/updates/$releasever/Everything/$basearch/",
            ),
            RepoData(
                repo_id="test-updates-source",
                metalink_repo_id="updates-released-source-f$releasever",
                baseurl_path="/updates/$releasever/Everything/SRPMS/",
            ),
        ],
    )


@pytest.fixture
def override_file(tmp_path):
    path = tmp_path / "999-mirrorctl.repo"
    with patch("mirrorctl.operations.OVERRIDE_FILE", path):
        yield path
