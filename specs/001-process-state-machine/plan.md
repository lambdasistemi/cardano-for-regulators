# Implementation Plan: Process State Machine Ontology

## Phase 1: Process Ontology (FR-001 through FR-006)

### What we're building

A new `ontology/process.ttl` that extends `cfr:` with process-level
concepts. The existing `cfr:LifecycleState`, `cfr:StateTransition`, and
`cfr:RedeemerAction` provide the foundation — the process ontology adds
sequencing, actor binding, signature requirements, datum changes, and
deadlines.

### Design decisions

**Extend cfr: not replace it.** The process ontology imports the `cfr:`
namespace. Process transitions reference existing `cfr:RedeemerAction`
and `cfr:Guard` instances. No duplication.

**Processes are independent of regulations.** A `proc:Process` references
the regulation it implements via `proc:implements` → `cfr:Obligation`,
but the process ontology itself is regulation-agnostic. The same process
structure works for GDPR, Battery Regulation, NIS2, etc.

**Steps are ordered.** Unlike the existing `cfr:StateTransition` (which
is unordered — just from/to states), process steps have a `proc:stepOrder`
integer that defines the narrative sequence. This is for the renderer, not
for the validator — the state machine is the source of truth, the step
order is the presentation order.

**Off-chain steps are first-class.** An `proc:OffChainStep` has no
redeemer action, no validator checks, no datum changes. It sits between
two on-chain transitions in the step sequence. It has a narrative
description (what happens off-chain) and optionally a duration estimate.

### New classes

| Class | Extends | Purpose |
|-------|---------|---------|
| `proc:Process` | new | Named sequence of steps implementing an obligation |
| `proc:Step` | new | Abstract base — either a transition or off-chain step |
| `proc:OnChainStep` | `proc:Step` | A transaction — wraps a `cfr:RedeemerAction` with context |
| `proc:OffChainStep` | `proc:Step` | An off-chain activity between transactions |
| `proc:DatumField` | new | A specific field in the UTxO datum |
| `proc:DatumChange` | new | A field that changes value during a transition |
| `proc:SignatureReq` | new | A required signature (references a `cfr:ConcreteParty`) |
| `proc:Deadline` | new | Slot-bounded constraint between two states |

### New properties

| Property | Domain | Range | Purpose |
|----------|--------|-------|---------|
| `proc:implements` | Process | cfr:Obligation | Which obligation this process covers |
| `proc:hasStep` | Process | Step | Steps in this process |
| `proc:stepOrder` | Step | xsd:integer | Presentation order |
| `proc:fromState` | OnChainStep | cfr:LifecycleState | State before transition |
| `proc:toState` | OnChainStep | cfr:LifecycleState | State after transition |
| `proc:usesAction` | OnChainStep | cfr:RedeemerAction | The redeemer action |
| `proc:requiresSig` | OnChainStep | SignatureReq | Required signature |
| `proc:checks` | OnChainStep | cfr:Guard | Validator checks (reuses cfr:Guard) |
| `proc:changes` | OnChainStep | DatumChange | Datum fields that change |
| `proc:actor` | Step | cfr:ConcreteParty | Who triggers this step |
| `proc:narrative` | Step | xsd:string | Human-readable description |
| `proc:fieldName` | DatumField | xsd:string | Datum field identifier |
| `proc:beforeValue` | DatumChange | xsd:string | Value before transition |
| `proc:afterValue` | DatumChange | xsd:string | Value after transition |
| `proc:changesField` | DatumChange | DatumField | Which field changes |
| `proc:deadline` | Process | Deadline | Deadline constraint |
| `proc:deadlineFrom` | Deadline | cfr:LifecycleState | Start state |
| `proc:deadlineTo` | Deadline | cfr:LifecycleState | Deadline state |
| `proc:slotDuration` | Deadline | xsd:string | Duration (e.g., "72h", "1 month") |
| `proc:sigParty` | SignatureReq | cfr:ConcreteParty | Who signs |
| `proc:sigType` | SignatureReq | xsd:string | Signature type (process/actor) |

### Relationship to existing cfr: classes

```
cfr:Obligation ← proc:implements ← proc:Process
                                      ↓ proc:hasStep
                                    proc:Step
                                      ├── proc:OnChainStep
                                      │     ├── proc:usesAction → cfr:RedeemerAction
                                      │     ├── proc:checks → cfr:Guard
                                      │     ├── proc:fromState → cfr:LifecycleState
                                      │     └── proc:toState → cfr:LifecycleState
                                      └── proc:OffChainStep
```

No existing class is modified. The process ontology is a pure extension.

## Phase 2: GDPR Breach Notification Instance (User Story 1)

### File: `ontology/processes/gdpr-breach.ttl`

The first process instance. Three steps:

