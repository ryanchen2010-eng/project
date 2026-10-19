"""Password-protected, host-neutral WSGI gateway for a small website beta.

Run through a production WSGI server, never Flask's development server. The
hosting ingress must enforce HTTPS and must not cache authenticated responses.
This is a shared-password prototype, not an identity-management system. Its
rate limits and job semaphore are process-local: use one worker for the trial.
Partitioned cookies help current Chrome iframe sessions, but not every browser
or Wix sandbox supports them. Sign in inside the actual embed; a top-level tab
can have a different cookie partition. The new-tab link is the safe fallback.
"""

from __future__ import annotations

import hashlib
import hmac
import mimetypes
import os
import re
import threading
import time
from collections import deque
from collections.abc import Callable, Mapping
from datetime import timedelta
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit

from flask import Flask, Response, jsonify, redirect, render_template_string, request, send_from_directory, session
from werkzeug.exceptions import HTTPException


MAX_BODY_BYTES = 200_000
LOGIN_BODY_BYTES = 4_096
COOKIE_NAME = "__Host-capstone_trial"
RETURN_PAGES = {"/", "/index.html", "/explore.html", "/builder.html", "/reaction-lab.html", "/calculators.html"}
ENV_NAMES = {
    "TRIAL_PASSWORD": "CAPSTONE_TRIAL_PASSWORD",
    "SESSION_SECRET": "CAPSTONE_SESSION_SECRET",
    "PUBLIC_ORIGIN": "CAPSTONE_PUBLIC_ORIGIN",
    "FRAME_ANCESTORS": "CAPSTONE_FRAME_ANCESTORS",
}


def _https_origin(raw: Any, setting: str) -> str:
    """Accept only a literal HTTPS origin, never a path, wildcard, or URL token."""
    if not isinstance(raw, str) or not raw or raw != raw.strip() or re.search(r"[\s\\\x00-\x1f]", raw):
        raise ValueError(f"{setting} must be an explicit HTTPS origin.")
    try:
        parsed = urlsplit(raw)
        port = parsed.port
    except ValueError as exc:
        raise ValueError(f"{setting} must be an explicit HTTPS origin.") from exc
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username is not None
            or parsed.password is not None or parsed.path not in ("", "/")
            or parsed.query or parsed.fragment or "*" in parsed.netloc
            or not re.fullmatch(r"[A-Za-z0-9.-]+", parsed.hostname)
            or parsed.hostname.startswith(".") or parsed.hostname.endswith(".")
            or parsed.hostname.lower() in {"localhost", "127.0.0.1", "0.0.0.0"}):
        raise ValueError(f"{setting} must be an explicit HTTPS origin.")
    host = parsed.hostname.lower()
    return f"https://{host}" + (f":{port}" if port is not None and port != 443 else "")


def _positive_int(value: Any, label: str, maximum: int) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError(f"{label} must be an integer from 1 to {maximum}.")
    return value


class _RateLimiter:
    """Small sliding-window peer and global budgets, without trusting XFF."""

    def __init__(self, budgets: Mapping[str, tuple[int, int]], clock: Callable[[], float], maximum_peers: int = 2048):
        self.budgets = budgets
        self.clock = clock
        self.maximum_peers = maximum_peers
        self.peers: dict[tuple[str, str], deque[float]] = {}
        self.global_events: dict[str, deque[float]] = {name: deque() for name in budgets}
        self.lock = threading.Lock()

    def allow(self, category: str, peer: str) -> bool:
        with self.lock:
            now = self.clock()
            cutoff = now - 60
            # Also bound storage when a peer appears only once or is idle.
            for key, events in list(self.peers.items()):
                while events and events[0] <= cutoff:
                    events.popleft()
                if not events:
                    del self.peers[key]
            global_events = self.global_events[category]
            while global_events and global_events[0] <= cutoff:
                global_events.popleft()
            key = (category, peer)
            if key not in self.peers and len(self.peers) >= self.maximum_peers:
                return False
            peer_events = self.peers.get(key, deque())
            peer_limit, global_limit = self.budgets[category]
            if len(peer_events) >= peer_limit or len(global_events) >= global_limit:
                return False
            peer_events.append(now)
            self.peers[key] = peer_events
            global_events.append(now)
            return True


