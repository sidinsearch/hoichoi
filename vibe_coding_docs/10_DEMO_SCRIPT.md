# Judge Demo Script

Target: under 5 minutes.

## 0:00 — Explain input

Show:

```text
Bengali episode.mp4
brand.json
```

Say:

> We give the system a Bengali drama and the synthetic brand catalogue. We don't tell it where ads belong.

---

## 0:30 — Analyze

Click:

`Analyze Video`

Show real progress.

Explain:

> Audio provides Bengali speech, pauses and sentence boundaries. Vision provides setting, objects and activities. The multimodal model turns these signals into semantic scenes.

---

## 1:15 — Show scenes

Open `scenes.json`.

Show:
- scene boundaries
- context
- activities
- transcript evidence

Say:

> Shots are not treated as final scenes. We combine visual and language evidence into semantic scenes.

---

## 1:45 — Show break decision

Open `debug.json`.

Choose a strong accepted break.

Show:

- timestamp
- scene boundary
- sentence complete
- dialogue paused
- audio silence
- score

Then show a rejected candidate:

- dialogue active
- sentence incomplete

Say:

> Hard constraints are deterministic. The LLM does not get to override them.

---

## 2:30 — Show brand safety

Show a candidate where a brand is blocked.

Example:

```text
Brand D
blocked: hospital
```

Say:

> Negative contexts are hard blocks. Semantic similarity cannot rescue a blocked brand.

---

## 3:00 — Show VMAP

Open `vmap.xml`.

Explain:

> The analysis becomes a machine-readable ad-break manifest.

---

## 3:20 — Play

Start the episode.

At generated timestamp:
- episode pauses
- black virtual ad appears
- brand information is shown
- countdown runs
- episode resumes

Say:

> We do not render a modified episode. The player executes the generated break schedule against the original video.

---

## 4:15 — Unseen brand

If time permits:
- add Brand I to JSON
- rerun

Say:

> No code changes are needed. Brands are data, not code.

---

## 4:40 — Closing

> The system answers the three decisions: where it is safe to interrupt, whether an interruption is warranted, and which synthetic brand belongs there.
