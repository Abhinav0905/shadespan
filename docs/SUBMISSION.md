# ShadeSpan — submission pack

Everything Devpost asks for, in the order the form asks for it. Repo: https://github.com/Abhinav0905/shadespan

---

## Elevator pitch (200 char limit)

Paste this — 195 characters:

```
The same t-shirt is obvious on one customer and nearly invisible on another. ShadeSpan renders every garment on every skin tone with YouCam VTO and grades the colours that vanish — before launch.
```

## Thumbnail

Devpost asks for 3:2. Use **`docs/screenshots/thumbnail-3x2.png`** (1500x1000, 754 KB)
— also copied to `~/Desktop/ShadeSpan-thumbnail.png`.

`cover.png` is 1200x630 (1.90:1), which is why Devpost crops its text off both
edges; keep that one for YouTube, where 16:9 is right.

It is the side-by-side proof rather than the 14x6 matrix, because a judge
scrolling a gallery has to get the idea from the thumbnail alone. A grid of
small faces reads as "some kind of chart"; one garment on two people reads
instantly, and it still holds at 330px wide.

---

## Text description

### The problem

Most catalogs photograph each garment on one model. Every shopper on a different skin tone is guessing, and the guess is expensive on both sides. A beige tee that vanishes against fair skin, a pale yellow that reads washed-out on deep skin, a camel that turns invisible on the exact tone it matches — the shopper either never clicks, or clicks and returns it. US online apparel returns run 30–35%, against an e-commerce average of 19.3% (NRF 2025), and roughly 23% of retail returns are attributed to style and colour rather than size or fit.

Brands almost never find out which garments are doing this. Nobody renders the full garment-by-tone grid before launch, because shooting 14 garments on 6 models is 84 shots and a week of studio time.

### What ShadeSpan does

ShadeSpan renders that grid in two minutes, then grades it.

1. Takes a catalog and a six-model panel spanning Fitzpatrick I–VI.
2. Renders every garment on every panel member through **YouCam Apparel VTO**.
3. Scores every cell with deterministic colour science — WCAG luminance contrast, chromatic edge contrast in the a\*b\* plane, CIEDE2000 separation between garment and skin, chroma, plus a washout gate for near-skin neutrals. No model opinions; every number traces to a formula in one file.
4. Checks each render against its catalog swatch and flags cells where the try-on didn't produce the colour that was asked for.
5. Grades each garment on its **worst** tone, not its average — because an average is exactly the statistic that hides the customer this tool exists to protect.
6. Writes a self-contained HTML report: full render matrix, per-tone scores, worst offenders, every flag explained in plain English.

### Why this is the non-obvious use of the API

Virtual try-on is built as a shopper-facing feature: one customer, one garment, one moment of delight. ShadeSpan turns it into a **measurement instrument pointed at the brand's own catalog**. Same API, opposite end of the funnel — used before launch, by the merch team, at grid scale, to catch a problem the brand currently only discovers through returns data months later.

That reframing is the whole idea. It's also why the unit economics work: an audit of a 14-garment capsule costs about 168 units, roughly the price of one shopper session, and it informs decisions about the entire season.

### Consumer and retail value

* **Merchandising** gets a pre-launch signal on which colourways to cut, recolour, or shoot on additional models.
* **Photography budget** goes where it matters — the report names the exact garment-and-tone pairs that need a second model shot, instead of shooting everything on everyone.
* **Shoppers** get product imagery that shows how a garment actually reads on them, which is the single most requested and least delivered thing in online apparel.
* **Returns** fall when the product page stops over-promising on a colour that disappears against the buyer's skin.

### Results on the demo catalog

The bundled catalog is synthetic and deliberately adversarial: half near-skin neutrals chosen to fail on specific tones, half saturated colours that should pass everywhere. 84 live YouCam renders later:

**14.3% coverage — only 2 of 14 garments hold grade B or better across all six tones.**

The failures land exactly where the colour science predicts: pinks and ivories collapse on the fair end, chocolate and rust on the deep end, camel in the middle. Cobalt and emerald clear every tone. That agreement between an independent physical model and 84 independent renders is the result I'd point a judge at.

---

## How I built it

