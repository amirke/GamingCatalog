"""Regression checks for the extraction mistakes that can silently corrupt a catalog."""
import unittest
import enrich_catalog as e


def page(text):
    return {'title': 'Test game', 'revisions': [{'content': text, 'revid': 123}], 'pageprops': {}}


class ExtractionTests(unittest.TestCase):
    def test_adjacent_templates_do_not_hide_earliest_year(self):
        result = e.extract(page("{{Infobox video game|released={{vgrelease|WW|February 20, 2024}}'''macOS'''{{vgrelease|WW|March 1, 2024}}'''Nintendo Switch 2'''{{vgrelease|WW|February 25, 2026}}}}"))
        self.assertEqual(result['year'], 2024)

    def test_html_breaks_and_comments(self):
        result = e.extract(page("{{Infobox video game\n<!-- documentation -->|released='''PS4, Windows'''<br/>14 May 2019<br/>'''PS5'''<br/>6 July 2021}}"))
        self.assertEqual(result['year'], 2019)

    def test_release_alias(self):
        self.assertEqual(e.extract(page('{{Infobox video game|release=February 21, 2023}}'))['year'], 2023)

    def test_citation_dates_not_used_as_release_dates(self):
        result = e.extract(page('{{Infobox video game|released={{vgrelease|WW|May 2018}}<ref>{{cite web|date=2001|access-date=2025}}</ref>}}'))
        self.assertEqual(result['year'], 2018)

    def test_ps4_score_preferred_and_platform_preserved(self):
        code = e.mw.parse('{{Video game reviews\n<!-- scores -->|MC=PC: 88/100<br/>PS4: 79/100}}')
        self.assertEqual(e.extract_score(code, '')['value'], 79)
        self.assertEqual(e.extract_score(code, '')['platform'], 'PS4')

    def test_non_ps4_score_never_labeled_ps4(self):
        code = e.mw.parse('{{Video game reviews|MC_PS3=91/100}}')
        self.assertEqual(e.extract_score(code, 'PS3 PS4')['platform'], 'PS3')

    def test_unidentified_score_platform_stays_unknown(self):
        code = e.mw.parse('{{Video game reviews|MC=79/100}}')
        self.assertEqual(e.extract_score(code, 'PS4 Windows')['platform'], 'unspecified')

    def test_franchise_is_not_a_game_match(self):
        self.assertIsNone(e.extract(page('{{Infobox video game series|first release date=1997}}')))

    def test_conflicting_optional_platform_year_is_omitted(self):
        row = {'cells': ['', '', '', '', '2019', '2019', '2019'], 'source': 'https://en.wikipedia.org/wiki/List'}
        result = e.extract(page('{{Infobox video game|released=2020}}'), row)
        self.assertEqual(result['year'], 2020)
        self.assertIsNone(result['ps4Year'])

    def test_summary_does_not_invent_missing_pros(self):
        summary = e.summarize('Critics praised the music but criticized the camera.', None)
        self.assertIn('music', summary['en'])
        self.assertIn('camera', summary['en'])
        self.assertNotIn('combat', summary['en'])
        self.assertIsNone(e.summarize('', None))


if __name__ == '__main__':
    unittest.main()
