import { board, launchWithMarket, ethUsd, normalise, mediaUrl } from "/core/api.js";
import { pairToGraduation, progressBps, fmtEth, fmtTokens } from "/core/curve.js";
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

function toGradText(row) {
  const v = pairToGraduation(row);
  return row.pairIsNative ? `${fmtEth(v, 4)} ETH` : `${fmtTokens(v)} ${(row.pairSymbol || "?").slice(0, 5)}`;
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
      return `<div class="row">
        <div class="rank">${String(i + 1).padStart(2, "0")}</div>
        <div class="tok">
          ${mediaUrl(r.image, "sq410.webp") ? `<img loading="lazy" src="${mediaUrl(r.image, "sq410.webp")}" alt=""/>` : ""}
          <div style="min-width:0">
            <div class="sym">${r.symbol}</div>
            <div class="nm">${r.name || ""}</div>
          </div>
        </div>
        <div class="pair">${(r.pairSymbol || "?").slice(0, 6)}</div>
        <div class="bar" title="${p.toFixed(2)}%"><i style="width:${Math.min(p, 100).toFixed(2)}%"></i></div>
        <div class="num">${toGradText(r)}</div>
        <div class="num muted eta">${eta(r)}</div>
      </div>`;
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
      return `<a class="card" href="https://testnet.vibevibe.fun/t/${r.token}" target="_blank" rel="noopener">
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
  if (tab === "trending") {
    const rows = (await board("TRENDING")).map(normalise).filter((r) => r.token && r.symbol);
    renderCards("#trending-grid", rows.slice(0, 12), "trending");
    return rows.length;
  }
  return loadRadar();
}

function showTab(tab) {
  state.tab = tab;
  document.querySelectorAll(".tab").forEach((b) => b.classList.toggle("active", b.dataset.tab === tab));
  document.querySelectorAll(".panel").forEach((p) => p.classList.add("hidden"));
  $(`#panel-${tab}`).classList.remove("hidden");
  refresh();
}

async function refresh() {
  if (state.loading) return;
  state.loading = true;
  const st = $("#status");
  st.className = "status";
  st.textContent = "loading…";
  try {
    const n = await loadTab(state.tab);
    st.textContent = `${n} launches · updated ${new Date().toLocaleTimeString()}`;
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

async function boot() {
  document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => showTab(b.dataset.tab)));
  $("#refresh").addEventListener("click", refresh);
  $("#score-go").addEventListener("click", () => scoreToken($("#score-addr").value));
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
  const wantTab = new URLSearchParams(location.search).get("tab");
  if (wantTab && document.querySelector(`.tab[data-tab="${wantTab}"]`)) {
    showTab(wantTab);
  } else {
    await refresh();
  }
  setInterval(refresh, 30_000);
}

boot();
