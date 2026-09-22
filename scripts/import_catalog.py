"""Read Archive SQLite metadata locally; export only allowlisted catalog fields."""
import argparse
import hashlib
import json
import pathlib
import re
import sqlite3


def build(source):
    games = []
    paths = sorted(source.glob('ps4-fpkg-collection-english-*_meta.sqlite'))
    if not paths:
        raise ValueError('No collection SQLite files found')
    for path in paths:
        collection = path.stem.removesuffix('_meta')
        letter = collection.rsplit('-', 1)[-1].upper()
        with sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True) as db:
            rows = db.execute('SELECT s3key, headers FROM s3api_per_key_metadata WHERE old_version_of IS NULL OR old_version_of = ? ', ('',))
            for filename, headers in rows:
                if not filename.lower().endswith('.pkg'):
                    continue
                title = re.split(r'\s*-\s*\[', filename.removesuffix('.pkg'), maxsplit=1)[0].strip()
                tags = re.findall(r'\[([^\]]+)\]', filename)
                size = re.search(r'^x-file-size:\s*(\d+)', headers or '', re.M | re.I)
                # Track each package separately: multiple versions can coexist.
                region = tags[0] if tags else ''
                key = hashlib.sha256((collection + '|' + filename).encode()).hexdigest()[:24]
                games.append(dict(id=key, title=title, letter=letter, region=region,
                                  version=tags[-1] if tags else '', filename=filename,
                                  bytes=int(size[1]) if size else None,
                                  archiveUrl='https://archive.org/download/' + collection))
    if len({g['id'] for g in games}) != len(games):
        raise ValueError('Duplicate package identity; review before exporting')
    return dict(schemaVersion=1, sourceFiles=len(paths), games=sorted(games, key=lambda g: g['title'].casefold()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=pathlib.Path)
    parser.add_argument('--output_dir', type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1] / 'data')
    args = parser.parse_args()
    catalog = build(args.source)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(catalog, ensure_ascii=False, separators=(',', ':'))
    (args.output_dir / 'catalog.js').write_text('window.GAMING_CATALOG = ' + payload + ';\n', encoding='utf-8')
    print(f"Imported {len(catalog['games'])} catalog entries from {catalog['sourceFiles']} databases")
