"""Enrich the static catalog from Wikipedia. No API key; cached, rate-limited, resumable.

Install requirements-metadata.txt, then run this script. --offline rebuilds from cache.
Missing/ambiguous data stays null. Scores always retain their platform and source.
"""
import argparse
import datetime as dt
import hashlib
import html
import json
import pathlib
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

import mwparserfromhell as mw

ROOT = pathlib.Path(__file__).resolve().parents[1]
YEAR = re.compile(r'(?<!\d)(?:19[7-9]\d|20[0-2]\d)(?!\d)')
UA = 'GamingCatalog/1.0 (https://github.com/amirke/GamingCatalog; personal game metadata)'


def normalized(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]', '', text.replace('&', 'and'))


def strip_refs(text):
    return re.sub(r'<ref\b[^>]*(?:/>|>.*?</ref\s*>)|<!--.*?-->', '', text, flags=re.I | re.S)


def plain(text):
    """Flatten date/list templates, rather than dropping their release dates."""
    code = mw.parse(re.sub(r'<br\s*/?>', ' ', strip_refs(str(text)), flags=re.I), skip_style_tags=True)
    for template in reversed(code.filter_templates()):
        name = str(template.name).strip().lower()
        if name in ['efn', 'sfn', 'refn', 'cite web', 'cite news']:
            replacement = ''
        elif name in ['!', "'", 'nbsp']:
            replacement = {'!': '|', "'": "'", 'nbsp': ' '}[name]
        else:
            replacement = ' '.join(str(p.value) for p in template.params
                                   if str(p.name).strip().isdigit() or str(p.name).strip() == 'title')
        try:
            code.replace(template, ' ' + replacement + ' ')
        except ValueError:
            pass
    return html.unescape(re.sub(r'\s+', ' ', code.strip_code())).strip()


def infobox(code):
    return next((t for t in code.filter_templates() if strip_refs(str(t.name)).strip().lower() == 'infobox video game'), None)


def reception(code):
    sections = code.get_sections(include_lead=False, matches=r'(?i).*?(reception|critical response|reviews).*')
    if not sections:
        return ''
    section = mw.parse(str(sections[0]))
    for template in list(section.filter_templates(recursive=False)):
        section.remove(template)
    return plain(str(section))[:12000]


def extract_score(code, platforms):
    scores = []
    for template in code.filter_templates():
        if strip_refs(str(template.name)).strip().lower().replace('_', ' ') not in ['video game reviews', 'video game review']:
            continue
        for param in template.params:
            name = str(param.name).strip().upper()
            if not (name == 'MC' or name.startswith('MC_')):
                continue
            raw = str(param.value)
            for part in re.split(r'<br\s*/?>', raw, flags=re.I):
                text = plain(part)
                match = re.search(r'\b(\d{1,3})\s*/\s*100\b', text)
                if not match or not 0 <= int(match[1]) <= 100:
                    continue
                platform = name[3:] if name.startswith('MC_') else None
                if not platform:
                    label = re.search(r'\b(PS[1-5]|PlayStation [1-5]|PC|X360|XONE|XSXS|NS|WIIU|WII|XBOX|PSP|VITA)\b', text, re.I)
                    platform = label[1].upper() if label else 'unspecified'
                if platform == 'unspecified' and re.fullmatch(r'(PlayStation 4|PS4)', platforms, re.I):
                    platform = 'PS4'
                links = re.findall(r'https?://(?:www\.)?metacritic\.com/[^\s|<>}\"]+', part)
                scores.append({'value': int(match[1]), 'platform': platform,
                               'provider': 'Metacritic', 'url': links[0].replace('http://', 'https://', 1) if links else None})
    return next((s for s in scores if s['platform'] in ['PS4', 'PLAYSTATION 4']), scores[0] if scores else None)


