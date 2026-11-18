# Market data evaluation

**Decision on November 17, 2026.** The synthetic fixture passes for public demonstration. Financial Modeling Prep (FMP) Basic and Alpha Vantage Free both fail the acceptance criteria for public, market-wide daily rankings. Acquiring a personal key would enable account-specific testing. It would leave the display rights and coverage gaps described below unresolved.

## Financial Modeling Prep

FMP Basic requires registration and advertises $0 per month, 250 calls per day, a 500 MB trailing 30-day bandwidth allowance, and end-of-day access. Its plan matrix includes both movers endpoints and the three requested index quote symbols. This makes FMP a candidate for future permitted index use. Confirm the official closing session, comparable prior close, and timestamps with actual entitled responses before enabling it. The vendor's movers guide and API documentation do not establish the count, eligible security types, inclusion of NYSE American or exhaustive ranking methodology needed here. [Pricing and endpoint entitlements](https://site.financialmodelingprep.com/pricing-plans) · [Movers guide](https://site.financialmodelingprep.com/how-to/how-to-retrieve-market-movers-gainers-losers-and-most-active-stocks-using-a-free-api)

Basic limits company market cap and full stock quotes to a selection of symbols. Its matrix excludes the stock screener, stock batch quote and exchange-wide quote endpoints. Profile/reference fields may help classify individual records, but the review found no entitlement guaranteeing complete current classifications, capitalizations and closes for the eligible universe. A `country=US` screen could omit qualifying ADRs. A strict `marketCapMoreThan` filter can also omit companies on the $10 billion boundary. A response capped at 1,000 rows needs reconciliation against the full membership before ranking. [FMP pricing matrix](https://site.financialmodelingprep.com/pricing-plans) · [Batch quote documentation](https://site.financialmodelingprep.com/developer/docs/stable/batch-quote)

The two movers requests, one hypothetical screener page and three index calls would consume six requests per session, or up to 18 with two retries per request. Even assuming a complete single-page roster, adding one quote request per candidate yields `6 + N` calls before retries or reference lookups. At 245 candidates that exceeds the 250-call allowance. Batch and screen entitlements already preclude this approach. A separate agreement governs public display. [FMP pricing and licensing](https://site.financialmodelingprep.com/pricing-plans)

## Alpha Vantage

A registered free key normally permits 25 requests per day. The provider describes a separate higher allowance for verified projects. The standard movers feed updates after the trading day and returns 20 gainers and 20 losers, plus a most-active list. The response provides limited reference information. Qualifying all 40 movers with one additional request each would take 41 requests, or up to 123 with two retries per request, before any index calls. A profile lookup such as `OVERVIEW` provides a company market cap when available, but cannot discover a large-cap mover outside those first 20 positions. [API documentation](https://www.alphavantage.co/documentation/) · [Free usage and registration](https://www.alphavantage.co/support/)

The provider documents premium daily index series for SPX (S&P 500), COMP (Nasdaq Composite) and DJI (Dow Jones Industrial Average). We found no evidence of a free entitlement to all three official daily series or a comprehensive, classified cross-section with split-comparable previous closes. The free individual license covers personal use, and the published terms do not establish public distribution and snapshot rights for this dashboard. [Index documentation](https://www.alphavantage.co/documentation/) · [Terms of service, §§2–3](https://www.alphavantage.co/terms_of_service/)

## Direct HTTPS smoke tests

The following requests were issued directly once each on November 17, 2026. FMP requests intentionally omitted credentials because no registered key was configured. Alpha Vantage used the public example key from its documentation. Eight requests reached the vendors in this test, with zero calls charged to a personal key. Only response metadata was retained.

| Provider and request | Calls | Result |
| --- | ---: | --- |
| FMP `/stable/biggest-gainers` and `/stable/biggest-losers` | 2 | Each returned HTTP 401. Result counts and universe coverage could not be measured. |
| FMP `/stable/company-screener` using the plan's $10B, US, active, ETF, fund and 1,000-row parameters | 1 | HTTP 401. Pagination, completeness and a registered Basic response were unverified. |
| FMP `/stable/quote` once each for `^GSPC`, `^IXIC`, `^DJI` | 3 | Each returned HTTP 401. The plan matrix lists the symbols. Runtime close timestamps and prior closes remain unverified. |
| FMP `/stable/batch-quote` with AAPL and MSFT | 1 | HTTP 401. See Basic entitlement exclusions above. |
| Alpha Vantage `TOP_GAINERS_LOSERS` with the public example key | 1 | HTTP 200. The response contained 20 gainers and 20 losers, timestamped November 17, 2026 at 4:15:59 p.m. Eastern. |

The Alpha Vantage gainers row contained ticker, price, change amount, change percentage and volume. It lacked primary exchange, security class, verified capitalization and prior comparable close. The response timestamp alone cannot certify the session of each price or the provider's split treatment. The returned prices were excluded from the project fixtures and archive.

## Decision by output

| Output | Public release decision |
| --- | --- |
| Three actual index closes | Display rights unverified, with official daily prior-close observations still untested. Synthetic observations only. |
| Overall market gainers and losers | Eligible-universe coverage and classification unverified. Synthetic rankings only. |
| Large-cap gainers and losers | Neither free candidate establishes a complete, session-matched cross-section at the inclusive $10 billion threshold. Synthetic rankings only. |
| Public fixtures and session archive | Project-generated numbers with explicit demo labeling. Zero provider requests per refresh and per page view. |

For a future feed, obtain the grant described in [Data licensing](DATA_LICENSE.md), then reconcile same-session listing identifiers, eligible counts, quote dates, splits and cap as-of dates against an independent roster. Investigate all missing eligible rows. Compare the three index closes and a sample of positive and negative movers against independent, date-matched references before the first live publication. The current release contains no live observations to certify through that comparison.
