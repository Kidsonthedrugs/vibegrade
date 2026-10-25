# Outreach copy — vibegrade

## 1) Discord `#builders` post (primary)

> **I built a free radar for vibe/vibe launches — and found something in the numbers**
>
> Hey — I've been reverse-engineering the V6 curve for a side project and ended up with a
> live dashboard for the testnet. Three things it measures that I haven't seen anywhere else:
>
> **1. Exact distance to graduation.** Not volume, not progress bars — the exact pair amount
> that completes the curve. It's a constant-product curve on virtual reserves
> (`VT0 = 800M × 4/3`, `V0 = target/3`), so I can compute it to the wei. Verified against
> `quoteBuyExactIn` / `quoteSell` — token amounts match to ~1e-16, sells to 1 wei.
>
> **2. Graduation has no price gap.** At `pairPrincipal = target`, `sold = 800,000,000`
> exactly and the curve price equals the Uniswap v4 pool's opening price (2e-8 ETH/token).
> Neat design — worth saying out loud.
>
> **3. Where the 50% budget actually goes.** Across the 134 launches I track:
> - **19%** configured a graduation airdrop
> - **38%** spent 30%+ of the 50% budget on their *own* opening buy
> - **66%** left the default tax weights untouched
> - median holders: **13**
>
> So the budget built for distribution mostly goes to the creator. That's the single
> clearest lever I can see for the "reach your first community" problem.
>
> There's also a **launch score** (0–100, six documented components) so a creator can see
> what their configuration will do before they sign.
>
> Site: https://vibegrade-eta.vercel.app
> Cards for every graduation: https://t.me/VibeGraduation
> Code (MIT-ish, read it): https://github.com/Kidsonthedrugs/vibegrade
>
> Unofficial, no wallet connection needed, read-only. Happy to change anything, add a
> view you want, or hand the data over — just say which.

---

## 2) X post (from @VibeGraduation or personal)

> vibe/vibe has a 50% launch budget meant for distribution.
>
> I measured 134 live launches on the testnet:
>
> → 19% configured a graduation airdrop
> → 38% spent 30%+ of that budget on their own opening buy
> → 66% never touched the default tax weights
> → median holders: 13
>
> The budget goes to the creator, not the community.
>
> Also, for the record: at graduation the curve price equals the Uniswap v4 opening price
> exactly (2e-8 ETH/token). No gap. Verified to the wei.
>
> radar + launch score → vibegrade-eta.vercel.app
>
> @vibevibefun @meta_alchemist

---

## 3) One-line DM to the team

> Built a read-only radar + launch score for vibe/vibe testnet (exact distance to
> graduation from the curve itself, plus a 0–100 config score).
> 134 launches tracked: only 19% use graduation airdrops, 38% spend 30%+ of the 50% budget
> on their own buy. Site: vibegrade-eta.vercel.app — repo: github.com/Kidsonthedrugs/vibegrade

---

## Numbers to keep straight (don't overclaim)

| claim | source |
|---|---|
| 134 launches tracked | union of the 5 board tabs, v6 only |
| 63 graduations in 7 days | `graduation.at` within window |
| 53 ETH-paired grads, 212 ETH raised | 53 × 4 ETH target = 212 ✓ |
| 19% airdrop configured | `gifts.reservedUnits > 0` |
| 38% self-allocated ≥30% | `initialNetPersonalUnits / 1e9 supply` |
| 66% default weights | weights == {2000, 7500, 500, 0} |
| median 13 holders | `market.holderCount` |
| curve math | verified against on-chain quotes, 13 tests |

These are a **sample of the public board**, not the whole chain history (131k launches exist).
Say "of the launches I track", not "of all launches".
