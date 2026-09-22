"""Audit EVERY catalog row; write a readable coverage report and fail on invalid data."""
import collections
import json
import pathlib
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_js(path):
    return json.loads(path.read_text(encoding='utf-8').split('=', 1)[1].strip().rstrip(';'))


def audit():
    catalog = load_js(ROOT / 'data/catalog.js')['games']
    metadata = load_js(ROOT / 'data/metadata.js')['entries']
    errors, rows = [], []
    counts = collections.Counter()
    for game in catalog:
        data = metadata.get(game['id'], {})
        missing = [key for key in ['year', 'image', 'score', 'review'] if not (data.get(key) or (key == 'review' and (data.get('receptionText') or data.get('criticExcerpts'))))]
        counts['entries'] += 1
        counts['writtenReview'] += bool(data.get('receptionText') or data.get('criticExcerpts'))
        counts['complete'] += not missing
        for key in ['year', 'ps4Year', 'image', 'score', 'review']:
            counts[key] += bool(data.get(key) or (key == 'review' and (data.get('receptionText') or data.get('criticExcerpts'))))
        for key in ['year', 'ps4Year']:
            if data.get(key) is not None and (type(data[key]) is not int or not 1970 <= data[key] <= 2026):
                errors.append([game['title'], 'Invalid ' + key, data[key]])
        if data.get('ps4Year') and data['ps4Year'] < 2013:
            errors.append([game['title'], 'PS4 date precedes console launch', data['ps4Year']])
        if data.get('year') and data.get('ps4Year') and data['ps4Year'] < data['year']:
            errors.append([game['title'], 'PS4 year precedes original year', data['year'], data['ps4Year']])
        if data:
            if not any(data.get('source', '').startswith(prefix) for prefix in ['https://en.wikipedia.org/wiki/', 'https://www.metacritic.com/game/']):
                errors.append([game['title'], 'Missing source'])
            if data.get('image') and urllib.parse.urlparse(data['image']).hostname not in ['upload.wikimedia.org', 'thumb.wikimedia.org', 'www.metacritic.com', 'shared.fastly.steamstatic.com']:
                errors.append([game['title'], 'Unexpected image host'])
            if data.get('score') and not (0 <= data['score']['value'] <= 100 and data['score'].get('platform')):
                errors.append([game['title'], 'Invalid score'])
            if data.get('review') and not all(data['review'].get(lang) for lang in ['he', 'en']):
                errors.append([game['title'], 'Missing review translation'])
        rows.append({'title': game['title'], 'id': game['id'], 'status': 'complete' if not missing else 'incomplete', 'missing': missing})
    if set(metadata) - {g['id'] for g in catalog}:
        errors.append(['Orphan metadata IDs'])
    hebrew_path = ROOT / 'data/hebrew-reviews.js'
    if hebrew_path.exists():
        hebrew = load_js(hebrew_path)['entries']
        counts['hebrewReview'] = len(hebrew)
        for game_id, reviews in hebrew.items():
            if game_id not in {g['id'] for g in catalog}: errors.append([game_id, 'Orphan Hebrew review'])
            for review in reviews:
                if urllib.parse.urlparse(review.get('url', '')).hostname not in ['gamepro.co.il', 'vgames.co.il', 'www.vgames.co.il', 'il.ign.com'] or not review.get('text') or review.get('language') != 'he':
                    errors.append([game_id, 'Invalid Hebrew review source or text'])
    translations_path = ROOT / 'data/review-translations.js'
    if translations_path.exists():
        translations = load_js(translations_path)['entries']
        counts['hebrewWikiTranslation'] = len(translations)
        for game_id, translated in translations.items():
            original = metadata.get(game_id, {}).get('receptionText', {}).get('text')
            if translated.get('sourceText') != original or not translated.get('he') or translated.get('provider') != 'Google Translate':
                errors.append([game_id, 'Stale or invalid review translation'])
    report = {'coverage': dict(counts), 'errors': errors, 'rows': rows}
    (ROOT / 'data/metadata-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    labels = {'year': 'Release year', 'image': 'Cover image', 'score': 'Critic score', 'review': 'Review summary or attributed excerpt'}
    lines = ['# Catalog metadata audit', '',
             f"Checked every catalog row: **{len(rows)}**. Complete: **{counts['complete']}**. Data errors: **{len(errors)}**.", '',
             '| Field | Present | Missing |', '| --- | ---: | ---: |']
    for key, label in labels.items():
        lines.append(f"| {label} | {counts[key]} | {len(rows) - counts[key]} |")
    lines += ['', 'PS4 year is optional. Missing information is explicitly shown in the portal; it is not fabricated.', '',
              'This is a structural and coverage audit of automatic source extraction, not a manual review of every game or a guarantee of remote image availability.', '',
              '## Incomplete entries', '', '| Game | Missing information |', '| --- | --- |']
    for row in rows:
        if row['missing']:
            title = row['title'].replace('|', '\\|')
            lines.append('| ' + title + ' | ' + ', '.join(labels[k] for k in row['missing']) + ' |')
    if errors:
        lines += ['', '## Data errors', '', '```json', json.dumps(errors, ensure_ascii=False, indent=2), '```']
    (ROOT / 'data/metadata-audit.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    coverage = {'catalogEntries': len(catalog), 'matched': len(metadata), **dict(counts)}
    (ROOT / 'data/metadata-report.json').write_text(json.dumps({'coverage': coverage, 'unresolved': [r for r in rows if not metadata.get(r['id'])], 'incomplete': [r for r in rows if r['missing']]}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'coverage': dict(counts), 'errors': errors}, ensure_ascii=True))
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(audit())
