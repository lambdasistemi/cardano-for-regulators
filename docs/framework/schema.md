# The Regulator Schema

How a regulator can use Cardano to enforce a multi-party regulation without
running infrastructure, managing identities, or trusting any single operator.

## Four parties, four concerns

A regulated process involves four independent parties. Each manages one
concern and trusts no other party beyond what the chain enforces.

```mermaid
graph TB
    KYC[KYC Provider<br/><i>identity trie</i>]
    REG[Regulator<br/><i>smart contract + data trie</i>]
    OP[Operator<br/><i>process trie</i>]
    U[User<br/><i>key sovereignty + data holder</i>]

    REG -->|writes| SC{Smart Contract}
    REG -->|trusts| KYC
    REG -->|maintains| DT[Data Trie]
    SC -->|governs| OP
    KYC -->|reference input| SC
    DT -->|reference input| SC
    OP -->|distributes signing functions| U
    U -->|double-signed payloads + data proofs| OP
    OP -->|submits transactions| SC
```

| Party | Manages | Trusts |
|-------|---------|--------|
| **KYC provider** | Identity trie — attested keys, identity data hashes, attestation lifecycle | Their own verification process |
| **Regulator** | Smart contract + data trie — rules and regulation-specific user attributes | The KYC provider's UTxO |
| **Operator** | Process trie — items and processes | The smart contract — cannot deviate |
| **User** | Their own key (rotation) and their own data (selective disclosure) | The signing function they received |

No overlap. The KYC provider doesn't know about processes. The regulator
doesn't run infrastructure. The operator can't fake users. The user controls
their own key and chooses what data to disclose.

## The on-chain architecture

Four Merkle Patricia Tries, four UTxOs, three owners.

```mermaid
graph LR
    subgraph KYC Provider
        KYC_UTxO[KYC UTxO<br/>root hash]
        KYC_T[KYC Trie]
        KYC_UTxO --- KYC_T
        KYC_T --- K1[User A Leaf<br/><i>key + status +<br/>identity data root</i>]
        KYC_T --- K2[User B Leaf<br/><i>key + status +<br/>identity data root</i>]
        KYC_T --- K3[User N Leaf]
    end

    subgraph Regulator
        REG_UTxO[Data UTxO<br/>root hash]
        REG_T[Data Trie]
        REG_UTxO --- REG_T
        REG_T --- D1[User A Data<br/><i>regulation-specific<br/>attribute hashes</i>]
        REG_T --- D2[User B Data]
        SC[Smart Contract<br/>Plutus Validator]
    end

    subgraph Operator
        OP_UTxO[Process UTxO<br/>root hash]
        OP_T[Process Trie]
        OP_UTxO --- OP_T
        OP_T --- L1[Leaf 1<br/>item/process]
        OP_T --- L2[Leaf 2<br/>item/process]
        OP_T --- L3[Leaf N<br/>item/process]
    end

    SC -->|governs| OP_UTxO
    KYC_UTxO -.->|reference input| SC
    REG_UTxO -.->|reference input| SC
```

| Trie | Owner | Contains | Role |
|------|-------|----------|------|
| **KYC trie** | KYC provider (trusted by regulator) | Per-user leaf: current public key, attestation status, identity data root hash | Who is allowed to participate |
| **Regulator data trie** | Regulator | Per-user leaf: regulation-specific attribute hashes (licenses, certifications, roles) | What the user is qualified to do |
| **Process trie** | Operator | Items, processes, leaves with state | What is happening |
| **Commitment** | Inside each process leaf | Slot windows, expected actions | When and how actions occur |

The KYC trie and regulator data trie are both **reference inputs** — read-only
from the operator's perspective. The operator never spends them. The
regulator's smart contract reads both at validation time: the KYC trie to
verify the actor is attested, the data trie to verify the actor has the
required attributes for the action they are performing.

## How a transaction works

Every state transition follows this flow:

