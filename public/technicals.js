"use strict";

const form = document.querySelector("#rating-form");
const input = document.querySelector("#rating-symbol");
const host = document.querySelector("#rating-widget");
const providerLink = document.querySelector("#rating-link");
const errorMessage = document.querySelector("#rating-error");
const benchmarks = new Map([["SPY", "AMEX:SPY"], ["QQQ", "NASDAQ:QQQ"]]);

function renderRating(symbol) {
  const [exchange, ticker] = symbol.split(":");
  document.querySelector("#rated-symbol").textContent = symbol;
  input.value = symbol;
  errorMessage.hidden = true;
  providerLink.href = "https://www.tradingview.com/symbols/" + exchange + "-" + ticker + "/technicals/";
  providerLink.textContent = "View " + ticker + " technicals on TradingView";

  const container = document.createElement("div");
  container.className = "tradingview-widget-container";
  const mount = document.createElement("div");
  mount.className = "tradingview-widget-container__widget";
  const credit = document.createElement("div");
  credit.className = "tradingview-widget-copyright";
  const link = providerLink.cloneNode(false);
  link.removeAttribute("id");
  link.textContent = ticker + " technical analysis";
  credit.append(link, " by TradingView");
  container.append(mount, credit);
  host.replaceChildren(container);

  const script = document.createElement("script");
  script.src = "https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js";
  script.async = true;
  script.textContent = JSON.stringify({
    symbol, interval: "1D", width: "100%", height: 320, displayMode: "single",
    colorTheme: "light", locale: "en", isTransparent: false,
    showIntervalTabs: false, disableInterval: true
  });
  script.addEventListener("error", () => {
    if (host.contains(container)) errorMessage.hidden = false;
  });
  container.append(script);
}

input.addEventListener("input", () => input.setCustomValidity(""));
form.addEventListener("submit", event => {
  event.preventDefault();
  const value = input.value.trim().toUpperCase();
  const symbol = benchmarks.get(value) || value;
  if (!/^(AMEX|NASDAQ|NYSE|NYSEARCA|ARCA|BATS|CBOE):[A-Z][A-Z0-9.\-]{0,14}$/.test(symbol)) {
    input.setCustomValidity("Enter SPY, QQQ or a U.S. exchange and ticker such as NYSE:IBM.");
    input.reportValidity();
    return;
  }
  renderRating(symbol);
});

renderRating(input.defaultValue);
