"""Regression probes for crawler-visible download stats (S1, S2, S3)."""

import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
TARGETS = ("index.html", "stats/index.html", "stats.txt")


class UpdateStatsTest(unittest.TestCase):
    def setUp(self):
        self._reset_scratch()

    def _reset_scratch(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        for rel in TARGETS + ("scripts/update-stats.py",):
            dst = self.root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / rel, dst)
        self.script = self.root / "scripts" / "update-stats.py"

    def hashes(self):
        return {r: hashlib.sha256((self.root / r).read_bytes()).hexdigest() for r in TARGETS}

    def strip_marker(self, rel):
        path = self.root / rel
        path.write_text(
            path.read_text(encoding="utf-8")
            .replace("<!-- STATS:START -->", "")
            .replace("<!-- STATS:END -->", ""),
            encoding="utf-8",
        )

    def strip_download_marker(self, rel):
        path = self.root / rel
        path.write_text(
            path.read_text(encoding="utf-8")
            .replace("<!-- DOWNLOADS:START -->", "")
            .replace("<!-- DOWNLOADS:END -->", ""),
            encoding="utf-8",
        )

    def run_script(self, payload=None, raw=None):
        fixture = self.root / "payload.json"
        fixture.write_text(raw if raw is not None else json.dumps(payload), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(self.script), str(fixture)],
            cwd=self.root,
            capture_output=True,
            text=True,
        )

    def test_s1_static_block_and_exact_stdout(self):
        payload = {
            "published_at": "2026-12-31T23:59:00Z",
            "assets": [
                {"name": "CheetahEngine-Linux.zip", "download_count": 1234567},
                {"name": "CheetahEngine-Windows.zip", "download_count": 89},
            ],
        }
        result = self.run_script(payload=payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout,
            "Total downloads: 1,234,656\nLinux: 1,234,567\nWindows: 89\nLast update: Dec 31, 2026\n",
        )
        for rel in TARGETS:
            text = (self.root / rel).read_text(encoding="utf-8")
            self.assertIn("Total downloads: 1,234,656", text)
            self.assertIn("Last update: Dec 31, 2026", text)
        self.assertEqual((self.root / "stats.txt").read_text(encoding="utf-8"), result.stdout)

    def test_s1_zero_missing_os_and_timezone(self):
        result = self.run_script(payload={"published_at": "2026-01-02T12:00:00Z", "assets": []})
        self.assertEqual(
            result.stdout,
            "Total downloads: 0\nLinux: 0\nWindows: 0\nLast update: Jan 2, 2026\n",
        )
        result = self.run_script(
            payload={
                "published_at": "2026-03-04T09:00:00Z",
                "assets": [{"name": "Other.zip", "download_count": 9}],
            }
        )
        self.assertEqual(
            result.stdout,
            "Total downloads: 9\nLinux: 0\nWindows: 0\nLast update: Mar 4, 2026\n",
        )
        result = self.run_script(payload={"published_at": "2026-01-02T23:30:00-05:00", "assets": []})
        self.assertIn("Last update: Jan 2, 2026", result.stdout)

    def test_s1_rejected_inputs_leave_files_identical(self):
        before = self.hashes()
        self.assertNotEqual(self.run_script(raw='{"published_at": BROKEN').returncode, 0)
        self.assertEqual(self.hashes(), before)
        self.assertNotEqual(self.run_script(payload={"assets": []}).returncode, 0)
        self.assertEqual(self.hashes(), before)

    def test_missing_marker_rejects_before_any_write(self):
        for rel in ("index.html", "stats/index.html"):
            with self.subTest(rel=rel):
                self._reset_scratch()
                self.strip_marker(rel)
                before = self.hashes()
                result = self.run_script(
                    payload={"published_at": "2026-01-01T00:00:00Z", "assets": []}
                )
                self.assertEqual(result.returncode, 1)
                self.assertEqual(
                    result.stderr.strip(),
                    "expected one STATS marker pair in {}, found 0".format(rel),
                )
                self.assertEqual(self.hashes(), before)

    def test_s1_idempotent(self):
        payload = {"published_at": "2026-11-22T00:00:00Z", "assets": []}
        self.assertEqual(self.run_script(payload=payload).returncode, 0)
        before = self.hashes()
        self.assertEqual(self.run_script(payload=payload).returncode, 0)
        self.assertEqual(self.hashes(), before)

    def test_s2_workflow_and_clean_urls(self):
        workflow = (REPO / ".github" / "workflows" / "update-stats.yml").read_text(encoding="utf-8")
        for token in (
            "schedule:",
            "release:",
            "repository_dispatch:",
            "workflow_dispatch:",
            "contents: write",
            "group: update-stats",
            "git add index.html stats.txt stats/index.html",
            "git diff --cached --quiet",
            "git push origin main",
        ):
            self.assertIn(token, workflow)
        for rel in ("stats/", "stats.txt"):
            for name in ("sitemap.xml", "llms.txt"):
                self.assertIn(
                    "CheetahEngine-Website/" + rel,
                    (REPO / name).read_text(encoding="utf-8"),
                )


    def latest_payload(self, names=("CheetahEngine-Windows.zip", "CheetahEngine-Linux.zip")):
        urls = {
            "CheetahEngine-Windows.zip": "https://github.com/Cheetahbrawl291/FNFCheetahEngine/releases/download/27-nov-2026/CheetahEngine-Windows.zip",
            "CheetahEngine-Linux.zip": "https://github.com/Cheetahbrawl291/FNFCheetahEngine/releases/download/27-nov-2026/CheetahEngine-Linux.zip",
        }
        return {
            "tag_name": "27-nov-2026",
            "published_at": "2026-11-28T01:55:07Z",
            "assets": [
                {
                    "name": name,
                    "download_count": index + 1,
                    "browser_download_url": urls[name],
                }
                for index, name in enumerate(names)
            ],
        }

    def test_latest_release_urls_are_baked_for_crawlers(self):
        payload = self.latest_payload()
        result = self.run_script(payload=payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        index = (self.root / "index.html").read_text(encoding="utf-8")
        for asset in payload["assets"]:
            self.assertIn('data-download="{}"'.format(asset["name"]), index)
            self.assertIn(asset["browser_download_url"], index)
        self.assertIn('"softwareVersion": "27-nov-2026"', index)
        self.assertNotIn("releases/download/Release/", index)

    def test_latest_url_rewrite_is_idempotent(self):
        payload = self.latest_payload()
        self.assertEqual(self.run_script(payload=payload).returncode, 0)
        before = self.hashes()
        result = self.run_script(payload=payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.hashes(), before)

    def test_missing_asset_keeps_previous_download_link(self):
        first = self.run_script(payload=self.latest_payload())
        self.assertEqual(first.returncode, 0, first.stderr)
        index = (self.root / "index.html").read_text(encoding="utf-8")
        windows_url = next(
            a["browser_download_url"]
            for a in self.latest_payload()["assets"]
            if a["name"] == "CheetahEngine-Windows.zip"
        )
        linux_url = next(
            a["browser_download_url"]
            for a in self.latest_payload()["assets"]
            if a["name"] == "CheetahEngine-Linux.zip"
        )
        result = self.run_script(payload=self.latest_payload(("CheetahEngine-Windows.zip",)))
        self.assertEqual(result.returncode, 0, result.stderr)
        updated = (self.root / "index.html").read_text(encoding="utf-8")
        self.assertIn(windows_url, updated)
        self.assertIn(linux_url, updated)

    def test_unsafe_asset_url_is_rejected_before_any_write(self):
        before = self.hashes()
        payload = self.latest_payload()
        payload["assets"][0]["browser_download_url"] = "https://evil.example/malware.zip"
        self.assertNotEqual(self.run_script(payload=payload).returncode, 0)
        self.assertEqual(self.hashes(), before)

    def test_missing_download_marker_rejects_before_any_write(self):
        self.strip_download_marker("index.html")
        before = self.hashes()
        result = self.run_script(payload=self.latest_payload())
        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            result.stderr.strip(),
            "expected one DOWNLOADS marker pair in index.html, found 0",
        )
        self.assertEqual(self.hashes(), before)

    def test_workflow_uses_latest_release(self):
        workflow = (REPO / ".github" / "workflows" / "update-stats.yml").read_text(encoding="utf-8")
        self.assertIn("releases/latest", workflow)
        self.assertNotIn("releases/tags/Release", workflow)

    def test_client_uses_latest_release_with_static_fallback(self):
        index = (REPO / "index.html").read_text(encoding="utf-8")
        self.assertIn("<!-- DOWNLOADS:START -->", index)
        self.assertIn("<!-- DOWNLOADS:END -->", index)
        self.assertIn('data-download="CheetahEngine-Windows.zip"', index)
        self.assertIn('data-download="CheetahEngine-Linux.zip"', index)
        self.assertIn("/releases/latest", index)
        self.assertNotIn("/tags/Release", index)


if __name__ == "__main__":
    unittest.main()