```mermaid
sequenceDiagram
    participant KP as KYC Provider
    participant R as Regulator
    participant O as Operator
    participant SF as Signing Function
    participant U as User
    participant C as Cardano

    Note over KP: Independently maintains<br/>identity trie

    R->>C: Deploy smart contract<br/>(references KYC UTxO + data trie UTxO)

    O->>C: Deploy process trie<br/>(governed by smart contract)
    O->>SF: Mint signing function<br/>(register pubkey on-chain)

    O->>C: Create commitment in leaf<br/>(slot window)

    U->>SF: Request signature<br/>(payload + commitment)
    SF->>U: Signed payload

    U->>O: Submit double-signed payload<br/>(process sig + actor sig)

    O->>C: Submit transaction

    Note over C: Validator checks:
    Note over C: 1. Actor key in KYC trie?<br/>(reference input)
    Note over C: 2. Commitment exists?<br/>(expected action)
    Note over C: 3. Slot in window?<br/>(timely)
    Note over C: 4. Process signature valid?<br/>(authentic)
    Note over C: 5. Actor key authorized?<br/>(baton holder)
    Note over C: 6. Leaf update matches payload?<br/>(untampered)
    Note over C: 7. New root hash consistent?<br/>(MPT integrity)

    C->>C: Clear commitment<br/>(no replay)
```

The validator has access to all the information it needs in a single
evaluation: the process trie UTxO (spent input), the KYC trie UTxO
(reference input), the signatures, and the slot range.

## What the regulator produces

The regulator has two on-chain responsibilities: the smart contract and
the data trie.

### The smart contract

The regulation in executable form:

```mermaid
graph TD
    REG[Regulator] -->|writes| SC[Smart Contract]

    SC --> DS[Data Schema<br/><i>what fields a leaf must contain</i>]
    SC --> VT[Valid Transitions<br/><i>what updates are allowed,<br/>in what order, by whom</i>]
    SC --> CP[Commitment Protocol<br/><i>how time windows work,<br/>what must be signed</i>]
    SC --> AR[Authorization Rules<br/><i>how the baton is assigned<br/>and passed</i>]
    SC --> KR[KYC Reference<br/><i>which UTxO is the trusted<br/>source of attested actors</i>]
    SC --> DR[Data Reference<br/><i>which UTxO is the regulator's<br/>data trie</i>]
```

The regulator deploys this contract once. Every operator in the market
operates under it. The regulator can audit any operator by checking their
trie against the contract — it's all on-chain, all governed by the same
rules.

The regulator does not run the KYC infrastructure. They decide **which
KYC provider to trust** — a government identity agency, eIDAS, a private
service — and hardcode (or parameterize) the reference to that provider's
UTxO in their smart contract. The chain does the rest.

The eUTxO model ensures the validator is evaluated at every transaction.
Non-compliant updates are rejected by the chain itself. The regulation is
enforced at the transaction level, not by inspectors after the fact.

### The regulator data trie

The KYC trie holds regulation-agnostic identity data — who you are. The
regulator data trie holds regulation-specific attributes — what you are
qualified to do under this particular regulation.

```mermaid
graph TD
    REG[Regulator] -->|maintains| DT[Data Trie UTxO<br/>root hash]
    DT --- U1[User A Data Leaf]
    DT --- U2[User B Data Leaf]

    U1 --> MT1[Attribute Merkle Tree]
    MT1 --> A1[hash — license type]
    MT1 --> A2[hash — certification level]
    MT1 --> A3[hash — jurisdiction]
    MT1 --> A4[hash — role assignment]
    MT1 --> A5[hash — expiry date]
```

Examples of regulation-specific data:

- Battery regulation: manufacturer license, recycler certification, importer
  permit number
- Financial regulation: accreditation level, jurisdictional scope, compliance
  tier
- Supply chain: producer registration, transport authorization, customs
  clearance class

This data belongs to the regulation, not to the user's identity. A user
participating in two different regulations has two different data leaves —
one per regulator — with different attributes. Their KYC identity leaf is
shared across both.

The regulator pays for on-chain transactions when updating user data
hashes. This gives the regulator skin in the game — they pay for the
attestations they make. The user can always request their current
attestation from the regulator.

### Regulation-specific data and selective disclosure

The same disclosure pattern applies: the user holds the actual data, the
chain holds the hashes. When the operator needs to verify a user's
qualifications:

1. The user obtains their data from the regulator (they have a right to it)
2. The user reveals the relevant attributes to the operator
3. The operator hashes each attribute and verifies against the regulator's
   data trie via reference input

The user controls what to disclose. The operator can verify it is genuine
without contacting the regulator. The regulator never knows which operators
the user works with.

## What the KYC provider does

