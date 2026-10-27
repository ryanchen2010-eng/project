# Beta publication status — repository rename verified

## Confirmed source version

The frozen `molecule-playground-beta-v1` has **zero differences** from the current 107 runtime files, including Phase 5H chemistry-confidence improvements and Phase 5I deployment fixes. The original archive and manifest remain unchanged. See [comparison](render-beta-release-confirmation.md).

`origin` now uses `git@github.com:ryanchen2010-eng/project.git` for fetch and push. The connected GitHub owner account and target repository were independently verified. The repository is public; the user explicitly approved publishing the reviewed beta there.

Published branch: [codex/molecule-playground-beta-v1](https://github.com/ryanchen2010-eng/project/tree/codex/molecule-playground-beta-v1).

Published commit: [e3fb8a3c9e91690bfc4c9df64a3e323f5b46b367](https://github.com/ryanchen2010-eng/project/commit/e3fb8a3c9e91690bfc4c9df64a3e323f5b46b367).

The committed runtime was independently hashed against the original manifest: 107 checked, zero mismatches. Supplemental current tests, scripts, immutable benchmarks and non-secret release records were included for verification; they do not change the Docker runtime inputs. Existing blank-at-EOF formatting was retained rather than editing frozen code for a cosmetic Git whitespace warning.

Remote main remains `a6142c67563978111ea672b93059ca395c8c3cb3`. Your local development branch/HEAD remain `codex/step-3-reaction-lab` / `fa00ac9acc75b82e0df4e57148755a904dc80cec`. A temporary Git index was used; your own staging index SHA-256 is unchanged at `2c75388cd6edf8bab2ad85639ead733ade239f5b06e01cdfef875418108cbdde`. No reset, force-push, merge, checkout, tag overwrite or discard occurred.

## Render progress

The existing signed-in Render account matches the project owner. Its New Web Service form is prepared with:

- Public repository `ryanchen2010-eng/project`; branch `codex/molecule-playground-beta-v1`.
- Name `molecule-playground-beta-v1`; Docker runtime; Ohio region.
- **Free: $0/month, 0.1 CPU, 512 MB RAM**, explicitly selected instead of the initial paid default.
- Root Docker context `.`; Dockerfile `./Dockerfile`; use its existing CMD.
- Health check `/healthz`.
- **Auto-Deploy Off**, confirmed by the selected menu item and displayed control value.
- Variable names `CAPSTONE_TRIAL_PASSWORD` and `CAPSTONE_SESSION_SECRET`; both values deliberately blank for private user entry.

No new GitHub app permissions were required: Render uses the approved public Git URL. No paid service, database, disk, account password change or additional reaction was introduced.

## Private user step still required

In the prepared Render browser tab:

1. Enter a private beta password of at least 12 characters in the Value beside `CAPSTONE_TRIAL_PASSWORD`.
2. Run `python3 -c 'import secrets; print(secrets.token_hex(32))'` in Terminal and paste its output directly into the Value beside `CAPSTONE_SESSION_SECRET`. Keep it private. Do not use Render's Generate button for this variable: it produces a different encoding than the app's required hex format.
3. Keep Free and Auto-Deploy Off, then click **Deploy web service** yourself to submit the newly entered authentication secrets. Do not paste them into chat or Git. Stop if Render asks to upgrade/pay.

The tab is left at the blank secret fields. This handoff is for credential entry/submission, **not another request to approve the already-approved source publication or Free plan**.

The app is **not live yet**; no service/deploy URL has been created. After submission, inspect the real Docker build, health and startup logs, obtain the actual URL, then repeat the hosted verification checklist. Local verification remains distinct from a real Render deployment.

![Prepared Free service with blank private values](render-beta-secret-entry-handoff.png)
