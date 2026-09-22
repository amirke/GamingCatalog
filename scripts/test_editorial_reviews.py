import unittest
from enrich_editorial_reviews import parse_reviews,candidate_urls

def page(name='Example',url='https://critic.example/review',text='A thoughtful and challenging game with a memorable story.'):
 return '<script type="application/ld+json">{"@type":"VideoGame","name":"'+name+'"}</script>'+f'<div data-testid="review-card"><div data-testid="review-card-header">85 Critic</div><a data-testid="review-full-review-link" href="{url}"></a><div data-testid="review-quote-text">{text}</div><span data-testid="review-platform">PC</span></div>'

class EditorialReviewsTests(unittest.TestCase):
 def test_sequel_not_assigned_to_original(self):
  self.assertEqual(parse_reviews(page('Example 2'),['Example'],'https://www.metacritic.com/game/example/')[0],[])
 def test_validated_alias_and_platform_retained(self):
  rs,_,status=parse_reviews(page(),['Example (video game)'],'https://www.metacritic.com/game/example/')
  self.assertEqual(status,'matched');self.assertEqual(rs[0]['publisher'],'Critic');self.assertEqual(rs[0]['platform'],'PC')
 def test_excerpt_limited(self):
  rs,_,_=parse_reviews(page(text='word '*90),['Example'],'https://www.metacritic.com/game/example/')
  self.assertEqual(len(rs[0]['text'].split()),24)
 def test_non_web_links_rejected(self):
  self.assertEqual(parse_reviews(page(url='javascript:alert(1)'),['Example'],'https://www.metacritic.com/game/example/')[0],[])
 def test_score_without_review_is_missing(self):
  raw='<script type="application/ld+json">{"@type":"VideoGame","name":"Example","aggregateRating":{"ratingValue":90}}</script>'
  self.assertEqual(parse_reviews(raw,['Example'],'https://www.metacritic.com/game/example/')[2],'no_editorial_excerpt')
 def test_null_score_supported(self):
  self.assertEqual(candidate_urls({'title':'Example'},{'score':None}),['https://www.metacritic.com/game/example/'])

if __name__=='__main__':unittest.main()
