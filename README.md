# VibeGrade

Graduation radar + launch scoring for **vibe/vibe** on Robinhood Chain Testnet.

Unofficial community tool. No affiliation with vibe/vibe, Seedify or Robinhood.

## What it does

1. **Radar** — every live launch, ranked by the exact pair amount needed to complete
   its bonding curve. The numbers come from the curve, not from volume guesses.
2. **Graduated** — a feed of completed curves, each with time-to-graduation, holders
   and volume.
3. **Token page** — price chart from 15m candles, exact progress, holder and volume stats.
4. **Launch score** — a 0–100 score with six published components and three concrete fixes.
5. **How it works** — the full curve math, so anyone can check the numbers.
6. **Telegram** — `@VibeGraduation` posts a card for every new graduation, plus a weekly report.

## The math (reverse-engineered, verified to the wei)

vibe/vibe V6 curves are constant-product on virtual reserves:

```
VT0 = 800M × 4/3       virtual token reserve
V0  = target / 3       virtual pair reserve (target = 4 ETH for ETH pairs)
k   = VT0 × V0

buy : netIn = amountIn × 10000 / (10000 + taxBps)          ← fee on top
      tokensOut = (VT0 − sold) − k / (V0 + pairPrincipal + netIn)

sell: proceeds = (V0 + pairPrincipal) × tokens / ((VT0 − sold) + tokens)
      net      = proceeds − proceeds × taxBps / 10000      ← fee off proceeds
```

At graduation `pairPrincipal = target`, so `sold = 800,000,000` exactly and the curve
price equals the Uniswap v4 pool's opening price (2e-8 ETH/token) — **no price gap**.

Verified against on-chain `quoteBuyExactIn` / `quoteSell` on curve
`0xb3bc6746dc4119b19f5887be42d4905c425b423b`: token amounts agree to ~1e-16 relative
error, sells to 1 wei of rounding.

## Layout

```
core/curve.js     shared curve math (browser)
core/api.js       vibe/vibe API client
web/              static site (no build step)
bot/curve.py      same math for the bot
bot/api.py        proxy-aware API client (Nekoray 2081)
bot/cards.py      Pillow card renderer (graduation / score / radar)
bot/telegram.py   channel poster
bot/watch.py      graduation watcher + state
scripts/          local server, mimo(codegen), demos
test/             parity tests against real chain quotes
```

## Run locally

```bash
node scripts/serve.mjs 4173          # site  → http://127.0.0.1:4173
python -m bot.radar                  # CLI radar
python -m bot.watch --no-post        # dry-run the watcher
node  test/curve.test.mjs            # curve tests
python test/test_curve.py            # python parity
```

The bot needs `TELEGRAM_BOT_TOKEN` in `~/AppData/Local/hermes/.env` and the Nekoray
proxy on `127.0.0.1:2081`. Target channel: `-1004398672746` (`@VibeGraduation`).

## Deploy

Static host (Vercel) serving the repo root: `index.html` + `web/` + `core/`.
No build command, no framework, output directory `.` .
