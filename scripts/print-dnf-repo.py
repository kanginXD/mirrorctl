#!/usr/bin/env python3

import json
import re
from pathlib import Path

REPO_DIR = "/etc/yum.repos.d"
PATTERN = "*.repo"

repo_re = re.compile(r"^\[(.+?)\]")
baseurl_re = re.compile(r"^#\s*baseurl=(.+)")
metalink_re = re.compile(r"^metalink=(.+)")
mirrorlist_re = re.compile(r"^mirrorlist=(.+)")


def parse():
    repos = []
    current = None

    for path in Path(REPO_DIR).glob(PATTERN):
        for line in path.read_text().splitlines():
            line = line.strip()

            m = repo_re.match(line)
            if m:
                current = {
                    "repo_id": m.group(1),
                    "baseurl_format": None,
                    "metalink_format": None,
                    "mirrorlist_format": None,
                }
                repos.append(current)
                continue

            if not current:
                continue

            if not current["baseurl_format"]:
                m = baseurl_re.match(line)
                if m:
                    current["baseurl_format"] = m.group(1)
                    continue

            m = metalink_re.match(line)
            if m:
                current["metalink_format"] = m.group(1)
                continue

            m = mirrorlist_re.match(line)
            if m:
                current["mirrorlist_format"] = m.group(1)

    return repos


if __name__ == "__main__":
    print(json.dumps(parse(), indent=2))
