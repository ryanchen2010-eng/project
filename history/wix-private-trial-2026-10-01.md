# Wix private trial — 2026-10-01

Status: preparing locally; not deployed and not yet imported.

- Ryan authorized using the open browser to import the current app into Wix
  My Site 1, keeping the trial private. Site 3 is outside scope.
- Confirmed the open Site 1 is Wix Harmony Editor and still contains the older
  standalone Explorer. It has one Home page. The latest four-page app and
  chemistry service are still local.
- Confirmed Home → Page Settings → Access → Manage Access offers
  “Visitors with a password”, with no upgrade prompt in this dialog.
- Opened that option without entering a password or saving/publishing it.
  Ryan must enter and save a new password himself; no password belongs in chat,
  project files, Git history, screenshots, or embed URLs.
- Suggested Render's free tier, but the hosting choice remains unconfirmed.
  No Render account, GitHub authorization, hosting service, or payment method
  was created.
- Preparing one password-protected app origin for the frontend and chemistry
  APIs. The existing development API and local launcher remain unchanged.
- Private iframe access requires real testing: partitioned session cookies may
  work in Chrome but browser restrictions can prevent embedded login.
  Standalone protected app access is the fallback, never a public bypass.
- The old Wix embed has not been replaced. No Wix publish or GitHub push has
  happened in this import attempt.

## Local preparation and verification completed

- Added a separate Flask/Gunicorn gateway for the private trial. All built
  pages/assets and chemistry/PubChem endpoints require a signed trial session.
  Startup rejects missing password, signing secret, HTTPS origin, and frame
  allowlist. The local development API and launcher are unchanged.
- Added secure, HttpOnly, SameSite=None, Partitioned one-hour session cookies,
  exact POST origin checks, body/content-type limits, process-local request and
  chemistry-job limits, protected static/gzip routing, and minimal health status.
- Disabled raw RDKit input diagnostics in the production process and excluded
  history, credentials, local environments, and Git metadata from the Docker
  image. Optional production dependencies were installed into `.venv` for tests.
- Verified 51 JavaScript and 79 Python tests (130 total), including 24 gateway
  tests and real RDKit SN2/diagram compatibility. TypeScript and frontend build
  passed. All 17 compressed assets round-trip exactly. Gunicorn configuration
  loads with synthetic test settings and fails closed with missing credentials.
- Independent read-only package/auth review found the native RDKit logging
  issue; it was fixed and covered by a regression test.
- No Docker runtime is installed here, so the actual Linux image build remains
  unverified. Real HTTPS, hosting quotas/memory, cookie behavior inside Wix,
  and mentor access still need deployment-time checks.
- Browser GitHub page confirms ownership of `ryanchen2010-eng/capstone-project`;
  no code was uploaded or account permissions changed in this attempt.

Pending: confirm hosting; user
sign-in/credential setup; deploy private endpoint; verify access denial directly
and inside Wix; replace Site 1 embed and check all three tools; publish a
password-protected trial only after confirming that the protections work.
