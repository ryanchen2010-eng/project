import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const css = await readFile(new URL('../src/reaction-lab.css', import.meta.url), 'utf8');
const inspector = await readFile(new URL('../src/atom-inspector.ts', import.meta.url), 'utf8');

test('mechanism colors share the measured visible halo, never the invisible hit target', () => {
  for (const state of ['source', 'destination']) {
    assert.match(css, new RegExp(`\\.atom-target\\.is-electron-${state} \\.atom-glow \\{[^}]*opacity: 1`));
  }
  assert.doesNotMatch(css, /\.is-electron-[\w.-]+\s+\.atom-hit\s*\{/);
});

test('sanitizer permits label-sized ellipse halos without changing mapped interaction attributes', () => {
  assert.match(inspector, /'ellipse'/);
  for (const attribute of ['cx', 'cy', 'rx', 'ry', 'data-atom-map', 'tabindex', 'aria-label']) {
    assert.ok(inspector.includes(`'${attribute}'`));
  }
});

test('keyboard focus uses a visible dashed measured halo instead of an overlapping rectangle', () => {
  assert.match(css, /\.lab-shell \.atom-target:focus-visible \{ outline: none; \}/);
  assert.match(css, /\.atom-target:focus-visible \.atom-glow \{[^}]*stroke-width: 3;[^}]*stroke-dasharray: 3 2/);
  assert.match(css, /\.atom-target:focus-visible \.atom-glow \{ opacity: 1; \}/);
});