# A short reception summary grounded in explicitly evaluative clauses, not an invented review.
ASPECTS = [
    (r'\b(story|narrative|writing|plot)\b', 'story and writing', 'הסיפור והכתיבה'),
    (r'\b(combat|battle system)\b', 'combat', 'מערכת הקרב'),
    (r'\b(visuals?|graphics|art style|art direction)\b', 'visual presentation', 'העיצוב החזותי'),
    (r'\b(music|soundtrack)\b', 'music', 'המוזיקה'),
    (r'\blevel design\b', 'level design', 'עיצוב השלבים'),
    (r'\bcontrols?\b', 'controls', 'השליטה'),
    (r'\bpuzzles?\b', 'puzzles', 'החידות'),
    (r'\bexploration\b', 'exploration', 'החקירה'),
    (r'\batmosphere\b', 'atmosphere', 'האווירה'),
    (r'\b(replayability|replay value)\b', 'replay value', 'הערך למשחק חוזר'),
    (r'\b(performance|frame rate|framerate|technical issues|bugs|glitches)\b', 'technical performance', 'הביצועים הטכניים'),
    (r'\b(camera)\b', 'camera', 'המצלמה'),
    (r'\b(difficulty|challenging)\b', 'difficulty', 'רמת הקושי'),
    (r'\b(length|short duration|short game)\b', 'length', 'אורך המשחק'),
    (r'\b(pacing)\b', 'pacing', 'הקצב'),
    (r'\b(multiplayer|co-op|cooperative)\b', 'multiplayer', 'המשחק מרובה המשתתפים'),
]


def summarize(text, score):
    positive, negative = [], []
    for sentence in re.split(r'(?<=[.!?])\s+', text):
        for clause in re.split(r'\b(?:but|although|however|whereas|while|despite)\b', sentence, flags=re.I):
            if re.search(r'\b(not|never|no praise|didn.t|wasn.t)\b', clause, re.I):
                continue
            for verbs, bucket in [(r'\b(?:praised|lauded|commended|complimented)\b', positive),
                                  (r'\b(?:criticized|criticised|criticism of|complained about)\b', negative)]:
                match = re.search(verbs, clause, re.I)
                if not match:
                    continue
                # Only the immediate object of an explicit evaluation; avoid distant claims.
                fragment = clause[match.end():match.end() + 160]
                for pattern, english, hebrew in ASPECTS:
                    if re.search(pattern, fragment, re.I) and (english, hebrew) not in bucket:
                        bucket.append((english, hebrew))
    en, he = [], []
    if score:
        n = score['value']
        description = ('very positive', 'חיובית מאוד') if n >= 85 else ('positive', 'חיובית') if n >= 70 else ('mixed', 'מעורבת') if n >= 50 else ('negative', 'שלילית')
        en.append(f"The {score['value']}/100 critic score indicates {description[0]} reception.")
        he.append(f"ציון המבקרים {score['value']}/100 מצביע על קבלת פנים {description[1]}.")
    if positive:
        en.append('The article reports praise for ' + ', '.join(x[0] for x in positive[:3]) + '.')
        he.append('הערך מציין שבחים על ' + ', '.join(x[1] for x in positive[:3]) + '.')
    if negative:
        en.append('Reported criticisms concern ' + ', '.join(x[0] for x in negative[:3]) + '.')
        he.append('נקודות ביקורת במקור: ' + ', '.join(x[1] for x in negative[:3]) + '.')
    return {'en': ' '.join(en), 'he': ' '.join(he)} if en else None


