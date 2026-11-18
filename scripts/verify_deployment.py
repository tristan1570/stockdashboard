"""Trigger a Pages production build when the public release differs, then verify its content."""
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, build_opener
from urllib.parse import urlsplit

from scripts.data_providers import NoRedirect

PUBLIC = Path(__file__).resolve().parents[1] / "public"


def release_files():
    sessions = json.loads((PUBLIC / "data/sessions.json").read_text(encoding="utf-8"))
    files = ["index.html", "app.js", "styles.css", "data/latest.json", "data/sessions.json", "data/status.json",
             "data/history/" + sessions[0] + ".json"]
    if (PUBLIC / "data/deployment-check.txt").is_file():
        files.append("data/deployment-check.txt")
    return files


def matches(base, files, opener):
    for name, digest in files.items():
        path = "" if name == "index.html" else name
        url = f"{base}/{path}?release={digest[:16]}"
        try:
            request = Request(url, headers={"Cache-Control": "no-cache", "User-Agent": "MarketDaily-Deployment-Check/1.0"})
            with opener.open(request, timeout=10) as res:
                if hashlib.sha256(res.read()).hexdigest() != digest:
                    return False
        except (TimeoutError, URLError):
            return False
    return True


def deploy(base, hook):
    if not base and not hook:
        print("Repository-only run. Set PAGES_URL to enable hosted verification.")
        return
    if not re.fullmatch(r"https://[a-z0-9-]+\.pages\.dev/?", base or ""):
        raise ValueError("Set PAGES_URL to the production pages.dev origin")
    parts = urlsplit(hook or "")
    if hook and (parts.scheme != "https" or parts.netloc != "api.cloudflare.com"
                 or not re.fullmatch(r"/client/v4/pages/webhooks/deploy_hooks/[A-Za-z0-9_-]+", parts.path)):
        raise ValueError("Configure a production Cloudflare Pages deploy hook")
    opener = build_opener(NoRedirect())
    files = {name: hashlib.sha256((PUBLIC / name).read_bytes()).hexdigest() for name in release_files()}
    base = base.rstrip("/")
    if matches(base, files, opener):
        print("Verified production already serves this release.")
        return
    if hook:
        try:
            with opener.open(Request(hook, method="POST", data=b""), timeout=20) as res:
                if res.status // 100 != 2:
                    raise RuntimeError("Deploy hook rejected")
        except (OSError, ValueError):
            raise RuntimeError("Deploy hook request failed. Check the Pages secret and deployment log.") from None
    else:
        print("Waiting for the Cloudflare Git integration to deploy the checked-out release.", flush=True)
    for _ in range(24):
        time.sleep(15)
        if matches(base, files, opener):
            print("Production HTML, assets, latest snapshot, history entry, manifest and update status match.")
            return
    raise RuntimeError("Production content did not match the release before the verification deadline")


if __name__ == "__main__":
    try:
        deploy(os.environ.get("PAGES_URL"), os.environ.get("PAGES_DEPLOY_HOOK"))
    except (ValueError, RuntimeError) as exc:
        sys.exit(str(exc))
