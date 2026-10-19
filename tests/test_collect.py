import unittest

from collect import collect, parse_standings


def aso_html():
    rows = "".join(f"<tr><td>{i}</td><td>Rider {i}</td><td>{100+i}</td><td>Team</td><td>10h</td><td>+1</td></tr>" for i in range(1, 6))
    return '<title>Tour de France Femmes</title><h2>2026 Rankings - Stage 9</h2><table class="rankingTable"><thead><tr>' + ''.join(f'<th>{h}</th>' for h in ['Rank','Rider','Rider No.','Team','Times','Gap']) + '</tr></thead><tbody>' + rows + '</tbody></table>'


class CollectorTests(unittest.TestCase):
    def test_bib_column_not_confused_with_team(self):
        race = parse_standings('tour', aso_html())
        self.assertEqual(race['standings'][0]['team'], 'Team')
        self.assertEqual(race['edition'], 2026)
        self.assertEqual(race['stage'], 9)

    def test_reject_wrong_race(self):
        with self.assertRaises(ValueError):
            parse_standings('tour', aso_html().replace('Tour de France Femmes', 'Tour de France'))

    def test_tour_mobile_rank_does_not_shift_columns(self):
        html = aso_html().replace('<td>Rider 1</td>', '<td>Rider 1</td><td class="hidden--md hidden--lg">1</td>')
        race = parse_standings('tour', html)
        self.assertEqual(race['standings'][0]['team'], 'Team')

    def test_reject_missing_edition(self):
        with self.assertRaises(ValueError):
            parse_standings('tour', aso_html().replace('2026 Rankings - Stage 9', 'Standings'))

    def test_reject_missing_riders(self):
        with self.assertRaises(ValueError):
            parse_standings('tour', aso_html().replace('<td>5</td>', '<td>6</td>'))

    def test_giro_uses_gc_not_youth(self):
        rows = ''.join(f'<div class="line-table"><div class="position">{i}</div><div class="name">Name</div><div class="surname">Surname</div><div class="team">Team</div><div class="tempo">10:00:00</div><div class="distacco">0:30</div></div>' for i in range(1,6))
        race = parse_standings('giro', '<title>Giro d\'Italia Women 2026</title><div data-category="tab-classifica-CLGEN">' + rows + '</div><div data-category="tab-classifica-CLGENGIO">unrelated youth classification</div>')
        self.assertEqual(race['standings'][0]['rider'], 'Name Surname')

    def test_failure_preserves_last_good_timestamp(self):
        previous = {'races': [{'key':'tour','standings':[{'rider':'Previous'}], 'last_success_at':'yesterday'}]}
        def broken(key):
            raise ValueError('Source unavailable')
        result = collect(previous, broken, now='today')
        self.assertEqual(result['races'][0]['last_success_at'], 'yesterday')
        self.assertEqual(result['races'][0]['standings'][0]['rider'], 'Previous')
        self.assertTrue(result['races'][0]['stale'])
        self.assertEqual(result['races'][1]['standings'], [])


if __name__ == '__main__':
    unittest.main()
