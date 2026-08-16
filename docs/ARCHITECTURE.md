# Architecture

```
catalog.json + panel.json
        |
        v
pipeline/orchestrator.run_audit          async fan-out, semaphore(3)
        |            \
        |             +-- youcam/client.YouCamClient   (live: auth -> upload -> task -> poll)
        |             +-- youcam/mock.MockYouCamClient (offline illustration engine)
        |
        +-- runs/_cache/           content-addressed renders (sha1 of inputs)
        +-- pipeline UnitLedger    projects spend, stops cleanly at the cap
        |
        v
scoring/metrics.score_cell         deterministic per-cell score + flags
scoring/grade                      worst-tone grading, coverage, palette gaps
        |
        v
report/html.write_report           self-contained HTML (base64 thumbnails)
server/app                         FastAPI wrapper: start run, poll, open report
```

Decisions worth knowing:

* **Endpoint isolation.** Every YouCam path and payload shape lives in
  `youcam/endpoints.py`. When the docs and the code disagree, one file changes.
* **Mock parity.** The mock client implements the exact client interface, so
  the orchestrator cannot tell engines apart. Tests run the full pipeline
  against it, which is why the suite needs no network and no secrets.
* **Cache as resume.** Renders are keyed by content hash of both images plus
  category and engine. A crashed live run resumes for the cost of what is
  missing, and threshold tuning re-runs are free.
* **Scores are render-independent (v0).** Scoring works from calibrated
  colors, so a failed render still yields a scored, flagged cell; the render
  is evidence, not input. Folding sampled render color into the score is the
  designed next step (the fidelity plumbing exists behind a flag).
* **Auth.** id_token = base64(RSA-PKCS1v15("client_id=...&timestamp=...",
  public key = the API secret)). Cached, refreshed on 401.