The KYC provider maintains a Merkle Patricia Trie of verified actors —
a reusable identity service independent of any specific regulation.

### The KYC leaf

Each user gets a leaf in the KYC trie. The leaf contains three concerns,
controlled by two different parties:

```mermaid
graph TD
    LEAF[User Leaf in KYC Trie]

    LEAF --> KEY[Current Public Key<br/><i>controlled by USER</i>]
    LEAF --> STATUS[Attestation Status<br/><i>controlled by KYC PROVIDER</i>]
    LEAF --> DATA[Identity Data Root<br/><i>controlled by KYC PROVIDER</i>]

    DATA --> DT[Identity Data Merkle Tree]
    DT --> H1[hash — name]
    DT --> H2[hash — address]
    DT --> H3[hash — email]
    DT --> H4[hash — home address]
    DT --> H5[hash — ...]
```

| Field | Controlled by | Purpose |
|-------|--------------|---------|
| **Current public key** | User | The key the operator uses for commitments. Updated by the user on rotation. |
| **Attestation status** | KYC provider | Whether this identity is active, suspended, or revoked. |
| **Identity data root** | KYC provider | Root hash of a Merkle tree of identity attributes. The user holds the data. |

### Key sovereignty

The user controls their own key. When a user needs to rotate their key —
compromised device, routine rotation, migration to new hardware — they do
it themselves. No KYC provider involvement, no operator involvement, no
off-chain process.

The smart contract validates the rotation: the previous key signs the
rotation event, the new key goes into the leaf. That's it. Everything
downstream keeps working because the operator's commitments reference the
leaf, not the key directly.

### The KYC event model

The KYC leaf evolves through a small, fixed set of events. Each event has
a clear authorization rule — who must sign — and a clear state transition.

```mermaid
stateDiagram-v2
    [*] --> Attested: Attest (KYC provider)
    Attested --> Attested: Rotate (User)
    Attested --> Suspended: Suspend (KYC provider)
    Suspended --> Attested: Reinstate (KYC provider)
    Attested --> Revoked: Revoke (KYC provider)
    Suspended --> Revoked: Revoke (KYC provider)
    Revoked --> [*]
```

| Event | Who signs | What it does |
|-------|-----------|-------------|
| **Attest** | KYC provider | Creates the leaf. Links an AID to an initial public key. "This entity is verified." |
| **Rotate** | User (previous key) | Updates the public key. No KYC involvement. Sovereignty. |
| **Suspend** | KYC provider | Temporarily disables participation. Key stays, attestation paused. |
| **Reinstate** | KYC provider | Lifts a suspension. |
| **Revoke** | KYC provider | Permanent. The AID is dead. |

Five events. Two actors. The user's sovereignty is exactly one event type:
**Rotate**. The KYC provider's power is the attestation lifecycle: attest,
suspend, reinstate, revoke. The two concerns never overlap.

The smart contract validates one step at a time: previous leaf state + new
event → new leaf state. No full history replay. The trie leaf is a
materialized view of the current state. Each update is incremental —
exactly what fits in a Plutus execution budget.

### Identity data and selective disclosure

The identity data root in the KYC leaf is itself a Merkle tree. Each
attribute (name, address, email, etc.) is stored as a separate hash. The
user holds the actual data off-chain.

When a user needs to prove an identity attribute to an operator:

1. The user reveals the attribute value to the operator
2. The operator hashes it
3. The operator verifies the hash against the identity data Merkle tree
   using the root from the KYC leaf (available via reference input)

The user chooses which attributes to reveal. Unrevealed attributes remain
opaque hashes. This is not cryptographic zero-knowledge — it is hash
preimage disclosure with Merkle proof verification. Simple, auditable,
and within Plutus budget.

The KYC provider updates identity data hashes when the user brings changed
information. The framework does not prescribe how the KYC provider verifies
that information — government ID, document check, self-attestation — that
is the KYC provider's business. The on-chain result is the same: a root
hash update in the leaf.

### Reusability

The same KYC trie can serve multiple regulators and multiple regulations.
One identity infrastructure, many smart contracts referencing it. Or
different regulators can trust different providers — each contract points
to its own.

This is what prevents the operator from faking users. The operator can
mint signing functions and simulate processes, but they cannot add keys to
the KYC provider's trie. Every actor in a regulated process must have a
key that appears in the trusted KYC trie. The validator checks this via
reference input at every transaction.

