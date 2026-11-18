import unittest
from scripts.trading_calendar import decision, previous, schedule, timestamp


class CalendarTests(unittest.TestCase):
    def test_closed_dates(self):
        for day in ["2025-01-09", "2026-07-03", "2026-11-21", "2026-11-26", "2026-12-25"]:
            self.assertEqual(decision(timestamp(day+"T23:45:00Z")), (day, "No trading session"))

    def test_early_close_and_dst(self):
        for date, before, close in [("2026-11-27", "17:59", "18:00"), ("2026-03-09", "19:59", "20:00"),
                                    ("2026-11-02", "20:59", "21:00")]:
            self.assertTrue(decision(timestamp(f"{date}T{before}:00Z"))[1])
            self.assertIsNone(decision(timestamp(f"{date}T{close}:00Z"))[1])

    def test_exchange_dates(self):
        self.assertEqual(decision(timestamp("2026-11-18T02:00:00Z")), ("2026-11-17", None))
        self.assertEqual(previous("2026-11-27"), "2026-11-25")
        self.assertEqual(schedule("2026-11-25")["next_session"], "2026-11-27")