Python 3.11+, async throughout. `httpx` for transport, `pydantic` for the domain model, `typer` for the CLI, `FastAPI` for the dashboard, `Jinja2` for the report, `numpy`/`Pillow` for the colour maths, `tenacity` for retries.

The architecture keeps every YouCam path and payload shape in exactly one file (`youcam/endpoints.py`). The orchestrator, scoring engine and report never see an HTTP detail, so an API change is a one-file fix. Renders are content-addressed and cached, so a re-run after a crash or a threshold tweak costs zero units, and a unit ledger projects spend before every live call and stops cleanly at the cap.

### Integrating the API — what actually took the time

Both features are **v2.0** and share one shape: a flat body naming file ids directly, and a task id polled as a **path** segment.

```
POST /s2s/v1.1/file/{feature}        declare -> file_id + presigned PUT
PUT  <presigned url>                 upload bytes
POST /s2s/v2.0/task/cloth            {src_file_id, ref_file_id, garment_category}
GET  /s2s/v2.0/task/cloth/{task_id}  -> data.task_status + data.results.url
```

Three findings that cost real time and are worth passing on:

1. **The apparel slug is `cloth`, not `clothes`.** Anything else 404s.
2. **The v1.0 generation is a trap.** It takes a nested `request_id`/`payload`/`actions` envelope and polls with `?task_id=`. Critically, `v1.0/task/cloth` *accepts* a task and then fails it with `invalid_garment_category` no matter which category you send — the category never reaches the engine. The error blames your input for a versioning mistake.
3. **There is no color-analysis feature at any version.** Existing slugs: `cloth`, `skin-analysis`, `hair-color`, `makeup`, `bag`, `shoes`. Skin tone is therefore measured locally rather than by API.

Accepted `garment_category` values, brute-forced against the live validator: `upper_body`, `lower_body`, `full_body`, `auto`.

**Skin AI needs a face, not a catalog shot.** It rejects images where the face is small relative to the frame, and a garment-framed photo never qualifies. Resolution doesn't help — the constraint is face-to-frame ratio, not pixel count; the same photo fails at 1000px and at 2400px. So the panel analyzer locates the face and crops to it, retrying with progressively tighter crops on rejection.

---

## Challenges I ran into

**The renders quietly contradicted the scores.** The first full audit produced a report that confidently said "this blush tee disappears on Fitzpatrick I" next to a photo of a man in a *black* shirt. The try-on had silently returned the model's original clothing. It correlated with the model's own garment being dark or heavily structured — a thick hoodie and a collared sweater broke it on every pale garment, while saturated colours worked on everyone.

Two fixes. Swapping those two panel photos for models in plain, light tops fixed most cells. And since it can happen again on any catalog, I built the check into the pipeline: sample the fabric on the chest, compare it to the catalog swatch in dE2000, flag the drift.

That measurement is harder than it looks. A diff against the source photo also catches repainted skin and collar edges; a fixed torso box catches whatever the engine left behind when the try-on failed. Neither works alone, so it uses both. And when the old and new garments are both dark, the *only* pixels clearing the change threshold are edge pixels — so a perfectly correct charcoal render measures light grey.

Checked by eye against 14 cells, the heuristic agrees on 10. So drift is **reported, never scored**: it adds a "check this render" note and leaves the grade untouched. A flag a merchandiser dismisses in a second is worth having at that accuracy; a penalty built on a lighting artefact would quietly corrupt the grade. Being honest about a heuristic's error rate in the code and the README seemed better than shipping a confident number I couldn't defend.

**Sourcing the panel was its own lesson.** Finding six openly licensed portraits spanning Fitzpatrick I–VI, front-facing with the torso visible, is genuinely hard — and the deep end is hardest. Most openly licensed deep-skin portraits are low-key studio work whose shadow measures darker than the subject. Building the tool reproduced, in miniature, the representation gap the tool exists to measure.

---

## Accomplishments I'm proud of

* The colour model and the renders agree. 84 independent VTO renders land where an independent physical model predicted they would.
* It grades on the worst tone, not the mean. That's a one-line decision that determines whether the tool protects anyone.
* Honest instrumentation: real balance read from the account, cost measured rather than assumed (2 units per render, verified), and a fidelity heuristic that publishes its own error rate.
* Everything runs offline in mock mode, so the whole pipeline is reviewable without spending a unit.

## What I learned

