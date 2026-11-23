# Crawler-visible download stats
Objective: make download counts and last update readable by crawlers without JavaScript. Branch: main. Delivery: ask-on-risk. Checks: python script, YAML parse, Chrome headless.

## Specs

### S1
"la IA de google en la busqueda no puede verla me dice: No, todavía no me carga el número de descargas. Lo que recibe se comporta así por dos motivos técnicos: • Desde tu pestaña abierta: El texto que me llega de tu navegador sigue mostrando la plantilla base estática con el mensaje Loading.... El lector extrae el DOM inicial de la página antes de que tu script termine de hacer la petición a GitHub y reemplace el texto en pantalla (o si el elemento donde inyectas ?stats=total está oculto por CSS, tampoco lo lee). • Al intentar abrir el enlace directamente: Como la URL exacta con ?stats=total es nueva, aún no está en el índice web y mi herramienta de navegación directa no puede cargarla de forma independiente (The URL is not in the search index)."

Acceptance: a plain HTTP GET of the published site returns real numbers in the initial HTML, never `Loading...` as the only value.

### S2
User selected: "GitHub Actions (Recommended)" — "Workflow actualiza diariamente y en cada release un stats.txt y el bloque de números del index.html, con commit automático. Rutas limpias /stats.txt y /stats/ en el sitemap. Se actualiza solo, pero toca el pipeline de deploy."

Acceptance: scheduled, release and manual triggers regenerate static stats and commit only when values changed.

### S3
Prior constraints still apply: strings show total downloads, per-system downloads and last update; site content in English; user-facing chat in Spanish; no new site sections beyond a small stats link.

## Tasks

- T1 S1,S3 — inline — static marker block in index.html, /stats.txt, /stats/index.html, sitemap + llms.txt links — done; raw HTTP GET of /, /stats/ and /stats.txt returns the four real lines
- T2 S2 — inline — scripts/update-stats.py, .github/workflows/update-stats.yml and tests/test_update_stats.py — done; generator run against live payload, synthetic cases, byte-idempotence, YAML/XML parse and 6 regression tests verified; independent verifier returned S1/S2/S3 MET

## Log

### L1
la IA de google en la busqueda no puede verla me dice: No, todavía no me carga el número de descargas. Lo que recibe se comporta así por dos motivos técnicos:
• Desde tu pestaña abierta: El texto que me llega de tu navegador sigue mostrando la plantilla base estática con el mensaje Loading.... El lector extrae el DOM inicial de la página antes de que tu script termine de hacer la petición a GitHub y reemplace el texto en pantalla (o si el elemento donde inyectas ?stats=total está oculto por CSS, tampoco lo lee).
• Al intentar abrir el enlace directamente: Como la URL exacta con ?stats=total es nueva, aún no está en el índice web y mi herramienta de navegación directa no puede cargarla de forma independiente (The URL is not in the search index).
Si quieres ver qué está pasando exactamente cuando se ejecuta en tu navegador, puedes pegarme el fragmento de código JS que procesa ?stats=total o una captura de cómo se ve en tu pantalla.
Si te sirve, puedes pegar el código JS de ese parámetro o subir una captura de pantalla de la página cargada para revisar cómo se está renderizando.

### L2
2026-11-23 — User chose "GitHub Actions (Recommended)" for static crawler-visible stats.

### L3
2026-11-23 — Route: inline for both tasks. No writer trigger (one behavior, no parallel units, context within budget). Baseline HEAD c9a5a02. Risk: item 5 (CI/deploy), independent verifier launched after local checks. No work-unit commit yet: user has not authorized a commit or push for this change.

### L4
2026-11-23 — Evidence: live release payload generated `Total downloads: 13 / Linux: 5 / Windows: 8 / Last update: Nov 22, 2026`. Synthetic Linux=1234 produced `1,242` total and `1,234` Linux; real payload restored values; second run byte-identical. `node --check` passed on both inline JS blocks, sitemap.xml parsed, workflow YAML parsed with four triggers. Raw local HTTP GET of /, /stats/ and /stats.txt contains real numbers in initial HTML.

### L5
2026-11-23 — Independent verifier (gentle-ai-verify) returned S1 MET, S2 MET (static config), S3 MET. Baseline c9a5a02. Advisory fixed: generator now validates all STATS marker pairs before any write, so a missing marker in the second target cannot leave index.html partially rewritten. Advisory fixed: workflow has `concurrency: group: update-stats, cancel-in-progress: false` to prevent overlapping pushes. Remaining advisories accepted: `release:` triggers on the website repo (engine releases refresh via daily schedule or `repository_dispatch: engine-release`); Python and browser local timezones can differ on a boundary day. Live GitHub Actions execution remains unverified locally; a manual `workflow_dispatch` run after push is the check.

### L6
2026-11-23 — Added tests/test_update_stats.py from the verifier's durable probes, adjusted for the marker-validation fix. `python3 -m unittest discover -s tests -v`: 6 tests, OK. Verifier scratch dirs /tmp/opencode/oddverify-cur.HauZaa and /tmp/opencode/oddverify-base.b6M2to removed by parent.
