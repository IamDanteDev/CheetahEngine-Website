# Latest GitHub release downloads

Objective: make the site's Downloads section use the newest GitHub release instead of the fixed `Release` tag. Branch: `feature/latest-release-downloads`. Delivery: reviewable work-unit commits, no push/PR/merge. Checks: `python3 -m unittest discover -s tests -v`, live payload generator run, `node --check` on inline JS, YAML/XML parse, raw HTTP GET.

## Specs

S1. "puedes hacer que la web muestre el least subido a github en lugar de uno fijo en el de downloads" — the Windows and Linux download links must point to the assets of the most recently published non-draft, non-prerelease GitHub release, not to the fixed `Release` tag. Technical artifacts and UI copy stay in English.

S2. The values must be crawler-visible in the initial HTML, matching the existing static-stats approach: generator and workflow refresh the same static files, and a plain HTTP GET of the site contains the latest release's URLs and stats with no JavaScript.

S3. Client-side rendering must read the same `/releases/latest` payload, update the visible links and release metadata, and keep the existing fallback behavior when the API is unavailable. Existing stats strings, `/stats.txt`, `/stats/` and sitemap/llms links stay intact.

S4. Standing constraints from prior work: site content in English, user-facing chat in Spanish; no new site sections; no push, PR or merge in this task. Engram mirror pending: `mem_current_project` for this workspace returned ambiguous (`cheetahengine-website`, `temprepo`), so no project-scoped mirror was written.

## Tasks

T1 | S1,S2 | inline | done | e4a84c0 — tests first (RED 6/13 failures), generator + workflow; 13/13 GREEN
T2 | S1,S3 | inline | done | e4a84c0 — index.html markers, data-download links, JSON-LD and inline JS latest-release rendering
T3 | S1-S4 | inline | in progress | 4d0cd62 — live payload regeneration and local checks pass; independent verifier S1-S4 MET, no blockers; 18/18 GREEN with durable probes; native review and push to origin/main pending (publish authorized by user)

## Log

L1. 2026-11-28 — user request verbatim: "puedes hacer que la web muestre el least subido a github en lugar de uno fijo en el de downloads".

L2. 2026-11-28 — evidence: site repository is the parent checkout `/home/dante/Descargas/FNF-CheetahEngineDevbuildv1`; `index.html:23-24,169` hardcodes `releases/download/Release/...`, `index.html:21` sets `softwareVersion: "Release"`, and `index.html:274` fetches `releases/tags/Release`. `scripts/update-stats.py` bakes STATS markers and `.github/workflows/update-stats.yml` feeds it from that same fixed tag. GitHub `GET /repos/Cheetahbrawl291/FNFCheetahEngine/releases/latest` (read-only, unauthenticated) returned tag `27-nov-2026`, published `2026-11-28T01:55:07Z`, with `CheetahEngine-Windows.zip` and `CheetahEngine-Linux.zip` assets. Route: inline; no Writer trigger (one behavior, no parallel units). Risk: item 5 (CI/deploy), so an independent verifier is required after local checks.

L3. 2026-11-28 — local evidence: RED was 13 tests with 6 failures before implementation; GREEN is 13/13 OK after adding `DOWNLOADS` markers, `data-download` anchors, URL validation, generator rewrites and the `/releases/latest` workflow endpoint. Live payload regeneration baked `27-nov-2026` URLs and `softwareVersion` into index.html with zero remaining fixed download links; second run byte-identical; raw local HTTP GET contains both latest zips. Inline JS passed `node --check` (2 blocks), workflow YAML parsed, sitemap XML parsed. RDD is on (global). User authorized publishing to the website repo; `origin` is `https://github.com/IamDanteDev/CheetahEngine-Website.git`, `Game/` is not tracked there (0 files), and Pages content is served from `main`.

L4. 2026-11-28 — consequence disclosed: the latest release's assets currently have `download_count: 0`, so the baked stats now read `Total downloads: 0 / Linux: 0 / Windows: 0` for tag `27-nov-2026` instead of the old `Release` tag counts. This follows from sourcing all values from the latest release; no aggregation across releases was requested.

L5. 2026-11-28 — independent verifier (`gentle-ai-verify`) returned S1-S4 MET, no blockers. It confirmed crawler-visible `27-nov-2026` URLs and JSON-LD, byte-identical rejection of unsafe/missing URLs, unchanged workflow triggers and stats paths, runtime `/releases/latest` with `v5` cache and intact fallback, and no push/PR/merge. Advisories reproduced on baseline: `llms.txt` still mentions the old API tag and v4 cache key; not download URLs and left unchanged to avoid scope expansion.

L6. 2026-11-28 — durable probes added in `tests/test_latest_release_probes.py` after correcting two harness defects from the verifier's suggested code: the Node harness must read `process.argv[2]` (client path) and the client block must stop at the release IIFE's own `})();`, not the star-count IIFE's. Full suite: 18/18 OK. Work units committed locally: `e4a84c0` (behavior + original tests), `4d0cd62` (independent probes + document). Pre-existing `odd/tasks/crawler-visible-download-stats.md` modification and `.atl/` stayed unstaged.