That an API's error messages describe *its* model of the world, not yours — `invalid_garment_category` meant "wrong API version". And that when a generated artefact becomes evidence in a report, you owe the reader a check that the evidence says what you claim it says.

## What's next

Real garment segmentation so fidelity can fold into the score instead of sitting beside it. Several models per Fitzpatrick band rather than one. Retuning thresholds against a brand's actual return data — the constants live in one file precisely so a merch team can do that. And a Shopify/PIM hook so an audit runs automatically when a colourway is added.

## Built with

`python` `youcam-apparel-vto` `youcam-skin-ai` `perfect-corp-api` `httpx` `pydantic` `fastapi` `typer` `jinja2` `numpy` `pillow` `ciede2000` `wcag` `asyncio`

---

# Demo video script (target 2:30)

Record at 1440p. The report and matrix are the stars — keep them on screen and let them do the work.

### 0:00–0:20 — The problem, stated on screen

> *Screen: a product page showing one garment on one model.*

"Every garment in this catalog was photographed on one model. If you're not that model's skin tone, you're guessing — and the guess costs the brand a return. Brands rarely find out which colours do this, because nobody renders the full garment-by-tone grid before launch."

### 0:20–0:45 — What it does, and the API

> *Screen: terminal, `shadespan audit --live` running, counter climbing to 84.*

"ShadeSpan renders that grid. It takes a catalog and a six-tone Fitzpatrick panel, and calls **YouCam Apparel VTO** — `POST /s2s/v2.0/task/cloth` — once for every garment-and-tone pair. Fourteen garments, six tones, eighty-four real renders, about two minutes, a hundred and sixty-eight units."

### 0:45–1:20 — The matrix (the money shot)

> *Screen: scroll `docs/screenshots/02-render-matrix.png` slowly, worst grade first.*

"Here's the grid. Sorted worst first. Look at the blush tee on the two fairest tones — it's gone, it reads as skin. Chocolate does the same thing on the deepest tone. Camel disappears in the middle of the range."

> *Pause on the cobalt and emerald rows.*

"And here's what passing looks like. Cobalt clears every tone. Emerald clears every tone. Two garments out of fourteen."

### 1:20–1:50 — The scoring, and why worst-tone

> *Screen: the report, a single row expanded showing per-cell scores and flags.*

"Every cell is scored with deterministic colour science — WCAG contrast, CIEDE2000 separation between garment and skin, and a washout gate for near-skin neutrals. No model opinions; every number traces to a formula.

And each garment is graded on its **worst** tone, never its average. An average is exactly the statistic that hides the customer this tool exists to protect. On this catalog that's 14.3% coverage."

### 1:50–2:10 — Skin AI and honest instrumentation

> *Screen: `shadespan panel analyze` output, then `shadespan credit`.*

"The panel also runs through **YouCam Skin AI** — `skin-analysis` — for per-member skin condition scores. It needs a face rather than a catalog shot, so ShadeSpan crops to the face first and retries tighter if the API pushes back.

Cost is measured, not assumed: it reads the real balance off the account. Two units per render, verified."

### 2:10–2:30 — The honest bit, and close

> *Screen: a drift-flagged cell in the report.*

"One more thing. A try-on can quietly return the model's original clothing — which would leave a report claiming a garment fails, next to evidence that says otherwise. So ShadeSpan measures what each render actually produced and flags the drift. It's a heuristic, it agrees with my eye on ten cells out of fourteen, and it's reported rather than scored — because a flag you can dismiss is worth having, and a wrong penalty isn't.

Everyone points try-on at the shopper. ShadeSpan points it at the catalog, before the season ships."

> *End card: repo URL.*

### Shot list

| # | Source |
|---|---|
| 1 | Any single-model product page (or the F4 render alone) |
| 2 | Terminal: `shadespan audit --live --max-units 250` |
| 3 | `docs/screenshots/02-render-matrix.png`, slow scroll |
| 4 | `docs/sample-report.html` in a browser, worst-offenders + one expanded row |
| 5 | Terminal: `shadespan panel analyze`, then `shadespan credit` |
| 6 | Report, scrolled to a cell carrying a render-fidelity flag |
| 7 | End card: github.com/Abhinav0905/shadespan |

**Do not show:** the `.env` file, the terminal scrollback containing the API key, or the raw auth response.
