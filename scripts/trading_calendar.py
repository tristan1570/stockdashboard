"""NYSE regular sessions, including exchange holidays and special closing times."""
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

import exchange_calendars as xcals

NY = ZoneInfo("America/New_York")
CAL = xcals.get_calendar("XNYS")


def utc_string(moment):
    return moment.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def timestamp(value):
    moment = datetime.fromisoformat(value)
    if moment.utcoffset() is None:
        raise ValueError("Timestamp must include a time zone")
    return moment


def session_close(day):
    return CAL.session_close(day).to_pydatetime()


def decision(now):
    day = now.astimezone(NY).date().isoformat()
    if not CAL.is_session(day):
        return day, "No trading session"
    if now < session_close(day):
        return day, "Session still open"
    return day, None


def previous(day):
    return CAL.previous_session(day).date().isoformat()


def schedule(day):
    following = CAL.next_session(day).date()
    return {
        "next_session": following.isoformat(),
        "next_update_due_utc": utc_string(datetime.combine(following, time(23, 45), UTC) + timedelta(hours=1)),
    }