## What the operator does

The operator participates in the regulated market. They manage a process
trie — one UTxO holding the root hash — containing all items or processes
under their responsibility.

```mermaid
graph TD
    OP[Operator] -->|1| MK[Mint signing functions<br/><i>generate keys, register on-chain,<br/>distribute capability</i>]
    OP -->|2| CC[Create commitments<br/><i>set time-bounded windows<br/>in trie leaves</i>]
    OP -->|3| CS[Collect submissions<br/><i>receive double-signed<br/>payloads from users</i>]
    OP -->|4| ST[Submit transactions<br/><i>batch updates to trie,<br/>pay all fees</i>]
    OP -->|5| PC[Prove computation<br/><i>smart contract verifies<br/>payload matches update</i>]
```

The operator is a **transparent pipe**. They choose *when* to batch, but
not *what* goes in. The signed payload is the input, the leaf update is
the output, and the contract verifies they match.

The operator cannot tamper with the data:

```mermaid
graph LR
    subgraph Cannot Tamper
        P[Signed Payload] -->|operator receives| O[Operator]
        O -->|operator submits| TX[Transaction]
        TX -->|validator checks| V{Payload = Leaf Update?}
        V -->|yes| OK[Accepted]
        V -->|no| REJECT[Rejected]
    end

    C[Commitment<br/><i>defined by smart contract</i>] -->|constrains| TX
    S[Signature<br/><i>invalidated if modified</i>] -->|protects| P
    R[Root Hash<br/><i>must be consistent</i>] -->|constrains| TX
```

- The commitment is defined by the smart contract
- The payload is signed (tampering invalidates the signature)
- The update is validated by the smart contract
- The new root hash must be consistent with the leaf change

## What the user does

The user interacts with a regulated process without any blockchain knowledge.
They don't have a wallet, don't hold ADA, don't know what Cardano is.

```mermaid
graph LR
    U[User] -->|1. receive| SF[Signing<br/>Function]
    U -->|2. disclose| DATA[Selective Data<br/>+ Merkle Proofs]
    U -->|3. use| ACT[Tap / Scan / Click]
    ACT --> DS[Double-Signed<br/>Payload]
    U -->|4. pass on| NEXT[Next Actor's<br/>Public Key]
    DATA --> OP[Operator]
    DS --> OP
    NEXT --> OP
```

1. **Receive a signing capability** — a physical device, an app, or access
   to a signing service
2. **Disclose data** — selectively reveal identity or regulation attributes
   to the operator, with Merkle proofs the operator can verify against
   on-chain roots
3. **Perform the regulated action** — tap an NFC chip, scan a QR code,
   press a button in an app
4. **Pass the baton** — the final action designates the next authorized key

The user also controls their own key. When they need to rotate — compromised
device, routine security, hardware migration — they sign the rotation with
their current key. No KYC provider, no operator, no off-chain process. The
new key propagates automatically because operators reference the KYC leaf,
not the key directly.

From the user's perspective: receive, disclose what's needed, use, pass on.
The cryptography is invisible. Key rotation is the one sovereign act — and
even that can be mediated by whatever wallet or agent the user prefers.

## The signing function

The atomic unit of the system is not a key, not a device, not a user — it
is a **signing function**. An opaque capability that produces signatures
when invoked, without exposing the private key.

```mermaid
graph TB
    OP[Operator] -->|mints| SF[Signing Function]
    SF -->|public key| CHAIN[On-chain Leaf]
    SF -->|capability| WORLD[Physical or Digital World]

    subgraph Substrates
        HW[Hardware SE<br/><i>physical isolation</i>]
        PH[Phone Enclave<br/><i>OS isolation</i>]
        SV[Server Endpoint<br/><i>access control</i>]
        TEE[TEE / Enclave<br/><i>HW-assisted SW</i>]
        ZK[ZK Circuit<br/><i>cryptographic isolation</i>]
    end

    WORLD --- HW
    WORLD --- PH
    WORLD --- SV
    WORLD --- TEE
    WORLD --- ZK
```

