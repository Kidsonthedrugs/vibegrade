# Nano Banana prompts (Gemini 2.5 Flash Image)

Paste one prompt at a time. Aspect ratio matters: cards are **16:9** (1200x630).

---

## 1) Hero / social artwork (main)

```
A cinematic 3D render on a near-black background (#101214) of a small glossy
charcoal creature with two round ears and a soft rounded body - a friendly mascot,
not scary - standing on a thin lime-green (#dff902) ascending line chart made of
three steps. The creature looks up at a single small glowing lime dot floating above
the last step, as if about to reach it. Matte clay material, subtle rim light in
lime, soft studio lighting from the upper left, faint grain, shallow depth of field.
Composition: creature and chart on the RIGHT third, the LEFT two thirds almost empty
dark negative space for text. Minimal, premium, product-launch aesthetic.
Aspect ratio 16:9. No text, no logos, no watermarks.
```

## 2) Logo / app icon

```
A flat vector app icon: a lime-green (#dff902) rounded square (corner radius 26%)
containing three dark near-black (#101214) ascending bars with rounded ends and a
small dark dot floating above the tallest bar, suggesting growth and graduation.
Extremely simple, geometric, centered, thick even strokes, generous padding, no
gradients, no shadows, no text. Crisp edges suitable for a 512x512 icon.
Square 1:1.
```

## 3) Card background texture (for channel cards)

```
Abstract dark texture on #101214: a very faint lime (#dff902) topographic contour map
of a rising hill, drawn with 2px lines at 4% opacity, plus a soft diagonal light sweep
from the top-left and fine film grain. Almost black, calm, premium, non-distracting.
It must stay readable under white text. 16:9, no text.
```

## 4) vibe vibers-style character set (optional, for community posts)

```
Three tiny collector-character illustrations in a consistent style: rounded blob
bodies, simple dot eyes, one wearing a tiny chef hat, one holding a small rising chart,
one with a graduation cap. Same lime-and-charcoal palette (#dff902 on #101214), flat
2.5D vector shading, thick outlines, playful but clean. Arranged in a row on a dark
background with even spacing. 16:9. No text.
```

---

### Notes when generating
- **Do not** ask it to draw the words "VibeGrade" - generated type will be wrong. Add text
  in the layout, not the image.
- Keep `#101214` and `#dff902` in the prompt; it holds the brand.
- If the output is too busy, append: *"simplify, fewer elements, more empty space"*.
- For the OG image, generate at 16:9 and crop to 1200x630 - the left third must stay empty.
