"""Add sourced reception text and fill gaps from public Metacritic game pages.
Uses exact normalized titles, cached responses, and a delay; never fills unknowns.
"""
import argparse, datetime, hashlib, json, pathlib, re, time, urllib.error, urllib.parse, urllib.request
from lxml import html
from enrich_catalog import normalized, reception, absorb, mw
ROOT=pathlib.Path(__file__).resolve().parents[1]

def readjs(name):
 return json.loads((ROOT/'data'/name).read_text(encoding='utf-8').split('=',1)[1].strip().rstrip(';'))

def parse_page(raw, title, url):
 doc=html.fromstring(raw)
 entries=[]
 for text in doc.xpath('//script[@type="application/ld+json"]/text()'):
  try:
   x=json.loads(text); entries.extend(x if isinstance(x,list) else [x])
  except ValueError: pass
 game=next((x for x in entries if x.get('@type')=='VideoGame' and normalized(x.get('name',''))==normalized(title)),None)
 if not game:return None
 result={'matchedTitle':game['name'],'source':url,'sourceName':'Metacritic','supplementSource':url,'checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 date=game.get('datePublished','')
 if re.match(r'(19[7-9]\d|20[0-2]\d)-',date):result['year']=int(date[:4])
 image=game.get('image')
 if isinstance(image,str) and urllib.parse.urlparse(image).hostname=='www.metacritic.com':result.update(image=image,imageSource=url)
 scores=[]
 for card in doc.xpath('//*[@data-testid="product-score-card"]'):
  score=card.xpath('.//*[@aria-label]/@aria-label'); match=re.search(r'Metascore (\d+) out of 100',' '.join(score))
  platform=urllib.parse.parse_qs(urllib.parse.urlparse(card.get('href','')).query).get('platform',[''])[0]
  if match and platform:scores.append({'value':int(match[1]),'provider':'Metacritic','platform':platform,'url':urllib.parse.urljoin(url,card.get('href'))})
 if scores:result['score']=next((s for s in scores if s['platform']=='playstation-4'),scores[0])
 excerpts=[]
 for card in doc.xpath('//*[@data-testid="review-card"]'):
  links=card.xpath('.//*[@data-testid="review-full-review-link"]/@href')
  quote=card.xpath('.//*[@data-testid="review-quote-text"]')
  header=card.xpath('.//*[@data-testid="review-card-header"]')
  if not links or not quote or not header:continue
  words=' '.join(quote[0].text_content().split()).split()
  if len(words)<5:continue
  # Deliberately short excerpt; full review remains at its publisher.
  publisher=re.sub(r'^\d+\s*','',' '.join(header[0].text_content().split()))
  platform=card.xpath('.//*[@data-testid="review-platform"]/text()')
  excerpts.append({'text':' '.join(words[:24])+('…' if len(words)>24 else ''),'publisher':publisher,'url':links[0],'via':url,'platform':' '.join(platform).strip(),'language':'en'})
  if len(excerpts)==2:break
 if excerpts:result['criticExcerpts']=excerpts
 return result

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cache-dir',type=pathlib.Path,required=True);ap.add_argument('--wiki-cache',type=pathlib.Path);ap.add_argument('--offline',action='store_true');ap.add_argument('--delay',type=float,default=2);args=ap.parse_args();args.cache_dir.mkdir(parents=True,exist_ok=True)
 payload=readjs('metadata.js');metadata=payload['entries'];catalog=readjs('catalog.js')['games'];suppath=ROOT/'data/metadata-supplements.json';supp=json.loads(suppath.read_text(encoding='utf-8')) if suppath.exists() else {}
 if args.wiki_cache:
  pages,redirects={},{}
  for path in list(args.wiki_cache.glob('batch-*.json'))+list(args.wiki_cache.glob('request-*.json')):
   absorb(json.loads(path.read_text(encoding='utf-8')),pages,redirects)
  for g in catalog:
   m=metadata.get(g['id'],{});p=pages.get(m.get('matchedTitle'))
   if not p:continue
   raw=p.get('revisions',[{}])[0].get('content','');text=reception(mw.parse(raw,skip_style_tags=True));text=re.sub(r'^\s*(Reception|Critical reception|Critical response|Reviews)\s*','',text,flags=re.I)
   if len(text.split())>=20:
    words=text.split();supp.setdefault(g['id'],{})['receptionText']={'text':' '.join(words[:110])+('…' if len(words)>110 else ''),'url':m['source'],'publisher':'Wikipedia (CC BY-SA)','language':'en'}
 results={};failures=0;report=[]
 for g in catalog:
  m=metadata.get(g['id'],{});title=g['title']
  if all(m.get(k) for k in ['year','image','score','review']):continue
  slug=re.sub(r'[^a-z0-9]+','-',title.lower().replace('&','and').replace("'",'')).strip('-');url='https://www.metacritic.com/game/'+slug+'/'
  if title not in results:
   cache=args.cache_dir/(hashlib.sha256(url.encode()).hexdigest()+'.html');result=None
   if not cache.exists() and not args.offline:
    time.sleep(args.delay)
    try:
     req=urllib.request.Request(url,headers={'User-Agent':'GamingCatalog/1.0 (https://github.com/amirke/GamingCatalog; personal library)'})
     with urllib.request.urlopen(req,timeout=30) as response:cache.write_bytes(response.read())
     failures=0
    except urllib.error.HTTPError as e:
     if e.code==404:cache.write_text('<html></html>');failures=0
     else:
      failures+=1
      if failures>=2 or e.code==429:args.offline=True
     print('HTTP',e.code,title,flush=True)
    except (urllib.error.URLError,TimeoutError) as e:
     failures+=1
     if failures>=2:args.offline=True
     print('Unavailable',title,str(e),flush=True)
   if cache.exists():result=parse_page(cache.read_bytes(),title,url)
   results[title]=result
   print(('Matched ' if result else 'Unresolved ')+title,flush=True)
  result=results[title]
  if result:
   extra=supp.setdefault(g['id'],{})
   for key,val in result.items():
    if key == 'criticExcerpts' and any(r.get('verifiedManually') for r in extra.get(key, [])):continue
    if key in ['criticExcerpts', 'supplementSource'] or not m.get(key):extra[key]=val
   if m.get('source','').startswith('https://en.wikipedia.org/'):extra.pop('sourceName',None)
  else:report.append(title)
 for id,extra in supp.items():metadata.setdefault(id,{}).update(extra)
 payload['generatedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 suppath.write_text(json.dumps(supp,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (ROOT/'data/metadata.js').write_text('window.GAME_METADATA = '+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
 (ROOT/'data/supplement-report.json').write_text(json.dumps({'unresolved':report,'receptionText':sum(bool(m.get('receptionText')) for m in metadata.values()),'criticExcerpts':sum(bool(m.get('criticExcerpts')) for m in metadata.values())},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
