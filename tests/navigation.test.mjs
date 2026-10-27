import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const read = (path) => readFile(new URL(`../${path}`, import.meta.url), 'utf8');

test('the production build includes Home and all four chemistry tools', async () => {
  const config = await read('vite.config.ts');
  for (const [name, file] of [
    ['home', 'index.html'],
    ['explorer', 'explore.html'],
    ['builder', 'builder.html'],
    ['reactionLab', 'reaction-lab.html'],
    ['calculators', 'calculators.html'],
  ]) {
    assert.ok(config.includes(`${name}: resolve(__dirname, '${file}'),`), `${file} must be a build entry`);
    assert.match(await read(file), /<title>.+<\/title>/);
  }
});

test('the Home page links to each tool and explains the teaching limits', async () => {
  const home = await read('index.html');
  assert.match(home, /<h1 id="home-title">/);
  for (const target of ['/explore.html', '/builder.html', '/reaction-lab.html', '/calculators.html']) {
    assert.ok(home.includes(`href="${target}"`), `${target} must be reachable from Home`);
  }
  assert.match(home, /No match does not mean no reaction/);
  assert.match(home, /Four Tools\. One Workspace\./);
  assert.equal((home.match(/<article class="tool-card">/g) ?? []).length, 4);
  assert.doesNotMatch(home, /3Dmol-min\.js/, 'Home should not load the 3D viewer unnecessarily');
});

test('Home uses title case for key headings and actions without changing descriptive or chemical text', async () => {
  const home = await read('index.html');
  for (const heading of [
    'A Clearer Way to Explore Molecules.',
    'Explore Molecules',
    'Build a Molecule',
    'Try a Reaction',
    'Chemistry Calculators',
    'Learn with Models, Not Predictions.',
  ]) {
    assert.ok(home.includes(`>${heading}</h`), `${heading} must retain its intended capitalization`);
  }
  assert.match(home, />Explore Molecules <span/);
  assert.match(home, />Draw a Structure <span/);
  assert.match(home, /Explore molecules, draw structures, compare reactions, and calculate quantities\./);
  assert.match(home, /class="figure-formula">H₂O<\/span>/);
});

test('every tool links back to Home and to the other tools', async () => {
  for (const file of ['src/main.ts', 'src/builder.ts', 'src/reaction-lab.ts']) {
    const source = await read(file);
    for (const target of ['/', '/explore.html', '/builder.html', '/reaction-lab.html', '/calculators.html']) {
      assert.ok(source.includes(`href="${target}"`), `${file} must link to ${target}`);
    }
  }
  const calculators = await read('calculators.html');
  for (const target of ['/', '/explore.html', '/builder.html', '/reaction-lab.html', '/calculators.html']) {
    assert.ok(calculators.includes(`href="${target}"`), `Calculators must link to ${target}`);
  }
  assert.doesNotMatch(calculators, /3Dmol-min\.js/, 'Calculators should not load the 3D viewer unnecessarily');
});

test('Reaction Lab offers a concise guide to every supported reaction type', async () => {
  const lab = await read('src/reaction-lab.ts');
  assert.match(lab, /<details class="reaction-guide">/);
  for (const type of ['Hydrogenation', 'Bromination', 'Chlorination', 'Hydrohalogenation', 'Hydration', 'E1', 'E2', 'SN1', 'SN2', 'Alcohol oxidation', 'Carbonyl hydrogenation', 'Esterification', 'Ester hydrolysis']) {
    assert.ok(lab.includes(`${type}:`), `${type} must appear in the guide`);
  }
});
