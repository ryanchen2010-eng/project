/* QA_URL=http://127.0.0.1:PORT node tests/sn1-e1-comparison.browser.cjs */
const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const url = process.env.QA_URL;
if (!url || !/^http:\/\/127\.0\.0\.1:\d+$/.test(url)) throw Error('A localhost-only QA_URL is required.');

const response = (page, endpoint) => page.waitForResponse(r => r.url().endsWith(endpoint) && r.status() === 200);
const option = (page, name) => page.locator('.reaction-option').filter({ has: page.locator('strong', { hasText: new RegExp(`^${name} ·`) }) }).first();
async function selectExample(page, id) {
  await page.getByRole('button', { name: 'Examples', exact: true }).click();
  const matched = response(page, '/api/reactions/match');
  await page.locator(`[data-example="${id}"]`).click();
  return (await matched).json();
}
async function diagram(page, name) {
  const pathways = page.locator('.research-pathways');
  if (!await pathways.evaluate(el => el.open)) await pathways.locator(':scope > summary').click();
  const pending = response(page, '/api/reactions/diagram');
  await option(page, name).click();
  return (await pending).json();
}

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true, args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  try {
    for (const width of [1440, 320]) {
      const context = await browser.newContext({ viewport: { width, height: 1000 } });
      try {
        const page = await context.newPage(), errors = [];
        page.on('pageerror', e => errors.push(e.message));
        await page.goto(`${url}/reaction-lab.html`, { waitUntil: 'domcontentloaded' });
        await page.locator('[data-example="tertiary-competition"]').waitFor({ state: 'attached' });
        let match = await selectExample(page, 'tertiary-competition');
        assert.deepEqual(new Set(match.reactions.map(x => x.mechanism)), new Set(['SN1', 'E1']));
        const branch = page.getByRole('region', { name: 'SN1 and E1 shared intermediate' });
        await branch.waitFor();
        assert.match(await branch.textContent(), /tertiary carbocation/);
        assert.match(await branch.textContent(), /2-methylpropan-2-ol/);
        assert.match(await branch.textContent(), /2-methylpropene/);
        assert.match(await branch.textContent(), /exact product ratio/);
        for (const [path, product, steps] of [['SN1', 'CC(C)(C)O', 3], ['E1', 'C=C(C)C', 2]]) {
          const selected = match.reactions.find(x => x.mechanism === path);
          assert.equal(selected.productSmiles, product);
          const payload = await diagram(page, path);
          assert.equal(payload.mechanism.steps.length, steps);
          assert.equal(payload.mechanism.steps[0].state.name, 'Carbocation intermediate');
          assert.equal(payload.mechanism.steps[0].state.atoms.find(a => a.mapId === 2).formalCharge, 1);
          assert.ok(payload.mechanism.steps.at(-1).protonTransfers.length);
          assert.equal(await page.locator('#reaction-mechanism').isHidden(), false);
          const run = response(page, '/api/reactions/run');
          await page.locator('#view-3d').click();
          assert.equal((await (await run).json()).balanced, true);
          await page.locator('#view-2d').click();
        }
        if (!await page.locator('#reaction-temperature').isVisible()) await page.getByRole('button', { name: 'Edit conditions', exact: true }).click();
        const changed = response(page, '/api/reactions/match');
        await page.locator('#reaction-temperature').selectOption('heated');
        match = await (await changed).json();
        assert.deepEqual(new Set(match.reactions.map(x => x.mechanism)), new Set(['SN1', 'E1']));
        if (!await page.locator('.research-pathways').evaluate(el => el.open)) await page.locator('.research-pathways > summary').click();
        await branch.waitFor();
        assert.equal(await page.locator('#result-details').evaluate(el => el.hidden), true);
        for (const path of ['SN1', 'E1']) assert.ok((await diagram(page, path)).mechanism);
        const other = await selectExample(page, 'ethyl-competition');
        assert.deepEqual(new Set(other.reactions.map(x => x.mechanism)), new Set(['SN2', 'E2']));
        assert.equal(await branch.count(), 0);
        for (const path of ['SN2', 'E2']) assert.ok((await diagram(page, path)).mechanism);
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
        assert.deepEqual(errors, []);
        console.log(JSON.stringify({ width, sn1: 'verified', e1: 'verified', temperature: 'switched', sn2e2: 'verified' }));
      } finally { await context.close(); }
    }
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