| Substrate | Key protection | When to use |
|-----------|---------------|-------------|
| Hardware secure element (SE050) | Physical isolation — key never leaves chip | Sensor-bound, physical measurements |
| Phone secure enclave | OS-level isolation | Consumer actions |
| Server endpoint | Access control | Abstract processes, enterprise |
| TEE / enclave | Hardware-assisted software isolation | High-assurance backends |
| ZK circuit | Cryptographic isolation | Privacy-preserving proofs |

All substrates present the same interface to the chain: a public key
registered in a leaf, and signatures the validator can verify.

The signing function does not need to be secret. It signs whatever is
asked of it. The security is not in the key's secrecy — it is in the
double signature and the commitment protocol.

### Key slots and reuse

A signing device — physical or software — can hold multiple key slots.
Each slot is an independent signing capability.

```mermaid
graph TD
    DEV[Signing Device]
    DEV --> S1[Slot 1<br/><i>Battery Regulation<br/>Operator A</i>]
    DEV --> S2[Slot 2<br/><i>Logistics Tracking<br/>Operator B</i>]
    DEV --> S3[Slot 3<br/><i>Empty — available<br/>for future use</i>]

    S1 -.->|registered in| L1[Operator A's Trie<br/>Leaf #4721]
    S2 -.->|registered in| L2[Operator B's Trie<br/>Leaf #89]
```

- **One slot, one purpose** — cheap, disposable. Lost? The on-chain key is
  deauthorized.
- **Multiple slots, multiple operators** — the same device participates in
  different compliance schemes simultaneously. Each operator only sees
  their own leaf.
- **Reflash and repurpose** — new key, new on-chain registration, new
  meaning. The device outlives any single use case.

The device has no owner in the blockchain sense. It has a *holder*. The
meaning of each slot is defined entirely by the on-chain leaf it's
registered in. The same hardware can be recollected and reused indefinitely,
as long as it has available slots.

## The double signature

Every state transition requires two signatures:

```mermaid
graph TD
    subgraph Process Signature
        SF[Signing Function] -->|signs| PL[Payload + Commitment]
        PL --> PS[Process Signature]
        PS -->|proves| ID[This process produced<br/>this data at this time]
    end

    subgraph Actor Signature
        AK[Actor's Key] -->|signs| SUB[Submission]
        SUB --> AS[Actor Signature]
        AS -->|proves| AUTH[The authorized party<br/>requests this transition]
    end

    PS --> V{Validator}
    AS --> V
    V -->|both valid +<br/>actor in KYC trie| OK[State transition accepted]
```

1. **The process signature** — the signing function signs the payload,
   including the commitment. This proves: *this specific process or item
   produced this specific data at this specific time*. It is an identifier,
   not an access control.

2. **The actor signature** — the current baton holder signs the submission.
   This proves: *the authorized party is requesting this state transition*.
   This is the access control.

Neither signature alone is sufficient:

- Process signature without actor signature → anyone could have called
  the signing function, no authorization
- Actor signature without process signature → the actor could claim
  anything about the process, no authentication

Together they prove: an authorized, attested actor interacted with a
specific process and is submitting a specific, time-bounded state update.

## The commitment protocol

The commitment prevents replay, ensures timeliness, and binds each action
to a specific moment in the on-chain state.

```mermaid
sequenceDiagram
    participant O as Operator
    participant C as Chain
    participant SF as Signing Function
    participant U as User (Baton Holder)

    O->>C: 1. Create commitment in leaf<br/>(validFrom, validUntil)
    Note over C: Leaf now expects an action

    U->>SF: 2. Feed payload + commitment
    SF->>U: Signed payload

    U->>U: 3. Sign submission with own key

    U->>O: 4. Send double-signed payload

    O->>C: 5. Submit transaction

    Note over C: Validator checks:<br/>commitment exists ✓<br/>slot in window ✓<br/>process sig valid ✓<br/>actor in KYC trie ✓<br/>actor authorized ✓<br/>leaf update matches ✓

    C->>C: 6. Clear commitment
    Note over C: Single-use — no replay
```

The commitment is the mechanism that turns a generic signing capability
into a one-shot, time-bounded, authorized action. Because the signing
function signs the commitment as part of the payload, and the smart
contract defines what a valid commitment looks like, the operator has no
room to manipulate timing or replay old submissions.

## The baton pattern

Authorization to act on a process is a baton that travels through
the real world — physical or digital.

