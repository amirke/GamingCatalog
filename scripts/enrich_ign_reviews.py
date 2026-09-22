"""Collect short Hebrew IGN Israel game reviews. Cached, exact-title matching; no forums."""
import argparse,hashlib,json,pathlib,re,time,urllib.request,urllib.parse
from lxml import html
from enrich_catalog import normalized
ROOT=pathlib.Path(__file__).resolve().parents[1]
def candidates(raw,games):
 found={};doc=html.fromstring(raw)
 for a in doc.xpath('//a[contains(@href,"/review/")]'):
  url=a.get('href','').split('#')[0];title=' '.join(a.text_content().split())
  if not url.startswith('https://il.ign.com/') or 'ביקורת' not in title or re.search(r'עונה|סרט|פרק|סדרה',title):continue
  slug=urllib.parse.urlparse(url).path.split('/')[1];parts=re.findall(r"[A-Za-z0-9][A-Za-z0-9 '\u2019:&!.+/-]*",title);keys=[normalized(slug)]+([normalized(parts[0])] if parts else [])
  matches=[g['id'] for g in games if normalized(g['title']) in keys]
  if matches:found[url]={'title':title,'url':url,'games':matches}
 return found

def extract(raw,item):
 doc=html.fromstring(raw);containers=doc.xpath('//div[contains(concat(" ",normalize-space(@class)," ")," article-review-content ")]')
 if not containers:return None
 root=containers[0];blurbs=root.xpath('.//div[@class="blurb"]');text=' '.join(blurbs[0].text_content().split()) if blurbs else ''
 if not re.search('[א-ת]',text):
  paras=doc.xpath('//*[@id="id_text"]//p');texts=[' '.join(p.text_content().split()) for p in paras];texts=[t for t in texts if len(t.split())>=12 and re.search('[א-ת]',t)];text=texts[-1] if texts else ''
 if not re.search('[א-ת]',text):return None
 nodes=root.xpath('.//span[contains(concat(" ",normalize-space(@class)," ")," hexagon-content ")]');score=None
 if nodes:
  match=re.match(r'\s*(\d+(?:\.\d+)?)',nodes[0].text_content())
  if match and 0<=float(match[1])<=10:score=float(match[1])
 platform='PC' if re.search(r'\bPC\b|מחשב',item['title'],re.I) else 'Nintendo Switch' if 'סוויטץ' in item['title'] else None
 words=text.split();return {'publisher':'IGN Israel','title':item['title'],'url':item['url'],'text':' '.join(words[:24])+('…' if len(words)>24 else ''),'language':'he','kind':'excerpt','score':score,'scale':10,'platform':platform}

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cache-dir',type=pathlib.Path,required=True);ap.add_argument('--offline',action='store_true');ap.add_argument('--archive-pages',type=int,default=70);args=ap.parse_args();args.cache_dir.mkdir(parents=True,exist_ok=True)
 games=json.loads((ROOT/'data/catalog.js').read_text(encoding='utf-8').split('=',1)[1].strip().rstrip(';'))['games'];found={};failures=0
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
 for page in range(1,args.archive_pages+1):
  raw=fetch('https://il.ign.com/article/review/?page='+str(page),args.cache_dir/f'archive-{page}.html')
  if raw:found.update(candidates(raw,games))
 outpath=ROOT/'data/ign-reviews.json';entries=json.loads(outpath.read_text(encoding='utf-8')) if outpath.exists() else {}
 for url,item in found.items():
  raw=fetch(url,args.cache_dir/(hashlib.sha256(url.encode()).hexdigest()+'.html'))
  review=extract(raw,item) if raw else None
  if review:
   for id in item['games']:entries[id]=review
 outpath.write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('IGN Israel:',len(entries),'catalog rows')
if __name__=='__main__':main()
