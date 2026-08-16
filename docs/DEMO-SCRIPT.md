# Demo video script — plain English

**Target length: 2 minutes 20 seconds.** Four parts: the problem, what we built, how it works, why it matters.

Speak slowly. The pictures do most of the work — you do not need to fill every second with talking.

**Live site:** https://abhinav0905.github.io/shadespan/
**Report:** https://abhinav0905.github.io/shadespan/report.html
**Code:** https://github.com/Abhinav0905/shadespan

---

## Part 1 — What is the problem? (0:00 – 0:35)

> **On screen:** any online shop's product page, showing one garment on one model. Then the landing page headline.

Say:

"Look at almost any clothing website. Every item is photographed on one model.

But customers do not all have that model's skin tone. So everyone else is guessing.

And sometimes the guess is wrong in an expensive way. A beige t-shirt can blend straight into fair skin. A pale yellow can look washed out on deep skin. A camel jumper can almost disappear on the exact skin tone it matches.

When that happens, the customer either never clicks buy, or they buy it and send it back.

The brand almost never finds out which items are doing this. To check properly you would need to photograph 14 garments on 6 different models. That is 84 photo shoots. Nobody has time for that. So the problem is only discovered months later, hidden inside the returns data."

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

> **On screen:** the "Why it's worth doing" section of the landing page, then the end card.

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
| 1 | 0:00 | A clothing product page with one model. Or open the landing page headline. |
| 2 | 0:20 | The landing page "The problem" section. |
| 3 | 0:35 | Terminal: `shadespan audit --live --max-units 250` running to 84. |
| 4 | 1:05 | The render matrix, scrolling slowly from top to bottom. |
| 5 | 1:30 | `report.html` in a browser — worst offenders, then one expanded row of scores. |
| 6 | 1:50 | The landing page "Why it's worth doing" cards. |
| 7 | 2:15 | End card with the GitHub link. |

## Before you record

* Full screen the browser and hide your bookmarks bar.
* **Do not show the `.env` file**, and do not scroll back to any terminal output containing your API key.
* If you want a live terminal moment without waiting, run the audit once first — the cache makes the second run instant and free.
* Record at 1440p if you can. The grid has small details.

## If you only have 60 seconds

Cut Part 3's scoring explanation and Part 4's middle two benefits. Keep: the problem, the grid, worst-tone grading, and the closing line.
