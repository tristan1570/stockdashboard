"use strict";
const $ = (selector) => document.querySelector(selector);
const el = (tag, text, cls) => {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (cls) node.className = cls;
  return node;
};
const ns = "http://www.w3.org/2000/svg";
function svg(tag, attrs) {
  const node = document.createElementNS(ns, tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  return node;
}
const num = (n, digits = 2) => n.toLocaleString("en-US", {minimumFractionDigits: digits, maximumFractionDigits: digits});
const money = (n) => "$" + num(n, n > 0 && n < 1 ? 4 : 2);
const signed = (n, suffix = "") => (n < 0 ? "−" : n > 0 ? "+" : "") + num(Math.abs(n)) + suffix;
const cap = (n) => n === null ? "Unavailable" : "$" + num(n / 1e9, 2) + "B";
const datePattern = /^\d{4}-\d{2}-\d{2}$/;
const fullDate = (d, opts = {weekday:"long", month:"long", day:"numeric", year:"numeric"}) =>
  new Intl.DateTimeFormat("en-US", {...opts, timeZone:"UTC"}).format(new Date(d + "T12:00:00Z"));
const easternTime = (stamp) => new Intl.DateTimeFormat("en-US", {timeZone:"America/New_York", hour:"numeric", minute:"2-digit", timeZoneName:"short"}).format(new Date(stamp));
const easternDay = (stamp) => new Intl.DateTimeFormat("sv-SE", {timeZone:"America/New_York", year:"numeric", month:"2-digit", day:"2-digit"}).format(stamp);
let report, latest, dates, status, group = "overall", side = "gainers", sequence = 0, pendingDate = "";
let auxiliaryWarning = "";

async function read(file) {
  const res = await fetch("./data/" + file, {cache:"no-store"});
  if (!res.ok) throw Error("Snapshot request failed");
  return res.json();
}
function acceptable(s, requested) {
  if (!s || s.is_demo !== true || s.provider !== "Market Daily simulation" || s.license_status !== "synthetic_only"
      || s.schema_version !== 1 || s.data_status !== "valid" || s.rankings_complete !== false
      || !datePattern.test(s.session_date) || (requested && requested !== s.session_date)
      || s.coverage?.overall_complete !== false || s.coverage?.largecap_complete !== false
      || !Number.isFinite(Date.parse(s.updated_at_utc)) || !Number.isFinite(Date.parse(s.next_update_due_utc))
      || !Number.isFinite(Date.parse(s.session_close_utc))) throw Error("Invalid snapshot");
  if (!Array.isArray(s.indices) || s.indices.length !== 3 || !["^GSPC","^IXIC","^DJI"].every(symbol => s.indices.some(i => i.symbol === symbol))
      || !s.indices.every(i => i.session_date === s.session_date && Number.isFinite(i.change_pct) && i.close > 0
        && Array.isArray(i.series) && i.series.length >= 2 && i.series.every(p => Number.isFinite(p.close) && datePattern.test(p.date))
        && i.series.at(-1).date === s.session_date && i.series.at(-1).close === i.close)) throw Error("Invalid index data");
  for (const universe of ["overall","largecap"]) for (const dir of ["gainers","losers"]) {
    const rows = s.rankings?.[universe + "_" + dir];
    if (!Array.isArray(rows) || rows.length > 10 || !rows.every(r => r.session_date === s.session_date
        && typeof r.symbol === "string" && typeof r.name === "string" && Number.isFinite(r.close_usd) && r.close_usd > 0
        && Number.isFinite(r.change_usd) && Number.isFinite(r.change_pct) && (dir === "gainers" ? r.change_pct > 0 : r.change_pct < 0)
        && (universe !== "largecap" || r.market_cap_usd >= 1e10))) throw Error("Invalid ranking data");
  }
  if (!["advancing","declining","unchanged"].every(k => Number.isInteger(s.breadth?.[k]) && s.breadth[k] >= 0)) throw Error("Invalid breadth");
  return s;
}
function notice(text = "", retry = false) {
  $("#notice").hidden = !text;
  $("#message").textContent = text;
  $("#retry").hidden = !retry;
}
function statusNotice() {
  const today = easternDay(new Date());
  const notes = [];
  if (status?.state === "failed" && status.session_date >= latest.session_date)
    notes.push("Update failed for " + fullDate(status.session_date, {month:"short", day:"numeric"}) + ". The last validated session is retained.");
  if (report.session_date !== latest.session_date) notes.push("Viewing an archived demo session.");
  else if (Date.now() > Date.parse(report.next_update_due_utc)) notes.push("Stale data. The next scheduled session update is overdue.");
  else if (today > report.session_date && today < report.next_session) notes.push("No trading session today. Showing the previous close.");
  if (auxiliaryWarning) notes.push(auxiliaryWarning);
  notice(notes.join(" "), Boolean(auxiliaryWarning));
}
function chart(points, positive) {
  const color = positive ? "#26846d" : "#b75b70";
  const root = svg("svg", {viewBox:"0 0 320 50", preserveAspectRatio:"none", class:"chart", "aria-hidden":"true"});
  const prices = points.map(p => p.close), min = Math.min(...prices), max = Math.max(...prices);
  const xy = prices.map((p, i) => [4 + i * 312 / (prices.length - 1), max === min ? 24 : 43 - 36 * (p-min)/(max-min)]);
  const path = xy.map(([x,y],i) => (i ? "L" : "M") + x.toFixed(2) + "," + y.toFixed(2)).join(" ");
  root.append(svg("path", {d:path+" L316,50 L4,50 Z", fill:color, opacity:".09"}),
    svg("path", {d:path, fill:"none", stroke:color, "stroke-width":"1.8", "stroke-linejoin":"round", "vector-effect":"non-scaling-stroke"}),
    svg("circle", {cx:xy.at(-1)[0], cy:xy.at(-1)[1], r:"2.7", fill:color}));
  return root;
}
function renderIndices() {
  $("#indices").replaceChildren(...report.indices.map(i => {
    const article = el("article", undefined, "index");
    const head = el("div", undefined, "index-head");
    head.append(el("h3", i.name), el("span", i.symbol, "ticker"));
    const value = el("div", undefined, "index-value");
    value.append(el("strong", num(i.close)), el("small", signed(i.change_pct,"%"), i.change_pct < 0 ? "neg":"pos"));
    const range = el("div", undefined, "chart-label");
    const label = fullDate(i.series[0].date, {month:"short",day:"numeric"}) + " – " + fullDate(i.session_date,{month:"short",day:"numeric"});
    range.append(el("span", label));
    range.title = i.series.length + " simulated closing values";
    article.append(head, value, chart(i.series, i.change_pct >= 0), range);
    return article;
  }));
}
function renderTable() {
  for (const btn of document.querySelectorAll("[data-group]")) btn.setAttribute("aria-pressed", String(btn.dataset.group === group));
  for (const btn of document.querySelectorAll("[data-side]")) btn.setAttribute("aria-pressed", String(btn.dataset.side === side));
  if (!report) return;
  const rows = report.rankings[group + "_" + side];
  const large = group === "largecap";
  $("#caption").textContent = (large ? "Large-cap" : "Overall") + " demo " + side + " for " + report.session_date;
  $("#row-count").textContent = rows.length + " of " + report.coverage[large ? "largecap_count" : "eligible_count"] + " equities";
  $("th.cap-col").hidden = !large;
  $("#empty").hidden = rows.length > 0;
  $("#empty").textContent = "No qualifying " + side + " in this demo session.";
  $("#table-foot").textContent = large ? "Companies with a verified demo market cap of at least $10 billion." : "Ranked by regular-session close-to-close percentage change.";
  const body = $("tbody");
  body.replaceChildren();
  rows.forEach((r,index) => {
    const row = el("tr"), company = el("td"), listing = el("div", undefined, "listing");
    const toggle = el("button", r.symbol);
    toggle.setAttribute("aria-label", "Details for " + r.symbol);
    toggle.setAttribute("aria-expanded", "false");
    const id = "detail-" + index;
    toggle.setAttribute("aria-controls", id);
    listing.append(toggle, el("span", r.name, "company"));
    company.append(listing);
    const pct = el("td", undefined, "numeric");
    pct.append(el("span", signed(r.change_pct,"%"), "pct " + (r.change_pct > 0 ? "pos" : "neg")));
    row.append(el("td",index+1,"rank"), company, el("td",money(r.close_usd),"numeric"),
      el("td",signed(r.change_usd),"numeric change-col"), pct);
    if (large) row.append(el("td",cap(r.market_cap_usd),"numeric cap-col"));
    const info = el("tr", undefined, "row-info");
    info.id = id; info.hidden = true;
    const volume = r.volume == null ? "Unavailable" : num(r.volume,0);
    const cell = el("td", r.exchange + " · Volume " + volume + " · Previous close " + money(r.previous_close_usd)
      + " · Daily change " + signed(r.change_usd) + " USD · Market cap " + cap(r.market_cap_usd));
    cell.colSpan = large ? 6 : 5;
    info.append(cell); body.append(row,info);
    toggle.addEventListener("click", () => { info.hidden = !info.hidden; toggle.setAttribute("aria-expanded", String(!info.hidden)); });
  });
}
function render() {
  $("#session-meta").textContent = fullDate(report.session_date) + "  ·  Updated " + easternTime(report.updated_at_utc);
  $("#market-status").textContent = "Closed for session";
  $("#closing-time").textContent = easternTime(report.session_close_utc);
  renderIndices(); renderTable();
  $("#breadth-total").textContent = report.coverage.eligible_count;
  const bar = $("#breadth-bar"); bar.replaceChildren();
  for (const [key, cls] of [["advancing","up-dot"],["declining","down-dot"],["unchanged","flat-dot"]]) {
    const n = report.breadth[key]; $("#" + key).textContent = n;
    if (n) { const seg = el("span", undefined, cls); seg.style.flex = String(n); bar.append(seg); }
  }
  statusNotice();
}
async function load(day = "") {
  const seq = ++sequence;
  pendingDate = day;
  notice("Loading session…");
  try {
    let chosen;
    if (!day) {
      const result = await Promise.allSettled([read("latest.json"), read("sessions.json"), read("status.json")]);
      if (seq !== sequence) return;
      if (result[0].status !== "fulfilled") throw Error("Latest unavailable");
      chosen = acceptable(result[0].value);
      const archive = result[1].value;
      const archiveOK = Array.isArray(archive) && archive[0] === chosen.session_date && archive.every(d => datePattern.test(d));
      dates = archiveOK ? archive : [chosen.session_date];
      status = result[2].value;
      auxiliaryWarning = [archiveOK ? "" : "Session history is unavailable.", ["ok","failed"].includes(status?.state) ? "" : "Update status is unavailable."].filter(Boolean).join(" ");
      latest = chosen;
      $("#history").replaceChildren(...dates.map(d => { const opt = el("option",fullDate(d,{month:"short",day:"numeric",year:"numeric"})); opt.value = d; return opt; }));
    } else {
      if (!dates.includes(day)) throw Error("Unknown date");
      chosen = day === latest.session_date ? latest : acceptable(await read("history/" + day + ".json"), day);
    }
    if (seq !== sequence) return;
    report = chosen;
    $("#history").value = report.session_date; $("#history").disabled = false;
    render();
  } catch {
    if (seq !== sequence) return;
    if (report) $("#history").value = report.session_date;
    else { $("#session-meta").textContent = "Session unavailable"; $("#indices").replaceChildren(); }
    notice(report ? "Could not load the requested session. Still showing " + report.session_date + "." : "The session could not be loaded. Check your connection and retry.", true);
  }
}
document.querySelectorAll("[data-group]").forEach(btn => btn.addEventListener("click", () => { group = btn.dataset.group; renderTable(); }));
document.querySelectorAll("[data-side]").forEach(btn => btn.addEventListener("click", () => { side = btn.dataset.side; renderTable(); }));
$("#history").addEventListener("change", e => load(e.target.value));
$("#retry").addEventListener("click", () => load(auxiliaryWarning ? "" : pendingDate));
load();
