"""Browser acceptance checks. Run with the optional Playwright development dependency."""
import argparse
import functools
import json
import shutil
import sys
import tempfile
import threading
from datetime import timedelta
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.trading_calendar import timestamp
from scripts.update_market import update


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def check(browser, folder, url, screenshots, mobile_engine):
    source = json.loads((folder/"data/latest.json").read_text(encoding="utf-8"))
    first_date = source["session_date"]
    errors, requests = [], []
    for width in [375, 390, 768, 1440]:
        options = {"viewport": {"width": width, "height": 950 if width > 650 else 844}}
        if mobile_engine and width < 651:
            options.update(is_mobile=True, has_touch=True, device_scale_factor=1)
        page = browser.new_page(**options)
        # Simulate a content blocker. Navigation and the direct provider link must still work.
        page.route("https://s3.tradingview.com/**", lambda route: route.abort())
        page.goto(url)
        expect(page.get_by_role("heading", name="U.S. stock screener")).to_be_visible()
        expect(page.get_by_role("link", name="open the screener on TradingView")).to_be_visible()
        expect(page.locator("#rating-link")).to_have_attribute("href", "https://www.tradingview.com/symbols/AMEX-SPY/technicals/")
        page.locator("#rating-symbol").fill("qqq")
        page.get_by_role("button", name="Show rating").click()
        expect(page.locator("#rated-symbol")).to_have_text("NASDAQ:QQQ")
        expect(page.locator("#rating-error")).to_be_visible()
        page.locator("#rating-symbol").fill("bad ticker")
        page.get_by_role("button", name="Show rating").click()
        assert not page.locator("#rating-symbol").evaluate("input => input.validity.valid")
        expect(page.locator("#rated-symbol")).to_have_text("NASDAQ:QQQ")
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: requests.append(request.url))
        page.clock.set_fixed_time(timestamp(source["updated_at_utc"]) + timedelta(minutes=2))
        page.get_by_role("link", name="Demo archive").click()
        expect(page.locator(".index")).to_have_count(3)
        expect(page.locator(".demo")).to_contain_text("Demo data")
        expect(page.locator("#history option")).to_have_count(30)
        if screenshots and (width == 1440 or width == 390):
            screenshots.mkdir(exist_ok=True, parents=True)
            page.screenshot(path=screenshots/("desktop.png" if width == 1440 else "mobile.png"), full_page=True)
        for group in ["overall","largecap"]:
            page.locator(f"[data-group={group}]").click()
            for side in ["gainers","losers"]:
                page.locator(f"[data-side={side}]").click()
                expected = [r["symbol"] for r in source["rankings"][f"{group}_{side}"]]
                assert page.locator(".listing button").all_text_contents() == expected
                first = page.locator(".listing button").first
                first.focus()
                first.press("Enter")
                expect(page.locator(".row-info:visible")).to_contain_text("Volume")
                if width <= 650:
                    expect(page.locator(".row-info:visible")).to_contain_text("Market cap")
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                first.press("Enter")
        archived = page.locator("#history option").nth(1).get_attribute("value")
        page.select_option("#history", archived)
        expect(page.locator("#notice")).to_contain_text("archived")
        expect(page.locator("#caption")).to_contain_text(archived)
        page.select_option("#history", first_date)
        expect(page.locator("#caption")).to_contain_text(first_date)
        page.get_by_text("Provider coverage and display rights", exact=True).click()
        expect(page.get_by_text("FMP plan and licensing")).to_be_visible()
        page.close()
    page = browser.new_page()
    page.clock.set_fixed_time(timestamp(source["next_update_due_utc"]) + timedelta(hours=1))
    page.goto(url + "demo.html")
    expect(page.locator("#notice")).to_contain_text("Stale")
    page.route("**/status.json", lambda route: route.fulfill(json={"state":"failed","session_date":first_date}))
    page.reload()
    expect(page.locator("#notice")).to_contain_text("Update failed")
    page.unroute("**/status.json")
    bad = dict(source, is_demo=False)
    page.route("**/latest.json", lambda route: route.fulfill(json=bad))
    page.reload()
    expect(page.locator("#retry")).to_be_visible()
    expect(page.locator(".index")).to_have_count(0)
    page.unroute("**/latest.json")
    page.locator("#retry").click()
    expect(page.locator(".index")).to_have_count(3)
    page.route("**/history/*.json", lambda route: route.abort())
    page.select_option("#history", index=1)
    expect(page.locator("#notice")).to_contain_text("Still showing " + first_date)
    page.unroute("**/history/*.json")
    page.locator("#retry").click()
    expect(page.locator("#notice")).to_contain_text("archived")
    empty = json.loads(json.dumps(source))
    empty["rankings"]["overall_gainers"] = []
    page.route("**/latest.json", lambda route: route.fulfill(json=empty))
    page.reload()
    expect(page.locator("#empty")).to_be_visible()
    page.unroute("**/latest.json")
    # Advance the served copy through another scheduled update, then reload the actual page.
    next_day = source["next_session"]
    update(timestamp(next_day + "T23:45:00Z"), folder/"data")
    page.reload()
    expect(page.locator("#history")).to_have_value(next_day)
    expect(page.locator("#caption")).to_contain_text(next_day)
    assert not errors, errors
    assert all(u.startswith(url) for u in requests)
    page.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", choices=["chromium","webkit"], default="chromium")
    parser.add_argument("--executable", help="Use an installed Chrome or Edge executable")
    parser.add_argument("--screenshots", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
        folder = Path(tmp)/"public"
        shutil.copytree(ROOT/"public", folder, ignore=shutil.ignore_patterns(".writer.lock"))
        handler = functools.partial(QuietHandler, directory=str(folder))
        with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
            threading.Thread(target=server.serve_forever, daemon=True).start()
            browser = getattr(pw, args.engine).launch(executable_path=args.executable)
            try:
                check(browser, folder, f"http://127.0.0.1:{server.server_port}/", args.screenshots, args.engine == "webkit")
            finally:
                browser.close()
                server.shutdown()
    print(f"{args.engine}: four responsive widths, four rankings, archive, recovery and next-session refresh passed")
