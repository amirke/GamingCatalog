"""Collect short Hebrew editorial review excerpts from GamePro (no forums).
Matches the leading English game name or an exact review URL slug. Cached/resumable.
"""
import argparse, datetime, hashlib, json, pathlib, re, time, urllib.request
from lxml import html
from enrich_catalog import normalized
ROOT=pathlib.Path(__file__).resolve().parents[1]

def plain(e):return ' '.join(e.text_content().split())
def candidates(doc,games):
 out={}
 for a in doc.xpath('//h2/a|//h3/a'):
  title=plain(a);url=a.get('href','')
  if any(part in url for part in ['round-up', 'roundup', 'first-review', 'worlds-first', 'reviews-are']):continue
  if 'ביקורת' not in title or 'ביקורות' in title or not url.startswith('https://gamepro.co.il/'):continue
  english=re.findall(r"[A-Za-z0-9][A-Za-z0-9 '\u2019:&!.+/-]*",title)
  names=[normalized(english[0])] if english else []
  slug=url.rstrip('/').split('/')[-1]
  if slug.endswith('-review'):names.append(normalized(slug[:-7]))
  matches=[g['id'] for g in games if normalized(g['title']) in names]
  if matches:out[url]={'title':title,'url':url,'games':matches}
 return out

def extract(raw,item):
 doc=html.fromstring(raw)
 paragraphs=[plain(p) for p in doc.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," entry-content ")]//p')]
 paragraphs=[p for p in paragraphs if len(p.split())>=12 and not any(x in p for x in ['טלגרם','הצטרפו','עדכונים שוטפים','עקבו אחרינו','כתבות נוספות','כל הזכויות','הביקורת נכתבה','הביקורת מבוססת','עותק סיקור','עותק ביקורת','גילוי נאות'])]
 if not paragraphs:return None
 # Prefer a concluding paragraph; no fabricated translation or sentiment.
 conclusions=[p for p in paragraphs if re.search(r'לסיכום|גזר דין|ממליץ|מומלץ|משחק חובה',p)]
 opinions=[p for p in paragraphs if re.search(r'מהנה|מעולה|מצוין|מרשים|מאכזב|מאתגר|חסרונות|חובה',p)]
 text=(conclusions or opinions or paragraphs)[-1];words=text.split();excerpt=' '.join(words[:24])+('…' if len(words)>24 else '')
 score=doc.xpath('//*[contains(@class,"lets-review-block__final-score") and not(contains(@class,"-type"))]')
 if not score:score=doc.xpath('//div[contains(@class,"lets-review-block__final-score ")]')
 rating=plain(score[0]) if score else None
 if rating and not re.fullmatch(r'(?:10|[0-9](?:\.\d+)?)',rating):rating=None
 return {'publisher':'GamePro','title':item['title'],'url':item['url'],'text':excerpt,'language':'he','kind':'excerpt','score':float(rating) if rating else None,'scale':10,'platform':None}

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cache-dir',type=pathlib.Path,required=True);ap.add_argument('--offline',action='store_true');args=ap.parse_args();args.cache_dir.mkdir(parents=True,exist_ok=True)
 games=json.loads((ROOT/'data/catalog.js').read_text(encoding='utf-8').split('=',1)[1].strip().rstrip(';'))['games'];items={};failures=0
 def fetch(url,file):
  nonlocal failures
  if not file.exists() and not args.offline:
   time.sleep(1)
   try:
    with urllib.request.urlopen(url,timeout=25) as response:file.write_bytes(response.read())
    failures=0
   except Exception as error:
    failures+=1;print('Fetch failed:',url,str(error),flush=True)
    if failures>=2:args.offline=True
  return file.read_bytes() if file.exists() else None
 for i in range(1,8):
  url='https://gamepro.co.il/category/reviews/'+(f'page/{i}/' if i>1 else '');raw=fetch(url,args.cache_dir/f'gamepro-{i}.html')
  if raw:items.update(candidates(html.fromstring(raw),games))
 entries={};manual=json.loads((ROOT/'scripts/hebrew-review-sources.json').read_text(encoding='utf-8'))
 for item in manual:
  for game in games:
   if normalized(game['title'])==normalized(item['game']):entries.setdefault(game['id'],[]).append({k:v for k,v in item.items() if k!='game'})
 for url,item in items.items():
  raw=fetch(url,args.cache_dir/(hashlib.sha256(url.encode()).hexdigest()+'.html'))
  if not raw:continue
  review=extract(raw,item)
  if review:
   for id in item['games']:
    current=entries.setdefault(id,[])
    if not any(r['publisher']=='GamePro' for r in current):current.append(review)
 ign_path=ROOT/'data/ign-reviews.json'
 if ign_path.exists():
  for id,review in json.loads(ign_path.read_text(encoding='utf-8')).items():entries.setdefault(id,[]).append(review)
 priorities={'Vgames':0,'IGN Israel':1,'GamePro':2}
 for reviews in entries.values():reviews.sort(key=lambda r:priorities.get(r['publisher'],99))
 payload={'generatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'entries':entries}
 (ROOT/'data/hebrew-reviews.js').write_text('window.HEBREW_REVIEWS = '+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
 report={'withHebrewReview':len(entries),'total':len(games),'byPublisher':{name:sum(any(r['publisher']==name for r in rs) for rs in entries.values()) for name in priorities},'unmatched':[g['title'] for g in games if g['id'] not in entries]}
 (ROOT/'data/hebrew-review-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Hebrew reviews:',len(entries),'of',len(games))
if __name__=='__main__':main()
