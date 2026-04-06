import configparser
from unittest.mock import patch

import pytest
from pydantic import AnyUrl

from mirrorctl.operations import (
    build_full_baseurl_list,
    metalink_builder,
    set_baseurl,
    set_metalink,
)
from mirrorctl.types import RepoData, RepoGroup


class TestMetalinkBuilder:
    def test_basic(self):
        url = str(
            metalink_builder(
                AnyUrl("https://mirrors.example.com"),
                "updates-released-f43",
            )
        )
        assert "repo=updates-released-f43" in url
        assert "arch=$basearch" in url
        assert "country" not in url
        assert "protocol" not in url

    def test_with_country(self):
        url = str(
            metalink_builder(
                AnyUrl("https://mirrors.example.com"),
                "updates-released-f43",
                country=["KR", "JP"],
            )
        )
        assert "country=KR,JP" in url

    def test_with_protocol(self):
        url = str(
            metalink_builder(
                AnyUrl("https://mirrors.example.com"),
                "updates-released-f43",
                protocol=["https", "http"],
            )
        )
        assert "protocol=https,http" in url

    def test_with_country_and_protocol(self):
        url = str(
            metalink_builder(
                AnyUrl("https://mirrors.example.com"),
                "updates-released-f43",
                country=["KR"],
                protocol=["https"],
            )
        )
        assert "country=KR" in url
        assert "protocol=https" in url


class TestBuildFullBaseurlList:
    def test_single_url(self):
        repo_data = RepoData(
            repo_id="test",
            metalink_repo_id="test-f43",
            baseurl_path="/updates/43/x86_64/",
        )
        result = build_full_baseurl_list(
            repo_data, [AnyUrl("https://mirror.example.com")]
        )
        assert len(result) == 1
        assert str(result[0]) == (
            "https://mirror.example.com/updates/43/x86_64/"
        )

    def test_multiple_urls(self):
        repo_data = RepoData(
            repo_id="test",
            metalink_repo_id="test-f43",
            baseurl_path="/path/",
        )
        result = build_full_baseurl_list(
            repo_data,
            [
                AnyUrl("https://mirror1.example.com"),
                AnyUrl("https://mirror2.example.com"),
            ],
        )
        assert len(result) == 2
        assert str(result[0]) == "https://mirror1.example.com/path/"
        assert str(result[1]) == "https://mirror2.example.com/path/"

    def test_trailing_slash_deduped(self):
        repo_data = RepoData(
            repo_id="test",
            metalink_repo_id="test-f43",
            baseurl_path="/path/",
        )
        result = build_full_baseurl_list(
            repo_data, [AnyUrl("https://mirror.example.com/")]
        )
        assert str(result[0]) == "https://mirror.example.com/path/"

    def test_empty_urls_raises(self):
        repo_data = RepoData(
            repo_id="test",
            metalink_repo_id="test-f43",
            baseurl_path="/path/",
        )
        with pytest.raises(ValueError, match="mirror_urls"):
            build_full_baseurl_list(repo_data, [])


class TestSetMetalink:
    def test_writes_file(self, sample_repo_group, override_file):
        result = set_metalink(sample_repo_group, country=["KR"])

        assert result == override_file
        assert override_file.exists()

        config = configparser.RawConfigParser()
        config.read(override_file)

        assert config.has_section("test-updates")
        assert config.has_section("test-updates-source")
        assert "country=KR" in config.get("test-updates", "metalink")
        assert config.get("test-updates", "baseurl") == ""

    def test_without_country(self, sample_repo_group, override_file):
        set_metalink(sample_repo_group)

        config = configparser.RawConfigParser()
        config.read(override_file)

        metalink = config.get("test-updates", "metalink")
        assert "country" not in metalink


class TestSetBaseurl:
    def test_writes_file(self, sample_repo_group, override_file):
        urls = [AnyUrl("https://mirror.example.com/pub/fedora/linux")]
        result = set_baseurl(sample_repo_group, urls)

        assert result == override_file
        assert override_file.exists()

        config = configparser.RawConfigParser()
        config.read(override_file)

        assert config.has_section("test-updates")
        baseurl = config.get("test-updates", "baseurl")
        assert "mirror.example.com" in baseurl
        assert config.get("test-updates", "metalink") == ""

    def test_multiple_baseurls(self, sample_repo_group, override_file):
        urls = [
            AnyUrl("https://mirror1.example.com/pub/fedora/linux"),
            AnyUrl("https://mirror2.example.com/pub/fedora/linux"),
        ]
        set_baseurl(sample_repo_group, urls)

        config = configparser.RawConfigParser()
        config.read(override_file)

        baseurl = config.get("test-updates", "baseurl")
        assert "mirror1.example.com" in baseurl
        assert "mirror2.example.com" in baseurl


class TestMerge:
    def test_different_groups_preserved(self, override_file):
        group_a = RepoGroup(
            group_name="group-a",
            metalink_base_url="https://mirrors.example.com",
            repo_data_list=[
                RepoData(
                    repo_id="repo-a",
                    metalink_repo_id="repo-a-f43",
                    baseurl_path="/a/",
                ),
            ],
        )
        group_b = RepoGroup(
            group_name="group-b",
            metalink_base_url="https://mirrors.example.com",
            repo_data_list=[
                RepoData(
                    repo_id="repo-b",
                    metalink_repo_id="repo-b-f43",
                    baseurl_path="/b/",
                ),
            ],
        )

        set_metalink(group_a)
        set_metalink(group_b, country=["US"])

        config = configparser.RawConfigParser()
        config.read(override_file)

        assert config.has_section("repo-a")
        assert config.has_section("repo-b")
        assert "country" not in config.get("repo-a", "metalink")
        assert "country=US" in config.get("repo-b", "metalink")

    def test_same_group_replaced(self, override_file):
        group = RepoGroup(
            group_name="test",
            metalink_base_url="https://mirrors.example.com",
            repo_data_list=[
                RepoData(
                    repo_id="repo-x",
                    metalink_repo_id="repo-x-f43",
                    baseurl_path="/x/",
                ),
            ],
        )

        set_metalink(group, country=["KR"])
        set_metalink(group, country=["US"])

        config = configparser.RawConfigParser()
        config.read(override_file)

        metalink = config.get("repo-x", "metalink")
        assert "country=US" in metalink
        assert "country=KR" not in metalink
