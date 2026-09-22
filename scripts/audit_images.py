"""Check every image URL using decoded image bytes. Cached; stops a host after repeated failures.
Never reports skipped/rate-limited URLs as broken. Does not inspect private browser data.
"""
import argparse,concurrent.futures,datetime,hashlib,io,json,pathlib,threading,time,urllib.request,urllib.error,urllib.parse
from PIL import Image
from enrich_editorial_reviews import readjs,ROOT,UA

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cache-dir',type=pathlib.Path,required=True);ap.add_argument('--offline',action='store_true');args=ap.parse_args();args.cache_dir.mkdir(parents=True,exist_ok=True)
 games=readjs('catalog.js')['games'];metadata=readjs('metadata.js')['entries'];urls=list(dict.fromkeys(m['image'] for m in metadata.values() if m.get('image')));lock=threading.Lock();blocked=set();failures={}
 def check(url):
  file=args.cache_dir/(hashlib.sha256(url.encode()).hexdigest()+'.json');host=urllib.parse.urlparse(url).hostname
  if file.exists():
   cached=json.loads(file.read_text(encoding='utf-8'))
   if cached.get('error')=='UnidentifiedImageError':cached['status']='invalid_image'
   return url,cached
  if args.offline or host in blocked:return url,{'status':'not_checked'}
  time.sleep(.8)
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA}),timeout=20) as r:
    raw=r.read(12*1024*1024+1)
    if len(raw)>12*1024*1024:return url,{'status':'too_large_to_check'}
   with Image.open(io.BytesIO(raw)) as img:width,height=img.size;img.verify()
   result={'status':'ok','width':width,'height':height,'checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat()}
   with lock:failures[host]=0
  except urllib.error.HTTPError as e:
   result={'status':'missing' if e.code in [404,410] else 'unavailable','httpStatus':e.code}
   if e.code in [403,429]:blocked.add(host)
  except Exception as e:
   result={'status':'unavailable','error':type(e).__name__}
   with lock:
    failures[host]=failures.get(host,0)+1
    if failures[host]>=2:blocked.add(host)
  file.write_text(json.dumps(result),encoding='utf-8');return url,result
 results={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for n,(url,result) in enumerate(pool.map(check,urls),1):
   results[url]=result
   if n%50==0:print('Images checked',n,'/',len(urls),'loaded',sum(x['status']=='ok' for x in results.values()),flush=True)
 rows=[{'id':g['id'],'title':g['title'],'url':metadata.get(g['id'],{}).get('image'),**results.get(metadata.get(g['id'],{}).get('image'),{'status':'no_image'})} for g in games]
 counts={state:sum(r['status']==state for r in rows) for state in sorted({r['status'] for r in rows})}
 (ROOT/'data/image-audit.json').write_text(json.dumps({'total':len(games),'coverage':counts,'rows':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(counts,flush=True)
if __name__=='__main__':main()
