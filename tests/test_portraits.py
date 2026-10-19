import unittest
from bs4 import BeautifulSoup
from collect import portrait_url, parse_profile_portrait, enrich_portraits


class PortraitTests(unittest.TestCase):
    def test_ignores_tracking_placeholder_and_uses_lazy_image(self):
        node = BeautifulSoup('<img src="data:image/gif;base64,xxx" data-src="https://img.aso.fr/rider.png|https://img.aso.fr/large.png">', 'html.parser').img
        self.assertEqual(portrait_url(node), 'https://img.aso.fr/rider.png')

    def test_wrong_host_not_used(self):
        node = BeautifulSoup('<img src="https://unrelated.example/portrait.png">', 'html.parser').img
        self.assertIsNone(portrait_url(node))

    def test_does_not_use_team_mates_photo(self):
        profile = 'https://www.lavueltafemenina.es/en/rider/2/team/rider'
        html = '<a href="/en/rider/1/team/other"><img class="riderFocus__img" src="https://img.aso.fr/wrong.png"></a><a href="/en/rider/2/team/rider"><img class="riderFocus__img" src="https://img.aso.fr/correct.png"></a>'
        self.assertEqual(parse_profile_portrait(html, profile), 'https://img.aso.fr/correct.png')

    def test_redirected_profile_not_used(self):
        html = '<link rel="canonical" href="https://www.lavueltafemenina.es/en/rider/1/team/other"><img class="pageIntroJerseys__img" src="https://img.aso.fr/wrong.png">'
        self.assertIsNone(parse_profile_portrait(html,'https://www.lavueltafemenina.es/en/rider/2/team/rider'))

    def test_portrait_failure_keeps_rider_and_initials(self):
        def broken(url):
            raise OSError('Unavailable')
        race = enrich_portraits({'standings':[{'rider':'Demi VOLLERING', 'profile_url':'https://example.test/profile'}]}, broken)
        self.assertEqual(race['standings'][0]['initials'],'DV')
        self.assertIsNone(race['standings'][0]['portrait_url'])
        self.assertEqual(race['standings'][0]['rider'],'Demi VOLLERING')
