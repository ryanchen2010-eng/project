"""Synthetic HTTP tests: no listening socket, hosting account, or network use.

The hard-coded credentials below are test fixtures, never deployment secrets.
This optional gateway suite needs server/requirements-production.txt. Local
chemistry development can still run without Flask installed.
"""

from __future__ import annotations

import gzip
import os
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

try:
    from server.production_app import COOKIE_NAME, MAX_BODY_BYTES, create_app
except ModuleNotFoundError as exc:
    if exc.name != "flask":
        raise
    create_app = None


ORIGIN = "https://trial.example.test"
PASSWORD = "Only-a-synthetic-test-password"
SECRET = "5a793bc832adc647a5f382190dead01d19f58f6fa0c9246eb8b2b31f0f419b60"


class FakeChemistryError(ValueError):
    pass


class FakePubChemError(Exception):
    pass


def fake_backend() -> SimpleNamespace:
    return SimpleNamespace(
        ChemistryError=FakeChemistryError, PubChemError=FakePubChemError,
        reaction_catalog=Mock(return_value={"reactants": [{"id": "water"}], "reactions": []}),
        search_pubchem=Mock(return_value={"results": [{"cid": 962}], "limited": False}),
        get_pubchem_structure=Mock(return_value="source-sdf"),
        get_pubchem_depiction=Mock(return_value=b"synthetic-png"),
        get_pubchem_smiles=Mock(return_value="O"),
        analyze_molfile=Mock(return_value={"representation": "3d", "molfile": "generated-sdf", "formula": "H2O"}),
        match_reactions=Mock(return_value={"reactions": [], "interpretationNotes": []}),
        run_curated_reaction=Mock(return_value={"balanced": True, "productName": "Water"}),
        reaction_diagram=Mock(return_value={"svg": "<svg></svg>", "atomMappings": []}),
        inspect_reactant=Mock(return_value={"name": "Water", "groups": [], "svg": "<svg></svg>"}),
        Chem=SimpleNamespace(MolFromSmiles=Mock(return_value="molecule"), MolToMolBlock=Mock(return_value="molfile")),
    )


