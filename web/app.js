import { board, launchWithMarket, candles, ethUsd, normalise, mediaUrl, shortAddr, walletTokens } from "/core/api.js";
import { pairToGraduation, progressBps, fmtEth, fmtTokens, spotPrice, virtualPair, virtualToken } from "/core/curve.js";
import { scoreLaunch, SCORE_WEIGHTS } from "/core/score.js";

const $ = (s) => document.querySelector(s);
const WAD = 10n ** 18n;

const state = { eth: null, tab: "radar", loading: false };

function eta(row) {
  const vol = BigInt(row.market?.volume24hPairUnits || 0);
  if (vol <= 0n) return "—";
  const perMin = Number(vol / WAD) / 1440;
  const need = Number(pairToGraduation(row)) / 1e18;
  if (perMin <= 0) return "—";
  const m = need / perMin;
  if (m < 1) return "<1m";
  if (m < 60) return `${Math.round(m)}m`;
  if (m < 6000) return `${Math.round(m / 60)}h`;
  return ">4d";
}

const pairLabels = new Map();
function pairLabel(row) {
  const sym = row.pairSymbol;
  if (sym) {
    if (row.pairCurrencyAddress) pairLabels.set(String(row.pairCurrencyAddress).toLowerCase(), sym);
    return sym;
  }
  const known = row.pairCurrencyAddress && pairLabels.get(String(row.pairCurrencyAddress).toLowerCase());
  return known || shortAddr(row.pairCurrencyAddress);
}

function toGradText(row) {
  const v = pairToGraduation(row);
  return row.pairIsNative ? `${fmtEth(v, 4)} ETH` : `${fmtTokens(v)} ${pairLabel(row).slice(0, 6)}`;
}

function art(row, cls = "") {
  const url = mediaUrl(row.image, "sq544.webp");
  if (!url) return `<div class="art"><div class="fallback">${(row.symbol || "?").slice(0, 2)}</div></div>`;
  return `<div class="art"><img loading="lazy" src="${url}" alt="" onerror="this.style.display='none';this.parentNode.querySelector('.fallback')?.removeAttribute('hidden')"/><div class="fallback" hidden>${(row.symbol || "?").slice(0, 2)}</div></div>`;
}

function renderRadar(rows) {
  const list = $("#radar-list");
  if (!rows.length) {
    list.innerHTML = `<div class="status">no launches in range right now</div>`;
    return;
  }
  list.innerHTML = rows
    .map((r, i) => {
      const p = progressBps(r) / 100;
      return `<a class="row" href="#token/${r.token}">
        <div class="rank">${String(i + 1).padStart(2, "0")}</div>
        <div class="tok">
          ${mediaUrl(r.image, "sq410.webp") ? `<img loading="lazy" src="${mediaUrl(r.image, "sq410.webp")}" alt=""/>` : ""}
          <div style="min-width:0">
            <div class="sym">${r.symbol}</div>
            <div class="nm">${r.name || ""}</div>
          </div>
        </div>
        <div class="pair">${pairLabel(r).slice(0, 6)}</div>
        <div class="bar" title="${p.toFixed(2)}%"><i style="width:${Math.min(p, 100).toFixed(2)}%"></i></div>
        <div class="num">${toGradText(r)}</div>
        <div class="num muted eta">${eta(r)}</div>
        <span class="star ${isWatched(r.token) ? "on" : ""}" data-star="${r.token}">${isWatched(r.token) ? "★" : "☆"}</span>
      </a>`;
    })
    .join("");
}

