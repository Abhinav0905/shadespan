# Panel photos

Mock mode uses the bundled illustrated figures. A live audit needs six real
photos, one per Fitzpatrick band, that you have the right to use:

* openly licensed (CC0 / Unsplash / Pexels license) or shot yourself with consent
* front-facing, upper body visible, arms relaxed, plain background
* even lighting on the face, no strong color cast, no sunglasses
* at least 1024px on the short side

Drop them in this folder, then point `panel.json` at them:

```json
{ "id": "F3", "label": "Fitzpatrick III", "fitzpatrick": "III",
  "skin_hex": "#D9A579", "image": "f3_yourphoto.jpg", "source": "declared" }
```

Recalibrate the skin hexes from the actual photos before auditing:

```bash
shadespan panel sample        # free: median pixel color from the face region
shadespan panel calibrate     # measured: YouCam AI Color Analysis (live units)
```

Keep the same six IDs (F1..F6) so cached renders stay valid per photo.
