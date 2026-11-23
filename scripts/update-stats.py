#!/usr/bin/env python3
"""Regenerate static download-stat files from a GitHub release payload."""

import datetime
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MARKER = re.compile(r"(<!-- STATS:START -->).*?(<!-- STATS:END -->)", re.DOTALL)
TARGETS = ("index.html", "stats/index.html")


def build_block(payload):
    counts = {asset["name"]: asset["download_count"] for asset in payload.get("assets", [])}
    published = datetime.datetime.fromisoformat(payload["published_at"].replace("Z", "+00:00"))
    return "\n".join(
        [
            "Total downloads: {:,}".format(sum(counts.values())),
            "Linux: {:,}".format(counts.get("CheetahEngine-Linux.zip", 0)),
            "Windows: {:,}".format(counts.get("CheetahEngine-Windows.zip", 0)),
            "Last update: {} {}, {}".format(published.strftime("%b"), published.day, published.year),
        ]
    )


def main():
    source = open(sys.argv[1], encoding="utf-8") if len(sys.argv) > 1 else sys.stdin
    with source:
        block = build_block(json.load(source))

    updates = []
    for relative in TARGETS:
        path = ROOT / relative
        text = path.read_text(encoding="utf-8")
        updated, count = MARKER.subn(lambda m: m.group(1) + block + m.group(2), text)
        if count != 1:
            raise SystemExit("expected one STATS marker pair in {}, found {}".format(relative, count))
        updates.append((path, updated, text))

    for path, updated, text in updates:
        if updated != text:
            path.write_text(updated, encoding="utf-8")

    (ROOT / "stats.txt").write_text(block + "\n", encoding="utf-8")
    print(block)


if __name__ == "__main__":
    main()
