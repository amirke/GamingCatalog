"""Build sourced multi-genre tags from cached Wikipedia and Metacritic metadata.
No title-based guessing. Unknown source labels are retained in the audit.
"""
import argparse,hashlib,json,pathlib,re,urllib.parse
from lxml import html
from enrich_catalog import absorb,infobox,mw,plain
ROOT=pathlib.Path(__file__).resolve().parents[1]
TAXONOMY=[
 ('action','פעולה','Action',r"action|hack.?and.?slash|beat[\s'’-]*em[\s'’-]*up|shooter|shoot[\s'’-]*em[\s'’-]*up|run.?and.?gun|bullet.?hell|twin.?stick"),
 ('adventure','הרפתקאות','Adventure',r'adventure|point.?and.?click|interactive.?fiction|walking.?simulator'),
 ('rpg','משחק תפקידים','Role-playing',r'role.?playing|\brpg\b|soulslike'),
 ('platform','פלטפורמה','Platformer',r'platform'),
 ('puzzle','פאזלים','Puzzle',r'puzzle'),
 ('shooter','יריות','Shooter',r"shooter|shoot[\s'’-]*em[\s'’-]*up|run.?and.?gun|bullet.?hell|twin.?stick"),
 ('fighting','קרבות','Fighting',r"fighting|beat[\s'’-]*em[\s'’-]*up"),
 ('racing','מרוצים','Racing',r'racing|kart'),
 ('sports','ספורט','Sports',r'sports|football|soccer|basketball|wrestling|skateboard|golf|tennis|cricket|hockey|baseball|snowboard'),
 ('strategy','אסטרטגיה','Strategy',r'strategy|tactics|tactical.?role|tower.?defen|4x'),
 ('simulation','סימולציה','Simulation',r'simulat|\bsim\b|sim.?racing|management|city.?build|construction'),
 ('survival','הישרדות','Survival',r'survival'),
 ('horror','אימה','Horror',r'horror'),
 ('stealth','התגנבות','Stealth',r'stealth'),
 ('music','מוזיקה וקצב','Music & rhythm',r'music|rhythm|karaoke|singing|dancing'),
 ('party','מסיבה','Party',r'party'),
 ('roguelike','רוגלייק','Roguelike',r'rogue'),
 ('metroidvania','מטרוידבניה','Metroidvania',r'metroidvania'),
 ('visual-novel','רומן חזותי','Visual novel',r'visual.?novel'),
 ('sandbox','עולם חופשי','Sandbox',r'sandbox'),
 ('beat-em-up','מכות רחוב','Beat ’em up',r"beat[\s'’-]*em[\s'’-]*up"),
 ('hack-slash','האק אנד סלאש','Hack and slash',r'hack.?and.?slash'),
 ('board-card','לוח וקלפים','Board & card',r'\bboard|card.?game|chess|deck.?build|mahjong'),
 ('trivia','טריוויה','Trivia',r'trivia|quiz'),
 ('pinball','פינבול','Pinball',r'pinball'),
 ('arcade','ארקייד','Arcade',r'arcade'),
 ('vehicle-combat','קרבות כלי רכב','Vehicular combat',r'vehicul|vehicle.?combat'),
 ('educational','חינוכי','Educational',r'education'),
 ('runner','ריצה אינסופית','Endless runner',r'endless.?runner'),
 ('fishing','דיג','Fishing',r'fishing'),
 ('creation','יצירה','Creation',r'game.?creation'),
 ('exploration','חקירה','Exploration',r'exploration|walking.?simulator'),
 ('interactive-film','סרט אינטראקטיבי','Interactive film',r'interactive.?film'),
 ('flight','טיסה וקרבות אוויר','Flight & aerial combat',r'aerial.?combat|space.?combat|flight'),
 ('compilation','אוסף משחקים','Compilation',r'compilation|collection'),
]

def tags(text):
 text=text.lower().replace('’',"'").replace('–','-')
 return [id for id,he,en,pattern in TAXONOMY if re.search(pattern,text)]

def loadjs(name):return json.loads((ROOT/'data'/name).read_text(encoding='utf-8').split('=',1)[1].strip().rstrip(';'))

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--wiki-cache',type=pathlib.Path,required=True);ap.add_argument('--critic-cache',type=pathlib.Path,required=True);args=ap.parse_args()
 games=loadjs('catalog.js')['games'];metadata=loadjs('metadata.js')['entries'];pages={};redirects={}
 for f in list(args.wiki_cache.glob('batch-*.json'))+list(args.wiki_cache.glob('request-*.json')):absorb(json.loads(f.read_text(encoding='utf-8')),pages,redirects)
 rows=json.loads((args.wiki_cache/'matches.json').read_text(encoding='utf-8'));entries={};parsed={};unrecognized=[]
 for game in games:
  m=metadata.get(game['id'],{});title=m.get('matchedTitle');source=None;raw=''
  if title and title not in parsed:
   page=pages.get(title)
   if page:
    box=infobox(mw.parse(page.get('revisions',[{}])[0].get('content',''),skip_style_tags=True))
    raw=plain(box.get('genre').value) if box and box.has('genre') else plain(box.get('genres').value) if box and box.has('genres') else ''
   parsed[title]=raw
  raw=parsed.get(title,'')
  if raw:source='https://en.wikipedia.org/wiki/'+urllib.parse.quote(title.replace(' ','_'))
  if not raw:
   row=rows.get(game['title'])
   if row:raw=row['cells'][1];source=row['source']
  if not raw:
   slug=re.sub(r'[^a-z0-9]+','-',game['title'].lower().replace('&','and').replace("'",'')).strip('-');url='https://www.metacritic.com/game/'+slug+'/'
   cache=args.critic_cache/(hashlib.sha256(url.encode()).hexdigest()+'.html')
   if cache.exists():
    doc=html.fromstring(cache.read_bytes())
    from enrich_catalog import normalized
    for text in doc.xpath('//script[@type="application/ld+json"]/text()'):
     try:d=json.loads(text)
     except ValueError:continue
     if isinstance(d,dict) and d.get('@type')=='VideoGame' and normalized(d.get('name',''))==normalized(game['title']):
      val=d.get('genre','');raw=', '.join(val) if isinstance(val,list) else val;source=url;break
  genre_ids=tags(raw)
  if genre_ids:entries[game['id']]={'genres':genre_ids,'source':source,'sourceLabel':raw}
  elif raw:unrecognized.append({'title':game['title'],'label':raw})
 for title,item in json.loads((ROOT/'scripts/genre-sources.json').read_text(encoding='utf-8')).items():
  for game in games:
   if game['title']==title and game['id'] not in entries:
    ids=tags(item['sourceLabel'])
    if ids:entries[game['id']]={**item,'genres':ids}
 payload={'taxonomy':{id:{'he':he,'en':en} for id,he,en,_ in TAXONOMY},'entries':entries}
 (ROOT/'data/genres.js').write_text('window.GAME_GENRES = '+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
 report={'total':len(games),'classified':len(entries),'multipleGenres':sum(len(v['genres'])>1 for v in entries.values()),'unrecognizedLabels':unrecognized,'missing':[{'id':g['id'],'title':g['title']} for g in games if g['id'] not in entries]}
 (ROOT/'data/genre-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=True))
if __name__=='__main__':main()
