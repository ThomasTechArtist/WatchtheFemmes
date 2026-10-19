from datetime import date, datetime, timezone
import unittest
from display import build_display, refresh_due, load_calendar

CAL = [{'key':'tour', 'name':'Tour', 'edition':2027, 'start':'2027-07-30', 'end':'2027-08-07', 'verified_at':'2026-10-18'}]


class DisplayTests(unittest.TestCase):
    def test_calendar_chronological(self):
        data = build_display({'races':[]}, CAL, date(2027,7,29))
        self.assertEqual(data['mode'], 'calendar')
        self.assertEqual(data['upcoming'][0]['days_to_go'], 1)

    def test_old_edition_not_presented_as_current(self):
        data = build_display({'races':[{'key':'tour','edition':2026,'standings':[{}]}]}, CAL, date(2027,7,30))
        self.assertEqual(data['mode'], 'race')
        self.assertIsNone(data['focus'])

    def test_race_end_is_inclusive(self):
        data = build_display({'races':[{'key':'tour','edition':2027,'standings':[{}]}]}, CAL, date(2027,8,7))
        self.assertIsNotNone(data['focus'])
        self.assertEqual(build_display({'races':[]}, CAL, date(2027,8,8))['mode'], 'calendar')

    def test_cadence(self):
        race_now = datetime(2027,7,30,12,tzinfo=timezone.utc)
        off_now = datetime(2027,7,29,12,tzinfo=timezone.utc)
        self.assertTrue(refresh_due({'checked_at':'2027-07-30T11:30:00+00:00','races':[]},race_now,CAL))
        self.assertFalse(refresh_due({'checked_at':'2027-07-29T11:30:00+00:00','races':[]},off_now,CAL))
        self.assertTrue(refresh_due(None,off_now,CAL))

    def test_calendar_dates_are_valid_and_sorted(self):
        calendar = load_calendar()
        self.assertEqual([e['key'] for e in calendar], ['giro','tour','vuelta'])


if __name__ == '__main__':
    unittest.main()
