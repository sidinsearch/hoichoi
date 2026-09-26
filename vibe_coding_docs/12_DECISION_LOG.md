# Architecture Decision Log

## ADR-001 — Do not render an edited episode

Decision:
Keep the original video unchanged and execute breaks in the player.

Reason:
- simpler
- faster
- easier to debug
- directly demonstrates generated timestamps
- avoids expensive rendering
- allows changing decisions without re-encoding

---

## ADR-002 — Virtual black-screen ad

Decision:
Represent selected advertisements as a black-screen UI card.

Reason:
No actual creative ad files are available.

The card displays:
- ADVERTISEMENT
- brand name
- category
- selected duration
- optional context

---

## ADR-003 — LLM for semantic understanding, not hard enforcement

Decision:
Use LLM/VLM for semantic scene interpretation and multimodal fusion.

Reason:
Hard rules need deterministic, reproducible enforcement.

---

## ADR-004 — Negative contexts are hard blocks

Decision:
A brand matching a negative context is removed from the candidate set.

Reason:
The handbook explicitly defines negative_contexts as a hard block.

---

## ADR-005 — Brands are data-driven

Decision:
No brand-specific Python or frontend logic.

Reason:
The system must generalise to a 9th unseen brand with zero code changes.

---

## ADR-006 — Single application

Decision:
FastAPI + frontend in one project.

Reason:
Solo 12-hour hackathon. Microservices would increase failure surface without improving the core demonstration.
