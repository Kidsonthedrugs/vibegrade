// Zero-dependency static server + API/media proxy for local preview.
//   node scripts/serve.mjs [port]
// /api/* and /media/* are tunneled to the vibe/vibe app through Nekoray (127.0.0.1:2081)
// so the browser sees a same-origin API (no CORS, no country blocking).
import { createServer } from "node:http";
import { request as httpsRequest } from "node:https";
import { readFile } from "node:fs/promises";
import { extname, join, normalize } from "node:path";

const ROOT = process.cwd();
const PORT = Number(process.argv[2] || 4173);
const UPSTREAM = "testnet.vibevibe.fun";

const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".webp": "image/webp",
  ".svg": "image/svg+xml",
};

function fetchUpstream(req, res, path) {
  // Verified reachable directly from this host (HTTP 200). In production the same
  // paths are rewritten by vercel.json, so neither CORS nor the local network matters.
  const up = httpsRequest(
    {
      host: UPSTREAM,
      port: 443,
      path,
      method: req.method,
      headers: {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0 Safari/537.36",
        accept: req.headers.accept || "*/*",
        origin: `https://${UPSTREAM}`,
        referer: `https://${UPSTREAM}/`,
      },
    },
    (ur) => {
      res.writeHead(ur.statusCode || 502, {
        "content-type": ur.headers["content-type"] || "application/octet-stream",
        "cache-control": "public, max-age=30",
      });
      ur.pipe(res);
    }
  );
  up.on("error", () => {
    if (!res.headersSent) res.writeHead(502, { "content-type": "text/plain" });
    res.end("upstream error");
  });
  up.end();
}


createServer(async (req, res) => {
  try {
    const url = new URL(req.url, "http://localhost");
    const clean = decodeURIComponent(url.pathname);
    const full = clean + (url.search || "");
    if (full.startsWith("/api/") || full.startsWith("/media/")) {
      fetchUpstream(req, res, full);
      return;
    }
    let path = clean;
    if (path === "/" || path === "") path = "/index.html";
    const file = normalize(join(ROOT, path));
    if (!file.startsWith(ROOT)) {
      res.writeHead(403).end("forbidden");
      return;
    }
    const body = await readFile(file);
    res.writeHead(200, { "content-type": TYPES[extname(file)] || "application/octet-stream" });
    res.end(body);
  } catch {
    res.writeHead(404, { "content-type": "text/plain" }).end("not found");
  }
}).listen(PORT, () => console.log(`serving ${ROOT} on http://127.0.0.1:${PORT}`));
