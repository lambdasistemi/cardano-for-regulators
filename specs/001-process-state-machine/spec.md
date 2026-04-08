# Feature Specification: Process State Machine Ontology

**Feature Branch**: `001-process-state-machine`
**Created**: 2026-04-08
**Status**: Draft
**Input**: GitHub issue #49 — Process state machine ontology with animated rendering

## User Scenarios & Testing

### User Story 1 - Regulator understands the breach notification protocol (Priority: P1)

A regulator visiting the documentation wants to understand exactly how the
72-hour breach notification works on Cardano — who acts at each step, what
the chain enforces, and what happens if the deadline is missed.

**Why this priority**: The breach notification is the flagship protocol and
the most concrete demonstration of blockchain value for GDPR compliance.
Without a step-by-step walkthrough, the protocol remains abstract.

**Independent Test**: A non-technical reader can follow the breach
notification animation from detection to notification and understand at
each step: who acted, what was signed, what the validator checked, and
how the deadline was tracked.

**Acceptance Scenarios**:

1. **Given** the GDPR breach notification process, **When** a reader steps
   through it, **Then** they see each transaction as a distinct step with
   the active actor highlighted, the required signatures listed, the
   validator checks shown with pass/fail, and the UTxO state before and
   after.

2. **Given** a step between two transactions, **When** the reader advances
   past the first transaction, **Then** they see an off-chain step
   (investigation) clearly distinguished from on-chain transactions.

3. **Given** the 72-hour deadline, **When** the reader steps through the
   process, **Then** they see a countdown from the commitment slot to the
   submission slot, with a visual indication of whether the submission was
   timely.

---

### User Story 2 - Developer models a new regulation's process (Priority: P1)

A developer adding a new case study (e.g., NIS2) wants to express the
regulation's processes as formal state machines that are automatically
validated and rendered.

**Why this priority**: The framework's value is in its reusability. If
adding a new process requires hand-writing diagrams and docs, it doesn't
scale.

**Independent Test**: A developer creates a new process instance file
following the ontology, CI validates it, and the rendering appears
automatically — no hand-written diagrams.

**Acceptance Scenarios**:

1. **Given** the process ontology, **When** a developer writes a new
   `.ttl` file describing a process with states, transitions, actors, and
   checks, **Then** the CI validates it against the ontology and the
   renderer produces a step-through animation.

2. **Given** an existing process instance, **When** the developer modifies
   a transition (adds a guard, changes a deadline), **Then** the rendered
   animation reflects the change without manual updates.

---

### User Story 3 - Auditor verifies protocol completeness (Priority: P2)

An auditor reviewing the GDPR compliance architecture wants to verify that
every obligation has a corresponding process, every process has complete
state coverage, and no transition is missing guards.

**Why this priority**: The process ontology makes completeness mechanically
verifiable, not just narratively claimed.

**Independent Test**: The validator reports if a process has unreachable
states, transitions without guards, or obligations without processes.

**Acceptance Scenarios**:

1. **Given** the GDPR case study, **When** the validator runs, **Then** it
   confirms that every obligation listed in `gdpr.ttl` has at least one
   process instance covering it.

2. **Given** a process with a missing guard on a transition, **When** the
   validator runs, **Then** it reports the gap.

---

### User Story 4 - Compare processes across regulations (Priority: P3)

A researcher comparing GDPR and the Battery Regulation wants to see how
the same protocol pattern (commitment-then-submit) manifests differently
in each regulation — different actors, different deadlines, different
checks, same structure.

**Why this priority**: Cross-regulation comparison is the framework's
thesis — one architecture, many regulations.

**Independent Test**: The renderer can show two processes side by side or
in sequence, with shared pattern nodes highlighted.

## Edge Cases

- A process with no deadline (consent lifecycle) — the countdown is absent
  but the state machine still works.
- A process with an extensible deadline (rights request: 1 month,
  extendable to 3) — the deadline can change mid-process via a transition.
- A process with off-chain-only steps (investigation between transactions)
  — these are steps with no transaction but they advance the narrative.
- A process that spans two operators (repurposing handoff) — the state
  machine crosses trie boundaries.
- A process where the beacon carries the data policy — the pre-sale
  disclosure flow involves beacon minting as a step.

## Requirements

### Functional Requirements

- **FR-001**: The ontology MUST express processes as ordered sequences of
  states and transitions.
- **FR-002**: Each transition MUST reference the redeemer action, required
  signatures, and validator checks.
- **FR-003**: Each transition MUST specify the UTxO state before and after
  (datum fields that change).
- **FR-004**: Deadlines MUST be expressible as slot-bounded constraints
  attached to transitions or states.
- **FR-005**: Off-chain steps MUST be expressible as steps between
  transactions without on-chain state changes.
- **FR-006**: The ontology MUST be compatible with the existing `cfr:`
  namespace — processes reference `cfr:RedeemerAction`, `cfr:Guard`, etc.
- **FR-007**: Process instances MUST be validatable by CI alongside the
  existing ontology validation.
- **FR-008**: The renderer MUST produce a step-through experience where
  each step shows the active actor, signatures, checks, and state change.
- **FR-009**: The renderer MUST distinguish on-chain transactions from
  off-chain steps visually.
- **FR-010**: The renderer MUST show deadline progress when a deadline is
  defined.

### Key Entities

- **Process**: A named, ordered sequence of steps that implements a
  regulatory obligation.
- **ProcessState**: A named state that a process can be in (maps to a
  leaf datum configuration).
- **ProcessTransition**: A step that moves the process from one state to
  another via a transaction.
- **OffChainStep**: A step between transactions where off-chain activity
  occurs (investigation, data retrieval, user interaction).
- **TransitionActor**: The party that triggers a transition.
- **SignatureRequirement**: A signature that must be present for a
  transition to be valid.
- **ValidatorCheck**: A condition the smart contract verifies during a
  transition.
- **DatumChange**: A specific field in the UTxO datum that changes as a
  result of a transition.
- **Deadline**: A slot-bounded constraint that limits the time between
  two states.

### Invariants

- Every process MUST have at least one initial state and one terminal
  state.
- Every transition MUST have at least one source state and one target
  state.
- Every on-chain transition MUST have at least one validator check.
- Every on-chain transition MUST have at least one signature requirement.
- No state can be unreachable (every non-initial state must be the target
  of at least one transition).
- Deadlines MUST reference exactly two states (the start state and the
  deadline state).
