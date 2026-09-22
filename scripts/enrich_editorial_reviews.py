"""Check every catalog title for attributed editorial excerpts, using cached Metacritic pages.

Never treats a score or store description as a review. Exact title matching only.
Publisher excerpts are at most 24 words, with both publisher and aggregator links.
"""
import argparse, concurrent.futures, datetime, hashlib, json, pathlib, re, threading, time
import urllib.error, urllib.parse, urllib.request
from lxml import html
from enrich_catalog import normalized

ROOT = pathlib.Path(__file__).resolve().parents[1]
UA = 'GamingCatalog/1.0 (https://github.com/amirke/GamingCatalog; personal library)'
ALIASES = json.loads((ROOT/'scripts/editorial-titles.json').read_text(encoding='utf-8'))

def readjs(name):
    return json.loads((ROOT/'data'/name).read_text(encoding='utf-8').split('=',1)[1].strip().rstrip(';'))

def title_key(title):
    return normalized(re.sub(r'\s*\((?:\d{4} )?(?:video )?game\)$', '', title, flags=re.I))

def parse_reviews(raw, titles, url):
    doc = html.fromstring(raw)
    names = []
    for text in doc.xpath('//script[@type="application/ld+json"]/text()'):
        try: data = json.loads(text)
        except ValueError: continue
        for item in data if isinstance(data,list) else [data]:
            if isinstance(item,dict) and item.get('@type')=='VideoGame': names.append(item.get('name',''))
    if not any(title_key(n) in {title_key(t) for t in titles} for n in names):
        return [], None, 'title_not_matched'
    reviews = []
    for card in doc.xpath('//*[@data-testid="review-card"]'):
        links = card.xpath('.//*[@data-testid="review-full-review-link"]/@href')
        quotes = card.xpath('.//*[@data-testid="review-quote-text"]')
        heads = card.xpath('.//*[@data-testid="review-card-header"]')
        if not links or not quotes or not heads: continue
        words = ' '.join(quotes[0].text_content().split()).split()
        publisher = re.sub(r'^\d+\s*','',' '.join(heads[0].text_content().split()))
        if len(words)<5 or not publisher or not links[0].startswith(('https://','http://')): continue
        if any(r['publisher']==publisher for r in reviews): continue
        platform = ' '.join(card.xpath('.//*[@data-testid="review-platform"]/text()')).strip()
        reviews.append({'publisher':publisher,'text':' '.join(words[:24])+('…' if len(words)>24 else ''),
                        'url':links[0],'via':url,'platform':platform,'language':'en','kind':'excerpt'})
    reviews.sort(key=lambda r: {'Vgames':0,'IGN Israel':1,'IGN':2}.get(r['publisher'],3))
    image = None
    for text in doc.xpath('//script[@type="application/ld+json"]/text()'):
        try: data=json.loads(text)
        except ValueError:continue
        if isinstance(data,dict) and data.get('@type')=='VideoGame' and isinstance(data.get('image'),str):
            if urllib.parse.urlparse(data['image']).hostname=='www.metacritic.com':image=data['image']
    return reviews[:3], image, 'matched' if reviews else 'no_editorial_excerpt'

def candidate_urls(game, metadata):
    urls=[ALIASES[game['title']]['url']] if game['title'] in ALIASES else []
    for u in [(metadata.get('score') or {}).get('url'), metadata.get('supplementSource'), metadata.get('source')]:
        if u and urllib.parse.urlparse(u).hostname=='www.metacritic.com':
            match=re.match(r'https://www.metacritic.com/game/([^/]+)',u)
            if match:urls.append(match.group(0)+'/')
    title=game['title'];slug=re.sub(r'[^a-z0-9]+','-',title.lower().replace('&','and').replace("'",'')).strip('-')
    urls.append('https://www.metacritic.com/game/'+slug+'/')
    return list(dict.fromkeys(urls))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cache-dir',required=True,type=pathlib.Path)
    ap.add_argument('--offline',action='store_true');ap.add_argument('--delay',type=float,default=1)
    args=ap.parse_args();args.cache_dir.mkdir(parents=True,exist_ok=True)
    games=readjs('catalog.js')['games'];meta=readjs('metadata.js')['entries']
    stop=threading.Event();lock=threading.Lock();failures=0
    def fetch(url):
        nonlocal failures
        file=args.cache_dir/(hashlib.sha256(url.encode()).hexdigest()+'.html')
        if file.exists():return file.read_bytes(),'cached'
        if args.offline or stop.is_set():return None,'not_fetched'
        time.sleep(args.delay)
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA}),timeout=25) as r:raw=r.read()
            file.write_bytes(raw)
            with lock:failures=0
            return raw,'fetched'
        except urllib.error.HTTPError as e:
            if e.code==404:file.write_text('<html></html>');return None,'http_404'
            with lock:failures+=1
            if e.code in [403,429] or failures>=2:stop.set()
            return None,'http_'+str(e.code)
        except Exception as e:
            with lock:failures+=1
            if failures>=2:stop.set()
            return None,type(e).__name__
    def process(game):
        m=meta.get(game['id'],{});checks=[];result=[];image=None
        for url in candidate_urls(game,m):
            raw,state=fetch(url)
            if raw:
                result,image,state=parse_reviews(raw,[game['title'],m.get('matchedTitle',game['title']),ALIASES.get(game['title'],{}).get('title',game['title'])],url)
            checks.append({'url':url,'status':state})
            if state=='no_editorial_excerpt':
                review_url=url.rstrip('/')+'/critic-reviews/'
                review_raw,review_state=fetch(review_url)
                if review_raw:result,review_image,review_state=parse_reviews(review_raw,[game['title'],m.get('matchedTitle',game['title']),ALIASES.get(game['title'],{}).get('title',game['title'])],review_url);image=review_image or image
                checks.append({'url':review_url,'status':review_state})
            if result:break
        return game['id'],result,image,checks
    entries={};checks={};images={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for n,(id,reviews,img,attempts) in enumerate(pool.map(process,games),1):
            if reviews:entries[id]=reviews
            if img:images[id]={'image':img,'imageSource':attempts[-1]['url']}
            checks[id]=attempts
            if n%25==0:print('Checked',n,'/',len(games),'editorial matches',len(entries),flush=True)
    # Re-running offline never deletes a previously verified record.
    path=ROOT/'data/editorial-reviews.js'
    old=readjs('editorial-reviews.js')['entries'] if path.exists() else {}
    old.update(entries);entries=old
    for review in json.loads((ROOT/'scripts/editorial-manual.json').read_text(encoding='utf-8')):
        for game in games:
            if game['title']==review['game']:
                current=entries.setdefault(game['id'],[])
                current[:]=[r for r in current if r['url']!=review['url']]
                current.insert(0,{k:v for k,v in review.items() if k!='game'})
                checks[game['id']].append({'url':review['url'],'status':'verified_manual_summary'})
    payload={'generatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'entries':entries}
    path.write_text('window.EDITORIAL_REVIEWS = '+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
    report={'total':len(games),'withEditorialReview':len(entries),'checks':checks,'missing':[{'id':g['id'],'title':g['title']} for g in games if g['id'] not in entries]}
    (ROOT/'data/editorial-review-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (args.cache_dir/'matched-images.json').write_text(json.dumps(images,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Finished:',len(entries),'of',len(games),'with editorial excerpts;',len(report['missing']),'unresolved',flush=True)

if __name__=='__main__':main()
