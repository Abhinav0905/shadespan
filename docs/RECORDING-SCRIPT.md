# Recording script — the dashboard and the live demo

Just the two screen-recorded parts. Read the **bold** lines aloud; the rest is
stage direction.

**Before you hit record**

* Server is already running: `http://127.0.0.1:8787`
* Have a Finder window open at `assets/demo-drops/` — you will drag from it
* Set **Engine → Live** in the "Try one garment" card *before* recording, so
  you are not fiddling with dropdowns on camera
* Browser full screen, bookmarks bar hidden
* `sand-tee.png` is **cold** — it will make real API calls and take ~30 seconds
* `teal-tee.png` is **warm** — it comes back instantly

---

## PART 1 — The dashboard  (about 25 seconds)

> **Screen:** top of `http://127.0.0.1:8787`. Do not scroll yet.

**"This is ShadeSpan running locally."**

> **Point the cursor at the six skin-tone swatches next to "Panel".**

**"These six swatches are the panel — six real people, one for each Fitzpatrick skin tone, from the very lightest to the deepest. Every garment gets tested against all six."**

> **Move the cursor to the "Run audit" row.**

**"This top section audits a whole catalogue at once — fourteen garments across six people, eighty-four renders."**

> **Now scroll down to "Try one garment on the whole panel".**

**"But the part I want to show you is this one."**

---

## PART 2 — The real demo  (about 70 seconds)

### 2a · Drop the failing garment

> **Screen:** the drop zone. Drag `sand-tee.png` from Finder onto it.

**"Here is a new colourway a buyer is thinking about. A sand t-shirt. It is not in the catalogue — I am just dropping the photo straight in."**

> **The thumbnail appears. Click "Render on all six".**

**"ShadeSpan reads the colour out of the photo itself — there it is, hex C-E-B-2-8-7 — and then calls the YouCam Apparel Virtual Try-On API once for every person on the panel."**

> **Now wait. The six panels fill in one at a time over ~30 seconds.**
> **Do not talk over the whole wait. Say this at about the halfway point:**

**"Six real renders. About twelve API units. Roughly half a minute."**

> **Let the rest land in silence. When the verdict banner appears:**

**"And there it is. Grade F."**

> **Point the cursor along the first four cells.**

**"Look at the first four models. Twenty-six. Twenty-six. Twenty-nine. Twenty-five. On four of the six skin tones this t-shirt is barely distinguishable from the person wearing it."**

> **Point at the last two cells.**

**"It only becomes a real garment on the two deepest tones — fifty-six, and seventy-nine."**

> **Point at the verdict line.**

**"And the grade is F, because we score a garment on its worst skin tone, not its average. An average would have called this a pass. The average hides exactly the customer we are trying to protect."**

### 2b · Drop the passing garment

> **Drag `teal-tee.png` onto the drop zone. Click "Render on all six".**
> **This one returns almost instantly — it is cached from an earlier run.**

**"Now the same panel, a different colour. A teal."**

> **The six cells appear.**

**"Grade B. Sixty-six at its very worst, and it holds on all six tones. That is a colour you can ship."**

### 2c · The point

> **Screen: leave the two results visible, or scroll between them.**

**"That is the entire decision — made in about a minute, before anyone has booked a photographer or cut a single sample."**

---

## Timing

| Segment | Length |
|---|---|
| Part 1 — dashboard | 0:25 |
| Part 2a — sand tee, grade F | 0:45 |
| Part 2b — teal tee, grade B | 0:15 |
| Part 2c — closing line | 0:10 |
| **Total** | **~1:35** |

Trim the 30-second render wait down to about 8 seconds in editing — speed it up
or cut to the panels appearing. Keep *some* of it: the wait is what makes it
obvious these are real API calls and not pre-baked pictures.

## Numbers you will see (so nothing surprises you)

**sand-tee.png** — detected `#CEB287`, **grade F**, worst 25 on Fitzpatrick IV
F1 26 · F2 26 · F3 29 · F4 25 · F5 56 · F6 79

**teal-tee.png** — detected `#0E6A73`, **grade B**, worst 66 on Fitzpatrick VI
F1 73 · F2 82 · F3 74 · F4 83 · F5 81 · F6 66

## If something goes wrong

* **A render fails or the network drops** — switch Engine to **Mock** and carry
  on. Same layout, same scores, renders offline, zero units. Do not say "live"
  while in mock.
* **You want another clean take of sand-tee** — the first take cached it, so
  take two would be instant and would *not* be calling the API. Ask me to clear
  its cache between takes, or record the take you want first.
* **Nothing responds** — check the server is still up: `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8787/` should print `200`.

## Do not show on camera

* The `.env` file (it holds your live API key)
* Any terminal scrollback containing the key
* The raw auth response