function renderCards(target, rows, kind) {
  const el = $(target);
  if (!rows.length) {
    el.innerHTML = `<div class="status">nothing here yet</div>`;
    return;
  }
  el.innerHTML = rows
    .map((r) => {
      const grad = r.graduation || {};
      const badge =
        r.kind !== "v6"
          ? `<span class="badge" style="background:var(--card-2);color:var(--muted)">v5</span>`
          : kind === "graduated"
            ? `<span class="badge">graduated</span>`
            : `<span class="badge" style="background:var(--card-2);color:var(--accent)">${progressBps(r) / 100 | 0}%</span>`;
      const stat2 =
        r.kind !== "v6"
          ? `<span>legacy curve</span>`
          : kind === "graduated"
          ? `<span><b>${fmtEth(BigInt(grad.pairUnits || 0), 2)}</b> raised</span>`
          : `<span><b>${toGradText(r)}</b> to go</span>`;
      return `<a class="card" href="#token/${r.token}">
        ${art(r)}
        <div class="body">
          <div class="title"><b>${r.symbol}</b>${badge}</div>
          <div class="sub">${r.name || ""}</div>
          <div class="stats">
            ${stat2}
            <span><b>${(r.market?.holderCount ?? 0).toLocaleString()}</b> holders</span>
          </div>
        </div>
      </a>`;
    })
    .join("");
}

async function loadRadar() {
  const items = await board("FINAL_STRETCH");
  const rows = items
    .map(normalise)
    .filter((r) => r.kind === "v6" && r.token && r.symbol && r.target > 0n && !r.graduated);
  rows.forEach((r) => (r._toGrad = pairToGraduation(r)));
  rows.sort((a, b) => (a._toGrad < b._toGrad ? -1 : a._toGrad > b._toGrad ? 1 : 0));
  renderRadar(rows.slice(0, 12));
  return rows.length;
}

async function loadTab(tab) {
  if (tab === "graduated") {
    const rows = (await board("GRADUATED")).map(normalise).filter((r) => r.token && r.symbol && r.graduated);
    rows.sort((a, b) => ((b.graduation?.at || "") > (a.graduation?.at || "") ? 1 : -1));
    renderCards("#grad-grid", rows.slice(0, 12), "graduated");
    return rows.length;
  }
  if (tab === "score") {
    return loadScorePanel();
  }
  if (tab === "wallet") {
    return loadWatchPanel();
  }
  if (tab === "trending") {
    const rows = (await board("TRENDING")).map(normalise).filter((r) => r.token && r.symbol);
    renderCards("#trending-grid", rows.slice(0, 12), "trending");
    return rows.length;
  }
  return loadRadar();
}

function showTab(tab, push = true) {
  const panel = document.getElementById(`panel-${tab}`);
  if (!panel) return;
  state.tab = tab;
  document.querySelectorAll(".tab").forEach((b) => b.classList.toggle("active", b.dataset.tab === tab));
  document.querySelectorAll(".panel").forEach((p) => p.classList.add("hidden"));
  panel.classList.remove("hidden");
  if (push && location.hash !== `#${tab}`) history.replaceState(null, "", `#${tab}`);
  if (tab !== "token") refresh();
}

async function refresh() {
  if (state.loading) return;
  state.loading = true;
  const st = $("#status");
  st.className = "status";
  st.textContent = "loading…";
  try {
    const n = await loadTab(state.tab);
    if (["radar", "graduated", "trending", "score"].includes(state.tab)) {
      st.textContent = `${n} launches · updated ${new Date().toLocaleTimeString()}`;
    } else {
      st.textContent = "";
    }
  } catch (e) {
    st.className = "status err";
    st.textContent = `error: ${e.message}`;
  } finally {
    state.loading = false;
  }
}

function colourFor(score) {
  if (score >= 75) return "var(--accent)";
  if (score >= 50) return "var(--warn)";
  return "var(--bad)";
}

