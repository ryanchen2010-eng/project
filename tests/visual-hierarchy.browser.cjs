const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const base = process.env.QA_URL;
if (!/^http:\/\/127\.0\.0\.1:\d+$/.test(base || '')) throw Error('Local QA_URL required');
(async () => { const browser = await chromium.launch({channel:'chrome',headless:true, args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try { for (const width of [1440, 320]) { const page = await browser.newPage({viewport:{width,height:900}});
  for (const [path, selector] of [['/','h1'], ['/explore.html','#molecule-search'], ['/builder.html','#ketcher-editor'], ['/reaction-lab.html','#reactant-a'], ['/calculators.html','#calculator-topic']]) {
    await page.goto(base + path, {waitUntil:'domcontentloaded'});
    if (path !== '/calculators.html' || width === 320) await page.locator(selector).waitFor({state:'visible', timeout:30000});
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${path} overflow at ${width}px`);
    if (path === '/explore.html' || path === '/builder.html') {
      if (path === '/explore.html') assert.equal(await page.locator('.molecule-list-hint').isVisible(), width === 320);
      const transfer = page.locator(path === '/explore.html' ? '.explorer-transfer-options' : '.reactant-transfer');
      await transfer.locator('summary').focus(); await page.keyboard.press('Enter');
      assert.notEqual(await transfer.getAttribute('open'), null);
      assert.equal(await transfer.locator('button').count(), 2);
    }
    if (path === '/reaction-lab.html') {
      const diagram = page.locator('#reaction-diagram');
      assert.ok((await diagram.boundingBox()).height < 250, 'empty diagram should be compact');
      await page.locator('#diagram-placeholder').evaluate(el => { el.hidden = true; });
      await page.locator('#diagram-drawing').evaluate(el => { el.hidden = false; });
      assert.ok((await diagram.boundingBox()).height >= (width === 320 ? 320 : 430), 'a diagram keeps the full viewing area');
      const disclosure = page.locator('.condition-explainer').first();
      if (!await disclosure.isVisible()) await page.getByRole('button', {name:'Edit conditions', exact:true}).click();
      assert.equal(await disclosure.getAttribute('open'), null);
      await disclosure.locator('summary').focus(); await page.keyboard.press('Enter');
      assert.notEqual(await disclosure.getAttribute('open'), null);
      assert.match(await disclosure.innerText(), /3D does not simulate temperature/);
      assert.match(await page.locator('.lab-notice').innerText(), /not a prediction/i);
    }
  }
  await page.close(); console.log(`Hierarchy checks passed at ${width}px`);
} } finally { await browser.close(); } })().catch(e => {console.error(e);process.exitCode=1;});
