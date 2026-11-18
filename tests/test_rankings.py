import unittest
from scripts.data_providers import demo_feed
from scripts.rankings import changes, normalize, rank

DAY = "2026-11-17"


class RankingTests(unittest.TestCase):
    def setUp(self):
        self.raw = demo_feed(DAY)["securities"][0]

    def norm(self, **fields):
        return normalize([self.raw | fields], DAY)

    def test_change_math(self):
        for close, expected in [(10, 0), (11, 10), (8, -20)]:
            self.assertEqual(changes(close, 10), (close - 10, expected))
        for invalid in [None, "10", -1, 0, float("nan"), float("inf"), True]:
            with self.assertRaises(ValueError):
                changes(2, invalid)

    def test_instruments(self):
        for kind in ["ETF", "ETN", "PREFERRED", "UNIT", "RIGHT", "WARRANT", "MUTUAL_FUND", "CLOSED_END"]:
            self.assertEqual(self.norm(security_type=kind), [])
        for fields in [{"exchange": "OTC"}, {"exchange": "LSE"}, {"currency": "CAD"}, {"active": False}]:
            self.assertEqual(self.norm(**fields), [])
        for kind in ["COMMON", "ADR", "REIT_COMMON"]:
            self.assertEqual(len(self.norm(security_type=kind, close=.12)), 1)

    def test_comparability_and_identity(self):
        for fields in [{"previous_session": DAY}, {"session_date": "2026-11-16"}, {"price_type": "after_hours"},
                       {"price_timestamp": DAY + "T22:01:00Z"}, {"comparable_previous": False}, {"symbol": "A!?"}]:
            with self.assertRaises(ValueError):
                self.norm(**fields)
        self.assertEqual(self.norm(close=25, previous_close=25, comparable_previous=True)[0]["change_pct"], 0)

    def test_caps(self):
        for cap, when, qualifies in [(10e9, DAY, True), (10e9 - 1, DAY, False), (None, DAY, False),
                                     ("11B", DAY, False), (-10, DAY, False), (12e9, "2026-10-01", False),
                                     (12e9, "2026-11-18", False)]:
            rows = self.norm(close=11, previous_close=10, market_cap_usd=cap, market_cap_date=when)
            self.assertEqual(bool(rank(rows)["largecap_gainers"]), qualifies)

    def test_duplicate_listings_and_distinct_classes(self):
        rows = [self.raw, self.raw.copy(), self.raw | {"symbol": "ASTQ.B", "listing_id": "class-b"}]
        self.assertEqual(len(normalize(rows, DAY)), 2)
        with self.assertRaises(ValueError):
            normalize([self.raw, self.raw | {"close": 3}], DAY)
        with self.assertRaises(ValueError):
            normalize([self.raw, self.raw | {"listing_id": "conflict"}], DAY)

    def test_cutoff_ties_signs_and_empty(self):
        rows = [{"symbol": chr(65 + i), "market_cap_usd": 10e9, "change_pct": p}
                for i, p in enumerate([8, 8, 7, 6, 5, 4, 3, 2, 1, .8, .1, 0, -1, -3])]
        results = rank(rows[::-1])
        self.assertEqual([r["symbol"] for r in results["overall_gainers"]], list("ABCDEFGHIJ"))
        self.assertEqual([r["symbol"] for r in results["largecap_losers"]], ["N", "M"])
        self.assertTrue(all(not v for v in rank([]).values()))

    def test_large_caps_rank_from_entire_universe(self):
        rows = [{"symbol": str(i), "change_pct": 100-i, "market_cap_usd": 1e6} for i in range(60)]
        rows += [{"symbol": "BIG", "change_pct": 1, "market_cap_usd": 20e9}]
        self.assertEqual(rank(rows)["largecap_gainers"][0]["symbol"], "BIG")