function renderScore(r) {
  const s = scoreLaunch(r);
  const rows = Object.entries(SCORE_WEIGHTS)
    .map(([k, w]) => {
      const v = s.breakdown[k] ?? 0;
      const cls = v >= 75 ? "" : v >= 50 ? "warn" : "bad";
      return `<div class="bar-row">
        <div class="lbl">${k} · ${w}%</div>
        <div class="trk"><i style="width:${Math.max(v, 2)}%;background:${v >= 75 ? "var(--accent)" : v >= 50 ? "var(--warn)" : "var(--bad)"}"></i></div>
        <div class="val">${v}</div>
      </div>`;
    })
    .join("");
  const notes = s.notes
    .map((n, i) => `<div class="note ${i === 0 ? "bad" : i === 1 ? "warn" : ""}"><span class="dot"></span><span>${n}</span></div>`)
    .join("");
  return `<div class="score-top">
      <div class="score-num" style="color:${colourFor(s.score)}">${s.score}<small>/100</small></div>
      <div class="score-meta">
        <div class="sym">${r.symbol || "?"}</div>
        <div class="nm">${r.name || ""} · tax ${(Number(r.taxBps) / 100).toFixed(0)}% · ${r.pairSymbol || "?"} pair</div>
        <div class="verdict">${s.verdict}</div>
        <div class="eta">${s.eta}</div>
      </div>
    </div>
    <div class="bars">${rows}</div>
    <div class="notes">${notes}</div>`;
}

async function scoreToken(addr) {
  const out = $("#score-out");
  out.innerHTML = `<div class="status">scoring…</div>`;
  try {
    const r = await launchWithMarket(addr.trim());
    out.innerHTML = renderScore(r);
    history.replaceState(null, "", `?token=${r.token}`);
  } catch (e) {
    out.innerHTML = `<div class="status err">could not load that token: ${e.message}<br/>use a v6 (current generation) token address</div>`;
  }
}

async function loadScorePanel() {
  const q = new URLSearchParams(location.search).get("token");
  if (q) {
    $("#score-addr").value = q;
    await scoreToken(q);
  }
  const items = (await board("FINAL_STRETCH")).map(normalise).filter((r) => r.kind === "v6" && r.token);
  $("#score-suggest").innerHTML = items
    .slice(0, 8)
    .map((r) => `<button data-addr="${r.token}">${r.symbol}</button>`)
    .join("");
  $("#score-suggest").querySelectorAll("button").forEach((b) =>
    b.addEventListener("click", () => {
      $("#score-addr").value = b.dataset.addr;
      scoreToken(b.dataset.addr);
    })
  );
  if (!q && items[0]) {
    $("#score-addr").value = items[0].token;
    await scoreToken(items[0].token);
  }
  return items.length;
}

function niceNum(v) {
  if (!isFinite(v)) return "—";
  const a = Math.abs(v);
  if (a >= 1e-4) return v.toFixed(6).replace(/0+$/, "").replace(/\.$/, "");
  return v.toExponential(2);
}

function chartSVG(items, label) {
  const vals = items.map((i) => {
    const raw = i.closePriceWeiPerToken ?? i.closePriceQuoteBaseUnitsPerToken;
    return raw == null ? null : Number(raw) / 1e18;
  });
  const valid = vals.filter((v) => v != null && isFinite(v) && v > 0);
  if (valid.length < 2) return `<div class="chart-empty">no trades in this window yet</div>`;
  const min = Math.min(...valid);
  const max = Math.max(...valid);
  const W = 1080;
  const H = 260;
  const pad = 10;
  const sx = (i) => pad + (i / Math.max(1, vals.length - 1)) * (W - pad * 2);
  const sy = (v) => (max === min ? H / 2 : H - pad - ((v - min) / (max - min)) * (H - pad * 2));
  let path = "";
  let seg = [];
  vals.forEach((v, i) => {
    if (v == null || !isFinite(v) || v <= 0) {
      if (seg.length) path += `M${seg.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join("L")}`;
      seg = [];
      return;
    }
    seg.push([sx(i), sy(v)]);
  });
  if (seg.length) path += `M${seg.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join("L")}`;
  const first = valid[0];
  const last = valid[valid.length - 1];
  const chg = ((last - first) / first) * 100;
  const up = chg >= 0;
  return `<div class="chart-head">
      <span class="chart-price">${niceNum(last)} <small>${label}/token</small></span>
      <span class="chart-chg" style="color:${up ? "var(--accent)" : "var(--bad)"}">
        ${up ? "+" : ""}${chg.toFixed(1)}% over the window</span>
    </div>
    <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" class="chart">
      <path d="${path}" fill="none" stroke="${up ? "#dff902" : "#ff5c5c"}" stroke-width="2.5"
            stroke-linejoin="round" stroke-linecap="round"/>
    </svg>
    <div class="chart-axis"><span>${niceNum(min)}</span><span>${niceNum(max)}</span></div>`;
}

