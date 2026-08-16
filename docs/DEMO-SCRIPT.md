# Demo video script — plain English

**Target length: 2 minutes 40 seconds.** Four parts: the problem, a live demo, the scale, the benefit.

The centrepiece is Part 2 — dropping a garment in and watching six renders come back. Rehearse that once so the drag-and-drop is smooth on camera.

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

## Part 2 — What have we built? (0:35 – 1:25) — **the live moment**

> **On screen:** the ShadeSpan dashboard at `http://127.0.0.1:8787`. Engine set to **Live**.
> Drag `assets/demo-drops/sand-tee.png` onto the drop zone.

Say, while dragging:

"So we built ShadeSpan. Here is a new colourway a buyer is considering. It is not in the catalogue — I am just dropping the photo in."

> **The six panels fill in one by one over about thirty seconds.** Let them land. Do not talk over the whole wait.

"ShadeSpan reads the colour straight out of the photo, then calls the **YouCam Apparel Virtual Try-On API** once for every person on the panel. Six real renders, about twelve API units.

And there it is — **grade F**. This sand colour scores twenty-five out of a hundred on Fitzpatrick four. Look at the first four models: the t-shirt is basically the same brightness as their skin. It only becomes a real garment on the two deepest tones."

> **Now drop `assets/demo-drops/teal-tee.png`.**

"Same panel, different colour. This teal comes back **grade B** — sixty-six at its worst, and it holds on all six.

That is the whole decision, in about a minute, before anyone has booked a photographer."

---

## Part 3 — And across a whole catalogue (1:25 – 2:05)

> **On screen:** scroll the render matrix slowly, worst grade at the top.

Say:

"Now run that across an entire collection. Fourteen garments, six people — eighty-four renders, about two minutes, a hundred and sixty-eight units.

Every garment, on every skin tone, in one grid, worst at the top.

Look at the blush pink t-shirt on the two lightest skin tones. It nearly vanishes. Now look at the chocolate brown top on the deepest skin tone — same problem, opposite end. And camel disappears in the middle of the range."

> **Pause on the cobalt and emerald rows at the bottom.**

"And this is what passing looks like. Cobalt blue works on everybody. Emerald green works on everybody.

Only two garments out of fourteen manage that."

> **On screen:** the report, with one row expanded to show the scores.

"Behind every picture there is a real measurement. We check the brightness difference, the colour difference, and how strong the colour is — using standard colour science that opticians and accessibility standards already use. Nothing here is a guess or an opinion.

And this is the important part: **each garment is graded on its worst skin tone, not its average.**

If you use the average, a garment that fails badly for one group still looks fine overall. The average hides exactly the customer we are trying to protect. So we refuse to use it."

---

## Part 4 — What is the benefit? (2:05 – 2:40)

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
| 3 | 0:35 | Dashboard. Drag `assets/demo-drops/sand-tee.png` in. Six panels fill → **grade F**. |
| 4 | 1:10 | Drag `assets/demo-drops/teal-tee.png` in → **grade B**. |
| 5 | 1:25 | The render matrix, scrolling slowly from top to bottom. |
| 6 | 1:50 | `report.html` — worst offenders, then one expanded row of scores. |
| 7 | 2:05 | The landing page "What a brand gets" cards. |
| 8 | 2:35 | End card with the GitHub link. |

## Before you record

* Start the dashboard first: `shadespan serve`, then open `http://127.0.0.1:8787` and set **Engine → Live**.
* Have `assets/demo-drops/sand-tee.png` and `teal-tee.png` visible in a Finder window, ready to drag.
* Full screen the browser and hide your bookmarks bar.
* **Do not show the `.env` file**, and do not scroll back to any terminal output containing your API key.
* A live drop takes about 30 seconds. That is fine on camera — but if you would rather not wait, drop the same file once before recording: the render cache makes the second drop nearly instant and free.
* If the network misbehaves mid-take, switch Engine to **Mock** and keep going. It renders the same layout offline with zero units.
* Record at 1440p if you can. The grid has small details.

## If you only have 60 seconds

Keep Part 1 (the side-by-side) and Part 2 (the sand-tee drop, grade F). Then jump straight to the closing line. That alone tells the whole story.
