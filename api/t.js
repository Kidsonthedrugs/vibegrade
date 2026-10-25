// /t/:addr — serves the app shell with per-token Open Graph tags.
// Crawlers do not run JS, so the meta has to be right in the HTML we return.
// We fetch our own index.html at runtime so the shell can never drift from the site.

const ORIGIN = "https://vibegrade-eta.vercel.app";
const API = "https://testnet.vibevibe.fun/api/v1/chains/46630";
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0 Safari/537.36";

const esc = (s) =>
  String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

async function getJSON(url) {
  const res = await fetch(url, {
    headers: { "user-agent": UA, accept: "application/json", origin: "https://testnet.vibevibe.fun" },
  });
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json();
}

export default async function handler(req, res) {
  const addr = String(req.query.addr || "").toLowerCase();
  const ok = /^0x[0-9a-f]{40}$/.test(addr);

  let title = "VibeGrade · graduation radar for vibe/vibe";
  let desc = "Exact distance to graduation for every live vibe/vibe launch — computed from the bonding curve.";

  if (ok) {
    try {
      const data = await getJSON(`${API}/v6/launches/${addr}`);
      const l = data?.data?.launch;
      if (l) {
        const supply = 1e9;
        const target = Number(l.targetPairUnits || 0) / 1e18;
        const principal = Number(l.curve?.pairReserveUnits || 0) / 1e18;
        const sold = Number(l.curve?.tokensSoldGrossUnits || 0) / 1e18;
        const prog = target > 0 ? Math.min(100, (principal / target) * 100) : 0;
        const left = Math.max(0, target - principal);
        const pair = l.pairIsNative ? "ETH" : l.pairSymbol || "pair";
        const holders = l.market?.holderCount ?? l.holderCount ?? null;
        title = `${l.symbol} · ${prog.toFixed(1)}% to graduation · VibeGrade`;
        desc =
          `${l.name || l.symbol} — ${left.toFixed(left < 1 ? 4 : 2)} ${pair} left on the curve, ` +
          `${(sold / 1e6).toFixed(1)}M of 800M sold, ${prog.toFixed(1)}% to graduation` +
          (holders ? `, ${holders} holders.` : ".");
      }
    } catch {
      /* keep the generic tags */
    }
  }

  let html;
  try {
    const shell = await fetch(`${ORIGIN}/index.html`, { headers: { "user-agent": "vibegrade-og" } });
    html = await shell.text();
  } catch {
    html = "<!doctype html><html><head><meta charset=utf-8></head><body><div id=app></div></body></html>";
  }

  const meta = `
    <title>${esc(title)}</title>
    <meta name="description" content="${esc(desc)}" />
    <meta property="og:type" content="website" />
    <meta property="og:title" content="${esc(title)}" />
    <meta property="og:description" content="${esc(desc)}" />
    <meta property="og:url" content="${ORIGIN}/t/${addr}" />
    <meta property="og:image" content="${ORIGIN}/og.png" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="${esc(title)}" />
    <meta name="twitter:description" content="${esc(desc)}" />
    <meta name="twitter:image" content="${ORIGIN}/og.png" />`;

  // replace the shell's own head tags with ours
  html = html
    .replace(/<title>[\s\S]*?<\/title>/, "")
    .replace(/<meta name="description"[^>]*>/, "")
    .replace(/<meta property="og:[^>]*>/g, "")
    .replace(/<meta name="twitter:[^>]*>/g, "")
    .replace("</head>", `${meta}\n  </head>`);

  res.setHeader("content-type", "text/html; charset=utf-8");
  res.setHeader("cache-control", "public, max-age=60, s-maxage=300");
  res.status(200).send(html);
}