def extract(page, row=None):
    text = page.get('revisions', [{}])[0].get('content', '')
    code = mw.parse(text, skip_style_tags=True)
    box = infobox(code)
    if not box or 'disambiguation' in page.get('pageprops', {}):
        return None
    releases = plain(box.get('released').value) if box.has('released') else plain(box.get('release').value) if box.has('release') else ''
    platforms = plain(box.get('platforms').value) if box.has('platforms') else ''
    years = [int(y) for y in YEAR.findall(releases)]
    original = min(years) if years else None
    ps4 = None
    if row:
        ps4years = [int(y) for y in YEAR.findall(' '.join(row['cells'][4:7]))]
        if ps4years:
            ps4 = min(ps4years)
    if ps4 is None:
        # Only accept a date immediately after an explicit PS4 platform heading.
        match = re.search(r'(?:PlayStation 4|PS4)(.{0,180})', releases, re.I)
        if match:
            y = YEAR.search(match[1])
            if y and not re.search(r'(?:Windows|Switch|Xbox|PlayStation [^4]|PS[1235])', match[1][:y.start()], re.I):
                ps4 = int(y[0])
        elif re.fullmatch(r'(PlayStation 4|PS4)', platforms, re.I):
            ps4 = original
    # Conflicting optional platform dates (e.g. early access vs full release) are not guessed.
    if ps4 and original and ps4 < original:
        ps4 = None
    score = extract_score(code, platforms)
    url = 'https://en.wikipedia.org/wiki/' + urllib.parse.quote(page['title'].replace(' ', '_'))
    picture = page.get('thumbnail', {}).get('source')
    if picture:
        picture = picture.split('?', 1)[0]
    imagefile = page.get('pageimage') or page.get('pageprops', {}).get('page_image')
    return {'matchedTitle': page['title'], 'year': original, 'ps4Year': ps4,
            'image': picture, 'imageSource': 'https://en.wikipedia.org/wiki/File:' + urllib.parse.quote(imagefile) if imagefile else url,
            'score': score, 'review': summarize(reception(code), score),
            'source': url, 'revision': page.get('revisions', [{}])[0].get('revid'),
            'ps4Source': row['source'] if row and ps4 else url if ps4 else None,
            'matchMethod': 'automatic title / redirect', 'checkedAt': dt.date.today().isoformat()}


class Client:
    def __init__(self, cache, offline, delay):
        self.cache, self.offline, self.delay = cache, offline, delay
        self.last = 0

    def query(self, params):
        params = {'action': 'query', 'format': 'json', 'formatversion': 2, **params}
        key = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()
        path = self.cache / ('request-' + key + '.json')
        if path.exists():
            return json.loads(path.read_text(encoding='utf-8'))
        if self.offline:
            return {}
        time.sleep(max(0, self.delay - (time.monotonic() - self.last)))
        url = 'https://en.wikipedia.org/w/api.php?' + urllib.parse.urlencode(params)
        self.last = time.monotonic()
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60) as response:
            data = json.load(response)
        if 'error' in data:
            raise RuntimeError(str(data['error']))
        path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        return data