1. **CommitBreach** (on-chain) — Controller creates commitment
   - Actor: gdpr:DataController
   - Action: gdpr:CommitBreach
   - Signatures: controller key
   - Checks: identity trie, standing ≠ suspended, no existing commitment
   - Datum: breach_commitment: None → Just(commit_slot, deadline)
   - Deadline starts: 72h countdown

2. **InvestigateBreach** (off-chain) — Controller investigates
   - Actor: gdpr:DataController
   - Narrative: "Prepare notification: nature, categories, numbers,
     consequences, measures taken"
   - No transaction, no datum change

3. **SubmitNotification** (on-chain) — Controller submits notification
   - Actor: gdpr:DataController
   - Action: gdpr:SubmitBreachNotification
   - Signatures: controller key
   - Checks: commitment exists, hash ≠ empty
   - Datum: breach_commitment: Just(...) → None; breach_record created
   - Deadline checked: timely flag set based on slot comparison

### Additional GDPR processes (same pattern)

- `gdpr-rights.ttl` — rights request (3 steps: commit, process, respond)
- `gdpr-consent.ttl` — consent lifecycle (2 steps: give, withdraw)

These follow the same structure. Once the breach notification works, these
are mechanical.

## Phase 3: Validation (FR-007, User Story 3)

### Extend `ontology/validate.py`

Add process-specific checks:

- Every process has at least one initial and one terminal state
- Every on-chain step has at least one check and one signature
- Every non-initial state is reachable (target of at least one transition)
- Every `proc:usesAction` references a valid `cfr:RedeemerAction`
- Every `proc:checks` references a valid `cfr:Guard`
- Every `proc:implements` references a valid `cfr:Obligation`
- Step orders are unique within a process

### Extend `flake.nix`

The `checks.ontology` derivation already validates `cfr.ttl` and
instances. Add `process.ttl` and `processes/*.ttl` to the validation.

## Phase 4: Rendering (FR-008 through FR-010, User Story 1)

### Approach: Graph-browser process tours

Reuse the existing tour infrastructure. Each process becomes a tour where:

- Each stop = a step in the process
- The stop's `node` = the step's node ID in the display graph
- The stop's `narrative` = the step's narrative + structured info
  (actor, signatures, checks, datum changes, deadline progress)
- The stop's `depth` = 2 (shows the step + its connected actors/checks)

### Display annotations

The `generate_display.py` script is extended to:

1. Read `processes/*.ttl`
2. Generate `gb:Node` for each step (kind: `on-chain-step` or
   `off-chain-step`)
3. Generate `gb:EdgeAssertion` for step → actor, step → guard,
   step → datum change, step → next step
4. Generate a tour JSON file for each process

### New graph-browser kinds

| Kind | Color | Shape | Purpose |
|------|-------|-------|---------|
| `on-chain-step` | `#3fb950` | `round-rectangle` | Transaction step |
| `off-chain-step` | `#8b949e` | `rectangle` | Off-chain activity |
| `datum-field` | `#79c0ff` | `ellipse` | Datum field before/after |
| `deadline` | `#f85149` | `triangle` | Deadline constraint |

### Tour narrative format

Each stop's narrative includes structured information rendered as
markdown within the tour text:

```
**Actor:** Data Controller
**Transaction:** CommitBreach

**Signatures required:**
- Controller key (actor authorization)

**Validator checks:**
- ✓ Controller key ∈ identity trie
- ✓ Standing ≠ suspended
- ✓ No existing commitment on leaf

**Datum change:**
- `breach_commitment`: None → Just(commit_slot: 50002100, deadline: 50005700)

**Deadline:** 72h countdown started (50005700 - 50002100 = 3600 slots)
```

## Phase 5: Cross-regulation comparison (User Story 4, P3)

Deferred. Once Battery Regulation processes are added (same patterns),
the view infrastructure already supports filtering by regulation. A
"Commitment-then-Submit" view would show both the GDPR breach and the
Battery SoH reading processes side by side.

## Risks

1. **Tour narrative length** — graph-browser tour narratives may not
   render well with structured tables/lists. May need graph-browser
   enhancement for richer stop content.

2. **Step count** — complex processes (rights request with extension) have
   5+ steps. The tour UI may need a progress indicator beyond "Stop 3 of 5".

3. **Datum visualization** — showing before/after datum as text in a
   narrative is functional but not visual. A dedicated datum diff widget
   would be better but is out of scope for v1.

## Deliverables

| Deliverable | File | Phase |
|-------------|------|-------|
| Process ontology | `ontology/process.ttl` | 1 |
| GDPR breach process | `ontology/processes/gdpr-breach.ttl` | 2 |
| GDPR rights process | `ontology/processes/gdpr-rights.ttl` | 2 |
| GDPR consent process | `ontology/processes/gdpr-consent.ttl` | 2 |
| Validation extensions | `ontology/validate.py` | 3 |
| Display generation | `ontology/generate_display.py` | 4 |
| Viewer config update | `ontology/viewer-config.json` | 4 |
| Tour generation | `ontology/generate_display.py` | 4 |
