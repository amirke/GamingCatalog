'use strict';
const catalog = window.GAMING_CATALOG;
const games = catalog.games;
const KEY = 'gaming-catalog-state-v1';
const $ = id => document.getElementById(id);
let state = {schemaVersion: 1, entries: {}};
let letter = 'all', page = 1;
const pageSize = 24;
let storageBlocked = false;
function notice(message) { $('notice').textContent = message; $('notice').hidden = !message; }
function validState(value) {
  if (!value || value.schemaVersion !== 1 || !value.entries || Array.isArray(value.entries) || typeof value.entries !== 'object') throw Error('קובץ הגיבוי אינו תקין');
  const clean = {schemaVersion: 1, entries: {}};
  for (const [id, fields] of Object.entries(value.entries)) {
    if (!/^[a-f0-9]{24}$/.test(id) || !fields || typeof fields !== 'object') throw Error('רשומה לא תקינה');
    clean.entries[id] = {};
    for (const [key, field] of Object.entries(fields)) {
      if (!['played', 'downloaded', 'notes'].includes(key)) continue;
      if (!field || typeof field.updatedAt !== 'number' || !Number.isFinite(field.updatedAt) || field.updatedAt < 0 ||
          (key === 'notes' ? typeof field.value !== 'string' : typeof field.value !== 'boolean')) throw Error('שדה לא תקין בגיבוי');
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
catch { storageBlocked = true; notice('לא ניתן לקרוא את השמירה הקיימת. היא לא תידרס. אפשר לייצא גיבוי של השינויים מההפעלה הנוכחית.'); }
function persist() {
  try {
    if (storageBlocked) throw Error('storage blocked');
    const previous = localStorage.getItem(KEY);
    if (previous) state = merge(state, JSON.parse(previous));
    localStorage.setItem(KEY, JSON.stringify(state));
    $('saveStatus').textContent = '✓ נשמר בדפדפן';
    return true;
  } catch { $('saveStatus').textContent = 'השמירה נכשלה — יש לייצא גיבוי'; notice('אין אפשרות לשמור בדפדפן. השינויים זמינים כרגע בזיכרון בלבד; השתמשו בגיבוי לפני סגירה.'); return false; }
}
function value(id, field) { return state.entries[id]?.[field]?.value ?? (field === 'notes' ? '' : false); }
function update(id, field, newValue) {
  state.entries[id] ||= {};
  state.entries[id][field] = {value: newValue, updatedAt: Math.max(Date.now(), (state.entries[id][field]?.updatedAt || 0) + 1)};
  persist(); stats();
  window.catalogSync?.schedule();
}
function stats() {
  $('total').textContent = games.length.toLocaleString('he');
  for (const field of ['downloaded', 'played', 'notes']) $('' + field + 'Count').textContent = games.filter(g => Boolean(value(g.id, field))).length.toLocaleString('he');
}
function node(tag, className, text) { const el = document.createElement(tag); if (className) el.className = className; if (text !== undefined) el.textContent = text; return el; }
function card(game) {
  const el = node('article', 'game'); el.dataset.id = game.id;
  const top = node('div', 'game-top');
  const icon = node('div', 'monogram', game.title[0].toUpperCase()); icon.setAttribute('aria-hidden', 'true');
  const heading = node('div'); const title = node('h3', '', game.title); title.dir = 'ltr';
  const meta = node('div', 'meta', ['PS4', game.region, 'v' + game.version, game.bytes ? (game.bytes / 1024 ** 3).toFixed(1) + ' GiB' : ''].filter(Boolean).join(' · ')); meta.dir = 'ltr';
  heading.append(title, meta); top.append(icon, heading);
  const checks = node('div', 'checks');
  for (const [field, label] of [['downloaded', 'הורדתי'], ['played', 'שיחקתי']]) {
    const wrap = node('label'); const input = node('input'); input.type = 'checkbox'; input.checked = value(game.id, field); input.dataset.field = field;
    input.setAttribute('aria-label', label + ' — ' + game.title);
    input.addEventListener('change', () => { update(game.id, field, input.checked); if ($('filter').value !== 'all') render(); });
    wrap.append(input, document.createTextNode(label)); checks.append(wrap);
  }
  const links = node('div', 'links');
  for (const [text, url] of [['↗ חיפוש באינטרנט', 'https://www.google.com/search?q=' + encodeURIComponent(game.title + ' PS4')], ['↗ Archive · ' + game.letter, game.archiveUrl]]) {
    const link = node('a', '', text); link.href = url; link.target = '_blank'; link.rel = 'noopener noreferrer'; links.append(link);
  }
  const label = node('label', 'notes-label', 'הערות, רשמים ועדכונים');
  const notes = node('textarea'); notes.placeholder = 'איך היה? מה כדאי לזכור לפעם הבאה?'; notes.value = value(game.id, 'notes'); notes.dir = 'auto'; notes.dataset.field = 'notes';
  notes.setAttribute('aria-label', 'הערות — ' + game.title);
  notes.addEventListener('input', () => update(game.id, 'notes', notes.value)); label.append(notes);
  const cheats = node('div', 'cheats'); cheats.append(node('span', '', 'צ׳יטים ומה הם עושים'), node('span', '', 'בהמשך'));
  el.append(top, checks, links, label, cheats); return el;
}
function filtered() {
  const search = $('search').value.trim().toLocaleLowerCase(); const filter = $('filter').value;
  return games.filter(g => (letter === 'all' || g.letter === letter) && (!search || (g.title + ' ' + g.filename).toLocaleLowerCase().includes(search)) &&
    (filter === 'all' || filter === 'notDownloaded' && !value(g.id, 'downloaded') || filter === 'notPlayed' && !value(g.id, 'played') || Boolean(value(g.id, filter))));
}
function render() {
  const list = filtered(); const pages = Math.max(1, Math.ceil(list.length / pageSize)); page = Math.min(page, pages);
  $('games').replaceChildren(...list.slice((page - 1) * pageSize, page * pageSize).map(card));
  $('empty').hidden = list.length > 0; $('resultCount').textContent = '(' + list.length + ')'; $('pageLabel').textContent = `עמוד ${page} מתוך ${pages}`;
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
  const btn = node('button', '', l === 'all' ? 'הכול' : l); btn.dataset.letter = l;
  btn.addEventListener('click', () => { letter = l; page = 1; render(); }); $('letters').append(btn);
}
$('search').addEventListener('input', () => { page = 1; render(); });
$('filter').addEventListener('change', () => { page = 1; render(); });
for (const [id, step] of [['previous', -1], ['next', 1]]) $(id).addEventListener('click', () => { page += step; render(); $('letters').scrollIntoView({behavior: 'smooth'}); });
$('export').addEventListener('click', () => {
  const blob = new Blob([JSON.stringify({...state, exportedAt: new Date().toISOString()}, null, 2)], {type: 'application/json'});
  const url = URL.createObjectURL(blob); const a = node('a'); a.href = url; a.download = `gaming-catalog-${new Date().toISOString().slice(0, 10)}.backup.json`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
});
$('import').addEventListener('click', () => $('importFile').click());
$('importFile').addEventListener('change', async event => {
  const file = event.target.files[0]; if (!file) return;
  try {
    if (file.size > 20 * 1024 * 1024) throw Error('הקובץ גדול מדי');
    const imported = validState(JSON.parse(await file.text())); state = merge(state, imported);
    const saved = persist(); stats(); render(); if (saved) notice('הגיבוי מוזג בהצלחה. בכל שדה נשמר העדכון החדש יותר.'); window.catalogSync?.schedule();
  } catch (error) { notice('הייבוא נכשל: ' + error.message); }
  event.target.value = '';
});
window.addEventListener('storage', event => {
  if (event.key !== KEY || !event.newValue) return;
  try { state = merge(state, JSON.parse(event.newValue)); stats(); refreshSavedFields(); }
  catch { notice('עדכון מלשונית אחרת לא נקרא. הנתונים הנוכחיים נשמרו בזיכרון.'); }
});
$('syncSettings').addEventListener('click', () => {
  if (window.catalogSync) window.catalogSync.open();
  else { $('syncContent').replaceChildren(node('p', '', 'הגדרת הסנכרון המקוון עדיין לא הושלמה. השמירה המקומית והגיבוי זמינים.')); $('syncDialog').showModal(); }
});
window.catalogStore = {get: () => state, merge, validState, apply: remote => {state = merge(state, remote); const saved = persist(); stats(); refreshSavedFields(); return saved;}, notice};
$('sourceCount').textContent = catalog.sourceFiles;
stats(); render();
