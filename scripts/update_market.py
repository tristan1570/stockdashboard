"""Build a validated static demo release after the NYSE close."""
import argparse
import json
import logging
import os
import sys
import tempfile
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.data_providers import FIXTURE, PROVIDER, ROOT, demo_feed
from scripts.rankings import LARGE_CAP, normalize, quote_fields, rank
from scripts.trading_calendar import CAL, decision, schedule, session_close, timestamp, utc_string
from scripts.validate_data import require, validate

DATA = ROOT / "public/data"


def snapshot(day, moment, feed):
    rows = normalize(feed["securities"], day)
    roster = {s["symbol"] for s in json.loads(FIXTURE.read_text(encoding="utf-8"))["securities"]}
    require({r["symbol"] for r in rows} == roster, "Incomplete synthetic listing roster")
    indices = []
    for index in feed["indices"]:
        fields = quote_fields(index, day)
        indices.append({k: index[k] for k in ("symbol", "name", "close", "previous_close", "series", "source")}
                       | {"session_date": day, "change_pct": fields["change_pct"], "change": fields["change_usd"]})
    s = {"schema_version": 1, "session_date": day, "updated_at_utc": utc_string(moment),
         "session_close_utc": utc_string(session_close(day)), **schedule(day),
         "market_status": "closed", "data_status": "valid", "freshness": "Simulated end-of-day",
         "is_demo": True, "provider": PROVIDER, "source_urls": [], "license_status": "synthetic_only",
         "universe_description": "Fictional active common shares, common REITs and ADRs assigned to Nasdaq, NYSE or NYSE American.",
         "coverage": {"overall_complete": False, "largecap_complete": False, "eligible_count": len(rows),
                      "largecap_count": sum((r["market_cap_usd"] or 0) >= LARGE_CAP for r in rows)},
         "rankings_complete": False,
         "warnings": ["Synthetic data. Actual market-wide rankings are unavailable."],
         "indices": indices, "rankings": rank(rows),
         "breadth": {"advancing": sum(r["change_pct"] > 0 for r in rows),
                     "declining": sum(r["change_pct"] < 0 for r in rows),
                     "unchanged": sum(r["change_pct"] == 0 for r in rows)}}
    validate(s)
    return s


def write_json(path, obj):
    content = json.dumps(obj, allow_nan=False, ensure_ascii=False, separators=(",", ":")) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8", suffix=".tmp") as f:
        tmp = Path(f.name)
        try:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        except BaseException:
            f.close()
            tmp.unlink(missing_ok=True)
            raise
    try:
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


@contextmanager
def writer_lock(folder):
    # Kernel releases the lock when a process exits, including after interruption.
    import sys
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / ".writer.lock").open("a+b") as lock:
        if sys.platform == "win32":
            import msvcrt
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def update(moment, folder=DATA, seed=False, provider=demo_feed):
    day, skip = decision(moment)
    if skip:
        logging.info("%s on %s; zero vendor requests", skip, day)
        return skip
    with writer_lock(folder):
        latest = folder / "latest.json"
        cached = json.loads(latest.read_text(encoding="utf-8")) if latest.exists() else None
        if cached:
            validate(cached)
            if day < cached["session_date"]:
                return "Older session skipped"
        try:
            dates = [day]
            if seed:
                dates = [d.date().isoformat() for d in CAL.sessions_window(day, -30)]
            staged = {}
            for d in dates:
                history = folder / "history" / f"{d}.json"
                if history.exists():
                    saved = json.loads(history.read_text(encoding="utf-8"))
                    validate(saved)
                    require(saved["session_date"] == d, "Archive date mismatch")
                    staged[d] = saved
                else:
                    staged[d] = snapshot(d, moment if d == day else session_close(d), provider(d))
            report = staged[day]
            for d, value in staged.items():
                write_json(folder / "history" / f"{d}.json", value)
            paths = sorted((folder / "history").glob("????-??-??.json"), reverse=True)
            keep = [p.stem for p in paths if p.stem <= day][:30]
            write_json(folder / "sessions.json", keep)
            write_json(latest, report)
            write_json(folder / "status.json", {"state": "ok", "session_date": day})
            for p in paths:
                if p.stem < keep[-1]:
                    p.unlink()
            logging.info("Session %s; %d demo equities; zero vendor requests", day, report["coverage"]["eligible_count"])
            return "Session ready"
        except (ValueError, TypeError, KeyError, OSError) as exc:
            write_json(folder / "status.json", {"state": "failed", "session_date": day,
                                               "attempted_at_utc": utc_string(moment)})
            raise ValueError(f"Update failed for {day}: {exc}") from None


def verify(folder):
    latest = json.loads((folder / "latest.json").read_text(encoding="utf-8"))
    validate(latest)
    days = json.loads((folder / "sessions.json").read_text(encoding="utf-8"))
    require(0 < len(days) <= 30 and days == sorted(set(days), reverse=True)
            and days[0] == latest["session_date"], "Archive manifest mismatch")
    for d in days:
        archived = json.loads((folder / "history" / f"{d}.json").read_text(encoding="utf-8"))
        validate(archived)
        require(archived["session_date"] == d and (d != days[0] or archived == latest), "Archive mismatch")
    return f"Verified {len(days)} sessions"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--at", type=timestamp, help="Offset-aware simulated run time")
    parser.add_argument("--seed-history", action="store_true", help="Seed the last 30 demo sessions")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--output", type=Path, default=DATA)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    print(verify(args.output) if args.verify else update(args.at or datetime.now(UTC), args.output, args.seed_history))
