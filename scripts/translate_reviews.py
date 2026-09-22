"""Translate public Wikipedia reception excerpts to Hebrew; never reads personal notes.
Anonymous translation endpoint: cached, paced, stops on rate limits; no API key required.
"""
import argparse,concurrent.futures,datetime,hashlib,json,pathlib,re,threading,time,urllib.parse,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cache-dir',type=pathlib.Path,required=True);ap.add_argument('--offline',action='store_true');ap.add_argument('--batch-size',type=int,choices=[1,2,3,4],default=4);args=ap.parse_args();args.cache_dir.mkdir(parents=True,exist_ok=True)
 metadata=json.loads((ROOT/'data/metadata.js').read_text(encoding='utf-8').split('=',1)[1].strip().rstrip(';'))['entries'];texts=list(dict.fromkeys(m['receptionText']['text'] for m in metadata.values() if m.get('receptionText')));stop=threading.Event()
 translated={};pending=[]
 for text in texts:
  path=args.cache_dir/(hashlib.sha256(text.encode()).hexdigest()+'.json')
  if path.exists():
   cached=json.loads(path.read_text(encoding='utf-8'))
   if cached.get('sourceText')==text and re.search('[א-ת]',cached.get('he','')):translated[text]=cached['he'];continue
  pending.append(text)
 batches=[];batch=[];size=0
 for text in pending:
  if batch and (size+len(text)>3500 or len(batch)>=args.batch_size):batches.append(batch);batch=[];size=0
  batch.append(text);size+=len(text)
 if batch:batches.append(batch)
 def translate_batch(batch):
  if args.offline or stop.is_set():return {}
  time.sleep(1)
  if stop.is_set():return {}
  source='\n'.join(f'[[[GC{i:04d}]]]\n'+text for i,text in enumerate(batch))
  url='https://translate.googleapis.com/translate_a/single?'+urllib.parse.urlencode({'client':'gtx','sl':'en','tl':'he','dt':'t','q':source})
  try:
   with urllib.request.urlopen(url,timeout=40) as response:result=json.load(response)
   hebrew=''.join(part[0] for part in result[0] if part and isinstance(part[0],str))
   parts=re.split(r'\[\[\[GC(\d{4})\]\]\]',hebrew)
   if len(parts)!=1+2*len(batch) or [parts[i] for i in range(1,len(parts),2)]!=[f'{i:04d}' for i in range(len(batch))]:raise ValueError('Translation batch boundaries changed')
   output={}
   for i,text in enumerate(batch):
    value=parts[2*i+2].strip()
    if not re.search('[א-ת]',value):raise ValueError('No Hebrew translation returned')
    output[text]=value
   for text,value in output.items():
    path=args.cache_dir/(hashlib.sha256(text.encode()).hexdigest()+'.json')
    path.write_text(json.dumps({'sourceText':text,'he':value,'provider':'Google Translate'},ensure_ascii=False),encoding='utf-8')
   return output
  except Exception as error:stop.set();print('Translation stopped:',str(error),flush=True);return {}
 print('Cached',len(translated),'pending',len(pending),'batches',len(batches),flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for i,result in enumerate(pool.map(translate_batch,batches),1):
   translated.update(result)
   if i%10==0:print('Batches',i,'of',len(batches),'translated',len(translated),'of',len(texts),flush=True)
 entries={id:{'sourceText':m['receptionText']['text'],'he':translated[m['receptionText']['text']],'provider':'Google Translate'} for id,m in metadata.items() if m.get('receptionText') and m['receptionText']['text'] in translated}
 payload={'generatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'entries':entries}
 (ROOT/'data/review-translations.js').write_text('window.REVIEW_TRANSLATIONS = '+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
 report={'wikiExcerpts':sum(bool(m.get('receptionText')) for m in metadata.values()),'translated':len(entries),'missing':[id for id,m in metadata.items() if m.get('receptionText') and id not in entries]}
 (ROOT/'data/translation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report),flush=True)
if __name__=='__main__':main()
