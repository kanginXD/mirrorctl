from unittest.mock import MagicMock, patch

import httpx
import pytest

from mirrorctl.validation import (
    _resolve_dnf_variables,
    get_dnf_variables,
    validate_country_mirrors,
)

_SAMPLE_DNF_DUMP = """\
======== Variables: ========
arch = x86_64
basearch = x86_64
releasever = 43
releasever_major = 43
"""

_METALINK_XML_WITH_KR = """\
<?xml version="1.0" encoding="utf-8"?>
<metalink>
  <files>
    <file name="repomd.xml">
      <resources>
        <url protocol="https" type="https" location="KR" preference="100">
          https://mirror.kakao.com/fedora/
        </url>
        <url protocol="https" type="https" location="US" preference="90">
          https://dl.fedoraproject.org/pub/fedora/linux/
        </url>
      </resources>
    </file>
  </files>
</metalink>
"""

_METALINK_XML_US_ONLY = """\
<?xml version="1.0" encoding="utf-8"?>
<metalink>
  <files>
    <file name="repomd.xml">
      <resources>
        <url protocol="https" type="https" location="US" preference="100">
          https://dl.fedoraproject.org/pub/fedora/linux/
        </url>
      </resources>
    </file>
  </files>
</metalink>
"""


@pytest.fixture
def _mock_dnf_variables():
    mock_result = MagicMock()
    mock_result.stdout = _SAMPLE_DNF_DUMP
    with patch(
        "mirrorctl.validation.subprocess.run",
        return_value=mock_result,
    ) as m:
        yield m


class TestGetDnfVariables:
    def test_parses_output(self, _mock_dnf_variables):
        variables = get_dnf_variables()

        assert variables["arch"] == "x86_64"
        assert variables["basearch"] == "x86_64"
        assert variables["releasever"] == "43"
        assert variables["releasever_major"] == "43"

    def test_skips_header_line(self, _mock_dnf_variables):
        variables = get_dnf_variables()
        assert "========" not in variables
        assert "Variables" not in variables

    def test_dnf_not_found(self):
        with patch(
            "mirrorctl.validation.subprocess.run",
            side_effect=FileNotFoundError(),
        ):
            with pytest.raises(ValueError, match="dnf command not found"):
                get_dnf_variables()


class TestResolveDnfVariables:
    def test_basic(self):
        result = _resolve_dnf_variables(
            "repo=test-f$releasever&arch=$basearch",
            {"basearch": "x86_64", "releasever": "43"},
        )
        assert result == "repo=test-f43&arch=x86_64"

    def test_longer_keys_replaced_first(self):
        result = _resolve_dnf_variables(
            "$releasever_major",
            {"releasever": "43", "releasever_major": "99"},
        )
        assert result == "99"

    def test_no_variables_unchanged(self):
        result = _resolve_dnf_variables(
            "no-variables-here", {"basearch": "x86_64"}
        )
        assert result == "no-variables-here"


class TestValidateCountryMirrors:
    def test_valid_country(
        self, sample_repo_group, _mock_dnf_variables
    ):
        mock_response = MagicMock()
        mock_response.text = _METALINK_XML_WITH_KR

        with patch(
            "mirrorctl.validation.httpx.get",
            return_value=mock_response,
        ):
            validate_country_mirrors(sample_repo_group, ["KR"])

    def test_no_mirrors_for_country(
        self, sample_repo_group, _mock_dnf_variables
    ):
        mock_response = MagicMock()
        mock_response.text = _METALINK_XML_US_ONLY

        with patch(
            "mirrorctl.validation.httpx.get",
            return_value=mock_response,
        ):
            with pytest.raises(ValueError, match="No mirrors found"):
                validate_country_mirrors(sample_repo_group, ["KR"])

    def test_http_error(
        self, sample_repo_group, _mock_dnf_variables
    ):
        with patch(
            "mirrorctl.validation.httpx.get",
            side_effect=httpx.ConnectError("connection failed"),
        ):
            with pytest.raises(ValueError, match="Failed to fetch"):
                validate_country_mirrors(sample_repo_group, ["KR"])

    def test_multiple_countries_all_valid(
        self, sample_repo_group, _mock_dnf_variables
    ):
        mock_response = MagicMock()
        mock_response.text = _METALINK_XML_WITH_KR

        with patch(
            "mirrorctl.validation.httpx.get",
            return_value=mock_response,
        ):
            validate_country_mirrors(sample_repo_group, ["KR", "US"])

    def test_multiple_countries_one_invalid(
        self, sample_repo_group, _mock_dnf_variables
    ):
        mock_response = MagicMock()
        mock_response.text = _METALINK_XML_US_ONLY

        with patch(
            "mirrorctl.validation.httpx.get",
            return_value=mock_response,
        ):
            with pytest.raises(ValueError, match="No mirrors found"):
                validate_country_mirrors(
                    sample_repo_group, ["US", "ZZ"]
                )
