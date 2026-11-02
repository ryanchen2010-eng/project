/* Run against a localhost QA server: QA_URL=http://127.0.0.1:PORT node tests/basic-conditions.browser.cjs */
const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const url = process.env.QA_URL;
if (!url || !/^http:\/\/127\.0\.0\.1:\d+$/.test(url)) throw Error('QA_URL must be a localhost-only QA server.');

const fixtures = [
  ['SN2', 'CBr', 'hydroxide', 'Hydroxide ion'],
  ['E2', 'CCBr', 'hydroxide', 'Hydroxide ion'],
  ['Ester saponification', 'CC(=O)OCC', 'hydroxide', 'Hydroxide ion'],
  ['Bromination', 'C=C', 'bromine', 'Bromine'],
];

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true,
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  try {
    for (const width of [1440, 320]) for (const fixture of fixtures) {
      const context = await browser.newContext({ viewport: { width, height: 1000 } });
      try {
        await context.addInitScript((f) => {
          const substrate = { id: 'drawn-1', name: 'Diagnostic substrate', formula: 'C', smiles: f[1], aliases: [] };
          sessionStorage.setItem('molecule-playground.reaction-draft.v1', JSON.stringify({
            values: [substrate.name, f[3]], selectedIds: ['drawn-1', f[2]], drawnInputs: [substrate, null],
            conditions: { temperature: 'ambient', solvent: 'aqueous-protic', catalyst: '' },
          }));
        }, fixture);
        const page = await context.newPage();
        const errors = [];
        page.on('pageerror', (error) => errors.push(error.message));
        await page.goto(`${url}/reaction-lab.html`, { waitUntil: 'domcontentloaded' });
        // Restoration may complete before listeners are attached; wait for its visible result instead.
        await page.locator('.reaction-option').first().waitFor({ timeout: 30000 });
        if (!await page.locator('#reaction-catalyst').isVisible()) {
          await page.getByRole('button', { name: 'Edit conditions', exact: true }).click();
        }
        const match = page.waitForResponse((r) => r.url().endsWith('/api/reactions/match') && r.status() === 200);
        await page.locator('#reaction-catalyst').selectOption('base');
        await match;
        const option = page.locator('.reaction-option').filter({
          has: page.locator('strong', { hasText: new RegExp(`^${fixture[0]} ·`) }),
        }).first();
        await option.waitFor({ timeout: 30000 });
        const diagramResponse = page.waitForResponse((r) => r.url().endsWith('/api/reactions/diagram') && r.status() === 200);
        await option.click();
        const diagram = await (await diagramResponse).json();
        assert.match(await page.locator('#condition-assessment').textContent(), /actual hydroxide|not validated/i);
        const blocked = fixture[0] === 'Bromination';
        assert.equal(diagram.assessment.canRun === false, blocked);
        assert.equal(await page.locator('#view-3d').isDisabled(), blocked);
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
        assert.deepEqual(errors, []);
        console.log(JSON.stringify({ width, pathway: fixture[0], baseSelected: true, blocked }));
      } finally {
        await context.close();
      }
    }
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
