"""Use already title-validated review-site artwork for missing or HTTP-404 images."""
import argparse,hashlib,json,pathlib
from enrich_editorial_reviews import readjs,ROOT,ALIASES,parse_reviews

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cache-dir',type=pathlib.Path,required=True);args=ap.parse_args()
 payload=readjs('metadata.js');meta=payload['entries'];games=readjs('catalog.js')['games'];audit=ROOT/'data/image-audit.json'
 broken={r['id'] for r in json.loads(audit.read_text(encoding='utf-8'))['rows'] if r['status'] in ['missing','invalid_image'] or r.get('error')=='UnidentifiedImageError'} if audit.exists() else set()
 file=args.cache_dir/'matched-images.json';candidates=json.loads(file.read_text(encoding='utf-8')) if file.exists() else {}
 for game in games:
  alias=ALIASES.get(game['title'])
  if not alias:continue
  file=args.cache_dir/(hashlib.sha256(alias['url'].encode()).hexdigest()+'.html')
  if file.exists():
   _,image,_=parse_reviews(file.read_bytes(),[alias['title']],alias['url'])
   if image:candidates[game['id']]={'image':image,'imageSource':alias['url']}
 sp=ROOT/'data/metadata-supplements.json';supp=json.loads(sp.read_text(encoding='utf-8'));changes=[]
 for game in games:
  id=game['id'];m=meta.get(id,{})
  if m.get('image') and id not in broken:continue
  extra=candidates.get(id)
  if not extra or extra['image']==m.get('image'):continue
  extra=dict(extra)
  if not m.get('source'):extra.update(source=extra['imageSource'],sourceName='Metacritic',matchedTitle=ALIASES.get(game['title'],{}).get('title',game['title']))
  meta.setdefault(id,{}).update(extra);supp.setdefault(id,{}).update(extra);changes.append({'id':id,'title':game['title'],**extra})
 (ROOT/'data/metadata.js').write_text('window.GAME_METADATA = '+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
 sp.write_text(json.dumps(supp,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 report=ROOT/'data/image-repair-report.json';previous=json.loads(report.read_text(encoding='utf-8')) if report.exists() else [];by_id={r['id']:r for r in previous+changes}
 report.write_text(json.dumps(list(by_id.values()),ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Images repaired',len(changes))
if __name__=='__main__':main()
