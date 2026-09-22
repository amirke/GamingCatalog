import unittest
from lxml import html
from enrich_hebrew_reviews import candidates, extract
from supplement_metadata import parse_page

class SourceMatchingTests(unittest.TestCase):
 def test_incidental_comparison_does_not_match_other_game(self):
  doc=html.fromstring('<h2><a href="https://gamepro.co.il/turtles-review/">ביקורת: Teenage Mutant Ninja Turtles – כש Hades פוגש פיצה</a></h2>')
  self.assertEqual(candidates(doc,[{'id':'1','title':'Hades'}]),{})
 def test_roundup_is_not_editorial_review(self):
  doc=html.fromstring('<h2><a href="https://gamepro.co.il/beyond-two-souls-reviews-round-up/">ביקורת: Beyond Two Souls</a></h2>')
  self.assertEqual(candidates(doc,[{'id':'1','title':'Beyond Two Souls'}]),{})
 def test_sequel_not_assigned_to_original(self):
  doc=html.fromstring('<h2><a href="https://gamepro.co.il/doom-2-review/">ביקורת: Doom 2</a></h2>')
  self.assertEqual(candidates(doc,[{'id':'1','title':'Doom'}]),{})
 def test_source_notice_not_used_as_review(self):
  raw='<div class="entry-content"><p>'+'משחק מוצלח ומאתגר '*15+'</p><p>הביקורת נכתבה '+('גרסת מחשב '*20)+'</p></div>'
  r=extract(raw,{'title':'Test','url':'https://gamepro.co.il/test-review/'})
  self.assertNotIn('נכתבה',r['text']);self.assertLessEqual(len(r['text'].split()),24)
 def test_unrelated_metacritic_title_rejected(self):
  raw='<script type="application/ld+json">{"@type":"VideoGame","name":"Doom 2"}</script>'
  self.assertIsNone(parse_page(raw,'Doom','https://www.metacritic.com/game/doom/'))
 def test_prefer_explicit_ps4_score(self):
  raw='<script type="application/ld+json">{"@type":"VideoGame","name":"Example"}</script>'
  for platform,score in [('pc',90),('playstation-4',75)]:raw+=f'<a data-testid="product-score-card" href="?platform={platform}"><span aria-label="Metascore {score} out of 100"></span></a>'
  result=parse_page(raw,'Example','https://www.metacritic.com/game/example/')
  self.assertEqual(result['score']['platform'],'playstation-4');self.assertEqual(result['score']['value'],75)
if __name__=='__main__':unittest.main()
