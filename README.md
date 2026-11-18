# Market Daily

Market Daily is a mobile-friendly U.S. equity dashboard with a 30-session archive. The public edition uses synthetic prices, volumes, capitalizations and index levels. Each day’s four lists rank the 40-stock demonstration universe and its qualifying large caps. The two free providers reviewed did not establish the rights and coverage required for a public market-wide ranking. [Provider evaluation](docs/API_EVALUATION.md)

## Open the dashboard

The hosted demonstration is available on desktop and mobile. [Open Market Daily](https://stockdashboard-1bn.pages.dev/)

Run this command from the project folder using Python 3.12 or later. The included archive is ready to view without installing the updater dependencies.

```sh
python -m http.server 8000 --bind 127.0.0.1 --directory public
```

Open [the local dashboard](http://127.0.0.1:8000). Select a session, switch between overall and large-cap movers, and choose gainers or losers. Select a ticker to inspect its exchange, volume, comparable previous close and capitalization. The deployment guide explains how to obtain a free URL accessible from an iPhone. [Deployment guide](docs/DEPLOYMENT.md)

## Run the updater

Create and activate a Python environment. On Windows PowerShell, run the following from the project folder.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/update_market.py
.\.venv\Scripts\python.exe scripts/update_market.py --verify
```

On macOS or Linux, use `python3 -m venv .venv` and substitute `.venv/bin/python` for the Windows interpreter path. The CLI uses the current Eastern date, skips exchange holidays and open sessions, and preserves an existing validated release for the same day. Each invocation reports its outcome. The scheduled job uses 23:45 UTC on weekdays. Generation and browser visits each use zero vendor API requests.

For a reproducible simulation in a separate directory, run the following with the environment’s Python interpreter. The fixed clock is the simulated run time. Historical seed entries use the simulated close as their observation and release time.

```sh
python scripts/update_market.py --at 2026-11-17T23:45:00Z --seed-history --output .qa/replay
python scripts/update_market.py --at 2026-11-18T23:45:00Z --output .qa/replay
python scripts/update_market.py --verify --output .qa/replay
```

## Project structure

| Component | Responsibility |
| --- | --- |
| `scripts/trading_calendar.py` | XNYS holidays, special closes, previous sessions and next update deadlines in Eastern time |
| `scripts/data_providers.py` | Deterministic synthetic observations and an optional, read-only FMP entitlement probe |
| `scripts/rankings.py` | Listing eligibility, duplicate handling, comparable daily returns and four independently ranked lists |
| `scripts/validate_data.py` and `scripts/update_market.py` | Publication checks, atomic file replacement, bounded history and update status |
| `public/` | Static HTML, CSS, browser JavaScript and precomputed snapshots served from the same origin |
| `.github/workflows/` | Read-only CI checks and a serialized, scheduled refresh on the default branch |
| `scripts/verify_deployment.py` | Cloudflare deploy hook and production file verification |

Separate share classes remain eligible when they represent distinct listings. Duplicate records must agree. Dollar changes and percentage changes use the official-close input and a split-comparable previous close. Stale, missing and invalid market caps never qualify for large-cap status. A return of zero appears in session breadth and is excluded from both mover directions. The data contract always identifies this edition as synthetic and marks both real-market coverage flags false.

## Verification and operating costs

The local acceptance suite exercised Chrome and WebKit at 375, 390, 768 and 1440 CSS pixels. It also advanced a temporary archive to the next session and verified the browser displayed the new release. Device emulation covers the layout and browser engine. Physical iPhone and hosted acceptance require the deployed site. [Desktop screenshot](docs/screenshots/desktop.png) · [Mobile screenshot](docs/screenshots/mobile.png)

To reproduce the browser checks, install `playwright==1.59.0` in the project environment and run `python -m playwright install chromium webkit`. Then run `python tests/browser_check.py --engine chromium` and `python tests/browser_check.py --engine webkit`. To use an installed Chrome executable, pass its path with `--executable`. The test suite serves an isolated copy over loopback.

| Item | Current scope and cost |
| --- | --- |
| Local implementation, archive and browser visits | $0 in service fees. No account required. |
| Hosted demo | Targets $0 on Cloudflare Pages Free and within the repository owner’s GitHub Actions allowance. |
| Actual U.S. market-wide rankings and official index closes | Blocked pending sufficient data entitlements, coverage validation and public display rights. |
| OpenAI API | No integration, key or charges. |

The optional FMP probe uses `python -m scripts.data_providers` with a key already available in the process environment as `MARKET_DATA_API_KEY`. It logs endpoint names, attempts and counts. No vendor payload enters the static site. Adding a key does not enable live rankings. [Data rights and private-use options](docs/DATA_LICENSE.md)