```mermaid
graph LR
    subgraph Lifecycle
        O[Operator creates leaf<br/><i>no actor assigned</i>]
        O --> A1[First tap<br/><i>Actor A becomes<br/>baton holder</i>]
        A1 --> U1[Actor A uses<br/><i>submits readings,<br/>progresses state</i>]
        U1 --> P1[Actor A passes<br/><i>final submission includes<br/>Actor B's pubkey</i>]
        P1 --> A2[Actor B holds baton<br/><i>Actor A locked out</i>]
        A2 --> U2[Actor B uses]
        U2 --> P2[Actor B passes<br/><i>to Actor C</i>]
        P2 --> A3[Actor C holds baton]
        A3 --> END[End of lifecycle]
    end
```

The baton passes atomically with the last action. There is no gap where
nobody holds authorization — the transfer is part of the state transition,
validated by the smart contract.

No user registration. No identity database. No login. Authorization is
determined entirely by the on-chain state. You hold the baton or you
don't.

## Two modes

The same architecture supports two fundamentally different modes:

```mermaid
graph TB
    subgraph Physical Mode
        SENSOR[Physical Sensor] -->|I2C| SE[Secure Element]
        SE -->|COSE_Sign1| NFC[NFC Interface]
        NFC -->|tap| PHONE[Phone]
        PHONE -->|payload| OP1[Operator]
        OP1 -->|tx| CHAIN1[Chain]

        NOTE1[Object is the identity<br/>AND the witness]
    end

    subgraph Process Mode
        SERVER[Server] -->|hosts| SFUNC[Signing Function]
        APP[App / API] -->|invokes| SFUNC
        SFUNC -->|signed payload| OP2[Operator]
        OP2 -->|tx| CHAIN2[Chain]

        NOTE2[Identity is abstract<br/>Protocol is the witness]
    end
```

### Physical mode

The object carries its own identity and can attest its own state.

- A battery with a sensor and secure element signs "my state of health
  is 87%"
- The data comes from the thing itself — a physical measurement
- No server needed — the object is both the identifier and the witness
- Trust comes from the hardware: the sensor measured reality, the secure
  element signed it, the chain anchored it

Use when: the regulation requires physical measurements, sensor data,
or tamper-evident attestation from the object itself.

### Process mode

There is no physical object — just a logical process advancing through
stages.

- A permit application moves from applicant → reviewer → approver
- A certification workflow passes through inspector → auditor → issuer
- A supply chain declaration flows from producer → transporter → customs

The signing function lives on a server. The operator mints a key pair,
registers the public key on-chain, and makes the signing function
available. The identity is abstract — it represents a process, not a
thing.

Trust comes from the protocol: the double signature proves the right
actor performed the right action, the commitment proves timeliness, the
smart contract proves correctness.

Use when: the regulation governs a multi-party workflow where what
matters is that the right sequence of actions happened, not what a
physical sensor measured.

### Same architecture

```mermaid
graph TD
    subgraph Shared Architecture
        MPT[Merkle Patricia Trie]
        COMMIT[Commitment Protocol]
        DSIG[Double Signature]
        BATON[Baton Pattern]
        SC[Smart Contract Validation]
        KYCC[KYC Trie Reference]
    end

    PHYS[Physical Mode] --> MPT
    PROC[Process Mode] --> MPT
    PHYS --> COMMIT
    PROC --> COMMIT
    PHYS --> DSIG
    PROC --> DSIG
    PHYS --> BATON
    PROC --> BATON
    PHYS --> SC
    PROC --> SC
    PHYS --> KYCC
    PROC --> KYCC
```

The difference is the trust basis: hardware attestation vs protocol
enforcement. Physical mode is strictly stronger (you get process
guarantees *plus* physical attestation), but process mode covers
regulations that have no physical component.

## Privacy and data sovereignty

No single party has the full picture:

```mermaid
graph TD
    subgraph Knowledge Boundaries
        OP[Operator<br/><i>sees only disclosed attributes<br/>+ process data</i>]
        U[User<br/><i>holds all their data<br/>chooses what to reveal</i>]
        CH[Chain<br/><i>sees only hashes<br/>no plaintext, no real-world link</i>]
        SV[Server<br/><i>sees requests<br/>can't attribute them</i>]
        KP[KYC Provider<br/><i>knows identities<br/>doesn't know which process</i>]
        RG[Regulator<br/><i>knows regulation attributes<br/>doesn't know which operator</i>]
    end

    OP -.-|no link| U
    U -.-|no link| CH
    KP -.-|no link| OP
    RG -.-|no link| OP
    SV -.-|no link| RG
```

