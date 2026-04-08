# Tasks: Process State Machine Ontology

## User Story 1 — Regulator understands breach notification protocol

### Task 1.1: Write process ontology (`process.ttl`)
**Phase:** 1
**Depends on:** nothing
**File:** `ontology/process.ttl`

Define 8 classes (Process, Step, OnChainStep, OffChainStep, DatumField,
DatumChange, SignatureReq, Deadline) and 20 properties in the `proc:`
namespace. Import `cfr:` for cross-references. No instances — just the
vocabulary.

**Acceptance:** `rdflib` parses `process.ttl` without errors. All classes
and properties have `rdfs:label` and `rdfs:comment`.

---

### Task 1.2: Define GDPR breach lifecycle states
**Phase:** 2
**Depends on:** 1.1
**File:** `ontology/processes/gdpr-breach.ttl`

Add `cfr:LifecycleState` instances for the breach notification process:
`NoBreach`, `BreachDetected`, `NotifiedTimely`, `NotifiedLate`. These
are the states the leaf datum can be in.

**Acceptance:** States are valid `cfr:LifecycleState` instances that
pass existing ontology validation.

---

### Task 1.3: Write GDPR breach notification process instance
**Phase:** 2
**Depends on:** 1.2
**File:** `ontology/processes/gdpr-breach.ttl`

Three steps:

1. `CommitBreach` (on-chain, step 1) — actor: DataController, action:
   gdpr:CommitBreach, sigs: controller key, checks: identity trie +
   standing + no existing commitment, datum: breach_commitment None →
   Just(commit_slot, deadline)
2. `InvestigateBreach` (off-chain, step 2) — actor: DataController,
   narrative: prepare notification
3. `SubmitNotification` (on-chain, step 3) — actor: DataController,
   action: gdpr:SubmitBreachNotification, sigs: controller key, checks:
   commitment exists + hash ≠ empty, datum: breach_commitment cleared,
   breach_record created

Plus a Deadline: 72h from BreachDetected to NotifiedTimely.

**Acceptance:** Process instance references valid `cfr:RedeemerAction`,
`cfr:Guard`, and `cfr:ConcreteParty` instances from `gdpr.ttl`. rdflib
parses without errors.

---

### Task 1.4: Write GDPR rights request process instance
**Phase:** 2
**Depends on:** 1.1
**File:** `ontology/processes/gdpr-rights.ttl`

Three steps: CommitRightsRequest → ProcessRequest (off-chain) →
SubmitResponse. Deadline: 1 month. Extensible to 3 months via an
optional fourth step (ExtendDeadline).

**Acceptance:** Same as 1.3.

---

### Task 1.5: Write GDPR consent lifecycle process instance
**Phase:** 2
**Depends on:** 1.1
**File:** `ontology/processes/gdpr-consent.ttl`

Two steps: RecordConsent → WithdrawConsent. No deadline. The
WithdrawConsent step must reference the process signature (data subject
signed).

**Acceptance:** Same as 1.3.

---

## User Story 2 — Developer models a new regulation's process

### Task 2.1: Add process validation to `validate.py`
**Phase:** 3
**Depends on:** 1.3
**File:** `ontology/validate.py`

Extend the validator to load `ontology/process.ttl` and
`ontology/processes/*.ttl`. Add checks:

- Every `proc:Process` has at least one step with `proc:fromState` that
  is not a `proc:toState` of any other step (initial state)
- Every `proc:OnChainStep` has at least one `proc:checks` and one
  `proc:requiresSig`
- Every `proc:usesAction` target is a valid `cfr:RedeemerAction`
- Every `proc:checks` target is a valid `cfr:Guard`
- Every `proc:implements` target is a valid `cfr:Obligation`
- `proc:stepOrder` values are unique within each process
- No unreachable states (every non-initial state is a `proc:toState`
  of at least one step)

**Acceptance:** Validator passes on valid processes. Validator fails with
a clear error when a guard is missing, a state is unreachable, or step
orders collide.

