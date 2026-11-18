"""Public release contract. The current edition accepts synthetic snapshots only."""
from datetime import date
from scripts.data_providers import INDEX_NAMES, PROVIDER
from scripts.rankings import LARGE_CAP, changes, number
from scripts.trading_calendar import CAL, session_close, timestamp


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(s):
    day = s["session_date"]
    date.fromisoformat(day)
    require(CAL.is_session(day) and timestamp(s["updated_at_utc"]) >= session_close(day), "Invalid release time")
    require(s["schema_version"] == 1 and s["data_status"] == "valid" and s["market_status"] == "closed",
            "Invalid snapshot status")
    require(s["is_demo"] is True and s["provider"] == PROVIDER and s["license_status"] == "synthetic_only",
            "Public edition requires synthetic observations")
    require(all(s["coverage"][k] is False for k in ("overall_complete", "largecap_complete"))
            and s["rankings_complete"] is False, "Unverified market-wide coverage")
    indices = s["indices"]
    require(len(indices) == 3 and {i["symbol"] for i in indices} == set(INDEX_NAMES), "Index roster mismatch")
    for i in indices:
        require(i["name"] == INDEX_NAMES[i["symbol"]] and i["session_date"] == day, "Index date or name mismatch")
        require(i["source"] == PROVIDER and changes(i["close"], i["previous_close"]) == (i["change"], i["change_pct"]),
                "Index close mismatch")
        series = i["series"]
        expected = [d.date().isoformat() for d in CAL.sessions_window(day, -20)]
        require([p["date"] for p in series] == expected and all(number(p["close"]) and p["close"] > 0 for p in series)
                and [p["close"] for p in series[-2:]] == [i["previous_close"], i["close"]], "Index history mismatch")
    keys = {f"{group}_{side}" for group in ("overall", "largecap") for side in ("gainers", "losers")}
    require(set(s["rankings"]) == keys, "Missing ranking")
    for key, rows in s["rankings"].items():
        sign = 1 if key.endswith("gainers") else -1
        require(len(rows) <= 10 and len({r["symbol"] for r in rows}) == len(rows), "Invalid ranking size")
        require(rows == sorted(rows, key=lambda r: (-sign * r["change_pct"], r["symbol"])), "Invalid rank order")
        for r in rows:
            require(r["session_date"] == day and r["source"] == PROVIDER and sign * r["change_pct"] > 0,
                    "Invalid ranking observation")
            require(changes(r["close_usd"], r["previous_close_usd"]) == (r["change_usd"], r["change_pct"]),
                    "Inconsistent daily change")
            if key.startswith("largecap"):
                require((r["market_cap_usd"] or 0) >= LARGE_CAP, "Invalid large-cap membership")
    breadth = s["breadth"]
    require(all(type(breadth[k]) is int and breadth[k] >= 0 for k in ("advancing", "declining", "unchanged"))
            and sum(breadth.values()) == s["coverage"]["eligible_count"] > 0, "Invalid market breadth")
