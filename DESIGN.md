# VibeGrade — visual system

The site and the cards borrow **vibe/vibe's own kit** so the tool reads as part of the
ecosystem rather than a bolt-on:

| token | where it comes from | used for |
|---|---|---|
| Clash Display 600 | `testnet.vibevibe.fun/fonts/clashdisplay-600-latin-core.woff2` → `assets/clashdisplay-600.ttf` | display type, score numbers, card headlines |
| Instrument Sans | their `/fonts/instrumentsans-latin.woff2` | body copy, labels |
| JetBrains Mono | their `/fonts/jetbrainsmono-latin.woff2` | all numbers, tickers, addresses |
| `#101214` / `#dff902` | their palette | base / single accent |
| their mark's geometry | `docs/assets/logo-soft-light.svg` | echoed (not copied) in our own mark |

Fonts are converted to TTF so Pillow can render the channel cards with the same faces.

## Rules (from the common Claude-Code design-skill playbook)

1. **One accent, used sparingly.** Lime appears on: the mark, the active tab underline,
   progress fills, the score, and primary buttons. Nothing else.
2. **Display type leads.** Clash Display carries headlines and numbers; Instrument Sans
   never competes with it. Numbers are always monospace — it makes data feel measured.
3. **Depth from 1px borders, not shadows.** Dark UI dies under drop shadows.
4. **4px spacing scale, 14px/10px radii.** No arbitrary values.
5. **Motion ≤ 180ms, only on hover/focus/enter.** A 4px rise on cards, a 90° spin on refresh.
6. **Every number is real.** No skeleton rows with fake values, no placeholder charts.

## The mark

A lime rounded square holding three ascending bars and a rising dot — "graduating".
It reads at 16px (favicon) and at 42px (header). Distinct from their blob-`v`, same family.

## Card system (Pillow, channel)

| card | file | job |
|---|---|---|
| graduation | `bot/cards.py: render_graduation_card` | celebrate a completed curve |
| launch score | `render_score_card` | 0–100 with six bars and wrapped notes |
| radar | `render_radar_card` | 8 rows, progress bars, to-graduation |
| weekly report | `render_report_card` | 2×3 stat grid |

All four: 6px accent spine, Clash headline, mono numbers, ellipsized text, no overlapping
elements — each was rendered and visually checked.
