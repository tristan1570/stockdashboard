# Data rights and deployment scope

The public homepage displays TradingView’s branded stock screener through its official embed. TradingView serves the observations directly to the browser and controls the available markets and delays. The site does not extract widget quotes, redistribute them as JSON or store them in the archive. Reviewed November 20, 2026. [TradingView widgets](https://www.tradingview.com/widget/) · [Widget data FAQ](https://www.tradingview.com/widget-docs/faq/data/)

The demo archive uses synthetic stock and index observations. They can be reproduced locally and published as a labeled software demonstration. No vendor quote payloads were copied into the fixtures.

## Daily indicators and written briefs

The official TradingView Technical Analysis widget displays moving-average and oscillator ratings. The dashboard passes it a symbol and a daily interval. TradingView's display license does not grant this public site permission to extract its quotes or ratings for automated commentary. [Widget documentation](https://www.tradingview.com/widget-docs/widgets/symbol-details/technical-analysis/) · [TradingView terms, §3](https://www.tradingview.com/policies/)

For a written report generated after the close and served as a static file, source rights must cover the calculations and persistence of the published results. Tiingo's Starter and trial terms prohibit durable storage of derived products. Twelve Data identifies public display of non-real-time derived analytics as a Venture plan use. Neither supplies verified free rights for the proposed stored public brief. Reviewed November 20, 2026. [Tiingo terms, §1.6](https://www.tiingo.com/tos/) · [Twelve Data usage guide](https://support.twelvedata.com/en/articles/5332349-commercial-and-personal-usage)

## Financial Modeling Prep

The FMP Services Subscription Agreement identifies August 1, 2023 as its last update. Sections 2.2 and 2.2.1 require prior written approval for public display and restrict personal use to the subscriber. Section 2.2.1 also restricts copying or downloading content without prior written approval. FMP's pricing page requires a specific Data Display and Licensing Agreement for display or redistribution. A private repository or password-protected site does not establish approval for storage or display. [FMP terms, §2](https://site.financialmodelingprep.com/terms-of-service) · [FMP display agreement notice](https://site.financialmodelingprep.com/pricing-plans)

## Alpha Vantage

The terms reviewed grant personal, non-commercial use on equipment under the user's control. Section 2 defines activities beyond private individual use as commercial, and §3 ties the agreement's effective date to the user's free-key acceptance. No version date appears in the reviewed terms. Public hosting, downloadable JSON, redistribution and a 30-session public archive require further authorization for this design. [Alpha Vantage terms, §§2–3](https://www.alphavantage.co/terms_of_service/) · [Alpha Vantage support](https://www.alphavantage.co/support/)

## Scope of a future agreement

Ask the provider for written authorization covering the audience, all three index brands, the exchanges and security types, close and change fields, derived rankings, the delivery of JSON to browsers, static website and CDN caching, repository storage and retention. A 30-session rolling history in the website also persists in earlier Git commits and may be retained by the host or in downloaded copies. Record the retention and deletion terms, attribution, delay, territory, effective dates and fees before selecting that storage model. Keep the agreement and credentials outside the public site.

For individual use, the existing synthetic dashboard can run locally on the owner's computer. If a provider authorizes individual calculation and local snapshots, use a local, unsynchronized directory, bind the site to loopback, and keep that data out of Git, cloud backups and the hosted output. A synchronized OneDrive project directory is suitable for the demonstration only unless the provider permits that storage. A hosted phone-accessible private dashboard requires the provider to authorize hosting and its access model.

If rights cover only some datasets, publish only the authorized outputs after validating their session and universe. A license to an index series does not establish equity ranking coverage. The current provider evaluation records the separate technical findings. [Market data evaluation](API_EVALUATION.md)