@unittest.skipIf(create_app is None, "Install optional server/requirements-production.txt to test the private gateway")
class ProductionAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="capstone-production-test-")
        self.root = Path(self.temporary.name)
        self.dist = self.root / "dist"
        self.dist.mkdir()
        for page in ("index.html", "explore.html", "builder.html", "reaction-lab.html", "calculators.html"):
            (self.dist / page).write_text(f"<h1>synthetic-{page}</h1>", encoding="utf-8")
        (self.dist / "assets").mkdir()
        (self.dist / "assets" / "app.js").write_text("synthetic-javascript", encoding="utf-8")
        (self.dist / "assets" / "app.js.gz").write_bytes(gzip.compress(b"synthetic-javascript"))
        self.backend = fake_backend()
        self.now = 100.0
        self.settings = {
            "TRIAL_PASSWORD": PASSWORD, "SESSION_SECRET": SECRET,
            "PUBLIC_ORIGIN": ORIGIN,
            "FRAME_ANCESTORS": "https://site.example.test https://editor.wix.com",
            "DIST_DIR": self.dist, "TESTING": True,
        }
        self.app = self.make_app()
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def make_app(self, **overrides):
        return create_app({**self.settings, **overrides}, chemistry_backend=self.backend, monotonic=lambda: self.now)

    def get(self, path, *, client=None, **kwargs):
        response = (client or self.client).get(path, base_url=ORIGIN, **kwargs)
        self.addCleanup(response.close)
        return response

    def post(self, path, *, client=None, headers=None, **kwargs):
        return (client or self.client).post(path, base_url=ORIGIN, headers={"Origin": ORIGIN, **(headers or {})}, **kwargs)

    def sign_in(self, *, client=None, next_page="/", password=PASSWORD):
        return self.post("/login", client=client, data={"password": password, "next": next_page})

    def assert_private_headers(self, response):
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.assertIn("private", response.headers["Cache-Control"])
        self.assertIn("noindex", response.headers["X-Robots-Tag"])
        self.assertEqual(response.headers["Referrer-Policy"], "no-referrer")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("https://site.example.test", response.headers["Content-Security-Policy"])
        self.assertNotIn("X-Frame-Options", response.headers)

    def test_required_settings_fail_closed(self):
        for setting in ("TRIAL_PASSWORD", "SESSION_SECRET", "PUBLIC_ORIGIN", "FRAME_ANCESTORS"):
            with self.subTest(setting=setting), self.assertRaises(ValueError):
                self.make_app(**{setting: None})
        for secret in ("development", "a" * 64, "0" * 64, "12345678" * 7, "01" * 32, "0123456789abcdef" * 4):
            with self.subTest(secret=secret), self.assertRaises(ValueError):
                self.make_app(SESSION_SECRET=secret)
        with self.assertRaises(ValueError):
            self.make_app(TRIAL_PASSWORD="short")

    def test_https_origin_and_explicit_frames_required(self):
        for origin in ("http://trial.example.test", "https://trial.example.test/path", "https://user:pass@trial.example.test",
                       "https://trial.example.test?key=secret", "https://*.example.test", "https://localhost",
                       "https://trial.example.test/#x", "https://trial.example.test\n", "https://trial.example.test\\evil"):
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                self.make_app(PUBLIC_ORIGIN=origin)
        for origins in ("*", "https://*.wix.com", "http://editor.wix.com", "'self'", [], ["https://editor.wix.com\n"]):
            with self.subTest(origins=origins), self.assertRaises(ValueError):
                self.make_app(FRAME_ANCESTORS=origins)

    def test_environment_factory_and_no_public_switch(self):
        env = {"CAPSTONE_TRIAL_PASSWORD": PASSWORD, "CAPSTONE_SESSION_SECRET": SECRET,
               "CAPSTONE_PUBLIC_ORIGIN": ORIGIN, "CAPSTONE_FRAME_ANCESTORS": "https://editor.wix.com"}
        with patch.dict("os.environ", env, clear=True):
            app = create_app({"DIST_DIR": self.dist}, chemistry_backend=self.backend)
        self.assertEqual(app.test_client().get("/", base_url=ORIGIN).status_code, 303)
        app = self.make_app(PUBLIC=True)
        self.assertEqual(app.test_client().get("/api/reactions/catalog", base_url=ORIGIN).status_code, 401)

    def test_health_is_minimal_and_reports_missing_dist(self):
        response = self.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "ok"})
        self.assert_private_headers(response)
        (self.dist / "index.html").unlink()
        response = self.get("/healthz")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json, {"status": "unavailable"})
        self.assertNotIn("RDKit", response.text)
        self.assertNotIn(str(self.dist), response.text)

    def test_health_rejects_external_symlink(self):
        (self.dist / "index.html").unlink()
        outside = self.root / "private.html"
        outside.write_text("private-content", encoding="utf-8")
        (self.dist / "index.html").symlink_to(outside)
        self.assertEqual(self.get("/healthz").status_code, 503)

    def test_no_unauthenticated_static_or_api_bypass(self):
        for path in ("/", "/explore.html", "/builder.html", "/reaction-lab.html", "/calculators.html", "/assets/app.js", "/assets/app.js.gz"):
            with self.subTest(path=path):
                response = self.get(path)
                self.assertEqual(response.status_code, 303)
                self.assertNotIn("synthetic", response.text)
                self.assert_private_headers(response)
        for path in ("/api/reactions/catalog", "/api/pubchem/search?q=water", "/api/pubchem/structure?cid=962",
                     "/api/pubchem/depiction?cid=962", "/api/unknown"):
            with self.subTest(path=path):
                response = self.get(path)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(set(response.json), {"error"})
        for path in ("/api/chemistry", "/api/reactions/match", "/api/reactions/run", "/api/reactions/diagram", "/api/reactions/inspect"):
            with self.subTest(path=path):
                self.assertEqual(self.post(path, json={"molfile": "body"}).status_code, 401)
        self.backend.reaction_catalog.assert_not_called()
        self.backend.search_pubchem.assert_not_called()
        self.backend.analyze_molfile.assert_not_called()

    def test_login_sets_partitioned_secure_signed_cookie(self):
        response = self.sign_in(next_page="/explore.html")
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["Location"], "/explore.html")
        cookie = response.headers["Set-Cookie"]
        for attribute in (COOKIE_NAME + "=", "Secure", "HttpOnly", "SameSite=None", "Partitioned", "Path=/", "Expires="):
            self.assertIn(attribute, cookie)
        self.assertNotIn("Domain=", cookie)
        self.assertNotIn(PASSWORD, cookie)
        self.assertNotIn(SECRET, cookie)
        self.assertEqual(self.app.config["PERMANENT_SESSION_LIFETIME"].total_seconds(), 3600)
        self.assertFalse(self.app.config["SESSION_REFRESH_EACH_REQUEST"])
        page = self.get("/explore.html")
        self.assertEqual(page.status_code, 200)
        self.assertIn("synthetic-explore.html", page.text)
        self.assertNotIn("Set-Cookie", page.headers)

    def test_signed_cookie_tampering_and_password_rotation_rejected(self):
        self.sign_in()
        cookie = self.client.get_cookie(COOKIE_NAME, domain="trial.example.test")
        self.assertIsNotNone(cookie)
        tampered = self.app.test_client()
        tampered.set_cookie(COOKIE_NAME, "forged-" + cookie.value, domain="trial.example.test", secure=True)
        self.assertEqual(self.get("/api/reactions/catalog", client=tampered).status_code, 401)
        rotated = self.make_app(TRIAL_PASSWORD="A-different-synthetic-password").test_client()
        rotated.set_cookie(COOKIE_NAME, cookie.value, domain="trial.example.test", secure=True)
        self.assertEqual(self.get("/api/reactions/catalog", client=rotated).status_code, 401)

    def test_calculators_page_preserves_private_sign_in_return_and_can_be_served(self):
        unsigned = self.get("/calculators.html")
        self.assertEqual(unsigned.status_code, 303)
        self.assertEqual(unsigned.headers["Location"], "/login?next=/calculators.html")
        self.assertNotIn("synthetic", unsigned.text)
        self.assert_private_headers(unsigned)
        login = self.get("/login?next=/calculators.html")
        self.assertIn('value="/calculators.html"', login.text)
        response = self.sign_in(next_page="/calculators.html")
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["Location"], "/calculators.html")
        page = self.get("/calculators.html")
        self.assertEqual(page.status_code, 200)
        self.assertIn("synthetic-calculators.html", page.text)
        self.assert_private_headers(page)

    def test_missing_or_cross_origin_post_denied_including_login_logout(self):
        for path in ("/login", "/logout", "/api/chemistry"):
            for origin in (None, "null", "https://evil.example.test", "https://trial.example.test.evil.test", "https://editor.wix.com"):
                with self.subTest(path=path, origin=origin):
                    headers = {} if origin is None else {"Origin": origin}
                    response = self.client.post(path, base_url=ORIGIN, data={"password": PASSWORD}, headers=headers)
                    self.assertEqual(response.status_code, 403)
                    self.assertNotIn("Set-Cookie", response.headers)
        self.backend.analyze_molfile.assert_not_called()

    def test_bad_host_rejected_without_redirect_or_disclosure(self):
        response = self.client.get("/healthz", base_url="https://evil.example.test")
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("Location", response.headers)
        self.assertNotIn("evil.example.test", response.text)
        self.assert_private_headers(response)

    def test_login_page_and_error_do_not_echo_secrets_or_unsafe_return(self):
        response = self.get("/login?next=https://evil.example.test")
        self.assertIn('href="https://trial.example.test/login"', response.text)
        self.assertIn('target="_blank" rel="noopener noreferrer"', response.text)
        self.assertNotIn(PASSWORD, response.text)
        self.assertNotIn(SECRET, response.text)
        self.assertNotIn("evil.example.test", response.text)
        wrong_password = "<script>example-password</script>"
        response = self.sign_in(password=wrong_password, next_page="//evil.example.test")
        self.assertEqual(response.status_code, 401)
        self.assertNotIn(wrong_password, response.text)
        self.assertNotIn("evil.example.test", response.text)
        response = self.sign_in(next_page="//evil.example.test")
        self.assertEqual(response.headers["Location"], "/")

    def test_logout_invalidates_current_browser_session(self):
        self.sign_in()
        self.assertEqual(self.get("/api/reactions/catalog").status_code, 200)
        response = self.post("/logout")
        self.assertEqual(response.status_code, 303)
        self.assertIn("Expires=Thu, 01 Jan 1970", response.headers["Set-Cookie"])
        self.assertEqual(self.get("/api/reactions/catalog").status_code, 401)

    def test_login_content_type_and_size_limits(self):
        self.assertEqual(self.post("/login", json={"password": PASSWORD}).status_code, 415)
        response = self.post("/login", data="password=" + "a" * 5000, content_type="application/x-www-form-urlencoded")
        self.assertEqual(response.status_code, 413)

    def test_api_json_shape_content_type_and_size_limits(self):
        self.sign_in()
        for data, content_type, expected in (("{}", "text/plain", 415), ("not-json", "application/json", 400),
                                             ("[]", "application/json", 422), ("{}", "application/json", 422)):
            with self.subTest(data=data, content_type=content_type):
                response = self.post("/api/chemistry", data=data, content_type=content_type)
                self.assertEqual(response.status_code, expected)
                self.assertEqual(set(response.json), {"error"})
        response = self.post("/api/chemistry", data="a" * (MAX_BODY_BYTES + 1), content_type="application/json")
        self.assertEqual(response.status_code, 413)
        self.backend.analyze_molfile.assert_not_called()

    def test_api_request_handlers_preserve_backend_responses_and_arguments(self):
        self.sign_in()
        self.assertEqual(self.get("/api/reactions/catalog").json, self.backend.reaction_catalog.return_value)
        self.assertEqual(self.get("/api/pubchem/search?q=Water").json, self.backend.search_pubchem.return_value)
        self.backend.search_pubchem.assert_called_once_with("Water")
        response = self.post("/api/chemistry", json={"molfile": "drawing"})
        self.assertEqual(response.json, self.backend.analyze_molfile.return_value)
        self.backend.analyze_molfile.assert_called_once_with("drawing")
        body = {"reactantA": "ethene", "reactantB": "hydrogen", "conditions": {"catalyst": "metal"}, "reactionId": "hydrogenation"}
        for path, function in (("match", self.backend.match_reactions), ("run", self.backend.run_curated_reaction),
                               ("diagram", self.backend.reaction_diagram)):
            response = self.post("/api/reactions/" + path, json=body)
            self.assertEqual(response.json, function.return_value)
            args = ("ethene", "hydrogen", {"catalyst": "metal"})
            function.assert_called_once_with(*(args if path == "match" else ("hydrogenation", *args)))

    def test_structure_and_depiction_binary_formats_and_fallback(self):
        self.sign_in()
        response = self.get("/api/pubchem/structure?cid=962")
        self.assertEqual(response.data, b"source-sdf")
        self.assertIn("chemical/x-mdl-sdfile", response.content_type)
        response = self.get("/api/pubchem/depiction?cid=962")
        self.assertEqual(response.data, b"synthetic-png")
        self.assertEqual(response.content_type, "image/png")
        self.backend.get_pubchem_structure.return_value = None
        response = self.get("/api/pubchem/structure?cid=962")
        self.assertEqual(response.data, b"generated-sdf")
        self.backend.Chem.MolFromSmiles.assert_called_once_with("O")
        self.backend.analyze_molfile.assert_called_once_with("molfile")
        self.backend.get_pubchem_smiles.return_value = None
        self.assertEqual(self.get("/api/pubchem/structure?cid=962").status_code, 404)
        self.backend.get_pubchem_depiction.return_value = None
        self.assertEqual(self.get("/api/pubchem/depiction?cid=962").status_code, 404)
        for cid in ("", "0", "-1", "word", "9" * 11):
            with self.subTest(cid=cid):
                self.assertEqual(self.get("/api/pubchem/structure?cid=" + cid).status_code, 422)

    def test_group_inspection_uses_authenticated_gateway_and_preserves_exact_request(self):
        self.sign_in()
        reference = {"name": "Exact structure", "smiles": "CCO"}
        response = self.post("/api/reactions/inspect", json={"reactant": reference, "include3D": True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, self.backend.inspect_reactant.return_value)
        self.backend.inspect_reactant.assert_called_once_with(reference, True)
        denied = self.client.post("/api/reactions/inspect", base_url=ORIGIN, json={"reactant": reference})
        self.assertEqual(denied.status_code, 403)

    def test_static_traversal_hidden_files_and_outside_symlinks_denied(self):
        self.sign_in()
        outside = self.root / "private.txt"
        outside.write_text("private-content", encoding="utf-8")
        (self.dist / "outside.txt").symlink_to(outside)
        (self.dist / ".env").write_text("synthetic-secret", encoding="utf-8")
        for path in ("/../private.txt", "/%2e%2e/private.txt", "/.env", "/assets/../../private.txt", "/outside.txt",
                     "/server/chemistry_server.py", "/src/shared-molecules.json", "/assets/app.js.gz", "/missing.html"):
            with self.subTest(path=path):
                response = self.get(path)
                self.assertEqual(response.status_code, 404)
                self.assertNotIn("private-content", response.text)
                self.assertNotIn("synthetic-secret", response.text)

    def test_gzip_requires_explicit_nonzero_acceptance_and_correct_mime(self):
        self.sign_in()
        for encoding in ("gzip", "br, gzip;q=0.4"):
            with self.subTest(encoding=encoding):
                response = self.get("/assets/app.js", headers={"Accept-Encoding": encoding})
                self.assertEqual(response.headers["Content-Encoding"], "gzip")
                self.assertEqual(gzip.decompress(response.data), b"synthetic-javascript")
                self.assertIn("javascript", response.content_type)
                self.assertIn("Accept-Encoding", response.headers["Vary"])
                self.assertIn("Cookie", response.headers["Vary"])
                self.assert_private_headers(response)
        for encoding in ("", "br", "*", "gzip;q=0, identity;q=1"):
            with self.subTest(encoding=encoding):
                response = self.get("/assets/app.js", headers={"Accept-Encoding": encoding})
                self.assertNotIn("Content-Encoding", response.headers)
                self.assertEqual(response.data, b"synthetic-javascript")

    def test_login_rate_limit_does_not_trust_x_forwarded_for_and_recovers(self):
        for attempt in range(5):
            response = self.post("/login", data={"password": "wrong-synthetic-password"}, headers={"X-Forwarded-For": f"192.0.2.{attempt}"})
            self.assertEqual(response.status_code, 401)
        response = self.sign_in()
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["Retry-After"], "60")
        self.now += 61
        self.assertEqual(self.sign_in().status_code, 303)

    def test_api_peer_and_global_rate_limits(self):
        self.app = self.make_app(API_REQUESTS_PER_MINUTE=2, API_GLOBAL_REQUESTS_PER_MINUTE=3)
        self.client = self.app.test_client()
        self.sign_in()
        for _ in range(2):
            self.assertEqual(self.get("/api/reactions/catalog").status_code, 200)
        self.assertEqual(self.get("/api/reactions/catalog").status_code, 429)
        self.assertEqual(self.get("/api/reactions/catalog", environ_overrides={"REMOTE_ADDR": "192.0.2.2"}).status_code, 200)
        self.assertEqual(self.get("/api/reactions/catalog", environ_overrides={"REMOTE_ADDR": "192.0.2.3"}).status_code, 429)
        self.assertEqual(self.get("/healthz").status_code, 200)
        self.now += 61
        self.assertEqual(self.get("/api/reactions/catalog").status_code, 200)

    def test_bounded_concurrent_jobs_released_after_completion(self):
        self.app = self.make_app(MAX_CHEMISTRY_JOBS=1)
        first = self.app.test_client()
        second = self.app.test_client()
        self.sign_in(client=first)
        self.sign_in(client=second)
        started = threading.Event()
        release = threading.Event()
        result = []

        def blocking_job(molfile):
            started.set()
            if not release.wait(3):
                raise RuntimeError("Synthetic blocking job timed out")
            return {"representation": "3d", "molfile": molfile}

        self.backend.analyze_molfile.side_effect = blocking_job
        worker = threading.Thread(target=lambda: result.append(self.post("/api/chemistry", client=first, json={"molfile": "drawing"})))
        worker.start()
        try:
            self.assertTrue(started.wait(2))
            response = self.post("/api/chemistry", client=second, json={"molfile": "drawing"})
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.headers["Retry-After"], "2")
        finally:
            release.set()
            worker.join(4)
        self.assertFalse(worker.is_alive())
        self.assertEqual(result[0].status_code, 200)
        self.assertEqual(self.post("/api/chemistry", client=second, json={"molfile": "again"}).status_code, 200)

    def test_expected_errors_retained_unexpected_errors_and_logs_redacted(self):
        self.sign_in()
        self.backend.search_pubchem.side_effect = FakePubChemError("PubChem is temporarily unavailable.")
        response = self.get("/api/pubchem/search?q=synthetic-private-query")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json, {"error": "PubChem is temporarily unavailable."})
        self.backend.analyze_molfile.side_effect = FakeChemistryError("Invalid valence in this drawing.")
        self.assertEqual(self.post("/api/chemistry", json={"molfile": "drawing"}).status_code, 422)
        private_text = "synthetic-private-query " + PASSWORD + " " + str(self.root)
        self.backend.analyze_molfile.side_effect = RuntimeError(private_text)
        with self.assertLogs(self.app.logger, level="WARNING") as logs:
            response = self.post("/api/chemistry", json={"molfile": private_text})
        self.assertEqual(response.status_code, 500)
        self.assertNotIn(private_text, response.text)
        self.assertNotIn(PASSWORD, " ".join(logs.output))
        self.assertNotIn("synthetic-private-query", " ".join(logs.output))
        self.assertNotIn(str(self.root), " ".join(logs.output))
        self.backend.analyze_molfile.side_effect = None
        self.assertEqual(self.post("/api/chemistry", json={"molfile": "drawing"}).status_code, 200)

    def test_actual_rdkit_catalog_and_supported_reaction_keep_shapes(self):
        app = create_app(self.settings)
        client = app.test_client()
        self.sign_in(client=client)
        catalog = self.get("/api/reactions/catalog", client=client)
        self.assertEqual(catalog.status_code, 200)
        self.assertIn("reactants", catalog.json)
        self.assertIn("reactions", catalog.json)
        body = {"reactantA": "bromomethane", "reactantB": "hydroxide", "reactionId": "sn2-bromomethane"}
        product = self.post("/api/reactions/run", client=client, json=body)
        self.assertEqual(product.status_code, 200)
        self.assertTrue(product.json["balanced"])
        self.assertEqual(product.json["productName"], "Methanol")
        self.assertEqual(product.json["product"]["representation"], "3d")
        diagram = self.post("/api/reactions/diagram", client=client, json=body)
        self.assertEqual(diagram.status_code, 200)
        self.assertIn("svg", diagram.json)

    def test_actual_rdkit_invalid_structure_not_logged_to_native_stderr(self):
        app = create_app(self.settings)
        client = app.test_client()
        self.sign_in(client=client)
        # Native RDKit writes to file descriptor 2, not necessarily Python's
        # sys.stderr. The file-descriptor capture proves the production-only
        # startup setting suppresses raw user structure diagnostics.
        submitted = "CCsynthetic_private_invalid_smiles"
        saved_stderr = os.dup(2)
        with tempfile.TemporaryFile(mode="w+b") as capture:
            try:
                os.dup2(capture.fileno(), 2)
                response = self.post("/api/reactions/match", client=client, json={
                    "reactantA": {"smiles": submitted}, "reactantB": "water",
                })
            finally:
                os.dup2(saved_stderr, 2)
                os.close(saved_stderr)
            capture.seek(0)
            captured = capture.read().decode("utf-8", errors="replace")
        self.assertEqual(response.status_code, 422)
        self.assertNotIn(submitted, response.text)
        self.assertNotIn(submitted, captured)
        self.assertEqual(captured, "")


if __name__ == "__main__":
    unittest.main()
