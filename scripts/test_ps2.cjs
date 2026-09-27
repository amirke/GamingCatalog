const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const fs = require('node:fs');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const sandbox = {window: {}};
vm.runInNewContext(fs.readFileSync(path.join(root, 'data/catalog.js'), 'utf8'), sandbox);
const ps4 = sandbox.window.GAMING_CATALOG.games[0].id;
(async () => {
  const browser = await chromium.launch({headless: true, channel: 'msedge'});
  try {
    const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
    await page.route('https://**/*', route => route.abort());
    const errors = []; page.on('pageerror', error => errors.push(error.message));
    await page.goto(pathToFileURL(path.join(root, 'index.html')).href);
    assert.equal(await page.locator('#total').textContent(), '911');
    const initial = await page.evaluate(() => ({games: window.PS2_GAMES, state: window.catalogStore.get()}));
    assert.equal(initial.games.length, 38);
    assert.equal(new Set(initial.games.map(g => g.id)).size, 38);
    for (const game of initial.games) {
      assert.equal(initial.state.entries[game.id].downloaded.value, true);
      assert.ok(game.description.he.length > 25 && game.description.en.length > 25);
      assert.ok(game.genres.length > 0 && new URL(game.descriptionSource.url).protocol === 'https:');
    }
    assert.ok(initial.games.find(g => g.titleId === 'SLES53934').description.en.includes('water-skiing'));
    await page.evaluate(id => {
      const entries = {}; entries[id] = {downloaded: {value: false, updatedAt: 100}, notes: {value: 'Keep existing PS4 notes', updatedAt: 100}};
      localStorage.setItem('gaming-catalog-state-v1', JSON.stringify({schemaVersion: 1, entries}));
    }, ps4);
    await page.reload();
    assert.deepEqual(await page.evaluate(id => window.catalogStore.get().entries[id], ps4), {downloaded: {value: false, updatedAt: 100}, notes: {value: 'Keep existing PS4 notes', updatedAt: 100}});
    await page.selectOption('#platformFilter', 'PS2');
    assert.equal(await page.locator('#resultCount').textContent(), '(38)');
    assert.equal(await page.locator('[data-field=downloaded]:checked').count(), 24);
    assert.equal(await page.locator('.game-description').count(), 24);
    assert.equal(await page.locator('.game-description').first().getAttribute('lang'), 'he');
    assert.equal(await page.locator('a[href*="archive.org"]').count(), 0);
    assert.ok((await page.locator('.links a[href*="google.com/search"]').first().getAttribute('href')).includes('PS2'));
    await page.selectOption('#genreFilter', 'music');
    assert.equal(await page.locator('#resultCount').textContent(), '(10)');
    await page.selectOption('#genreFilter', 'sports');
    assert.equal(await page.locator('#resultCount').textContent(), '(3)');
    await page.selectOption('#genreFilter', 'unknown');
    assert.equal(await page.locator('#resultCount').textContent(), '(0)');
    await page.selectOption('#genreFilter', 'all');
    await page.click('#next');
    assert.equal(await page.locator('[data-field=downloaded]:checked').count(), 14);
    assert.equal(await page.locator('.game-description').count(), 14);
    await page.click('#previous');
    await page.click('[data-letter="#"]');
    assert.equal(await page.locator('#resultCount').textContent(), '(2)');
    await page.click('[data-letter=all]');
    await page.click('#listView');
    await page.locator('.row-toggle').first().click();
    assert.equal(await page.locator('.row-toggle').first().getAttribute('aria-expanded'), 'true');
    assert.equal(await page.locator('.game-description').first().isVisible(), true);
    const firstId = await page.locator('.game').first().getAttribute('data-id');
    await page.locator('[data-field=downloaded]').first().uncheck();
    await page.reload();
    assert.equal(await page.locator('[data-field=downloaded]').first().isChecked(), false);
    const secondId = initial.games.find(g => g.id !== firstId).id;
    await page.evaluate(id => window.catalogStore.apply({schemaVersion: 1, entries: {[id]: {downloaded: {value: false, updatedAt: 500}}}}), secondId);
    await page.reload();
    assert.equal(await page.evaluate(id => window.catalogStore.get().entries[id].downloaded.value, secondId), false);
    await page.selectOption('#downloadFilter', 'yes');
    assert.equal(await page.locator('#resultCount').textContent(), '(36)');
    await page.selectOption('#downloadFilter', 'all');
    const backup = await page.evaluate(() => JSON.stringify(window.catalogStore.get()));
    await page.locator('#importFile').setInputFiles({name: 'ps2.backup.json', mimeType: 'application/json', buffer: Buffer.from(backup)});
    await page.waitForFunction(() => !document.getElementById('notice').hidden);
    assert.equal(await page.evaluate(id => window.catalogStore.get().entries[id].downloaded.value, firstId), false);
    await page.click('#language');
    await page.waitForFunction(() => document.documentElement.lang === 'en');
    assert.equal(await page.locator('#platformFilter').inputValue(), 'PS2');
    assert.equal(await page.locator('#resultCount').textContent(), '(38)');
    assert.equal(await page.locator('.game-description').first().getAttribute('lang'), 'en');
    assert.equal(await page.locator('.game-description h4').first().textContent(), 'About the game');
    await page.selectOption('#platformFilter', 'PS4');
    assert.equal(await page.locator('#resultCount').textContent(), '(873)');
    await page.click('#resetFilters');
    assert.equal(await page.locator('#resultCount').textContent(), '(911)');
    await page.setViewportSize({width: 390, height: 844});
    await page.selectOption('#platformFilter', 'PS2');
    for (const selector of ['#cardsView', '#listView']) {
      await page.click(selector);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    }
    if (process.env.PS2_SCREENSHOT) {
      await page.setViewportSize({width: 1440, height: 1100});
      await page.click('#cardsView');
      await page.screenshot({path: process.env.PS2_SCREENSHOT});
    }
    assert.deepEqual(errors, []);
    console.log('PASS: 38 PS2 entries, 911 total, filters, cards/list, downloaded defaults, existing PS4 state, persisted uncheck, remote merge, backup import, English.');
  } finally { await browser.close(); }
})().catch(error => {console.error(error); process.exitCode = 1;});
