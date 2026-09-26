# Definition of Done

The project is submission-ready when all of the following are true.

## Input

- [ ] Video upload works
- [ ] brand.json upload works
- [ ] Invalid inputs show useful errors

## Understanding

- [ ] Bengali ASR runs automatically
- [ ] Audio signals are generated
- [ ] Shot detection runs
- [ ] Visual context is generated
- [ ] Semantic scenes are generated

## Break engine

- [ ] Candidates are generated automatically
- [ ] Mid-sentence cuts are rejected
- [ ] Active dialogue cuts are rejected
- [ ] Minimum gap enforced
- [ ] Maximum breaks/hour enforced
- [ ] Maximum ad-load enforced
- [ ] Break score generated

## Brand engine

- [ ] All brands loaded dynamically
- [ ] Negative contexts are hard blocks
- [ ] Eligible brands are semantically ranked
- [ ] Dominant scene activity influences matching
- [ ] Brand I test passes with zero code changes

## Outputs

- [ ] scenes.json
- [ ] debug.json
- [ ] vmap.xml
- [ ] all files viewable
- [ ] all files downloadable

## Player

- [ ] Original video plays
- [ ] generated break timestamps are used
- [ ] black virtual ad appears
- [ ] selected brand is displayed dynamically
- [ ] selected duration is respected
- [ ] episode resumes
- [ ] multiple breaks work
- [ ] seeking does not create obvious duplicate ad playback

## Compliance

- [ ] no hard-coded timestamps
- [ ] no hard-coded brand assignments
- [ ] no hand-corrected transcripts
- [ ] no negative-context violations
- [ ] no real-company brand substitution
- [ ] live demo works

## Submission

- [ ] live demo link
- [ ] public GitHub repo
- [ ] explanatory video under 5 minutes