async function openToken(addr, push = true) {
  const panel = $("#panel-token");
  document.querySelectorAll(".panel").forEach((p) => p.classList.add("hidden"));
  panel.classList.remove("hidden");
  document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
  state.tab = "token";
  if (push) history.replaceState(null, "", `#token/${addr}`);
  panel.innerHTML = `<div class="status">loading token…</div>`;
  try {
    const [r, ks] = await Promise.all([launchWithMarket(addr), candles(addr).catch(() => [])]);
    const sc = scoreLaunch(r);
    const label = pairLabel(r);
    const art = mediaUrl(r.image, "sq544.webp");
    const done = r.graduated || progressBps(r) >= 10000;
    const m = r.market || {};
    const volRaw = BigInt(Math.trunc(Number(m.volume24hPairUnits || 0)));
    panel.innerHTML = `
      <a class="back" href="#radar">← back to radar</a>
      <div class="tok-head">
        <div class="tok-art">${art ? `<img src="${art}" alt=""/>` : (r.symbol || "?").slice(0, 2)}</div>
        <div class="tok-id">
          <h2>${r.symbol}</h2>
          <p>${r.name || ""}</p>
          <div class="chips">
            <span class="chip">${done ? "graduated" : "on the curve"}</span>
            <span class="chip">tax ${(Number(r.taxBps) / 100).toFixed(0)}%</span>
            <span class="chip">${label} pair</span>
            ${r.kind === "v6" ? "" : '<span class="chip warn">legacy v5</span>'}
          </div>
        </div>
      </div>
      <div class="tok-stats">
        <div><b>${done ? "complete" : toGradText(r)}</b><span>${done ? "curve closed" : "to graduation"}</span></div>
        <div><b>${(m.holderCount ?? 0).toLocaleString()}</b><span>holders</span></div>
        <div><b>${fmtTokens(volRaw)}</b><span>24h volume (${label})</span></div>
        <div><b style="color:${sc.score >= 75 ? "var(--accent)" : sc.score >= 50 ? "var(--warn)" : "var(--bad)"}">${sc.score}</b><span>launch score</span></div>
      </div>
      <div class="progress-wrap">
        <div class="progress"><i style="width:${Math.min(100, progressBps(r) / 100)}%"></i></div>
        <span>${(progressBps(r) / 100).toFixed(2)}% of the way to graduation</span>
      </div>
      <div class="chart-box">${chartSVG(ks, label)}</div>
      <button class="watch-btn ${isWatched(r.token) ? "on" : ""}" data-star="${r.token}">
        ${isWatched(r.token) ? "★ watching" : "☆ watch"}
      </button>
      <div class="tok-actions">
        <a class="btn" href="https://testnet.vibevibe.fun/t/${r.token}" target="_blank" rel="noopener">open on vibe/vibe</a>
        <a class="btn ghost" href="https://explorer.testnet.chain.robinhood.com/address/${r.token}" target="_blank" rel="noopener">explorer</a>
        <a class="btn ghost" href="#score">score this config →</a>
        <button class="btn ghost" data-copy="${r.token}">copy share link</button>
      </div>`;
  } catch (e) {
    panel.innerHTML = `<a class="back" href="#radar">← back</a><div class="status err">could not load ${addr}: ${e.message}</div>`;
  }
}

