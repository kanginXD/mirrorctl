from pydantic import AnyUrl

from mirrorctl.utils import join_url


class TestJoinUrl:
    def test_basic(self):
        result = join_url(AnyUrl("https://mirrors.fedoraproject.org"), "/path")
        assert str(result) == "https://mirrors.fedoraproject.org/path"

    def test_strips_trailing_slash(self):
        result = join_url(AnyUrl("https://mirrors.fedoraproject.org/"), "/path")
        assert str(result) == "https://mirrors.fedoraproject.org/path"

    def test_with_query_string(self):
        result = join_url(
            AnyUrl("https://mirrors.fedoraproject.org"),
            "/metalink?repo=test&arch=x86_64",
        )
        assert str(result) == (
            "https://mirrors.fedoraproject.org/metalink?repo=test&arch=x86_64"
        )
