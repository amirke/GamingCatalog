'use strict';
const catalog = window.GAMING_CATALOG;
const games = catalog.games;
const metadata = window.GAME_METADATA?.entries || {};
const gameInfo = id => metadata[id] || {};
const metadataComplete = id => ['year', 'image', 'score', 'review'].every(key => Boolean(gameInfo(id)[key]));
const KEY = 'gaming-catalog-state-v1';
const $ = id => document.getElementById(id);
let state = {schemaVersion: 1, entries: {}};
let letter = 'all', page = 1;
const UI_KEY = 'gaming-catalog-ui-v1';
let ui = {};
try { ui = JSON.parse(localStorage.getItem(UI_KEY) || '{}') || {}; } catch {}
let view = ui.view === 'list' ? 'list' : 'cards';
const expanded = new Set();
const filterIds = ['search', 'filter', 'downloadFilter', 'playFilter', 'notesFilter', 'regionFilter', 'yearFilter', 'ps4YearFilter', 'metadataFilter', 'sort'];
for (const [id, field] of [['yearFilter', 'year'], ['ps4YearFilter', 'ps4Year']]) {
  for (const year of [...new Set(Object.values(metadata).map(m => m[field]).filter(Boolean))].sort((a, b) => b - a)) {
    const option = document.createElement('option'); option.value = String(year); option.textContent = year; $(id).append(option);
  }
}
for (const region of [...new Set(games.map(g => g.region))].sort()) {
  const option = document.createElement('option'); option.value = region; option.textContent = region; $('regionFilter').append(option);
}
for (const id of filterIds) if (typeof ui[id] === 'string') {
  $(id).value = ui[id]; if ($(id).tagName === 'SELECT' && !$(id).value) $(id).selectedIndex = 0;
}
if (ui.letter === 'all' || /^[A-Z]$/.test(ui.letter || '')) letter = ui.letter;
function saveUI() {
  ui = {view, letter}; for (const id of filterIds) ui[id] = $(id).value;
  try { localStorage.setItem(UI_KEY, JSON.stringify(ui)); } catch { notice(tr('לא ניתן לשמור את העדפות התצוגה בדפדפן.')); }
}
const pageSize = 24;
let storageBlocked = false;
function notice(message) { $('notice').textContent = message; $('notice').hidden = !message; }
function validState(value) {
  if (!value || value.schemaVersion !== 1 || !value.entries || Array.isArray(value.entries) || typeof value.entries !== 'object') throw Error(tr('קובץ הגיבוי אינו תקין'));
  const clean = {schemaVersion: 1, entries: {}};
  for (const [id, fields] of Object.entries(value.entries)) {
    if (!/^[a-f0-9]{24}$/.test(id) || !fields || typeof fields !== 'object') throw Error(tr('רשומה לא תקינה'));
    clean.entries[id] = {};
    for (const [key, field] of Object.entries(fields)) {
      if (!['played', 'downloaded', 'notes'].includes(key)) continue;
      if (!field || typeof field.updatedAt !== 'number' || !Number.isFinite(field.updatedAt) || field.updatedAt < 0 ||
          (key === 'notes' ? typeof field.value !== 'string' : typeof field.value !== 'boolean')) throw Error(tr('שדה לא תקין בגיבוי'));
      clean.entries[id][key] = {value: field.value, updatedAt: field.updatedAt};
    }
  }
  return clean;
}
function merge(a, b) {
  const out = validState(a);
  for (const [id, fields] of Object.entries(validState(b).entries)) {
    out.entries[id] ||= {};
    for (const [key, field] of Object.entries(fields)) {
      const old = out.entries[id][key];
      if (!old || field.updatedAt > old.updatedAt || (field.updatedAt === old.updatedAt && JSON.stringify(field.value) > JSON.stringify(old.value))) out.entries[id][key] = field;
    }
  }
  return out;
}
try { const saved = localStorage.getItem(KEY); if (saved) state = validState(JSON.parse(saved)); }
catch { storageBlocked = true; notice(tr('לא ניתן לקרוא את השמירה הקיימת. היא לא תידרס. אפשר לייצא גיבוי של השינויים מההפעלה הנוכחית.')); }
function persist() {
  try {
    if (storageBlocked) throw Error('storage blocked');
    const previous = localStorage.getItem(KEY);
    if (previous) state = merge(state, JSON.parse(previous));
    localStorage.setItem(KEY, JSON.stringify(state));
    $('saveStatus').textContent = tr('✓ נשמר בדפדפן');
    return true;
  } catch { $('saveStatus').textContent = tr('השמירה נכשלה — יש לייצא גיבוי'); notice(tr('אין אפשרות לשמור בדפדפן. השינויים זמינים כרגע בזיכרון בלבד; השתמשו בגיבוי לפני סגירה.')); return false; }
}
function value(id, field) { return state.entries[id]?.[field]?.value ?? (field === 'notes' ? '' : false); }
function update(id, field, newValue) {
  state.entries[id] ||= {};
  state.entries[id][field] = {value: newValue, updatedAt: Math.max(Date.now(), (state.entries[id][field]?.updatedAt || 0) + 1)};
  persist(); stats();
  window.catalogSync?.schedule();
}
function stats() {
  $('total').textContent = games.length.toLocaleString(window.catalogLanguage);
  for (const field of ['downloaded', 'played', 'notes']) $('' + field + 'Count').textContent = games.filter(g => Boolean(value(g.id, field))).length.toLocaleString(window.catalogLanguage);
}
function node(tag, className, text) { const el = document.createElement(tag); if (className) el.className = className; if (text !== undefined) el.textContent = text; return el; }
function sourceLink(text, url) {
  const link = node('a', '', text);
  if (/^https:\/\//.test(url || '')) { link.href = url; link.target = '_blank'; link.rel = 'noopener noreferrer'; }
  return link;
}
function reviewBlock(info) {
  const block = node('section', 'review-block');
  block.append(node('h4', '', tr('ביקורות')));
  if (info.score) {
    const score = node('div', 'critic-score');
    score.append(node('strong', '', info.score.value + '/100'), node('span', '', 'Metacritic · ' + (info.score.platform === 'unspecified' ? tr('פלטפורמה לא צוינה') : info.score.platform)));
    block.append(score);
  } else block.append(node('p', 'metadata-missing', tr('לא נמצא ציון מבקרים במקור.')));
  const summary = info.review?.[window.catalogLanguage];
  block.append(node('p', 'review-summary', summary || tr('לא נמצא תקציר ביקורת במקור.')));
  if (info.source) {
    block.append(node('small', 'matched-title', tr('זוהה אוטומטית כ: ') + info.matchedTitle));
    const sources = node('div', 'review-sources');
    sources.append(sourceLink(tr('מקור: Wikipedia ↗'), info.source), sourceLink(tr('מקור התמונה ↗'), info.imageSource));
    if (info.score?.url) sources.append(sourceLink('Metacritic ↗', info.score.url));
    block.append(sources, node('small', '', tr('סיכום אוטומטי מהמקור; הביקורות עשויות להתייחס גם לגרסאות אחרות.')));
  } else block.append(node('small', '', tr('לא נמצאה התאמה אוטומטית בטוחה לשם המשחק.')));
  return block;
}
function card(game) {
  const info = gameInfo(game.id);
  const el = node('article', 'game'); el.dataset.id = game.id;
  const top = node('div', 'game-top');
  const icon = node('div', 'monogram', game.title[0].toUpperCase()); icon.setAttribute('aria-hidden', 'true');
  if (/^https:\/\/(?:upload|thumb)\.wikimedia\.org\//.test(info.image || '')) {
    const image = node('img'); image.alt = ''; image.loading = 'lazy'; image.decoding = 'async'; image.referrerPolicy = 'no-referrer';
    image.addEventListener('error', () => { icon.replaceChildren(document.createTextNode(game.title[0].toUpperCase())); icon.classList.remove('cover'); });
    image.src = info.image; icon.replaceChildren(image); icon.classList.add('cover');
  }
  const heading = node('div'); const title = node('h3', '', game.title + (info.year ? ` (${info.year})` : '')); title.dir = 'ltr';
  const meta = node('div', 'meta', ['PS4' + (info.ps4Year ? ' ' + info.ps4Year : ''), game.region, 'v' + game.version, game.bytes ? (game.bytes / 1024 ** 3).toFixed(1) + ' GiB' : ''].filter(Boolean).join(' · ')); meta.dir = 'ltr';
  heading.append(title, meta); top.append(icon, heading);
  if (!info.year) heading.append(node('span', 'metadata-missing', tr('שנת יציאה לא נמצאה')));
  if (info.score) heading.append(node('span', 'score-chip', info.score.value + '/100 · ' + (info.score.platform === 'unspecified' ? 'Metacritic' : info.score.platform)));
  const checks = node('div', 'checks');
  for (const [field, label] of [['downloaded', tr('הורדתי')], ['played', tr('שיחקתי')]]) {
    const wrap = node('label'); const input = node('input'); input.type = 'checkbox'; input.checked = value(game.id, field); input.dataset.field = field;
    input.setAttribute('aria-label', label + ' — ' + game.title);
    input.addEventListener('change', () => { update(game.id, field, input.checked); render(); });
    wrap.append(input, document.createTextNode(label)); checks.append(wrap);
  }
  const links = node('div', 'links');
  for (const [text, url] of [[tr('↗ חיפוש באינטרנט'), 'https://www.google.com/search?q=' + encodeURIComponent(game.title + ' PS4')], ['↗ Archive · ' + game.letter, game.archiveUrl]]) {
    const link = node('a', '', text); link.href = url; link.target = '_blank'; link.rel = 'noopener noreferrer'; links.append(link);
  }
  const label = node('label', 'notes-label', tr('הערות, רשמים ועדכונים'));
  const notes = node('textarea'); notes.placeholder = tr('איך היה? מה כדאי לזכור לפעם הבאה?'); notes.value = value(game.id, 'notes'); notes.dir = 'auto'; notes.dataset.field = 'notes';
  notes.setAttribute('aria-label', tr('הערות — ') + game.title);
  notes.addEventListener('input', () => update(game.id, 'notes', notes.value)); label.append(notes);
  const cheats = node('div', 'cheats'); cheats.append(node('span', '', tr('צ׳יטים ומה הם עושים')), node('span', '', tr('בהמשך')));
  if (view === 'list') {
    el.classList.add('game-row');
    const row = node('div', 'row-heading');
    const toggle = node('button', 'row-toggle'); toggle.type = 'button';
    toggle.setAttribute('aria-expanded', expanded.has(game.id));
    toggle.setAttribute('aria-controls', 'details-' + game.id);
    const arrow = node('span', 'row-arrow', expanded.has(game.id) ? '▾' : '▸'); arrow.setAttribute('aria-hidden', 'true');
    toggle.append(arrow, top); row.append(toggle, checks);
    const details = node('div', 'row-details'); details.id = 'details-' + game.id; details.hidden = !expanded.has(game.id);
    details.append(links, reviewBlock(info), label, cheats);
    toggle.addEventListener('click', () => {
      const open = !expanded.has(game.id); if (open) expanded.add(game.id); else expanded.delete(game.id);
      toggle.setAttribute('aria-expanded', open); details.hidden = !open; arrow.textContent = open ? '▾' : '▸';
    });
    el.append(row, details);
  } else el.append(top, checks, links, reviewBlock(info), label, cheats);
  return el;
}
function filtered() {
  const search = $('search').value.trim().toLocaleLowerCase(); const filter = $('filter').value;
  const match = (id, field, control) => $(control).value === 'all' || Boolean(value(id, field)) === ($(control).value === 'yes');
  const yearMatch = (id, field, control) => $(control).value === 'all' || ($(control).value === 'unknown' ? !gameInfo(id)[field] : String(gameInfo(id)[field]) === $(control).value);
  const list = games.filter(g => (letter === 'all' || g.letter === letter) && (!search || (g.title + ' ' + g.filename).toLocaleLowerCase().includes(search)) &&
    (filter === 'all' || filter === 'notDownloaded' && !value(g.id, 'downloaded') || filter === 'notPlayed' && !value(g.id, 'played') || Boolean(value(g.id, filter))) &&
    match(g.id, 'downloaded', 'downloadFilter') && match(g.id, 'played', 'playFilter') && match(g.id, 'notes', 'notesFilter') &&
    ($('regionFilter').value === 'all' || g.region === $('regionFilter').value) && yearMatch(g.id, 'year', 'yearFilter') && yearMatch(g.id, 'ps4Year', 'ps4YearFilter') &&
    ($('metadataFilter').value === 'all' || metadataComplete(g.id) === ($('metadataFilter').value === 'complete')));
  const sort = $('sort').value;
  return list.sort((a, b) => {
    const names = a.title.localeCompare(b.title, 'en') || a.id.localeCompare(b.id);
    if (sort === 'za') return -names;
    if (sort === 'sizeDesc' || sort === 'sizeAsc') {
      if (a.bytes == null || b.bytes == null) return a.bytes == null ? (b.bytes == null ? names : 1) : -1;
      return (sort === 'sizeDesc' ? b.bytes - a.bytes : a.bytes - b.bytes) || names;
    }
    return names;
  });
}
function render() {
  const list = filtered(); const pages = Math.max(1, Math.ceil(list.length / pageSize)); page = Math.min(page, pages);
  $('games').replaceChildren(...list.slice((page - 1) * pageSize, page * pageSize).map(card));
  $('games').classList.toggle('list-view', view === 'list');
  $('cardsView').setAttribute('aria-pressed', view === 'cards'); $('listView').setAttribute('aria-pressed', view === 'list');
  $('collapseControls').hidden = view !== 'list';
  $('empty').hidden = list.length > 0; $('resultCount').textContent = '(' + list.length + ')'; $('pageLabel').textContent = (window.catalogLanguage === 'en' ? `Page ${page} of ${pages}` : `עמוד ${page} מתוך ${pages}`);
  $('previous').disabled = page === 1; $('next').disabled = page === pages;
  for (const btn of $('letters').children) { const active = btn.dataset.letter === letter; btn.classList.toggle('active', active); btn.setAttribute('aria-pressed', active); }
}
function refreshSavedFields() {
  if (document.activeElement?.tagName !== 'TEXTAREA') { render(); return; }
  for (const card of document.querySelectorAll('.game')) {
    for (const input of card.querySelectorAll('[data-field]')) {
      if (input === document.activeElement) continue;
      if (input.type === 'checkbox') input.checked = value(card.dataset.id, input.dataset.field);
      else input.value = value(card.dataset.id, input.dataset.field);
    }
  }
}
for (const l of ['all', ...'ABCDEFGHIJKLMNOPQRSTUVWXYZ']) {
  const btn = node('button', '', l === 'all' ? tr('הכול') : l); btn.dataset.letter = l;
  btn.addEventListener('click', () => { letter = l; page = 1; saveUI(); render(); }); $('letters').append(btn);
}
for (const id of filterIds) $(id).addEventListener(id === 'search' ? 'input' : 'change', () => { page = 1; saveUI(); render(); });
for (const [id, mode] of [['cardsView', 'cards'], ['listView', 'list']]) $(id).addEventListener('click', () => { view = mode; saveUI(); render(); });
for (const [id, open] of [['expandAll', true], ['collapseAll', false]]) $(id).addEventListener('click', () => {
  for (const game of filtered().slice((page - 1) * pageSize, page * pageSize)) { if (open) expanded.add(game.id); else expanded.delete(game.id); } render();
});
$('resetFilters').addEventListener('click', () => { for (const id of filterIds) { if (id === 'search') $(id).value = ''; else $(id).selectedIndex = 0; } letter = 'all'; page = 1; saveUI(); render(); });
for (const [id, step] of [['previous', -1], ['next', 1]]) $(id).addEventListener('click', () => { page += step; render(); $('letters').scrollIntoView({behavior: 'smooth'}); });
$('export').addEventListener('click', () => {
  const blob = new Blob([JSON.stringify({...state, exportedAt: new Date().toISOString()}, null, 2)], {type: 'application/json'});
  const url = URL.createObjectURL(blob); const a = node('a'); a.href = url; a.download = `gaming-catalog-${new Date().toISOString().slice(0, 10)}.backup.json`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
});
$('import').addEventListener('click', () => $('importFile').click());
$('importFile').addEventListener('change', async event => {
  const file = event.target.files[0]; if (!file) return;
  try {
    if (file.size > 20 * 1024 * 1024) throw Error(tr('הקובץ גדול מדי'));
    const imported = validState(JSON.parse(await file.text())); state = merge(state, imported);
    const saved = persist(); stats(); render(); if (saved) notice(tr('הגיבוי מוזג בהצלחה. בכל שדה נשמר העדכון החדש יותר.')); window.catalogSync?.schedule();
  } catch (error) { notice(tr('הייבוא נכשל: ') + error.message); }
  event.target.value = '';
});
window.addEventListener('storage', event => {
  if (event.key !== KEY || !event.newValue) return;
  try { state = merge(state, JSON.parse(event.newValue)); stats(); refreshSavedFields(); }
  catch { notice(tr('עדכון מלשונית אחרת לא נקרא. הנתונים הנוכחיים נשמרו בזיכרון.')); }
});
$('syncSettings').addEventListener('click', () => {
  if (window.catalogSync) window.catalogSync.open();
  else { $('syncContent').replaceChildren(node('p', '', tr('הגדרת הסנכרון המקוון עדיין לא הושלמה. השמירה המקומית והגיבוי זמינים.'))); $('syncDialog').showModal(); }
});
window.catalogStore = {get: () => state, merge, validState, apply: remote => {state = merge(state, remote); const saved = persist(); stats(); refreshSavedFields(); return saved;}, notice};
$('sourceCount').textContent = catalog.sourceFiles;
$('metadataCoverage').textContent = tr('מידע אוטומטי מלא: ') + games.filter(g => metadataComplete(g.id)).length + '/' + games.length + ' · ' + tr('אפשר לסנן רשומות עם מידע חסר.');
stats(); render();
