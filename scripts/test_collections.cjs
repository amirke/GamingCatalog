const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
(async () => {
  const browser = await chromium.launch({headless: true, channel: 'msedge'});
  try {
    const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
    await page.route('https://**/*', route => process.env.LIVE_COVER && route.request().url().includes('steamstatic.com') ? route.continue() : route.abort());
    const errors = []; page.on('pageerror', error => errors.push(error.message));
    await page.goto(pathToFileURL(path.resolve(__dirname, '../index.html')).href);
    const data = await page.evaluate(() => ({collections: window.GAME_COLLECTIONS.entries, games: [...window.GAMING_CATALOG.games, ...window.PS2_GAMES, ...window.MANUAL_GAMES]}));
    const ids = new Set(data.games.map(g => g.id));
    assert.equal(ids.size, 911);
    assert.equal(Object.values(data.collections).filter(c => c.status === 'complete').length, 48);
    for (const [id, entry] of Object.entries(data.collections)) {
      assert.ok(ids.has(id));
      assert.equal(new Set(entry.items).size, entry.items.length);
      if (entry.status === 'complete') assert.ok(entry.items.length > 1 && entry.source.startsWith('https://'));
    }
    const contents = title => data.collections[data.games.find(g => g.title === title).id];
    assert.equal(contents('Taito Legends 2').items.length, 39);
    assert.ok(!contents('Taito Legends 2').items.includes('Bubble Symphony'));
    assert.equal(contents('2004 Classics Hitlist').items.length, 11);
    assert.equal(contents('Best Games Ever 1').items.length, 4);
    assert.equal(contents('Arcade Action - 30 Games').items.length, 30);
    for (let i=1;i<=3;i++) assert.equal(contents(`Atari Flashback Classics vol.${i}`).items.length, 50);
    await page.locator('#search').fill('Wisdom Seekers');
    assert.equal(await page.locator('#resultCount').textContent(), '(1)');
    assert.match(await page.locator('.game h3').textContent(), /Arcade Action/);
    await page.click('.collection-contents summary');
    assert.equal(await page.locator('.included-games li').count(), 30);
    await page.click('#listView');
    assert.equal(await page.locator('.collection-contents').isVisible(), false);
    const height = await page.locator('.game-row').evaluate(el => el.getBoundingClientRect().height);
    assert.ok(height < 100, `Collapsed row too tall: ${height}`);
    await page.click('.row-toggle');
    assert.equal(await page.locator('.collection-contents').isVisible(), true);
    await page.click('#language');
    assert.match(await page.locator('.collection-contents summary').textContent(), /Included|collection/i);
    await page.click('#resetFilters');
    await page.locator('#search').fill('Smurfs: Village Party');
    assert.equal(await page.locator('#resultCount').textContent(), '(1)');
    await page.click('#cardsView');
    assert.match(await page.locator('.game h3').textContent(), /2024/);
    assert.match(await page.locator('.game-description').textContent(), /50 mini-games/);
    assert.equal(await page.locator('.genre-tag').count(), 2);
    assert.match(await page.locator('.source-review').textContent(), /camera/);
    assert.equal(await page.locator('.local-score').textContent(), '6/10');
    assert.match(await page.locator('.review-block').textContent(), /Xbox Series X/);
    assert.doesNotMatch(await page.locator('.review-block').textContent(), /No critic score found/);
    await page.selectOption('#yearFilter', '2024');
    assert.equal(await page.locator('#resultCount').textContent(), '(1)');
    await page.selectOption('#genreFilter', 'party');
    assert.equal(await page.locator('#resultCount').textContent(), '(1)');
    await page.locator('[data-field=interested]').check();
    await page.locator('[data-field=interestedReason]').fill('Play with family');
    await page.reload();
    assert.equal(await page.locator('[data-field=interestedReason]').inputValue(), 'Play with family');
    await page.click('#language');
    assert.match(await page.locator('.source-review').textContent(), /מצלמה/);
    if (process.env.LIVE_COVER) {
      await page.locator('.game').scrollIntoViewIfNeeded();
      await page.waitForFunction(() => document.querySelector('.cover img')?.naturalWidth > 0);
      await page.click('.cover');
      await page.waitForFunction(() => document.querySelector('#largeImage')?.naturalWidth > 0);
      await page.click('#closeImage');
    }
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.click('#resetFilters');
    await page.locator('#search').fill('Wisdom Seekers');
    await page.click('.collection-contents summary');
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    assert.deepEqual(errors, []);
    console.log('PASS: collection identities/content, contained-title search, bilingual collapse, Smurfs metadata/review, persistence, filters, mobile' + (process.env.LIVE_COVER ? ', live cover and enlargement' : ''));
  } finally {await browser.close();}
})().catch(e => {console.error(e);process.exitCode=1;});
