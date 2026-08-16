# Demo video script — plain English

**Target length: 2 minutes 20 seconds.** Four parts: the problem, what we built, how it works, why it matters.

Speak slowly. The pictures do most of the work — you do not need to fill every second with talking.

**Live site:** https://abhinav0905.github.io/shadespan/
**Report:** https://abhinav0905.github.io/shadespan/report.html
**Code:** https://github.com/Abhinav0905/shadespan

---

## Part 1 — What is the problem? (0:00 – 0:35)

> **On screen — start here, no talking for two seconds:** the two side-by-side photos from the top of the landing page. Same blush t-shirt, two different people. Let the viewer look before you say anything.

Say:

"This is the same t-shirt. The same colour. On two different customers.

On the right, you can see it. On the left, it has almost the same brightness as her skin — so its edges stop existing. In a small listing photo, she is looking at a blank shape.

That is not an editing trick. Both pictures came out of the same system, one after the other.

Now — the brand photographed this t-shirt once, on one model, and never found out. And to check properly, they would have to photograph 14 garments on 6 different models. That is 84 separate photo shoots. Nobody has time for that.

So the colour ships anyway. And the brand only finds out months later, buried in the returns data."

---

## Part 2 — What have we built? (0:35 – 1:05)

> **On screen:** terminal running `shadespan audit --live`, the counter climbing to 84.

Say:

"So we built ShadeSpan.

ShadeSpan does those 84 photo shoots in about two minutes, and then marks them like an exam.

It takes the brand's own product photos, and a panel of six people covering the full range of skin tones, from the very lightest to the deepest.

Then it calls the **YouCam Apparel Virtual Try-On API** once for every combination. Fourteen garments, six people, eighty-four real renders.

The whole audit costs about 168 API units. That is roughly the price of a single shopper using try-on once."

---

## Part 3 — How does it solve the problem? (1:05 – 1:50)

> **On screen:** scroll the render matrix slowly, worst grade at the top.

Say:

"Here is the result. Every garment, on every skin tone, in one grid. The worst ones are at the top.

Look at the blush pink t-shirt on the two lightest skin tones. It nearly vanishes. Now look at the chocolate brown top on the deepest skin tone — same problem, opposite end. And camel disappears in the middle of the range."

> **Pause on the cobalt and emerald rows at the bottom.**

"And this is what passing looks like. Cobalt blue works on everybody. Emerald green works on everybody.

Only two garments out of fourteen manage that."

> **On screen:** the report, with one row expanded to show the scores.

"Behind every picture there is a real measurement. We check the brightness difference, the colour difference, and how strong the colour is — using standard colour science that opticians and accessibility standards already use. Nothing here is a guess or an opinion.

And this is the important part: **each garment is graded on its worst skin tone, not its average.**

If you use the average, a garment that fails badly for one group still looks fine overall. The average hides exactly the customer we are trying to protect. So we refuse to use it."

---

## Part 4 — What is the benefit? (1:50 – 2:20)

> **On screen:** the "What a brand gets" section of the landing page, then the end card.

Say:

"So what does a brand get out of this?

They find the bad colours **before** the season goes on sale, while there is still time to change them.

They spend their photography budget precisely. The report tells them exactly which garment needs a second model, instead of shooting everything on everybody.

They get fewer returns, because the product page stops promising a colour that disappears on the customer.

And it is cheap enough to run every single time a new colour is added.

Everyone else points virtual try-on at the shopper. We pointed it at the catalogue instead — and used it to find the problem before the customer ever sees it.

Thank you."

> **End card:** github.com/Abhinav0905/shadespan

---

## Shot list

| # | Time | What to show |
|---|---|---|
| 1 | 0:00 | The two side-by-side photos at the top of the landing page. **Hold silently for 2 seconds.** |
| 2 | 0:22 | The landing page "Why nobody catches this today" numbers. |
| 3 | 0:35 | Terminal: `shadespan audit --live --max-units 250` running to 84. |
| 4 | 1:05 | The render matrix, scrolling slowly from top to bottom. |
| 5 | 1:30 | `report.html` in a browser — worst offenders, then one expanded row of scores. |
| 6 | 1:50 | The landing page "What a brand gets" cards. |
| 7 | 2:15 | End card with the GitHub link. |

## Before you record

* Full screen the browser and hide your bookmarks bar.
* **Do not show the `.env` file**, and do not scroll back to any terminal output containing your API key.
* If you want a live terminal moment without waiting, run the audit once first — the cache makes the second run instant and free.
* Record at 1440p if you can. The grid has small details.

## If you only have 60 seconds

Cut Part 3's scoring explanation and Part 4's middle two benefits. Keep: the problem, the grid, worst-tone grading, and the closing line.
