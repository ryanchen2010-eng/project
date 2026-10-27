# Private Wix Site 1 trial

This is deployment preparation, not proof that the online trial works.
No host has been chosen or service created as of 2026-10-01.

## Architecture

Wix My Site 1 embeds one HTTPS app origin. The same origin serves the four built
pages and all `/api` endpoints through `server/production_app.py`. The original
local launcher and development server remain unchanged. The runtime imports
`src/shared-molecules.json`; do not omit it when deploying the backend.

The Docker frontend build uses Node 24.19.0 and locked pnpm 11.19.0 packages.
Ketcher needs Node 24.14.1 or newer. The runtime uses Python 3.12, RDKit
2026.3.6, Flask 3.1.3, and Gunicorn 26.2.0. RDKit publishes Python 3.12 Linux
glibc 2.28+ wheels for x86-64 and ARM64. Secrets are runtime environment values,
not Docker build arguments or files copied into the image.

## User-owned setup and secrets

Confirm the host and spending limit before creating resources. Do not add a
payment method or enable paid resources without Ryan's explicit approval.
Account creation, new credential entry, and new app/repository permissions are
user handoffs. A public source repository is not a private application: existing
GitHub source remains public unless separately changed by Ryan.

Set these values in the hosting dashboard's **secret/environment settings**:

- `CAPSTONE_TRIAL_PASSWORD`: a unique trial password of at least 12 characters.
  Ryan enters it himself; do not reuse his Wix or Google account password.
- `CAPSTONE_SESSION_SECRET`: a high-entropy random signing secret, at least
  32 random bytes represented by 64 hexadecimal characters. Use the host's
  secret generator or a password manager. Never commit, screenshot, or place it
  in the Wix embed URL.
- `CAPSTONE_PUBLIC_ORIGIN`: the assigned HTTPS app origin, without a trailing
  slash, path, query, or credentials.
- `CAPSTONE_FRAME_ANCESTORS`: space-separated exact HTTPS origins allowed to
  frame the app. Inspect the actual iframe ancestors during integration. Site 1
  currently uses these known origins:

  ```text
  https://ryanchen20101201.wixsite.com
  https://ryanchen20101201-my-site-1.editor.wix.com
  https://d26d7cf1-8b52-4d8b-90ef-ebd5ce01a884.filesusr.com
  ```

The password on the Wix page and the app's trial password protect different
layers. There may be two prompts. Share passwords only with intended reviewers
through a private channel; never put them in a URL or public GitHub file.

## Host requirements

- One Docker web service with managed TLS and enforced HTTP-to-HTTPS redirects.
- Runtime `PORT` value (defaults to 10000); bind through Gunicorn, not the old
  `server/chemistry_server.py` HTTP entry point.
- Health check `/healthz` and outbound HTTPS access to PubChem.
- Do not expose a second unauthenticated chemistry port or service.
- One worker is intentional: basic rate limits and the two-job chemistry cap
  are per-process, not distributed. This is a small private trial, not a
  production security or scaling guarantee.
- Disable request/access-body logging. Gunicorn access logging is disabled by
  the supplied configuration; the host may still retain network metadata.
- No database or persistent disk is required for existing features. Drawings
  and transfers are retained only within a browser tab.

Render is one possible free trial host. Its free web service sleeps after 15
idle minutes, may take about one minute to wake, and has usage/resource limits.
Without a payment method, exceeding included bandwidth/build limits can cause
service suspension instead of a charge. Check current account settings before
deployment; do not select a paid plan. Auto-deploy should remain disabled for
the reviewed Wix trial so unfinished pushes cannot change the embedded version.

## Required verification before importing

1. Build and run the production package. Local Python authentication tests are
   not a substitute for a real Linux container build and HTTPS deployment.
2. Anonymous direct requests to all four pages, JS/assets, molecule files,
   and all API endpoints must deny access or show only the login screen.
   `/healthz` must expose only availability, not source, secrets, or chemistry.
3. Wrong passwords, missing/cross-origin POST origins, oversized bodies, and
   unsupported content types must fail. No credentials go in URLs or logs.
4. Authorized access must load all four tools and preserve existing responses,
   name/formula searches, drawings, 3D, mapped reaction atoms, and page transfers.
5. Logout/session expiry must stop subsequent private requests. Changing the
   app password must invalidate prior trial sessions.
6. Inspect Chrome's actual Wix iframe login. Sessions use Secure, HttpOnly,
   SameSite=None, Partitioned cookies, which reduce third-party-cookie issues
   but do not guarantee compatibility with every browser or privacy setting.
   Verify protected navigation, downloads, and requests inside the actual frame.
   If it fails, open the protected app in its own tab; do not bypass protection.
7. Save the old Wix embed before replacing it. Use an HTTPS website embed in
   Site 1, with enough desktop/mobile height and an internal scrollbar.
8. Ryan completes the Wix page password setup. Confirm privacy before publishing
   a protected trial. A hidden/unindexed page is not access control.

## Mentor review and later improvements

The mentor can use the private link and password; the trial need not become
public or merely hidden. Continue local development independently, test updates,
then deploy an approved revision. Updating the hosted app changes what Wix
displays even without clicking Wix Publish. Keep a separately reviewed trial
revision and rollback path. Public launch is a later explicit decision.

## Primary references

- [Wix page password protection](https://support.wix.com/en/article/password-protecting-a-page)
- [Wix HTTPS website embeds](https://dev.wix.com/docs/develop-websites/articles/wix-editor-elements/other-elements/html-i-frame-element/embedding-a-site-in-an-html-i-frame-element)
- [Render free-instance limits](https://render.com/docs/free)
- [Render Docker deployments](https://render.com/docs/docker)
- [Flask partitioned session-cookie configuration](https://flask.palletsprojects.com/en/stable/config/#SESSION_COOKIE_PARTITIONED)
- [RDKit 2026.3.6 Linux wheels](https://pypi.org/project/rdkit/2026.3.6/)
