# YouTube upload details

Video file: **`~/Desktop/ShadeSpan-demo.mp4`** — 2:55, 1920x1080, 30fps, 9.1 MB.

Speech is at 1.30x with silences removed, so the pacing sounds natural rather than rushed.

Set visibility to **Public** or **Unlisted**. Do not use Private: Devpost judges
cannot open a private video, and that counts as a missing deliverable.

## Title

```
ShadeSpan — finding the clothes that disappear on your skin tone (YouCam API Hackathon 2026)
```

## Description

```
Most online shops photograph each garment on one model. Everyone whose skin is a
different shade is guessing — and sometimes the guess is expensive. A beige tee
that blends into fair skin. A chocolate brown that goes muddy on deep skin. The
customer either never clicks, or buys it and sends it back.

ShadeSpan renders every garment in a catalogue on every skin tone using the
YouCam Apparel Virtual Try-On API, scores how clearly each colour reads against
each tone using published colour science, and grades each garment on its WORST
skin tone — never its average, because an average hides exactly the customer the
tool exists to protect.

On the demo catalogue, only 14.3% of garments hold a passing grade on all six
Fitzpatrick tones. Two out of fourteen.

In this video:
00:00  The problem — one t-shirt, two customers, one of them can't see it
00:25  Why nobody catches it before launch
00:57  What ShadeSpan does, and the whole catalogue graded
01:35  Live demo — drop in a garment, rendered on six skin tones
02:30  A colour that passes, for contrast

YouCam APIs used:
• Apparel Virtual Try-On  (POST /s2s/v2.0/task/cloth)  — all 84 renders
• Skin AI analysis        (POST /s2s/v2.0/task/skin-analysis)

Live site:  https://abhinav0905.github.io/shadespan/
Audit report: https://abhinav0905.github.io/shadespan/report.html
Source code: https://github.com/Abhinav0905/shadespan

Built for the YouCam API Skin AI & Apparel VTO Hackathon 2026.
Panel photographs used under the Unsplash License. Apache-2.0.
```

## Tags

```
YouCam API, Perfect Corp, virtual try-on, apparel VTO, fashion tech, retail tech,
inclusive design, skin tone, Fitzpatrick, colour science, CIEDE2000, ecommerce
returns, hackathon, Python, FastAPI
```

## Thumbnail

Upload `docs/screenshots/cover.png` — the side-by-side proof. It reads at
thumbnail size, which the 14x6 matrix does not.

## Chapter timestamps

Measured against the final cut, not estimated: Part 1 runs 00:00-01:35, the live
demo 01:35-02:53, end card to 02:55. The in-description marks above are rounded
to the nearest sentence start. YouTube only builds chapters if the first mark is
`00:00` and there are at least three.

## Captions

YouTube will auto-caption this after upload — turn them on in Studio once
processing finishes. Worth doing: the narration is dense and captions help more
than any further pacing change would.
