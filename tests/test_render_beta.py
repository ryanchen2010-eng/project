"""Deployment-only contracts. Existing chemistry fixtures stay unchanged."""
import importlib.util
import os
from pathlib import Path
import secrets
import json
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from server.production_app import create_app

ROOT = Path(__file__).resolve().parents[1]


class RenderBetaTests(unittest.TestCase):
    def environment(self):
        return {'CAPSTONE_TRIAL_PASSWORD': 'Synthetic-beta-test-password',
                'CAPSTONE_SESSION_SECRET': secrets.token_hex(32),
                'RENDER_EXTERNAL_URL': 'https://assigned-beta.example.test'}

    def test_render_actual_origin_and_standalone_frames_default_fail_closed(self):
        with patch.dict(os.environ, self.environment(), clear=True):
            app = create_app({}, chemistry_backend=object())
        client = app.test_client()
        response = client.get('/login', base_url='https://assigned-beta.example.test')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Wix frame', response.text)
        self.assertIn("frame-ancestors 'self' https://assigned-beta.example.test", response.headers['Content-Security-Policy'])
        self.assertEqual(client.get('/healthz', base_url='https://evil.example.test').status_code, 400)
        self.assertEqual(client.post('/login', base_url='https://assigned-beta.example.test',
                                    data={'password': 'Synthetic-beta-test-password'}, headers={'Origin': 'https://evil.example.test'}).status_code, 403)

    def test_explicit_origin_wins_and_empty_or_http_values_do_not_fallback(self):
        for value in ('', 'http://assigned-beta.example.test', 'https://localhost', 'https://a.example.test/path'):
            with self.subTest(value=value), patch.dict(os.environ, {**self.environment(), 'CAPSTONE_PUBLIC_ORIGIN': value}, clear=True):
                with self.assertRaises(ValueError): create_app({}, chemistry_backend=object())
        with patch.dict(os.environ, {**self.environment(), 'CAPSTONE_PUBLIC_ORIGIN': 'https://custom.example.test'}, clear=True):
            app = create_app({}, chemistry_backend=object())
        self.assertEqual(app.config['TRUSTED_HOSTS'], ['custom.example.test'])

    def test_render_missing_secrets_or_origin_does_not_start(self):
        for field in ('CAPSTONE_TRIAL_PASSWORD', 'CAPSTONE_SESSION_SECRET', 'RENDER_EXTERNAL_URL'):
            env = self.environment(); del env[field]
            with self.subTest(field=field), patch.dict(os.environ, env, clear=True):
                with self.assertRaises(ValueError): create_app({}, chemistry_backend=object())

    def test_login_form_policy_preserves_origin_without_relaxing_csrf(self):
        with patch.dict(os.environ, self.environment(), clear=True):
            app = create_app({}, chemistry_backend=object())
        client = app.test_client(); base = 'https://assigned-beta.example.test'
        self.assertEqual(client.get('/login', base_url=base).headers['Referrer-Policy'], 'same-origin')
        self.assertEqual(client.get('/healthz', base_url=base).headers['Referrer-Policy'], 'no-referrer')
        for origin in ('null', 'https://evil.example.test'):
            self.assertEqual(client.post('/login', base_url=base, data={'password': 'Synthetic-beta-test-password'},
                                        headers={'Origin': origin}).status_code, 403)
        self.assertEqual(client.post('/login', base_url=base, data={'password': 'Synthetic-beta-test-password'},
                                    headers={'Origin': base}).status_code, 303)

    def test_gunicorn_port_and_hard_worker_timeout_are_explicit(self):
        path = ROOT / 'server/gunicorn.conf.py'
        spec = importlib.util.spec_from_file_location('beta_config', path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(os.environ, {'PORT': '10456'}): spec.loader.exec_module(module)
        self.assertEqual(module.bind, '0.0.0.0:10456')
        self.assertEqual((module.workers, module.worker_class, module.threads), (1, 'sync', 1))
        self.assertEqual(module.timeout, 90); self.assertIsNone(module.accesslog)
        for value in ('0', '65536', '8000;echo nope'):
            with self.subTest(value=value), patch.dict(os.environ, {'PORT': value}):
                with self.assertRaises(ValueError): spec.loader.exec_module(module)

    def test_all_python_runtime_modules_are_in_docker_context_and_image(self):
        image = (ROOT / 'Dockerfile').read_text(); ignored = (ROOT / '.dockerignore').read_text()
        self.assertIn('COPY server/*.py ./server/', image)
        self.assertIn('!server/*.py', ignored)
        for p in ('reaction_engine.py', 'reaction_conditions.py', 'aldehyde_oxidation_conditions.py',
                  'reaction_condition_guidance.py', 'stereochemistry.py', 'molecular_graph.py'):
            self.assertTrue((ROOT / 'server' / p).is_file())
        self.assertNotRegex(image, r'(?m)^COPY\s+\.\s')
        self.assertIn('--only-binary=:all:', image)
        self.assertIn('from server import chemistry_server', image)

    def test_blueprint_has_one_manual_free_service_no_secrets_or_fake_url(self):
        blueprint = (ROOT / 'render.yaml').read_text()
        self.assertEqual(blueprint.count('- type: web'), 1)
        for field in ('runtime: docker', 'plan: free', 'autoDeployTrigger: "off"', 'healthCheckPath: /healthz'):
            self.assertIn(field, blueprint)
        self.assertEqual(blueprint.count('sync: false'), 2)
        self.assertNotIn('generateValue:', blueprint)
        self.assertNotRegex(blueprint, r'(?m)^\s*(?:databases|repo|image|disk):')

    def test_rdkit_drawing_system_dependency_is_installed_in_python_stage(self):
        image = (ROOT / 'Dockerfile').read_text()
        runtime = image.split('FROM python:3.12-slim-bookworm AS trial', 1)[1]
        install = runtime.split('apt-get install -y --no-install-recommends ', 1)[1].split('\\', 1)[0]
        self.assertIn('libexpat1', install.split())
        self.assertLess(runtime.index('libexpat1'), runtime.index('pip install'))
        # Keep the real import gate: missing native drawing dependencies must fail
        # during the image build, never after a supposedly successful deployment.
        self.assertIn('from server import chemistry_server', runtime)
        diagrams = (ROOT / 'server/reaction_diagrams.py').read_text()
        self.assertIn('from rdkit.Chem.Draw import rdMolDraw2D', diagrams)

    def test_release_allowlist_contains_all_runtime_but_no_local_data(self):
        from scripts.prepare_beta_release import source_files
        paths = {str(p.relative_to(ROOT)) for p in source_files()}
        self.assertIn('render.yaml', paths)
        self.assertIn('server/reaction_engine.py', paths)
        self.assertIn('src/shared-molecules.json', paths)
        self.assertFalse(any(p.startswith(('tests/', 'docs/', 'history/', '.git/', '.venv/', 'node_modules/')) for p in paths))
        self.assertFalse(any('.env' in p or p.endswith(('.key', '.pem', '.pyc')) for p in paths))

    def test_ketcher_mixed_module_requires_are_transformed_for_production(self):
        config = (ROOT / 'vite.config.ts').read_text()
        self.assertIn('transformMixedEsModules: true', config)

    def test_release_archive_captures_dirty_bytes_and_cannot_overwrite(self):
        from scripts.prepare_beta_release import freeze
        with tempfile.TemporaryDirectory(prefix='capstone-release-test-') as directory:
            root = Path(directory)
            sample = root / 'Dockerfile'; sample.write_text('synthetic-safe-image')
            with patch('scripts.prepare_beta_release.source_files', return_value=[sample]), \
                 patch('scripts.prepare_beta_release.subprocess.check_output', side_effect=['base-commit\n', '?? Dockerfile\n']):
                output = freeze('synthetic-beta-v1', root)
            manifest = json.loads((output / 'manifest.json').read_text())
            self.assertTrue(manifest['dirtySource']); self.assertFalse(manifest['published'])
            with tarfile.open(output / manifest['archive']) as archive:
                self.assertEqual(archive.getnames(), ['synthetic-beta-v1/Dockerfile'])
                self.assertEqual(archive.extractfile(archive.getmembers()[0]).read(), b'synthetic-safe-image')
            with patch('scripts.prepare_beta_release.source_files', return_value=[sample]), \
                 patch('scripts.prepare_beta_release.subprocess.check_output', side_effect=['base-commit\n', '']):
                with self.assertRaises(FileExistsError): freeze('synthetic-beta-v1', root)

    def test_release_rejects_path_names_and_credentials(self):
        from scripts.prepare_beta_release import freeze, TOKEN
        for name in ('../bad', '/tmp/bad', 'beta/release', 'Beta V1'):
            with self.subTest(name=name), self.assertRaises(ValueError): freeze(name)
        self.assertIsNotNone(TOKEN.search(b'-----BEGIN PRIVATE KEY-----'))


if __name__ == '__main__': unittest.main()
