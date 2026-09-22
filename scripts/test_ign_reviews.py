import unittest
from enrich_ign_reviews import candidates,extract
class IGNReviewTests(unittest.TestCase):
 def test_tv_review_not_game(self):
  raw='<a href="https://il.ign.com/the-last-of-us/12/review/test">ביקורת: The Last of Us עונה 1</a>'
  self.assertFalse(candidates(raw,[{'title':'The Last of Us','id':'a'}]))
 def test_sequel_not_original(self):
  raw='<a href="https://il.ign.com/blasphemous-2/12/review/test">ביקורת: Blasphemous 2</a>'
  self.assertFalse(candidates(raw,[{'title':'Blasphemous','id':'a'}]))
 def test_score_scoped_to_actual_review(self):
  raw='<div class="article-review-content"><span class="hexagon-content"><div>8</div>IGN Logo</span><div class="blurb">משחק מוצלח ומאתגר</div></div><div class="reviews-author"><span class="hexagon-content">10</span></div>'
  result=extract(raw,{'title':'ביקורת Game','url':'https://il.ign.com/game/1/review/test'})
  self.assertEqual(result['score'],8);self.assertEqual(result['text'],'משחק מוצלח ומאתגר')
 def test_english_name_is_not_hebrew_verdict(self):
  raw='<div class="article-review-content"><div class="blurb">Game title</div></div><div id="id_text"><p>'+('משחק מצוין ומאתגר '*8)+'</p></div>'
  result=extract(raw,{'title':'ביקורת Game','url':'https://il.ign.com/game/1/review/test'})
  self.assertIn('מצוין',result['text']);self.assertLessEqual(len(result['text'].split()),24)
if __name__=='__main__':unittest.main()
