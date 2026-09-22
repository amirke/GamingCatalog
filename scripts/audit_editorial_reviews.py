"""Audit every catalog row separately for editorial reviews, Hebrew text and image loading.
Wikipedia reception and score-derived sentences never count as editorial reviews here.
"""
import collections,json,urllib.parse
from enrich_editorial_reviews import readjs,ROOT

def main():
 games=readjs('catalog.js')['games'];meta=readjs('metadata.js')['entries'];editorial=readjs('editorial-reviews.js')['entries'];local=readjs('hebrew-reviews.js')['entries'];translations=readjs('editorial-translations.js')['entries'];checks=json.loads((ROOT/'data/editorial-review-report.json').read_text(encoding='utf-8'))['checks']
 ipath=ROOT/'data/image-audit.json';images={r['id']:r for r in json.loads(ipath.read_text(encoding='utf-8'))['rows']} if ipath.exists() else {}
 rows=[];errors=[];publishers=collections.Counter();counts=collections.Counter();valid_ids={g['id'] for g in games}
 for id in (set(editorial)|set(local))-valid_ids:errors.append([id,'Orphan review'])
 for game in games:
  id=game['id'];seen=set();reviews=[]
  for r in meta.get(id,{}).get('criticExcerpts',[])+editorial.get(id,[])+local.get(id,[]):
   if r['url'] in seen:continue
   seen.add(r['url']);reviews.append(r)
   if urllib.parse.urlparse(r['url']).scheme not in ['http','https'] or not r.get('publisher'):errors.append([id,'Invalid source'])
   if r.get('kind')=='summary' and r.get('summary'):
    if not all(r['summary'].get(lang) for lang in ['he','en']):errors.append([id,'Summary missing language'])
   elif not r.get('text'):errors.append([id,'Review missing text'])
   elif r.get('language')=='en' and len(r['text'].split())>24:errors.append([id,'Publisher excerpt too long'])
  names=sorted({r['publisher'] for r in reviews});publishers.update(names)
  translated=all(r.get('language')=='he' or r.get('summary',{}).get('he') or translations.get(r.get('text'),{}).get('sourceText')==r.get('text') and bool(translations.get(r.get('text'),{}).get('he')) for r in reviews)
  image=images.get(id,{})
  row={'id':id,'title':game['title'],'editorialReview':bool(reviews),'publishers':names,'reviewCount':len(reviews),'allEditorialTextInHebrew':bool(reviews) and translated,'israeliReview':bool(local.get(id)),'imageStatus':image.get('status','not_checked'),'checks':checks.get(id,[])}
  rows.append(row);counts['total']+=1;counts['withEditorialReview']+=bool(reviews);counts['allEditorialTextInHebrew']+=bool(reviews) and translated;counts['israeliReview']+=bool(local.get(id));counts['multiplePublishers']+=len(names)>1
  if id not in checks:errors.append([id,'No review search result recorded'])
  if reviews and not translated:errors.append([id,'Missing Hebrew translation'])
  if image.get('status')=='ok' and image.get('url')!=meta.get(id,{}).get('image'):errors.append([id,'Stale image audit'])
 for text,t in translations.items():
  if t.get('sourceText')!=text or not t.get('he'):errors.append(['Invalid translation'])
 report={'coverage':dict(counts),'byPublisher':dict(publishers.most_common()),'errors':errors,'rows':rows}
 (ROOT/'data/editorial-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 lines=['# Editorial review coverage','',f"All {len(games)} catalog rows have been audited.",'','| Measure | Count |','| --- | ---: |']
 lines.extend(f'| {k} | {v} |' for k,v in counts.items())
 lines+=['','A score-only sentence and Wikipedia reception are not counted as editorial reviews. Excerpts via Metacritic retain both links. Hebrew translations are automatic and expose the English original. Image checks verify loading/decoding, not a visual inspection of every picture.','', 'Vgames automated archive access returned HTTP 403. Indexed reviews were manually matched where available; no claim of exhaustive Vgames coverage is made.','', '## No verified editorial review found','', '| Game | Search outcome |','| --- | --- |']
 for r in rows:
  if not r['editorialReview']:lines.append('| '+r['title'].replace('|','/')+' | '+', '.join(sorted({x['status'] for x in r['checks']}))+' |')
 (ROOT/'data/editorial-audit.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(json.dumps({'coverage':dict(counts),'errors':errors},ensure_ascii=True))
 return bool(errors)
if __name__=='__main__':raise SystemExit(main())
