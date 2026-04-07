# Architecture Patterns

Reusable on-chain patterns extracted from the EU Digital Product Passport
work. Each pattern addresses a specific class of regulatory requirement.

## MPT-per-operator

**When:** The regulation assigns responsibility to economic operators, each
managing many items.

```mermaid
graph TD
    OP1[Operator A] --> MPT1[MPT Root A<br/>UTxO]
    OP2[Operator B] --> MPT2[MPT Root B<br/>UTxO]
    MPT1 --> L1[Item 1]
    MPT1 --> L2[Item 2]
    MPT1 --> L3[Item N]
    MPT2 --> L4[Item X]
    MPT2 --> L5[Item Y]
```

**Properties:**

- One UTxO per operator, regardless of item count
- Operator is the sole writer — no contention
- Items are leaves; updates recompute the root
- Cost scales with operators (~100s), not items (~millions)

**Constraint fit:**

- Data cadence: operator batches updates periodically
- Sequential access: one writer per trie
- Fee alignment: operator pays for their own trie
- Identity delegation: items carry proxy keys, operator submits on behalf

## Commitment-then-submit

**When:** The regulation requires proving that an action occurred within a
specific time window.

```mermaid
sequenceDiagram
    participant O as Operator
    participant C as Chain
    participant U as User

    O->>C: Tx1: Set commitment (validFrom, validUntil)
    Note over C: Commitment stored in leaf
    U->>O: Tap NFC / submit reading
    O->>C: Tx2: Submit reading + clear commitment
    Note over C: Commitment = None
    Note over C: Replay rejected (no commitment)
```

**Properties:**

- On-chain commitment acts as a trusted clock
- Single-use: cleared on submission, prevents replay
- Slot-bounded: validator checks `validFrom <= slot <= validUntil`
- No off-chain timestamp trust needed

**Invariant:** After submission, `leaf.commitment = none`. Formally proved.

## Operator-as-aggregator

**When:** Users must interact with the blockchain but cannot have wallets.

```mermaid
graph LR
    U1[User 1] -->|reading| OP[Operator]
    U2[User 2] -->|reading| OP
    U3[User N] -->|reading| OP
    OP -->|batch tx| BC[Blockchain]
```

**Properties:**

- Users have zero blockchain presence — no wallet, no ADA, no keys
- Operator collects actions and batches them into transactions
- The operator pays all fees (compliance is their incentive)
- Happy path: cooperative. Sad path: user escalates via bond/timeout

**Key design:** The user's action is authenticated not by a wallet signature
but by a **proxy credential** (NFC secure element, institutional badge,
delegated key). The operator includes this proof in the transaction.

## Lifecycle state machine

**When:** The regulation defines product/item status transitions.

```mermaid
stateDiagram-v2
    [*] --> Virgin: manufactured
    Virgin --> Active: placed on market
    Active --> Active: readings, updates
    Active --> Repurposed: second life
    Repurposed --> Active: re-activated
    Active --> Recycled: end of life
    Repurposed --> Recycled: end of life
    Recycled --> [*]
```

**Properties:**

- Status is a field in the MPT leaf
- Transitions are validated on-chain (no backward transitions)
- Each transition may change the responsible operator
- Historical states are preserved in the trie's audit trail

**Invariant:** `transition(s1, s2) → ord(s2) >= ord(s1)`. No backward
transitions except explicitly allowed ones (e.g., repurposed → active).

## Reward distribution

**When:** The regulation benefits from incentivizing third-party data
collection.

**Properties:**

- Reporters accumulate rewards in a monotonically increasing counter
- Each valid reading adds to the reporter's accumulated total
- Rewards are stored in the MPT alongside item data
- Withdrawal is a separate transaction (operator funds the pool)

**Invariant:** `credit(reporter, reward) → reporter'.accumulated > reporter.accumulated`
for any `reward > 0`. Formally proved.

## Cross-operator handoff

**When:** The regulation transfers responsibility between parties (resale,
repurposing, import/export).

```mermaid
graph LR
    T1[Operator A's Trie] -->|handoff| T2[Operator B's Trie]
    T1 --> L1[Item leaf<br/>status: handed-off<br/>read-only]
    T2 --> L2[New item leaf<br/>back-link to A's root]
```

**Properties:**

- Old leaf becomes read-only in the originating trie
- New leaf is created in the receiving operator's trie
- Back-link to the original root preserves provenance
- Full history is verifiable across both tries

## Relay state machine

**When:** Multiple actors must act in sequence, each contributing their
part to the compliance record.

```mermaid
sequenceDiagram
    participant M as Manufacturer
    participant T as Transporter
    participant C as Customs
    participant I as Importer

    M->>M: Create leaf (product data)
    M->>T: Physical handover
    T->>T: Update leaf (shipment data)
    T->>C: Arrive at border
    C->>C: Update leaf (verification)
    C->>I: Release
    I->>I: Update leaf (take ownership)
```

**Properties:**

- The regulation defines the actor ordering
- Each actor can only act when it's their turn
- Timeout/escalation if an actor doesn't act within deadline
- The trie serializes access naturally — no contention because the
  regulation already requires sequential processing

## Beacon-gated attestation

**When:** The regulation requires the user to see the operator's current
compliance status before contributing data.

```mermaid
sequenceDiagram
    participant R as Regulator
    participant C as Chain
    participant O as Operator
    participant U as User

    R->>C: Update standing in regulation trie
    O->>C: Mint beacon (policy reads standing)
    O->>U: Relay beacon + query
    U->>U: Verify beacon, sign data + beacon
    U->>O: Return signed payload
    O->>C: Submit batch (contract validates beacon)
```

**Properties:**

- Operator cannot collect attestations without a current beacon
- Minting policy forces inclusion of operator's standing from regulation trie
- Beacon has bounded validity — no stale reputation
- User signs over the beacon — informed consent by construction
- The user needs only the regulator's published beacon policy identifier
  and trust anchor to verify the beacon

**Invariant:** A batch submission is rejected if it includes a beacon whose
expiry has passed or whose standing hash doesn't match the regulation trie
at mint time.

## Identity delegation via hardware

**When:** Non-crypto actors must make on-chain state transitions.

```mermaid
graph TB
    S[Physical Sensor] -->|I2C| SE[Secure Element<br/>Ed25519 / secp256k1]
    SE -->|COSE_Sign1| NFC[NFC Interface]
    NFC -->|tap| P[Phone App]
    P -->|HTTPS| OP[Operator API]
    OP -->|tx with proof| BC[Blockchain Validator]
```

**Hardware requirements:**

| Component | Role | Constraint |
|-----------|------|-----------|
| Sensor | Measures physical state | Analog — tamper is expensive |
| Secure element | Signs with private key | Key never leaves chip |
| NFC interface | Bridges to phone | Powered by phone's field |
| Validator | Verifies signature on-chain | Must use Plutus built-in curve |

**Supported curves:** Ed25519 and secp256k1 have native Plutus built-in
verifiers. P-256/P-384 do not — avoid hardware that only supports NIST
curves.