---

### Task 2.2: Update flake to include process files in validation
**Phase:** 3
**Depends on:** 2.1
**File:** `flake.nix`

The `checks.ontology` derivation must include `process.ttl` and
`processes/*.ttl` in the validation scope.

**Acceptance:** `nix build .#checks.x86_64-linux.ontology` validates
process files alongside existing ontology.

---

## User Story 1 (continued) — Rendering

### Task 3.1: Add process kinds to viewer config
**Phase:** 4
**Depends on:** 1.3
**File:** `ontology/viewer-config.json`

Add four new kinds: `on-chain-step`, `off-chain-step`, `datum-field`,
`deadline`.

**Acceptance:** Config is valid JSON with correct color/shape definitions.

---

### Task 3.2: Generate display annotations for process steps
**Phase:** 4
**Depends on:** 3.1, 1.3
**File:** `ontology/generate_display.py`

Extend the generator to read `process.ttl` + `processes/*.ttl`:

- Each `proc:OnChainStep` → `gb:Node` (kind: `on-chain-step`)
- Each `proc:OffChainStep` → `gb:Node` (kind: `off-chain-step`)
- Each `proc:Deadline` → `gb:Node` (kind: `deadline`)
- Edges: step → actor, step → guard (via `proc:checks`), step → next
  step (via step order), process → first step, deadline → states

**Acceptance:** Generated display TTL includes process nodes and edges.
The ontology viewer shows process steps as colored nodes connected to
their actors and guards.

---

### Task 3.3: Generate process tours
**Phase:** 4
**Depends on:** 3.2
**File:** `ontology/generate_display.py`

For each `proc:Process`, generate a graph-browser tour JSON file:

- Tour title = process label
- Tour description = process narrative
- Stops ordered by `proc:stepOrder`
- Each stop's node = the step's `gb:nodeId`
- Each stop's narrative = structured text with actor, signatures,
  checks, datum changes, deadline progress
- Each stop's depth = 2

Write tour files to the viewer data directory alongside view files.

**Acceptance:** The ontology viewer shows a "Guided Tours" menu with
one tour per process. Stepping through the tour highlights each step
in sequence with its narrative.

---

### Task 3.4: Add process view
**Phase:** 4
**Depends on:** 3.2
**File:** `ontology/generate_display.py`

Generate a "Processes" view that includes only process-related nodes
and edges (steps, actors, guards, datum fields, deadlines) — filtering
out the static ontology nodes.

**Acceptance:** The "Views" menu includes a "Processes" option that
shows only the process flow graph.

---

## User Story 3 — Auditor verifies protocol completeness

### Task 4.1: Obligation coverage check
**Phase:** 3
**Depends on:** 2.1
**File:** `ontology/validate.py`

For each regulation with a fit assessment, check that every
`cfr:Obligation` with a `cfr:implementedBy` pattern has at least one
`proc:Process` with `proc:implements` pointing to it.

Report uncovered obligations as warnings (not errors — some obligations
may not have processes yet).

**Acceptance:** The validator reports which obligations have process
coverage and which don't.

---

## Summary

| Task | Phase | Depends | Priority |
|------|-------|---------|----------|
| 1.1 Write process ontology | 1 | — | P1 |
| 1.2 Define breach states | 2 | 1.1 | P1 |
| 1.3 Write breach process | 2 | 1.2 | P1 |
| 1.4 Write rights process | 2 | 1.1 | P1 |
| 1.5 Write consent process | 2 | 1.1 | P1 |
| 2.1 Add process validation | 3 | 1.3 | P1 |
| 2.2 Update flake | 3 | 2.1 | P1 |
| 3.1 Add viewer kinds | 4 | 1.3 | P1 |
| 3.2 Generate display annotations | 4 | 3.1 | P1 |
| 3.3 Generate process tours | 4 | 3.2 | P1 |
| 3.4 Add process view | 4 | 3.2 | P1 |
| 4.1 Obligation coverage | 3 | 2.1 | P2 |