def absorb(data, pages, redirects):
    query = data.get('query', {})
    for kind in ['normalized', 'redirects']:
        for item in query.get(kind, []):
            redirects[item['from']] = item['to']
    for page in query.get('pages', []):
        pages[page['title']] = page


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir', type=pathlib.Path, default=ROOT / '.metadata-cache')
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--delay', type=float, default=5)
    parser.add_argument('--search-missing', action='store_true', help='Search once per unresolved title; accept only an exact normalized result')
    args = parser.parse_args()
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    raw = (ROOT / 'data/catalog.js').read_text(encoding='utf-8').split('=', 1)[1].strip().rstrip(';')
    catalog = json.loads(raw)
    existing_path = ROOT / 'data/metadata.js'
    existing = json.loads(existing_path.read_text(encoding='utf-8').split('=', 1)[1].strip().rstrip(';')).get('entries', {}) if existing_path.exists() else {}
    aliases = json.loads((ROOT / 'scripts/metadata-titles.json').read_text(encoding='utf-8'))
    rows_path = args.cache_dir / 'matches.json'
    rows = json.loads(rows_path.read_text(encoding='utf-8')) if rows_path.exists() else {}
    pages, redirects = {}, {}
    for path in list(args.cache_dir.glob('batch-*.json')) + list(args.cache_dir.glob('request-*.json')):
        absorb(json.loads(path.read_text(encoding='utf-8')), pages, redirects)
    def resolve(title):
        seen = set()
        while title in redirects and title not in seen:
            seen.add(title)
            title = redirects[title]
        return pages.get(title)
    client = Client(args.cache_dir, args.offline, args.delay)
    targets = list(dict.fromkeys(aliases.get(g['title'], g['title']) for g in catalog['games']))
    missing = [t for t in targets if resolve(t) is None]
    for start in range(0, len(missing), 25):
        try:
            data = client.query({'titles': '|'.join(missing[start:start+25]), 'prop': 'pageimages|revisions|pageprops',
                                 'rvprop': 'ids|timestamp|content', 'piprop': 'thumbnail|name', 'pithumbsize': 320, 'pilicense': 'any', 'redirects': 1})
            absorb(data, pages, redirects)
        except (urllib.error.URLError, RuntimeError) as error:
            print('Source unavailable; keeping cached results:', error, flush=True)
            break
    enriched, unresolved, title_results = {}, [], {}
    for game in catalog['games']:
        title = game['title']
        if title not in title_results:
            page = resolve(aliases.get(title, title))
            result = extract(page, rows.get(title)) if page and not page.get('missing') else None
            if not result and args.search_missing and not args.offline:
                try:
                    print('Searching:', title.encode('ascii', 'backslashreplace').decode(), flush=True)
                    data = client.query({'generator': 'search', 'gsrsearch': title + ' video game', 'gsrlimit': 5,
                                         'prop': 'pageimages|revisions|pageprops', 'rvprop': 'ids|timestamp|content',
                                         'piprop': 'thumbnail|name', 'pithumbsize': 320, 'pilicense': 'any'})
                    candidates = data.get('query', {}).get('pages', [])
                    exact = [c for c in candidates if normalized(re.sub(r'\s*\([^)]*\)$', '', c['title'])) == normalized(title)
                             and infobox(mw.parse(c.get('revisions', [{}])[0].get('content', ''), skip_style_tags=True))]
                    if len(exact) == 1:
                        result = extract(exact[0], rows.get(title))
                        aliases[title] = exact[0]['title']
                except (urllib.error.URLError, RuntimeError) as error:
                    print('Search stopped:', error, flush=True)
                    args.offline = client.offline = True
            title_results[title] = result
        result = title_results[title] or existing.get(game['id'])
        previous = existing.get(game['id'], {})
        if (result and not result.get('ps4Year') and previous.get('ps4Year')
                and result.get('matchedTitle') == previous.get('matchedTitle')
                and (not result.get('year') or previous['ps4Year'] >= result['year'])):
            result = {**result, 'ps4Year': previous['ps4Year'], 'ps4Source': previous.get('ps4Source')}
        if result:
            enriched[game['id']] = result
        else:
            unresolved.append({'id': game['id'], 'title': title, 'reason': 'No unambiguous video-game article matched automatically'})
    supplements = ROOT / 'data/metadata-supplements.json'
    if supplements.exists():
        for game_id, extra in json.loads(supplements.read_text(encoding='utf-8')).items():
            enriched.setdefault(game_id, {}).update(extra)
    for game_id in json.loads((ROOT / 'scripts/metadata-exclusions.json').read_text(encoding='utf-8')):
        enriched.pop(game_id, None)
    (ROOT / 'scripts/metadata-titles.json').write_text(json.dumps(aliases, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    payload = {'schemaVersion': 1, 'generatedAt': dt.datetime.now(dt.timezone.utc).isoformat(), 'entries': enriched}
    (ROOT / 'data/metadata.js').write_text('window.GAME_METADATA = ' + json.dumps(payload, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
    coverage = {'catalogEntries': len(catalog['games']), 'matched': len(enriched),
                **{key: sum(bool(v.get(key)) for v in enriched.values()) for key in ['year', 'ps4Year', 'image', 'score', 'review']}}
    coverage['complete'] = sum(all(v.get(k) for k in ['year', 'image', 'score', 'review']) for v in enriched.values())
    report = {'coverage': coverage, 'unresolved': unresolved,
              'incomplete': [{'id': g['id'], 'title': g['title'], 'missing': [k for k in ['year', 'image', 'score', 'review'] if not enriched.get(g['id'], {}).get(k)]} for g in catalog['games'] if any(not enriched.get(g['id'], {}).get(k) for k in ['year', 'image', 'score', 'review'])]}
    (ROOT / 'data/metadata-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(coverage), flush=True)


if __name__ == '__main__':
    main()
