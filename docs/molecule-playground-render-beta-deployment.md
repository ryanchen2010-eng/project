# Molecule Playground — Render beta deployment preparation (Phase 5I)

Prepared 2026-10-19, America/Toronto. This is a regular browser website; no Wix, mobile app conversion, database or new chemistry.

| State | Result |
| --- | --- |
| Deployment configuration prepared | Yes: one Docker web service, manual deployments, existing password protection. |
| Awaiting authorization | Yes: source upload/push and initial Render creation/deployment. |
| Actually deployed | **No.** No account or hosting service was changed. |
| Live website verified | **Pending.** Localhost results are not Render verification. |
| Live beta URL | **None created.** |

## 1. Existing architecture inspected

The current project is a Vite/TypeScript multi-page application: `index.html`, `explore.html`, `builder.html`, `reaction-lab.html`, and `calculators.html`. `vite.config.ts` already includes all five production entries. It is not an SPA that requires unknown URLs to fall back to Home; direct page URLs and hash-based calculator topics are the actual routing model. Missing routes remain 404.

Frontend requests already use relative same-origin `/api/...` URLs. The loopback `127.0.0.1:8000` proxy belongs only to Vite's local development server, not the compiled client. `start-local.command` remains the development launcher and was not changed.

The Python/RDKit chemistry implementation is exposed by the existing Flask `server.production_app:create_app()` gateway under Gunicorn. The older `ThreadingHTTPServer` in `chemistry_server.py` is local-development-only and is not the deployment command. The production gateway serves authenticated built files from `dist/` and handles the chemistry, reaction, inspection and PubChem routes itself.

Ketcher and its standalone chemistry engine are bundled locally by Vite; Builder uses `staticResourcesUrl: '/'`. 3Dmol.js is loaded from its existing official HTTPS CDN. Curated SDFs are copied from `public/molecules/`. PubChem requests go from the hosted backend to the fixed HTTPS NCBI endpoint, with bounded/cacheable lookups, a 10-second individual upstream timeout and clear unavailable responses.

No browser-side production API request needs localhost, a separate backend hostname, CORS wildcard or a separate service. Source files, benchmarks, environments and credentials are not public static content.

## 2. Architecture selected

**One Render Docker web service** serves all five pages and `/api` from the same HTTPS origin. Build Node assets in a first Docker stage, then run only the Python gateway/RDKit and built assets in the final image. Render terminates TLS. No Node/Vite development server is run in production.

This reuses the existing private-trial gateway rather than replacing it. One shared beta password is sufficient for this small trial; no individual accounts or database were added. Friends use a browser and the eventual URL. Unlisted is not private: the existing authentication is retained.

## 3. Files added or modified

Modified deployment/runtime configuration:

- `Dockerfile`: include **all** existing Python runtime modules, Linux native libraries needed by the wheel/drawing stack, binary-wheel installation, bounded numeric-library threads and a build-time import/24-pathway smoke check. Non-root execution, multi-stage build and explicit copies remain.
- `.dockerignore`: allow the Python module files required by the current engine while retaining deny-by-default behavior and credential/history/environment exclusions.
- `server/requirements-production.txt`: pin already-used transitive packages to the versions exercised locally. No new runtime package or chemistry model was introduced.
- `server/gunicorn.conf.py`: one synchronous worker, one thread, the existing 90-second timeout and bounded worker recycling. A sync worker makes timeout an actual stuck-worker restart bound; a threaded worker heartbeat is not a per-request hard deadline. Normal requests can queue; this is deliberately a small beta, not a scalable job service.
- `server/production_app.py`: use Render's actual supplied external URL when an explicit origin is absent; default standalone frame policy to that exact origin; remove the obsolete Wix-only login hint; fix the form's Referrer-Policy without accepting missing/null/cross-origin requests.
- `vite.config.ts`: transform mixed ESM/CommonJS dependencies so Ketcher's Raphael require call is included in the browser bundle.
- `.gitignore`: ignore local `releases/` artifacts.

