# Render beta startup verification — 2026-10-20

## Outcome

The existing Free service `molecule-playground-beta-v1` is now live at https://molecule-playground-beta-v1.onrender.com/.

- Service: `srv-dbbavhjbc2fs73ah7l80`.
- Manual deployment: `dep-dbbpmtoae00c73ae13mg`.
- Deployed commit: `1f5a9a579e8d4bd7312932555060ccbbc926e480` (the previously tested native drawing dependency fix).
- Render log: `Your service is live` at 12:49:25 PM America/Toronto.
- Public root redirects to `/login?next=/` and displays the private trial password form.
- `/healthz` displays `{"status":"ok"}`.
- Current service settings verified: Docker, Free, Ohio, branch `codex/molecule-playground-beta-v1`, Dockerfile `./Dockerfile`, health check `/healthz`, Auto-Deploy **Off**.

The user corrected the private password value directly in Render. No secret values were read, revealed, copied, entered or changed by the agent during this retry. No source changes, new commits, benchmark changes or snapshot overwrites were needed today.

## Remaining verification

Successful startup and the public password gate do not prove every hosted chemistry or UI feature works. Authenticated Explorer/PubChem, Builder, Reaction Lab, Calculators, linked atom highlighting and mobile checks remain pending user sign-in. Do not claim these checks have passed yet.

The earlier local verification remains: 1,885 Python plus 1,881 JavaScript tests (3,766 total), TypeScript and production build passed for the dependency patch. The original v1 snapshot and `main` branch were preserved.

## Evidence

- `render-beta-live-login-2026-10-20.png`
- `render-beta-live-deploy-2026-10-20.png`

Next action: user signs in on the live website using the trial password (not the session secret), then asks for hosted functional checks. Friends can use the same website URL and receive the trial password privately. Free instances may require a startup wait after inactivity.
