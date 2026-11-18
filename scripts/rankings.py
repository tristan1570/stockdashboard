import math
import re
from datetime import date

from scripts.trading_calendar import previous, session_close, timestamp

LARGE_CAP = 10_000_000_000
EXCHANGES = {"NYSE", "NASDAQ", "NYSE AMERICAN"}
TYPES = {"COMMON", "REIT_COMMON", "ADR"}
SYMBOL = re.compile(r"[A-Z][A-Z0-9.-]{0,14}")


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def changes(close, prior):
    if not all(number(x) and x > 0 for x in (close, prior)):
        raise ValueError("Invalid close")
    pct = (close - prior) / prior * 100
    if not math.isfinite(pct):
        raise ValueError("Invalid percentage")
    return round(close - prior, 8), pct


def quote_fields(raw, day):
    if (raw["session_date"] != day or raw["previous_session"] != previous(day)
            or timestamp(raw["price_timestamp"]) != session_close(day)
            or raw["price_type"] != "regular_close" or raw["comparable_previous"] is not True):
        raise ValueError("Session, official close or corporate-action comparison invalid")
    delta, pct = changes(raw["close"], raw["previous_close"])
    return dict(close_usd=raw["close"], previous_close_usd=raw["previous_close"],
                change_usd=delta, change_pct=pct, session_date=day, source=raw["source"])


def normalize(records, day):
    rows, symbols = {}, {}
    for raw in records:
        if not (raw["active"] is True and raw["exchange"] in EXCHANGES
                and raw["security_type"] in TYPES and raw["currency"] == "USD"):
            continue
        symbol = raw["symbol"]
        if not SYMBOL.fullmatch(symbol) or not raw["name"] or not raw["listing_id"]:
            raise ValueError("Invalid listing identity")
        fields = quote_fields(raw, day)
        cap = raw.get("market_cap_usd")
        if number(cap) and cap > 0 and raw.get("market_cap_date"):
            age = (date.fromisoformat(day) - date.fromisoformat(raw["market_cap_date"])).days
            cap = cap if 0 <= age <= 7 else None
        else:
            cap = None
        volume = raw.get("volume")
        if volume is not None and (type(volume) is not int or volume < 0):
            raise ValueError("Invalid volume")
        row = {**fields, "symbol": symbol, "name": raw["name"], "exchange": raw["exchange"],
               "market_cap_usd": cap, "volume": volume}
        identity = raw["listing_id"]
        if identity in rows and rows[identity] != row or symbol in symbols and symbols[symbol] != identity:
            raise ValueError("Conflicting duplicate listing")
        rows[identity], symbols[symbol] = row, identity
    return list(rows.values())


def rank(rows):
    results = {}
    for group in ("overall", "largecap"):
        pool = rows if group == "overall" else [r for r in rows if (r["market_cap_usd"] or 0) >= LARGE_CAP]
        for side, sign in (("gainers", 1), ("losers", -1)):
            matching = (r for r in pool if sign * r["change_pct"] > 0)
            results[f"{group}_{side}"] = sorted(matching, key=lambda r: (-sign * r["change_pct"], r["symbol"]))[:10]
    return results
