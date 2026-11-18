"""Synthetic session provider and a read-only, quota-bounded FMP entitlement probe."""
import argparse
import json
import logging
import math
import os
import socket
import time
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, build_opener

from scripts.trading_calendar import CAL, previous, session_close, utc_string

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/sample_market_data.json"
PROVIDER = "Market Daily simulation"
INDEX_NAMES = {"^GSPC": "S&P 500", "^IXIC": "Nasdaq Composite", "^DJI": "Dow Jones Industrial Average"}


def simulated_price(day, base, seed, amplitude):
    n = date.fromisoformat(day).toordinal()
    wave = math.sin(n * .67 + seed * 2.39) + .55 * math.sin(n * .23 - seed * .63)
    return round(base * (1 + amplitude * wave), 4 if base < 1 else 2)


def demo_feed(day):
    spec = json.loads(FIXTURE.read_text(encoding="utf-8"))
    prior = previous(day)
    stamp = utc_string(session_close(day))
    common = dict(session_date=day, previous_session=prior, price_timestamp=stamp,
                  price_type="regular_close", comparable_previous=True, source=PROVIDER)
    securities = []
    for i, stock in enumerate(spec["securities"]):
        amplitude = .05 if i < 26 else .17
        def price(d):
            return simulated_price(d, stock["base_price"], i, amplitude)
        securities.append({**stock, **common, "close": price(day), "previous_close": price(prior),
                           "market_cap_date": day, "listing_id": stock["symbol"],
                           "volume": 140000 + (date.fromisoformat(day).toordinal() * (i + 3) * 317) % 12000000})
    dates = [x.date().isoformat() for x in CAL.sessions_window(day, -20)]
    indices = []
    for i, (symbol, name, base) in enumerate(spec["indices"]):
        series = [{"date": d, "close": simulated_price(d, base, i + 1, .013)} for d in dates]
        indices.append({**common, "symbol": symbol, "name": name, "series": series,
                        "close": series[-1]["close"], "previous_close": series[-2]["close"]})
    return {"securities": securities, "indices": indices}


class ProviderError(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


def fetch_rows(endpoint, params, key, open_url=None, sleep=time.sleep):
    if not key:
        raise ProviderError("MARKET_DATA_API_KEY is missing")
    if open_url is None:
        open_url = build_opener(NoRedirect()).open
    url = "https://financialmodelingprep.com/stable/" + endpoint + "?" + urlencode({**params, "apikey": key})
    for attempt in range(3):
        logging.info("FMP endpoint=%s attempt=%s", endpoint, attempt + 1)
        delay = 2 ** attempt
        try:
            with open_url(url, timeout=12) as response:
                rows = json.load(response)
            if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
                raise ProviderError("Unexpected provider payload")
            return rows
        except HTTPError as exc:
            if exc.code in (401, 402, 403):
                raise ProviderError(f"HTTP {exc.code}: check key and endpoint entitlement") from None
            if exc.code != 429 and not 500 <= exc.code < 600:
                raise ProviderError(f"HTTP {exc.code}: request refused") from None
            retry = exc.headers.get("Retry-After", "") if exc.headers else ""
            if retry and (not retry.isdigit() or int(retry) > 60):
                raise ProviderError("Provider requested a longer retry interval") from None
            delay = max(delay, int(retry or 0))
        except (URLError, socket.timeout, ConnectionError):
            pass
        except (ValueError, UnicodeError):
            raise ProviderError("Invalid provider JSON") from None
        if attempt < 2:
            sleep(delay)
    raise ProviderError("Provider unavailable after three attempts") from None


def probe():
    endpoints = [("biggest-gainers", {}), ("biggest-losers", {}),
                 ("company-screener", {"marketCapMoreThan": 9999999999, "isEtf": "false",
                                       "isFund": "false", "isActivelyTrading": "true", "limit": 1000}),
                 ("batch-quote", {"symbols": "AAPL,MSFT"})]
    endpoints.extend(("quote", {"symbol": symbol}) for symbol in INDEX_NAMES)
    failed = False
    for endpoint, params in endpoints:
        try:
            rows = fetch_rows(endpoint, params, os.environ.get("MARKET_DATA_API_KEY"))
            logging.info("endpoint=%s rows=%d coverage=unverified", endpoint, len(rows))
        except ProviderError as exc:
            logging.error("endpoint=%s %s", endpoint, exc)
            failed = True
        time.sleep(1)
    return int(failed)


if __name__ == "__main__":
    argparse.ArgumentParser(description="Probe FMP entitlements without saving quotes").parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    raise SystemExit(probe())
