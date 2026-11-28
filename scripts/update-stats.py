#!/usr/bin/env python3
"""Regenerate static download links and stats from a GitHub release payload."""

import datetime
import html
import json
import pathlib
import re
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
MARKER = re.compile(r"(<!-- STATS:START -->).*?(<!-- STATS:END -->)", re.DOTALL)
DOWNLOAD_MARKER = re.compile(r"(<!-- DOWNLOADS:START -->)(.*?)(<!-- DOWNLOADS:END -->)", re.DOTALL)
ASSET_NAMES = ("CheetahEngine-Windows.zip", "CheetahEngine-Linux.zip")
VERSION_FIELD = re.compile(r'"softwareVersion"\s*:\s*"[^"]*"')
DOWNLOAD_URL = re.compile(
    r'"https://github\.com/Cheetahbrawl291/FNFCheetahEngine/releases/download/'
    r'[^"]+/CheetahEngine-(?:Windows|Linux)\.zip"'
)
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


def safe_download_url(value):
    """Only accept engine release asset URLs from GitHub over HTTPS."""
    if not isinstance(value, str):
        return None
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme != "https" or parsed.netloc != "github.com":
        return None
    if not parsed.path.startswith("/Cheetahbrawl291/FNFCheetahEngine/releases/download/"):
        return None
    if not parsed.path.endswith(".zip") or parsed.query or parsed.fragment:
        return None
    return value


def asset_urls(payload):
    urls = {}
    for asset in payload.get("assets", []):
        name = asset.get("name")
        if name not in ASSET_NAMES or "browser_download_url" not in asset:
            continue
        url = safe_download_url(asset.get("browser_download_url"))
        if url is None:
            raise SystemExit("invalid browser_download_url for {}".format(name))
        urls[name] = url
    return urls


def rewrite_links(block, urls):
    def anchor_sub(match):
        tag = match.group(0)
        name_match = re.search(r'\bdata-download="([^"]+)"', tag)
        if not name_match:
            return tag
        url = urls.get(name_match.group(1))
        if not url:
            return tag
        escaped = html.escape(url, quote=True)
        href = re.compile(r'\bhref="[^"]*"')
        if href.search(tag):
            return href.sub('href="{}"'.format(escaped), tag, count=1)
        return tag[:-1] + ' href="{}">'.format(escaped)

    return re.sub(r"<a\b[^>]*>", anchor_sub, block)


def rewrite_release_metadata(text, payload, urls):
    tag = payload.get("tag_name")
    if isinstance(tag, str) and tag.strip():
        text = VERSION_FIELD.sub(lambda m: '"softwareVersion": ' + json.dumps(tag.strip()), text, count=1)

    def url_sub(match):
        name_match = re.search(r"CheetahEngine-(?:Windows|Linux)\.zip", match.group(0))
        url = urls.get(name_match.group(0)) if name_match else None
        return json.dumps(url) if url else match.group(0)

    return DOWNLOAD_URL.sub(url_sub, text)


def main():
    source = open(sys.argv[1], encoding="utf-8") if len(sys.argv) > 1 else sys.stdin
    with source:
        payload = json.load(source)
    block = build_block(payload)
    urls = asset_urls(payload)

    updates = []
    for relative in TARGETS:
        path = ROOT / relative
        text = path.read_text(encoding="utf-8")
        updated, count = MARKER.subn(lambda m: m.group(1) + block + m.group(2), text)
        if count != 1:
            raise SystemExit("expected one STATS marker pair in {}, found {}".format(relative, count))

        if relative == "index.html":
            updated, downloads = DOWNLOAD_MARKER.subn(
                lambda m: m.group(1) + rewrite_links(m.group(2), urls) + m.group(3), updated
            )
            if downloads != 1:
                raise SystemExit(
                    "expected one DOWNLOADS marker pair in {}, found {}".format(relative, downloads)
                )
            updated = rewrite_release_metadata(updated, payload, urls)

        updates.append((path, updated, text))

    for path, updated, text in updates:
        if updated != text:
            path.write_text(updated, encoding="utf-8")

    (ROOT / "stats.txt").write_text(block + "\n", encoding="utf-8")
    print(block)


if __name__ == "__main__":
    main()
