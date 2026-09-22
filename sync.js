'use strict';
(() => {
  const CONFIG = 'gaming-catalog-sync-v1';
  const SESSION = 'gaming-catalog-token';
  const store = window.catalogStore;
  let config = {}, token = '', timer, busy = false, pending = false;
  // Each tab writes a different file: simultaneous devices never replace each other's data.
  const writer = Array.from(crypto.getRandomValues(new Uint8Array(16)), b => b.toString(16).padStart(2, '0')).join('');
  const filename = `gaming-catalog-${writer}.json`;
  let lastWritten = '';
  try { config = JSON.parse(localStorage.getItem(CONFIG) || '{}'); token = sessionStorage.getItem(SESSION) || config.token || ''; }
  catch { store.notice(tr('לא ניתן לקרוא את הגדרות הסנכרון. ניתן להגדיר אותן מחדש.')); }
  const status = message => { document.getElementById('syncSettings').textContent = message; };
  function saveConfig(remember) {
    config.token = remember ? token : '';
    localStorage.setItem(CONFIG, JSON.stringify(config));
    sessionStorage.setItem(SESSION, token);
  }
  async function api(path, method = 'GET', body) {
    const response = await fetch('https://api.github.com/gists' + path, {
      method, headers: {Accept: 'application/vnd.github+json', Authorization: 'Bearer ' + token,
        'X-GitHub-Api-Version': '2026-03-10', ...(body ? {'Content-Type': 'application/json'} : {})},
      ...(body ? {body: JSON.stringify(body)} : {}), cache: 'no-store', signal: AbortSignal.timeout(25000)
    });
    if (!response.ok) throw Error(response.status === 401 ? tr('אסימון הגישה לא תקין או שפג תוקפו') : response.status === 404 ? tr('ה־Gist לא נמצא או שאין אליו גישה') : (window.catalogLanguage === 'en' ? `GitHub returned error ${response.status}` : `GitHub החזיר שגיאה ${response.status}`));
    return response.json();
  }
  function parseGist(gist) {
    if (gist.public !== false) throw Error(tr('יש לבחור Gist סודי'));
    if (gist.truncated) throw Error(tr('רשימת קובצי הסנכרון גדולה מדי. יש לייצא גיבוי וליצור Gist חדש'));
    let merged = {schemaVersion: 1, entries: {}};
    const files = Object.entries(gist.files || {}).filter(([name]) => /^gaming-catalog-[a-f0-9]+\.json$/.test(name));
    if (!files.length) throw Error(tr('ה־Gist אינו מכיל גיבוי של Gaming Catalog'));
    for (const [, file] of files) {
      if (file.truncated || typeof file.content !== 'string') throw Error(tr('קובץ הסנכרון גדול מדי לקריאה. יש לייצא גיבוי וליצור Gist חדש'));
      merged = store.merge(merged, JSON.parse(file.content));
    }
    return merged;
  }
  async function sync() {
    if (!token || !config.id) return;
    if (busy) { pending = true; return; }
    busy = true; status(tr('☁ מסנכרן…'));
    try {
      const gist = await api('/' + config.id);
      const merged = parseGist(gist);
      if (!store.apply(merged)) throw Error(tr('השמירה המקומית נכשלה; ייצאו גיבוי'));
      const content = JSON.stringify(store.get());
      if (content !== lastWritten) {
        if (new Blob([content]).size > 950000) throw Error(tr('הגיבוי גדול מדי לסנכרון. ייצאו אותו לקובץ'));
        await api('/' + config.id, 'PATCH', {files: {[filename]: {content}}});
        lastWritten = content;
      }
      status(tr('☁ מסונכרן'));
    } catch (error) {
      status(tr('☁ הסנכרון נכשל')); store.notice(tr('סנכרון: ') + error.message + tr('. השמירה המקומית ממשיכה לפעול.'));
    } finally { busy = false; if (pending) { pending = false; schedule(); } }
  }
  function schedule() { if (!token || !config.id) return; status(tr('☁ ממתין לסנכרון')); clearTimeout(timer); timer = setTimeout(sync, 1800); }
  function open() {
    const content = document.getElementById('syncContent');
    content.innerHTML = `<p>שמירה מקומית וסנכרון אוטומטי דרך Gist סודי. בכל מכשיר מזינים את אותו מזהה Gist ואסימון GitHub.</p>
      <p>Gist סודי אינו מופיע בחיפוש, אבל כל מי שמחזיק בקישור יכול לקרוא אותו.</p>
      <p><a href="https://github.com/settings/tokens/new?scopes=gist&description=GamingCatalog" target="_blank" rel="noopener noreferrer">יצירת אסימון GitHub עם הרשאת gist בלבד ↗</a></p>
      <label>אסימון גישה<input id="syncToken" type="password" dir="ltr" autocomplete="off" placeholder="GitHub token"></label>
      <label><input id="rememberToken" type="checkbox" style="width:auto"> זכור אסימון במכשיר זה (רק במכשיר אישי)</label>
      <p style="font-size:12px">ללא סימון, האסימון נשמר רק למשך הלשונית. עם סימון, הוא נשמר בדפדפן ואינו מוצפן. הוא אינו נכלל בגיבויים או בקוד המאגר.</p>
      <label>מזהה Gist קיים<input id="gistId" dir="ltr" autocomplete="off" placeholder="להשאיר ריק רק ביצירה הראשונה"></label>
      <div style="display:flex;gap:8px;flex-wrap:wrap"><button type="button" id="connectGist">חיבור וסנכרון</button><button type="button" id="createGist">יצירת Gist חדש</button><button type="button" id="disconnectGist">ניתוק</button></div>
      <p id="syncMessage" role="status"></p>`;
    translateInterface(content);
    const tokenInput = document.getElementById('syncToken'); tokenInput.value = token;
    const idInput = document.getElementById('gistId'); idInput.value = config.id || '';
    const remember = document.getElementById('rememberToken'); remember.checked = Boolean(config.token);
    const message = document.getElementById('syncMessage');
    async function connect(create) {
      if (busy) { message.textContent = tr('הסנכרון הקודם עדיין מתבצע'); return; }
      const nextToken = tokenInput.value.trim(), nextId = idInput.value.trim();
      if (!nextToken) { message.textContent = tr('יש להזין אסימון גישה'); return; }
      if (!create && !/^[a-f0-9]{20,64}$/i.test(nextId)) { message.textContent = tr('יש להזין מזהה Gist תקין'); return; }
      if (create && nextId) { message.textContent = tr('כבר הוזן מזהה. לחיבור אליו בחרו חיבור וסנכרון; ליצירה חדשה יש לפנות את השדה'); return; }
      clearTimeout(timer); busy = true;
      const previousToken = token; token = nextToken;
      const controls = [...content.querySelectorAll('button')]; controls.forEach(b => b.disabled = true);
      try {
        message.textContent = tr('מתחבר…');
        let gist;
        if (create) {
          gist = await api('', 'POST', {description: 'Gaming Catalog personal progress', public: false, files: {[filename]: {content: JSON.stringify(store.get())}}});
          // Expose the created ID before any local write, so storage errors cannot hide it.
          idInput.value = gist.id;
        } else { gist = await api('/' + nextId); parseGist(gist); }
        config.id = gist.id; saveConfig(remember.checked); lastWritten = '';
        message.textContent = tr('מחובר. במכשיר אחר יש להזין את המזהה: ') + config.id;
      } catch (error) { token = previousToken; message.textContent = error.message; }
      finally { busy = false; controls.forEach(b => b.disabled = false); }
      if (token && config.id) await sync();
    }
    document.getElementById('connectGist').onclick = () => connect(false);
    document.getElementById('createGist').onclick = () => connect(true);
    document.getElementById('disconnectGist').onclick = () => {
      if (busy) { message.textContent = tr('יש להמתין לסיום הסנכרון'); return; }
      token = ''; config = {}; clearTimeout(timer);
      try { localStorage.removeItem(CONFIG); sessionStorage.removeItem(SESSION); } catch {}
      tokenInput.value = ''; idInput.value = ''; status(tr('☁ סנכרון')); message.textContent = tr('מנותק. השמירה המקומית וה־Gist נשארו ללא מחיקה.');
    };
    document.getElementById('syncDialog').showModal();
  }
  window.catalogSync = {open, schedule};
  window.addEventListener('online', schedule);
  window.addEventListener('focus', schedule);
  setInterval(() => { if (!document.hidden) sync(); }, 45000);
  if (token && config.id) sync();
  else if (config.id) status(tr('☁ נדרש אסימון'));
})();
