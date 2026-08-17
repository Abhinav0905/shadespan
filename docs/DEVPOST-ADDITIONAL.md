# Devpost "Additional info" page — copy and paste

Paste each block into the matching field. Plain English, nothing to rewrite.

---

## "What date did you start this project?"

Already filled: `08/14/2026`. Leave it.

---

## "If Existing, explain what you updated during the submission period."

Optional — this is a new project, so leave it blank. If you would rather write something:

> Not an existing project. ShadeSpan was started and finished inside the submission period.

---

## "Provide a text description explaining the features, functionality, and consumer or retail value of your project."

ShadeSpan checks whether a clothing brand's colours actually work on every customer, before the collection goes on sale.

**What it does.** You give it a catalogue and a panel of six people, one for each Fitzpatrick skin tone from the lightest to the deepest. It renders every garment on every person using YouCam Apparel Virtual Try-On. It then scores each combination on how clearly the garment separates from that skin tone, using published colour science: brightness contrast from the WCAG standard, colour distance using CIEDE2000, and saturation. Anything sitting too close to skin in brightness, saturation and hue at once is capped at a fail, because that failure is categorical rather than marginal.

Each garment is graded on its **worst** skin tone, never its average. Grade on the average and a garment that fails badly for one group still looks acceptable overall, which hides exactly the customer the tool exists to protect.

It also works on garments that are not in the catalogue yet. Drop any product photo into the dashboard and it comes back rendered on all six people with scores, in about half a minute and roughly 12 API units.

**Retail value.** Photographing 14 garments on 6 models is 84 separate photo shoots and about a week of studio time, so brands do not do it. The colour ships and they find out months later from returns data. US online clothing is returned at 30–35%, roughly double the 19.3% e-commerce average, and about 23% of returns are attributed to style and colour rather than size or fit.

So the value is concrete: drop or recolour a bad colourway while there is still time to change it; spend the photography budget only on the garment-and-tone pairs that genuinely need a second model; stop product pages over-promising on a colour that vanishes against the buyer's skin. Auditing a 14-piece capsule costs about 168 API units — roughly one shopper session — and informs the whole season.

On the demo catalogue, only 14.3% of garments pass on all six tones. Two out of fourteen.

---

## "Provide a URL to your code repository for judging and testing."

    https://github.com/Abhinav0905/shadespan

Public, Apache-2.0, setup instructions in the README. Mock mode runs the whole pipeline offline, so a judge can review it end to end without spending any API units.

---

## "Was there a moment during the hackathon where the API surprised you — in a good or frustrating way?"

Two, and they were opposites.

The frustrating one: my first live call kept failing with `invalid_garment_category`, no matter which category I sent. I tried every spelling I could think of. The real problem was that I was on the older v1.0 endpoint, which takes a nested payload/actions body. `v1.0/task/cloth` accepts your task, hands back a task id as if everything is fine, and only then fails it — because the category never reaches the engine at all. The error blamed my input for what was actually a versioning mistake. Moving to the flat v2.0 body fixed it instantly. I also learned the apparel slug is `cloth`, not `clothes`.

Skin AI surprised me the same way. It kept rejecting my photos as "face too small", so I re-downloaded everything at 2400px. Still rejected. The constraint is not pixel count, it is how much of the frame the face fills — the same photo fails at 1000px and at 2400px. Once I cropped to the face it worked first time.

The good surprise was the try-on quality. I expected to spend the hackathon fighting artefacts, and instead got 84 renders clean enough to use as evidence in a report. The failures my colour maths predicted were visibly there in the actual pictures, which is the whole reason the project works.

---

## "Are there industries or use cases you think Perfect Corp.'s API could serve that nobody is talking about yet?"

Yes — using try-on as a **testing instrument** rather than a shopper feature. Everyone points it at the customer. Point it at your own catalogue instead and it becomes quality control you can run before launch, at grid scale. That is what ShadeSpan does, and it opens up a few places:

**Uniform and workwear procurement.** A hospital, airline or hotel chain picks one uniform colour for thousands of staff with every skin tone. That choice is currently made from a fabric swatch and one fit model. It could be checked against a whole panel first.

**Safety clothing.** High-visibility and protective wear exists to be seen. Visibility is a safety requirement, not a style preference, and it gets signed off today without ever being tested across skin tones.

**School and team uniforms**, where one colour is imposed on an entire student body.

**Accessibility auditing for product imagery.** There are contrast standards for text on websites and nothing equivalent for whether a product photo actually shows the product. The same maths applies.

**Costume and stage design**, where a garment has to read from the back of a room under coloured light.

The common thread is any situation where one colour decision is made once and then applied to many different people. That is a measurement problem, and nobody is using this API for it yet.

---

## "Where did you hit a wall technically? How did you work around it?"

The renders contradicted the numbers.

My first full audit produced a report that confidently said "this blush tee disappears on Fitzpatrick I" — directly next to a photograph of a man in a **black** shirt. The try-on had quietly returned the model's original clothing instead of the garment I asked for. It happened when the model's own clothes were dark or heavily structured: a thick hoodie and a collared jumper broke it on every pale colour, while saturated colours worked on everyone. A report whose evidence contradicts its own claim is worse than one with no pictures at all.

Two things fixed it. I swapped those two panel photos for people in plain, light tops, which corrected most cells. And because it can happen on any catalogue, I built the check into the pipeline: sample the fabric on the chest of the finished render, compare it to the catalogue colour in CIEDE2000, and flag anything that drifted.

That measurement was its own wall. Comparing the render against the original photo also catches repainted skin and collar edges. A fixed box on the chest catches whatever the engine left behind when the try-on failed. Neither works alone, so it uses both together. And when the old garment and the new one are both dark, the only pixels that change enough to register are the edges — so a perfectly correct charcoal render measured light grey.

Checked by eye against 14 cells, it agrees on 10. So I made it report drift and never score it: it adds a "check this render" warning and leaves the grade untouched. A warning a merchandiser can dismiss in a second is worth having at that accuracy. A penalty built on a lighting artefact would quietly corrupt the grade instead. Doing it properly needs real garment segmentation, which is the next job rather than something I would claim to have now.

---

## "Share a link to any social posts about your project."

Optional. Leave blank if you have not posted, otherwise paste your LinkedIn or X URL.
