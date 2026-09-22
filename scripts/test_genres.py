import unittest
from enrich_genres import tags
class GenreTests(unittest.TestCase):
 def test_hybrid_has_both_genres(self):
  self.assertEqual(tags('Action role-playing'),['action','rpg'])
 def test_puzzle_platform_has_both(self):
  self.assertEqual(tags('Puzzle-platform'),['platform','puzzle'])
 def test_apostrophes_and_punctuation(self):
  self.assertIn('beat-em-up',tags("Beat 'em up"))
  self.assertIn('shooter',tags("Top-Down Shoot-'Em-Up"))
 def test_skateboarding_is_not_board_game(self):
  self.assertIn('sports',tags('Skateboarding'))
  self.assertNotIn('board-card',tags('Skateboarding'))
 def test_unknown_is_not_guessed(self):self.assertEqual(tags('Unknown'),[])
 def test_deduplicates_categories(self):self.assertEqual(tags('Role-playing, RPG'),['rpg'])
if __name__=='__main__':unittest.main()
