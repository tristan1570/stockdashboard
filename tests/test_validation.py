import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from urllib.error import HTTPError

from scripts.data_providers import ProviderError, demo_feed, fetch_rows
from scripts.trading_calendar import timestamp
from scripts.update_market import snapshot, update, verify
from scripts.validate_data import validate

NOW = timestamp("2026-11-17T23:45:00Z")
DAY = "2026-11-17"


class ReleaseTests(unittest.TestCase):
    def test_publication_contract(self):
        valid = snapshot(DAY, NOW, demo_feed(DAY))
        for mutate in [lambda s: s.update(is_demo=False), lambda s: s.update(rankings_complete=True),
                       lambda s: s["coverage"].update(largecap_complete=True),
                       lambda s: s["indices"][0].update(session_date="2026-11-16"),
                       lambda s: s["rankings"]["overall_gainers"][0].update(change_pct=4),
                       lambda s: s["indices"].pop()]:
            broken = copy.deepcopy(valid)
            mutate(broken)
            with self.assertRaises(ValueError):
                validate(broken)

    def test_scheduling_and_history(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root)
            update(NOW, folder, seed=True)
            self.assertEqual(verify(folder), "Verified 30 sessions")
            latest = folder/"latest.json"
            original = latest.read_bytes(), latest.stat().st_mtime_ns
            for stamp in [NOW, timestamp("2026-11-14T23:45:00Z"), timestamp("2026-11-18T18:00:00Z"),
                          timestamp("2026-11-16T23:45:00Z")]:
                update(stamp, folder)
                self.assertEqual((latest.read_bytes(), latest.stat().st_mtime_ns), original)
            bad = demo_feed("2026-11-18")
            bad["securities"].pop()
            with self.assertRaises(ValueError):
                update(timestamp("2026-11-18T23:45:00Z"), folder, provider=lambda _: bad)
            self.assertEqual(latest.read_bytes(), original[0])
            self.assertFalse((folder/"history/2026-11-18.json").exists())
            self.assertEqual(json.loads((folder/"status.json").read_text())["state"], "failed")
            update(timestamp("2026-11-18T23:45:00Z"), folder)
            self.assertEqual(verify(folder), "Verified 30 sessions")
            self.assertEqual(len(list((folder/"history").glob("*.json"))), 30)


class NetworkTests(unittest.TestCase):
    def test_bad_key_or_json(self):
        for code in (401, 402, 403):
            call = Mock(side_effect=HTTPError("redacted", code, "", {}, None))
            with self.assertRaisesRegex(ProviderError, str(code)):
                fetch_rows("quote", {}, "unused", call, Mock())
            self.assertEqual(call.call_count, 1)
        for payload in (b"bad", b'{"error":"unused"}', b'[123]'):
            with self.assertRaises(ProviderError):
                fetch_rows("quote", {}, "unused", Mock(return_value=io.BytesIO(payload)), Mock())

    def test_bounded_retries(self):
        for exc in (TimeoutError(), HTTPError("", 503, "", {}, None), HTTPError("", 429, "", {}, None)):
            call, sleep = Mock(side_effect=exc), Mock()
            with self.assertRaises(ProviderError):
                fetch_rows("quote", {}, "unused", call, sleep)
            self.assertEqual((call.call_count, sleep.call_count), (3, 2))
        call = Mock(side_effect=[HTTPError("", 429, "", {"Retry-After":"5"}, None), io.BytesIO(b'[{}]')])
        sleep = Mock()
        self.assertEqual(fetch_rows("quote", {}, "unused", call, sleep), [{}])
        sleep.assert_called_once_with(5)