Added: `render.yaml`, `scripts/prepare_beta_release.py`, `tests/test_render_beta.py`, this report and `docs/render-beta-friend-guide.md`. Browser screenshots are verification artifacts, not website assets.

### Two production-only blockers found and fixed

The old image copied only five Python files, omitting most current reaction rules and confidence/mapping modules. It could not represent the current product. The image now includes every root-level Python runtime module and checks imports/catalog startup while building.

A real browser opening the original production Builder failed with `ReferenceError: require is not defined` at Ketcher's Raphael load. Vite's mixed-module transformation fixed it; a newly drawn carbon–carbon bond then generated an ethane 3D model, with a passed structure check and MMFF94 shown.

The login form also exposed a deployment blocker: `no-referrer` can produce a null Origin on ordinary form POSTs. Only the login form document now uses `same-origin`; other responses retain `no-referrer`. Exact Origin checking, secure signed cookies and denial of null/cross-origin POSTs remain intact. Sign-in and sign-out were retested after removing the temporary null-Origin test workaround. See the [Fetch Standard's Origin algorithm](https://fetch.spec.whatwg.org/#append-a-request-origin-header).

No reaction rule, molecule collection, calculator formula, reagent permission, mapped edit or layout was changed.

## 4. Render configuration

`render.yaml` defines one `type: web`, `runtime: docker` service, named `molecule-playground-beta-v1`, with the **Free** compute plan, Ohio region, root build context, `Dockerfile`, `/healthz` and `autoDeployTrigger: "off"`. The Docker CMD starts Gunicorn; do not supply a Vite/npm development start command or a second Python server.

Gunicorn binds `0.0.0.0:$PORT`, default 10000. Only valid unprivileged ports are accepted. Health is unauthenticated/minimal and depends on imported backend plus built Home assets. The configured public Host must match the Render hostname; if adding a custom domain later, update the explicit origin/frame settings consistently. [Render documents the health-check Host behavior](https://render.com/docs/health-checks).

The Blueprint passed local validation against Render's published JSON schema using existing YAML/Ajv libraries. The validator's unused URI-format warning does not affect any submitted field. Account-side validation and an actual Docker build remain pending. [Blueprint fields and defaults](https://render.com/docs/blueprint-spec).

**Turning auto-deploy off does not prevent the initial deployment when a service/Blueprint is created. Do not click Create/Apply until publication is explicitly authorized.**

## 5. Required environment variables

| Variable | Setting |
| --- | --- |
| `CAPSTONE_TRIAL_PASSWORD` | Owner supplies a new private beta password, 12–256 characters, no surrounding whitespace. Required; no value is in Git or the image. |
| `CAPSTONE_SESSION_SECRET` | Owner supplies at least 32 cryptographically random bytes encoded as 64+ hex characters. Required; persist it across restarts. Render's base64 `generateValue` format is deliberately not used. |
| `RENDER_EXTERNAL_URL` | Render supplies its actual generated HTTPS URL. Used only if `CAPSTONE_PUBLIC_ORIGIN` is absent; never guessed. |
| `CAPSTONE_PUBLIC_ORIGIN` | Optional explicit exact HTTPS origin, normally needed only for a verified custom domain. No paths, tokens, wildcards or localhost. Invalid explicit values fail rather than falling back. |
| `CAPSTONE_FRAME_ANCESTORS` | Optional for this standalone beta; defaults to the exact public origin. Only add exact HTTPS parent origins if embedding is deliberately enabled later. |
| `PORT` | Provided by Render; the image default is 10000. Do not set an arbitrary local port in the dashboard. |

The image sets `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`, and numeric-library thread limits to 1. No PubChem key is required. No `VITE_API_URL` is needed: API calls are relative.

Generate a session secret locally if needed with `python3 -c 'import secrets; print(secrets.token_hex(32))'`, then enter it directly into Render's secret environment field. Do not paste secrets into chat, YAML, a commit, a build argument or a shared guide. The owner should enter new authentication credentials themselves.

The existing password gate fails closed if credentials or a valid origin are absent. Changing the shared password or session secret invalidates old signed sessions. Sessions last one hour; a service restart with unchanged secrets does not require a database.

## 6. Hosting resources, costs and operational limits

Current official compute specifications list Free as 512 MB RAM / 0.1 CPU. The live pricing page showed $0 Free, $7/month for 0.5 CPU / 512 MB, and $25/month for 1 CPU / 2 GB. Paid workspace subscriptions are separate; no paid plan is required merely to prepare this beta, and none was purchased. Prices are USD as observed 2026-10-19, not a quote. [Compute specifications](https://render.com/docs/compute-plans), [current pricing](https://render.com/pricing).

Free instances sleep after 15 idle minutes, take about a minute to wake, share 750 free hours per workspace/month and have ephemeral local storage. Usage limits also apply to build minutes, bandwidth and unusual outbound traffic; billing or suspension depends on the account/payment settings. No keep-awake workaround is configured. [Free service limits](https://render.com/docs/free).

Local macOS point-in-time summed RSS samples for the Gunicorn parent/worker were approximately **102 MiB** after startup/early lookup and **96 MiB** after Builder/PubChem/guided chemistry. These are not peak Linux container measurements; shared pages can be counted twice, macOS memory behavior differs, and a 0.1 CPU quota was not emulated. They support a **monitored small Free trial**, not a guarantee of fitting every allowed workload within 512 MB. Cache-heavy or unusually expensive chemistry still needs hosted measurement. The app serializes production jobs and bounds request/structure sizes; it does not promise concurrent classroom capacity.

Linux x86-64/Python 3.12 wheels were successfully downloaded from PyPI for all pinned production dependencies, including RDKit 2026.3.6. They were not installed or executed in a Linux container here. Docker/Podman is absent; no virtual machine or container runtime was installed. The actual container build/import/native-library check is still required before treating deployment as verified.

The compressed Builder JS is about 8.1 MiB (28 MiB uncompressed). Private responses intentionally use no-store, so reloads consume bandwidth; the live Hobby pricing page showed 5 GB included. Browser download time and device-side Ketcher/WebGL memory are separate from server RAM. A $7 service removes free sleeping/CPU limitations but **does not increase 512 MB RAM**; if hosted memory is insufficient, evaluate a larger-memory option with the owner before paying.

## 7. Source protection and beta release identity

Original branch: `codex/step-3-reaction-lab`. Original HEAD: `fa00ac9acc75b82e0df4e57148755a904dc80cec`. The tree already contained extensive modified and untracked work, including nearly all later chemistry phases. That old commit by itself is **not** the current beta.

Configured origin remote, read locally: `git@github.com:ryanchen2010-eng/capstone-project.git`. Current remote contents, repository visibility and signed-in GitHub permissions were not assumed or changed.

Before configuration edits, a recovery source archive was made at `/private/tmp/capstone-phase5i-before.gZS1Pi/molecule-playground-before-phase5i.tar.gz`, excluding credentials/local environments. A pre-edit hash inventory records 378 existing files. No reset, deletion, staging, commit, branch switch, tag overwrite or push occurred.

The equivalent frozen beta source snapshot is prepared by `scripts/prepare_beta_release.py` under ignored `releases/molecule-playground-beta-v1/`. Its `manifest.json` records the base commit, dirty-source flag, exact per-file hashes and archive SHA-256. This is a local **candidate**, not a GitHub release or uploaded image. The write-once script refuses an existing name, paths, symlinks and credential-pattern inputs. It packages an explicit runtime allowlist, not the whole worktree; Git metadata, tests, history, docs, `.env`, keys and local environments are not deployment inputs.

Local development cannot mutate bytes already in that archive. After authorization, publish a reviewed beta branch/commit from these exact runtime bytes (suggested branch: `codex/molecule-playground-beta-v1`), record its actual new commit SHA and select it in Render. Do not point Render at the old HEAD or blindly stage the whole dirty tree. Keep auto-deploy off and manually deploy only a reviewed SHA. For later candidates use a new release name; never overwrite beta-v1 or an existing tag. External PubChem data, the existing 3Dmol CDN and base-image patch tags can evolve; this is a source freeze, not a claim of bit-identical third-party infrastructure.

## 8. Local production verification

Verification used the **built/precompressed assets and real Gunicorn/Flask/RDKit gateway**, not Vite's dev server. It bound only `127.0.0.1:10456` for the local check. The production configuration's `0.0.0.0:$PORT` behavior is separately tested.

Because the real gateway requires an HTTPS origin and secure cookies, a temporary non-shipping loopback-only WSGI adapter translated the local Host and exact HTTP Origin to a synthetic HTTPS test origin. The final adapter did **not** accept missing/null/cross-origin headers and did not weaken production validation. This simulates ingress for local UI verification; it does not prove Render TLS, proxy behavior, external browser cookies or Linux execution. No security warning was bypassed and no machine certificate was installed.

| Local check | Observed result |
| --- | --- |
| All five pages/navigation/direct refresh | Passed in the in-app Chromium browser, including calculator hash routing. Unknown routes remain 404 in gateway tests. |
| Password gate | Sign-in and sign-out passed after the real form-policy fix; automated tests reject null/cross-origin requests and invalid/missing secrets. |
| Live PubChem | Searching propanal returned its exact record, 58.08 g/mol and an available model. No fixture substituted for this browser lookup. |
| 3Dmol.js | Existing water/propanal models and generated chemistry product views loaded. |
| Ketcher | Fixed production bundle initialized; a newly drawn C–C molecule produced C2H6, 30.070 g/mol, eight explicit 3D atoms, seven bonds, Passed/MMFF94. |
| Secondary guide | Review showed Water conflict, consent was required, settings applied and backend rematched; separate Compare generated acetone. |
| Linked 2D/3D selection | Selecting acetone Carbon 2 selected mapped reactant/product occurrences and displayed linked-in-3D status. |
| Lindlar guide | Partial propyne option initially blocked under metal activation; explicit review/consent replaced it with Lindlar, then a separate generation action produced propene. |
| Calculator | 18.015 g of selected water gave 1 mol and 6.02214e+23 molecules; negative input replaced the result with a validation message. |
| Unsupported/invalid requests | Existing tests cover forged permissions, A105/A276 restrictions, malformed chemistry, wrong conditions, oversized requests, authentication and protected static paths. Browser negative calculator and conditional Lindlar controls were also checked. |
| Mobile viewport | All five pages at 390×844 had 390 px document width, visible page headings and working direct loads/refreshes. Not a real phone/browser matrix or a complete touch-drawing test. |
| Console/server behavior | The original Builder require error was reproduced and fixed. No new error-level browser entry appeared during the subsequent core workflows. Expected validation errors are not unexpected server failures. |

Screenshots: [production Builder](render-beta-builder-production.png), [linked reaction](render-beta-reaction-production.png), [mobile Calculator](render-beta-mobile-calculators.png). Actual Safari/Chrome device testing and full hosted touch behavior are pending.

## 9. Regression and benchmark verification

All 3,754 existing tests are preserved. New deployment-only tests cover Render origin defaults/failure cases, login form policy/CSRF, all Python module packaging, sync-worker timeout/port settings, manual/free Blueprint fields, Ketcher conversion and write-once secret-excluding snapshots. No old test or frozen expectation was edited.

The unchanged 347-case audit has **zero changed result rows** versus Phase 5H: 155 Fully supported, 63 Partial, 90 Unsupported, 38 correctly rejected controls and the one existing A304 benchmark-defect classification. A105 and A276 remain Partial. The benchmark source SHA remains `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`. The registry remains 24 pathway types; the curated catalog remains 20 examples, not 347 audit fixtures.

The immutable companion stays v1.0.0: 40/53 structural matches, no newly approved condition-complete/product/independent-chemistry cases; diagnostic overlay 33 model-only generations. Version comparison reports no case/profile/defect changes. Existing public API, linked mapping, mechanism, both-guidance and calculator fixtures are included in the full suites.

TypeScript and Vite production build pass. Latest frontend build: 18.95 seconds, with the existing large-chunk warning. Asset precompression passes. Final test totals and preservation results are recorded in the verification addendum below. Whitespace checks apply to all edited/new text files, not just already-tracked files.

## 10. Security and reliability review

Scoped filename/token scans found no tracked deployment `.env`/private-key files or high-confidence key/token patterns in the allowlisted runtime snapshot. This is not a claim of a comprehensive third-party vulnerability or penetration audit. Known synthetic test credentials are not deployed.

The image excludes Git/history/secrets, runs as non-root, serves only `dist`, and cannot return source/hidden files or outside symlinks through static routing. Authentication protects static assets and APIs; `/healthz` is intentionally minimal. Host allowlisting, exact POST Origin, secure HttpOnly signed one-hour cookies, no-store responses, noindex and process-local rate limits remain. No wildcard CORS, debug server, database or public-mode bypass was added. Missing secrets fail startup.

Existing limits include a 200,000-byte body, small login form, 80 drawn atoms, bounded conformer work and bounded PubChem response/query/result/cache sizes. One worker keeps process-local budgets coherent; its 90-second timeout restarts a stuck worker, which can interrupt a request and require retry. It is not graceful cancellation or a performance guarantee. Worker recycling bounds long-lived process accumulation. Request/credential bodies and raw access URLs are not enabled in Gunicorn logs.

Behind a proxy, the existing peer limiter deliberately does not trust arbitrary X-Forwarded-For; visitors may share one peer budget (40 API calls/minute, 80 global). This can constrain classroom-style use and should be measured before any carefully scoped trusted-proxy change. No silent IP-trust relaxation was made.

App data is browser-local and public lookup caches are in-memory. Restarts discard caches/rate-limit state but do not lose a required server database. Moving from localhost to a hosted origin does not automatically move browser-local drawings, saved inputs or selected compounds; friends start fresh. Sessions depend on stable configured secrets. No real personal/research data should be entered during beta testing.

## 11. Hosted verification and URL

**Not deployed; no live URL exists.** There is no verified Render build, Linux container runtime, actual HTTPS login, hosted PubChem egress, hosted Ketcher/WebGL, hosted guided workflow, real mobile-browser result or cloud resource measurement to report.

After authorization and an actual deployment, test the exact dashboard-provided HTTPS URL directly. Repeat all five routes/refreshes, login/logout, PubChem, a newly drawn Builder molecule, reaction matching/2D/3D, linked atom selection, both guided profiles and calculator/invalid inputs. Check Render health/logs/memory and a cold restart; repeat in Chrome and Safari and a real mobile browser before sharing broadly. Do not replace these with localhost evidence.

## 12. Exact manual actions still required

1. **Authorize publication of the reviewed frozen candidate to the configured existing GitHub repository and creation of one Free, password-protected Render beta.** No source upload or initial deployment has happened. Confirm repository visibility and that GitHub is authenticated as the intended owner (`ryanchen2010-eng`), not a different family account. If you do not want the current source public, choose/authorize a private repository first; none will be created automatically.
2. After approval, commit only reviewed candidate/runtime plus appropriate verification files on a dedicated beta branch, preserve unrelated work, push that approved branch and record the actual commit SHA. Do not deploy the current old HEAD.
3. In Render, connect that exact repository/branch. Use a **Docker Web Service** (or the prepared Blueprint), not Static Site. Confirm **Free**, Ohio, root context, Dockerfile and `/healthz`; no separate build/start command is needed for Docker. Avoid paid workspace/service additions.
4. Enter the new beta password and random hexadecimal session secret directly into Render's environment fields. They must be runtime variables, never Docker ARGs. Render supplies the real external HTTPS URL; leave origin overrides unset unless using a verified custom domain. [Render environment behavior](https://render.com/docs/environment-variables), [secret configuration](https://render.com/docs/configure-environment-variables), [Docker secret cautions](https://render.com/docs/docker).
5. Confirm automatic deployments are **Off** in the dashboard as well as YAML. Review the initial deployment action before creating/applying it: it publishes the password-protected application. Check current billing limits and do not enable paid resources without separate approval.
6. Build/deploy the frozen beta commit. If the image fails, inspect the actual Docker build/import logs; if memory or latency is unsuitable, stop and review options rather than silently upgrading. Copy the actual HTTPS URL from Render only after it exists.
7. Run the hosted checklist above, record its real outcomes, replace the friend-guide placeholder with that real URL, and share the password separately.

The immediate next step is authorization of the reviewed release/source destination and Free beta deployment—not installing something on friends' computers or rebuilding in Wix.

## 13. Update and rollback procedure

Keep local development separate from the frozen archive/approved beta branch. Test a future candidate completely, make a new write-once snapshot/version and commit its reviewed bytes. With auto-deploy Off, use Render's manual deployment of that explicit commit; ordinary unrelated commits must not change the running beta. Blueprint syncing/config edits are also deliberate deployment changes and should not be performed casually.

For rollback, use a previous successful Render deploy when available, or manually redeploy the recorded previous beta commit/source. Free services currently retain rollback to the two most recent previous deploys; keep the local archive/manifest independently. Do not force-push/reset the development tree, overwrite an old tag or restore old leaked secrets. Verify health, login and core chemistry after any rollback. Rollback does not restore server filesystem data, and browser-local state may need clearing/reentry if a later version changes its format.

## 14. Known limits and stopping point

This is a prepared, password-protected source candidate awaiting authorization, not a public launch. Actual container/Render execution, TLS/browser matrix, cold start, cloud memory and externally enforced timeouts need hosted verification. Large Builder downloads, bounded caches, shared proxy limits and serial chemistry are explicit small-beta constraints.

The scientific limits from Phase 5H remain: 3D does not establish experimental outcomes, acid reporting does not certify speciation/workup, unsupported primary selective aldehyde generation stays blocked, and no new reactions or curated examples were added. A105/A276 and A304's annotation remain unchanged. Some legacy condition wording still repeats caveats; this cosmetic issue was not changed in a deployment-only increment.

The temporary local verification server is stopped at completion. The ordinary development launcher remains available separately. Phase 5I stops here; no automatic publication, paid service or additional chemistry phase is authorized by this preparation.

## Final verification addendum

- **3,765 tests pass**: 1,884 Python + 1,881 JavaScript; 11 new deployment-only Python tests, no failures or skips. All 3,754 prior tests are preserved unchanged. Final Python run: 187.712 seconds; JavaScript run: 27,133.672333 ms.
- The 45 Python runtime modules parse with Python 3.12 syntax. Pinned Linux/Python 3.12 dependency-wheel resolution succeeds. Neither observation replaces a Linux container run.
- The extracted frozen archive independently imports the real runtime and reports 24 pathway types and 20 curated examples using the existing macOS environment.
- Release: `molecule-playground-beta-v1`; 107 packaged files, archive SHA-256 `52ee21388501a6a317480797b27edbc961616e9cb7e54c69723f632ffabfbcbb`. Archive checksum and all 107 source-file checksums match; no source changed after freezing.
- The 378-file before/after inventory identifies only the seven intended existing-file changes listed above. Existing chemistry/calculator sources, all old tests, curated inputs, benchmark files and previous reports remain byte-identical; no file was deleted.
- No source push, new Git tag, hosting service, payment, public URL or live verification occurred. The local archive is not deployment authorization.

[Verification summary and preservation evidence](molecule-playground-render-beta-results.json). The friend-facing handout is [here](render-beta-friend-guide.md); its URL remains a placeholder.
