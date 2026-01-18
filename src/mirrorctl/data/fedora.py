from mirrorctl.types import RepoData, RepoGroup

FEDORA_REPO_GROUP = RepoGroup(
    metalink_base_url="https://mirrors.fedoraproject.org",
    repo_data_list=[
        # These are patent-licensed repos, not mirrored to any mirror
        # The metalink sever always returns the same server, so we don't need to set it
        # RepoData(
        #     repo_id="fedora-cisco-openh264",
        #     metalink_repo_id="fedora-cisco-openh264-$releasever",
        #     baseurl_path="",
        # ),
        # RepoData(
        #     repo_id="fedora-cisco-openh264-source",
        #     metalink_repo_id="fedora-cisco-openh264-source-$releasever",
        #     baseurl_path="",
        # ),
        RepoData(
            repo_id="updates-testing",
            baseurl_path="/updates/testing/$releasever/Everything/$basearch/",
            metalink_repo_id="updates-testing-f$releasever",
        ),
        RepoData(
            repo_id="updates-testing-debuginfo",
            baseurl_path="/updates/testing/$releasever/Everything/$basearch/debug/",
            metalink_repo_id="updates-testing-debug-f$releasever",
        ),
        RepoData(
            repo_id="updates-testing-source",
            baseurl_path="/updates/testing/$releasever/Everything/SRPMS/",
            metalink_repo_id="updates-testing-source-f$releasever",
        ),
        RepoData(
            repo_id="updates",
            baseurl_path="/updates/$releasever/Everything/$basearch/",
            metalink_repo_id="updates-released-f$releasever",
        ),
        RepoData(
            repo_id="updates-debuginfo",
            baseurl_path="/updates/$releasever/Everything/$basearch/debug/",
            metalink_repo_id="updates-released-debug-f$releasever",
        ),
        RepoData(
            repo_id="updates-source",
            baseurl_path="/updates/$releasever/Everything/SRPMS/",
            metalink_repo_id="updates-released-source-f$releasever",
        ),
        RepoData(
            repo_id="fedora",
            baseurl_path="/releases/$releasever/Everything/$basearch/os/",
            metalink_repo_id="fedora-$releasever",
        ),
        RepoData(
            repo_id="fedora-debuginfo",
            baseurl_path="/releases/$releasever/Everything/$basearch/debug/tree/",
            metalink_repo_id="fedora-debug-$releasever",
        ),
        RepoData(
            repo_id="fedora-source",
            baseurl_path="/releases/$releasever/Everything/source/tree/",
            metalink_repo_id="fedora-source-$releasever",
        ),
    ],
)
