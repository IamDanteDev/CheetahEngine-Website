"""Independent latest-release probes (S1-S3)."""

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
FILES = ("index.html", "stats/index.html", "stats.txt")
PREFIX = "https://github.com/Cheetahbrawl291/FNFCheetahEngine/releases/download/"


class LatestReleaseProbe(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        for rel in FILES + ("scripts/update-stats.py",):
            dst = self.root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / rel, dst)

    def payload(self, tag="v-next", names=("CheetahEngine-Windows.zip", "CheetahEngine-Linux.zip")):
        return {
            "tag_name": tag,
            "published_at": "2027-01-02T03:04:05Z",
            "assets": [
                {
                    "name": name,
                    "download_count": 7,
                    "browser_download_url": PREFIX + tag + "/" + name,
                }
                for name in names
            ],
        }

    def run_generator(self, payload=None, raw=None):
        fixture = self.root / "payload.json"
        fixture.write_text(raw if raw is not None else json.dumps(payload), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(self.root / "scripts" / "update-stats.py"), str(fixture)],
            cwd=self.root,
            capture_output=True,
            text=True,
        )

    def hashes(self):
        return {rel: hashlib.sha256((self.root / rel).read_bytes()).hexdigest() for rel in FILES}

    def test_new_tag_baked_for_crawlers(self):  # S1,S2
        result = self.run_generator(self.payload())
        self.assertEqual(
            (result.returncode, result.stderr, result.stdout),
            (0, "", "Total downloads: 14\nLinux: 7\nWindows: 7\nLast update: Jan 2, 2027\n"),
        )
        index = (self.root / "index.html").read_text(encoding="utf-8")
        for name in ("CheetahEngine-Windows.zip", "CheetahEngine-Linux.zip"):
            self.assertIn('data-download="{}" href="{}"'.format(name, PREFIX + "v-next/" + name), index)
        self.assertIn('"softwareVersion": "v-next"', index)
        self.assertNotIn("releases/download/Release/", index)
        before = self.hashes()
        self.assertEqual(self.run_generator(self.payload()).returncode, 0)
        self.assertEqual(self.hashes(), before)

    def test_invalid_asset_urls_reject_without_writes(self):  # S1,S2
        bad = (
            "http://github.com/Cheetahbrawl291/FNFCheetahEngine/releases/download/v-next/CheetahEngine-Windows.zip",
            "https://evil.example/CheetahEngine-Windows.zip",
            PREFIX + "v-next/CheetahEngine-Windows.tar.gz",
            PREFIX + "v-next/CheetahEngine-Windows.zip?x=1",
            123,
        )
        for value in bad:
            with self.subTest(value=value):
                before = self.hashes()
                payload = self.payload()
                payload["assets"][0]["browser_download_url"] = value
                result = self.run_generator(payload)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(
                    result.stderr.strip(),
                    "invalid browser_download_url for CheetahEngine-Windows.zip",
                )
                self.assertEqual(self.hashes(), before)

    def test_missing_url_keeps_previous_href(self):  # S1,S3
        before_index = (self.root / "index.html").read_text(encoding="utf-8")
        previous = re.search(
            r'data-download="CheetahEngine-Windows.zip" href="([^"]+)"', before_index
        ).group(1)
        payload = self.payload()
        del payload["assets"][0]["browser_download_url"]
        result = self.run_generator(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        updated = (self.root / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="{}"'.format(previous), updated)
        self.assertIn(PREFIX + "v-next/CheetahEngine-Linux.zip", updated)

    def test_client_contract(self):  # S3
        index = (REPO / "index.html").read_text(encoding="utf-8")
        self.assertIn("releases/latest", index)
        self.assertNotIn("releases/tags/Release", index)
        self.assertIn("cheetah-release-info-v5", index)
        for name in ("CheetahEngine-Windows.zip", "CheetahEngine-Linux.zip"):
            self.assertIn('data-download="{}"'.format(name), index)

    @unittest.skipUnless(shutil.which("node"), "node unavailable")
    def test_client_runtime_updates_hrefs(self):  # S3
        html = (REPO / "index.html").read_text(encoding="utf-8")
        start = html.index("var nodes = document.querySelectorAll('.dl-count');")
        block_start = html.rfind("(function () {", 0, start)
        block_end = html.index("})();", html.index("statsEl.textContent = 'Unavailable';", start)) + 5
        harness = r'''
const fs=require('fs'),vm=require('vm');
const mk=a=>({attrs:a,getAttribute(k){return this.attrs[k]||null;},setAttribute(k,v){this.attrs[k]=v;},hasAttribute(k){return k in this.attrs;},textContent:''});
const links=[mk({'data-download':'CheetahEngine-Windows.zip','href':'OLD-W'}),mk({'data-download':'CheetahEngine-Linux.zip','href':'OLD-L'})];
const counts=[mk({'data-asset':'CheetahEngine-Windows.zip'}),mk({'data-asset':'CheetahEngine-Linux.zip'})];
const meta=mk({}),api=mk({});
global.document={documentElement:mk({}),querySelectorAll(s){return s==='.dl-count'?counts:links;},getElementById(id){return id==='releaseMeta'?meta:id==='apiString'?api:mk({});}};
let url; global.fetch=u=>{url=u;return Promise.resolve({ok:true,json:()=>Promise.resolve({tag_name:'v-next',published_at:'2027-01-02T03:04:05Z',assets:[{name:'CheetahEngine-Windows.zip',download_count:7,size:1048576,browser_download_url:'https://github.com/Cheetahbrawl291/FNFCheetahEngine/releases/download/v-next/CheetahEngine-Windows.zip'}]})});};
global.window={fetch:global.fetch}; global.localStorage={getItem:()=>null,setItem:()=>{}};
vm.runInThisContext(fs.readFileSync(process.argv[2],'utf8'));
setTimeout(()=>console.log(JSON.stringify({url,hrefs:links.map(x=>x.attrs.href),meta:meta.textContent,api:api.textContent})),50);
'''
        harness_path = self.root / "harness.js"
        client_path = self.root / "client.js"
        harness_path.write_text(harness, encoding="utf-8")
        client_path.write_text(html[block_start:block_end], encoding="utf-8")
        output = subprocess.run(
            ["node", str(harness_path), str(client_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        data = json.loads(output.stdout)
        self.assertEqual(
            data["url"],
            "https://api.github.com/repos/Cheetahbrawl291/FNFCheetahEngine/releases/latest",
        )
        self.assertIn("v-next/CheetahEngine-Windows.zip", data["hrefs"][0])
        self.assertEqual(data["hrefs"][1], "OLD-L")
        self.assertIn("v-next", data["meta"])


if __name__ == "__main__":
    unittest.main()
