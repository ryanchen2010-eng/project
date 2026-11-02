const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const base = process.env.QA_URL;
if (!/^http:\/\/127\.0\.0\.1:\d+$/.test(base || '')) throw Error('Local QA_URL required');
(async () => {
  const browser = await chromium.launch({channel: 'chrome', headless: true, args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']});
  try {
    for (const width of [1440, 320]) {
      const page = await browser.newPage({viewport: {width, height: 900}});
      const errors = [];
      page.on('pageerror', e => errors.push(e.message));
      await page.route('**/api/pubchem/search?**', route => route.fulfill({json: {limited: false, results: [{cid: 24872, name: 'Rhodium chloride', formula: 'RhCl3', structure: '[Rh+3].[Cl-].[Cl-].[Cl-]', ionicAssembly: true}]}}));
      await page.goto(`${base}/explore.html`, {waitUntil: 'domcontentloaded'});
      const structure = await page.evaluate(async () => {
        const el = document.createElement('div'); el.style.width = '200px'; el.style.height = '200px'; document.body.append(el);
        const v = window.$3Dmol.createViewer(el);
        const cif = await (await fetch('/crystals/rhodium-trichloride-cod-1534198.cif')).text();
        const { rhodiumUnitCell } = await import('/src/crystal-unit-cell.ts');
        const m = v.addModel(rhodiumUnitCell(cif), 'cif', {assignBonds: false});
        return m.selectedAtoms({}).map(a => ({elem: a.elem, x: a.x, y: a.y, z: a.z}));
      });
      assert.equal(structure.length, 16);
      assert.equal(structure.filter(atom => atom.elem === 'Rh').length, 4);
      assert.equal(structure.filter(atom => atom.elem === 'Cl').length, 12);
      const distances = structure.filter(a => a.elem === 'Rh').flatMap(a => structure.filter(b => b.elem === 'Cl').map(b => Math.hypot(a.x-b.x, a.y-b.y, a.z-b.z)));
      assert.ok(distances.some(d => d > 2.2 && d < 2.5), 'Expected an Rh–Cl neighbor in the displayed cell');
      for (let i = 0; i < structure.length; i++) for (let j = 0; j < i; j++)
        assert.ok(Math.hypot(structure[i].x - structure[j].x, structure[i].y - structure[j].y, structure[i].z - structure[j].z) > 0.1);
      await page.locator('#molecule-search').fill('Rhodium chloride');
      await page.locator('#molecule-search-form button').click();
      await page.locator('#crystal-view').waitFor({state: 'visible'});
      assert.equal(await page.locator('.viewer-stage').isHidden(), true);
      await page.locator('#crystal-view').click();
      await page.waitForFunction(() => document.querySelector('#viewer-status')?.textContent?.includes('ready') || document.querySelector('#viewer-status')?.classList.contains('is-error'), null, {timeout: 30000});
      assert.match(await page.locator('#viewer-status').textContent(), /Crystal unit cell ready/);
      assert.match(await page.locator('#structure-provenance').textContent(), /extended solid.*not a discrete molecule/i);
      assert.equal(await page.locator('#crystal-view').getAttribute('aria-pressed'), 'true');
      await page.locator('#explorer-measurements summary').first().click();
      await page.locator('#explorer-measurements select').selectOption('distance');
      assert.match(await page.locator('#explorer-measurements').textContent(), /choose/i);
      await page.getByText('Choose atoms by list').click();
      const atomButtons = page.locator('.measurement-atom-buttons button');
      assert.equal(await atomButtons.count(), 16);
      await atomButtons.nth(0).click(); await atomButtons.nth(1).click();
      assert.match(await page.locator('.measurement-value').textContent(), /Å/);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.locator('#crystal-info').click();
      assert.equal(await page.locator('.viewer-stage').isHidden(), true);
      await page.locator('#explorer-solution-calculator > summary').click();
      await page.locator('#explorer-solution-calculator-amount').fill('1');
      await page.getByLabel('Unit for Amount of solute').selectOption('mol');
      await page.locator('#explorer-solution-calculator-volume').fill('1');
      await page.getByLabel('Unit for Final solution volume').selectOption('L');
      await page.locator('#explorer-solution-calculator .solution-submit').click();
      assert.match(await page.locator('#explorer-solution-calculator .solution-output').textContent(), /1(?:\.0+)?\s*(?:mol\/L|M)/i);
      await page.goto(`${base}/calculators.html#solutions`, {waitUntil: 'domcontentloaded'});
      await page.locator('#hub-solution-calculator-amount').fill('2');
      await page.getByLabel('Unit for Amount of solute').selectOption('mol');
      await page.locator('#hub-solution-calculator-volume').fill('1');
      await page.getByLabel('Unit for Final solution volume').selectOption('L');
      await page.locator('#hub-solution-calculator .solution-submit').click();
      assert.match(await page.locator('#hub-solution-calculator .solution-output').textContent(), /2(?:\.0+)?\s*(?:mol\/L|M)/i);
      assert.deepEqual(errors, []);
      console.log(`Crystal viewer passed at ${width}px`);
      await page.close();
    }
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