LOGIN_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Molecule Playground · Private trial</title><style>
body{margin:0;background:#f5f3ee;color:#18372d;font:16px/1.55 system-ui,sans-serif;padding:24px}
main{max-width:440px;margin:5vh auto;padding:28px;background:white;border:1px solid #ccd8d1;border-radius:18px}
h1{font-size:26px;line-height:1.2;margin:0 0 12px}p{margin:12px 0}label{display:block;font-weight:650}
input{box-sizing:border-box;width:100%;margin:8px 0 16px;padding:12px;border:1px solid #a8bcb1;border-radius:8px;font:inherit}
button{background:#2e5b49;color:white;border:0;padding:12px 20px;border-radius:8px;font:inherit;cursor:pointer}
a{color:#265f49}.hint{font-size:14px;color:#56685f}.error{color:#9b2636}
</style></head><body><main><h1>Private project trial</h1>
{% if signed_in %}<p>You are signed in to Molecule Playground.</p><p><a href="{{ next_page }}">Open the website</a></p>
<form method="post" action="/logout"><button type="submit">Sign out</button></form>
{% else %}<p>Enter the trial password shared by the project owner.</p>
{% if error %}<p class="error" role="alert">{{ error }}</p>{% endif %}
<form method="post" action="/login"><input type="hidden" name="next" value="{{ next_page }}">
<label for="password">Trial password</label><input id="password" type="password" name="password" autocomplete="current-password" maxlength="256" required>
<button type="submit">Sign in</button></form>{% endif %}
<p class="hint">Open the website directly in your browser. If it is embedded elsewhere, that frame may need its own sign-in because of browser privacy settings.</p>
<p><a href="{{ fallback_url }}" target="_blank" rel="noopener noreferrer">Open the private trial in a new tab</a></p>
<p class="hint">Keep the password private. Access expires after one hour. This trial is not a public launch.</p>
</main></body></html>"""


def create_app(config: Mapping[str, Any] | None = None, *, chemistry_backend: Any = None,
               monotonic: Callable[[], float] = time.monotonic) -> Flask:
    """Create a fail-closed private app; injectable settings/backend aid tests.

    Required environment: CAPSTONE_TRIAL_PASSWORD (12–256 characters),
    CAPSTONE_SESSION_SECRET (64+ hexadecimal characters from random bytes),
    CAPSTONE_PUBLIC_ORIGIN (defaults to Render's RENDER_EXTERNAL_URL), and
    CAPSTONE_FRAME_ANCESTORS (defaults to that same origin for standalone use).
    Explicit embedding requires every exact HTTPS parent origin.
    No public-mode switch or credentials in embed URLs are supported.
    """
    settings: dict[str, Any] = {key: os.environ.get(name) for key, name in ENV_NAMES.items()}
    # Render supplies its actual generated URL; never guess an onrender.com URL.
    # Explicit invalid settings still fail closed, including config overrides.
    if settings["PUBLIC_ORIGIN"] is None:
        settings["PUBLIC_ORIGIN"] = os.environ.get("RENDER_EXTERNAL_URL")
    if settings["FRAME_ANCESTORS"] is None:
        settings["FRAME_ANCESTORS"] = settings["PUBLIC_ORIGIN"]
    settings.update({
        "DIST_DIR": Path(__file__).resolve().parents[1] / "dist",
        "MAX_CHEMISTRY_JOBS": 1,
        "API_REQUESTS_PER_MINUTE": 40,
        "API_GLOBAL_REQUESTS_PER_MINUTE": 80,
        "LOGIN_REQUESTS_PER_MINUTE": 5,
        "LOGIN_GLOBAL_REQUESTS_PER_MINUTE": 25,
    })
    if config is not None:
        settings.update(config)
    password = settings.get("TRIAL_PASSWORD")
    if not isinstance(password, str) or not 12 <= len(password) <= 256 or password != password.strip():
        raise ValueError("CAPSTONE_TRIAL_PASSWORD must contain 12–256 characters without surrounding whitespace.")
    secret_hex = settings.get("SESSION_SECRET")
    if (not isinstance(secret_hex, str) or not re.fullmatch(r"[0-9a-fA-F]{64,}", secret_hex)
            or len(secret_hex) % 2 or len(set(secret_hex.lower())) < 8):
        raise ValueError("CAPSTONE_SESSION_SECRET must be 64+ hexadecimal characters generated from random bytes.")
    secret = bytes.fromhex(secret_hex)
    if len(set(secret)) < 16:
        raise ValueError("CAPSTONE_SESSION_SECRET must be generated from random bytes, not a repeated pattern.")
    public_origin = _https_origin(settings.get("PUBLIC_ORIGIN"), "CAPSTONE_PUBLIC_ORIGIN")
    raw_frames = settings.get("FRAME_ANCESTORS")
    if isinstance(raw_frames, str):
        raw_frames = raw_frames.split()
    if not isinstance(raw_frames, (list, tuple)) or not raw_frames or len(raw_frames) > 12:
        raise ValueError("CAPSTONE_FRAME_ANCESTORS must list exact HTTPS origins.")
    frame_origins = list(dict.fromkeys(_https_origin(value, "CAPSTONE_FRAME_ANCESTORS") for value in raw_frames))
    dist_root = Path(settings["DIST_DIR"]).resolve()
    jobs_limit = _positive_int(settings["MAX_CHEMISTRY_JOBS"], "MAX_CHEMISTRY_JOBS", 8)
    budgets = {
        "api": (_positive_int(settings["API_REQUESTS_PER_MINUTE"], "API_REQUESTS_PER_MINUTE", 200),
                _positive_int(settings["API_GLOBAL_REQUESTS_PER_MINUTE"], "API_GLOBAL_REQUESTS_PER_MINUTE", 500)),
        "login": (_positive_int(settings["LOGIN_REQUESTS_PER_MINUTE"], "LOGIN_REQUESTS_PER_MINUTE", 20),
                  _positive_int(settings["LOGIN_GLOBAL_REQUESTS_PER_MINUTE"], "LOGIN_GLOBAL_REQUESTS_PER_MINUTE", 100)),
    }
    if chemistry_backend is None:
        # RDKit's native parser diagnostics can contain submitted SMILES or
        # drawings. Disable them once per production process, not in a
        # request-scoped context that could race another chemistry thread.
        from rdkit import rdBase
        rdBase.DisableLog("rdApp.*")
        # Importing validates the RDKit installation and shared catalog before
        # this app can report itself healthy. Do not run the old HTTP server.
        from . import chemistry_server as chemistry_backend

    app = Flask(__name__, static_folder=None)
    app.config.update(
        DEBUG=False, TESTING=bool(settings.get("TESTING", False)), SECRET_KEY=secret,
        TRUSTED_HOSTS=[urlsplit(public_origin).hostname],
        SESSION_COOKIE_NAME=COOKIE_NAME, SESSION_COOKIE_PATH="/", SESSION_COOKIE_DOMAIN=None,
        SESSION_COOKIE_SECURE=True, SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="None", SESSION_COOKIE_PARTITIONED=True,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=1), SESSION_REFRESH_EACH_REQUEST=False,
        MAX_CONTENT_LENGTH=MAX_BODY_BYTES, MAX_FORM_MEMORY_SIZE=LOGIN_BODY_BYTES, MAX_FORM_PARTS=5,
        PROPAGATE_EXCEPTIONS=False,
    )
    password_digest = hashlib.sha256(password.encode("utf-8")).digest()
    fingerprint = hmac.new(secret, b"capstone-trial-v1:" + password_digest, hashlib.sha256).hexdigest()
    limiter = _RateLimiter(budgets, monotonic)
    jobs = threading.BoundedSemaphore(jobs_limit)
    frame_policy = "frame-ancestors 'self' " + " ".join(frame_origins)

    def signed_in() -> bool:
        value = session.get("trial")
        return isinstance(value, str) and hmac.compare_digest(value, fingerprint)

    def safe_return(raw: Any) -> str:
        return raw if isinstance(raw, str) and raw in RETURN_PAGES else "/"

    def json_error(message: str, code: int, retry: int | None = None) -> Response:
        response = jsonify(error=message)
        response.status_code = code
        if retry is not None:
            response.headers["Retry-After"] = str(retry)
        return response

    @app.before_request
    def protect_requests() -> Response | None:
        if request.method == "POST":
            # Even login is protected: SameSite=None must not allow login CSRF.
            if request.headers.get("Origin") != public_origin:
                return json_error("This request must come from the private trial website.", 403)
            if request.content_length is None or request.content_length <= 0:
                # Empty logout is allowed because it has no submitted data.
                if request.path != "/logout":
                    return json_error("The request is empty or has no declared size.", 422)
            if request.content_length is not None and request.content_length > MAX_BODY_BYTES:
                return json_error("The request is too large.", 413)
        # TRUSTED_HOSTS failures are routing exceptions; do not turn them into
        # a login redirect or health success from this callback. Origin/size
        # checks above also cover POSTs to missing or method-mismatched routes.
        if request.routing_exception is not None:
            return None
        if request.path == "/healthz" and request.method in {"GET", "HEAD"}:
            return None
        if request.path == "/login":
            if request.method == "POST" and not limiter.allow("login", request.remote_addr or "unknown"):
                return json_error("Too many sign-in attempts. Try again in a minute.", 429, 60)
            return None
        if request.path.startswith("/api/"):
            if not limiter.allow("api", request.remote_addr or "unknown"):
                return json_error("Too many chemistry requests. Try again in a minute.", 429, 60)
            if not signed_in():
                return json_error("Sign in to this private trial first.", 401)
        elif not signed_in():
            return redirect("/login?next=" + safe_return(request.path), code=303)
        return None

    @app.after_request
    def private_headers(response: Response) -> Response:
        response.headers["Cache-Control"] = "private, no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
        # no-referrer can make ordinary HTML form POST Origin serialize as
        # null. Keep strict Origin validation; permit same-origin referrers
        # only on the login/logout form document, never to external sites.
        response.headers["Referrer-Policy"] = "same-origin" if request.path == "/login" else "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers.setdefault("Content-Security-Policy", frame_policy)
        response.headers.pop("X-Frame-Options", None)
        response.vary.add("Cookie")
        return response

    def login_page(error: str | None = None, code: int = 200, next_page: str = "/") -> Response:
        response = app.make_response((render_template_string(
            LOGIN_TEMPLATE, error=error, signed_in=signed_in(), next_page=next_page,
            fallback_url=public_origin + "/login",
        ), code))
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; " + frame_policy
        )
        return response

    @app.route("/login", methods=["GET", "POST"])
    def login() -> Response:
        if request.method == "GET":
            return login_page(next_page=safe_return(request.args.get("next")))
        if request.mimetype != "application/x-www-form-urlencoded":
            return json_error("Use the private trial sign-in form.", 415)
        if request.content_length is not None and request.content_length > LOGIN_BODY_BYTES:
            return json_error("The sign-in request is too large.", 413)
        candidate = request.form.get("password", "")
        next_page = safe_return(request.form.get("next"))
        if not 12 <= len(candidate) <= 256 or not hmac.compare_digest(
                hashlib.sha256(candidate.encode("utf-8")).digest(), password_digest):
            return login_page("The password is not correct.", 401, next_page)
        session.clear()
        session["trial"] = fingerprint
        session.permanent = True
        return redirect(next_page, code=303)

    @app.post("/logout")
    def logout() -> Response:
        if request.content_length and request.mimetype not in {"application/json", "application/x-www-form-urlencoded"}:
            return json_error("Use the private trial sign-out form.", 415)
        session.clear()
        return redirect("/login", code=303)

    @app.get("/healthz")
    def health() -> tuple[Response, int]:
        index = (dist_root / "index.html").resolve()
        ready = index.is_relative_to(dist_root) and index.is_file()
        return jsonify(status="ok" if ready else "unavailable"), 200 if ready else 503

    def run_job(action: Callable[[], Any]) -> Any:
        if not jobs.acquire(blocking=False):
            return json_error("The chemistry service is busy. Try again shortly.", 503, 2)
        try:
            return action()
        except chemistry_backend.PubChemError as exc:
            return json_error(str(exc), 503)
        except (chemistry_backend.ChemistryError, ValueError, TypeError) as exc:
            return json_error(str(exc), 422)
        except Exception as exc:
            # No request path/query/body/password, exception text, or traceback
            # is emitted here. Disable ingress/WSGI raw access logs separately.
            app.logger.warning("Private trial chemistry failure (%s).", type(exc).__name__)
            return json_error("The chemistry service could not process this request.", 500)
        finally:
            jobs.release()

    @app.get("/api/reactions/catalog")
    def catalog() -> Any:
        return run_job(lambda: jsonify(chemistry_backend.reaction_catalog()))

    @app.get("/api/pubchem/search")
    def pubchem_search() -> Any:
        return run_job(lambda: jsonify(chemistry_backend.search_pubchem(request.args.get("q", ""))))

    @app.get("/api/pubchem/structure")
    @app.get("/api/pubchem/depiction")
    def pubchem_structure() -> Any:
        raw_cid = request.args.get("cid", "")
        if not raw_cid.isdecimal() or len(raw_cid) > 10 or int(raw_cid) <= 0:
            return json_error("Choose a valid PubChem compound.", 422)

        def lookup() -> Response:
            cid = int(raw_cid)
            if request.path == "/api/pubchem/depiction":
                data = chemistry_backend.get_pubchem_depiction(cid)
                return Response(data, content_type="image/png") if data else json_error(
                    "A 2D depiction is not available for this PubChem compound.", 404)
            structure = chemistry_backend.get_pubchem_structure(cid)
            if structure is None:
                smiles = chemistry_backend.get_pubchem_smiles(cid)
                molecule = chemistry_backend.Chem.MolFromSmiles(smiles) if smiles else None
                if molecule is not None:
                    try:
                        generated = chemistry_backend.analyze_molfile(chemistry_backend.Chem.MolToMolBlock(molecule))
                        structure = generated.get("molfile") if generated["representation"] == "3d" else None
                    except chemistry_backend.ChemistryError:
                        pass
            return Response(structure, content_type="chemical/x-mdl-sdfile; charset=utf-8") if structure else json_error(
                "A 3D structure is not available for this PubChem compound.", 404)

        return run_job(lookup)

    @app.post("/api/chemistry")
    @app.post("/api/reactions/match")
    @app.post("/api/reactions/run")
    @app.post("/api/reactions/diagram")
    @app.post("/api/reactions/inspect")
    def chemistry_post() -> Any:
        if request.mimetype != "application/json":
            return json_error("Expected an application/json molecule request.", 415)
        body = request.get_json()
        if not isinstance(body, dict):
            return json_error("Expected a molecule request.", 422)
        if request.path == "/api/chemistry":
            if not isinstance(body.get("molfile"), str):
                return json_error("Expected a molecule drawing in Molfile format.", 422)
            return run_job(lambda: jsonify(chemistry_backend.analyze_molfile(body["molfile"])))
        if request.path == "/api/reactions/inspect":
            return run_job(lambda: jsonify(chemistry_backend.inspect_reactant(body.get("reactant"), body.get("include3D", False))))
        if request.path != "/api/reactions/match" and not isinstance(body.get("reactionId"), str):
            return json_error("Choose two molecules and a matching reaction.", 422)
        if not all(isinstance(body.get(key), (str, dict)) for key in ("reactantA", "reactantB")):
            return json_error("Choose two molecules and a matching reaction.", 422)
        functions = {
            "/api/reactions/match": chemistry_backend.match_reactions,
            "/api/reactions/run": chemistry_backend.run_curated_reaction,
            "/api/reactions/diagram": chemistry_backend.reaction_diagram,
        }
        arguments = [body["reactantA"], body["reactantB"], body.get("conditions")]
        if request.path != "/api/reactions/match":
            arguments.insert(0, body["reactionId"])
        return run_job(lambda: jsonify(functions[request.path](*arguments)))

    @app.get("/")
    @app.get("/<path:filename>")
    def static_file(filename: str = "index.html") -> Response:
        parts = PurePosixPath(filename).parts
        if (not parts or any(part.startswith(".") for part in parts) or "\\" in filename
                or "\x00" in filename or filename.endswith(".gz") or parts[0] in {"api", "server", "src"}):
            return json_error("Not found.", 404)
        path = (dist_root / filename).resolve()
        if not path.is_relative_to(dist_root) or not path.is_file():
            return json_error("Not found.", 404)
        compressed = (dist_root / (filename + ".gz")).resolve()
        accepts_gzip = any(name.lower() == "gzip" and quality > 0 for name, quality in request.accept_encodings)
        gzip_variant = accepts_gzip and compressed.is_relative_to(dist_root) and compressed.is_file()
        response = send_from_directory(
            dist_root, filename + ".gz" if gzip_variant else filename,
            mimetype=mimetypes.guess_type(filename)[0] or "application/octet-stream",
            conditional=False, etag=False, max_age=0,
        )
        if gzip_variant:
            response.headers["Content-Encoding"] = "gzip"
        response.vary.add("Accept-Encoding")
        return response

    @app.errorhandler(HTTPException)
    def http_error(error: HTTPException) -> Response:
        messages = {400: "The request could not be read.", 404: "Not found.",
                    405: "This request method is not supported.", 413: "The request is too large.",
                    415: "The request content type is not supported."}
        return json_error(messages.get(error.code, "The request could not be completed."), error.code or 500)

    @app.errorhandler(Exception)
    def unexpected_error(error: Exception) -> Response:
        app.logger.warning("Private trial gateway failure (%s).", type(error).__name__)
        return json_error("The private trial could not complete this request.", 500)

    return app
