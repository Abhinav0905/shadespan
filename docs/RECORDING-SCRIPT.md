# Recording scripts

Two screen recordings, joined in editing.

| | What is on screen | Length |
|---|---|---|
| **Script 1** | The website — problem, solution, what we built | ~1:15 |
| **Script 2** | Localhost — the thing actually working | ~1:15 |
| | **Total** | **~2:30** |

The hackathon allows 1–3 minutes, so this fits with room to breathe.

Read the **bold** lines aloud. Everything else is stage direction.

## The three numbers — say these correctly

They are easy to mix up, so here they are plainly:

| Number | What it actually means |
|---|---|
| **30–35%** | Return rate for US online apparel |
| **19.3%** | Return rate for e-commerce overall (NRF 2025) — apparel is nearly **double** this |
| **~23%** | Share of retail returns blamed on **style and colour**, not size or fit |

Do not say "23% is the return rate" — 23% is the *share of returns caused by colour and style*. The return rate is 30–35%.

---

# SCRIPT 1 — The website (~1:15)

**Before recording:** open `https://abhinav0905.github.io/shadespan/` full screen, bookmarks bar hidden, scrolled to the very top.

## 1 · The problem, shown not told (0:00 – 0:25)

> **Start on the hero. Say nothing for two seconds. Let them look at the two photos.**

**"This is the same t-shirt. The same colour. On two different customers."**

> **Cursor to the left photo.**

**"On the left, it has almost exactly the same brightness as her skin, so its edges stop existing. In a small listing photo she is looking at a blank shape."**

> **Cursor to the right photo.**

**"On the right, same garment, same system, one after the other — and it reads perfectly."**

> **Scroll slowly to "And it cuts both ways".**

**"And this is not a story about one kind of skin. Here is a chocolate brown that is crisp on the lightest tone and muddy on the deepest. It happens at both ends."**

## 2 · Why nobody catches it (0:25 – 0:50)

> **Scroll to "Why nobody catches this today" — the three big numbers.**

**"Here is why this matters commercially."**

> **Cursor on 30–35%.**

**"Online clothing in the US gets returned at thirty to thirty-five percent. That is nearly double the e-commerce average of nineteen point three percent."**

> **Cursor on ~23%.**

**"And about twenty-three percent of returns are put down to style and colour — not size, not fit. Colour."**

> **Cursor on 84.**

**"But to actually check this before launch, a brand would have to photograph fourteen garments on six different models. Eighty-four separate photo shoots, for one small collection. So nobody checks. The colour ships, and the brand only finds out months later in the returns data."**

## 3 · What we built and how it works (0:50 – 1:15)

> **Scroll to "What ShadeSpan does" — the three cards.**

**"So we built ShadeSpan. It does those eighty-four photo shoots in about two minutes, and then marks them."**

**"It renders every garment on every skin tone using the YouCam Apparel Virtual Try-On API. It measures how clearly each colour separates from each skin tone using standard colour science — the same contrast maths that accessibility standards use. And then it grades."**

> **Scroll to "The whole catalogue at once" — the 14.3% and the grid.**

**"Here is a whole catalogue. Fourteen garments, six skin tones, eighty-four real renders."**

> **Scroll slowly down the grid.**

**"Only fourteen point three percent of this catalogue passes on every skin tone. Two garments out of fourteen."**

**"And the grading rule is the important part: each garment is scored on its worst skin tone, never its average. An average lets a garment that fails badly for one group still look fine overall. It hides exactly the customer we are trying to protect."**

> **Optional if you want the extra 10 seconds — scroll to "Why a simple brightness check isn't enough".**

**"And it is not naive. This emerald sits at one-to-one brightness against this skin tone — identical lightness. A simple checker would call that the worst failure in the catalogue. It is actually one of the best, because green against brown skin separates by hue, not brightness. We measure both."**

---

# SCRIPT 2 — The live demo (~1:15)

**Before recording:**

* Server running at `http://127.0.0.1:8787` — check it loads
* Finder open at `assets/demo-drops/`, ready to drag
* **Engine set to Live** in the "Try one garment" card, before you start recording
* `sand-tee.png` is **cold** — it will make real API calls, ~30 seconds
* `teal-tee.png` is **warm** — it comes back instantly

## 1 · Hand off from the website (0:00 – 0:15)

> **Screen: top of `http://127.0.0.1:8787`.**

**"That is the case. Now let me show you it actually running."**

> **Cursor across the six skin-tone swatches.**

**"This is ShadeSpan running live. These six swatches are the panel — one real person for each Fitzpatrick skin tone, lightest to deepest."**

> **Scroll to "Try one garment on the whole panel".**

## 2 · Drop the failing garment (0:15 – 0:55)

> **Drag `sand-tee.png` onto the drop zone.**

**"Here is a new colourway a buyer is considering. A sand t-shirt. It is not in the catalogue — I am dropping the photo straight in."**

> **Click "Render on all six".**

**"ShadeSpan reads the colour out of the photo itself — there, hex C-E-B-2-8-7 — and calls the YouCam Apparel Virtual Try-On API once for every person on the panel."**

> **Now wait. Six panels fill in over ~30 seconds. Say this around halfway, then stay quiet:**

**"Six real renders. About twelve API units. Half a minute."**

> **When the verdict banner appears:**

**"And there it is. Grade F."**

> **Run the cursor along the first four cells.**

**"Twenty-six. Twenty-six. Twenty-nine. Twenty-five. On four of the six skin tones, this t-shirt is barely distinguishable from the person wearing it."**

> **Cursor to the last two cells.**

**"It only becomes a real garment on the two deepest tones — fifty-six, and seventy-nine."**

> **Cursor to the verdict line.**

**"Grade F, because we score on the worst tone, not the average. On average this looks acceptable. On the customer it fails, it is invisible."**

## 3 · Drop the passing garment (0:55 – 1:05)

> **Drag `teal-tee.png` on. Click "Render on all six". This returns almost instantly.**

**"Same panel, different colour. A teal."**

**"Grade B. Sixty-six at its very worst, and it holds on all six tones. That is a colour you can ship."**

## 4 · Close (1:05 – 1:15)

**"That is the whole decision — made in about a minute, before anyone has booked a photographer or cut a single sample."**

**"Everyone else points virtual try-on at the shopper. We pointed it at the catalogue, and used it to find the problem before the customer ever sees it."**

> **End card: `github.com/Abhinav0905/shadespan`**

---

## Numbers you will see, so nothing surprises you

**sand-tee.png** — detected `#CEB287` · **grade F** · worst 25 on Fitzpatrick IV
F1 26 · F2 26 · F3 29 · F4 25 · F5 56 · F6 79

**teal-tee.png** — detected `#0E6A73` · **grade B** · worst 66 on Fitzpatrick VI
F1 73 · F2 82 · F3 74 · F4 83 · F5 81 · F6 66

## Editing

Trim the 30-second render wait down to about 8 seconds — speed it up, or cut to
the panels appearing. Keep *some* of it. That wait is the thing that proves
these are real API calls and not pictures prepared earlier.

## If something goes wrong

* **Network drops mid-take** — switch Engine to **Mock** and carry on. Same
  layout, same scores, renders offline, zero units. Do not say "live" while in
  mock.
* **You want a second take of sand-tee** — take one caches it, so take two
  returns instantly and is *not* calling the API. Ask me to clear its cache
  between takes.
* **Nothing responds** — `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8787/` should print `200`.

## Never on camera

* The `.env` file — it holds your live API key
* Terminal scrollback containing the key
* The raw auth response