| Party | Knows | Doesn't know |
|-------|-------|-------------|
| **KYC provider** | Identity data behind each attested key | Which processes the key participates in, which operators |
| **Regulator** | Regulation-specific attributes for each user | Which operators the user works with |
| **Operator** | Only the attributes the user chose to disclose | Full identity, undisclosed attributes |
| **User** | All their own data — identity and regulation attributes | The private key of the signing function |
| **Chain** | Hashes and signatures | Any plaintext data or real-world identities |
| **Server** (process mode) | That signing requests came in | Who made them or what they mean |

The user is the **data holder**. The KYC provider and regulator publish
hashes on-chain. The user holds the preimages. Disclosure is always
user-initiated and selective — the user presents specific attributes with
Merkle proofs, and the operator can verify without seeing anything else.

The KYC provider knows identities but not processes or operators. The
regulator knows regulation attributes but not which operators the user
works with. The operator sees only what the user reveals. The chain sees
only hashes and signatures. No single party can reconstruct the full
picture.

Privacy is structural, not policy-based. There is no personal data on-chain
to protect because the chain holds only hashes. Off-chain, the user
controls their own data and decides who sees what.

## The full picture

```mermaid
graph TB
    subgraph KYC Layer
        KYC_P[KYC Provider<br/><i>off-chain verification</i>]
        KYC_UTxO[KYC UTxO<br/><i>identity trie root</i>]
        KYC_P -->|maintains| KYC_UTxO
    end

    subgraph Regulator Layer
        REG[Regulator<br/><i>writes rules, maintains data</i>]
        SC[Smart Contract<br/><i>Plutus validator</i>]
        DT[Data Trie UTxO<br/><i>regulation attributes</i>]
        REG -->|deploys| SC
        REG -->|maintains| DT
        SC -->|references| KYC_UTxO
        SC -->|references| DT
    end

    subgraph Operator Layer
        OP[Operator<br/><i>transparent pipe</i>]
        TRIE[Process Trie UTxO<br/><i>items / processes</i>]
        SF1[Signing Function 1]
        SF2[Signing Function 2]
        SF3[Signing Function N]
        OP -->|manages| TRIE
        OP -->|mints| SF1
        OP -->|mints| SF2
        OP -->|mints| SF3
        SC -->|governs| TRIE
    end

    subgraph User Layer
        U1[User A<br/><i>holds baton + data</i>]
        U2[User B<br/><i>next in line</i>]
        U3[User N<br/><i>future actor</i>]
    end

    SF1 -.->|signing capability| U1
    SF2 -.->|signing capability| U2
    SF3 -.->|signing capability| U3

    U1 -->|double-signed payload<br/>+ data proofs| OP
    U1 -->|passes baton to| U2
```

## Summary

The regulator's workflow:

1. **Analyze the regulation** — extract the data schema, valid transitions,
   parties, and deadlines
2. **Choose a KYC provider** — decide which identity infrastructure to
   trust, reference its UTxO
3. **Deploy the data trie** — maintain regulation-specific user attributes,
   pay for on-chain attestation updates
4. **Write the smart contract** — encode the regulation as a Plutus
   validator that governs the process trie and checks actors against the
   KYC trie and data trie
5. **Publish the contract** — operators deploy their tries under it
6. **Audit** — verify any operator's trie against the contract at any time

The KYC provider's workflow:

1. **Verify entities** — through whatever off-chain process they use
2. **Maintain the trie** — attest, suspend, reinstate, or revoke actors;
   update identity data hashes when users bring changed information
3. **Serve multiple regulators** — the same trie can be referenced by
   many smart contracts

The operator's workflow:

1. **Deploy a trie** — create a UTxO governed by the regulator's contract
2. **Mint signing functions** — generate keys, register on-chain, distribute
3. **Verify user data** — receive disclosed attributes + Merkle proofs from
   users, verify against on-chain roots
4. **Collect and submit** — receive double-signed payloads, batch into
   transactions
5. **Pay fees** — compliance is cheaper than non-compliance

The user's workflow:

1. **Receive** — get a device or access to a signing function
2. **Disclose** — selectively reveal identity or regulation attributes to
   the operator with Merkle proofs
3. **Use** — tap, scan, click
4. **Pass on** — designate the next actor in your final submission
5. **Rotate** — update your own key when needed, without anyone's permission

No blockchain knowledge required at any level. The regulator writes
rules and attests qualifications. The KYC provider attests identities.
The operator follows the rules. The user holds their data, controls their
key, and participates. The chain enforces.

## Open question: operator honesty and user data

The selective disclosure model has a gap. The user reveals data to the
operator off-chain. The operator verifies it against on-chain hashes. But
the smart contract never sees the data — only the trie root via reference
input. Nothing on-chain proves the operator actually performed the
verification.

This means:

- The operator could accept a user who didn't provide valid data
- The operator could let a user participate without the required
  qualifications
- The operator could ignore the data requirements entirely

The chain enforces process integrity (signatures, commitments, state
transitions) but cannot enforce that the operator checked the user's
disclosed data before creating a commitment.

### Why this matters

The regulator's contract governs the process trie. Every state transition
is validated. But the data verification step — "does this user actually
hold a valid inspector license?" — happens off-chain between the user and
the operator. A dishonest operator could collude with unqualified users
or simply skip the check.

### Possible approaches

**After-the-fact audit.** The regulator can request data from any user and
verify it against the on-chain hashes. If the operator accepted users
without valid data, this is detectable — but only after the fact.

**Zero-knowledge proofs.** The user generates a ZK proof: "I know data
whose hash matches my leaf in the trie, and this data satisfies predicate
P" — without revealing the data. The proof is submitted on-chain. The
smart contract verifies it.

Plutus V3 has BLS12-381 built-ins (G1/G2 point operations, pairing
checks) which enable Groth16 SNARK verification on-chain. In principle,
the user could prove they satisfy the regulation's requirements and the
smart contract could verify the proof at transaction time — making the
data check enforceable on-chain.

**Status:** The BLS12-381 primitives exist in Plutus V3. The practical
feasibility — execution budget cost, proof generation tooling targeting
Cardano, circuit complexity for Merkle proof + predicate satisfaction —
is not yet established. This is an active area of development in the
Cardano ecosystem.

### Current position

Without ZK, the operator is trusted to check user data. The contract
enforces everything else — signatures, commitments, state transitions,
baton passing — but data verification is a trust assumption on the
operator. ZK would close this gap but adds significant complexity and
depends on tooling maturity.

This is an open design question. The framework works without ZK (the
operator has economic incentives and audit exposure), but the gap exists
and should be acknowledged.

## Why Cardano

This analysis is based on Cardano's capabilities. The design patterns
described here — signing functions, double signatures, commitment
protocols, the baton pattern — are conceptual and other blockchains are
free to find their own way to implement them.

That said, the on-chain requirements are non-trivial:

- **Merkle Patricia Trie verification in the validator** — the smart
  contract must verify that a leaf update produces the correct new root
  hash. This is Merkle proof verification at every transaction.
- **Reference inputs** — the validator must read the KYC trie UTxO and
  the regulator data trie UTxO without spending them. This is a
  Cardano-native feature (CIP-31) that enables cross-trie verification
  without coordination. Multiple reference inputs in a single transaction
  allow the validator to check identity, qualifications, and process state
  together.
- **Native signature verification** — Ed25519 and secp256k1 must be
  available as cheap built-in operations, not expensive general-purpose
  computation.
- **Full transaction context** — the validator must see the previous state,
  the new state, all signatures, and the current slot range in a single
  evaluation.
- **Deterministic payload parsing** — CBOR/COSE decoding inside the
  validator to check that signed data matches the state update.
- **Economically viable validator complexity** — all of the above must
  fit within the execution budget of a single transaction at reasonable
  cost.

Cardano's eUTxO model and Plutus built-ins meet these requirements. The
UTxO model naturally maps to the operator-owns-their-trie pattern — one
UTxO per operator, the validator sees the full spend-and-produce context,
reference inputs enable cross-trie KYC checks, and native built-ins for
Ed25519 and secp256k1 make signature verification practical.

Other chains may offer equivalent primitives. The schema does not depend
on Cardano-specific features at the design level — but the implementation
does depend on a chain that can handle non-trivial smart contract logic
at reasonable cost.