function route() {
  const h = (location.hash || "").replace(/^#/, "");
  if (h.startsWith("token/")) return openToken(h.slice(6), false);
  if (h && document.querySelector(`.tab[data-tab="${h}"]`)) return showTab(h, false);
  return showTab("radar", false);
}

const WATCH_KEY = "vg_watch";
const WALLET_KEY = "vg_wallet";

function watchList() {
  try {
    return JSON.parse(localStorage.getItem(WATCH_KEY) || "[]");
  } catch {
    return [];
  }
}
function isWatched(token) {
  return watchList().some((t) => String(t).toLowerCase() === String(token).toLowerCase());
}
function toggleWatch(token) {
  const t = String(token).toLowerCase();
  const list = watchList();
  const i = list.findIndex((x) => String(x).toLowerCase() === t);
  if (i >= 0) list.splice(i, 1);
  else list.push(t);
  localStorage.setItem(WATCH_KEY, JSON.stringify(list));
  return i < 0;
}

/** value of a holding, priced off the curve itself (exact) when the token is still on it */
function holdingValue(row, amountRaw, decimals) {
  if (!row || row.graduated) return null;
  try {
    const amount = (amountRaw * 10n ** 18n) / 10n ** BigInt(decimals);
    const price = spotPrice(row);
    return { pair: (amount * price) / 10n ** 18n, pairSymbol: pairLabel(row) };
  } catch {
    return null;
  }
}

function positionRow(row, amountRaw, decimals) {
  const prog = progressBps(row);
  const val = holdingValue(row, amountRaw, decimals);
  const amount = Number(amountRaw) / 10 ** decimals;
  return `<a class="row wallet-row" href="#token/${row.token}">
      <div class="rank">${row.graduated ? "✓" : (prog / 100).toFixed(0) + "%"}</div>
      <div class="tok">
        ${mediaUrl(row.image, "sq410.webp") ? `<img loading="lazy" src="${mediaUrl(row.image, "sq410.webp")}" alt=""/>` : ""}
        <div style="min-width:0">
          <div class="sym">${row.symbol}</div>
          <div class="nm">${fmtTokens(BigInt(Math.trunc(amount * 1e6)) * 10n ** 12n)} tokens</div>
        </div>
      </div>
      <div class="pair">${pairLabel(row).slice(0, 6)}</div>
      <div class="bar"><i style="width:${Math.min(100, prog / 100).toFixed(1)}%"></i></div>
      <div class="num">${row.graduated ? "graduated" : toGradText(row)}</div>
      <div class="num muted eta">${val ? fmtTokens(val.pair) + " " + val.pairSymbol.slice(0, 6) : "—"}</div>
    </a>`;
}

async function loadWatchPanel() {
  const q = new URLSearchParams(location.search).get("wallet");
  if (q) localStorage.setItem(WALLET_KEY, q);
  const saved = localStorage.getItem(WALLET_KEY);
  if (saved) $("#wallet-addr").value = saved;
  await renderWatchList();
  if (saved) await loadWallet(saved);
  return watchList().length;
}

async function renderWatchList() {
  const list = watchList();
  const out = $("#watch-out");
  if (!list.length) {
    out.innerHTML = `<div class="status">nothing watched yet — hit ☆ on any launch to follow it</div>`;
    return;
  }
  const rows = [];
  for (const tab of ["FINAL_STRETCH", "TRENDING", "NEW", "GRADUATED"]) {
    try {
      for (const r of (await board(tab)).map(normalise)) {
        if (r.kind === "v6" && list.includes(String(r.token).toLowerCase())) rows.push(r);
      }
    } catch {}
  }
  const seen = new Set();
  const uniq = rows.filter((r) => (seen.has(r.token) ? false : seen.add(r.token)));
  uniq.sort((a, b) => progressBps(b) - progressBps(a));
  out.innerHTML = uniq
    .map(
      (r) => `<a class="row" href="#token/${r.token}">
        <div class="rank">${String(progressBps(r) / 100 | 0).padStart(3, " ")}%</div>
        <div class="tok"><div style="min-width:0">
          <div class="sym">${r.symbol}</div><div class="nm">${r.name || ""}</div></div></div>
        <div class="pair">${pairLabel(r).slice(0, 6)}</div>
        <div class="bar"><i style="width:${Math.min(100, progressBps(r) / 100).toFixed(1)}%"></i></div>
        <div class="num">${r.graduated ? "graduated" : toGradText(r)}</div>
        <div class="num muted eta">${eta(r)}</div>
      </a>`
    )
    .join("");
}

async function loadWallet(addr) {
  const a = String(addr || "").trim();
  const out = $("#wallet-out");
  if (!/^0x[0-9a-fA-F]{40}$/.test(a)) {
    out.innerHTML = `<div class="status err">that is not a wallet address</div>`;
    return;
  }
  localStorage.setItem(WALLET_KEY, a);
  out.innerHTML = `<div class="status">reading balances from the explorer…</div>`;
  try {
    const [balances, ...tabs] = await Promise.all([
      walletTokens(a),
      ...["FINAL_STRETCH", "TRENDING", "NEW", "GRADUATED", "MOVERS"].map((t) => board(t).catch(() => [])),
    ]);
    const index = new Map();
    for (const tab of tabs) {
      for (const r of tab.map(normalise)) {
        if (r.kind === "v6" && r.token && !index.has(r.token)) index.set(r.token.toLowerCase(), r);
      }
    }
    const mine = balances
      .map((b) => ({ b, row: index.get(b.token) }))
      .filter((x) => x.row);
    if (!mine.length) {
      out.innerHTML = `<div class="status">no vibe/vibe launches in this wallet (checked ${balances.length} tokens on chain)</div>`;
      return;
    }
    mine.sort((x, y) => progressBps(y.row) - progressBps(x.row));
    out.innerHTML =
      `<div class="status">${mine.length} vibe/vibe holding(s) · ${shortAddr(a)}</div>` +
      `<div class="row wallet-row legend">
         <div class="rank">%</div><div class="tok">TOKEN</div><div class="pair">PAIR</div>
         <div class="bar"></div><div class="num">TO GRADUATION</div>
         <div class="num muted eta">VALUE AT CURVE PRICE</div><span></span>
       </div>` +
      mine.map((x) => positionRow(x.row, BigInt(x.b.raw), x.b.decimals)).join("");
  } catch (e) {
    out.innerHTML = `<div class="status err">could not read that wallet: ${e.message}</div>`;
  }
}

async function boot() {
  document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => showTab(b.dataset.tab)));
  window.addEventListener("hashchange", route);
  document.addEventListener("click", (e) => {
    const cp = e.target.closest("[data-copy]");
    if (cp) {
      const url = `${location.origin}/t/${cp.dataset.copy}`;
      navigator.clipboard?.writeText(url);
      cp.textContent = "copied ✓";
      setTimeout(() => (cp.textContent = "copy share link"), 1600);
      return;
    }
    const el = e.target.closest("[data-star]");
    if (!el) return;
    e.preventDefault();
    e.stopPropagation();
    const on = toggleWatch(el.dataset.star);
    el.textContent = on ? "★" : "☆";
    el.classList.toggle("on", on);
    if (state.tab === "wallet") renderWatchList();
  });
  $("#refresh").addEventListener("click", refresh);
  $("#score-go").addEventListener("click", () => scoreToken($("#score-addr").value));
  $("#wallet-go").addEventListener("click", () => loadWallet($("#wallet-addr").value));
  $("#wallet-addr").addEventListener("keydown", (e) => {
    if (e.key === "Enter") loadWallet($("#wallet-addr").value);
  });
  $("#score-addr").addEventListener("keydown", (e) => {
    if (e.key === "Enter") scoreToken($("#score-addr").value);
  });
  try {
    state.eth = await ethUsd();
    $("#eth").textContent = `ETH $${state.eth.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
  } catch {
    $("#eth").textContent = "ETH —";
  }
  const tick = () => ($("#clock").textContent = new Date().toUTCString().slice(17, 25) + " utc");
  tick();
  setInterval(tick, 1000);
  const pathToken = (location.pathname.match(/^\/t\/(0x[0-9a-fA-F]{40})/) || [])[1];
  if (pathToken) {
    await openToken(pathToken, false);
    setInterval(refresh, 60_000);
    return;
  }
  const wantTab = new URLSearchParams(location.search).get("tab");
  if (wantTab && document.querySelector(`.tab[data-tab="${wantTab}"]`)) showTab(wantTab, false);
  else if (location.hash) route();
  else await refresh();
  setInterval(refresh, 30_000);
}

boot();
