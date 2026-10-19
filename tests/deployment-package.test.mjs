import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, readFile, stat, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { gunzipSync } from 'node:zlib';

const project = fileURLToPath(new URL('../', import.meta.url));

test('deployment compression preserves large asset bytes and skips tiny/binary files', async () => {
  const taskDirectory = await mkdtemp(join(tmpdir(), 'capstone-compression-test-'));
  try {
    await mkdir(join(taskDirectory, 'dist', 'assets'), { recursive: true });
    const content = 'const molecule = "ethanol";\n'.repeat(200);
    const asset = join(taskDirectory, 'dist', 'assets', 'sample.js');
    await writeFile(asset, content);
    await writeFile(join(taskDirectory, 'dist', 'tiny.html'), '<p>small</p>');
    await writeFile(join(taskDirectory, 'dist', 'sample.png'), 'binary-fixture'.repeat(200));
    const run = spawnSync(process.execPath, [resolve(project, 'scripts/compress-dist.mjs')], {
      cwd: taskDirectory, encoding: 'utf8',
    });
    assert.equal(run.status, 0, run.stderr);
    const compressed = await readFile(`${asset}.gz`);
    assert.equal(gunzipSync(compressed).toString(), content);
    assert.ok(compressed.length < Buffer.byteLength(content));
    await assert.rejects(stat(join(taskDirectory, 'dist', 'tiny.html.gz')), { code: 'ENOENT' });
    await assert.rejects(stat(join(taskDirectory, 'dist', 'sample.png.gz')), { code: 'ENOENT' });
  } finally {
    // Only remove the isolated, newly-created test fixture directory.
    await rm(taskDirectory, { recursive: true, force: true });
  }
});

test('deployment image names the real gateway, shared catalog, and every page', async () => {
  const dockerfile = await readFile(resolve(project, 'Dockerfile'), 'utf8');
  assert.match(dockerfile, /server\.production_app:create_app\(\)/);
  assert.match(dockerfile, /COPY src\/shared-molecules\.json/);
  for (const file of ['index.html', 'explore.html', 'builder.html', 'reaction-lab.html', 'calculators.html']) {
    assert.ok(dockerfile.includes(file));
    assert.ok((await stat(resolve(project, file))).isFile());
  }
  assert.doesNotMatch(dockerfile, /^COPY\s+\.\s/m);
  assert.doesNotMatch(dockerfile, /ARG\s+CAPSTONE_(TRIAL_PASSWORD|SESSION_SECRET)/);
  const config = await readFile(resolve(project, 'server/gunicorn.conf.py'), 'utf8');
  assert.match(config, /^workers = 1$/m);
  assert.match(config, /^accesslog = None$/m);
});

test('deployment context excludes credentials and project history by default', async () => {
  const ignored = await readFile(resolve(project, '.dockerignore'), 'utf8');
  assert.equal(ignored.split('\n')[0], '*');
  assert.ok(!ignored.includes('!history/'));
  assert.ok(!ignored.includes('!.git/'));
  assert.ok(!ignored.includes('!.venv/'));
  assert.match(ignored, /\*\*\/\.env\*/);
  assert.match(ignored, /\*\*\/\*\.key/);
  assert.match(ignored, /^!calculators\.html$/m);
  const gitIgnored = await readFile(resolve(project, '.gitignore'), 'utf8');
  assert.match(gitIgnored, /^\.env$/m);
  assert.match(gitIgnored, /^\.env\.\*$/m);
});
