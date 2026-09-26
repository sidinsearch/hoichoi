# Test Plan

## 1. Pipeline tests

### Video ingestion
- valid MP4
- missing audio
- invalid video
- long video

### Brand ingestion
- valid JSON
- missing fields
- empty catalogue
- duplicate brand IDs
- Brand I addition

---

## 2. Audio tests

### Mid-sentence

Expected:
`REJECT`

### Completed sentence + silence

Expected:
candidate can survive to scoring.

### Active dialogue

Expected:
`REJECT`

### Low-confidence ASR

Expected:
conservative behavior.

---

## 3. Scene tests

### Multiple shots, same activity

Expected:
shots can be grouped into one semantic scene.

### Visual transition + new activity

Expected:
new semantic scene candidate.

---

## 4. Break tests

### Minimum gap

Expected:
reject.

### Maximum breaks/hour

Expected:
reject.

### Maximum ad load

Expected:
reject.

### Emotional climax

Expected:
strong penalty or rejection according to configured safety rule.

---

## 5. Brand tests

### Positive context

Cooking scene:
Brand A should be eligible if no negative context is present.

### Hard negative

Funeral:
food brand must be blocked.

### Hospital

Any brand with hospital in negative contexts must be blocked.

### Compound context

Phone + hospital:
telecom brand may be semantically relevant but must still be blocked if hospital is a negative context.

---

## 6. Unseen brand test

Add Brand I to JSON.

Do not modify code.

Expected:
- brand loads
- context embeddings generated
- negative contexts enforced
- brand can be selected if context matches

---

## 7. Player tests

### Break reached
Expected:
video pauses.

### Virtual ad
Expected:
black overlay displays selected brand.

### Duration
Expected:
overlay remains for selected duration.

### Resume
Expected:
video resumes from break position.

### Seeking
Expected:
already-consumed break does not replay accidentally.

### Multiple breaks
Expected:
each break executes once during normal playback.

---

## 8. Auto-disqualifier tests

The following should be manually checked before submission:

- no hard-coded sample timestamps
- no hard-coded sample brand assignments
- no hand-corrected transcripts
- no negative-context violation
- demo runs live
- synthetic brand names remain synthetic
