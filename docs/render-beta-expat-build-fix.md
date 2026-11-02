# Render beta: RDKit native drawing dependency fix

## Failure and correction

The first Render build of `e3fb8a3c9e91690bfc4c9df64a3e323f5b46b367` failed at the existing chemistry import smoke test. RDKit's `rdMolDraw2D` extension could not load `libexpat.so.1`. The frontend build had succeeded.

Install `libexpat1` explicitly in the Python Debian Bookworm runtime stage. Debian's [package file list](https://packages.debian.org/bookworm/amd64/libexpat1/filelist) confirms this package provides `/lib/x86_64-linux-gnu/libexpat.so.1`. No development headers, chemistry changes, credential changes or validation bypasses are needed. Keep the real chemistry import smoke test so native dependency failures stop the build.

## Preservation and release identity

- Original `molecule-playground-beta-v1` archive remains unchanged, SHA-256 `52ee21388501a6a317480797b27edbc961616e9cb7e54c69723f632ffabfbcbb`.
- New write-once patch snapshot: `molecule-playground-beta-v1-expat-fix`, archive SHA-256 `598c9b2e203f49772950d28ca5df13a16deb65289717d5127fdc718031600655`.
- All 107 runtime file hashes compared with v1: only `Dockerfile` differs; no runtime files removed or added.
- New regression check ensures `libexpat1` is installed in the Python stage before the pinned Python wheels, and the real chemistry/drawing import gate remains present.
- Existing local branch, index, working files and frozen benchmark are preserved. Publish a normal child commit on the existing beta branch only; do not update `main`.
- Render service: `srv-dbbavhjbc2fs73ah7l80`, Docker, Ohio, Free; auto-deploy verified Off, health check `/healthz`.

## Verification status

Deployment-specific tests: 12 passed. JavaScript regression: 1,881 passed. TypeScript and Vite production build: passed (existing dependency-directive and bundle-size warnings).

Full Python regression: 1,885 passed in 201.746 seconds. Combined regression: **3,766 passed**, including one new deployment test. Local drawing and all 24 pathway definitions import successfully. Patch whitespace checks pass. No chemistry, benchmark, UI, calculator or authentication code changed.

Actual Render Linux build **passed** for commit `1f5a9a579e8d4bd7312932555060ccbbc926e480`, manually deployed as `dep-dbbb3l6q1p3s73buksag`. The previously failing chemistry import gate completed in 0.9 seconds, and the Docker image was built successfully. No local Docker/Podman runtime is installed.

## Separate startup blocker: private configuration

Gunicorn then failed closed because `CAPSTONE_TRIAL_PASSWORD` did not meet the existing 12–256-character/no-surrounding-whitespace requirement. No password values were inspected, copied or logged here. The user must correct the value directly in Render and submit it themselves. The session secret must also remain a private hexadecimal value accepted by the existing validation. Do not remove or weaken either check.

The service URL has been assigned as `https://molecule-playground-beta-v1.onrender.com/`, but the application is **not live or functionally verified** until credential configuration and startup succeed. Do not share it as a working beta yet. The original beta snapshot remains unchanged; the original `main` ref remains `a6142c67563978111ea672b93059ca395c8c3cb3`.
